import asyncio
import json
import os
import threading
import time
import random
from discord.commands import Option

# import inspect
from flask import Flask, jsonify, request
from waitress import serve
from datetime import datetime
import discord
from discord import Option

import sqlite3


def notifydb():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS joinnotify (
            discordidnotify INTEGER,
            uidnotify INTEGER,
            PRIMARY KEY (discordidnotify, uidnotify)
            )"""
    )
    tfdb.commit()
    tfdb.close()
def joincounterdb():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS joincounter (
            uid INTEGER,
            serverid INTEGER,
            count INTEGER,
            PRIMARY KEY (uid, serverid)
            )"""
    )
    tfdb.commit()
    tfdb.close()
def playtimedb():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS playtime (
            id INTEGER PRIMARY KEY,
            playeruid INTEGER,
            joinatunix INTEGER,
            leftatunix INTEGER,
            endtype INTEGER,
            serverid INTEGER,
            scoregained INTEGER,
            titankills INTEGER,
            pilotkills INTEGER,
            npckills INTEGER,
            deaths INTEGER,
            map TEXT
            )"""
    )
    tfdb.commit()
    tfdb.close()
def playeruidnamelink():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS uidnamelink (
            id INTEGER PRIMARY KEY,
            playeruid INTEGER,
            playername TEXT
            )"""
    )
    tfdb.commit()
    tfdb.close()

# import importlib


# this whole thing is a mess of global varibles, jank threading and whatever, but it works just fine :)
# (I never bothered much with coding style)

messageflush = []
messageflushnotify = []
lastmessage = 0
Ijuststarted = time.time()


log_file = "logs.txt"
if not os.path.exists("./data/" + log_file):
    with open("./data/" + log_file, "w") as f:
        f.write("")
realprint = print
def print(*message, end="\n"):
    message = " ".join([str(i) for i in message])
    if len(message) < 1000000:
        with open("./data/" + log_file, "a") as file:
            file.write(
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                + ": "
                + str(message)
                + "\n"
            )
    realprint(message, end=end)
print("running discord logger bot")
lastrestart = 0
messagecounter = 0
SLEEPTIME_ON_FAILED_COMMAND = 2.5
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True  
intents.presences = True

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "0")
SHOULDUSEIMAGES = os.getenv("DISCORD_BOT_USE_IMAGES", "0")
SHOULDUSETHROWAI = os.getenv("DISCORD_BOT_USE_THROWAI", "1")
LOCALHOSTPATH = os.getenv("DISCORD_BOT_LOCALHOST_PATH","localhost")
DISCORDBOTAIUSED = os.getenv("DISCORD_BOT_AI_USED","deepseek-r1")
DISCORDBOTLOGSTATS = os.getenv("DISCORD_BOT_LOG_STATS","1")
SERVERPASS = os.getenv("DISCORD_BOT_PASSWORD", "*")

if DISCORDBOTLOGSTATS == "1":
    print("stats logging enabled")
    notifydb()
    playtimedb()
    playeruidnamelink()
    joincounterdb()
    

if SHOULDUSEIMAGES == "1":
    print("Images enabled")
    import io
    from PIL import Image
    import numpy as np
    from sklearn.cluster import MeanShift, estimate_bandwidth
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
    "commands": {},
}
serverchannels = []
if not os.path.exists("./data"):
    os.makedirs("./data")
channel_file = "channels.json"
command_file = "commands.json"


if os.path.exists("./data/" + channel_file):
    with open("./data/" + channel_file, "r") as f:
        tempcontext = json.load(f)
        for key in tempcontext.keys():
            context[key] = tempcontext[key]
else:
    context["logging_cat_id"] = 0
    context["activeguild"] = 0
    print("Channel file not found, using default channel ID 0.")
if os.path.exists("./data/" + command_file):
    with open("./data/" + command_file, "r") as f:
        context["commands"] = json.load(f)
        print("Command file found, using commands.")
        for command in context["commands"].keys():
            print(f"{command} ", end="")
else:
    context["commands"] = {}
    print("Command file not found, using NO (added) commands.")
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
        await ctx.respond("Logging is already bound to a category.", ephemeral=False)
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
        ephemeral=False,
    )
if DISCORDBOTLOGSTATS == "1":
    # @bot.slash_command(
    #     name="getplayerhours",
    #     description="Get a player's playtime",
    # )
    # async def getplayerhours(ctx, name: Option(str, "The playername/uid to Query")):
    @bot.slash_command(
        name="whois",
        description="Get a player's Aliases",
    )
    async def whois(ctx,name: Option(str, "The playername/uid to Query")):
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT playeruid, playername FROM uidnamelink")
        data = c.fetchall()
        if not data:
            tfdb.commit()
            tfdb.close()
            await ctx.respond("No players in the database", ephemeral=False)
            return
        data = [{"name": x[1], "uid": x[0]} for x in data]
        data = sorted(data, key=lambda x: len(x["name"]))

        data = [x for x in data if name.lower() in x["name"].lower()]
        if len(data) == 0:
            c.execute("SELECT playeruid FROM uidnamelink WHERE playeruid = ?",(name,))
            output = c.fetchone()
            if not output:
                tfdb.commit()
                tfdb.close()
                await ctx.respond("No players found", ephemeral=False)
    
                return
            output = {"uid":output[0]}
        player = data[0]
        c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC",(player["uid"],))
        data = c.fetchall()
        data = [f"{x[0]}" for y,x in enumerate(data)]
        tfdb.commit()
        tfdb.close()
        embed = discord.Embed(
            title=f"Aliases for uid {player['uid']}",
            color=0xff70cb,
            description=f"Most recent to oldest",
        )
        for y,x in enumerate( data):
            embed.add_field(name=f"Alias {y+1}:", value=f"\u200b {x}", inline=False)
        await ctx.respond(embed=embed, ephemeral=False)
        
        # await ctx.respond(data, ephemeral=False)
    @bot.slash_command(
        name="togglejoinnotify",
        description="Toggle if you are notified when a player joins",
    )
    async def togglejoinnotify(ctx,name: Option(str, "The playername to toggle")):
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT playeruid, playername FROM uidnamelink")
        data = c.fetchall()
        if not data:
            tfdb.commit()
            tfdb.close()
            await ctx.respond("No players in the database", ephemeral=True)
            return
        data = [{"name": x[1], "uid": x[0]} for x in data]
        data = sorted(data, key=lambda x: len(x["name"]))

        data = [x for x in data if name.lower() in x["name"].lower()]
        if len(data) == 0:
            tfdb.commit()
            tfdb.close()
            await ctx.respond("No players found", ephemeral=True)
            return
        player = data[0]
        c.execute("SELECT * FROM joinnotify WHERE discordidnotify = ? AND uidnotify = ?", (ctx.author.id,player["uid"]))
        data = c.fetchone()
        if data is None:
            c.execute("INSERT INTO joinnotify (discordidnotify, uidnotify) VALUES (?,?)",(ctx.author.id,player["uid"]))
            await ctx.respond(f"{player['name']} added to notify list", ephemeral=True)
        else:
            c.execute("DELETE FROM joinnotify WHERE discordidnotify = ? AND uidnotify = ?", (ctx.author.id,player["uid"]))
            await ctx.respond(f"{player['name']} removed from notify list", ephemeral=True)
        tfdb.commit()
        tfdb.close()
        

@bot.slash_command(name="help", description="Show help for commands")
async def help(
    ctx,
    command: Option(str, "The command to get help for", required=False,choices = list(context["commands"].keys()))
):
    global context
    print("help requested")
    if command is None:
        embed = discord.Embed(
            title="Help",
            description="Use /help <command> to get help for a specific command",
            color=0xff70cb,
        )
        for key in context["commands"].keys():
            embed.add_field(name=key, value=context["commands"][key]["description"], inline=False)
        embed.add_field(name="whois", value="Get somones aliases", inline=False)
        embed.add_field(name="togglejoinnotify", value="Toggle notifying on a player joining / leaving", inline=False)
        if SHOULDUSETHROWAI == "1":
            embed.add_field(name="thrownonrcon", value="Throw a player, after being persuasive", inline=False)
        await ctx.respond(embed=embed)
    else:
        defaults = {"description": "No description available", "parameters": [], "rcon": False, "commandparaminputoverride": {}, "outputfunc": None, "regularconsolecommand": False}
        embed = discord.Embed(
            title=command,
            description=context["commands"][command]["description"],
            color=0xff70cb,
        )
        mergeddescriptions = {**defaults, **context["commands"][command]}
        for key in mergeddescriptions.keys():
            embed.add_field(name=key, value=f"```json\n{json.dumps(mergeddescriptions[key],indent=4)}```", inline=False)
        await ctx.respond(embed=embed)

# sanction command. expiry, playername, reason, and a choice bettween ban or mute must be provided

# @bot.slash_command(name="sanction", description="Sanction a player")
# async def sanction(
#     ctx,
#     playername: str,
#     reason: str,
#     sanctiontype: Option(
#         str, "The type of sanction to apply", choices=["mute", "ban"]
#     ),
#     expiry: Option(str, "The expiry time of the sanction in format yyyy-mm-dd, omit is forever") = None,
#     servername: Option(
#         str, "The servername (omit for current channel's server)", required=False
#     ) = None,
# ):
#     global context, discordtotitanfall

#     if ctx.author.id not in context["RCONallowedusers"]:
#         await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#         return
#     if expiry == None: expiry = ""
#     commandstring = f"!sanctionban {playername} -expire {expiry} -reason {reason} -type {sanctiontype} -issuer {ctx.author.name}"
#     print(commandstring)
#     print("sanction command from", ctx.author.id, "to", playername)
#     serverid = getchannelidfromname(servername,ctx)
#     if serverid is None:
#         await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#         await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
#         return
#     await ctx.defer()
    
    
#     await returncommandfeedback(*sendrconcommand(serverid,commandstring), ctx, sanctionoverride)

def sanctionoverride(data, serverid,statuscode):
    embed = discord.Embed(
        title="Sanction Result",
        color=0xff70cb,
    )

    try:
        embed.add_field(name="Targeted Player", value=f"\u200b {data['playername']}", inline=False)
        embed.add_field(name="Sanction Type", value=f"\u200b {data['Sanctiontype']}", inline=False)
        embed.add_field(name="Sanction Reason", value=f"\u200b {data['reason']}", inline=False)
        embed.add_field(name="Sanction Expiry", value=f"\u200b {data['expire']}", inline=False)
        embed.add_field(name="Targeted player UID", value=f"\u200b {data['UID']}", inline=False)
        embed.add_field(name="Sanction Issuer", value=f"\u200b {data['issueruid']}", inline=False)
    except:
        embed.add_field(name="Response", value=f"\u200b {data}", inline=False)
    return embed

# @bot.slash_command(name="getuid", description="Get a player's UID")
# async def getuid(
#     ctx,
#     playername: Option(str, "The playername to get the UID of"),
#     servername: Option(
#         str, "The servername (omit for current channel's server)", required=False
#     ) = None,
# ):
#     global context, discordtotitanfall

#     if not checkrconallowed(ctx.author):
#         await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#         return
#     print("getuid command from", ctx.author.id, "to", playername)
#     serverid = getchannelidfromname(servername,ctx)
#     if serverid is None:
#         await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#         await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
#         return
#     await ctx.defer()
#     await returncommandfeedback(*sendrconcommand(serverid,f"!getuid {playername}"), ctx)

# @bot.slash_command(name="playing", description="List the players on a server")
# async def playing(
#     ctx,
#     servername: Option(
#         str, "The servername (omit for current channel's server)", required=False
#     ) = None,
# ):
#     global context, discordtotitanfall
    
#     if servername is None and ctx.channel.id in context["serveridnamelinks"].values():
#         serverid = [
#             key
#             for key, value in context["serveridnamelinks"].items()
#             if value == ctx.channel.id
#         ][0]
#     elif ctx.channel.id in context["serverchannelidlinks"].values():
#         for key, value in context["serverchannelidlinks"].items():
#             if value == ctx.channel.id:
#                 serverid = key
#                 break
#     else:
#         await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#         await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
#         return
    
#     print("playing command from", ctx.author.id, "to", servername if servername is not None else "Auto")
#     await ctx.defer()
#     await returncommandfeedback(*sendrconcommand(serverid, "!playing"), ctx, listplayersoverride)

def listplayersoverride(data, serverid, statuscode):
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
                # formattedata["meta"]["time"] = f"<t:{int(time.time()+value[1])}:R>"
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
    if statuscode != 200:
        embed.add_field(name="Error", value=f"\u200b {data} {statuscode}", inline=False)
        return embed
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
        await ctx.respond("This guild is not the active guild.", ephemeral=False)
        return
    if ctx.author.id not in context["RCONallowedusers"]:
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return
    if channel.id in context["serverchannelidlinks"].values():
        await ctx.respond("This channel is already bound to a server.", ephemeral=False)
        return
    context["globalchannelid"] = channel.id
    savecontext()
    await ctx.respond(f"Global channel bound to {channel.name}.", ephemeral=False)




# @bot.slash_command(name="rcon", description="Send an RCON command to a server")
# async def rcon_command(
#     ctx,
#     cmd: Option(str, "The command to send"),
#     servername: Option(
#         str,
#         "The servername (* for all, omit for current channel's server)",
#         required=False,
#     ) = None,
# ):
#     #only add if needed :(
#     print(
#         "rcon command from",
#         ctx.author.id,
#         cmd,
#         "to",
#         servername if servername is not None else "Auto",
#     )

#     global context, discordtotitanfall
#     if ctx.author.id not in context["RCONallowedusers"]:
#         await ctx.respond("You are not allowed to use RCON commands.", ephemeral=False)
#         return
#     # await ctx.respond(f"Command: {cmd}, Server: {servername if servername != None else 'current channels'}", ephemeral=False)
#     allservers = False
#     ids = []
#     if (
#         servername is None
#         and ctx.channel.id in context["serverchannelidlinks"].values()
#     ):
#         for key, value in context["serverchannelidlinks"].items():
#             if value == ctx.channel.id:
#                 serverid = key
#                 break
#         else:
#             await ctx.respond(
#                 "Server not bound to this channel, could not send command.",
#                 ephemeral=False,
#             )
#             return
#         initdiscordtotitanfall(serverid)

#         # message = await ctx.respond(
#         #     f"Command added to queue for server: **{context['serveridnamelinks'][serverid]}**.",
#         #     ephemeral=False,
#         # )
#         ids.append(random.randint(0, 100000000000000))
#         discordtotitanfall[serverid]["commands"].append(
#             {"command": cmd, "id": ids[-1]}
#         )

#     elif servername == "*":
#         for serverid in context["serverchannelidlinks"].keys():
#             initdiscordtotitanfall(serverid)
#             message = await ctx.respond(
#             "Command added to queue for all servers.", ephemeral=False
#         )
#             allservers = True
#             ids.append(random.randint(0, 100000000000000))
#             discordtotitanfall[serverid]["commands"].append({"command": cmd, "id": ids[-1]})
#         return
        
#     elif servername in context["serveridnamelinks"].values():
#         for serverid, name in context["serveridnamelinks"].items():
#             if name == servername:
#                 break
#         else:
#             await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#             await ctx.respond("Server not found.", ephemeral=False)
#             return
#         initdiscordtotitanfall(serverid)

#         # message = await ctx.respond(
#         #     f"Command added to queue for server: **{servername}**.", ephemeral=False
#         # )
#         ids.append(random.randint(0, 100000000000000))
#         discordtotitanfall[serverid]["commands"].append(
#             {"command": cmd, "id": ids[-1]}
#         )
#     else:
#         await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#         await ctx.respond("Server not found.", ephemeral=False)
#         return
#     if allservers:
#         await ctx.respond(
#             f"Command sent to all servers.", ephemeral=False
#         )
#         return
#     await ctx.defer()
#     await returncommandfeedback(serverid, ids[-1], ctx)
#     # i = 0
#     # while i < 100:
#     #     await asyncio.sleep(0.1)
#     #     if not allservers:
#     #         if str(ids[0]) in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys():
#     #             await ctx.respond(
#     #                 f"Command sent to server: **{context['serveridnamelinks'][serverid]}**." +f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(ids[0])]}```",
#     #                 ephemeral=False,
#     #             )
#     #             break

#     #     i += 1
#     # else:
#     #     await ctx.respond("Command response timed out.", ephemeral=False)

@bot.slash_command(
    name="rconchangeuserallowed",
    description="toggle if a user is allowed to use RCON commands",
)
async def rcon_add_user(ctx, user: Option(discord.User, "The user to add")):
    global context
    # return
    # check if the user is an admin on the discord
    if user.id in context["RCONallowedusers"]:
        context["RCONallowedusers"].remove(user.id)
        savecontext()
        await ctx.respond(
            f"User {user.name} removed from RCON whitelist.", ephemeral=False
        )
    elif ctx.author.guild_permissions.administrator:
        context["RCONallowedusers"].append(user.id)
        savecontext()
        await ctx.respond(f"User {user.name} added to RCON whitelist.", ephemeral=False)
    else:
        await ctx.respond(
            "Only administrators can add users to the RCON whitelist.", ephemeral=False
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
            > 240222
        ):
            await message.channel.send("Message too long, cannot send.")
            return
        if message.content != "":
            print(f"{message.author.nick if message.author.nick is not None else message.author.display_name}: {message.content}")
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
        if message.attachments and SHOULDUSEIMAGES == "1":
            print("creating image")
            image = await createimage(message)
            await returncommandfeedback(*sendrconcommand(serverid,f"!sendimage {' '.join(image)}"), message, iscommandnotmessage = False)
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
                discordtotitanfall[serverid]["returnids"]["commandsreturn"][key] = getjson(value)
        ids = list(data.keys())
        if "time" in data.keys():
            timesent = int(data["time"])
            # print(timesent, discordtotitanfall[serverid]["returnids"]["messages"].keys())
            if timesent in discordtotitanfall[serverid]["returnids"]["commands"].keys():
                del discordtotitanfall[serverid]["returnids"]["commands"][timesent]
            if timesent in discordtotitanfall[serverid]["returnids"]["messages"].keys():
                del discordtotitanfall[serverid]["returnids"]["messages"][timesent]
        if len (data.keys()) > 2:
            pass
            # realprint(json.dumps(data, indent=4))
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
        newmessage["metadata"] = {"type": None}
        #print(list(data.keys()))
        if "metadata" in data.keys() and data["metadata"] != "None":
            data["metadata"] = getjson(data["metadata"])
            newmessage["metadata"] = data["metadata"]
            if data["metadata"]["type"] == "connect":
                onplayerjoin(data["metadata"]["uid"],data["serverid"],data["player"])
            elif data["metadata"]["type"] == "disconnect":
                onplayerleave(data["metadata"]["uid"],data["serverid"])
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
    normalized_servername = servername.lower().replace(" ", "-")
    # check if channel name already exists, if so use that
    if any(normalized_servername == channel.name.lower() for channel in category.channels):
        channel = discord.utils.get(category.channels, name=normalized_servername)
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


def get_ordinal(i): #Shamelessly stolen
    SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
    # Adapted from https://codereview.stackexchange.com/questions/41298/producing-ordinal-numbers
    if 10 <= i % 100 <= 20:
        return 'th'
    else:
        return SUFFIXES.get(i % 10, 'th')
def getmessagewidget(metadata,serverid):
    output = ""
    if not metadata["type"]:
        pass
    elif metadata["type"] == "connect":
        pass
        uid = metadata["uid"]
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT count FROM joincounter WHERE uid = ? AND serverid = ?", (uid,serverid))
        data = c.fetchone()
        if data:
            data = data[0]
            output = f"\n({data}{get_ordinal(data)} time joining)"
        
            
        
    elif metadata["type"] == "disconnect":
        pass
    return output

def messageloop():
    global messageflush, lastmessage,discordtotitanfall, context,messageflushnotify
    addflag = False
    while True:
        try:
            # for each entry in messageflushnotify, dm the user
            if messageflushnotify:
                messageflushnotifycopy = messageflushnotify.copy()
                messageflushnotify = []
                for message in messageflushnotifycopy:
                    user = bot.get_user(message["userid"])
                    if user is None:
                        continue
                    asyncio.run_coroutine_threadsafe(
                        user.send(message["sendingmessage"]), bot.loop
                    )
        except Exception as e:
            time.sleep(3)
            print("bot not ready", e)
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
                        print(message)
                        print(list( context["serverchannelidlinks"].keys()),   message["serverid"])

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
                    messagewidget = getmessagewidget(message["metadata"],message["serverid"])
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
                            f"**{message['player']}**:  {message['messagecontent']} {messagewidget}"
                        )
                        print(f"**{message['player']}**:  {message['messagecontent']}")
                    elif message["type"] == 2:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(
                            f"""```{message["player"]} {message["messagecontent"]} {messagewidget}```"""
                        )
                        print(
                            (
                                f"""{message["player"]} {message["messagecontent"]}"""
                            )
                        )
                    elif message["type"] == 3:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(f"{message['messagecontent']} {messagewidget}")
                        print(f"{message['messagecontent']}")
                    elif message["type"] == 4:
                        output[message["serverid"] if not message["globalmessage"] else context["globalchannelid"]].append(f"```{message['messagecontent']} {messagewidget}```")
                        print(f"{message['messagecontent']}")

                    else:
                        print("type of message unkown")
                    realprint("\033[0m", end="")
                for serverid in output.keys():
                    if serverid not in context["serverchannelidlinks"].keys() and serverid != context["globalchannelid"]:
                        print("channel not in bots known channels")
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


        except Exception as e:
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
    for key, value in sorted(context["serveridnamelinks"].items(), key = lambda x: len(x[1])):
        if name and name.lower() in value.lower():
            print("default server overridden, sending to", value.lower())
            return key
    if ctx.channel.id in context["serverchannelidlinks"].values():
        for key, value in context["serverchannelidlinks"].items():
            if value == ctx.channel.id:
                return key
    print("could not find overridden server")
def sendrconcommand(serverid, command):
    global discordtotitanfall
    initdiscordtotitanfall(serverid)
    commandid = random.randint(0, 100000000000000)
    discordtotitanfall[serverid]["commands"].append(
            {"command": command, "id": commandid}
        )
    return serverid,commandid

def getjson(data): #ty chatgpt
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return getjson(parsed)
        except json.JSONDecodeError:
            return data
    elif isinstance(data, dict):
        return {key: getjson(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [getjson(item) for item in data]
    else:
        return data
    
def defaultoverride(data, serverid, statuscode):
    print(data)

    embed = discord.Embed(
    
        title=f"Command sent to server: *{context['serveridnamelinks'][serverid]}*",
        description=f"Status code: {statuscode}",
        color=0xff70cb,
    )
    if type(data) == str:
        embed.add_field(name="> Output:", value=f"```{data}```", inline=False)
    else:
        for key, value in data.items():
            embed.add_field(name=f"> {key}:", value=f"```json\n{json.dumps(value,indent=4)}```", inline=False)
    return embed

def resolveplayeruidfromdb(name,uidnameforce = None):
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT playeruid, playername FROM uidnamelink")
        data = c.fetchall()
        if not data:
            tfdb.commit()
            tfdb.close()
            return []

        data = [{"name": x[1], "uid": x[0]} for x in data]
        data = sorted(data, key=lambda x: len(x["name"]))

        data = [x for x in data if name.lower() in x["name"].lower()]
        if len(data) == 0 and uidnameforce == "name":
            return []
        if len(data) == 0 or uidnameforce == "uid":
            c.execute("SELECT playeruid, playername FROM uidnamelink WHERE playeruid = ?",(name,))
            output = c.fetchone()
            if not output:
                tfdb.commit()
                tfdb.close()
                
    
                return []
            data = {"uid":output[0], "name":output[1]}
        players = []
        for x in data:
            if x["uid"] not in players:
                players.append(x)

        tfdb.commit()
        tfdb.close()
        if len(players) == 0:
            return []
        return players
        

async def returncommandfeedback(serverid, id, ctx,overridemsg = defaultoverride, iscommandnotmessage = True):
    # print(serverid, id, ctx,overridemsg)
    if not overridemsg:
        overridemsg = defaultoverride
    i = 0
    while i < 200:
        await asyncio.sleep(0.05)
        if str(id) in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys():
            print(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)])
            if overridemsg:
                try:
                   
                    realmessage = overridemsg(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["output"], serverid,discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["statuscode"] )
           
                    if not realmessage:
                        overridemsg = None
                        return
                except Exception as e:
                    print("error in overridemsg", e)
                    overridemsg = None
                    try:
                        realmessage = defaultoverride(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["output"], serverid,discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["statuscode"] )
                        overridemsg = True
                    except Exception as e:
                        print("error in defaultoverride", e)
                        overridemsg = None
            if iscommandnotmessage:
                try:
                    await ctx.respond(
                        f"Command sent to server: **{context['serveridnamelinks'][serverid]}**." +f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]['output']}```" if overridemsg is None else "",embed=realmessage if overridemsg is not None else None,
                        ephemeral=False,
                    )
                except:
                    await ctx.reply(
                    f"Command sent to server: **{context['serveridnamelinks'][serverid]}**." +f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]['output']}```" if overridemsg is None else "",embed=realmessage if overridemsg is not None else None
                )
            else:
                await reactomessages([ctx.id], serverid, "🟢"   )
                
            break

        i += 1
    else:
        if iscommandnotmessage:
            try:
                await ctx.respond("Command response timed out - server is unresponsive", ephemeral=False)
            except:
                await ctx.reply("Command response timed out - server is unresponsive")

        else:
            await reactomessages([ctx.id], serverid, "🔴"   )

def checkrconallowed(author):
    global context
    if author.id not in context["RCONallowedusers"]:
        return False
    return True
# command slop

def create_dynamic_command(command_name, description = None, rcon = False, parameters = [], commandparaminputoverride = {}, outputfunc=None,regularconsolecommand=False):
    param_list = []
    for param in parameters:
        pname = param["name"]
        ptype = param["type"]
        pdesc = param.get("description", "")
        prequired = param.get("required", True)
        if "choices" in param and param["choices"]:
            pchoices = param["choices"]
            param_str = f'{pname}: Option({ptype}, "{pdesc}", choices={pchoices}, required={prequired})'
        else:
            param_str = f'{pname}: Option({ptype}, "{pdesc}", required={prequired})'
        if not prequired:
            param_str += " = None"
        param_list.append(param_str)
    servername_param = f'servername: Option(str, "The servername (omit for current channel\'s server)", required=False) = None' # ,choices=list(context["serveridnamelinks"].values())) = None
    param_list.append(servername_param)
    params_signature = ", ".join(param_list)
    # print(commandparaminputoverride)
    quotationmark = '"'
    if not regularconsolecommand:
        command_parts = [f'"!{command_name}"'] +  [f'{"("+quotationmark+commandparaminputoverride[param["name"]]+ " " +quotationmark  + "if bool("+param["name"]+") else "+quotationmark+quotationmark+") +"   if param["name"] in list(commandparaminputoverride.keys())else ""}(str({param["name"]}) if bool({param["name"]}) else "")' for param in parameters]
    else:
        command_parts =  [f'{"("+quotationmark+commandparaminputoverride[param["name"]] +" " +quotationmark  + "if bool("+param["name"]+") else "+quotationmark+quotationmark+") +"   if param["name"] in list(commandparaminputoverride.keys())else ""}(str({param["name"]}) if bool({param["name"]}) else "")' for param in parameters]
    if "appendtoend" in commandparaminputoverride.keys():
        command_parts.append(commandparaminputoverride["appendtoend"])
    # print(command_name,command_parts)
    command_expr = " + ' ' + ".join(command_parts)
    # print(command_expr)

    # print(parameters[0]["name"] if len(parameters) > 0 else None,list(commandparaminputoverride.keys()))

    dict_literal = "{" + ", ".join([f'"{p["name"]}": {p["name"]}' for p in parameters]) + "}"

    # print(dict_literal)
    outputfunc_expr = outputfunc.__name__ if outputfunc is not None else None
    # this code here HURTS MY HEAD but is incredibly cool in the way it works
    func_code = f'''
@bot.slash_command(name="{command_name}", description="{description}")
async def {command_name}(ctx, {params_signature}):
    if {rcon} and not checkrconallowed(ctx.author):
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return
    params = {dict_literal}
    print("DISCORDCOMMAND {command_name} command from", ctx.author.name, "with parameters:", params," to server:", servername)
    serverid = getchannelidfromname(servername, ctx)
    if serverid is None:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
        return
    await ctx.defer()
    command = {command_expr}
    print("Expression:",command)
    await returncommandfeedback(*sendrconcommand(serverid, command), ctx, {outputfunc_expr})
'''

    env = globals().copy()
    local_vars = {}
    exec(func_code, env, local_vars)
    return local_vars[command_name]


for command_name, command_info in context["commands"].items():
    create_dynamic_command(
        command_name=command_name,
        description=command_info["description"] if "description" in command_info else "No description available",
        parameters=command_info["parameters"] if "parameters" in command_info else [],
        rcon=command_info["rcon"] if "rcon" in command_info else False,
        commandparaminputoverride=command_info["commandparaminputoverride"] if "commandparaminputoverride" in command_info else {},
        outputfunc=globals().get(command_info["outputfunc"]) if "outputfunc" in command_info  and callable(globals().get(command_info["outputfunc"])) else None,
        regularconsolecommand=command_info["regularconsolecommand"] if "regularconsolecommand" in command_info else False,
    )
# THROW AI NON SLOP
if SHOULDUSETHROWAI == "1":
    print("ai throw enabled")
    lasttimethrown = {"specificusers":{},"globalcounter":0,"passes":{}}
    aibotmessageresponses = {}
    import requests
    @bot.slash_command(name="thrownonrcon", description="non rcon throw command")
    async def getuid(
        ctx,
        playername: Option(str, "Who gets thrown"),
        servername: Option(
            str, "The servername (omit for current channel's server)", required=False
        ) = None,
    ):
        
        global context, discordtotitanfall, lasttimethrown, aibotmessageresponses
        messagehistory = []
        keyaireply = random.randint(1,10000000000000)
        aibotmessageresponses[keyaireply] = []
        print("thrownonrcon command from", ctx.author.id, "to", playername)
        serverid = getchannelidfromname(servername, ctx)
        if serverid is None:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
            return
        if ctx.author.id in lasttimethrown["passes"].keys() and lasttimethrown["passes"][ctx.author.id] > time.time() - 120:
            print("has been allowed recently")
            await ctx.defer(ephemeral=False)
            await  returncommandfeedback(*sendrconcommand(serverid, f"!throw {playername}"), ctx)   
            return
        if lasttimethrown["globalcounter"] > time.time() - 60:
            await ctx.respond("This command is on cooldown, try again in " + str(int(60 - (time.time() - lasttimethrown["globalcounter"]))) + " seconds.", ephemeral=False)
            return

        await ctx.defer(ephemeral=False)
   
   
        original_message = await ctx.interaction.original_response()
        
        # Create a thread attached to the original message.
        await ctx.respond("creating thread", ephemeral=False)
        threade = await original_message.create_thread(
            name=f"throw request for {ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}",
            auto_archive_duration=60  
        )
        
        # Notify the channel that the thread has been created.
        # await ctx.followup.send(f"Thread created: {thread.mention}", ephemeral=False)

        # Set up waiting for messages from the original user in the thread.
        count = 0
        start_time = time.time()
            # response = requests.post("http://localhost:11434/api/generate", json = {"prompt": question,"model":"mistral","stream":True,"seed":0,"temperature":1,"options":{"num_predict":-1}})

        await threade.send('''Justify your use of this command:
- you have 5 messages to do so, after witch, it auto denys
- Only send one message at a time, and wait for response (it can take a while, ai is hard).
- messages that are being processed are marked by a 🟢
- if you fail, you must wait a short while before asking again.
- if you succeed, you are allowed to freely use the command for 120 seconds''')
        while count < 5 and (time.time() - start_time < 15 * 60):
            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == threade.id
            remaining_time = 15 * 60 - (time.time() - start_time)
            try:
                message = await bot.wait_for("message", timeout=remaining_time, check=check)
                await message.add_reaction("🟢")
                if count != len(aibotmessageresponses[keyaireply]):
                            await message.reply(f"Text not used, wait for response")
            except asyncio.TimeoutError:
                break

            messagehistory.append(f"{ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}: {message.content}")
            newline = "\n"
            historyinfo = (f'''
The users history of using this command, from oldest to newest is:
{newline.join(list(map(lambda a: f"button {a['button']}: Time since: {str(int((time.time()-a['timestamp'])//60)) + ' minutes ago' if (time.time()-a['timestamp'])  < 86400 else '> 1 day'} because {a['one_word_reason']}",list(filter(lambda a: time.time()-a["timestamp"] < 172800,lasttimethrown["specificusers"][ctx.author.id][-10:])))))}
''' if ctx.author.id in lasttimethrown["specificusers"].keys() and len(lasttimethrown["specificusers"][ctx.author.id]) > 1  else "")
            prompt = f'''<SYSTEM MESSAGE>
You are a AI model, choosing one of three choices, "allow_request", "deny_request" and "more_information_needed". You should also give a reason for your choice.
To inform your choices, you are given an array of user messages, in chronological order, formatted ["username: messagecontent",...], as such, you should place most importance on the later user past messages.
The user is asking to use a command on a titanfall 2 sever. this command throws a targeted player into the air, in the game Titanfall 2. Your role is to be skeptical that the user needs to use this command, due to the fact that it can be seen as unfair or even unfun by the targeted player.
If the user has a reason that you deem would bring value however, don't hesitate to press the "allow_request button". This will allow the command to be executed.
If you believe the user might make a good case to deserve using the command, with good reasoning, press "more_information_needed".
If you believe the user is trying to mislead you, is undeserving, is too rude, is trying to get a competitive advantage, or simply have the feeling of being powerful, press "deny_request".

You will be expected to press exactly one of those 3 choices after each request, and also give a one - two sentence reason as to why, and a single word reason for the choice.
In order to do this, format your output exactly like this, otherwise it will fail to be parsed.
"{{"reason":"YOUR_REASON_HERE","button":"YOUR_BUTTON_PRESSED","reasononeword":"ONE_WORD_REASON"}}"
For example:
"{{"reason":"I believe your reasoning to use /throw holds water. you provided a concise argument that clearly displayed your intentions with the command","button":"allow_request,"reasononeword":"coherent"}}"

"{{"reason":"I feel your arguments are flawed, and you intend to use this for other purposes than stated.","button":"deny_request","reasononeword":"misleading"}}"

"{{"reason":"You make a interesting point, however your points are not fully explained. could you expand upon why you think this would be comedic?","button":"more_information_needed","reasononeword":"incomplete"}}"

Lastly:
If you do not come to a conclusion after 5 messages from the user, the request will be denied.
KEEP RESPONSE BELOW 2000 CHARACTERS
The player that is targeted is "{playername}" (if this is "all", the user is attempting to throw EVERYONE. make this request need a VERY strong line of reasoning, however still intend to clear it up in 5 messages. (DO NOT BE AFRAID TO QUERY MORE INFORMATION)
The player that used this command is "{ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}"
{"The last time the user tried to use this command was: " + str(int(time.time()-lasttimethrown["specificusers"][ctx.author.id][-1]["timestamp"])) + " seconds ago, and you responded " + lasttimethrown["specificusers"][ctx.author.id][-1]["button"] +" due to " + lasttimethrown["specificusers"][ctx.author.id][-1]["one_word_reason"]if ctx.author.id in lasttimethrown["specificusers"].keys() else "This is the first time the user has tried to use this command. (since bot restart)"}
{historyinfo} 
base your leniance on this info too.
Here are the users message, after this system prompt ends.

after that array will be an array of your responses to these messages. this will be one shorter by 1, as a placeholder for your current message.

</SYSTEM MESSAGE>
user past messages:
{newline.join(messagehistory)}
your past responses:
{newline.join(list(map( lambda x: str(x) ,aibotmessageresponses[keyaireply])))}
'''             # TO BE DONE, SAY HOW MANY DENYS AND HOW MANY ALLOWS, AND HOW MANY WERE IN PAST HOUR. LEARN ABOUT SANDBOXING IMPLEMENT THE SHORT TIME WHITELIST, AND ALSO THE 60 SECONDS DENY
            # print(f'{"The last time the user tried to use this command was: " + str(time.time()-lasttimethrown["specificusers"][ctx.author.id][-1]["timestamp"]) + " seconds ago, and it was " + lasttimethrown["specificusers"][ctx.author.id][-1]["button"] if ctx.author.id in lasttimethrown["specificusers"].keys() else "This is the first time the user has tried to use this command. since bot restart"}')
            print(prompt)
            thready = threading.Thread(target=respondtotext, daemon=True, args=(message,prompt,keyaireply))
            thready.start()
            count += 1

            while count != len(aibotmessageresponses[keyaireply]):
                await asyncio.sleep(0.3)
                # print(aibotmessageresponses)
            if aibotmessageresponses[keyaireply][-1]["button"] == "deny_request":
                if ctx.author.id not in lasttimethrown["specificusers"].keys():
                    lasttimethrown["specificusers"][ctx.author.id] = []
                lasttimethrown["specificusers"][ctx.author.id].append({"button":"deny_request","timestamp":time.time(),"one_word_reason":aibotmessageresponses[keyaireply][-1]["reasononeword"]})
                await threade.send("# request denied, run the command again, and try be more persuasive :)")
                # await ctx.respond("request denied", ephemeral=False)
                del aibotmessageresponses[keyaireply]
                return
            elif aibotmessageresponses[keyaireply][-1]["button"] == "allow_request":
                if ctx.author.id not in lasttimethrown["specificusers"].keys():
                    lasttimethrown["specificusers"][ctx.author.id] = []
                lasttimethrown["specificusers"][ctx.author.id].append({"button":"allow_request","timestamp":time.time(),"one_word_reason":aibotmessageresponses[keyaireply][-1]["reasononeword"]})
                lasttimethrown["passes"][ctx.author.id] = time.time()
                
                await threade.send("# request allowed, executing command")
                await returncommandfeedback(*sendrconcommand(serverid, f"!throw {playername}"), message)   
                del aibotmessageresponses[keyaireply]
                return
            elif aibotmessageresponses[keyaireply][-1]["button"] == "more_information_needed":
                print("more info needed", aibotmessageresponses[keyaireply][-1]["button"])
                pass
            # print("there")
        await threade.send("timeout, request denied")
        del aibotmessageresponses[keyaireply]
    def respondtotext(message,prompt,keyaireply):
        global aibotmessageresponses
        print("generating")
        try:
            # print(f"http://{LOCALHOSTPATH}:11434/api/generate")
            response = requests.post(f"http://{LOCALHOSTPATH}:11434/api/generate", json = {"prompt": prompt,"model":DISCORDBOTAIUSED,"stream":False,"keep_alive":"120m","seed":0,"temperature":1,"options":{"num_predict":-1}})
            print(response.json()["response"])
            output = response.json()["response"]
            output = output[output.index("</think>")+8:].strip()
            output = json.loads(output)
            aibotmessageresponses[keyaireply].append((output))
            print("done, responding")
        except Exception as e:
            print(e)
            output = {"button":"deny_request","reason":"ai broken. "+ str(e),"reasononeword":"broken"}
            aibotmessageresponses[keyaireply].append(output)
        asyncio.run_coroutine_threadsafe(aireplytouser(message,output),bot.loop)
        

    async def aireplytouser(message,output):
        await message.reply(f"**button pressed by AI:**```{output['button']}``` \n**Reason:** ```{output['reason']}```\n**Short reason:**```{output['reasononeword']}```")
# joinleave logging stuff
playercontext = {}
playerjoinlist = {}
def onplayerjoin(uid,serverid,nameof = False):
    global context,messageflushnotify,playerjoinlist
    print("joincommand")
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute("SELECT discordidnotify FROM joinnotify WHERE uidnotify = ?",(uid,))
    discordnotify = c.fetchall()
    c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",(uid,))
    # c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ?",(uid,))
    playernames = c.fetchall()
    if playernames:
        playernames = [x[0] for x in playernames]
    if nameof not in playernames or not playernames:
        c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(uid,nameof))
        tfdb.commit()
    if nameof:
        playername = nameof
    else:
        playername = f"Unknown user by uid {uid}"
    print(f"{uid}{playername}",playerjoinlist)
    if f"{uid}{playername}" in playerjoinlist.keys() and playerjoinlist[f"{uid}{playername}"]:
        print("already in list")
        return
    c.execute("SELECT count FROM joincounter WHERE uid = ?",(uid,))
    count = c.fetchone()
    if count:
        count = count[0] + 1
        c.execute("UPDATE joincounter SET count = ? WHERE uid = ? AND serverid = ?",(count,uid,serverid))
    else:
        c.execute("INSERT INTO joincounter (uid,serverid,count) VALUES (?,?,1)",(uid,serverid))
    tfdb.commit()

    
    if discordnotify:
        discordnotify = [x[0] for x in discordnotify]
    servername = context["serveridnamelinks"][serverid]

    playerjoinlist[f"{uid}{playername}"] = True
    for discordid in discordnotify:
        messageflushnotify.append(
            {
                "servername": servername,
                "player": playername,
                "userid": discordid,
                "sendingmessage": f"[JOINNOTIFY] {playername} has joined {servername}, disable this with /togglejoinnotify",
            }
        )
    tfdb.close()
    
    
    
    
def onplayerleave(uid,serverid):
    global context,messageflushnotify,playercontext
    print("leavecommand")
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute("SELECT discordidnotify FROM joinnotify WHERE uidnotify = ?",(uid,))
    discordnotify = c.fetchall()
    c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",(uid,))
    playername = c.fetchone()
    if playername:
        playername = playername[0]
    else:
        playername = f"Unkown user by uid {uid}"
    if discordnotify:
        discordnotify = [x[0] for x in discordnotify]
    servername = context["serveridnamelinks"][serverid]
    if f"{uid}{playername}" in playerjoinlist.keys() and not playerjoinlist[f"{uid}{playername}"]:
        return
    playerjoinlist[f"{uid}{playername}"] = False
    for discordid in discordnotify:
        messageflushnotify.append(
            {
                "servername": servername,
                "player": playername,
                "userid": discordid,
                "sendingmessage": f"[JOINNOTIFY] {playername} has left {servername}, disable this with /togglejoinnotify",
            }
        )
    tfdb.close()
    # if str(uid)+playername in playercontext.keys():
    #     savestats(playercontext[str(uid)+playername],1)
    #     playercontext[str(uid)+playername] = {}
    # if  playercontext[pinfo["uid"]+pinfo["name"]]


def savestats(stats,endtype):
    # 1 is normal, they just left
    # 2 is map change
    # 3 is server crash
    # 4 is tempory save
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    try:
        c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",(stats["uid"],))
        playernames = c.fetchall()
        if playernames:
            playernames = [x[0] for x in playernames]
        if stats["name"] not in playernames or not playernames:
            c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(stats["uid"],stats["name"]))
        if stats["idoverride"] != 0:
            c.execute("UPDATE playtime SET leftatunix = ?, endtype = ?, scoregained = ?, titankills = ?, pilotkills = ?, deaths = ? WHERE id = ?",(stats["endtime"],endtype,stats["score"],stats["titankills"],stats["pilotkills"],stats["deaths"],stats["idoverride"]))
            lastrowid = stats["idoverride"]
        else:
            c.execute("INSERT INTO playtime (playeruid,joinatunix,leftatunix,endtype,serverid,scoregained,titankills,pilotkills,npckills,deaths,map ) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(stats["uid"],stats["joined"],stats["endtime"],endtype,stats["serverid"],stats["score"],stats["titankills"],stats["kills"],stats["npckills"],stats["deaths"],stats["map"]))
            lastrowid = c.lastrowid
    except Exception as e:
        print("error in saving",e)
        return 0
    tfdb.commit()
    tfdb.close()
    return lastrowid
def playerpolllog(data,serverid,statuscode):
    Ithinktheplayerhasleft = 30
    global discordtotitanfall,playercontext,playerjoinlist
    # save who is playing on the specific server into playercontext.
    # dicts kind of don't support composite primary keys..
    # use the fact that theoretically one player can be on just one server at a time
    # playerid+playername = primary key. this is because of the edge case where people join one server on one account twice because.. well they do that sometimes
    # print(data,serverid,statuscode)
    map = data["meta"][0]
    now = int(time.time())
    # players = [lambda x: {"uid":x[0],"score":x[1][0],"team":x[1][1],"kills":x[1][2],"deaths":x[1][3],"name":x[1][4],"titankills":x[1][5],"npckills":x[1][6]} for x in list(filter(lambda x: x[0] != "meta",list(data.items())))]
    players = [{"uid":x[0], "score":x[1][0], "team":x[1][1], "kills":x[1][2], "deaths":x[1][3], "name":x[1][4], "titankills":x[1][5], "npckills":x[1][6]} for x in list(filter(lambda x: x[0] != "meta", list(data.items())))]
    #print("players",players)
    for pinfo in players:
        if pinfo["uid"]+pinfo["name"] in list(playercontext.keys()) and playercontext[pinfo["uid"]+pinfo["name"]] and ( playercontext[pinfo["uid"]+pinfo["name"]]["map"] != map or playercontext[pinfo["uid"]+pinfo["name"]]["serverid"] != serverid  ):
            playercontext[pinfo["uid"]+pinfo["name"]]["endtime"] = now
            print("saving-mapserver")
            savestats(playercontext[pinfo["uid"]+pinfo["name"]] ,2)
            playercontext[pinfo["uid"]+pinfo["name"]] = {}
            pass #SAVE SAVE SAVE
        if pinfo["uid"]+pinfo["name"] not in list(playercontext.keys()) or playercontext[pinfo["uid"]+pinfo["name"]] == {}:
            if now - Ijuststarted > 30:
                print("alternate join", pinfo["uid"]+pinfo["name"])
                onplayerjoin(pinfo["uid"],serverid,pinfo["name"])
            playercontext[pinfo["uid"]+pinfo["name"]] = {"joined":now,"map":map,"name":pinfo["name"],"uid":pinfo["uid"],"idoverride":0,"endtime":0,"serverid":serverid,"kills":0,"deaths":0,"titankills":0,"npckills":0,"score":0}
        # check if any data that requires a save has changed
            # on map change, we save before we overwrite. also we couuld try to return a thing, given stuff!
        playercontext[pinfo["uid"]+pinfo["name"]]["endtime"] = now
        playercontext[pinfo["uid"]+pinfo["name"]]["kills"] = pinfo["kills"]
        playercontext[pinfo["uid"]+pinfo["name"]]["deaths"] = pinfo["deaths"]
        playercontext[pinfo["uid"]+pinfo["name"]]["titankills"] = pinfo["titankills"]
        playercontext[pinfo["uid"]+pinfo["name"]]["npckills"] = pinfo["npckills"]
        playercontext[pinfo["uid"]+pinfo["name"]]["score"] = pinfo["score"]

        # playercontext[pinfo["uid"]+pinfo["name"]]["kills"] = pinfo["kills"]
    for key,pinfo in playercontext.items():
        if pinfo and  now -pinfo["endtime"] > Ithinktheplayerhasleft:
            # SAVE SAVE SAVE
            print("saving-left")
            onplayerleave(pinfo["uid"],serverid)
            playercontext[key] = {}
            savestats(pinfo,1)
        
    

def playerpoll():
    global discordtotitanfall,playercontext
    Ithinktheserverhascrashed = 180
    autosaveinterval = 180
    pinginterval = 20
    # if the player leaves and rejoins, continue their streak.
    # if the server does not respond for this time, assume it crashed.
    counter = 0
    while True:
        shouldIsave = True
        counter +=1
        
                    
                    
       # poll time
        # I want to iterate through all servers, and ask them what they are up too.
        for serverid,data in discordtotitanfall.items():
            if time.time() - data["lastheardfrom"] > Ithinktheserverhascrashed:
                pass #SAVE SAVE SAVE
                # the server has crashed, or is empty. assume all players left.
                # save all sql stuff related to this server.
                print("saving-crashempty")
                for key,pinfo in playercontext.items():
                    if pinfo != {} and pinfo["serverid"] == serverid:
                        lastrow = savestats(pinfo,3)
                        playercontext[key]["idoverride"] = lastrow # not sure if I want to wipe it so the save can be overwritten if server restarts to same map or not. it's fine.
                        playercontext[key] = {}
            # ask the server nicely who is playing
            else:
                shouldIsave = False
                asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,"!playingpoll"),"fake context",playerpolllog), bot.loop)
                # returncommandfeedback(*sendrconcommand(serverid,"!playingpoll"),"fake context",playerpolllog)
        if shouldIsave:
            if not counter % autosaveinterval*pinginterval:
                for key,pinfo in playercontext.items():
                    if pinfo != {}:
                        print("saving-autosave")
                        lastrow = savestats(pinfo,4)
                        playercontext[key]["idoverride"] = lastrow
        time.sleep(pinginterval)      
    # should poll for players on ALL servers every xyz seconds.
    # only do it on servers that have been active recently.
    # blah
    # this one just asks the server every so often, using a command.
    # then it calls commandresponseoverrideand does stuff!

# IMAGE SLOP PLEASE DON'T LOOK AT IT I HATE IT

async def createimage(message):
    for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif",".webp"]):
                    image_bytes = await attachment.read()
                    ascii_art = fitimage(image_bytes, output_width=80, ascii_char = "~", maxlen = 249)
                    lenarray = [len(s) for s in ascii_art]
                    length = min(lenarray)
                    if lenarray.count(length) > 1:
                        secondshortest = min(lenarray)
                    else:
                        secondshortest = min([x for x in lenarray if x != length])
                    for i in range(len(ascii_art)):
                        if len(ascii_art[i]) == length:
                            # print(length)
                            ascii_art[i] = ascii_art[i] + "\x1b[38;5;105m-" + (message.author.nick if message.author.nick is not None else message.author.display_name).replace(" ", "_")
                            length = -1
                        elif len(ascii_art[i]) == secondshortest:
                            ascii_art[i] = ascii_art[i] + "\x1b[38;5;105m-" + ("Image from discord").replace(" ", "_")
                            secondshortest = -1

                  
                    art_text = "\n".join(ascii_art)
                    # print(art_text) OUTPUT IT ON DISCORD
                    return ascii_art

def convansi(rgb):
    r, g, b = rgb
    r_val = int(r / 51)
    g_val = int(g / 51)
    b_val = int(b / 51)
    ansi_code = 16 + 36 * r_val + 6 * g_val + b_val
    return ansi_code

def fitimage(image_bytes, output_width=30, ascii_char="█",maxlen = 249):
    ascii_art = lotsofmathscreatingimage(image_bytes, output_width, ascii_char)
    length = max(len(s) for s in ascii_art)
    while length > maxlen:
        if (length - maxlen) > 200:
            output_width -= 10
        elif (length - maxlen) > 100:
            output_width -= 5
        output_width -= 1
        # print(output_width)
        ascii_art = lotsofmathscreatingimage(image_bytes, output_width, ascii_char)
        length = max(len(s) for s in ascii_art)
    return ascii_art

def lotsofmathscreatingimage(image_bytes, output_width=80, ascii_char="█", max_height=11):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_width, original_height = image.size
    computed_height = int((original_height / original_width) * output_width)
    if computed_height > max_height:
        output_height = max_height
        output_width = int((original_width / original_height) * max_height)
    else:
        output_height = computed_height
    output_width*=1.8
    output_width = int(output_width)
    image = image.resize((output_width, output_height), Image.LANCZOS)
    img_array = np.array(image)
    pixels = img_array.reshape((-1, 3))
    bandwidth = estimate_bandwidth(pixels, quantile=0.05, n_samples=100)
    if bandwidth <= 0:
        bandwidth = 10 
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    ms.fit(pixels)
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_
    label_to_ansi = {}
    for label, center in enumerate(cluster_centers):
        rgb = tuple(map(int, center))
        ansi = convansi(rgb)
        label_to_ansi[label] = ansi
    ascii_art = []
    idx = 0
    for row in range(output_height):
        row_chars = ""
        lastansi = None
        for col in range(output_width):
            pixel_label = labels[idx]
            ansi = label_to_ansi[pixel_label]
            if ansi != lastansi:
                colored_char = f"\x1b[38;5;{ansi}m{ascii_char}"
                lastansi = ansi
            else:
                colored_char = ascii_char
            row_chars += colored_char
            idx += 1
        ascii_art.append(row_chars)
    return ascii_art
if DISCORDBOTLOGSTATS == "1":
    threading.Thread(target=playerpoll).start()
threading.Thread(target=messageloop).start()
threading.Thread(target=recieveflaskprintrequests).start()



bot.run(TOKEN)
