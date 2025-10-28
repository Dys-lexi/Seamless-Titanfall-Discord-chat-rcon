import discord
from discord.ext import tasks
import asyncio
import os
import json
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
import math
import re


def setup(bot, db_func, global_vars):
    """Setup function called by output.py"""
    root = "./extensions/"

    # Get access to global variables
    version = 4
    context = global_vars['context']
    savecontext = global_vars['savecontext']
    getpriority = global_vars['getpriority']
    os.makedirs(f"{root}pfps", exist_ok=True)
    os.makedirs(f"{root}evaluated", exist_ok=True)

    def deep_merge(a, b):
        """Returns new dict with b merged into a"""
        result = a.copy()
        for key, value in b.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    async def ollama_vision(image_path, prompt, model="llava:7b"):
        """Call Ollama with image and text (async)"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            # Use asyncio to run the blocking request in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post('http://localhost:11434/api/generate',
                    json={
                        'model': model,
                        'prompt': prompt,
                        'images': [image_data],
                        'stream': False
                    }, timeout=120)
            )

            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Ollama vision error for {image_path}: {e}")
            return f"Error: {str(e)}"

    def create_pfp_collage():
        """Create a collage of all analyzed pfps with their results"""
        if "pfpinfo" not in context or not context["pfpinfo"]:
            return

        # Get all users with analyzed pfps
        analyzed_users = [(uid, data) for uid, data in context["pfpinfo"].items()
                         if "mostrecenthash" in data and "contains" in data and data.get("version") == version]

        if not analyzed_users:
            return

        # Calculate grid size (roughly square)
        total = len(analyzed_users)
        cols = math.ceil(math.sqrt(total))
        rows = math.ceil(total / cols)

        # Create canvas
        img_size = 256
        canvas_width = cols * img_size
        canvas_height = rows * img_size
        canvas = Image.new('RGB', (canvas_width, canvas_height), color='black')
        draw = ImageDraw.Draw(canvas)

        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()

        # Place each pfp
        for idx, (uid, data) in enumerate(analyzed_users):
            row = idx // cols
            col = idx % cols
            x = col * img_size
            y = row * img_size

            # Load and resize pfp
            pfp_path = f"{root}pfps/{data['mostrecenthash']}.png"
            if os.path.exists(pfp_path):
                try:
                    pfp = Image.open(pfp_path).convert('RGBA')
                    pfp = pfp.resize((img_size, img_size))
                    canvas.paste(pfp, (x, y))

                    # Calculate text background size
                    json_lines = list(filter(lambda x: "}," not in x,json.dumps({**data["contains"],"name":data["name"]}, indent=2).split('\n')))
                    text_height = len(json_lines[1:-1]) * 15 + 10
                    text_width = img_size // 1  # Left 50% of image

                    # Create semi-transparent overlay for left 50%
                    overlay = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 180))
                    canvas.paste(overlay, (x, y), overlay)

                    # Draw JSON text with color coding
                    y_offset = 5
                    for line in json_lines[1:-1]:
                        # Determine color based on value
                        if 'true' in line.lower():
                            color = 'green'
                        elif 'false' in line.lower():
                            color = 'red'
                        elif '"name":' in line.lower():
                            color = 'pink'
                        else:
                            color = 'orange'

                        draw.text((x + 5, y + y_offset), line, fill=color, font=font)
                        y_offset += 15
                except Exception as e:
                    print(f"Error adding pfp {uid} to collage: {e}")

        # Save collage
        canvas.save(f"{root}evaluated/pfps_analysis.png")
        print(f"Saved collage with {len(analyzed_users)} pfps")

    async def checkaperson(person,force = False):
        querys = {
            "hascat":'Decide if this image contain a cat. First, provide your reasoning about what you see in the image, and if you therefore think there is a cat. Then provide a conclusion in valid JSON format: {"hascat":true} or {"hascat":false}. Format your response as:\nReasoning: [your analysis]\nConclusion: [JSON]',
            "hasdog":'Decide if this image contain a dog. First, provide your reasoning about what you see in the image, and if you therefore think there is a dog. Then provide a conclusion in valid JSON format: {"hasdog":true} or {"hasdog":false}. Format your response as:\nReasoning: [your analysis]\nConclusion: [JSON]',
            "hashuman":'Decide if this image contain a human. First, provide your reasoning about what you see in the image, and if you therefore think there is a human. Then provide a conclusion in valid JSON format: {"hashuman":true} or {"hashuman":false}. Format your response as:\nReasoning: [your analysis]\nConclusion: [JSON]',
            "isphoto":'Decide if this image is a photograph or otherwise photos that are slightly edited, for example changing framing and orientation flipping are fine. First, provide your reasoning about what you observe in the image. Then provide a conclusion in valid JSON format: {"isphoto":true} for a photograph, or {"isphoto":false} for hand drawn, paintings and computer-generated art. Format your response as:\nReasoning: [your analysis]\nConclusion: [JSON]'
            }
        print(f"Checking {person.display_name}".ljust(30), end = " ")
        uid = str(person.id)
        built = {
        "mostrecenthash":None,
        "version" : version,
        "contains":{x:None for x in querys},
        "queries":{x:None for x in querys},
        "name": person.name
        }
        if not person.avatar:


            context["pfpinfo"][uid] = built
            savecontext()
            return {}
        recheck = False
        if not force and (hashcheck := person.avatar.key) == getpriority(context,["pfpinfo",uid,"mostrecenthash"]) and getpriority(context,["pfpinfo",uid,"version"]) == version :
            print("already processed")
            if len(querys) != len(getpriority(context,["pfpinfo",uid,"queries"],nofind = [])) or len(set([*querys,*getpriority(context,["pfpinfo",uid,"queries"],nofind = [])])) != len(querys):
                # print("recheck")
                recheck = True
            else:
                return {}
        if recheck:
            built =  deep_merge(built,context["pfpinfo"][uid])
        built["mostrecenthash"] = hashcheck
        # print("")
        # at this point evaluate time!!!
        loop = asyncio.get_event_loop()
        if not  os.path.exists(filepath :=f"{root}pfps/{hashcheck}.png"):
            print("Avatar not cached - puliing")
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(person.avatar.replace(size=256).url)
            )
            with open(filepath, 'wb') as f:
                f.write(response.content)
        for output,query in querys.items():
            if recheck and output in context["pfpinfo"][uid]["queries"]: 
                # print("skipping",output)
                continue
            while built["contains"][output] is None:
                result = await ollama_vision(filepath,query)
                if "Conclusion:" in result:
                    conclusion_part = result.split("Conclusion:")[-1].strip()
                    json_match = re.search(r'\{[^}]+\}', conclusion_part)
                    if json_match:
                        built["contains"] = {**built["contains"],**(json.loads(json_match.group()))}
                        built["queries"][output] = {"result":result}
        print(f"built\n{json.dumps(built,indent=4)}")
        if "pfpinfo" not in context:
            context["pfpinfo"] = {}
        context["pfpinfo"][uid] = built
        savecontext()
        await loop.run_in_executor(None, create_pfp_collage)

        
                  
    

    @tasks.loop(seconds=1800)
    async def pfps():
        """Analyze all gun images with llava:7b"""
        print("meow")
        if "pfpinfo" not in context:
            context["pfpinfo"] = {}

        people = bot.get_guild(context["activeguild"]).members
        for person in people:
            await checkaperson(person,False)

    pfps.start()