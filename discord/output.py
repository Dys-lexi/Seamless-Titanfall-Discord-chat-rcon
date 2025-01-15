import os
import json
import random
import time
import threading
import discord
import asyncio
from asgiref.sync import async_to_sync
from flask import Flask, request, jsonify
from waitress import serve
from discord import Option
# print("meow")
messageflush = []
lastmessage = 0

print("running discord logger bot")
lastrestart = 0
messagecounter = 0

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True  # Enable the members intent
intents.presences = True

# Load token from environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN', 0)
if TOKEN == 0:
    print("NO TOKEN FOUND")
messagestosend = {}
commands = {}
# Load channel ID from file
context = {
    "logging_cat_id": 0,
    "activeguild": 0,
    "serveridnamelinks": {},
    "serverchannelidlinks": {},
    "RCONallowedusers": []
}
serverchannels = []
if not os.path.exists("./data"):
    os.makedirs("./data")
channel_file = "channels.json"
if os.path.exists("./data/"+channel_file):
    with open("./data/"+channel_file, "r") as f:
        tempcontext = json.load(f)
        for key in tempcontext.keys():
            context[key] = tempcontext[key]
else:
    context["logging_cat_id"] = 0
    context["activeguild"] = 0
    print("Channel file not found, using default channel ID 0.")
print(json.dumps(context, indent=4))
bot = discord.Bot(intents=intents)
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    if context["logging_cat_id"] != 0:
        # get all channels in the category and store in serverchannels
        guild = bot.get_guild(context["activeguild"])
        category = guild.get_channel(context["logging_cat_id"])
        serverchannels = category.channels


@bot.slash_command(name="bindloggingtocategory", description="Bind logging to a new category (begin logging) can be existing or new")
async def bind_logging_to_category(ctx, category_name: str):
    global context

    guild = ctx.guild
    if guild.id == context["activeguild"] and context["logging_cat_id"]!= 0:
        await ctx.respond("Logging is already bound to a category.", ephemeral=True)
        return
    # Create the new category, unless the name exists, then bind to that one
    if category_name in [category.name for category in guild.categories]:
        category = discord.utils.get(guild.categories, name=category_name)
        print("binding to existing category")
    else:
        category = await guild.create_category(category_name)
        print("creating new category")

    context["logging_cat_id"]= category.id
    # Store the channel ID in the variable
    # context["logging_cat_id"]= channel.id
    context["activeguild"] = guild.id

    # Save the channel ID to the file for persistence
    savecontext()

    await ctx.respond(f"Logging channel created under category '{category_name}' with channel ID {context['logging_cat_id']}.", ephemeral=True)

@bot.slash_command(
    name="rcon", 
    description="Send an RCON command to a server"
)
async def rcon_command(
    ctx,
    cmd: Option(str, "The command to send"),
    servername: Option(str, "The servername (* for all, omit for current channel's server)", required=False) = None
):
    print("rcon command from", ctx.author.id, cmd, "to", servername if servername != None else "Auto")
    
    global context, commands
    if ctx.author.id not in context["RCONallowedusers"]:
        await ctx.respond("You are not allowed to use RCON commands.", ephemeral=True)
        return
    # await ctx.respond(f"Command: {cmd}, Server: {servername if servername != None else 'current channels'}", ephemeral=True)

    if servername == None and ctx.channel.id in context["serverchannelidlinks"].values():
        for key, value in context["serverchannelidlinks"].items():
            if value == ctx.channel.id:
                serverid = key
                break
        else:
            await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=True)
            return
        if serverid not in commands.keys():
            commands[serverid] = []
        commands[serverid].append(cmd)
        await ctx.respond(f"Command added to queue for server: **{context['serveridnamelinks'][serverid]}**.", ephemeral=True)
    elif servername == "*":
        for serverid in context["serverchannelidlinks"].keys():
            if serverid not in commands.keys():
                commands[serverid] = []
            commands[serverid].append(cmd)
        await ctx.respond(f"Command added to queue for all servers.", ephemeral=True)
    elif servername in context["serveridnamelinks"].values():
        for serverid, name in context["serveridnamelinks"].items():
            if name == servername:
                break
        else:
            await ctx.respond("Server not found.", ephemeral=True)
            return
        if serverid not in commands.keys():
            commands[serverid] = []
        commands[serverid].append(cmd)
        await ctx.respond(f"Command added to queue for server: **{servername}**.", ephemeral=True)
    else:
        await ctx.respond("Server not found.", ephemeral=True)
    

    

@bot.slash_command(
    name="rconchangeuserallowed",
    description="toggle if a user is allowed to use RCON commands"
)
async def rcon_add_user(
    ctx,
    user: Option(discord.User, "The user to add")
):
    global context
    # check if the user is an admin on the discord
    if user.id in context["RCONallowedusers"]:
        context["RCONallowedusers"].remove(user.id)
        savecontext()
        await ctx.respond(f"User {user.name} removed from RCON whitelist.", ephemeral=True)
    elif ctx.author.guild_permissions.administrator:
        context["RCONallowedusers"].append(user.id)
        savecontext()
        await ctx.respond(f"User {user.name} added to RCON whitelist.", ephemeral=True)
    else:
        await ctx.respond(f"Only administrators can add users to the RCON whitelist.", ephemeral=True)

@bot.event
async def on_message(message):
    global messagestosend, context
    if message.author == bot.user:
        return
    if message.channel.id in context["serverchannelidlinks"].values():
        serverid = [key for key, value in context["serverchannelidlinks"].items() if value == message.channel.id][0]
        if serverid not in messagestosend.keys():
            messagestosend[serverid] = []
        if len(f"{message.author.nick if message.author.nick != None else message.author.display_name}: [38;5;254m{message.content}") > 240:
            await message.channel.send("Message too long, cannot send.")
            return
        messagestosend[serverid].append(f"{message.author.nick if message.author.nick != None else message.author.display_name}: [38;5;254m{message.content}")



# @bot.slash_command(name="bindloggingtochannel", description="Bind logging to an existing channel")
# async def bind_logging_to_channel(ctx, servername: str):
#     global context
#     # get all the server ids and names from context, and present as options
#     guild = ctx.guild
#     if guild.id == activeguild and context["logging_cat_id"]!= 0:
#         await ctx.respond("Logging is already bound to a category.")
#         return


def recieveflaskprintrequests():
    app = Flask(__name__)

    @app.route('/askformessage', methods=['POST'])
    def askformessage():
        global context, messagestosend
        # print("uwu")
        data = request.get_json()
        serverid = data["serverid"]
        timer = 0
        while timer < 60:
            timer += 1
            if  serverid in messagestosend.keys() and len(messagestosend[serverid]) > 0 or serverid in commands.keys() and len(commands[serverid]) > 0:
                if serverid in commands.keys() and len(commands[serverid]) > 0:
                    sendingcommands = commands[serverid]
                    commands[serverid] = []
                else:
                    sendingcommands = []
                if serverid in messagestosend.keys() and len(messagestosend[serverid]) > 0:
                    texts = messagestosend[serverid]
                    messagestosend[serverid] = []
                else:
                    texts = []
                return  {"texts":"%&%&".join(texts),"commands":"%&%&".join(sendingcommands)}
            time.sleep(0.2)

        return {"texts":"","commands":""}
            

    @app.route('/servermessagein', methods=['POST'])
    def printmessage():
        global messageflush, lastmessage, messagecounter, context
        data = request.get_json()
        if context["logging_cat_id"] == 0:
            return jsonify({"message": "no category bound"})
        if "servername" in data.keys():
            servername = data["servername"]
        if "player" in data.keys():
            playername = data["player"]
        if "serverid" not in data.keys() or "type" not in data.keys() or "timestamp" not in data.keys() or "messagecontent" not in data.keys():
            return jsonify({"message": "missing paramaters (type, timestamp, messagecontent, serverid)"})
        serverid = data["serverid"]
        typeofmessage = data["type"]
        timestamp = data["timestamp"]
        messagecontent = data["messagecontent"]

        messageflush.append({
            "servername": servername,
            "player": playername,
            "messagecontent": messagecontent,
            "timestamp": timestamp,
            "type": typeofmessage,
            "serverid": serverid,
        })

        messagecounter += 1
        lastmessage = time.time()

        if serverid not in context["serveridnamelinks"]:
            context["serveridnamelinks"][serverid] = servername
            savecontext()

        print(context["serverchannelidlinks"])

        if serverid not in context["serverchannelidlinks"].keys():
            # Get guild and category
            guild = bot.get_guild(context["activeguild"])
            category = guild.get_channel(context["logging_cat_id"])

            
        return jsonify({"message": "success"})

    serve(app, host="0.0.0.0", port=3451, threads=60) #prod
    # app.run(host="0.0.0.0", port=3451, threads=60)  #dev

async def createchannel(guild, category, servername, serverid):
    global context
    print("Creating channel...")
    # check if channel name already exists, if so use that
    if servername in [channel.name for channel in category.channels]:
        channel = discord.utils.get(category.channels, name=servername)
        context["serverchannelidlinks"][serverid] = channel.id
        savecontext()
        return
    channel = await guild.create_text_channel(servername, category=category)
    context["serverchannelidlinks"][serverid] = channel.id
    savecontext()

async def changechannelname(guild, servername, serverid):
    global context
    print("Changing channel name...")
    channel = guild.get_channel(context["serverchannelidlinks"][serverid])
    await channel.edit(name=servername)
    context["serveridnamelinks"][serverid] = servername
    savecontext()

    # return channel
def messageloop():
    global messageflush, lastmessage
    addflag = False
    while True:
        try:
        # check if any uncreated channels exist
            if (time.time() - lastmessage > 0.5 and len(messageflush) > 0) or len(str(messageflush)) > 1500:
                for message in messageflush:
                    print(addflag)
                    if message["serverid"] not in context["serverchannelidlinks"].keys() and addflag == False:
                        addflag = True
                        guild = bot.get_guild(context["activeguild"])
                        category = guild.get_channel(context["logging_cat_id"])
                        asyncio.run_coroutine_threadsafe(createchannel(guild, category, message["servername"], message["serverid"]), bot.loop)
                        time.sleep(10)
                    print(addflag)
                addflag = False
                for message in messageflush:   
                    if message["serverid"] in context["serverchannelidlinks"].keys() and message["servername"] not in context["serveridnamelinks"].values() and addflag == False:
                        addflag = True
                        guild = bot.get_guild(context["activeguild"])
                        asyncio.run_coroutine_threadsafe(changechannelname(guild, message["servername"], message["serverid"]), bot.loop)
                addflag = False    
                print("boop",messageflush)
                channel = bot.get_channel(context["serverchannelidlinks"][messageflush[0]["serverid"]])
                output = []
                messageflush = sorted(messageflush, key=lambda x: x["timestamp"])
                for message in messageflush:
                    print("sending")
                    if message["type"] == 1:
                        output.append(f"**{message['player']}**:  {message['messagecontent']}")
                    elif message["type"] == 2:
                        # print("2")
                        # output.append(f"meow")
                        output.append(f"""```{message['player']} {message['messagecontent']}```""")
                    elif message["type"] == 3:
                        output.append(f"{message['messagecontent']}")

                    else:print("sob")
                    
                asyncio.run_coroutine_threadsafe(channel.send("\n".join(output)), bot.loop)
                messageflush = []
                lastmessage = time.time()
        except AttributeError as e:
            time.sleep(3)
            print("bot not ready",e)
        time.sleep(0.1)

def savecontext():
    global context
    print("saving")
    with open("./data/"+channel_file, "w") as f:
        json.dump(context, f, indent=4)


threading.Thread(target=messageloop).start()
threading.Thread(target=recieveflaskprintrequests).start()



bot.run(TOKEN)
