import asyncio
import json
import os
import threading
import time
import random

from flask import Flask, jsonify, request
from waitress import serve

import discord
from discord import Option

# this whole thing is a mess of global varibles, jank threading and whatever, but it works just fine :)
# (I never bothered much with coding style)

# print("meow")
messageflush = []
lastmessage = 0

print("running discord logger bot")
lastrestart = 0
messagecounter = 0
SLEEPTIME_ON_FAILED_COMMAND = 7
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True  # Enable the members intent
intents.presences = True

# Load token from environment variable
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "0")
SERVERPASS = os.getenv("DISCORD_BOT_PASSWORD", "*")
if SERVERPASS == "*":
    print("No password found, allowing inputs from all addresses")
else:
    print("Server password set to", "*"*len(SERVERPASS))
if TOKEN == 0:
    print("NO TOKEN FOUND")
stoprequestsforserver = {}
discordtotitanfall = {}
# Load channel ID from file
context = {
    "logging_cat_id": 0,
    "activeguild": 0,
    "serveridnamelinks": {},
    "serverchannelidlinks": {},
    "RCONallowedusers": [],
    "globalchannelid": 0,
}
serverchannels = []
if not os.path.exists("./data"):
    os.makedirs("./data")
channel_file = "channels.json"
if os.path.exists("./data/" + channel_file):
    with open("./data/" + channel_file, "r") as f:
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
    print(f"{bot.user} has connected to Discord!")
    if context["logging_cat_id"] != 0:
        # get all channels in the category and store in serverchannels
        guild = bot.get_guild(context["activeguild"])
        category = guild.get_channel(context["logging_cat_id"])
        serverchannels = category.channels


@bot.slash_command(
    name="bindloggingtocategory",
    description="Bind logging to a new category (begin logging) can be existing or new",
)
async def bind_logging_to_category(ctx, category_name: str):
    global context

    guild = ctx.guild
    if guild.id == context["activeguild"] and context["logging_cat_id"] != 0:
        await ctx.respond("Logging is already bound to a category.", ephemeral=True)
        return
    # Create the new category, unless the name exists, then bind to that one
    if category_name in [category.name for category in guild.categories]:
        category = discord.utils.get(guild.categories, name=category_name)
        print("binding to existing category")
    else:
        category = await guild.create_category(category_name)
        print("creating new category")

    context["logging_cat_id"] = category.id
    # Store the channel ID in the variable
    # context["logging_cat_id"]= channel.id
    context["activeguild"] = guild.id

    # Save the channel ID to the file for persistence
    savecontext()

    await ctx.respond(
        f"Logging channel created under category '{category_name}' with channel ID {context['logging_cat_id']}.",
        ephemeral=True,
    )
# sanction command. expiry, playername, reason, and a choice bettween ban or mute must be provided
@bot.slash_command(name="sanction", description="Sanction a player")
async def sanction(
    ctx,
    playername: str,
    reason: str,
    sanctiontype: Option(
        str, "The type of sanction to apply", choices=["mute", "ban"]
    ),
    expiry: Option(str, "The expiry time of the sanction in format yyyy-mm-dd, omit is forever") = None,
    servername: Option(
        str, "The servername (omit for current channel's server)", required=False
    ) = None,
):
    global context, discordtotitanfall
    await ctx.defer()

    if ctx.author.id not in context["RCONallowedusers"]:
        await ctx.respond("You are not allowed to use this command.", ephemeral=True)
        return
    if expiry == None: expiry = ""
    commandstring = f"!sanctionban {playername} -expire {expiry} -reason {reason} -type {sanctiontype} -issuer {ctx.author.name}"
    print("sanction command from", ctx.author.id, "to", playername)
    serverid = getchannelidfromname(servername,ctx)
    if serverid is None:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=True)
        return
    initdiscordtotitanfall(serverid)
    discordtotitanfall[serverid]["commands"].append(
        {"command": commandstring, "id": random.randint(0, 100000000000)}
    )
    await returncommandfeedback(serverid, discordtotitanfall[serverid]["commands"][-1]["id"], ctx, sanctionoverride)

def sanctionoverride(data, serverid):
    embed = discord.Embed(
        title="Sanction Result",
        color=0xff70cb,
    )
    try:
        data = json.loads(data)
    except:
        embed.add_field(name="Response", value=f"\u200b {data}", inline=False)
    else:
        embed.add_field(name="Targeted Player", value=f"\u200b {data['playername']}", inline=False)
        embed.add_field(name="Sanction Type", value=f"\u200b {data['Sanctiontype']}", inline=False)
        embed.add_field(name="Sanction Reason", value=f"\u200b {data['reason']}", inline=False)
        embed.add_field(name="Sanction Expiry", value=f"\u200b {data['expire']}", inline=False)
        embed.add_field(name="Targeted player UID", value=f"\u200b {data['UID']}", inline=False)
        embed.add_field(name="Sanction Issuer", value=f"\u200b {data['issueruid']}", inline=False)

    return embed


@bot.slash_command(name="playing", description="List the players on a server")
async def playing(
    ctx,
    servername: Option(
        str, "The servername (omit for current channel's server)", required=False
    ) = None,
):
    global context, discordtotitanfall
    await ctx.defer()
    if servername is None and ctx.channel.id in context["serveridnamelinks"].values():
        serverid = [
            key
            for key, value in context["serveridnamelinks"].items()
            if value == ctx.channel.id
        ][0]
    elif ctx.channel.id in context["serverchannelidlinks"].values():
        for key, value in context["serverchannelidlinks"].items():
            if value == ctx.channel.id:
                serverid = key
                break
    else:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=True)
        return
    print("playing command from", ctx.author.id, "to", servername if servername is not None else "Auto")
    initdiscordtotitanfall(serverid)
    discordtotitanfall[serverid]["commands"].append(
            {"command": "!playing", "id": random.randint(0, 100000000000)}
        )
    await returncommandfeedback(serverid, discordtotitanfall[serverid]["commands"][-1]["id"], ctx, listplayersoverride)

def listplayersoverride(data, serverid):
    data = json.loads(data)
    if len(data) == 0:
        return discord.Embed(
            title=f"Server status for {context['serveridnamelinks'][serverid]}",
            description="No players online",
            color=0xff70cb,
        )
    else:
        formattedata = {"meta":{}}
        for key, value in data.items():
            if key == "meta":
                formattedata["meta"]["map"] = value[0]
                formattedata["meta"]["time"] = f"{value[1]//60}m {value[1]%60}s"
                continue
                
            if value[1] not in formattedata.keys():
                formattedata[value[1]] = {
                "playerinfo": {},
                "teaminfo": {"score":0},
                }
            formattedata[value[1]]["playerinfo"][key] = {"score":value[0],"kills":value[2],"deaths":value[3]}
            formattedata[value[1]]["teaminfo"]["score"] += value[0]
    embed = discord.Embed(
        title=f"Server status for {context['serveridnamelinks'][serverid]}",
        # description="This is a **test embed** with multiple customizations!",
        color=0xff70cb,
    )
    embed.add_field(name="Map", value=f"\u200b {formattedata['meta']['map']}", inline=True)
    embed.add_field(name="Players", value=f"\u200b {len(data)-1} players online", inline=True)
    embed.add_field(name="Time left", value=f"\u200b {formattedata['meta']['time']}", inline=True)
    sortedteams = sorted([team for team in formattedata.keys() if team != "meta"], key=lambda x: formattedata[x]["teaminfo"]["score"], reverse=True)
    sortedvalues = {}
    for team in sortedteams:
        sortedvalues[team] = formattedata[team]
    for team in sortedvalues.keys():
        if team == "meta":
            continue
        embed.add_field(name=f"> *Team {team}*", value=f"\u200b Score: {formattedata[team]['teaminfo']['score']} | Players: {len(formattedata[team]['playerinfo'])}", inline=False)
        for player in sorted(formattedata[team]["playerinfo"].keys(), key=lambda x: formattedata[team]["playerinfo"][x]["score"], reverse=True):
            embed.add_field(name=f"\u200b \u200b \u200b \u200b \u200b \u200b {player}", value=f"\u200b \u200b \u200b \u200b \u200b \u200b \u200b Score: {formattedata[team]['playerinfo'][player]['score']} | Kills: {formattedata[team]['playerinfo'][player]['kills']} | Deaths: {formattedata[team]['playerinfo'][player]['deaths']}", inline=False)
    return embed

        
        
    
        
    return f"```{data}```"
    

@bot.slash_command(name="bindglobalchannel", description="Bind a global channel to the bot")
async def bind_global_channel(
    ctx,
    channel: Option(
        discord.TextChannel, "The channel to bind to", required=True
    )):
    global context
    guild = ctx.guild
    if guild.id != context["activeguild"]:
        await ctx.respond("This guild is not the active guild.", ephemeral=True)
        return
    if ctx.author.id not in context["RCONallowedusers"]:
        await ctx.respond("You are not allowed to use this command.", ephemeral=True)
        return
    if channel.id in context["serverchannelidlinks"].values():
        await ctx.respond("This channel is already bound to a server.", ephemeral=True)
        return
    context["globalchannelid"] = channel.id
    savecontext()
    await ctx.respond(f"Global channel bound to {channel.name}.", ephemeral=True)




@bot.slash_command(name="rcon", description="Send an RCON command to a server")
async def rcon_command(
    ctx,
    cmd: Option(str, "The command to send"),
    servername: Option(
        str,
        "The servername (* for all, omit for current channel's server)",
        required=False,
    ) = None,
):
    await ctx.defer() #only add if needed :(
    print(
        "rcon command from",
        ctx.author.id,
        cmd,
        "to",
        servername if servername is not None else "Auto",
    )

    global context, discordtotitanfall
    if ctx.author.id not in context["RCONallowedusers"]:
        await ctx.respond("You are not allowed to use RCON commands.", ephemeral=True)
        return
    # await ctx.respond(f"Command: {cmd}, Server: {servername if servername != None else 'current channels'}", ephemeral=True)
    allservers = False
    ids = []
    if (
        servername is None
        and ctx.channel.id in context["serverchannelidlinks"].values()
    ):
        for key, value in context["serverchannelidlinks"].items():
            if value == ctx.channel.id:
                serverid = key
                break
        else:
            await ctx.respond(
                "Server not bound to this channel, could not send command.",
                ephemeral=True,
            )
            return
        initdiscordtotitanfall(serverid)

        # message = await ctx.respond(
        #     f"Command added to queue for server: **{context['serveridnamelinks'][serverid]}**.",
        #     ephemeral=True,
        # )
        ids.append(random.randint(0, 100000000000))
        discordtotitanfall[serverid]["commands"].append(
            {"command": cmd, "id": ids[-1]}
        )

    elif servername == "*":
        for serverid in context["serverchannelidlinks"].keys():
            initdiscordtotitanfall(serverid)
            message = await ctx.respond(
            "Command added to queue for all servers.", ephemeral=True
        )
            allservers = True
            ids.append(random.randint(0, 100000000000))
            discordtotitanfall[serverid]["commands"].append({"command": cmd, "id": ids[-1]})
        return
        
    elif servername in context["serveridnamelinks"].values():
        for serverid, name in context["serveridnamelinks"].items():
            if name == servername:
                break
        else:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("Server not found.", ephemeral=True)
            return
        initdiscordtotitanfall(serverid)

        # message = await ctx.respond(
        #     f"Command added to queue for server: **{servername}**.", ephemeral=True
        # )
        ids.append(random.randint(0, 100000000000))
        discordtotitanfall[serverid]["commands"].append(
            {"command": cmd, "id": ids[-1]}
        )
    else:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Server not found.", ephemeral=True)
        return
    if allservers:
        await ctx.respond(
            f"Command sent to all servers.", ephemeral=True
        )
        return
    await returncommandfeedback(serverid, ids[-1], ctx)
    # i = 0
    # while i < 100:
    #     await asyncio.sleep(0.1)
    #     if not allservers:
    #         if str(ids[0]) in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys():
    #             await ctx.respond(
    #                 f"Command sent to server: **{context['serveridnamelinks'][serverid]}**." +f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(ids[0])]}```",
    #                 ephemeral=True,
    #             )
    #             break

    #     i += 1
    # else:
    #     await ctx.respond("Command response timed out.", ephemeral=True)

@bot.slash_command(
    name="rconchangeuserallowed",
    description="toggle if a user is allowed to use RCON commands",
)
async def rcon_add_user(ctx, user: Option(discord.User, "The user to add")):
    global context
    return
    # check if the user is an admin on the discord
    if user.id in context["RCONallowedusers"]:
        context["RCONallowedusers"].remove(user.id)
        savecontext()
        await ctx.respond(
            f"User {user.name} removed from RCON whitelist.", ephemeral=True
        )
    elif ctx.author.guild_permissions.administrator:
        context["RCONallowedusers"].append(user.id)
        savecontext()
        await ctx.respond(f"User {user.name} added to RCON whitelist.", ephemeral=True)
    else:
        await ctx.respond(
            "Only administrators can add users to the RCON whitelist.", ephemeral=True
        )


@bot.event
async def on_message(message):
    global  context, discordtotitanfall
    if message.author == bot.user:
        return
    if message.channel.id in context["serverchannelidlinks"].values():
        print("discord message recieved")
        serverid = [
            key
            for key, value in context["serverchannelidlinks"].items()
            if value == message.channel.id
        ][0]
        # if serverid not in messagestosend.keys():
        #     messagestosend[serverid] = []
        initdiscordtotitanfall(serverid)
        if (
            len(
                f"{message.author.nick if message.author.nick is not None else message.author.display_name}: [38;5;254m{message.content}"
            )
            > 240
        ):
            await message.channel.send("Message too long, cannot send.")
            return
        elif message.content == "":
            return
        discordtotitanfall[serverid]["messages"].append(
            {
                "id": message.id,
                "content": f"{message.author.nick if message.author.nick is not None else message.author.display_name}: [38;5;254m{message.content}",
            }
        )
        if discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 45: #server crash (likely)
            await reactomessages([message.id], serverid, "🔴"   )
        elif discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 5: #changing maps (likely)
            await reactomessages([message.id], serverid, "🟡"   )
        
        # messagestosend[serverid].append(
        #     f"{message.author.nick if message.author.nick is not None else message.author.display_name}: [38;5;254m{message.content}"
        # )


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

    @app.route("/getrunningservers", methods=["POST"])
    def getrunningservers():
        global discordtotitanfall
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on getrunningservers")
            return {"message": "invalid password"}
        print("getting running servers")
        output = {"message":"ok","servers":{}}
        for (key, value) in discordtotitanfall.items():
            output["servers"][key] = value["lastheardfrom"]
        return output
            


    @app.route("/stoprequests", methods=["POST"])
    def stoprequests():
        global stoprequestsforserver
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on stoprequests")
            return {"message": "invalid password"}
        serverid = data["serverid"]
        print("stopping requests for", serverid)
        stoprequestsforserver[serverid] = True
        return {"message": "ok"}

    @app.route("/askformessage", methods=["POST"])
    def askformessage():
        global context,  discordtotitanfall
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on askformessage")
            time.sleep(30)
            return {"message": "invalid password","texts": {}, "commands": {}, "time": "0"}
        serverid = data["serverid"]
        initdiscordtotitanfall(serverid)
        if "commands" in data.keys():
            for key, value in data["commands"].items():
                discordtotitanfall[serverid]["returnids"]["commandsreturn"][key] = value
        ids = list(data.keys())
        if "time" in data.keys():
            timesent = int(data["time"])
            # print(timesent, discordtotitanfall[serverid]["returnids"]["messages"].keys())
            if timesent in discordtotitanfall[serverid]["returnids"]["commands"].keys():
                del discordtotitanfall[serverid]["returnids"]["commands"][timesent]
            if timesent in discordtotitanfall[serverid]["returnids"]["messages"].keys():
                del discordtotitanfall[serverid]["returnids"]["messages"][timesent]
        if len (data.keys()) > 2:
            print(json.dumps(data, indent=4))
        # print(ids)
        asyncio.run_coroutine_threadsafe(reactomessages(list(ids), serverid), bot.loop)
        if serverid not in stoprequestsforserver.keys():
            stoprequestsforserver[serverid] = False
        timer = 0
        while timer < 50 and not stoprequestsforserver[serverid]:
            discordtotitanfall[serverid]["lastheardfrom"] = int(time.time())
            timer += 0.2
            if serverid in discordtotitanfall.keys() and (
                discordtotitanfall[serverid]["messages"] != []
                or discordtotitanfall[serverid]["commands"] != []
            ):
                texts = [
                    message["content"]
                    for message in discordtotitanfall[serverid]["messages"]
                ]
                textvalidation = [
                    str(message["id"])
                    for message in discordtotitanfall[serverid]["messages"]
                ]
                while len(textvalidation) < len(texts):
                    textvalidation.append("0")
                sendingcommands = [
                    command["command"]
                    for command in discordtotitanfall[serverid]["commands"]
                ]
                sendingcommandsids = [
                    str(command["id"])
                    for command in discordtotitanfall[serverid]["commands"]
                ]
        
                discordtotitanfall[serverid]["messages"] = []
                discordtotitanfall[serverid]["commands"] = []
                now = int(time.time()*100)
                if len(textvalidation) > 0:
                    discordtotitanfall[serverid]["returnids"]["messages"][now] = textvalidation
                if len(sendingcommands) > 0:
                    # print("true")
                    discordtotitanfall[serverid]["returnids"]["commands"][now] = sendingcommandsids                
                # print(json.dumps(discordtotitanfall, indent=4))
                print("sending messages and commands to titanfall", texts, sendingcommands)
                # print({a: b for a, b in zip(texts, textvalidation)})
                # print((texts), (textvalidation))
                return {
                    "texts": {a: b for a, b in zip(textvalidation,texts)},
                    # "texts": "%&%&".join(texts),
                    "commands": {a: b for a, b in zip( sendingcommandsids,sendingcommands)},
                    # "textvalidation": "%&%&".join(textvalidation),
                    "time": str(now)
                }
            time.sleep(0.2)
        stoprequestsforserver[serverid] = False
        return {"texts": {}, "commands": {}, "time": "0"}

    @app.route("/servermessagein", methods=["POST"])
    def printmessage():
        global messageflush, lastmessage, messagecounter, context
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on printmessage")
            return {"message": "invalid password"}
        newmessage = {}
        if context["logging_cat_id"] == 0:
            return jsonify({"message": "no category bound"})
        if "servername" in data.keys():
            newmessage["servername"] = data["servername"]
        if "player" in data.keys():
            newmessage["player"] = data["player"]
        if (
            "serverid" not in data.keys()
            or "type" not in data.keys()
            or "timestamp" not in data.keys()
            or "messagecontent" not in data.keys()
        ):
            print("invalid message request recieved (not all params supplied)")
            return {
                    "message": "missing paramaters (type, timestamp, messagecontent, serverid)"
                }
            
        if "player" not in data.keys() and data["type"] < 3:
            data["type"] +=2 #set the type to a one that does not need a player
        newmessage["serverid"] = data["serverid"]
        newmessage["type"] = data["type"]
        newmessage["timestamp"] = data["timestamp"]
        newmessage["globalmessage"] = data["globalmessage"] if "globalmessage" in data.keys() else False
        
        newmessage["messagecontent"] = data["messagecontent"]
        if not newmessage["globalmessage"]:
            print("message request from", newmessage["serverid"], newmessage["servername"])
        else:
            print("global message request from", newmessage["serverid"], newmessage["servername"])
        messageflush.append(newmessage)

        messagecounter += 1
        lastmessage = time.time()

        if  newmessage["serverid"] not in context["serveridnamelinks"]:
            context["serveridnamelinks"][newmessage["serverid"]] = newmessage["servername"]
            savecontext()

        if newmessage["serverid"] not in context["serverchannelidlinks"].keys():
            # Get guild and category
            guild = bot.get_guild(context["activeguild"])
            category = guild.get_channel(context["logging_cat_id"])

        return {"message": "success"}

    serve(app, host="0.0.0.0", port=3451, threads=60)  # prod
    #app.run(host="0.0.0.0", port=3451)  #dev


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


async def reactomessages(messages, serverid, emoji = "🟢"):
    # print(messages,"wqdqw")
    for message in messages:
        # print("run")
        if message == "serverid" or message == "commands" or message == "time" or message == "password":
            continue
        # print("run2")
        # print(message,"owo")
        message = await bot.get_channel(
            context["serverchannelidlinks"][serverid]
        ).fetch_message(int(message))
        # print("reacting to message")
        # if the bot has reacted with "🔴" remove it.
        # if "🔴" in [reaction.emoji for reaction in message.reactions] or "🟡" in [reaction.emoji for reaction in message.reactions]:
        #     await message.clear_reactions()
        await message.add_reaction(emoji)


async def changechannelname(guild, servername, serverid):
    global context
    print("Changing channel name...")
    channel = guild.get_channel(context["serverchannelidlinks"][serverid])
    await channel.edit(name=servername)
    context["serveridnamelinks"][serverid] = servername
    savecontext()

    # return channel


def messageloop():
    global messageflush, lastmessage,discordtotitanfall, context
    addflag = False
    while True:
        try:
            # check if any uncreated channels exist
            if (time.time() - lastmessage > 0.5 and len(messageflush) > 0) or len(
                str(messageflush)
            ) > 1500:
                for message in messageflush:
                    if (
                        message["serverid"]
                        not in context["serverchannelidlinks"].keys()
                        and not addflag
                    ):
                        addflag = True
                        guild = bot.get_guild(context["activeguild"])
                        category = guild.get_channel(context["logging_cat_id"])
                        asyncio.run_coroutine_threadsafe(
                            createchannel(
                                guild,
                                category,
                                message["servername"],
                                message["serverid"],
                            ),
                            bot.loop,
                        )
                        time.sleep(10)
                addflag = False
                for message in messageflush:
                    if (
                        message["serverid"] in context["serverchannelidlinks"].keys()
                        and message["servername"]
                        not in context["serveridnamelinks"].values()
                        and not addflag
                    ):
                        addflag = True
                        guild = bot.get_guild(context["activeguild"])
                        asyncio.run_coroutine_threadsafe(
                            changechannelname(
                                guild, message["servername"], message["serverid"]
                            ),
                            bot.loop,
                        )
                addflag = False
                # channel = bot.get_channel(
                #     context["serverchannelidlinks"][messageflush[0]["serverid"]]
                # )
                output = {}
                messageflush = sorted(messageflush, key=lambda x: x["timestamp"])
                for message in messageflush:
                    if message["serverid"] not in output.keys() and not message["globalmessage"]:
                        output[message["serverid"]] = []
                    elif message["globalmessage"] and context["globalchannelid"] not in output.keys():
                        output[context["globalchannelid"]] = []
                    if ("\033[") in message["messagecontent"]:
                        print("colour codes found in message")
                        while "\033[" in message["messagecontent"]:
                            startpos = message["messagecontent"].index("\033[")
                            endpos = (
                                message["messagecontent"][startpos:].index("m")
                                + startpos
                            )
                            message["messagecontent"] = (
                                message["messagecontent"][:startpos]
                                + message["messagecontent"][endpos + 1 :]
                            )
                    if message["type"] == 1:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(
                            f"**{message['player']}**:  {message['messagecontent']}"
                        )
                        print(f"**{message['player']}**:  {message['messagecontent']}")
                    elif message["type"] == 2:
                        # print("2")
                        # output.append(f"meow")
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(
                            f"""```{message["player"]} {message["messagecontent"]}```"""
                        )
                        print(
                            (
                                f"""```{message["player"]} {message["messagecontent"]}```"""
                            )
                        )
                    elif message["type"] == 3:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(f"{message['messagecontent']}")
                        print(f"{message['messagecontent']}")
                    elif message["type"] == 4:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(f"```{message['messagecontent']}```")
                        print(f"```{message['messagecontent']}```")

                    else:
                        print("type of message unkown")
                    print("\033[0m", end="")
                for serverid in output.keys():
                    if serverid not in context["serverchannelidlinks"].keys() and serverid != context["globalchannelid"]:
                        print("channel not not in bots known channels")
                        continue
                    channel = bot.get_channel(context["serverchannelidlinks"][serverid]) if serverid != context["globalchannelid"] else bot.get_channel(context["globalchannelid"])
                    if channel is None:
                        print("channel not found")
                        continue

                    asyncio.run_coroutine_threadsafe(
                    channel.send("\n".join(output[serverid])), bot.loop
                )
                messageflush = []
                lastmessage = time.time()
            now = int(time.time()*100)
            for serverid in discordtotitanfall.keys():
                iterator = 0
                while iterator < len(discordtotitanfall[serverid]["returnids"]["messages"].keys()):
                    key = list(discordtotitanfall[serverid]["returnids"]["messages"].keys())[iterator]
                    value = [int(x) for x in discordtotitanfall[serverid]["returnids"]["messages"][key]]
                    # print("key",key)
                    iterator += 1

                    if int(key) < now-300:
                        # print("running this")
                        asyncio.run_coroutine_threadsafe(reactomessages(value, serverid, "🟡"), bot.loop)
                        del discordtotitanfall[serverid]["returnids"]["messages"][key]
                        iterator -= 1


        except AttributeError as e:
            time.sleep(3)
            print("bot not ready", e)
        time.sleep(0.1)


def savecontext():
    global context
    print("saving")
    with open("./data/" + channel_file, "w") as f:
        json.dump(context, f, indent=4)


def initdiscordtotitanfall(serverid):
    global discordtotitanfall
    if serverid not in discordtotitanfall.keys():
        discordtotitanfall[serverid] = {"messages": [], "commands": []}
    if "messages" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["messages"] = []
    if "commands" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["commands"] = []
    if "returnids" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["returnids"] = {"messages": {}, "commands": {}, "commandsreturn": {}}
    if "lastheardfrom" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["lastheardfrom"] = 0

def getchannelidfromname(name,ctx):
    for key, value in context["serveridnamelinks"].items():
        if value == name:
            return key
    if ctx.channel.id in context["serverchannelidlinks"].values():
        for key, value in context["serverchannelidlinks"].items():
            if value == ctx.channel.id:
                return key
            
async def returncommandfeedback(serverid, id, ctx,overridemsg = None):
    i = 0
    while i < 100:
        await asyncio.sleep(0.1)
        if str(id) in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys():
            if overridemsg:
                realmessage = overridemsg(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)], serverid)
            await ctx.respond(
                f"Command sent to server: **{context['serveridnamelinks'][serverid]}**." +f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]}```" if overridemsg is None else "",embed=realmessage if overridemsg is not None else None,
                ephemeral=True,
            )
            break

        i += 1
    else:
        await ctx.respond("Command response timed out.", ephemeral=True)

threading.Thread(target=messageloop).start()
threading.Thread(target=recieveflaskprintrequests).start()



bot.run(TOKEN)
