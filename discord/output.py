# chat relay for tf|1 and tf|2 by dyslexi!
import asyncio
import json
import os
import threading
import time
import random
from PIL import Image, ImageDraw, ImageFont
import traceback
from discord.commands import Option
from io import BytesIO

import inspect
from flask import Flask, jsonify, request,send_from_directory
from waitress import serve
from discord.ext import commands, tasks
from datetime import datetime, timedelta,timezone
import discord
from discord import Option, OptionChoice
import requests
from rcon.source import Client
import sqlite3
import re
import aiohttp
from defs import *

def discorduidinfodb():
    global colourslink
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    # c.execute("DROP TABLE IF EXISTS discorduiddata")
    c.execute(
        """CREATE TABLE IF NOT EXISTS discorduiddata (
            discorduid INTEGER PRIMARY KEY,
            chosencolour STRING
            )"""
    )
    c.execute("SELECT discorduid, chosencolour FROM discorduiddata")
    output = c.fetchall()
    colourslink = {x[0]:eval(x[1]) if x[1] != "reset" else RGBCOLOUR  for x in output}
    print("COLOURSLINK",colourslink) 
    tfdb.commit()
    tfdb.close()
def specifickilltrackerdb():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS specifickilltracker (
            id INTEGER PRIMARY KEY,
            serverid               TEXT,
            attacker_z              REAL,
            attacker_x              REAL,
            attacker_y              REAL,
            victim_id               TEXT,
            victim_name             TEXT,
            victim_offhand_weapon_2 TEXT,
            attacker_titan          TEXT,
            map                     TEXT,
            attacker_offhand_weapon_1 TEXT,
            attacker_offhand_weapon_2 TEXT,
            victim_offhand_weapon_1 TEXT,
            attacker_weapon_3       TEXT,
            attacker_name           TEXT,
            match_id                TEXT,
            victim_titan            TEXT,
            distance                REAL,
            victim_current_weapon   TEXT,
            victim_z                REAL,
            attacker_weapon_2       TEXT,
            game_time               REAL,
            attacker_current_weapon TEXT,
            victim_weapon_3         TEXT,
            playeruid               TEXT,
            game_mode               TEXT,
            victim_x                REAL,
            attacker_weapon_1       TEXT,
            victim_weapon_1         TEXT,
            victim_weapon_2         TEXT,
            timeofkill              INTEGER,
            cause_of_death          TEXT,
            victim_y                REAL
        )"""
    )
    tfdb.commit()
    c.close()
    tfdb.close()
# def matchidtf1():
#     tfdb = sqlite3.connect("./data/tf2helper.db")
#     c = tfdb.cursor()
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS matchidtf1 (
#             matchid STRING,
#             serverid INTEGER,
#             map STRING,
#             time INTEGER,
#             PRIMARY KEY (matchid, serverid)
#             )"""
#     )
#     tfdb.commit()
#     tfdb.close()
def tf1matchplayers():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute("DROP TABLE IF EXISTS matchtf1")
    c.execute(
        """CREATE TABLE IF NOT EXISTS matchtf1 (
            matchid STRING,
            serverid INTEGER,
            map STRING,
            time INTEGER,
            playername STRING,
            playerip INTEGER,
            PRIMARY KEY (playername, playerip)
            )"""
    )
    tfdb.commit()
    tfdb.close()

def bantf1():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    # banid is because the bot automatically bans new names / ips
    c.execute(
        """CREATE TABLE IF NOT EXISTS banstf1 (
            id INTEGER PRIMARY KEY,
            banid INTEGER,
            ismute INTEGER, 
            banstart INTEGER,
            banend INTEGER,
            playerip STRING,
            playername STRING,
            reason STRING,
            banuploader STRING
            )"""
    )
    tfdb.commit()
    tfdb.close()

def matchid():
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS matchid (
            matchid STRING PRIMARY KEY,
            map STRING,
            time INTEGER,
            serverid INTEGER
            )"""
    )
    tfdb.commit()
    tfdb.close()

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
            playeruid INTEGER,
            serverid INTEGER,
            count INTEGER,
            PRIMARY KEY (playeruid, serverid)
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
            duration INTEGER,
            matchid STRING,
            map TEXT,
            timecounter INTEGER
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
            playername TEXT,
            lastseenunix INTEGER,
            firstseenunix INTEGER
            )"""
    )
    try:
        c.execute("ALTER TABLE uidnamelink ADD COLUMN firstseenunix INTEGER")
        c.execute("ALTER TABLE uidnamelink ADD COLUMN lastseenunix INTEGER") 
    except:pass
    tfdb.commit()
    tfdb.close()

# import importlib


# this whole thing is a mess of global varibles, jank threading and whatever, but it works just fine :)
# (I never bothered much with coding style)

messageflush = []
messageflushnotify = []
lastmessage = 0
Ijuststarted = time.time()

reactedyellowtoo = []


log_file = "logs"
if not os.path.exists("./data/" + log_file):
    with open("./data/" + log_file, "w") as f:
        f.write("")
realprint = print
def print(*message, end="\n"):
    message = " ".join([str(i) for i in message])
    if len(message) < 1000000 and False:
        with open("./data/" + log_file, "a") as file:
            file.write(
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                + ": "
                + str(message)
                + "\n"
            )
    realprint(f"[{inspect.currentframe().f_back.f_lineno}] {message}", end=end)
print("running discord logger bot")
lastrestart = 0
messagecounter = 0
SLEEPTIME_ON_FAILED_COMMAND = 2.5 #for when you are running multiple versions of the bot (like a dev version). if one bot cannot fulfill the command,
# the other bot that can has time too, instead of the first responding with failure
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
LEADERBOARDUPDATERATE = int(os.getenv("DISCORD_BOT_LEADERBOARD_UPDATERATE", "800"))
DISCORDBOTLOGCOMMANDS = os.getenv("DISCORD_BOT_LOG_COMMANDS", "1")
SERVERNAMEISCHOICE = os.getenv("DISCORD_BOT_SERVERNAME_IS_CHOICE", "0")
SANCTIONAPIBANKEY = os.getenv("SANCTION_API_BAN_KEY", "0")
TF1RCONKEY = os.getenv("TF1_RCON_PASSWORD", "pass") 
USEDYNAMICPFPS = os.getenv("USE_DYNAMIC_PFPS","1")
PFPROUTE = os.getenv("PFP_ROUTE","https://raw.githubusercontent.com/Dys-lexi/TitanPilotprofiles/main/avatars/")
FILTERNAMESINMESSAGES = os.getenv("FILTER_NAMES_IN_MESSAGES","usermessagepfp,chat_message,command,tf1command")
SENDKILLFEED = os.getenv("SEND_KILL_FEED","0")
OVERRIDEIPFORCDNLEADERBOARD = os.getenv("OVERRIDE_IP_FOR_CDN_LEADERBOARD","hidden")
ANSICOLOUR = "\x1b[38;5;105m"
RGBCOLOUR = (135, 135, 255)
GLOBALIP = 0
if OVERRIDEIPFORCDNLEADERBOARD == "use_actual_ip":
    GLOBALIP ="http://"+requests.get('https://api.ipify.org').text+":34511"
elif OVERRIDEIPFORCDNLEADERBOARD != "hidden":
    GLOBALIP = OVERRIDEIPFORCDNLEADERBOARD

# bantf1()
# tf1matchplayers()
# matchidtf1()
def savecontext():
    global context
    print("saving")
    with open("./data/" + channel_file, "w") as f:
        filteredcontext = context.copy()
        del filteredcontext["commands"]
        json.dump(filteredcontext, f, indent=4)


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
colourslink = {}
# Load channel ID from file
context = {
        "wordfilter":{
        "banwords":[
        ],
        "notifybadwords":[
        ]
    },
    "logging_cat_id": 0,
    "activeguild": 0,
    "serveridnamelinks": {},
    "serverchannelidlinks": {},
    "istf1server": {},
    "RCONallowedusers": [],
    "overridechannels" : {
        "globalchannel":0,
        "commandlogchannel":0,
        "leaderboardchannel":0,
        "wordfilternotifychannel":0
    },
    "leaderboardchannelmessages": [],
    "commands": {}

}
notifydb()
playtimedb()
playeruidnamelink()
joincounterdb()
matchid()
discorduidinfodb()
specifickilltrackerdb()
serverchannels = []
pngcounter = random.randint(0,9)
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
savecontext()
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
    if DISCORDBOTLOGSTATS == "1":
        updateleaderboards.start()



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
if SANCTIONAPIBANKEY != "":
    @bot.slash_command(
        name="serverlesssanction",
        description="Sanctions a offline player, without a server. try saying it 3 times fast",
    )
    async def serverlesssanction(
        ctx,
        playeroruid: Option(str, "Sanction a name or uid", required=True, choices=["uid", "name"]),
        who: Option(str, "The playername/uid to sanction", required=True),
        
        sanctiontype: Option(
            str, "The type of sanction to apply", choices=["mute", "ban"] ),
        reason: Option(str, "The reason for the sanction", required=False) = None,
        expiry: Option(str, "The expiry time of the sanction in format yyyy-mm-dd, omit is forever") = None,
    ):
        global context,messageflush
        if ctx.author.id not in context["RCONallowedusers"]:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("You are not allowed to use this command.", ephemeral=False)
            return
        matchingplayers = resolveplayeruidfromdb(who, playeroruid,True)
        if len (matchingplayers) > 1:
            multistring = "\n" + "\n".join(f"{i+1}) {p['name']} uid: {p['uid']}" for i, p in enumerate(matchingplayers[0:10]))
            await ctx.respond(f"{len(matchingplayers)} players found, please be more specific: {multistring}", ephemeral=False)
            return
        elif len(matchingplayers) == 0:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("No players found", ephemeral=False)
            return
        player = matchingplayers[0]
        await ctx.defer()
        url = f"http://{LOCALHOSTPATH}:3000/sanctions"
        sendjson = {
                "UID": player["uid"],
                "Issuer": ctx.author.name,
                "SanctionType": "1" if sanctiontype == "ban" else "0",
                # "Expire": expiry,
                "ipadd": "127.0.0.1",
                # "Reason": reason,
                "PlayerName": player["name"]
            }
        if expiry:
            sendjson["Expire"] = expiry
        if reason:
            sendjson["Reason"] = reason
        response = requests.post(
            url,
         
            params=sendjson,
               headers={"x-api-key": SANCTIONAPIBANKEY}
        )
        jsonresponse = response.json()
        statuscode = response.status_code
        if statuscode == 201 or statuscode == 200:
            messageflush.append(
                {
                    "servername": "No server",
                    "serverid": "-100",
                    "type": 3,
                    "timestamp": int(time.time()),
                    "globalmessage": True,
                    "overridechannel": "globalchannel",
                    "messagecontent": f"New {sanctiontype} uploaded by {ctx.author.name} for player {player['name']} UID: {player['uid']} {'Expiry: ' + expiry if expiry else ''} {'Reason: ' + reason if reason else ''}",
                    "metadata": {
                        "type": None
                    },
                }
            )
            pass

        await ctx.respond(f"```{jsonresponse}```", ephemeral=False)
if DISCORDBOTLOGSTATS == "1":

    @bot.slash_command(name="leaderboards", description="Gets lederboards for a player")
    async def retrieveleaderboard(
        ctx,
        playername: Option(str, "Who to get a leaderboard for"),
        leaderboard: Option(
            str, "Witch leaderboard, omit for all, more specific data when not ommitted", choices=list(map(lambda x:x["name"],list(filter(lambda x:"name" in x.get("merge","none") ,context["leaderboardchannelmessages"]))))
        ) = None
    ):
        player = resolveplayeruidfromdb(playername,None,True)
        if not player:
            await ctx.respond(f"{playername}player not found", ephemeral=False)
        if leaderboard is None:
            output = {}
            colour = 0
            for logid in range(len(context["leaderboardchannelmessages"])):
                if "name" in context["leaderboardchannelmessages"][logid]["merge"]:
                    output[logid] = await updateleaderboard(logid,specificuidsearch = str(player[0]["uid"]),compact = True)
                    if output[logid]:
                        colour = output[logid]["title"]["color"]
        else:
            for logid in range(len(context["leaderboardchannelmessages"])):
                if "name" in context["leaderboardchannelmessages"][logid]["merge"] and context["leaderboardchannelmessages"][logid]["name"] == leaderboard:
                    output = await updateleaderboard(logid, str(player[0]["uid"]),False,11)
            # print("OUTPUT",output)
            if not output:
                await ctx.respond(f"Leaderboard data not found, or {player[0]['name']} is not in the chosen leaderboard", ephemeral=False)
                return
            embed = discord.Embed(
                    title=output["title"]["title"],
                    color=output["title"]["color"],
                    description=output["title"]["description"],
                )
            for field in output["rows"]:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field["inline"]
            )
            message = await ctx.respond(f"leaderboard for **{player[0]['name']}**", embed=embed, ephemeral=False)
            return
        embed = discord.Embed(
            title=f"leaderboards for **{player[0]['name']}**",
            color=colour,
            description="all leaderboards!",
        )
        for entry in output.values():
            if not entry:
                continue
            # print(json.dumps(entry))
            embed.add_field(
                name=entry["title"]["title"],
                    value=entry["rows"][0]["value"],
                    inline=False
            )
        # print(output)
        message = await ctx.respond(embed=embed ,ephemeral=False)
    # @bot.slash_command(
    #     name="getplayerhours",
    #     description="Get a player's playtime",
    # )
    # async def getplayerhours(ctx, name: Option(str, "The playername/uid to Query")):
    # @bot.slash_command(
    #     name="bindleaderboardchannel",
    #     description="Bind a channel to the leaderboard",
    # )
    # async def bind_leaderboard_channel(
    #     ctx,
    #     channel: Option(
    #         discord.TextChannel, "The channel to bind to", required=True
    #     )):
    #     global context
    #     guild = ctx.guild
    #     if guild.id != context["activeguild"]:
    #         await ctx.respond("This guild is not the active guild.", ephemeral=False)
    #         return
    #     # if channel exists
    #     if channel.id in context["serverchannelidlinks"].values():
    #         await ctx.respond("This channel is already bound to a server.", ephemeral=False)
    #         return
    #     # if channel is not in the serverchannels
    #     # bind
    #     if context["overridechannels"]["leaderboardchannel"] == 0:
    #         context["leaderboardchannelmessages"].append( {
    #         "name": "Pilot kills",
    #         "description": "Top 10 players with most pilot kills",
    #         "color": 16740555,
    #         "database": "playtime",
    #         "orderby": "Total kills",
    #         "categorys": {
    #             "Total kills": {
    #                 "columnsbound": [
    #                     "pilotkills"
    #                 ]
    #             },
    #             "Total score": {
    #                 "columnsbound": [
    #                     "scoregained"
    #                 ]
    #             },
    #             "duration": {
    #                 "format": "time",
    #                 "columnsbound": [
    #                     "duration"
    #                 ]
    #             },
    #             "Score Per Hour": {
    #                 "columnsbound": [
    #                     "scoregained",
    #                     "duration"
    #                 ],
    #                 "format": "XperY*3600",
    #                 "calculation": "scoregained / duration"
    #             }
    #         },
    #         "filters": {},
    #         "merge": "name",
    #         "maxshown": 10,
    #         "id": 0
    #     })
    #     context["overridechannels"]["leaderboardchannel"] = channel.id
        
    #     for i in range(len(context["leaderboardchannelmessages"])):
    #         context["leaderboardchannelmessages"][i]["id"] = 0
        
    #     await ctx.respond(
    #         f"Leaderboard channel bound to {channel.name}.", ephemeral=False
    #     )
    #     savecontext()
        
    @tasks.loop(seconds=LEADERBOARDUPDATERATE)
    async def updateleaderboards():
        # print("leaderboardchannelmessages",context["leaderboardchannelmessages"])
        if context["overridechannels"]["leaderboardchannel"] == 0:
            return
        print("updating leaderboards")
        for logid in range(len(context["leaderboardchannelmessages"])):
            await updateleaderboard(logid)
            await asyncio.sleep(6)
        print("leaderboards updated")
    async def updateleaderboard(logid,specificuidsearch = False,compact = False,maxshownoverride = 5):
        global context
        SEPERATOR = "|"
        now = int(time.time())
        leaderboard_entry = context["leaderboardchannelmessages"][logid].copy()

        leaderboardname = leaderboard_entry.get("name", "Default Leaderboard")
        leaderboarddescription = leaderboard_entry.get("description", "no desc")
        maxshown = leaderboard_entry.get("maxshown", 10)
        leaderboarddcolor = leaderboard_entry.get("color", 0xff70cb)
        leaderboardid = leaderboard_entry.get("id", 0)
        leaderboardcategorysshown = leaderboard_entry["categorys"]
        if isinstance(leaderboardcategorysshown, list) and GLOBALIP != 0:
            print("trying to update cdn leaderboard")
            try:
                # print("here")
                getweaponspng(leaderboardcategorysshown,maxshown,5)
                channel = bot.get_channel(context["overridechannels"]["leaderboardchannel"])
                if leaderboardcategorysshown:
                    image_name = "_".join(sorted(leaderboardcategorysshown)).upper() + ".png"
                else:
                    image_name = "ALL.png"

                cdn_url = f"{GLOBALIP}/cdn/{pngcounter}{image_name}"

                # Check if the image is available before continuing
                image_available = True
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(cdn_url) as response:
                            if response.status != 200:
                                image_available = False
                    except:
                        print("FAILED TO CONNECT TO CDN TO SEND LEADERBOARDIMAGE")
                # print("here2")
                embed = discord.Embed(title=leaderboardname)
                if image_available:
                    embed.set_image(url=cdn_url)

                if leaderboardid != 0 and not specificuidsearch:
                    try:
                        old_message = await channel.fetch_message(leaderboardid)
                        if image_available:
                            # print("here3")
                            await old_message.edit(embed=embed, content=None)
                        else:
                            # print("here4")
                            await old_message.edit(content="⚠ Could not retrieve leaderboard image. Using last image.", embed=old_message.embeds[0] if old_message.embeds else None)
                    except discord.NotFound as e:
                        print("Leaderboard message not found, sending new one.", e, "ID", leaderboardid)
                        new_message = await channel.send(embed=embed)
                        context["leaderboardchannelmessages"][logid]["id"] = new_message.id
                        savecontext()
                
                elif not specificuidsearch:
                    # print("here5")
                    if image_available:
                        new_message = await channel.send(embed=embed)
                        context["leaderboardchannelmessages"][logid]["id"] = new_message.id
                        savecontext()
                    else:
                        await channel.send("Could not retrieve leaderboard image.")
                return
            except Exception as e:
                traceback.print_exc()
                return

        elif  isinstance(leaderboardcategorysshown, list) :
            print("skipping cdn leaderboard")
            return
        leaderboarddatabase = leaderboard_entry["database"]
        leaderboardorderby = leaderboard_entry["orderby"]

        leaderboardfilters = leaderboard_entry.get("filters", {})
        leaderboardmerge = leaderboard_entry["merge"]


        indexoverride = leaderboard_entry.get("nameindex", -1)

        nameoverride = False
        serveroverride = False

        if  isinstance(leaderboardmerge, str):
            leaderboardmerge = [leaderboardmerge]
       
        leaderboardmerge = list(leaderboardmerge)
        oldleaderboardmerge = leaderboardmerge.copy()
        # leaderboardmerge = sorted(leaderboardmerge, key = lambda x: x != "name") #jank to make name always come first no longer needed
        for i,value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "name":
                leaderboardmerge[i] = "playeruid"
                nameoverride = True
        for i,value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "server":
                leaderboardmerge[i] = "serverid"
                serveroverride = True       

        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()

        # Build WHERE clause
        where_clauses = []
        params = []
        if not isinstance(leaderboardfilters, str):
            for key, values in leaderboardfilters.items():
                if len(values) == 1:
                    where_clauses.append(f"{key} = ?")
                    params.append(values[0])
                else:
                    placeholders = ",".join(["?"] * len(values))
                    where_clauses.append(f"{key} IN ({placeholders})")
                    params.extend(values)

            wherestring = " AND ".join(where_clauses)
        else:
            wherestring = eval(leaderboardfilters)
        if not specificuidsearch:
            print("Updating leaderboard:",leaderboardname)
        # print("wherestring",wherestring,where_clauses)
        orderbyiscolumn = leaderboardorderby not in [x for x in leaderboardcategorysshown.keys()]

        leaderboardcategorys = list(set([
            *( [leaderboardorderby] if orderbyiscolumn else [] ),
            *leaderboardmerge,
            *[col for x in leaderboardcategorysshown.values() for col in x["columnsbound"]]
        ]))
        # print("leaderboardcats",leaderboardcategorys)
        countadd = False
        if "matchcount" in leaderboardcategorys:
            countadd = True
            del(leaderboardcategorys[leaderboardcategorys.index("matchcount")])
        # print("leaderboardcategorys",leaderboardcategorys)
        # leaderboardcategorys = sorted(leaderboardcategorys, key=lambda x: list(leaderboardcategorysshown.keys()).index(x) if x in leaderboardcategorysshown else len(leaderboardcategorysshown))
        base_query = f"SELECT {','.join(leaderboardcategorys)} FROM {leaderboarddatabase}"
        query = f"{base_query} WHERE {wherestring}" if wherestring else base_query

        # print("Executing query:", query)
        c.execute(query, params)
        data = c.fetchall()

        if not data:
            pass
            # tfdb.close() (if this is uncommented, it will not update leaderboard if no data found, else it will display no data message)
            # return
            
        # add times appeared columns
        if countadd:
            leaderboardcategorys.append("matchcount")

        # Group rows by the merge key
        output = {}
        mergeindexes = []
        for i in leaderboardmerge:
            mergeindexes.append(leaderboardcategorys.index(i))

        # for row in data:
        #     mergekeys = []
        #     for key in mergeindexes:
        #         mergekeys.append(row[mergeindexes])
        #     # recursion time
        #     output.setdefault(merge_key, []).append(row)
        
 
                
        output = {}    
        for row in data:
            output.setdefault(SEPERATOR.join(list(map(lambda x: str(row[x]),mergeindexes))), []).append(row)
        # print("output",list(output.keys()))

                
                  

        # Merge data per player
        actualoutput = {}
        for key, rows in output.items():
            merged = {}
            for row in rows:
                for idx, col_name in enumerate(leaderboardcategorys):
                    if col_name == "matchcount":
                        merged[col_name] = len(rows)
                        continue
                    val = row[idx]
                    if col_name not in merged:
                        merged[col_name] = val
                    else:
                        if isinstance(val, (int, float)) and isinstance(merged[col_name], (int, float)):
                            merged[col_name] += val
                        elif isinstance(val, str):
                            continue  # Keep the first string
            actualoutput[key] = merged
        # print(actualoutput)
        # print("a",leaderboardcategorysshown)
        # print("b",leaderboardorderby)
        # print("c",leaderboardcategorysshown[leaderboardorderby]["columnsbound"])
        actualoutput = sorted(actualoutput.items(), key=lambda x: x[1][leaderboardorderby] if orderbyiscolumn else (  x[1][leaderboardcategorysshown[leaderboardorderby]["columnsbound"][0]] if len (leaderboardcategorysshown[leaderboardorderby]["columnsbound"]) == 1 else eval(leaderboardcategorysshown[leaderboardorderby]["calculation"], {}, x[1])), reverse=True)
        def swopper(itemname):
            global context
            return str(namemap.get(int(itemname), context["serveridnamelinks"].get(str(itemname),itemname)))
        displayoutput = []
        nameuidmap = []
        if nameoverride:
            c.execute("SELECT playername, playeruid FROM uidnamelink ORDER BY id")
            namemap = {uid: name for name, uid in c.fetchall()}
            for uid, rowdata in actualoutput:
                uid = uid.split(SEPERATOR)#horrible jank
                displayname = SEPERATOR.join(list(map( swopper,uid )))
                nameuidmap.append(uid[0])
                displayoutput.append((displayname, rowdata))
        else:
            displayoutput = actualoutput

        tfdb.close()

        # Build embed
        if not specificuidsearch:
            embed = discord.Embed(
                title=f"{leaderboardname}",
                color=leaderboarddcolor,
                description=f"{leaderboarddescription} **{len(displayoutput)} Entrys**"
            )

        # print(leaderboardcategorysshown)
        # print("displayout",displayoutput)
        # print([nameuidmap[0]],[specificuidsearch])
        ioffset = 0
        entrycount = len(displayoutput)
        if specificuidsearch:
            if specificuidsearch not in nameuidmap:
                return False
            playerindex = nameuidmap.index(specificuidsearch)
            if compact:
                ioffset = playerindex
                displayoutput = displayoutput[playerindex:playerindex+1]
            else:
                n = maxshownoverride
                half = n // 2 
                length = len(displayoutput)
                if length <= n:
                    window = displayoutput
                else:
             
                    start = playerindex - half
                    end   = playerindex + half + 1 
                    
                    if start < 0:
                        end += -start
                        start = 0

                    if end > length:
                        start -= (end - length)
                        end = length
                    start = max(0, start)
                    end = min(length, end)

                    window = displayoutput[start:end]
                # print("STARTEND",start,end)
                ioffset = start
                displayoutput = window
                maxshown = n
        fakembed = {"rows":[]}
        if not compact:
            fakembed["title"] = {
                "title":f"{leaderboardname}",
                "color":leaderboarddcolor,
                "description":f"{leaderboarddescription} **{(entrycount)} Entrys**"
            }
        else:
            fakembed["title"] = {
                    "title":f"{leaderboardname} ***Position: {playerindex+1}***",
                    "color":leaderboarddcolor,
                    "description":leaderboarddescription
                }
        for i, (name, data) in enumerate(displayoutput):
            if i >= maxshown:
                break
            ioffsetted = i + ioffset
            output = {}
            for catname,category in leaderboardcategorysshown.items():
                # print("catname",catname)
                if "calculation" in category.keys():
                    value = eval(category["calculation"],{},data)
                else:
                    if len(category["columnsbound"]) > 1:
                        output[catname] = "Cannot bind multiple columns without a calculation function"
                    value = data[category["columnsbound"][0]]
                value = modifyvalue(value, category.get("format", None), category.get("calculation", None))
                output[catname] = value
                
            actualoutput = "> \u200b \u200b \u200b " + " ".join(
                [f"{category}: **{value}**" for category, value in list(filter(lambda x: x[0] != oldleaderboardmerge[indexoverride], zip(leaderboardcategorysshown, output.values())))]
            )
                # first pull the category names, then send em through the calculator, 
            # print(list(leaderboardcategorysshown.keys()), name.split(SEPERATOR)[indexoverride],oldleaderboardmerge[indexoverride])
            # print(list(zip(leaderboardcategorysshown, output.values())))
            


            
            if not specificuidsearch:
                embed.add_field(
                    name=f" \u200b {str(ioffsetted+1)}. ***{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}***",
                    value=f"{actualoutput}",
                    inline=False
            )
            else:
                fakembed["rows"].append({
                "name":f" \u200b {str(ioffsetted+1)}. **{'*' if playerindex != ioffsetted else ''}{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}{'*' if playerindex != ioffsetted else ''}**",
                "value": actualoutput,
                "inline": False
            })
        if not data:
            fakembed["rows"].append({
                "name":  "Error",
                "value": "No data found for this leaderboard",
                "inline": False
            })
            if not specificuidsearch:
                embed.add_field(
                    name="Error",
                    value="No data found for this leaderboard",
                    inline=False,
                )

        # Update or send leaderboard message
        channel = bot.get_channel(context["overridechannels"]["leaderboardchannel"])

        if leaderboardid != 0 and not specificuidsearch:
            try:
                message = await channel.fetch_message(leaderboardid)
                await message.edit(embed=embed)
            except discord.NotFound as e:
                print("[38;5;100mLeaderboard message not found, resending a new one",e,"ID",leaderboardid)
                return
                message = await channel.send(embed=embed)
                context["leaderboardchannelmessages"][logid]["id"] = message.id
                savecontext()
        elif not specificuidsearch:
            message = await channel.send(embed=embed)
            context["leaderboardchannelmessages"][logid]["id"] = message.id
            savecontext()
        else:
            return fakembed

    def getweaponspng(specificweapon=False, max_players=10, COLUMNS=5):
        global pngcounter
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        FONT_SIZE = 16
        LINE_SPACING = 10
        GOLD = (255, 215, 0)
        SILVER = (192, 192, 192)
        BRONZE = (205, 127, 50)
        DEFAULT_COLOR = (255, 255, 255)
        IMAGE_DIR = "./gunimages"
        CDN_DIR = "./data/cdn"

        # Create the CDN directory if it doesn't exist
        os.makedirs(CDN_DIR, exist_ok=True)

        # Gather available weapon images
        weapon_images = [f for f in os.listdir(IMAGE_DIR) if f.startswith("mp_") and f.endswith(".png")]
        weapon_names = [os.path.splitext(f)[0] for f in weapon_images]

        # Filter by specificweapon list
        if specificweapon:
            specific_set = set(specificweapon)
            weapon_names = [w for w in weapon_names if w in specific_set]
            if not weapon_names:
                print("No matching weapon images found for the given list.")
                return None

        # Fetch kill data from DB
        def fetch_kill_data():
            conn = sqlite3.connect("./data/tf2helper.db")
            c = conn.cursor()
            c.execute("SELECT cause_of_death, playeruid FROM specifickilltracker")
            rows = c.fetchall()
            conn.close()
            return rows

        kill_data = fetch_kill_data()
        weapon_kills = {}
        for weapon, attacker in kill_data:
            weapon_kills.setdefault(weapon, []).append(attacker)

        def max_kill_count(attacker_list):
            counts = {}
            for attacker in attacker_list:
                counts[attacker] = counts.get(attacker, 0) + 1
            return max(counts.values(), default=0)

        if not specificweapon:
            weapon_names.sort(key=lambda w: max_kill_count(weapon_kills.get(w, [])), reverse=True)

        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except (OSError, IOError):
            font = ImageFont.load_default()

        panels = []
        for weapon in weapon_names:
            img_path = os.path.join(IMAGE_DIR, weapon + ".png")
            gun_img = Image.open(img_path)

            counts = {}
            if weapon in weapon_kills:
                for attacker in weapon_kills[weapon]:
                    counts[attacker] = counts.get(attacker, 0) + 1

            sorted_players = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:max_players]
            num_display = len(sorted_players)
            text_area_height = (FONT_SIZE + LINE_SPACING) * num_display + 10
            panel_height = gun_img.height + text_area_height

            panel = Image.new("RGBA", (gun_img.width, panel_height), (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50), 80))
            draw = ImageDraw.Draw(panel)
            panel.paste(gun_img, (0, 0))

            for i, (attacker, count) in enumerate(sorted_players):
                try:
                    name = resolveplayeruidfromdb(attacker, "uid", True)[0]["name"]
                except:
                    name = attacker
                text = f"{name}: {count}"

                color = (
                    GOLD if i == 0 else
                    SILVER if i == 1 else
                    BRONZE if i == 2 else
                    DEFAULT_COLOR
                )

                y = gun_img.height + i * (FONT_SIZE + LINE_SPACING) + 5
                draw.text((5, y), text, font=font, fill=color)

            panels.append(panel)

        if not panels:
            print("No panels to render.")
            return None

        panel_width = max(panel.width for panel in panels)
        final_columns = min(COLUMNS, len(panels))
        rows = (len(panels) + final_columns - 1) // final_columns

        row_heights = []
        for row in range(rows):
            row_panels = panels[row * final_columns:(row + 1) * final_columns]
            row_heights.append(max(p.height for p in row_panels))

        canvas_width = final_columns * panel_width
        canvas_height = sum(row_heights)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (30, 30, 30, 0))

        y_offset = 0
        for row in range(rows):
            row_panels = panels[row * final_columns:(row + 1) * final_columns]
            for col, panel in enumerate(row_panels):
                x = col * panel_width
                canvas.paste(panel, (x, y_offset))
            y_offset += row_heights[row]

        # Determine filename
        if specificweapon:
            base_name = "_".join(sorted(weapon_names)).upper()
        else:
            base_name = "ALL"
        pngcounter = (pngcounter + 1) % 9
        file_path = os.path.join(CDN_DIR, str(pngcounter) + base_name +".png")
        
        # Save to disk
        canvas.save(file_path, format="PNG")

    def modifyvalue(value, format, calculation=None):
        if format is None:
            return value
        elif format == "time":
            hours = value // 3600
            minutes = (value % 3600) // 60
            seconds = value % 60
            if hours:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m {seconds}s"
        elif format == "XperY*3600":
            if value == 0:
                return "0"
            else:
                return f"{value*3600:.2f}{ calculation.split('/')[0].strip()[0].lower()}/{ calculation.split('/')[1].strip()[0].lower()}"
        elif format == "server":
            return str(context["serveridnamelinks"].get(str(value), value))
        elif format == "hammertometres":
            if value == 0:
                return "0"
            else:
                return f"{value/52.5:.2f}m"
        elif format == "gun":
            # print("gun",value,list(WEAPON_NAMES.keys())[0])
            return str(WEAPON_NAMES.get(value, value))
        elif format == "XperY":
            if value == 0:
                return "0"
            else:
                return f"{value:.2f}{ calculation.split('/')[0].strip()[0].lower()}/{ calculation.split('/')[1].strip()[0].lower()}"
        elif format == "map":
            return str(MAP_NAME_TABLE.get(value, value))
        return value
        



    @bot.slash_command(
        name="whois",
        description="Get a player's Aliases",
    )
    async def whois(ctx, name: Option(str, "The playername/uid to Query")):
        MAXALIASESSHOWN = 22
        originalname = name
        print("whois command from", ctx.author.id, "to", name)
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT playeruid, playername FROM uidnamelink")
        data = c.fetchall()
        
        if not data:
            tfdb.commit()
            tfdb.close()
            asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("No players in the database", ephemeral=False)
            return

        unsortedata = [{"name": x[1], "uid": x[0]} for x in data]
        data = sorted(unsortedata, key=lambda x: len(x["name"]))
        data = sorted(data, key=lambda x: not x["name"].lower().startswith(name.lower()))
        data = [x for x in data if name.lower() in x["name"].lower()]
        unsortedata = [x for x in unsortedata if name.lower() in x["name"].lower()]

        if len(data) == 0:
            c.execute("SELECT playeruid FROM uidnamelink WHERE playeruid = ?", (name,))
            output = c.fetchone()
            if not output:
                tfdb.commit()
                tfdb.close()
                asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
                await ctx.respond("No players found", ephemeral=False)
                return
            player = {"uid": output[0]}
        else:
            player = data[0]

        c.execute("""
            SELECT playername, firstseenunix, lastseenunix 
            FROM uidnamelink 
            WHERE playeruid = ? 
            ORDER BY id DESC
        """, (player["uid"],))
        aliases_raw = c.fetchall()

        aliases = []
        for name, first, last in aliases_raw:
            first_str = f"<t:{first}:R>" if first else "unknown"
            last_str = f"<t:{last}:R>" if last else "unknown"
            aliases.append(f"{name} *(first seen: {first_str}, last seen: {last_str})*")

        tfdb.commit()
        tfdb.close()

        alsomatching = {}
        for entry in unsortedata:
            if entry["uid"] == player["uid"]:
                continue
            alsomatching[entry["uid"]] = entry["name"]

        embed = discord.Embed(
            title=f"Aliases for uid {player['uid']} ({len(alsomatching.keys()) + 1} match{'es' if len(alsomatching.keys()) > 0 else ''} for '{originalname}')",
            color=0xff70cb,
            description="Most recent to oldest",
        )

        for y, x in enumerate(aliases[0:MAXALIASESSHOWN]):
            embed.add_field(name=f"Alias {y+1}:", value=f"\u200b {x}", inline=False)

        if len(aliases) > MAXALIASESSHOWN:
            embed.add_field(
                name=f"{len(aliases) - MAXALIASESSHOWN} more alias{'es' if len(aliases) - MAXALIASESSHOWN > 1 else ''}",
                value=f"({', '.join(list(map(lambda x: f'*{x}*', aliases[MAXALIASESSHOWN:])))})"
            )

        if len(alsomatching.keys()) > 0:
            embed.add_field(
                name=f"The {len(alsomatching.keys())} other match{'es are:' if len(alsomatching.keys()) > 1 else ' is:'}",
                value=f"({', '.join(list(map(lambda x: f'*{x}*', list(alsomatching.values())[0:20])))}) {'**only first 20 shown**' if len(alsomatching.keys()) > 20 else ''}"
            )

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
        embed.add_field(name="leaderboards", value="Get the leaderboards for a specific player", inline=False)
        embed.add_field(name="togglejoinnotify", value="Toggle notifying on a player joining / leaving", inline=False)
        embed.add_field(name="bindloggingtocategory", value="Bind logging to a new category (use for first time init)", inline=False)
        # embed.add_field(name="bindleaderboardchannel", value="Bind a channel to the leaderboards", inline=False)
        embed.add_field(name="rconchangeuserallowed", value="Toggle if a user is allowed to use RCON commands", inline=False)
        # embed.add_field(name="bindglobalchannel", value="Bind a global channel to the bot (for global messages from servers, like bans)", inline=False)
        embed.add_field(name="bindchannel", value="Bind a channel to the bot for other functions, like leaderboards, globalmessages", inline=False)
        embed.add_field(name="tf2chatcolour",value="put in a hex colour eg: '#ff30cb', or a normal colour eg: 'red' to colour your tf2 name")
        if SHOULDUSETHROWAI == "1":
            embed.add_field(name="thrownonrcon", value="Throw a player, after being persuasive", inline=False)
        if SANCTIONAPIBANKEY != "":
            embed.add_field(name="serverlesssanction", value="Sanction a player without a server", inline=False)
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
                value[1] = int(value[1])
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
    

# @bot.slash_command(name="bindglobalchannel", description="Bind a global channel to the bot")
# async def bind_global_channel(
#     ctx,
#     channel: Option(
#         discord.TextChannel, "The channel to bind to", required=True
#     )):
#     global context
#     guild = ctx.guild
#     if guild.id != context["activeguild"]:
#         await ctx.respond("This guild is not the active guild.", ephemeral=False)
#         return
#     if ctx.author.id not in context["RCONallowedusers"]:
#         await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#         return
#     if channel.id in context["serverchannelidlinks"].values():
#         await ctx.respond("This channel is already bound to a server.", ephemeral=False)
#         return
#     context["overridechannels"]["globalchannel"] = channel.id
#     savecontext()
#     await ctx.respond(f"Global channel bound to {channel.name}.", ephemeral=False)


@bot.slash_command(name="bindchannel", description="Bind a channel to the bot.")
async def bind_global_channel(
    ctx,
       channeltype: Option(
        str,
        "The type of channel to bind",
        required=True,
        choices=list(context["overridechannels"].keys()),
    ),
    channel: Option(
        discord.TextChannel, "The channel to bind to", required=True
    ),
 
        
    
    ):
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
    
    if channeltype == "leaderboardchannel":
        if context["overridechannels"]["leaderboardchannel"] == 0:
            context["leaderboardchannelmessages"].extend([ {
            "name": "Pilot kills",
            "description": "Top 10 players with most pilot kills",
            "color": 16740555,
            "database": "playtime",
            "orderby": "Total kills",
            "categorys": {
                "Total kills": {
                    "columnsbound": [
                        "pilotkills"
                    ]
                },
                "Total score": {
                    "columnsbound": [
                        "scoregained"
                    ]
                },
                "duration": {
                    "format": "time",
                    "columnsbound": [
                        "duration"
                    ]
                },
                "Score Per Hour": {
                    "columnsbound": [
                        "scoregained",
                        "duration"
                    ],
                    "format": "XperY*3600",
                    "calculation": "scoregained / duration"
                }
            },
            "filters": {},
            "merge": "name",
            "maxshown": 10,
            "id": 0
        },
                   {
            "name": "Frag grenade kills",
            "description": "frag kills in last week",
            "color": 16740555,
            "database": "specifickilltracker",
            "orderby": "Frag kills",
            "categorys": {
                "Frag kills": {
                    "columnsbound": [
                        "matchcount"
                    ]
                }
            },
            "filters": "f'cause_of_death = \"mp_weapon_frag_grenade\" AND timeofkill > {int((datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).weekday())).timestamp())}'",
            "merge": "name",
            "maxshown": 10,
            "id": 0
        },
        {
            "name": "All weapon kills",
            "categorys": [],
            "color": 16740555,
            "id": 0,
            "maxshown":3
        }
        ])
        context["overridechannels"]["leaderboardchannel"] = channel.id
    elif channel.id != context["overridechannels"]["leaderboardchannel"]:
        for i in range(len(context["leaderboardchannelmessages"])):
            context["leaderboardchannelmessages"][i]["id"] = 0
    context["overridechannels"][channeltype] = channel.id
    savecontext()
    await ctx.respond(f"Channel type {channeltype} bound to {channel.name}.", ephemeral=False)




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
    if user.id in context["RCONallowedusers"] and ctx.author.guild_permissions.administrator:
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
@bot.slash_command(
    name="tf2chatcolour",
    description="put in a hex colour eg: '#ff30cb', or a normal colour eg: 'red' to colour your tf2 name"
)
async def show_color(ctx, colour: Option(str, "Enter a hex color")):
    global colourslink
    if not re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour) and colour.lower() not in CSS_COLOURS.keys() and colour != "reset":
        await ctx.respond("Please enter a **valid** hex color (e.g: '#1A2B3C'), or a valid normal colour, (e.g: 'red')", ephemeral=False)
        return
    if re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour):
        r = int(colour[1:3], 16)
        g = int(colour[3:5], 16)
        b = int(colour[5:7], 16)
        rgba = (r, g, b)
    elif colour.lower()  in CSS_COLOURS.keys():
        rgba = CSS_COLOURS[colour]
    else:
        rgba = "reset"
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        "INSERT OR REPLACE INTO discorduiddata (discorduid, chosencolour) VALUES (?, ?)",
        (ctx.author.id, str(rgba))
    )

    tfdb.commit()
    tfdb.close()
    
    if rgba == "reset":
        colourslink[ctx.author.id] = RGBCOLOUR
        await ctx.respond(f"reset colour to default")
        return
    colourslink[ctx.author.id] = rgba
    await ctx.respond(f"Set colour to {rgba}")

# lifted straight from my chat colours thing
def gradient(message,colours, maxlen):
    """gradient colouring (Two colours)"""
    # print(message)
    # message = message.split(" ")
    # if len(message) < 0:
    #     return 0
    # colours = []
    # for i in message[::-1]:
    #     if coloursheet.returncolour(i.lower()):
    #         colours.append(coloursheet.returncolour(i.lower()))
    #     else:
    #         break
    # actualmessage = " ".join(message[0 : -len(colours)]).replace(" ", "")
    # strmessage = " ".join(message[0 : -len(colours)])
    actualmessage = message.replace(" ", "")
    if colours == []:
        return 1
    if len(colours) == 1:
        colours.append(colour[0])
    
    # colours.reverse()
    encodelength = 1
    overcharlimit = True
    outputmessage = []
    differences = []
    for i in range(len(colours) - 1):
        differences.append(
            (
                colours[i + 1][0] - colours[i][0],
                colours[i + 1][1] - colours[i][1],
                colours[i + 1][2] - colours[i][2],
            )
        )
    groupedletters = []
    for i in range(len(colours) - 1):
        groupedletters.append([])
    for i in range(len(actualmessage)):
        groupedletters[int(i / len(actualmessage) * (len(colours) - 1))].append(
            actualmessage[i]
        )
    while overcharlimit:
        counter = 0
        messagecounter = 0
        for i in range(len(groupedletters)):
            counter2 = 0
            letters = groupedletters[i]
            for letter in letters:
                while message[messagecounter] == " ":
                    outputmessage.append(" ")
                    messagecounter += 1
                if counter % encodelength != 0:
                    counter += 1
                    counter2 += 1
                    messagecounter += 1
                    outputmessage.append(letter)
                    continue
                Colour = (
                    colours[i][0]
                    + int(differences[i][0] * (counter2) / (len(letters))),
                    colours[i][1]
                    + int(differences[i][1] * (counter2) / (len(letters))),
                    colours[i][2]
                    + int(differences[i][2] * (counter2) / (len(letters))),
                )
                outputmessage.append(rgb_to_ansi(Colour, 0) + letter)
                counter += 1
                counter2 += 1
                messagecounter += 1
        if len("".join(outputmessage)) > maxlen:
            encodelength += 1
            outputmessage = []
        else:
            overcharlimit = False
        if encodelength > maxlen / 2:
            return 2
    return "".join(outputmessage)

def rgb_to_ansi(value, vary=0):
    """conversts an rgb code to an ansi string variance is random variance that is less prominent on brighter,less saturated colours"""
    value = list(value)
    # print(value)
    a = max(value)
    b = min(value)
    if a - b < vary:
        vary += (-50 + a - b) * 0.7
        # print("vary",vary,a,b)
        if vary < 0:
            vary = 0
    for i in range(len(value)):
        offset = 0
        value[i] = int(value[i])
        if value[i] - int((value[i] / 255 + 0.3) * vary) < 0:
            offset = int((value[i] / 255 + 0.3) * vary) - value[i]
        elif value[i] + int((value[i] / 255 + 0.3) * vary) > 255:
            offset = 255 - value[i] - int((value[i] / 255 + 0.3) * vary)
        value[i] += random.randint(
            int(-(value[i] / 255) * vary) + offset,
            int((value[i] / 255) * vary) + offset,
        )
        if value[i] > 254:
            value[i] = 254
        elif value[i] < 1:
            value[i] = 1
    output = "[38;2;" + str(value[0]) + ";" + str(value[1]) + ";" + str(value[2]) + "m"
    return output

@bot.event
async def on_message(message):
    global  context, discordtotitanfall
    if message.author == bot.user or message.webhook_id is not None:
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
                f"{ANSICOLOUR}{message.author.nick if message.author.nick is not None else message.author.display_name}: [38;5;254m{message.content}"
            )
            > 254 - bool(context["istf1server"].get(serverid,False))*130
        ):
            await message.channel.send("Message too long, cannot send.")
            return
        authornick = gradient(message.author.nick if message.author.nick is not None else message.author.display_name,[RGBCOLOUR,colourslink.get(message.author.id,RGBCOLOUR)], 254 -len( f": [38;5;254m{message.content}")- bool(context["istf1server"].get(serverid,False))*130)
        # dotreacted = None
        # if discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 45:
        #     dotreacted = "🔴"
        # elif discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 5:
        #     dotreacted = "🟡" 
        if message.content != "": #and not context["istf1server"].get(serverid,False):
            print(f"{authornick}: [38;5;254m{message.content}\033[0m")
            print(len(f"{authornick}{': ' if not  bool(context['istf1server'].get(serverid,False)) else ''}[38;5;254m{': ' if   bool(context['istf1server'].get(serverid,False)) else ''}{message.content}"))
            discordtotitanfall[serverid]["messages"].append(
                {
                    "id": message.id,
                    "content": f"{authornick}{': ' if not  bool(context['istf1server'].get(serverid,False)) else ''}[38;5;254m{': ' if   bool(context['istf1server'].get(serverid,False)) else ''}{message.content}",
                    # "dotreacted": dotreacted
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
            
    @app.route("/cdn/<filename>", methods=["GET"])
    def get_cdn_image(filename):
        if not filename.lower().endswith(".png"):
            abort(400, "Only .png files are allowed")
        cdn_path = os.path.join(".", "data", "cdn")
        file_path = os.path.join(cdn_path, filename)
        if not os.path.exists(file_path):
            print("error fetching cdn leaderboard",filename)
            return send_from_directory("./data","bunny.png")
        return send_from_directory(cdn_path, filename)

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
                # print("sending messages and commands to titanfall", texts, sendingcommands)
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

    @app.route("/data", methods=["POST"])
    def onkilldata():
        # takes input directly from (slightly modified) nutone (https://github.com/nutone-tf) code for this to work is not on the github repo, so probably don't try using it.
        global context, messageflush
        data = request.get_json()
        print(f"{data['attacker_name']} killed {data['victim_name']} with {data['attacker_current_weapon']}")
        # messageflush.append({
        #     "timestamp": int(time.time()),
        #     "serverid": data["server_id"],
        #     "type": 3,
        #     "globalmessage": False,
        #     "overridechannel": None,
        #     "messagecontent": f"{data['attacker_name']} killed {data['victim_name']} with {WEAPON_NAMES.get(data['attacker_current_weapon'],data['attacker_current_weapon'])}",
        #     "metadata": {"type":"killfeed"},
        #     "servername" :context["serveridnamelinks"][data["server_id"]]

        #             })
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on data")
            return {"message": "invalid password"}
        specifickillbase = sqlite3.connect("./data/tf2helper.db")
        c = specifickillbase.cursor()
        c.execute(
            """
            INSERT INTO specifickilltracker (
                serverid,
                attacker_z,
                attacker_x,
                attacker_y,
                victim_id,
                victim_name,
                victim_offhand_weapon_2,
                attacker_titan,
                map,
                attacker_offhand_weapon_1,
                attacker_offhand_weapon_2,
                victim_offhand_weapon_1,
                attacker_weapon_3,
                attacker_name,
                match_id,
                victim_titan,
                distance,
                victim_current_weapon,
                victim_z,
                attacker_weapon_2,
                game_time,
                attacker_current_weapon,
                victim_weapon_3,
                playeruid,
                game_mode,
                victim_x,
                attacker_weapon_1,
                victim_weapon_1,
                victim_weapon_2,
                timeofkill,
                cause_of_death,
                victim_y
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["server_id"],
                data["attacker_z"],
                data["attacker_x"],
                data["attacker_y"],
                data["victim_id"],
                data["victim_name"],
                data["victim_offhand_weapon_2"],
                data["attacker_titan"],
                data["map"],
                data["attacker_offhand_weapon_1"],
                data["attacker_offhand_weapon_2"],
                data["victim_offhand_weapon_1"],
                data["attacker_weapon_3"],
                data["attacker_name"],
                data["match_id"],
                data["victim_titan"],
                data["distance"],
                data["victim_current_weapon"],
                data["victim_z"],
                data["attacker_weapon_2"],
                data["game_time"],
                data["attacker_current_weapon"],
                data["victim_weapon_3"],
                data["attacker_id"],
                data["game_mode"],
                data["victim_x"],
                data["attacker_weapon_1"],
                data["victim_weapon_1"],
                data["victim_weapon_2"],
                data["timeofkill"],
                data["cause_of_death"],
                data["victim_y"],
            )
        )
        specifickillbase.commit()
        c.close()
        specifickillbase.close()
        return {"message": "ok"}

    @app.route("/servermessagein", methods=["POST"])
    def printmessage():
        global messageflush, lastmessage, messagecounter, context
        data = request.get_json()
        addtomessageflush = True
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
        newmessage["overridechannel"] = data["overridechannel"] if data["overridechannel"] != "None" else None
        if newmessage["overridechannel"] is not None:
            newmessage["globalmessage"] = True
        elif newmessage["globalmessage"] == True:
            newmessage["overridechannel"] = "globalchannel"
        if newmessage["overridechannel"] and newmessage["overridechannel"] not in context["overridechannels"].keys():
            print("invalid override channel, valid channels are", context["overridechannels"].keys(), "not", newmessage["overridechannel"])
            newmessage["overridechannel"] = None
            newmessage["globalmessage"] = False
            addtomessageflush = False
        elif newmessage["globalmessage"] and newmessage["overridechannel"] not in context["overridechannels"].keys():
            print("Override channel is not bound to a channel")
            newmessage["overridechannel"] = None
            newmessage["globalmessage"] = False
            addtomessageflush = False
        newmessage["messagecontent"] = data["messagecontent"]
        if not newmessage["globalmessage"]:
            print("message request from", newmessage["serverid"], newmessage["servername"])
        else:
            print("global message request from", newmessage["serverid"], newmessage["servername"],"True" if addtomessageflush else "False")
        newmessage["metadata"] = {"type": None}
        #print(list(data.keys()))
        if "metadata" in data.keys() and data["metadata"] != "None":
            data["metadata"] = getjson(data["metadata"])
            newmessage["metadata"] = data["metadata"]
            if data["metadata"]["type"] == "connect":
                onplayerjoin(data["metadata"]["uid"],data["serverid"],data["player"])
            elif data["metadata"]["type"] == "disconnect":
                onplayerleave(data["metadata"]["uid"],data["serverid"])
        if addtomessageflush:
            print(newmessage)
            messageflush.append(newmessage)     

        messagecounter += 1
        lastmessage = time.time()

        if  newmessage["serverid"] not in context["serveridnamelinks"]:
            context["serveridnamelinks"][newmessage["serverid"]] = newmessage["servername"]
            context["istf1server"][newmessage["serverid"]] = False
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
def getmessagewidget(metadata,serverid,messagecontent,message):
    global context
    output = messagecontent
    player = str(message.get("player","Unknown player"))

    # print("metadata",metadata)
    if metadata.get("teamtype","not team") != "not team":
        player = f"{player} {metadata.get('teamtype','not team')}"
    if metadata.get("isalive","unknown") != "unknown" and not metadata.get("isalive","unknown"):
        player = f"{player} [DEAD]"
        
    if not metadata["type"]:
        pass
    elif metadata["type"] == "connect" and DISCORDBOTLOGSTATS == "1":
        pass
        uid = metadata["uid"]
        tfdb = sqlite3.connect("./data/tf2helper.db")
        c = tfdb.cursor()
        c.execute("SELECT count FROM joincounter WHERE playeruid = ? AND serverid = ?", (uid,serverid))
        data = c.fetchone()
        c.execute("SELECT leftatunix,joinatunix FROM playtime WHERE playeruid = ? AND serverid = ?", (uid,serverid))
        data2 = c.fetchall()
        
        if data:
            data = data[0]
            output += f"\n({data}{get_ordinal(data)} time joining"
            if data2:
                data2 = sum(list(map(lambda x: x[0]-x[1], data2)))
                output += f" - {data2//3600}h {data2//60%60}m time playing"
            output += ")"
    elif metadata["type"] == "command":
        if DISCORDBOTLOGCOMMANDS != "1":
            return "",player
        output = f"""> {context['serveridnamelinks'].get(serverid,'Unknown server').ljust(30)} {(message['player']+":").ljust(20)} {message['messagecontent']}"""
    elif metadata["type"] == "tf1command":
        if DISCORDBOTLOGCOMMANDS != "1":
            return "",player
        output = f"""> {context['serveridnamelinks'].get(serverid,'Unknown server').ljust(50)} {message['messagecontent']}"""  
    
    elif metadata["type"] == "disconnect":
        pass
    return output,player



def filterquotes(inputstr):
    return re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', inputstr.replace('"', "'").replace("wqdwqqwdqwdqwdqw$", "").replace("\n", r"\n")) 

def bansystem(statusoutput):
    pass
# if TF1RCONKEY != "":
#     @bot.slash_command(
#         name="tf1ban",
#         description="ban and mute somone in a tf1 server",
#     )
#     async def serverlesssanction(
#         ctx,
#         # playeroruid: Option(str, "Sanction a name or uid", required=True, choices=["uid", "name"]),
#         who: Option(str, "The playername to sanction", required=True),
        
#         sanctiontype: Option(
#             str, "The type of sanction to apply", choices=["mute", "ban"] ),
#         reason: Option(str, "The reason for the sanction", required=False) = None,
#         expiry: Option(str, "The expiry time of the sanction in format yyyy-mm-dd, omit is forever") = None,
#     ):
#         global context,messageflush
#         if ctx.author.id not in context["RCONallowedusers"]:
#             await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#             await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#             return
#         matchingplayers = resolveplayeruidfromdb(who, playeroruid)
#         if len (matchingplayers) > 1:
#             multistring = "\n" + "\n".join(f"{i+1}) {p['name']}" for i, p in enumerate(matchingplayers[0:10]))
#             await ctx.respond(f"{len(matchingplayers)} players found, please be more specific: {multistring}", ephemeral=False)
#             return
#         elif len(matchingplayers) == 0:
#             await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#             await ctx.respond("No players found", ephemeral=False)
#             return
#         player = matchingplayers[0]
#         await ctx.defer()
#         url = f"http://{LOCALHOSTPATH}:3000/sanctions"
#         sendjson = {
#                 "UID": player["uid"],
#                 "Issuer": ctx.author.name,
#                 "SanctionType": "1" if sanctiontype == "ban" else "0",
#                 # "Expire": expiry,
#                 "ipadd": "127.0.0.1",
#                 # "Reason": reason,
#                 "PlayerName": player["name"]
#             }
#         if expiry:
#             sendjson["Expire"] = expiry
#         if reason:
#             sendjson["Reason"] = reason
#         response = requests.post(
#             url,
         
#             params=sendjson,
#                headers={"x-api-key": SANCTIONAPIBANKEY}
#         )
#         jsonresponse = response.json()
#         statuscode = response.status_code
#         if statuscode == 201 or statuscode == 200:
#             messageflush.append(
#                 {
#                     "servername": "No server",
#                     "serverid": "-100",
#                     "type": 3,
#                     "timestamp": int(time.time()),
#                     "globalmessage": True,
#                     "overridechannel": "globalchannel",
#                     "messagecontent": f"New {sanctiontype} uploaded by {ctx.author.name} for player {player['name']} UID: {player['uid']} {'Expiry: ' + expiry if expiry else ''} {'Reason: ' + reason if reason else ''}",
#                     "metadata": {
#                         "type": None
#                     },
#                 }
#             )
#             pass

#         await ctx.respond(f"```{jsonresponse}```", ephemeral=False)
tf1servercontext ={}

# def tf1savecontexttosql():
#     global tf1servercontext

# def tf1statusinterp(status,serverid,matchid):
#     global tf1servercontext
#     currentmap, players = interpstatus(status)
#     # setdefault(now,[])
#     now = int(time.time())
#     # for player in players:
#     #     tf1servercontext.setdefault(player["name"],{})
#     #     tf1servercontext[currentmap].setdefault(player["ip"],{})
#     #     tf1servercontex[currentmap][player["ip"]].setdefault(player["name"],{"timejoined":now})
#     #     tf1servercontext[currentmap][player["ip"]][player["name"]]["timepoll"] = now


        



# def interpstatus(log):
#     m = re.search(r"map\s*:\s*(\S+)", log)
#     map_name = m.group(1) if m else None
#     players = []
#     for line in log.splitlines():
#         if "#" in line and '"' in line:
#             m1 = re.search(r'#\s*(\d+)\s+\d+\s+"([^"]+)"', line)
#             if not m1:
#                 continue
#             userid, name = m1.group(1), m1.group(2)
#             m2 = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})(?=\[)', line)
#             ip = m2.group(1) if m2 else None

#             players.append({
#                 "userid": userid,
#                 "name": name,
#                 "ip": ip
#             })

#     return map_name, players

def tf1readsend(serverid,checkstatus):
    # don't even bother trying to send anything or read anything if the server is offline!
    global discordtotitanfall,context,reactedyellowtoo
    commands = {}
    offlinethisloop = False
    now = int((time.time())*100) # increased by 8 seconds, to increase the time it takes for a yellow dot to be reacted
    for command in list(discordtotitanfall[serverid]["commands"]):
        command = {**command}
        if command["command"][0] != "!":
            commands[command["id"]] = {"type":"rcon","command":command["command"],"id":command["id"]}
            continue
        # print(command)
        command["command"] = command["command"][1:]
        command["command"] = command["command"].split(" ")
        # print("COMMAND",command)
        commands[command["id"]] = {"type":"rpc","command":command["command"][0],"id":command["id"],"args":command["command"][1:]}
    inputstring = {}
    if discordtotitanfall[serverid]["lastheardfrom"] > int(time.time()) - 6:
    # if discordtotitanfall[serverid].get("serveronline",False):
    


        # print("HERHE",discordtotitanfall[serverid]["messages"])
        # print(discordtotitanfall)
        messages = False
        toolongmessages = []
        for message in discordtotitanfall[serverid]["messages"]:
            messages = True
            if str(message["id"]) in discordtotitanfall[serverid]["returnids"]["messages"].keys():
                continue   #TRADEOFF HERE. EITHER I SEND IT EACH RCON CALL (and don't update the timestamp) OR I do what I do here and only send it once, wait untill yellow dot cleaner comes, then send again.
            if len(message["content"]) > 130:
                toolongmessages.append(message["id"])
            commands[message["id"]] = {"type":"msg","command":"sendmessage","id":message["id"],"args":str(message['content'])[0:130]}
        if len(discordtotitanfall[serverid]["returnids"]["messages"].keys()) != -1 and messages:# and discordtotitanfall[serverid]["serveronline"]:
            
            for messageid in list(map(lambda x: str(x["id"]),list(filter(lambda x: True ,discordtotitanfall[serverid]["messages"])))):
                discordtotitanfall[serverid]["returnids"]["messages"].setdefault(messageid,[now])
            print("RETURNIDS",discordtotitanfall[serverid]["returnids"]["messages"])
            # discordtotitanfall[serverid]["returnids"]["messages"][now] = list(map(lambda x: x["id"],list(filter(lambda x: x["id"] not in reactedyellowtoo ,discordtotitanfall[serverid]["messages"]))))
        # I don't recall why I needed this grouping system. hence, I am removing it.
        # what if a message is sent, and it fails? oh that's why I had it isn't it.
            # print(discordtotitanfall[serverid]["returnids"]["messages"][now])
        # elif messages:# and discordtotitanfall[serverid]["serveronline"]:
        #     msgids = []
        #     searcher = list(discordtotitanfall[serverid]["returnids"]["messages"].keys())
        #     for search in searcher:
        #         for msgid in discordtotitanfall[serverid]["returnids"]["messages"][search]:
        #             msgids.append(msgid)
        #     for newmsgid in discordtotitanfall[serverid]["messages"]:
        #         if newmsgid["id"] not in msgids and  newmsgid["id"] not in reactedyellowtoo:
        #             discordtotitanfall[serverid]["returnids"]["messages"].setdefault(now,[]).append(newmsgid["id"])
        #     print("RETURNIDS",discordtotitanfall[serverid]["returnids"]["messages"])
            # discordtotitanfall[serverid]["returnids"]["messages"][list(discordtotitanfall[serverid]["returnids"]["messages"].keys())[0]]  = list(map(lambda x: x["id"],discordtotitanfall[serverid]["messages"])) 
        # print(discordtotitanfall[serverid]["returnids"]["messages"])
        
        # shouldnotreturn = discordtotitanfall[serverid]["serveronline"]
        # print("commands",commands)
    try:
        with Client(discordtotitanfall[serverid]["ip"].split(":")[0],  int(discordtotitanfall[serverid]["ip"].split(":")[1]), passwd=TF1RCONKEY,timeout=2) as client:
            
            if checkstatus or len(commands) > 0:
                client.run('sv_cheats','1')
            if checkstatus:
                # playingpollidentity
                statusoutput = client.run("script",'Lrconcommand("playingpollidentity")')
                # print(statusoutput)
                if "OUTPUT<" in statusoutput and "/>ENDOUTPUT" in statusoutput:
                    statusoutput = "".join("".join("".join(statusoutput.split("BEGINMAINOUT")[1:]).split("OUTPUT<")[1:]).split("/>ENDOUTPUT")[:-1])
                    statusoutput = statusoutput.replace("☻",'"')
                    statusoutput = getjson(statusoutput)
                # print((statusoutput))
                peopleonserver = len(statusoutput.keys()) -1
                discordtotitanfall[serverid]["serveronline"] = bool (len(statusoutput.keys()) -1)
                if not discordtotitanfall[serverid]["serveronline"]:
                    offlinethisloop = True
                    return
                # status = client.run("status")
                # # print("statuscheck","not hibernating" not in status or "0 humans" in status,status)
                # if "not hibernating" not in status and "0 humans" in status:
                #     # print("server not online")
                #     discordtotitanfall[serverid]["serveronline"] = False
                #     offlinethisloop = True
                #     if discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 5:
                #         return False
                # else:
                #     pass
                    # matchid = client.run("autocvar_matchid") 
                    # tf1statusinterp(status,serverid,matchid)
            if len(commands) > 0:
                print("sending messages and commands to tf1",commands)

                for w, command in commands.items():
                    quotationmark = '"'
                    if command["type"] == "rcon":
                        # print("beep boop")
                        inputstring[command["id"]] = client.run(*command["command"].split(" "))
                        # print("I managed it!")
                        continue
                    # print("BEEP BOOP",filterquotes("".join(command["args"])))
                    print("script", f'Lrconcommand("{filterquotes(command["command"])}"{","+quotationmark+filterquotes("".join(command["args"]))+quotationmark if "args" in command.keys() else "" },"{command["id"] }")')
                    inputstring[command["id"]] = client.run("script", f'Lrconcommand("{filterquotes(command["command"])}"{","+quotationmark+filterquotes("".join(command["args"]))+quotationmark if "args" in command.keys() else "" },"{command["id"] }")')#{","+quotationmark+filterquotes(command["name"])+quotationmark if "name" in command.keys() else "" })')
                    # print(inputstring[command["id"]])
            if checkstatus or len(commands) > 0:
                client.run('sv_cheats','0')
            outputstring = client.run("autocvar_Lcommandreader") 
            # print("out",outputstring)
            if "☻" in outputstring:
                clearup = client.run("autocvar_Lcommandreader",'""')
                
            
            
    except Exception as e:
        # print("CORE BROKEY SOB",e)
        outputstring = ""
        status = ""
        discordtotitanfall[serverid]["serveronline"] = False
        # return False
        # traceback.print_exc()
    else:
        if not offlinethisloop:
            discordtotitanfall[serverid]["lastheardfrom"] = int(time.time())
    # print("I got here!")
    try:
        if "☻" in outputstring:
            # print(outputstring)
            # print(outputstring)
            outputstring = "☻".join(outputstring.split("☻")[1:-1])
            outputstring = f"☻{outputstring}☻"
            # print("outputstr",outputstring)
            outputs = outputstring.split("☻X☻")
            for output in outputs:
                output = output.split("☻")
                if output[0] == "":
                    del output[0]
                
                # print(output)
                output = {"id":output[0],"command":output[1],"output":output[2],"commandtype":output[3]}
                print(output)
                if output["commandtype"] == "chat_message":
                    # print("here")
                    messageflush.append({
                        "timestamp": int(time.time()),
                        "serverid": serverid,
                        "type": 3,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": output["command"],
                        "metadata": {"type":None},
                        "servername" :context["serveridnamelinks"][serverid]

                    })
                # print(output["commandtype"])
                if output["commandtype"] == "usermessagepfp":
                    
                    outputjson = getjson(output["output"].replace("♥",'"'))
                    # print("here",json.dumps(outputjson,indent = 4))
                    messageflush.append({
                        "timestamp": int(time.time()),
                        "serverid": serverid,
                        "player": outputjson["name"],
                        "type": 1,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": output["command"],
                        "metadata": {**outputjson,"type":output["commandtype"]},
                        "servername" :context["serveridnamelinks"][serverid]

                    })
                if output["commandtype"] == "command_message":
                    # print("here")
                    messageflush.append({
                        "timestamp": int(time.time()),
                        "serverid": serverid,
                        "type": 3,
                        "globalmessage": True,
                        "overridechannel": "commandlogchannel",
                        "messagecontent": output["command"],
                        "metadata": {"type":"tf1command"},
                        "servername" :context["serveridnamelinks"][serverid]

                    })
                if output["commandtype"] == "connect_message":
                    # print("here")
                    messageflush.append({
                        "timestamp": int(time.time()),
                        "serverid": serverid,
                        "type": 4,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": output["command"],
                        "metadata": {"type":"connecttf1"},
                        "servername" :context["serveridnamelinks"][serverid]

                    })
    except Exception as e:
        print("read brokey")
        traceback.print_exc()

            
        # print("outputs",outputs)

    idlist = {}
    messagelist = {}
    for index, commandid in enumerate(discordtotitanfall[serverid]["commands"]):
        idlist[commandid["id"]] = index
    for index, commandid in enumerate(discordtotitanfall[serverid]["messages"]):
        messagelist[commandid["id"]] = index
    messageflag = False
    ids = []
    # print(discordtotitanfall[serverid]["commands"])
    senttoolongmessages =[]
    for key, value in inputstring.items():
        origval = value
        funcprint = None
        # print("rawout",value)
        if "OUTPUT<" in value and "/>ENDOUTPUT" in value:
            value = "".join("".join("".join(value.split("BEGINMAINOUT")[1:]).split("OUTPUT<")[1:]).split("/>ENDOUTPUT")[:-1])
            value = value.replace("☻",'"')
            oldoldvalue = value
            value = getjson(value)
            if isinstance(value, str):
                value = value[0:800]
            elif isinstance(value, bool):
                value = str(value)
            
        else:
            value = value[0:800]
        if "FUNCRETURN<" in origval and "/>FUNCRETURN" in origval:
            funcprint = "".join("".join("".join(origval.split("BEGINMAINOUT")[:1]).split("FUNCRETURN<")[1:]).split("/>FUNCRETURN")[:-1])[0:500]
            if len(funcprint) == 0:
                funcprint = None
        # print("BEEP BOOOOP","".join("".join("".join(origval.split("BEGINMAINOUT")[:1]).split("FUNCRETURN<")[1:]).split("/>FUNCRETURN")[:-1])[0:500])
        print("output from server:",value,funcprint)
        # print("funcout",funcprint)
        if  commands[key]["type"] == "msg" and (value != "sent!" or messageflag):
            continue
        elif commands[key]["type"] == "msg" and value == "sent!":
            # messageflag = True
            if key in toolongmessages:
                senttoolongmessages.append(key)
            # print("BOOP",key,discordtotitanfall[serverid]["returnids"]["messages"][now])
            try:
                # del discordtotitanfall[serverid]["returnids"]["messages"][now]
                del discordtotitanfall[serverid]["returnids"]["messages"][str(key)]#[discordtotitanfall[serverid]["returnids"]["messages"][now].index(key)]
                # if len(discordtotitanfall[serverid]["returnids"]["messages"][now]) == 0:
                    # del discordtotitanfall[serverid]["returnids"]["messages"][now]
            except Exception as e:print("crash while deleting key",e)
            ids.append(commands[key]["id"])
            # print("HEREEEE SENT IT I THINK MABYE")
            discordtotitanfall[serverid]["messages"][messagelist[key]] = False
            continue
        # print(key,"key")
        if funcprint and not isinstance(value,dict): 
            funcoutput =  {"output":{"output":value},"statuscode":200}
        # if funcprint and not isinstance(value,dict): 
            # print("HERE")
            funcoutput["output"]["funcprint"] = funcprint
        else:
            funcoutput =  {"output":value,"statuscode":200}
        
        discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)] = funcoutput
        # discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)]["output"] = value
        # discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)]["statuscode"] = "0"
        # print(discordtotitanfall[serverid]["commands"])
        try:
            discordtotitanfall[serverid]["commands"][idlist[key]] = "hot potato"
        except:
            print("race condition probably")
    discordtotitanfall[serverid]["commands"] = list(filter(lambda x: x != "hot potato",discordtotitanfall[serverid]["commands"]))
    discordtotitanfall[serverid]["messages"] = list(filter(lambda x: x,discordtotitanfall[serverid]["messages"]))
    asyncio.run_coroutine_threadsafe(reactomessages(list(ids), serverid), bot.loop)
    discordtotitanfall[serverid]["serveronline"] = not offlinethisloop
    if senttoolongmessages:
             asyncio.run_coroutine_threadsafe(reactomessages(senttoolongmessages, serverid,"✂️"), bot.loop)

    return True
    
# test if ; breaks things and ()
def tf1relay():
    global context
    global discordtotitanfall
    if TF1RCONKEY == "":
        return
    
    print("Running tf1rcon support!")
    # with Client('127.0.0.1', 37019, passwd='pass',timeout=5) as client:
    #     response = client.run('sv_cheats','1')
    #     response = client.run("script", 'Lrconcommand("sendmessage","WOQWOFKQFQWspace",34,"lexi")')
        
    # print(response,"woqdoqw")
    servers = []
    for server,value in context["istf1server"].items():
        if value:
            initdiscordtotitanfall(server)
            servers.append(server)
            discordtotitanfall[server]["ip"] = value
            # print(context["istf1server"],value,discordtotitanfall[server]["ip"].split(":")[0], discordtotitanfall[server]["ip"].split(":")[1])
            # discordtotitanfall[server]["client"] = Client(discordtotitanfall[server]["ip"].split(":")[0], discordtotitanfall[server]["ip"].split(":")[1], passwd=TF1RCONKEY,timeout=1.5)
    i = 0
    while True:
        i += 1
        time.sleep(1)
        for server in servers:
            # print("boop")
            # print("meow",server)
            if discordtotitanfall[server].get("serveronline",True) == True or i % 10 == 0:
                # try:print((discordtotitanfall[server]["serveronline"]))
                # except:print(list(discordtotitanfall[server].keys()))
                threading.Thread(target=tf1readsend, daemon=True, args=(server,i%10 == 0)).start()

  
            # response = discordtotitanfall[server]["client"].run('sv_cheats1;script Lrconcommand("sendmessage","OWOWOOWOWOOW")')
          

def messageloop():
    global messageflush, lastmessage,discordtotitanfall, context,messageflushnotify,reactedyellowtoo
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
                        user.send(discord.utils.escape_mentions(message["sendingmessage"])), bot.loop
                    )
        except Exception as e:
            time.sleep(3)
            traceback.print_exc()
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
                        and message["serverid"] != "-100"
                    ):
                        addflag = True
                        # print(message)
                        # print(list( context["serverchannelidlinks"].keys()),   message["serverid"])

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
                # print(messageflush)
                for message in messageflush:
                    message.setdefault("globalmessage",False)
                    message.setdefault("type",3)
                    message.setdefault("overridechannel",None)
                    # print("MESSAGE",message)
                    messagewidget,playername = getmessagewidget(message["metadata"],message["serverid"],message["messagecontent"],message)
                    if messagewidget == "":
                        # print("here")
                        continue
                    if message["serverid"] not in output.keys() and not message["globalmessage"]:
                        # print("a")
                        output[message["serverid"]] = []
                    elif message["globalmessage"] and message["overridechannel"] not in output.keys():
                        # print("b")
                        output[message["overridechannel"]] = []
                    if ("\033[") in messagewidget:
                        print("colour codes found in message")
                        while "\033[" in messagewidget:
                            startpos = messagewidget.index("\033[")
                            if "m" not in messagewidget[startpos:]:
                                break
                            endpos = (
                                messagewidget[startpos:].index("m")
                                + startpos
                            )
                            messagewidget = (
                                messagewidget[:startpos]
                                + messagewidget[endpos + 1 :]
                            )
                    
                    messageadders = {"pfp":message["metadata"].get("pfp",None),"name":playername,"type":message["metadata"]["type"],"uid":message["metadata"].get("uid",None),"originalname":str(message.get("player",False))}
                    if message["metadata"]["type"] == "usermessagepfp" and USEDYNAMICPFPS == "1":
                        message["type"] = 3
                    # else: messageadders = {"type":message["metadata"]["type"]}
                    if message["type"] == 1:
                        # print("c")
                        output[message["serverid"] if not message["globalmessage"] else message["overridechannel"]].append(
                            {"message": f"**{playername}**: {messagewidget}",**messageadders,"messagecontent":messagewidget}
                        )
                        # print(f"**{playername}**:  {messagewidget}")
                    elif message["type"] == 2:
                        # print("d")
                        output[message["serverid"] if not message["globalmessage"] else message["overridechannel"]].append(
                            {"message": f"""```{playername} {messagewidget}```""",**messageadders,"messagecontent":messagewidget}
                        )
                        # print(f"""{playername} {messagewidget}""")
                    elif message["type"] == 3:
                        # print("e")
                        output[message["serverid"] if not message["globalmessage"] else message["overridechannel"]].append(
                            {"message": f"{messagewidget}",**messageadders,"messagecontent":messagewidget}
                        )
                        # print(f"{messagewidget}")
                    elif message["type"] == 4:
                        # print("f")
                        output[message["serverid"] if not message["globalmessage"] else message["overridechannel"]].append(
                            {"message": f"```{messagewidget}```",**messageadders,"messagecontent":messagewidget}
                        )
                        # print(f"{messagewidget}")
                    else:
                        print("type of message unkown")
                        continue
                    realprint("\033[0m", end="")
                if output:
                    print("sending output",json.dumps(output, indent=4))
                for serverid in output.keys():
                    for key,message in enumerate(output[serverid]):
                        isbad = checkifbad(message)
                        if isbad[0]:
                            print("horrible message found")
                            output[serverid][key]["isbad"] = isbad
                    # print("OUTPUT",output)
                    # print("sending to", serverid)
                    if serverid not in context["serverchannelidlinks"].keys() and serverid not in context["overridechannels"].keys():
                        print("channel not in bots known channels")
                        continue
                    channel = bot.get_channel(context["serverchannelidlinks"][serverid]) if  serverid in context["serverchannelidlinks"].keys() else bot.get_channel(context["overridechannels"][serverid])
                    if channel is None:
                        print("channel not found")
                        continue
                    # # to save my sanity, I'm going to throw the order out for pfp messages, so I can group them and make them a wee bit more compact, if somone is REALLY sending a lot of messages 
                    userpfpmessages ={}
                    for message in list(filter(lambda x: x["type"] == "usermessagepfp" and USEDYNAMICPFPS == "1",output[serverid])):
                        if not message["pfp"] or not message["name"] or not message["uid"]:
                            print("VERY BIG ERROR, PLEASE LOOK INTO IT",message)
                            continue
                        userpfpmessages.setdefault(message["name"],{"messages":[],"pfp":message["pfp"],"uid":message["uid"],"originalname":message["originalname"]})
                        userpfpmessages[message["name"]]["messages"].append({"message":message["message"],"isbad":message.get("isbad",[0,0]),"messagecontent":message["messagecontent"]})
               
                    asyncio.run_coroutine_threadsafe(sendpfpmessages(channel,userpfpmessages,serverid),bot.loop)
                
                    asyncio.run_coroutine_threadsafe(outputmsg(channel, output, serverid, USEDYNAMICPFPS), bot.loop )
                messageflush = []
                lastmessage = time.time()
            now = int(time.time()*100)
            # WHAT ON EARTH IS THIS AND HOW ON EARTH DOES IT WORK
            for serverid in discordtotitanfall.keys():
                iterator = 0
                while iterator < len(discordtotitanfall[serverid]["returnids"]["messages"].keys()):
                    key = list(discordtotitanfall[serverid]["returnids"]["messages"].keys())[iterator]
                    value = [int(x) for x in discordtotitanfall[serverid]["returnids"]["messages"][key]]
                    # print("key",key)
                    iterator += 1

                    if type(key) == int and int(key) < now-300:
                        if len(value) > 0:
                            reactedyellowtoo.extend(value)
                            reactedyellowtoo = reactedyellowtoo[-200:]
                            # print("running this",value,serverid,key,now)
                            asyncio.run_coroutine_threadsafe(reactomessages(value, serverid, "🟡"), bot.loop)
                        del discordtotitanfall[serverid]["returnids"]["messages"][key]
                        iterator -= 1
                    elif type(key) == str and value[0]  < now - 300:
                        reactedyellowtoo.extend(value)
                        reactedyellowtoo = reactedyellowtoo[-200:]
                        # print("running this2",value,serverid,key,now)
                        asyncio.run_coroutine_threadsafe(reactomessages([key], serverid, "🟡"), bot.loop)
                        del discordtotitanfall[serverid]["returnids"]["messages"][key]
                        iterator -= 1
                    # print(type(key) == str,value[0] - (now - 300))



        except Exception as e:
            time.sleep(3)
            traceback.print_exc()
            print("bot not ready", e)
        time.sleep(0.1)

def checkifbad(message):
    global context
    if message["type"] not in FILTERNAMESINMESSAGES.split(","):
        return [0,0]
    lowered = message["message"].lower()
    wordfilter = context.get("wordfilter", {})
    banwords = wordfilter.get("banwords", [])
    notifywords = wordfilter.get("notifybadwords", [])
    def checknono(words, text):
        for word in words:
            if word.startswith("/") and word.endswith("/") and len(word) > 2:
                try:
                    pattern = re.compile(word[1:-1], re.IGNORECASE)
                    if pattern.search(text):
                        return word
                except re.error:
                    continue
            else:
                if word.lower() in text:
                    return word
        return False
    if checknono(banwords, lowered):
        # print("here")
        return [2,checknono(banwords, lowered)]
    elif checknono(notifywords, lowered):
        # print("here2",checknono(notifywords, lowered))
        return [1,checknono(notifywords, lowered)]
    if message.get("name"):
        # print("MESSAGENAME",message["name"])
        name_lowered = message["name"].lower()
        if checknono(banwords, name_lowered):
            # print("here3")
            return [2,checknono(banwords, name_lowered)]
        elif checknono(notifywords, name_lowered):
            # print("here4")
            return [1,checknono(notifywords, name_lowered)]

    return [0,0]

async def outputmsg(channel, output, serverid, USEDYNAMICPFPS):
    global context

    content = discord.utils.escape_mentions(
        "\n".join(
            x["message"]
            for x in output[serverid]
            if x["type"] != "usermessagepfp" or USEDYNAMICPFPS != "1"
        )
    )
    if not content:
        return

    message = await channel.send(content)
    # print(f"Sent message ID: {message.id}")
    # print("OUTPUT",output[serverid])
    await checkfilters(output[serverid], message)


async def checkfilters(messages, message):
    try:
        global context
        # print(messages)
        message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        notify_channel_id = context["overridechannels"].get("wordfilternotifychannel")
        notify_channel = bot.get_channel(notify_channel_id) if notify_channel_id else None

        if not notify_channel:
            return

        bad_msg = next((x for x in messages if x.get("isbad", [0,0])[0] == 2), None)
        if bad_msg:
            print("BAN MESSAGE FOUND",json.dumps(bad_msg,indent = 4))
            if bad_msg["originalname"] and bad_msg.get("uid",False) and bad_msg["messagecontent"]:
                await notify_channel.send(
                discord.utils.escape_mentions(f""">>> **Ban word found**
    Sent by: **{bad_msg['originalname']}**
    UID: **{bad_msg['uid']}**
    Message: "{bad_msg['messagecontent']}"
    Found pattern: "{bad_msg['isbad'][1]}"
    Message Link: {message_link}""")
            )
            else:

                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Ban word found**
    Message: "{bad_msg['message']}"
    Found pattern: "{bad_msg['isbad'][1]}"
    Message Link: {message_link}""")
                )

        notify_msg = next((x for x in messages if x.get("isbad", [0.0])[0] == 1), None)
        # print("HERE")
        if notify_msg:
            print("NOTIFY MESSAGE FOUND",json.dumps(notify_msg,indent = 4))
            # print("HERE2")
            if notify_msg["originalname"] and notify_msg.get("uid",False) and notify_msg["messagecontent"]:
                # print("HERE3")
                await notify_channel.send(
                discord.utils.escape_mentions(f""">>> **Filtered word found**
    Sent by: **{notify_msg['originalname']}**
    UID: **{notify_msg['uid']}**
    Message: "{notify_msg['messagecontent']}"
    Found pattern: "{notify_msg['isbad'][1]}"
    Message Link: {message_link}""")
            )
            else:
                # print("HERE4")

            # print("NOTIFY",notify_msg)
                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Filtered word found**
    Message: "{notify_msg['message']}"
    Found pattern: "{notify_msg['isbad'][1]}"
    Message Link: {message_link}""")
                )
            # print("HERE5")
    except Exception as e:
        print("ERROR",e)
        traceback.print_exc()
        

# name_dict = {
#     '$"models/humans/pilots/pilot_medium_geist_m.mdl"': "grapple",
#     '$"models/humans/pilots/pilot_medium_geist_f.mdl"': "grapple",
#     '$"models/titans/medium/titan_medium_ajax.mdl"': "ion",
#     '$"models/titans/heavy/titan_heavy_ogre.mdl"': "scorch",
#     '$"models/titans/light/titan_light_raptor.mdl"': "northstar",
#     '$"models/titans/light/titan_light_locust.mdl"': "ronin",
#     '$"models/titans/medium/titan_medium_wraith.mdl"': "tone",
#     '$"models/humans/pilots/pilot_heavy_drex_f.mdl"': "cloak",
#     '$"models/titans/heavy/titan_heavy_deadbolt.mdl"': "legion",
#     '$"models/titans/medium/titan_medium_vanguard.mdl"': "monarch",
#     '$"models/titans/medium/titan_medium_ion_prime.mdl"': "ion prime",
#     '$"models/titans/heavy/titan_heavy_scorch_prime.mdl"': "scorch",
#     '$"models/titans/light/titan_light_northstar_prime.mdl"': "northstar",
#     '$"models/titans/light/titan_light_ronin_prime.mdl"': "ronin",
#     '$"models/titans/medium/titan_medium_tone_prime.mdl"': "tone",
#     '$"models/titans/heavy/titan_heavy_legion_prime.mdl"': "legion",
#     '$"models/humans/pilots/pilot_heavy_roog_m.mdl"': "awall",
#     '$"models/humans/pilots/pilot_heavy_roog_f.mdl"': "awall",
#     '$"models/humans/pilots/pilot_medium_reaper_m.mdl"': "pulse",
#     '$"models/humans/pilots/pilot_medium_reaper_f.mdl"': "pulse",
#     '$"models/humans/pilots/pilot_light_jester_m.mdl"': "stim",
#     '$"models/humans/pilots/pilot_light_jester_f.mdl"': "stim",
#     '$"models/humans/pilots/pilot_light_ged_m.mdl"': "phase",
#     '$"models/humans/pilots/pilot_light_ged_f.mdl"': "phase",
#     '$"models/humans/pilots/pilot_medium_stalker_m.mdl"': "holo",
#     '$"models/humans/pilots/pilot_medium_stalker_f.mdl"': "holo",
#     "unknown": "unknown/unkownpfp.png"
# }

pilotstates = {}
# PFPROUTE
async def sendpfpmessages(channel,userpfpmessages,serverid):
    global pilotstates
    try:
        if not userpfpmessages:
            return

        webhooks = await channel.webhooks()
        webhook = None
        webhook2 = None
        for wh in webhooks:
            if wh.name == "ChatBridge":
                webhook = wh
            if wh.name == "ChatBridge2":
                webhook2 = wh
        # print(userpfpmessages)
        if webhook is None:
            webhook = await channel.create_webhook(name="ChatBridge")
        if webhook2 is None:
            webhook2 = await channel.create_webhook(name="ChatBridge2")
        actualwebhooks = {"ChatBridge":webhook,"ChatBridge2":webhook2}
        for username, value in userpfpmessages.items():
            # print("Sending as:", username)
            # print("Message:", "\n".join(value["messages"]))
            pilotstates.setdefault(serverid,{"uid":-1,"model":None,"webhook":"ChatBridge"})
            if pilotstates[serverid]["uid"] == value["uid"] and str(value["pfp"]) != pilotstates[serverid]["model"]:
                if pilotstates[serverid]["webhook"] == "ChatBridge":
                    pilotstates[serverid]["webhook"] = "ChatBridge2"
                else:
                    pilotstates[serverid]["webhook"] = "ChatBridge"
            pilotstates[serverid] = {"uid":value["uid"],"model":str(value["pfp"]),"webhook":pilotstates[serverid]["webhook"]}
            # print("here")
            pfp = MODEL_DICT.get(str(value["pfp"]),"unknown/confused.jpg")
            if pfp == "unknown/confused.jpg" and (str(value["pfp"].startswith("true")) or str(value["pfp"].startswith("false"))):
                print("FALLING BACK TO GUESSING")
                for model, valuew in MODEL_DICT.items():
                    if str(value["pfp"])[6:] in model:
                        print("setting pfp too",pfp)
                        pfp = valuew
                        break
            # print("SENDING PFP MESSAGE","\n".join(list(map(lambda x: x["message"],value["messages"]))),f'{PFPROUTE}{pfp}')
            
            async with aiohttp.ClientSession() as session:
                # print(pilotstates[serverid])
                message = await actualwebhooks[pilotstates[serverid]["webhook"]].send(
                    "\n".join(list(map(lambda x: x["message"],value["messages"]))),#+" "+pilotstates[serverid]["webhook"],
                    username=f"{username}",
                    avatar_url=f'{PFPROUTE}{pfp}',
                    wait = True
                )
            await checkfilters(list(map(lambda x: {"isbad":x["isbad"],"messagecontent":x["messagecontent"],"message":f"{username}: {x['message']}","originalname":value["originalname"],"uid":value["uid"]},value["messages"])),message)
    except Exception as e:
        print("WEBHOOK CRASH",e)
        traceback.print_exc()

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

def resolveplayeruidfromdb(name,uidnameforce = None,oneuidpermatch = False):
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
            c.execute("SELECT playeruid, playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC", (name,))
            output = c.fetchall()
            if not output:
                tfdb.commit()
                tfdb.close()
                
    
                return []

            data = [{"name": x[1], "uid": x[0]} for x in output]
        players = []
        uids = []
        for x in data:
            if not oneuidpermatch or x["uid"] not in uids:
                players.append(x)
                uids.append(x["uid"])

        tfdb.commit()
        tfdb.close()

        if len(players) == 0:
            return []
        return  sorted(players, key=lambda x: len(x["name"]))
        

async def returncommandfeedback(serverid, id, ctx,overridemsg = defaultoverride, iscommandnotmessage = True,logthiscommand = True):
    # print(serverid, id, ctx,overridemsg)
    if not overridemsg:
        overridemsg = defaultoverride
    i = 0
    while i < 200:
        await asyncio.sleep(0.05)
        if str(id) in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys():
            if logthiscommand:
                print(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)])
            if overridemsg:
                try:
                   
                    realmessage = overridemsg(discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["output"], serverid,discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]["statuscode"] )
           
                    if not realmessage:
                        overridemsg = None
                        return
                except Exception as e:
                    print("error in overridemsg", e)
                    traceback.print_exc()
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
    # SERVERNAMEISCHOICE
    if SERVERNAMEISCHOICE == "1":
        servername_param = f'servername: Option(str, "The servername (omit for current channel\'s server)", required=False ,choices=list(context["serveridnamelinks"].values())) = None'
    else:
        servername_param = f'servername: Option(str, "The servername (omit for current channel\'s server)", required=False) = None'
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
    global messageflush, context
    if {rcon} and not checkrconallowed(ctx.author):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
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
    messageflush.append({{
        "timestamp": int(time.time()),
        "serverid": serverid,
        "type": 3,
        "globalmessage": True,
        "overridechannel": "commandlogchannel",
        "messagecontent": command,
        "metadata": {{"type":"command"}},
        "servername" :context["serveridnamelinks"][serverid],
        "player":  f"`BOT COMMAND` sent by {{ctx.author.name}}"
    }})
    await returncommandfeedback(*sendrconcommand(serverid, command), ctx, {outputfunc_expr})
'''

    exec(func_code, globals())
    return globals()[command_name]




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
        # servername: Option(
        #     str, "The servername (omit for current channel's server)", required=False
        # ) = None,
    ):
        
        global context, discordtotitanfall, lasttimethrown, aibotmessageresponses
        servername = None
        messagehistory = []
        keyaireply = random.randint(1,10000000000000)
        aibotmessageresponses[keyaireply] = []
        print("thrownonrcon command from", ctx.author.id, "to", playername)
        serverid = getchannelidfromname(servername, ctx)
        if serverid is None:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
            return
        if ctx.author.id in lasttimethrown["passes"].keys() and lasttimethrown["passes"][ctx.author.id] > time.time() - 60:
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
- if you succeed, you are allowed to freely use the command for 60 seconds''')
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
The user is asking to use a command on a titanfall 2 sever. this command throws a targeted player into the air, in the game Titanfall 2. Your role is to be skeptical that the user needs to use this command, due to the fact that it can be seen as unfair or even unfun by the targeted player(s).
If the user has a reason that you deem would bring GREAT value however, don't hesitate to press the "allow_request button". This will allow the command to be executed. HOWEVER YOU SHOULD HAVE EXTREME PREJUDICE AGAINST USING THIS BUTTON. ALMOST NEVER ALLOW IT, ESPECIALLY IF THE USER HAS BEEN ALLOWED OR DENIED RECENTLY.
If you believe the user might make a good case to deserve using the command, with good reasoning, press "more_information_needed".
If you believe the user is trying to mislead you (they probably are), is undeserving, is too rude, is trying to get a competitive advantage, or simply have the feeling of being powerful, press "deny_request".
ENQUIRE A LOT ABOUT LARGE CLAIMS. the user is probably LYING. and so you should "deny_request"

You will be expected to press exactly one of those 3 choices after each request, and also give a one - two sentence reason as to why, and a single word reason for the choice.
In order to do this, format your output exactly like this, otherwise it will fail to be parsed.
"{{"reason":"YOUR_REASON_HERE","button":"YOUR_BUTTON_PRESSED","reasononeword":"ONE_WORD_REASON"}}"
For example:
"{{"reason":"I believe your reasoning to use /throw holds water. you provided a concise argument that clearly displayed your intentions with the command","button":"allow_request,"reasononeword":"coherent"}}"

"{{"reason":"I feel your arguments are flawed, and you intend to use this for other purposes than stated.","button":"deny_request","reasononeword":"misleading"}}"

"{{"reason":"You make a interesting point, however your points are not fully explained. could you expand upon why you think this would be comedic?","button":"more_information_needed","reasononeword":"incomplete"}}"

Some more information:
If you do not come to a conclusion after 5 messages from the user, the request will be denied.
KEEP RESPONSE BELOW 2000 CHARACTERS
The player that is targeted is "{playername}" (if this is "all", the user is attempting to throw EVERYONE ON THE SERVER. make this request need a VERY strong line of reasoning due to the EXTREME IMPACT this will have. however still intend to clear it up in 5 messages. (do not be afraid to query more information) TO BE SAFE, ALWAYS DENY REQUESTS FOR "all".
The player that used this command is "{ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}"
{"The last time the user tried to use this command was: " + str(int(time.time()-lasttimethrown["specificusers"][ctx.author.id][-1]["timestamp"])) + " seconds ago, and you responded " + lasttimethrown["specificusers"][ctx.author.id][-1]["button"] +" due to " + lasttimethrown["specificusers"][ctx.author.id][-1]["one_word_reason"]if ctx.author.id in lasttimethrown["specificusers"].keys() else "This is the first time the user has tried to use this command. (since bot restart)"}
{historyinfo} 
base your leniance on this info too - if you have allowed the request a lot in the past hour, do you really need to allow more? You may need to enquire about this.
if the user has been using the command a lot recently as well, they most likely do not deserve to use it again.
Lastly:
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
            response = requests.post(f"http://{LOCALHOSTPATH}:11434/api/generate", json = {"prompt": prompt,"model":DISCORDBOTAIUSED,"stream":False,"keep_alive":"12000m","seed":0,"temperature":1,"options":{"num_predict":-1}})
            print(response.json()["response"])
            output = response.json()["response"]
            output = output[output.index("</think>")+8:].strip()
            output = json.loads(output)
            aibotmessageresponses[keyaireply].append((output))
            print("done, responding")
        except Exception as e:
            print("ai crashed, error is:",e)
            traceback.print_exc()
            output = {"button":"deny_request","reason":"ai broken. "+ str(e),"reasononeword":"broken"}
            aibotmessageresponses[keyaireply].append(output)
        asyncio.run_coroutine_threadsafe(aireplytouser(message,output),bot.loop)
        

    async def aireplytouser(message,output):
        await message.reply(f"**button pressed by AI:**```{output['button']}``` \n**Reason:** ```{output['reason']}```\n**Short reason:**```{output['reasononeword']}```")
# joinleave logging stuff
playercontext = {}
matchids = []
playerjoinlist = {}

def checkandaddtouidnamelink(uid, playername):
    global playercontext
    now = int(time.time())
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute(
        "SELECT id, playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",(uid,))
    row = c.fetchone()
    if row:
        last_id, last_name = row
        if str(playername) == str(last_name):
            c.execute(
                "UPDATE uidnamelink SET lastseenunix = ? WHERE id = ?",(now, last_id))
        else:
            c.execute(
                "INSERT INTO uidnamelink (playeruid, playername, firstseenunix, lastseenunix) VALUES (?, ?, ?, ?)",(uid, playername, now, now))
    else:
        c.execute(
            "INSERT INTO uidnamelink (playeruid, playername, firstseenunix, lastseenunix) VALUES (?, ?, ?, ?)",(uid, playername, now, now))
    tfdb.commit()
    tfdb.close()


def onplayerjoin(uid,serverid,nameof = False):
    global context,messageflushnotify,playerjoinlist
    print("joincommand", uid, serverid)
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
        # c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(uid,nameof))
        checkandaddtouidnamelink(uid,nameof)
        tfdb.commit()
    if nameof:
        playername = nameof
    else:
        playername = f"Unknown user by uid {uid}"
    # print(f"{uid}{playername}",playerjoinlist)
    if f"{uid}{playername}" in playerjoinlist.keys() and playerjoinlist[f"{uid}{playername}"]:
        print("already in list")
        return
    c.execute("SELECT count FROM joincounter WHERE playeruid = ? AND serverid = ?",(uid,serverid))
    count = c.fetchone()
    if count:
        count = count[0] + 1
        c.execute("UPDATE joincounter SET count = ? WHERE playeruid = ? AND serverid = ?",(count,uid,serverid))
    else:
        c.execute("INSERT INTO joincounter (playeruid,serverid,count) VALUES (?,?,1)",(uid,serverid))
    tfdb.commit()

    
    if discordnotify:
        discordnotify = [x[0] for x in discordnotify]
    servername = context["serveridnamelinks"][serverid]

    playerjoinlist[f"{uid}{playername}"] = True
    for discordid in discordnotify:
        print("notifying join",discordid)
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
    print("leavecommand",uid,serverid)
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
        print("notifying leave",discordid)
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


def savestats(saveinfo):
    # 1 is normal, they just left
    # 2 is map change
    # 3 is server crash
    # 4 is tempory save
    global playercontext
    print("saving playerinfo",saveinfo)
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    try:
        c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["uid"],))
        playernames = c.fetchall()
        if playernames:
            playernames = [x[0] for x in playernames]
        if playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["name"] not in playernames or not playernames:
            # c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["uid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["name"]))
            checkandaddtouidnamelink(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["uid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["name"])
        if playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["idoverride"] != 0:
            c.execute("UPDATE playtime SET leftatunix = ?, endtype = ?, scoregained = ?, titankills = ?, pilotkills = ?, deaths = ?, duration = ? WHERE id = ?",(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"],saveinfo["endtype"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["score"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["titankills"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["kills"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["deaths"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"]-playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["joined"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["idoverride"]))
            lastrowid = playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["idoverride"]
        else:
            c.execute("INSERT INTO playtime (playeruid,joinatunix,leftatunix,endtype,serverid,scoregained,titankills,pilotkills,npckills,deaths,map,duration,matchid,timecounter ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["uid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["joined"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"],saveinfo["endtype"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["serverid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["score"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["titankills"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["kills"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["npckills"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["deaths"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["map"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"]-playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["joined"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["matchid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["timecounter"]))
            lastrowid = c.lastrowid
    except Exception as e:
        print("error in saving",e)
        traceback.print_exc()
        return 0
    if saveinfo["endtype"] == 1 or saveinfo["endtype"] == 2:
        playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["playerhasleft"] = True
    if saveinfo["endtype"] != 4:
        pass
    playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["mostrecentsave"] = True
    playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["idoverride"] = lastrowid
    
    tfdb.commit()
    tfdb.close()
    return lastrowid

def addmatchtodb(matchid,serverid,currentmap):
    global matchids,playercontext
    print("adding match to db",matchid,serverid)
    tfdb = sqlite3.connect("./data/tf2helper.db")
    c = tfdb.cursor()
    c.execute("SELECT matchid FROM matchid WHERE matchid = ?",(matchid,))
    matchidcheck = c.fetchone()
    if matchidcheck:
        if serverid not in playercontext.keys():
            playercontext[serverid] = {}
        print("already in db, loading data")
        c.execute("SELECT playeruid,joinatunix,leftatunix,endtype,serverid,scoregained,titankills,pilotkills,npckills,deaths,map,duration,id,timecounter FROM playtime WHERE matchid = ?",(matchid,))
        matchdata = c.fetchall()
        c.execute("SELECT playername,playeruid FROM uidnamelink")
        playernames = c.fetchall()
        playernames = {str(x[1]):x[0] for x in playernames}
        for player in matchdata:
            player = list(player)
            player[0] = str(player[0])
            player[4] = str(player[4])
            print("loading player data",player[0])
            if player[0] not in playercontext[serverid]:
                playercontext[serverid][player[0]] = {}
            if player[0] in playernames.keys() and playernames[player[0]] not in playercontext[serverid][player[0]].keys():
                playercontext[serverid][player[0]][playernames[player[0]]] = {}
            else:
                pass
                # print("panic")
                # print(player[0],playernames[player[0]],playercontext[serverid][player[0]],playernames, player[0] in playernames.keys(),playernames[player[0]] not in playercontext[serverid][player[0]].keys())
                #print(list(playernames.keys()),[ player[0]])
                continue
            if matchid not in playercontext[serverid][player[0]][playernames[player[0]]]:
                playercontext[serverid][player[0]][playernames[player[0]]][matchid] = []
            playercontext[serverid][player[0]][playernames[player[0]]][matchid].append({
                "uid":player[0],
                "name":playernames[player[0]],
                "joined":player[1],
                "endtime":player[2],
                "serverid":player[4],
                "score":player[5],
                "titankills":player[6],
                "kills":player[7],
                "npckills":player[8],
                "deaths":player[9],
                "map":player[10],
                "idoverride":player[12],
                "matchid":matchid,
                "playerhasleft": player[3] == 1,
                "mostrecentsave": True,
                "loadedfromsave": True,
                "timecounter": player[13]
            })
        matchids.append(matchid)
        return
    c.execute("INSERT INTO matchid (matchid,serverid,map,time) VALUES (?,?,?,?)",(matchid,serverid,currentmap,int(time.time())))
    
    tfdb.commit()
    tfdb.close()
    matchids.append(matchid)

def playerpolllog(data,serverid,statuscode):
    # print("playerpoll",serverid,statuscode)
    Ithinktheplayerhasleft = 90
    global discordtotitanfall,playercontext,playerjoinlist,matchids
    # save who is playing on the specific server into playercontext.
    # dicts kind of don't support composite primary keys..
    # use the fact that theoretically one player can be on just one server at a time
    # playerid+playername = primary key. this is because of the edge case where people join one server on one account twice because.. well they do that sometimes
    # print(data,serverid,statuscode)
    currentmap = data["meta"][0]
    matchid = data["meta"][2]
    if matchid not in matchids:
        addmatchtodb(matchid,serverid,currentmap)
    now = int(time.time())
    # players = [lambda x: {"uid":x[0],"score":x[1][0],"team":x[1][1],"kills":x[1][2],"deaths":x[1][3],"name":x[1][4],"titankills":x[1][5],"npckills":x[1][6]} for x in list(filter(lambda x: x[0] != "meta",list(data.items())))]
    players = [{"uid":x[0], "score":x[1][0], "team":x[1][1], "kills":x[1][2], "deaths":x[1][3], "name":x[1][4], "titankills":x[1][5], "npckills":x[1][6],"timecounter":x[1][7]} for x in list(filter(lambda x: x[0] != "meta", list(data.items())))]
    # playercontext[pinfo["uid"]+pinfo["name"]] = {"joined":now,"map":map,"name":pinfo["name"],"uid":pinfo["uid"],"idoverride":0,"endtime":0,"serverid":serverid,"kills":0,"deaths":0,"titankills":0,"npckills":0,"score":0}
    # print(list(map(lambda x: x["name"],players)))
    uids =list(set( [*list(map(lambda x: x["uid"],players))]))
    names = list(set( [*list(map(lambda x: x["name"],players))]))
    # print("serverid",[serverid])
    if serverid not in playercontext.keys():
        playercontext[serverid] = {}
    for player in players:
        if player["uid"] not in playercontext[serverid]:
            playercontext[serverid][player["uid"]] = {}
        if player["name"] not in playercontext[serverid][player["uid"]]:
            playercontext[serverid][player["uid"]][player["name"]] = {}
        if matchid not in playercontext[serverid][player["uid"]][player["name"]]:
            # print("playercontext[serverid]",json.dumps(playercontext[serverid],indent=4))
            # print([player["uid"]],list(playercontext[serverid].keys()))
            # print("here")
            # onplayerjoin(player["uid"],serverid,player["name"])
            checkandaddtouidnamelink(player["uid"],player["name"])
            playercontext[serverid][player["uid"]][player["name"]][matchid] = [{  #ON FIRST MAP JOIN
                "joined": player["timecounter"],  #FOR BOTH JOINED CASES, TEST CHANGINT IT TO INT(PLAYER["TIMECOUNTER"])
                "map": currentmap,
                "name": player["name"],
                "uid": player["uid"],
                "idoverride": 0,
                "endtime": now+1,
                "serverid": serverid,
                "kills": 0,
                "deaths": 0,
                "titankills": 0,
                "npckills": 0,
                "score": 0,
                "matchid": matchid,
                "mostrecentsave": False,
                "playerhasleft": False,
                "timecounter": player["timecounter"]
            }]
        elif playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["playerhasleft"] or  playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["timecounter"] != player["timecounter"]:
            # print("here2")
            if not  playercontext[serverid][player["uid"]][player["name"]][matchid][-1].get("loadedfromsave",False):
                onplayerjoin(player["uid"],serverid,player["name"])
            # print("beep boop",playercontext[serverid][player["uid"]][player["name"]][matchid][-1].get("loadedfromsave",False),playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["playerhasleft"], playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["timecounter"] != player["timecounter"])
            playercontext[serverid][player["uid"]][player["name"]][matchid].append({ #ON JOINING AFTER LEAVING
                "joined": player["timecounter"],
                "map": currentmap,
                "name": player["name"],
                "uid": player["uid"],
                "idoverride": 0,
                "endtime": now+1,
                "serverid": serverid,
                "kills": 0,
                "deaths": 0,
                "titankills": 0,
                "npckills": 0,
                "score": 0,
                "matchid": matchid,
                "mostrecentsave": False,
                "playerhasleft": False,
                "timecounter": player["timecounter"]
            })
        else:
            # print("here3")
            playercontext[serverid][player["uid"]][player["name"]][matchid][-1] = { #ON NOT LEAVING
                **playercontext[serverid][player["uid"]][player["name"]][matchid][-1],
                "endtime": now,
                "kills": player["kills"],
                "deaths": player["deaths"],
                "titankills": player["titankills"],
                "npckills": player["npckills"],
                "score": player["score"],
                "mostrecentsave": False,
            }
        # DISCOVER MISSING PLAYERS
    # print("boop")
    # print("playercontext[serverid]",json.dumps(playercontext[serverid],indent=4))
    to_delete = []  # Store (uid, name, matchidofsave) to delete after the loop
    # print(json.dumps(playercontext[serverid], indent=4))
    for uid, value in playercontext[serverid].items():
        # if uid in uids:
        #     continue
        for name, value2 in value.items():
            # if name in names:
            #     continue
            for matchidofsave, value3 in value2.items():
                # if len(value3) != 0 and value3[-1]["serverid"] != serverid:
                #     print("breaking, wrong server")
                #     break
                for index,value4 in enumerate(value3):
                    if  (now - value4["endtime"] < Ithinktheplayerhasleft and matchidofsave == matchid and index == len(value3) - 1):
                        # print("not saving1", uid, name, matchidofsave)
                        continue

                    if  value3[-1]["mostrecentsave"] == True and (value3[-1]["playerhasleft"] == True or matchidofsave != matchid):
                            # print("not saving2", uid, name, matchidofsave)
                            # Mark for deletion
                            to_delete.append((uid, name, matchidofsave))
                            continue
                    # print("here4")
                    if value4["mostrecentsave"] == False:
                        print("SAVING", uid, name, matchidofsave,index)
                        if matchid != matchidofsave:
                            savestats({"uid": uid, "name": name, "matchid": matchidofsave, "endtype": 2, "index": index, "serverid": serverid})
                        elif matchid == matchidofsave:
                            if index == len(value3) - 1:
                                onplayerleave(uid, serverid)
                            savestats({"uid": uid, "name": name, "matchid": matchidofsave, "endtype": 1, "index": index, "serverid": serverid})
                

    # Perform deletions after the loop
    for uid, name, matchidofsave in to_delete:
        print("deleting", uid, name, matchidofsave)
        try:
            del playercontext[serverid][uid][name][matchidofsave]
            if not playercontext[serverid][uid][name]:
                del playercontext[serverid][uid][name]
            if not playercontext[serverid][uid]:
                del playercontext[serverid][uid]
        except KeyError:
            # Optional: log or silently skip in case something was already deleted
            pass

                # value[3][-1]["playerhasleft"] = True  CHANGE THIS INSIDE THE SAVE FUNCTION ITSELF
                # value[3][-1]["mostrecentsave"] = True
                # At this point, all of these values should be saved. Either: is a old match, OR the player has left
    # i,j,k = 0,0,0
    # while i < len(playercontext[serverid].keys()):
    #     while j < len(playercontext[serverid][i].keys()):
    #         while k < len(playercontext[serverid][i][j].keys()):
    #             if playercontext[serverid][i][j][k][-1]["playerhasleft"] == True and playercontext[serverid][i][j][k][-1]["mostrecentsave"] == True:
    #                     # dump the entry
    #                     print("deleting",uid,name,matchidofsave)
              
    #                     if not playercontext[uid][name]:
    #                         del playercontext[uid][name]
    #                     if not playercontext[uid]:
    #                         del playercontext[uid]
    #             k += 1
    #         j += 1
        # print("pinfo",pinfo)
    #print("players",players)
    # for pinfo in players:
    #     if pinfo["uid"]+pinfo["name"] in list(playercontext.keys()) and playercontext[pinfo["uid"]+pinfo["name"]] and ( playercontext[pinfo["uid"]+pinfo["name"]]["map"] != map or playercontext[pinfo["uid"]+pinfo["name"]]["serverid"] != serverid  ):
    #         playercontext[pinfo["uid"]+pinfo["name"]]["endtime"] = now
    #         print("saving-mapserver")
    #         savestats(playercontext[pinfo["uid"]+pinfo["name"]] ,2)
    #         playercontext[pinfo["uid"]+pinfo["name"]] = {}
    #         pass #SAVE SAVE SAVE
    #     if pinfo["uid"]+pinfo["name"] not in list(playercontext.keys()) or playercontext[pinfo["uid"]+pinfo["name"]] == {}:
    #         if now - Ijuststarted > 30:
    #             print("alternate join", pinfo["uid"]+pinfo["name"])
    #             onplayerjoin(pinfo["uid"],serverid,pinfo["name"])
    #         playercontext[pinfo["uid"]+pinfo["name"]] = {"joined":now,"map":map,"name":pinfo["name"],"uid":pinfo["uid"],"idoverride":0,"endtime":0,"serverid":serverid,"kills":0,"deaths":0,"titankills":0,"npckills":0,"score":0}
    #     # check if any data that requires a save has changed
    #         # on map change, we save before we overwrite. also we couuld try to return a thing, given stuff!
    #     playercontext[pinfo["uid"]+pinfo["name"]]["endtime"] = now
    #     playercontext[pinfo["uid"]+pinfo["name"]]["kills"] = pinfo["kills"]
    #     playercontext[pinfo["uid"]+pinfo["name"]]["deaths"] = pinfo["deaths"]
    #     playercontext[pinfo["uid"]+pinfo["name"]]["titankills"] = pinfo["titankills"]
    #     playercontext[pinfo["uid"]+pinfo["name"]]["npckills"] = pinfo["npckills"]
    #     playercontext[pinfo["uid"]+pinfo["name"]]["score"] = pinfo["score"]

    

def playerpoll():
    global discordtotitanfall,playercontext,context
    Ithinktheserverhascrashed = 180
    autosaveinterval = 120
    pinginterval = 10
    # if the player leaves and rejoins, continue their streak.
    # if the server does not respond for this time, assume it crashed.
    counter = 0
    while True:
        shouldIsave = True
        counter +=1
        # print("counter",counter,autosaveinterval/pinginterval)
        if not counter % int(autosaveinterval/pinginterval):
            print("autosaving")
            for serverid,data in playercontext.items():
                for uid,value in data.items():
                    for name, value2 in value.items():
                        for matchid,value3 in value2.items():
                            if value3[-1]["mostrecentsave"] == False:
                                # print("here")
                                savestats({"uid":uid,"name":name,"matchid":matchid,"endtype":4,"index":-1,"serverid":serverid})
                                playercontext[serverid][uid][name][matchid][-1]["mostrecentsave"] = True
   
                    
       # poll time
        # I want to iterate through all servers, and ask them what they are up too.
        for serverid,data in discordtotitanfall.items():
            # print(discordtotitanfall)
            if context["istf1server"].get(serverid,False):
                continue
            if time.time() - data["lastheardfrom"] > Ithinktheserverhascrashed:
                pass
            else:
                shouldIsave = False
                asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,"!playingpoll"),"fake context",playerpolllog,True,False), bot.loop)
                # returncommandfeedback(*sendrconcommand(serverid,"!playingpoll"),"fake context",playerpolllog)
        # if shouldIsave:
        #     if not counter % autosaveinterval*pinginterval:
        #         for key,pinfo in playercontext.items():
        #             if pinfo != {}:
        #                 print("saving-autosave")
        #                 lastrow = savestats(pinfo,4)
        #                 playercontext[key]["idoverride"] = lastrow
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
                            ascii_art[i] = ascii_art[i] + ANSICOLOUR + "-" + (message.author.nick if message.author.nick is not None else message.author.display_name).replace(" ", "_")
                            length = -1
                        elif len(ascii_art[i]) == secondshortest:
                            ascii_art[i] = ascii_art[i] + ANSICOLOUR + "-" + ("Image from discord").replace(" ", "_")
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
threading.Thread(target=tf1relay).start()



bot.run(TOKEN)
