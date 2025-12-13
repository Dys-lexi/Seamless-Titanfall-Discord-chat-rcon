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
import signal
import inspect
from flask_cors import CORS
from flask import Flask, jsonify, request, send_from_directory, send_file
from waitress import serve
from discord.ext import  tasks
from datetime import datetime,  timezone, timedelta
import discord
import requests
import functools
from rcon.source import Client
import importlib.util
import sqlite3
import re
import aiohttp
from defs import *
import io
import sys
import logging
import psycopg2
from psycopg2 import pool
from sanshelper import sans



def safe_eval(calculation, data):
    """Safely evaluate calculation with division by zero protection"""
    try:
        return eval(calculation, {}, data)
    except ZeroDivisionError:
        return 0
    except:
        return 0

# foo.cache_clear()
# @functools.lru_cache(maxsize = None)
# DASH THEN HASHTAG
stuck_monitor_lock = threading.Lock()
current_execution = {"file": None, "line": None, "start_time": None}


def log_stuck_execution(filename, lineno, duration):
    """Log stuck execution to ./data/stuck.txt"""
    try:
        os.makedirs("./data", exist_ok=True)
        with open("./data/stuck.txt", "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] STUCK: {filename}:{lineno} - {duration:.1f}s\n")
    except Exception as e:
        print(f"Failed to log stuck execution: {e}")


def execution_tracer(frame, event, arg):
    """Trace function execution and detect stuck lines"""
    if event == "line":
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        current_time = time.time()

        with stuck_monitor_lock:
            # Check if previous line was stuck
            if current_execution["start_time"] is not None:
                duration = current_time - current_execution["start_time"]
                if duration > 35.0:  # 35 second threshold
                    log_stuck_execution(
                        current_execution["file"], current_execution["line"], duration
                    )

            # Update current execution tracking
            current_execution["file"] = filename
            current_execution["line"] = lineno
            current_execution["start_time"] = current_time

    return execution_tracer


sys.settrace(execution_tracer)


def create_all_indexes():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    # --- specifickilltracker ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_victim_id ON specifickilltracker(victim_id);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_playeruid ON specifickilltracker(playeruid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_timeofkill ON specifickilltracker(timeofkill);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_cause_of_death ON specifickilltracker(cause_of_death);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_combined_player_time ON specifickilltracker(playeruid, timeofkill);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_combined_victim_time ON specifickilltracker(victim_id, timeofkill);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_victim_type ON specifickilltracker(victim_type);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_specifickilltracker_attacker_type ON specifickilltracker(attacker_type);"
    )

    # --- playtime ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtime_playeruid ON playtime(playeruid);"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_playtime_matchid ON playtime(matchid);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_playtime_serverid ON playtime(serverid);")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtime_joinatunix ON playtime(joinatunix);"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_playtime_map ON playtime(map);")

    # --- uidnamelink ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelink_playeruid ON uidnamelink(playeruid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelink_playername ON uidnamelink(playername);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelink_lastseenunix ON uidnamelink(lastseenunix);"
    )

    # --- uidnamelinktf1 ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelinktf1_playeruid ON uidnamelinktf1(playeruid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelinktf1_playername ON uidnamelinktf1(playername);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_uidnamelinktf1_lastseenunix ON uidnamelinktf1(lastseenunix);"
    )

    # --- discordlinkdata ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_discordlinkdata_discordid ON discordlinkdata(discordid);"
    )

    # --- discorduiddata ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_discorduiddata_discorduid ON discorduiddata(discorduid);"
    )

    # --- joinnotify ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_joinnotify_uidnotify ON joinnotify(uidnotify);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_joinnotify_discordidnotify ON joinnotify(discordidnotify);"
    )

    # --- joincounter ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_joincounter_playeruid_serverid ON joincounter(playeruid, serverid);"
    )

    # --- matchid ---
    c.execute("CREATE INDEX IF NOT EXISTS idx_matchid_serverid ON matchid(serverid);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_matchid_map_time ON matchid(map, time);")

    # --- matchtf1 ---
    c.execute("CREATE INDEX IF NOT EXISTS idx_matchtf1_serverid ON matchtf1(serverid);")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_matchtf1_map_time ON matchtf1(map, time);"
    )

    # --- banstf1 ---
    # c.execute("CREATE INDEX IF NOT EXISTS idx_banstf1_playerip ON banstf1(playerip);")
    # c.execute("CREATE INDEX IF NOT EXISTS idx_banstf1_playername ON banstf1(playername);")
    # c.execute("CREATE INDEX IF NOT EXISTS idx_banstf1_banid ON banstf1(banid);")

    # --- messagelogger ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_messagelogger_serverid ON messagelogger(serverid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_messagelogger_type ON messagelogger(type);"
    )

    # --- playtimetf1 ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtimetf1_playeruid ON playtimetf1(playeruid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtimetf1_matchid ON playtimetf1(matchid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtimetf1_serverid ON playtimetf1(serverid);"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playtimetf1_joinatunix ON playtimetf1(joinatunix);"
    )

    # --- playeruidpreferences ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_playeruidpreferences_uid_istf1 ON playeruidpreferences(uid, istf1);"
    )

    tfdb.commit()
    tfdb.close()


def creatediscordlinkdb():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    c.execute(
        """CREATE TABLE IF NOT EXISTS discordlinkdata (
            uid INTEGER PRIMARY KEY,
            discordid INTEGER,
            linktime INTEGER
        )"""
    )

    tfdb.commit()
    tfdb.close()


def messagelogger():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """CREATE TABLE IF NOT EXISTS messagelogger (
            id SERIAL PRIMARY KEY,
            message TEXT,
            serverid TEXT,
            type TEXT
        )"""
    )
    # try:
    #     c.execute("ALTER TABLE messagelogger ADD COLUMN serverid INTEGER")
    #     c.execute("ALTER TABLE messagelogger ADD COLUMN type TEXT")
    # except sqlite3.OperationalError:
    #     pass

    tfdb.commit()
    tfdb.close()

def duelsinit():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    # c.execute("DROP TABLE IF EXISTS DUELS")
    c.execute(
        """CREATE TABLE IF NOT EXISTS duels (
            initiator INTEGER,
            receiver INTEGER,
            matchid TEXT,
            initiatorscore INTEGER,
            receiverscore INTEGER,
            serverid TEXT,
            isfinished INTEGER,
            PRIMARY KEY (initiator, receiver,matchid)
        )"""
    )
    # try:
    #     c.execute("ALTER TABLE messagelogger ADD COLUMN serverid INTEGER")
    #     c.execute("ALTER TABLE messagelogger ADD COLUMN type TEXT")
    # except sqlite3.OperationalError:
    #     pass
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE duels
        ALTER COLUMN initiator TYPE BIGINT USING initiator::BIGINT;
        """)
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE duels
        ALTER COLUMN receiver TYPE BIGINT USING receiver::BIGINT;
        """)
    tfdb.commit()
    tfdb.close()

def discorduidinfodb():
    global colourslink
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    # c.execute("DROP TABLE IF EXISTS discorduiddata")
    # c.execute("DELETE FROM discorduiddata WHERE choseningamecolour = 'reset'")
    c.execute(
        """CREATE TABLE IF NOT EXISTS discorduiddata (
            discorduid INTEGER PRIMARY KEY,
            chosencolour TEXT,
            choseningamecolour TEXT,
            nameprefix TEXT
            )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE discorduiddata
        ALTER COLUMN discorduid TYPE BIGINT USING discorduid::BIGINT;
        """)
    # try:
    #     c.execute("ALTER TABLE discorduiddata ADD COLUMN nameprefix TEXT")
    # except:
    #     pass
    # c.execute("ALTER TABLE discorduiddata ADD COLUMN choseningamecolour TEXT")
    c.execute(
        "SELECT discorduid, chosencolour,choseningamecolour, nameprefix FROM discorduiddata"
    )
    output = c.fetchall()
    # print(output)
    teams = ["FRIENDLY", "ENEMY", "NEUTRAL"]
    # print(json.dumps(list(output),indent=4))
    colourslink = {
        x[0]: {
            "discordcolour": list(
                map(
                    lambda y: tuple(map(int, y.strip("()").split(","))), x[1].split("|")
                )
            )
            if x[1] is not None and x[1] != "reset"
            else [],
            **(
                (
                    {
                        team: (
                            list(
                                map(
                                    lambda y: tuple(map(int, y.strip("()").split(","))),
                                    x[2].split("|"),
                                )
                            )
                        )
                        for team in teams
                    }
                    if "[" not in x[2]
                    else json.loads(x[2])
                )
                if x[2] is not None and x[2] != "reset"
                else {}
            ),
            "nameprefix": (x[3]) if x[3] and x[3] != "reset" else None,
        }
        for x in output
    }
    # print(json.dumps(colourslink,indent=4))
    c.execute("SELECT discorduid, choseningamecolour FROM discorduiddata")
    # output = c.fetchall()
    # colourslink = {x[0]:list(map(lambda y: eval(y), x[1].split("|"))) if x[1] != "reset" else RGBCOLOUR['DISCORD']  for x in output}
    # print("COLOURSLINK",colourslink)
    tfdb.commit()
    tfdb.close()


def specifickilltrackerdb():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    # Create the table if it doesn't exist
    c.execute(
        """CREATE TABLE IF NOT EXISTS specifickilltracker (
            id SERIAL PRIMARY KEY,
            serverid               TEXT,
            attacker_z              REAL,
            attacker_x              REAL,
            attacker_y              REAL,
            victim_id               INTEGER,
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
            playeruid               INTEGER,
            game_mode               TEXT,
            victim_x                REAL,
            attacker_weapon_1       TEXT,
            victim_weapon_1         TEXT,
            victim_weapon_2         TEXT,
            timeofkill              INTEGER,
            cause_of_death          TEXT,
            victim_y                REAL,
            weapon_mods             TEXT,
            victim_type             TEXT,
            attacker_type           TEXT
        )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE specifickilltracker
        ALTER COLUMN playeruid TYPE BIGINT  USING playeruid::BIGINT ,
        ALTER COLUMN victim_id TYPE BIGINT  USING victim_id::BIGINT ;
        """)
        c.commit()

    # c.execute("PRAGMA table_info(specifickilltracker)")
    # columns = [row[1] for row in c.fetchall()]

    # if "victim_type" not in columns:
    #     c.execute("ALTER TABLE specifickilltracker ADD COLUMN victim_type TEXT")

    tfdb.commit()
    c.close()
    tfdb.close()

def specifickilltrackerdbtf1():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    # Create the table if it doesn't exist
    c.execute(
        """CREATE TABLE IF NOT EXISTS specifickilltrackertf1 (
            id SERIAL PRIMARY KEY,
            serverid               TEXT,
            attacker_z              REAL,
            attacker_x              REAL,
            attacker_y              REAL,
            victim_id               INTEGER,
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
            playeruid               INTEGER,
            game_mode               TEXT,
            victim_x                REAL,
            attacker_weapon_1       TEXT,
            victim_weapon_1         TEXT,
            victim_weapon_2         TEXT,
            timeofkill              INTEGER,
            cause_of_death          TEXT,
            victim_y                REAL,
            weapon_mods             TEXT,
            victim_type             TEXT,
            attacker_type           TEXT
        )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE specifickilltrackertf1
        ALTER COLUMN playeruid TYPE BIGINT  USING playeruid::BIGINT ,
        ALTER COLUMN victim_id TYPE BIGINT  USING victim_id::BIGINT ;
        """)
        c.commit()

    # c.execute("PRAGMA table_info(specifickilltracker)")
    # columns = [row[1] for row in c.fetchall()]

    # if "victim_type" not in columns:
    #     c.execute("ALTER TABLE specifickilltracker ADD COLUMN victim_type TEXT")

    tfdb.commit()
    c.close()
    tfdb.close()

def playeruidpreferences():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    # c.execute("DROP TABLE IF EXISTS playeruidpreferences")
    c.execute(
        """CREATE TABLE IF NOT EXISTS playeruidpreferences (
            id SERIAL PRIMARY KEY,
            uid INTEGER,
            istf1 INTEGER,
            preferences TEXT
            )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE playeruidpreferences
        ALTER COLUMN uid TYPE BIGINT USING uid::BIGINT;
        """)
    tfdb.commit()
    tfdb.close()


playerpreferencescache = {"tf1": {}, "tf2": {}}


def readplayeruidpreferences(uid, istf1=False):
    """read settings that generally affect gameplay and are linked to a tf|1/2 account, eg toggle stats"""
    global playerpreferencescache
    output = playerpreferencescache["tf1" if istf1 else "tf2"].get(uid)
    if output:
        return output
    # uid = int(uid)
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        "SELECT preferences FROM playeruidpreferences WHERE uid = ? AND istf1 = ?",
        (uid, 1 if istf1 else 0),
    )
    output = c.fetchone()
    try:
        output = json.loads(output[0]) if output else {}
    except:
        traceback.print_exc()
    tfdb.close()
    return output


def deep_set(d, keys, value="not added"):
    """like setdefault, but seeeeets default"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    if value != "not added":
        d[keys[-1]] = value


def setplayeruidpreferences(path, value, uid, istf1=False):
    """see readplayeruidpreferences()"""
    global playerpreferencescache
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    istf1_int = 1 if istf1 else 0

    c.execute(
        "SELECT preferences FROM playeruidpreferences WHERE uid = ? AND istf1 = ?",
        (uid, istf1_int),
    )
    row = c.fetchone()

    if row:
        preferences_json = json.loads(row[0])
    else:
        preferences_json = {}

    deep_set(preferences_json, path, value)
    playerpreferencescache["tf1" if istf1 else "tf2"][uid] = preferences_json

    if row:
        c.execute(
            "UPDATE playeruidpreferences SET preferences = ? WHERE uid = ? AND istf1 = ?",
            (json.dumps(preferences_json), uid, istf1_int),
        )
    else:
        c.execute(
            "INSERT INTO playeruidpreferences (uid, istf1, preferences) VALUES (?, ?, ?)",
            (uid, istf1_int, json.dumps(preferences_json)),
        )

    tfdb.commit()
    tfdb.close()


def matchidtf1():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """CREATE TABLE IF NOT EXISTS matchidtf1 (
            matchid TEXT,
            serverid INTEGER,
            map TEXT,
            time INTEGER,
            PRIMARY KEY (matchid, serverid)
            )"""
    )
    tfdb.commit()
    tfdb.close()
# def tf1matchplayers():
#     tfdb = postgresem("./data/tf2helper.db")
#     c = tfdb
#     # c.execute("DROP TABLE IF EXISTS playtimetfw1")
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS matchtf1 (
#             matchid TEXT PRIMARY KEY,
#             map TEXT,
#             time INTEGER,
#             serverid INTEGER
#             )"""
#     )
#     tfdb.commit()
#     tfdb.close()


def playtimedbtf1():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    c.execute(
        """CREATE TABLE IF NOT EXISTS playtimetf1 (
            id SERIAL PRIMARY KEY,
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
            matchid TEXT,
            map TEXT,
            timecounter INTEGER
            )"""
    )

    tfdb.commit()
    tfdb.close()


def playeruidnamelinktf1():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """CREATE TABLE IF NOT EXISTS uidnamelinktf1 (
            id SERIAL PRIMARY KEY,
            playeruid INTEGER,
            playername TEXT,
            lastseenunix INTEGER,
            firstseenunix INTEGER,
            lastserverid INTEGER,
            ipinfo TEXT
            )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE uidnamelinktf1
        ALTER COLUMN playeruid TYPE BIGINT USING playeruid::BIGINT;
        """)
    # try:
    #     c.execute("ALTER TABLE uidnamelinktf1 ADD COLUMN ipinfo TEXT")
    # except:
    #     pass
    tfdb.commit()
    tfdb.close()


def bantf1():
    tfdb = postgresem("./data/tf2helper")
    c = tfdb
    # banid is because the bot automatically bans new names / ips
    # c.execute("DROP TABLE IF EXISTS banstf1")
    c.execute(
        """CREATE TABLE IF NOT EXISTS banstf1 (
            id SERIAL PRIMARY KEY,
            banlinks INTEGER,
            bantype TEXT,
            baninfo TEXT,
            playerip TEXT,
            playername TEXT,
            playeruid INTEGER,
            lastseen INTEGER,
            lastserverid INTEGER,
            expire INTEGER,
            messageid INTEGER
            )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE banstf1
        ALTER COLUMN playeruid TYPE BIGINT USING playeruid::BIGINT;
        """)
        c.execute("""
        ALTER TABLE banstf1
        ALTER COLUMN messageid TYPE BIGINT USING messageid::BIGINT;
        """)
    # c.execute("ALTER TABLE banstf1 ADD COLUMN lastserverid INTEGER")

    tfdb.commit()
    tfdb.close()


def matchid():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """CREATE TABLE IF NOT EXISTS matchid (
            matchid TEXT PRIMARY KEY,
            map TEXT,
            time INTEGER,
            serverid INTEGER
            )"""
    )
    tfdb.commit()
    tfdb.close()


def notifydb():
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
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
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
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
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """CREATE TABLE IF NOT EXISTS playtime (
            id SERIAL PRIMARY KEY,
            expire INTEGER,
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
            matchid TEXT,
            map TEXT,
            timecounter INTEGER
            )"""
    )

    tfdb.commit()
    tfdb.close()


def playeruidnamelink():
    tfdb = postgresem("./data/tf2helper.db")

    c = tfdb
    # c.execute("DROP TABLE IF EXISTS uidnamelink")
    c.execute(
        """CREATE TABLE IF NOT EXISTS uidnamelink (
            id SERIAL PRIMARY KEY,
            playeruid INTEGER,
            playername TEXT,
            lastseenunix INTEGER,
            firstseenunix INTEGER,
            lastserverid INTEGER,
            ipinfo TEXT
            )"""
    )
    if POSTGRESQLDBURL != "0":
        c.execute("""
        ALTER TABLE uidnamelink
        ALTER COLUMN playeruid TYPE BIGINT USING playeruid::BIGINT;
        """)

    # # One-time migration to convert ipinfo format from dict to array
    # try:
    #     c.execute("SELECT id, ipinfo FROM uidnamelink WHERE ipinfo IS NOT NULL AND ipinfo != ''")
    #     rows = c.fetchall()
    #     for row_id, ipinfo_str in rows:
    #         try:
    #             ipinfo_data = json.loads(ipinfo_str)
    #             # Check if already in new format (array)
    #             if isinstance(ipinfo_data, list):
    #                 continue
    #             # Convert from dict to array format
    #             ipinfo_array = []
    #             for ip, timestamps in ipinfo_data.items():
    #                 ipinfo_array.append({
    #                     "ip": ip,
    #                     "first": timestamps.get("first"),
    #                     "last": timestamps.get("last")
    #                 })
    #             # Update the row with new format
    #             c.execute("UPDATE uidnamelink SET ipinfo = %s WHERE id = %s", 
    #                      (json.dumps(ipinfo_array), row_id))
    #         except Exception as e:
    #             # Skip malformed data
    #             print(f"Error migrating ipinfo for row {row_id}: {e}")
    #             pass
    #     tfdb.commit()
    # except Exception as e:
    #     print(f"Error during ipinfo migration: {e}")
    #     pass
    
    # try:
    #     c.execute("ALTER TABLE uidnamelink ADD COLUMN ipinfo TEXT")
    # except:
    #     pass
    tfdb.commit()
    tfdb.close()


# import importlib
# this whole thing is a mess of global varibles, jank threading and whatever, but it works just fine :)
# (I never bothered much with coding style)

messageflush = []
messageflushnotify = []
lastmessage = 0
Ijuststarted = time.time()
discorduidnamelink = {}
reactedyellowtoo = []
knownpeople = {}
currentduels = {}
mostrecentmatchids = {}
potentialduels = {}
registeredaccepts = {}
tfcommandspermissions = {}


# log_file = "logs"
# if not os.path.exists("./data/" + log_file):
#     with open("./data/" + log_file, "w") as f:
#         f.write("")
realprint = print
linecolours = {}


def removecolourcodes(message):
    import re

    # Remove all ANSI escape sequences: [...m, \u001b[...m, and [38;2;R;G;Bm patterns
    # Pattern matches:
    # - [...m (hex escape)
    # - \u001b[...m (unicode escape)
    # - [38;2;R;G;Bm (RGB color codes)
    # - \033[...m (octal escape)
    ansi_pattern = r"(\[[0-9;]*m|\\u001b\[[0-9;]*m|\[38;2;[0-9;]*m|\033\[[0-9;]*m)"
    message = re.sub(ansi_pattern, "", message)
    return message


linecolours = {}


def print(*message, end="\033[0m\n"):
    global linecolours
    message = (
        " ".join([str(i) for i in message])
        .replace("[110m", "[38;2;200;200;200m")
        .replace("[111m", "[38;2;80;229;255m")
        .replace("[112m", "[38;2;213;80;16m")
    )
    if len(message) < 1000000 and False:
        with open("./data/" + log_file, "a") as file:
            file.write(
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                + ": "
                + str(message)
                + "\n"
            )

    function = str(inspect.currentframe().f_back.f_code.co_name)
    line = str(inspect.currentframe().f_back.f_lineno)
    if line not in linecolours:
        while True:
            colour = random.randint(0, 255)
            if colour not in DISALLOWED_COLOURS:
                break
        linecolours[line] = colour
    if MORECOLOURS != "1":
        realprint(
            f"[0m{(('[' + function[:9] + ']').ljust(11) if True else '⯈'.ljust(11))}{('[' + line + ']').ljust(7)}[{datetime.now().strftime('%H:%M:%S %d/%m')}] {message}"
        )
    else:
        realprint(
            f"[38;2;215;22;105m{(('[' + function[:9] + ']').ljust(11) if True else '⯈'.ljust(11))}[38;2;126;89;140m{('[' + line + ']').ljust(7)}[38;2;27;64;152m[{datetime.now().strftime('%H:%M:%S %d/%m')}][38;5;{linecolours[line]}m {(message)}",
            end=end,
        )


lastrestart = 0
botisalreadyready = False
messagecounter = 0
SLEEPTIME_ON_FAILED_COMMAND = 0  # for when you are running multiple versions of the bot (like a dev version). if one bot cannot fulfill the command,
# the other bot that can has time too, instead of the first responding with failure
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
intents.presences = True
# ENV VARS
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "0")
SHOULDUSEIMAGES = os.getenv("DISCORD_BOT_USE_IMAGES", "0")
SHOULDUSETHROWAI = os.getenv("DISCORD_BOT_USE_THROWAI", "1")
LOCALHOSTPATH = os.getenv("DISCORD_BOT_LOCALHOST_PATH", "localhost")
DISCORDBOTAIUSED = os.getenv("DISCORD_BOT_AI_USED", "deepseek-r1")
DISCORDBOTLOGSTATS = os.getenv("DISCORD_BOT_LOG_STATS", "1")
DISCORDBOTLOGSTATS = "1"  # I worry about the amount of things that will break if this is off (banning,custom messages, stats, every command that needs a name)
SERVERPASS = os.getenv("DISCORD_BOT_PASSWORD", "*")
LEADERBOARDUPDATERATE = int(os.getenv("DISCORD_BOT_LEADERBOARD_UPDATERATE", "800"))
DISCORDBOTLOGCOMMANDS = os.getenv("DISCORD_BOT_LOG_COMMANDS", "1")
SERVERNAMEISCHOICE = os.getenv("DISCORD_BOT_SERVERNAME_IS_CHOICE", "0")
SANCTIONAPIBANKEY = os.getenv("SANCTION_API_BAN_KEY", "0")
TF1RCONKEY = os.getenv("TF1_RCON_PASSWORD", "pass")
USEDYNAMICPFPS = os.getenv("USE_DYNAMIC_PFPS", "1")
# USEDYNAMICPFPS = "1"
PFPROUTE = os.getenv(
    "PFP_ROUTE",
    "https://raw.githubusercontent.com/Dys-lexi/TitanPilotprofiles/main/avatars/",
)
FILTERNAMESINMESSAGES = os.getenv(
    "FILTER_NAMES_IN_MESSAGES",
    "usermessagepfp,chat_message,command,tf1command,botcommand,connecttf1",
)
SENDKILLFEED = os.getenv("SEND_KILL_FEED", "1")
OVERRIDEIPFORCDNLEADERBOARD = os.getenv(
    "OVERRIDE_IP_FOR_CDN_LEADERBOARD", "hidden"
)
OVVERRIDEROLEREQUIRMENT = os.getenv("OVERRIDE_ROLE_REQUIREMENT", "1")
COOLPERKSROLEREQUIRMENTS = os.getenv(
    "COOL_PERKS_REQUIREMENT", "You need something or other to get this"
)
SHOWIMPERSONATEDMESSAGESINDISCORD = os.getenv(
    "SHOW_IMPERSONATED_MESSAGES_IN_DISCORD", "1"
)
KILLSTREAKNOTIFYTHRESHOLD = int(os.getenv("KILL_STREAK_NOTIFY_THRESHOLD", "5"))
KILLSTREAKNOTIFYSTEP = int(os.getenv("KILL_STREAK_NOTIFY_STEP", "5"))
REACTONMENTION = os.getenv("REACT_EMOJI_ON_MENTION", "0")
POSTGRESQLDBURL = os.getenv("POSTGRESQL_DB_URL", "0")
NOTIFYCOMMANDSONALLSERVERSDEBUG = int(os.getenv("SHOULD_NOTIFY_ALL_COMMANDS", "1"))
PORT = os.getenv("BOT_PORT", "3451")
MAXTAGLEN = int(os.getenv("MAX_TAG_LEN", "6"))
MORECOLOURS = os.getenv("MORE_COLOURFUL_OUTPUT", "1")
NOCAROENDPOINT = os.getenv("NOCARO_API_ENDPOINT", "https://nocaro.awesome.tf/")
NOCAROAUTH = os.getenv("NOCARO_AUTH", False)
SANSURL = os.getenv("SANS_URL",False)
TIMETILLCHANNELSGETHIDDEN = int(os.getenv("TIME_TO_HIDE_CHANNEL",86400*3))
GLOBALIP = 0
if OVERRIDEIPFORCDNLEADERBOARD == "use_actual_ip":
    GLOBALIP = "http://" + requests.get("https://api.ipify.org").text + ":" + "34511"
elif OVERRIDEIPFORCDNLEADERBOARD != "hidden":
    GLOBALIP = OVERRIDEIPFORCDNLEADERBOARD
print("running discord logger bot")
if MORECOLOURS == "1":
    print(
        "Colours:"
        + "".join(
            [
                f"{'\n' if not i % 3 else ''}{x[1].split('m')[0]}m{x[0].ljust(15)}"
                for i, x in enumerate(PREFIXES.items())
            ]
        )
    )

if POSTGRESQLDBURL == "0":
    print("RUNNING ON SQLITEDB")

    class postgresem:
        def __init__(self, path=None):
            self.closed = False
            self.conn = sqlite3.connect(path)
            self.cursor = self.conn.cursor()

        def execute(self, query, params=None):
            self.cursor.execute(
                query.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY"),
                params or (),
            )

        def fetchall(self):
            return self.cursor.fetchall()

        def fetchone(self):
            return self.cursor.fetchone()

        def commit(self):
            self.conn.commit()

        def lastrowid(self):
            return self.cursor.lastrowid

        def close(self):
            if self.closed:
                return
            self.closed = True
            self.cursor.close()
            self.conn.close()

else:
    print("RUNNING ON POSTGRESQL DB")
    pgpool = pool.ThreadedConnectionPool(20, 200, dsn=POSTGRESQLDBURL)

    class postgresem:
        def __init__(self, what=False):
            self.closed = False
            self.pool = pgpool
            self.conn = None
            self.cursor = None
            self._empty_result = False
            self.connection_id = id(self)  # Track this connection instance
            # Establish connection immediately like original code
            self._connect()

        def _connect(self):
            """Establish database connection"""
            try:
                if self.conn:
                    try:
                        self.pool.putconn(self.conn)
                    except Exception:
                        pass
                    self.conn = None
                    self.cursor = None

                self.conn = self.pool.getconn()
                self.cursor = self.conn.cursor()

                # Print current pool status when acquiring
                # used = len(pgpool._used) if hasattr(pgpool, '_used') else "?"
                # free = len(pgpool._pool) if hasattr(pgpool, '_pool') else "?"
                # function = str(inspect.currentframe().f_back.f_code.co_name)
                # print(f"[{function}] DB Connection {self.connection_id}: ACQUIRED (Pool now: {free} left, {used} in use)")
            except Exception:
                print(f"DB Connection {self.connection_id}: FAILED TO ACQUIRE")
                traceback.print_exc()
                self._cleanup()
                raise

        def _reconnect(self):
            """Attempt to reconnect to the database"""
            if self.closed:
                return False
            try:
                print(f"DB Connection {self.connection_id}: Attempting reconnection...")
                self._connect()
                print(f"DB Connection {self.connection_id}: Reconnection successful")
                return True
            except Exception:
                print(f"DB Connection {self.connection_id}: Reconnection failed")
                traceback.print_exc()
                return False

        def _is_connection_lost(self, error):
            """Check if the error indicates a lost connection"""
            connection_errors = [
                "server closed the connection unexpectedly",
                "connection to server lost",
                "the database system is shutting down",
                "terminating connection",
                "could not receive data from server",
                "SSL connection has been closed unexpectedly",
                "connection not open",
                "no connection to the server",
            ]
            error_str = str(error).lower()
            return any(err_msg in error_str for err_msg in connection_errors)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._cleanup()

        def _cleanup(self):
            if self.closed:
                # print(f"DB Connection {self.connection_id}: ALREADY CLOSED (double cleanup)")
                return
            self.closed = True
            if self.cursor:
                try:
                    self.cursor.close()
                except Exception:
                    traceback.print_exc()
                    pass
            if self.conn:
                try:
                    self.pool.putconn(self.conn)
                except Exception:
                    traceback.print_exc()
                    pass
            self.cursor = None
            self.conn = None

        def execute(self, query, params=None):
            if self.closed:
                raise RuntimeError("Database connection is closed")

            # Check if we need to reconnect
            if not self.cursor or not self.conn:
                if not self._reconnect():
                    raise RuntimeError("Cannot establish database connection")

            query = query.replace("?", "%s")
            query = re.sub(r"\s+COLLATE\s+NOCASE", "", query, flags=re.IGNORECASE)
            query = re.sub(r"\bLIKE\b", "ILIKE", query, flags=re.IGNORECASE)

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.cursor.execute(query, params or ())
                    break
                except psycopg2.errors.InvalidTextRepresentation as e:
                    traceback.print_exc()
                    if self.conn:
                        self.conn.rollback()
                    if "invalid input syntax for type bigint" in str(
                        e
                    ) and query.strip().upper().startswith("SELECT"):
                        self._empty_result = True
                        return
                    else:
                        raise
                except psycopg2.errors.UndefinedFunction as e:
                    traceback.print_exc()
                    if self.conn:
                        self.conn.rollback()
                    if "operator does not exist" in str(
                        e
                    ) and query.strip().upper().startswith("SELECT"):
                        self._empty_result = True
                        return
                    else:
                        raise
                except psycopg2.Error as e:
                    if self._is_connection_lost(e) and attempt < max_retries - 1:
                        print(
                            f"DB Connection {self.connection_id}: Connection lost during execute, retrying..."
                        )
                        if self._reconnect():
                            continue
                    traceback.print_exc()
                    if self.conn:
                        try:
                            self.conn.rollback()
                        except Exception:
                            pass
                    raise
            else:
                self._empty_result = False

        def fetchall(self):
            if getattr(self, "_empty_result", False):
                return []
            if self.closed:
                raise RuntimeError("Database connection is closed")
            if not self.cursor or not self.conn:
                if not self._reconnect():
                    raise RuntimeError("Cannot establish database connection")

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    return self.cursor.fetchall()
                except psycopg2.Error as e:
                    if self._is_connection_lost(e) and attempt < max_retries - 1:
                        print(
                            f"DB Connection {self.connection_id}: Connection lost during fetchall, retrying..."
                        )
                        if self._reconnect():
                            continue
                    raise
            return []

        def fetchone(self):
            if getattr(self, "_empty_result", False):
                return []
            if self.closed:
                raise RuntimeError("Database connection is closed")
            if not self.cursor or not self.conn:
                if not self._reconnect():
                    raise RuntimeError("Cannot establish database connection")

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    return self.cursor.fetchone()
                except psycopg2.Error as e:
                    if self._is_connection_lost(e) and attempt < max_retries - 1:
                        print(
                            f"DB Connection {self.connection_id}: Connection lost during fetchone, retrying..."
                        )
                        if self._reconnect():
                            continue
                    raise
            return None

        def commit(self):
            if self.closed:
                raise RuntimeError("Database connection is closed")
            if not self.conn:
                if not self._reconnect():
                    raise RuntimeError("Cannot establish database connection")

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.conn.commit()
                    break
                except psycopg2.Error as e:
                    if self._is_connection_lost(e) and attempt < max_retries - 1:
                        print(
                            f"DB Connection {self.connection_id}: Connection lost during commit, retrying..."
                        )
                        if self._reconnect():
                            continue
                    raise

        def lastrowid(self):
            if self.closed:
                return None
            if not self.cursor or not self.conn:
                if not self._reconnect():
                    return None

            max_retries = 2
            for attempt in range(max_retries):
                try:
                    if self.cursor.description:
                        row = self.cursor.fetchone()
                        return row[0] if row else None
                    else:
                        return None
                except psycopg2.Error as e:
                    if self._is_connection_lost(e) and attempt < max_retries - 1:
                        print(
                            f"DB Connection {self.connection_id}: Connection lost during lastrowid, retrying..."
                        )
                        if self._reconnect():
                            continue
                    traceback.print_exc()
                    return None
                except Exception:
                    traceback.print_exc()
                    return None
            return None

        def close(self):
            self._cleanup()

        def __del__(self):
            self._cleanup()

callbacks = {}
def on(thing,sync="thread"):
    def fancything(function):
        global callbacks
        callbacks.setdefault(thing, []).append({"func":function,"sync":sync})
        return function
    return fancything
def callback(name,*stuff,**morestuff):
    global callbacks
    for callback in callbacks.get(name,[]):
        if callback["sync"] == "thread":
            threading.Thread(target=threadwrap,daemon=True,args=(callback["func"], *stuff),kwargs=morestuff).start()
        elif callback["sync"] == "async":
            asyncio.run_coroutine_threadsafe(threadwrap(callback["func"], *stuff, **morestuff),bot.loop)

# @on("bleh")
# def whatever():
#     print("meow")

# callback("bleh")


# tf1matchplayers()

def savecontext():
    """saves varible context to channels.json"""
    global context
    # print("saving")
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
    print("Server password set to", "*" * len(SERVERPASS))
if TOKEN == 0:
    print("NO TOKEN FOUND")
stoprequestsforserver = {}
discordtotitanfall = {}
pilotstates = {}
colourslink = {}
titanfall1currentlyplaying = {}
consecutivekills = {}
maxkills = {}
lexitoneapicache = {}
# Load channel ID from file
context = {
    "wordfilter": {"banwords": [], "notifybadwords": [], "namestokick": []},
    "categoryinfo":{
        "logging_cat_id":0,
        "hidden_cat_id":0,
        "idealorder":[],
        "activeguild": 0
    },

    "servers": {},
    "overridechannels": {
        "globalchannel": 0,
        "commandlogchannel": 0,
        "leaderboardchannel": 0,
        "wordfilternotifychannel": 0,
    },
    "slashcommandoverrides":{},
    "overrideroles": {"rconrole": 0, "coolperksrole": 0, "debugchat": 0},
    "overriderolesuids": {
        "rconrole": [],
        "coolperksrole": [],
    },
    "leaderboardchannelmessages": [],
    "commands": {},
    "coolperksnatter":"You should do this! for that!"
}
notifydb()
playtimedb()
playeruidnamelink()
joincounterdb()
matchid()
discorduidinfodb()
duelsinit()
messagelogger()
playeruidpreferences()
creatediscordlinkdb()
specifickilltrackerdb()
specifickilltrackerdbtf1()
playeruidnamelinktf1()
# tf1matchplayers()
matchidtf1()
playtimedbtf1()
create_all_indexes()
bantf1()

serverchannels = []
pngcounter = random.randint(0, 9)
imagescdn = {}
sansthings = False
accountlinker = {}
if not os.path.exists("./data"):
    os.makedirs("./data")
channel_file = "channels.json"
command_file = "commands.json"
nongitcommandfile = "commandsnosync.json"
tf1messagesizeadd = 254
tf1messagesizesubtract = 0

if os.path.exists("./data/" + channel_file):
    with open("./data/" + channel_file, "r") as f:
        tempcontext = json.load(f)
        for key in tempcontext.keys():
            context[key] = tempcontext[key]
else:
    context["categoryinfo"]["logging_cat_id"] = 0
    context["categoryinfo"]["activeguild"] = 0
    print("Channel file not found, using default channel ID 0.")
savecontext()
context["commands"] = {"botcommands": {}, "ingamecommands": {}}
if os.path.exists("./data/" + command_file):
    with open("./data/" + command_file, "r") as f:
        context["commands"] = json.load(f)
        print("Command file found, using commands.")
        # for commands in context["commands"].values():
        # for command in commands.keys():
        #     # print(f"{command} ", end="")
else:
    print("Command file not found, using NO (added) commands.")
if os.path.exists("./data/" + nongitcommandfile):
    with open("./data/" + nongitcommandfile, "r") as f:
        for key, value in json.load(f).items():
            context["commands"][key] = {**context["commands"][key], **value}
        print("Commandnosync file found, using commands.")
        # for commands in context["commands"].values():
        # for command in commands.keys():
        # print(f"{command} ", end="")
# print(json.dumps(context, indent=4))
# make aliases work
# print(json.dumps(context["commands"]["ingamecommands"],indent=2))
internaltoggles = {}



def processaliases():
    global context, internaltoggles
    if not context.get("commands", {}).get("ingamecommands", {}):
        return
    context["commands"]["ingamecommands"] = dict(
        sorted(
            {
                **context["commands"]["ingamecommands"],
                **dict(
                    functools.reduce(
                        lambda a, b: {
                            **a,
                            **{
                                cmd: {
                                    "alias": b[0],
                                    **dict(
                                        filter(
                                            lambda x: x[0] != "aliases", b[1].items()
                                        )
                                    ),
                                }
                                for cmd in b[1]["aliases"]
                            },
                        },
                        map(
                            lambda x: [
                                x[0],
                                {
                                    **x[1],
                                    "aliases": [x[1]["aliases"]]
                                    if isinstance(x[1]["aliases"], str)
                                    else x[1]["aliases"],
                                },
                            ],
                            filter(
                                lambda x: x[1].get("aliases"),
                                context["commands"]["ingamecommands"].items(),
                            ),
                        ),
                        {},
                    )
                ),
            }.items(),
            key=lambda z: z[1]["alias"] if z[1].get("alias") else z[0],
        )
    )
    internaltoggles = dict(
        map(
            lambda x: [x[0], x[0]]
            if "internaltoggle" not in x[1]
            else [x[1]["internaltoggle"], x[0]],
            context["commands"]["ingamecommands"].items(),
        )
    )


processaliases()
# print(json.dumps(internaltoggles,indent=4))
# print(json.dumps(context["commands"]["ingamecommands"],indent=2))

original_slash_command = discord.Bot.slash_command


def patched_slash_command(self, *args, **kwargs):
    if "integration_types" not in kwargs:
        kwargs["integration_types"] = {
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    if "contexts" not in kwargs:
        kwargs["contexts"] = {
            discord.InteractionContextType.guild,
            discord.InteractionContextType.private_channel,
            discord.InteractionContextType.bot_dm,
        }
    return original_slash_command(self, *args, **kwargs)




discord.Bot.slash_command = patched_slash_command

bot = discord.Bot(intents=intents)


async def droppycallback(interaction):
    custom_id = interaction.data.get('custom_id', '')
    
    if custom_id and 'dropdown' in custom_id and '_' in custom_id:
        parts = custom_id.split('_')
        function_name = parts[0]
        
        if function_name in globals() and callable(globals()[function_name]):
            func = globals()[function_name]
            await func(interaction, parts[1:])
        else:
            print(f"No handler function found for: {function_name}")



async def moderation(interaction, parts):
    # parts = ["dropdown", "userid", "serverid", "messageid"]
    user_id = parts[1]
    original_message_id = parts[3]
    message_link = f"https://discord.com/channels/{context["categoryinfo"]["activeguild"]}/{context["servers"][parts[2]]["channelid"]}/{original_message_id}"
    
    action_map = {
        "mute_h_1": {"duration": 1/24, "action_text": "1 hour mute", "type": "mute"},
        "mute_1": {"duration": 1, "action_text": "1 day mute", "type": "mute"},
        "mute_7": {"duration": 7, "action_text": "7 day mute", "type": "mute"},
        "mute_30": {"duration": 30, "action_text": "30 day mute", "type": "mute"},
        "mute_60": {"duration": 60, "action_text": "60 day mute", "type": "mute"}, 
        "ban_h_1": {"duration": 1/24, "action_text": "1 hour ban", "type": "ban"},
        "ban_1": {"duration": 1, "action_text": "1 day ban", "type": "ban"},
        "ban_7": {"duration": 7, "action_text": "7 day ban", "type": "ban"},
        "ban_30": {"duration": 30, "action_text": "30 day ban", "type": "ban"},
        "ban_60": {"duration": 60, "action_text": "60 day ban", "type": "ban"},
        "unsanction":"unsanction"
    }
    selected_action = action_map[interaction.data['values'][0]]
    await quickaddsanction(user_id, selected_action, interaction, message_link)


async def autocompleteserversfromdb(ctx):
    if not ctx.value.strip(" "):
        return []
    server_names = [
        s.get("name", "Unknown") for s in context["servers"].values() if s.get("name")
    ]
    output = [
        name for name in server_names if ctx.value.strip(" ").lower() in name.lower()
    ][:20]
    if len(output) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No server matches"]
    return output


async def autocompletesounds(ctx):
    """autocompletes tf2 sounds"""
    # {x["comment"]+"|" if x["comment"] else ""}
    output = completesound(ctx.value)
    if len(output) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No sound matches"]
    return output[:30]

@functools.lru_cache(maxsize=None)
def completesound(sound):
    return list(map(lambda x: f"{x["id"]+"|" if x["id"] else ""}{x["sound_name"]+" " if x["sound_name"] else ""}" ,sorted( filter(lambda x: sound.lower() in (x["sound_name"] or "&").lower() or sound.lower() in ( x["id"] or "&").lower() or sound.lower() in (x["comment"] or "&").lower() ,SOUNDS),key = lambda x: int(sound.lower() in (x["sound_name"] or "&"))*100+ int(sound.lower() in (x["id"] or "&"))*10+ int(sound.lower() in (x["comment"] or "&")),reverse = True)))
 

async def autocompletenamesfromdb(ctx):
    """autocompletes tf2 names"""
    output = [
        x["name"] if x["name"].strip() else str(x["uid"])
        for x in resolveplayeruidfromdb(ctx.value.strip(" "), None, True)
    ][:20]
    if len(output) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No one matches"]
    return output

async def autocompletetf1namesfromdb(ctx):
    """autocompletes tf1 names"""
    output = [
        x["name"] if x["name"].strip() else str(x["uid"])
        for x in resolveplayeruidfromdb(ctx.value.strip(" "), None, True,True)
    ][:20]
    if len(output) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No one matches"]
    return output

async def autocompletenamesanduidsfromdb(ctx):
    """autocompletes tf2 names and uids"""
    # print([ctx.value.strip(" ")])
    output = [
        f"{x['name']}->({x['uid']})" if x["name"].strip() else str(x["uid"])
        for x in resolveplayeruidfromdb(ctx.value.strip(" "), None, True)
    ][:20]
    if len(output) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No one matches"]
    return output

async def autocompletefilterwordcomplete(ctx):
    """toggles wordfilter"""
    serverid = getchannelidfromname(False, ctx.interaction)
    if not checkrconallowed(ctx.interaction.user,getslashcommandoverridesperms("wordfiltermodify"), serverid=serverid):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["You don't have permission to use this command"]
    potential = list(
        map(
            lambda x: f"{x[1]} - {x[0]}",
            filter(
                lambda x: ctx.value.strip(" ").lower() in x[1].lower(),
                [[x[0], y] for x in context["wordfilter"].items() for y in x[1]],
            ),
        )
    )
    if not potential:
        return ["No matches. whatever you type will be a new rule"]
    return potential


async def autocompletenamesfromtf1bans(ctx):
    """autocompletes tf1 bans"""
    serverid = getchannelidfromname(False, ctx.interaction)
    if not checkrconallowed(ctx.interaction.user,getslashcommandoverridesperms("autocompleteip"), serverid=serverid):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["You don't have permission to use this command"]
    # print("meow")
    if not ctx.value.strip(" "):
        return []

    try:
        c = postgresem("./data/tf2helper.db")
        c.execute(
            """
            SELECT b.id, b.playername, b.playerip, b.playeruid, b.lastseen
            FROM banstf1 b
            WHERE LOWER(b.playername) LIKE ?
            ORDER BY 
                CASE WHEN LOWER(b.playername) LIKE ? THEN 0 ELSE 1 END,
                b.lastseen DESC,
                LENGTH(b.playername)
            LIMIT 25
        """,
            (f"%{ctx.value.strip(' ').lower()}%", f"{ctx.value.strip(' ').lower()}%"),
        )

        results = c.fetchall()
        c.close()
        if not results:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            return ["No matches found"]

        options = []
        current_time = int(time.time())

        for ban_id, name, ip, uid, lastseen in results:
            if lastseen:
                time_diff = current_time - lastseen
                days = time_diff // 86400
                hours = (time_diff % 86400) // 3600
                minutes = (time_diff % 3600) // 60
                time_ago = f"{days}d {hours}h {minutes}m ago"
            else:
                time_ago = "unknown"

            uid_str = str(uid) if uid else "unknown"
            ip_str = ip if ip else "unknown"

            name_with_id = f"{name} ({ban_id})"

            option = f"{name} | {ip_str} | {uid_str} | {time_ago}"
            options.append(option[:80])
        # print("w",options)
        return options

    except Exception as e:
        print(f"Error in autocompletenamesfromtf1bans: {e}")
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["Database error"]


async def autocompletenamesfromingame(ctx):
    """autocompletes using who is playing on the server. includes all / _ options"""
    channel = getchannelidfromname(False, ctx.interaction)
    main = ["all", "_"]
    if channel and channel in discordtotitanfall:
        main.extend(list(discordtotitanfall[channel]["currentplayers"].values()))
    else:
        main.extend(list(map(lambda x: x["name"],filter(lambda x: not mostrecentmatchids.get(x["serverid"]) or mostrecentmatchids.get(x["serverid"]) == x["matchid"],peopleonline.values()))))
    main = list(set([str(p) for p in main]))
    output = sorted(
        list(filter(lambda x: ctx.value.strip(" ").lower() in x.lower(), main)),
        key=lambda x: x.lower().startswith(ctx.value.strip(" ").lower()) * 50,
        reverse=True,
    )
    if len(main) == 2:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No one playing"]
    elif len(output) == 2:
        return ["No matches"]

    return output


async def autocompletenamesfromingamenowildcard(ctx):
    """autocompletes using who is playing. does not include all / _ options"""
    channel = getchannelidfromname(False, ctx.interaction)
    if channel and channel in discordtotitanfall:
        main = list(discordtotitanfall[channel]["currentplayers"].values())
    else:
        main = list(map(lambda x: x["name"],filter(lambda x: not mostrecentmatchids.get(x["serverid"]) or mostrecentmatchids.get(x["serverid"]) == x["matchid"],peopleonline.values())))
    main = list(set([str(p) for p in main]))
    output = sorted(
        list(filter(lambda x: ctx.value.strip(" ").lower() in x.lower(), main)),
        key=lambda x: x.lower().startswith(ctx.value.strip(" ").lower()) * 50,
        reverse=True,
    )
    if len(main) == 0:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        return ["No one playing"]
    elif len(output) == 0:
        return ["No matches"]

    return output


@functools.lru_cache(maxsize=None)
def getallweaponnames(weapon):
    """Processes weapon names with fuzzy matching for autocomplete functionality"""
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        "SELECT DISTINCT cause_of_death FROM specifickilltracker ORDER BY cause_of_death"
    )
    weapons = list(c.fetchall())
    weapons = list(
        set(
            [
                *weapons,
                *list(
                    map(
                        lambda x: (x["weapon_name"],),
                        [
                            *ABILITYS_PILOT,
                            *GRENADES,
                            *DEATH_BY_MAP,
                            *MISC_MISC,
                            *MISC_TITAN,
                            *MISC_PILOT,
                            *CORES,
                            *GUNS_TITAN,
                            *GUNS_PILOT,
                            *ABILITYS_TITAN,
                        ],
                    )
                ),
            ]
        )
    )
    return sorted(
        list(
            map(
                lambda x: WEAPON_NAMES.get(x[0], x[0]),
                list(
                    filter(
                        lambda x: (
                            WEAPON_NAMES.get(x[0], False)
                            and weapon.lower() in WEAPON_NAMES.get(x[0], "").lower()
                        )
                        or weapon.lower() in x[0].lower(),
                        weapons,
                    )
                ),
            )
        ),
        key=lambda x: x.lower().startswith(weapon.lower()) * 50,
        reverse=True,
    )[:30]


async def weaponnamesautocomplete(ctx):
    """probably should not cache this, due to new guns being added, but this returns all matching guns"""
    return getallweaponnames(ctx.value.strip(" "))


@bot.event
async def on_ready():
    global context
    global botisalreadyready
    print(f"{bot.user} Connected!!")
    if context["categoryinfo"]["logging_cat_id"] != 0:
        # get all channels in the category and store in serverchannels
        guild = bot.get_guild(context["categoryinfo"]["activeguild"])
        category = guild.get_channel(context["categoryinfo"]["logging_cat_id"])
        serverchannels = category.channels
    if not botisalreadyready:
        if DISCORDBOTLOGSTATS == "1":
            updateleaderboards.start()
        updateroles.start()
        
        # 
        load_extensions()
        await hideandshowchannels(None,True)
        await asyncio.sleep(30)
        updatechannels.start()
        hideandshowchannels.start()


    botisalreadyready = True


@bot.event
async def on_interaction(interaction):
    # Only handle component interactions with "dropdown" in custom_id
    if (interaction.type == discord.InteractionType.component and 
        interaction.data.get('custom_id', '') and 
        'dropdown' in interaction.data.get('custom_id', '')):
        
        await droppycallback(interaction)
        return
    
    # For all other interactions, explicitly process them with the bot
    await bot.process_application_commands(interaction)


@tasks.loop(seconds=1800)
async def updateroles():
    """If a user messages the bot in dms, they have no roles. this serves to check their roles, so if they run a admin command, the bot knows they are admin in a dm (and also in game)"""
    global knownpeople, context
    if not context["categoryinfo"]["activeguild"]:
        return
    guild = bot.get_guild(context["categoryinfo"]["activeguild"])
    for roletype, potentialrole in context["overrideroles"].items():
        if isinstance(potentialrole, int):
            potentialrole = [potentialrole]
        uids = []
        for role in potentialrole:
            if not role:
                continue
            # context["overriderolesuids"][roletype]
            uids.extend([member.id for member in guild.get_role(role).members])
        context["overriderolesuids"][roletype] = uids
    knownpeople = {
        x.id: {
            "name": x.global_name if x.global_name else x.display_name,
            "nick": x.nick,
            "username": x.name,
        }
        for x in guild.members
    }
    savecontext()
    checkrconallowedtfuid.cache_clear()

@tasks.loop(seconds=7200)
async def hideandshowchannels(serveridforce = None, force = False):
    """hide inactive servers"""
    if not context["categoryinfo"]["hidden_cat_id"] or not TIMETILLCHANNELSGETHIDDEN:
        return
    now = time.time()
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    guild = bot.get_guild(context["categoryinfo"]["activeguild"])
    hidden = discord.utils.get(guild.categories, id=context["categoryinfo"]["hidden_cat_id"])
    found = discord.utils.get(guild.categories, id=context["categoryinfo"]["logging_cat_id"])
    if force:
        for server,details in context["servers"].items():
            channel = bot.get_channel(details["channelid"])
            category = channel.category
            if category.id != context["categoryinfo"]["logging_cat_id"]:
                context["servers"][server]["ishidden"] = True
            else:
                context["servers"][server]["ishidden"] = False
    ididthisserver = []
    enumeratethrough = enumerate([*context["categoryinfo"]["idealorder"],*list(map(lambda x: x[0],sorted(sorted(filter(lambda x: not serveridforce or serveridforce == x[0], context["servers"].items()),key = lambda x: x[0]),key = lambda x: x[1].get("widget","zzzz") or "zzzz")))])
    for index,server in enumeratethrough:
        # print(context["servers"][server]["name"])
        if server in ididthisserver:
            continue
        ididthisserver.append(server)
        if server not in context["categoryinfo"]["idealorder"]: context["categoryinfo"]["idealorder"].insert(index,server)
        placement = functools.reduce(lambda a,b: {**a,"hasfound":True} if b == server else (a if (a["hasfound"] or context["servers"][b].get("ishidden",bot.get_channel(context["servers"][b]["channelid"]).id != context["categoryinfo"]["logging_cat_id"]) == True) else {**a,"server":b}),  context["categoryinfo"]["idealorder"],{"server":None,"hasfound":False})["server"]
        if not placement:
            actualplacement = functools.reduce(lambda a,b: {**a,"hasfound":True} if b == server else ({**a,"server":b} if (not a["server"] and (a["hasfound"] and not context["servers"][b].get("ishidden",bot.get_channel(context["servers"][b]["channelid"]).id != context["categoryinfo"]["logging_cat_id"]) == True)) else a),  context["categoryinfo"]["idealorder"],{"server":None,"hasfound":False})["server"]
            # print("placing before",actualplacement)
        
        istf1 = bool(context["servers"][server].get("istf1server",False) )
        c.execute(f"SELECT time FROM matchid{"tf1" if istf1 else ""} WHERE serverid = ? ORDER BY time DESC LIMIT 1",(server,))
        mostrecentmatchid = c.fetchone()
        if not mostrecentmatchid:
            mostrecentmatchid = [0] # bork to make sure that servers that have never been played on get shadow wealmed
        mostrecentmatchid = mostrecentmatchid[0]
        channel = bot.get_channel(context["servers"][server]["channelid"])
        category = channel.category
        # set to not equal for now, instead of == hidden_cat_id so that the ones in the weird old limbo cat slowly get moved
        if (force or category.id != context["categoryinfo"]["logging_cat_id"]) and now - TIMETILLCHANNELSGETHIDDEN < mostrecentmatchid:
            if not force:
                print("showing",context["servers"][server]["name"],("after" if placement else "before"),placement or actualplacement)

            if not placement and actualplacement:
                await channel.move(sync_permissions=True,category=found,before=bot.get_channel(context["servers"][actualplacement]["channelid"]))
            elif not placement and not actualplacement:
                await channel.move(sync_permissions=True,category=found,beginning=True)
            else:
                await channel.move(sync_permissions=True,category=found,after=bot.get_channel(context["servers"][placement]["channelid"]))
            context["servers"][server]["ishidden"] = False
            pass
            # show the channel
        elif (force or category.id == context["categoryinfo"]["logging_cat_id"]) and now - TIMETILLCHANNELSGETHIDDEN > mostrecentmatchid:
            if not force:
                print("hiding",context["servers"][server]["name"])

            await channel.edit(sync_permissions=True,category=hidden)
            context["servers"][server]["ishidden"] = True
            # hide the channel
        # else:
        #     print(context["servers"][server]["name"],force,category.id != context["categoryinfo"]["logging_cat_id"],category.id == context["categoryinfo"]["logging_cat_id"],(now - TIMETILLCHANNELSGETHIDDEN < mostrecentmatchid))
    savecontext()
    tfdb.close()



@bot.event
async def on_member_joinadd(member):
    knownpeople[member.id] = {
        "name": member.global_name if member.global_name else member.display_name,
        "nick": None,
        "username": member.name,
    }


@bot.slash_command(
    name="messagelogs",
    description="Pull all non command message logs with a given filter",
)
async def pullmessagelogs(ctx, filterword1: str = "", filterword2: str = "", filterword3: str = ""):
    """returns all messages with that matching string"""

    await ctx.defer()
    threading.Thread(
        target=threadwrap, daemon=True, args=(threadedfinder, ctx, filterword1,filterword2,filterword3)
    ).start()


def threadedfinder(ctx, filterword1,filterword2,filterword3):
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """
        SELECT message, type, serverid
        FROM messagelogger
        WHERE message LIKE ? AND message LIKE ? AND message LIKE ? COLLATE NOCASE
        AND type NOT IN ('command', 'tf1command', 'botcommand')
    """,
        ("%" + filterword1 + "%","%" + filterword2 + "%","%" + filterword3 + "%"),
    )
    matches = [{**(getjson(row[0])), "serverid": row[2]} for row in c.fetchall()][::-1]
    truncationmessage = ""
    if len(matches) > 1000:
        truncationmessage = (
            f"- only 1000 shown, {len(matches) - 1000} messages truncated"
        )
    matches = matches[:1000]
    tfdb.close()
    if matches:
        file_obj = io.BytesIO(json.dumps(matches, indent=4).encode("utf-8"))
        file_obj.seek(0)
        discord_file = discord.File(file_obj, filename="matches.json")
        asyncio.run_coroutine_threadsafe(
            ctx.respond(f"Matching Messages{truncationmessage}:", file=discord_file),
            bot.loop,
        )
    else:
        asyncio.run_coroutine_threadsafe(
            asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND), bot.loop
        )
        asyncio.run_coroutine_threadsafe(ctx.respond("No matches found."), bot.loop)


@bot.slash_command(
    name="bindloggingtocategory",
    description="Bind logging to a new category (begin logging) can be existing or new",
)
async def bind_logging_to_category(ctx, category_name: str):
    """only used once. tells the bot to use a specific category on discord to add new servers"""
    global context
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("bindcategory")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.")
        return
    guild = ctx.guild
    if guild.id == context["categoryinfo"]["activeguild"] and context["categoryinfo"]["logging_cat_id"] != 0:
        await ctx.respond("Logging is already bound to a category.", ephemeral=False)
        return
    # Create the new category, unless the name exists, then bind to that one
    if category_name in [category.name for category in guild.categories]:
        category = discord.utils.get(guild.categories, name=category_name)
        print("binding to existing category")
    else:
        category = await guild.create_category(category_name)
        print("creating new category")

    context["categoryinfo"]["logging_cat_id"] = category.id
    # Store the channel ID in the variable
    # context["categoryinfo"]["logging_cat_id"]= channel.id
    context["categoryinfo"]["activeguild"] = guild.id

    # Save the channel ID to the file for persistence
    savecontext()

    await ctx.respond(
        f"Logging channel cat created under category '{category_name}' with channel ID {context["categoryinfo"]["logging_cat_id"]}.",
        ephemeral=False,
    )

@bot.slash_command(
    name="bindinactivechannelcategory",
    description="designate a category where servers that have not been played for 3 days will be moved",
)
async def bind_hidden_to_category(ctx, category_name: str):
    """only used once. tells the bot to use a specific category on discord to add new servers"""
    global context
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("bindcategory")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.")
        return
    guild = ctx.guild

    if guild.id != context["categoryinfo"]["activeguild"]:
        await ctx.respond("This category is not in the same guild", ephemeral=False)
        return
    # Create the new category, unless the name exists, then bind to that one
    if category_name in [category.name for category in guild.categories]:
        category = discord.utils.get(guild.categories, name=category_name)
        print("binding to existing category")
    else:
        category = await guild.create_category(category_name)
        print("creating new category")

    context.setdefault("categoryinfo",{})["hidden_cat_id"] = category.id
    # Store the channel ID in the variable
    # context["categoryinfo"]["logging_cat_id"]= channel.id
    # context["categoryinfo"]["activeguild"] = guild.id

    # Save the channel ID to the file for persistence
    savecontext()

    await ctx.respond(
        f"hidden channel cat created under category '{category_name}' with channel ID {context["categoryinfo"]["logging_cat_id"]}.",
        ephemeral=False,
    )

@bot.slash_command(name="sanctionchecktf2", description="Shows a players Sanction")
async def sanctiontf2check(
    ctx,
    name: Option(str, "The playername / uid", autocomplete=autocompletenamesfromdb),
    # banlinks:Option(int, "How many links needed for a ban to persist (DON'T USE IF DON'T KNOW)",choices=[1,2,3]),
    #     servername: Option(
    #     str,
    #     "The servername (omit for current channel's server)",
    #     required=False,
    #     **({
    #         "choices": list(s.get("name", "Unknown") for s in context["servers"].values())
    #     } if SERVERNAMEISCHOICE == "1" else {
    #         "autocomplete": autocompleteserversfromdb
    #     })
    # ) = None,
):
    output = process_matchingtf2(name)
    if isinstance(output, str):
        await ctx.respond(output)
        return
    await ctx.respond(embed=embedjson("Existing Sanction:", output, ctx))


def process_matchingtf2(name):
    matchingplayers = resolveplayeruidfromdb(name, None, True)
    # if len(matchingplayers) > 1:
    #     multistring = "\n" + "\n".join(f"{i+1}) {p['name']} uid: {p['uid']}" for i, p in enumerate(matchingplayers[0:10]))
    #     return f"{len(matchingplayers)} players found, please be more specific: {multistring}"
    if len(matchingplayers) == 0:
        return "No players found"
    player = matchingplayers[0]
    sanction, messageid = pullsanction(player["uid"])
    if sanction:
        return sanction
    return f"No sanction found for {player['name']}"


@bot.slash_command(name="sanctionchecktf1", description="Shows a TF1 player's sanction")
async def sanctiontf1check(
    ctx,
    name: Option(str, "The playername", autocomplete=autocompletetf1namesfromdb),
):
    await ctx.defer()
    output = process_matchingtf1(name)
    if isinstance(output, str):
        await ctx.respond(output)
        return
    await ctx.respond(embed=embedjson("Existing Sanction:", output, ctx))


def process_matchingtf1(name):
    matchingplayers = resolveplayeruidfromdb(name, None, True, True)
    
    if len(matchingplayers) == 0:
        return "No players found"
    
    player = matchingplayers[0]
    player_name = player['name']
    player_uid = player['uid']
    
    c = postgresem("./data/tf2helper.db")
    
    c.execute(
        "SELECT id FROM banstf1 WHERE playername = ? AND playeruid = ?",
        (player_name, int(player_uid))
    )
    playerid = c.fetchone()
    
    if not playerid:
        c.close()
        return f"No ban record found for {player_name}"
    
    playerid = playerid[0]
    

    c.execute(
        "SELECT playerip, playername, playeruid, bantype, banlinks, baninfo, expire, id FROM banstf1"
    )
    bans = list(
        map(
            lambda x: {
                "ip": x[0],
                "name": x[1],
                "uid": x[2],
                "bantype": x[3],
                "banlinks": x[4],
                "baninfo": x[5],
                "expire": x[6],
                "exhaustion": 0,
                "id": x[7],
            },
            list(c.fetchall()),
        )
    )
    c.close()
    

    bannedpeople = findallbannedpeople(
        bans,
        list(
            filter(
                lambda x: x["bantype"]
                and (x["expire"] is None or x["expire"] > int(time.time())),
                bans,
            )
        ),
        10,  
    )
    

    player_ban = list(filter(lambda x: playerid == x["id"], bannedpeople))
    
    if not player_ban:
        return f"No sanction found for {player_name}"
    
    ban = player_ban[0]
    
    sanction_info = {
        "name": player_name,
        "uid": str(player_uid),
        "sanctiontype": ban["bantype"],
        "reason": ban["baninfo"] if ban["baninfo"] else "No reason provided",
        "expiry": modifyvalue(ban["expire"], "date") if ban["expire"] else "Never",
        "status": "Active (inherited)" if ban.get("origbanid") and ban["origbanid"] != ban["id"] else "Active"
    }
    
    return sanction_info


@bot.slash_command(name="togglewordfilter", description="Adds or removes a word filter")
async def keywordtoggle(
    ctx,
    typeofkeyword: Option(
        str,
        "what list the keyword should be in / removed from",
        choices=list(context["wordfilter"].keys()),
    ),
    keywordtotoggle: Option(
        str, "The keyword to remove / add", autocomplete=autocompletefilterwordcomplete
    ),
):
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("wordfiltermodify")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.")
        return
    keywordtotoggle = keywordtotoggle.rsplit("-", 1)[0].strip(" ")
    if keywordtotoggle in context["wordfilter"][typeofkeyword]:
        context["wordfilter"][typeofkeyword].pop(
            context["wordfilter"][typeofkeyword].index(keywordtotoggle)
        )
        savecontext()
        await ctx.respond(f"Deleted {keywordtotoggle} from {typeofkeyword}")
        return
    context["wordfilter"][typeofkeyword].append(keywordtotoggle.lower())
    savecontext()
    await ctx.respond(f"Added `{keywordtotoggle}` to {typeofkeyword}")


@bot.slash_command(
    name="sanctiontf2",
    description="Sanctions a tf2 player - run in a server channel to apply instantly",
)
async def sanctiontf2(
    ctx,
    name: Option(
        str, "The playername / uid", autocomplete=autocompletenamesanduidsfromdb
    ),
    sanctiontype: Option(
        str,
        "The type of sanction to apply (meanmute does not alert the person muted)",
        choices=["mute", "ban", "meanmute","nessify"],
    ),
    # banlinks:Option(int, "How many links needed for a ban to persist (DON'T USE IF DON'T KNOW)",choices=[1,2,3]),
    reason: Option(str, "The reason for the sanction", required=True),
    expiry: Option(
        str,
        "The expiry date in format yyyy-mm-dd, (or enter num days) 'never' is forever (uses gmt time)",

    ),
    #     servername: Option(
    #     str,
    #     "The servername (omit for current channel's server)",
    #     required=False,
    #     **({
    #         "choices": list(s.get("name", "Unknown") for s in context["servers"].values())
    #     } if SERVERNAMEISCHOICE == "1" else {
    #         "autocomplete": autocompleteserversfromdb
    #     })
    # ) = None,
):
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("sanctionsomonetf2")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.")
        return

    # serverid = getchannelidfromname(servername,ctx)
    try:
        where = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.interaction.id}"
    except:
        where = "RAN IN A DM"
    output = await process_sanctiontf2(
        False, ctx.author.name, name, sanctiontype, reason, ("never" != expiry or None) and expiry , where
    )
    if isinstance(output, str):
        await ctx.respond(output)
        return
    await ctx.respond(embed=embedjson("New Sanction:", output, ctx))


def embedjson(name, output, ctx=False):
    embed = discord.Embed(
        title=f"**{name}**",
        color=0xFF70CB,
        # description=output["title"]["description"],
    )
    for field, data in output.items():
        if field == "textversion":
            continue
        embed.add_field(
            name=f"> {field.title()}:",
            value=f"{'\u200b \u200b \u200b \u200b \u200b \u200b \u200b' if False else ''} {data}",
            inline=True,
        )
    return embed


def pullsanction(uid):
    existing_sanction = getpriority(
        readplayeruidpreferences(uid, False), ["banstf2", "sanction"], nofind={}
    )
    if (
        existing_sanction
        and "expiry" in existing_sanction
        and not (
            existing_sanction.get("expiry")
            and existing_sanction["expiry"]
            and int(time.time()) > existing_sanction["expiry"]
        )
    ):
        try:
            expiry_text = (
                modifyvalue(existing_sanction["expiry"], "date")
                if existing_sanction["expiry"]
                else "Never"
            )
        except (OSError, ValueError, OverflowError):
            expiry_text = f"Invalid date ({existing_sanction['expiry']})"
        name = resolveplayeruidfromdb(uid, None, True)
        if name:
            name = name[0]["name"]
        else:
            name = "Unknown player"
        return {
            **existing_sanction,
            "uid":uid,
            "affectedplayer": name,
            "humanexpire": expiry_text,
            "link": f"https://discord.com/channels/{context["categoryinfo"]["activeguild"]}/{context['overridechannels']['globalchannel']}/{existing_sanction.get('messageid')}"
            if existing_sanction.get("messageid")
            else None,
            "textversion": f"**Type**: `{existing_sanction['sanctiontype']}`\n**Expires:** `{expiry_text}`\n**Reason:** `{existing_sanction['reason']}`"
            + (
                f"\n**Issuer:** {existing_sanction.get('issuer')}"
                if existing_sanction.get("issuer")
                else "\nNo Issuer found"
            )
            + (
                f"\n**Source:** {existing_sanction.get('source')}"
                if existing_sanction.get("source")
                else "\nNo source found"
            )
            + (
                f"\n**Issuedelta:** {existing_sanction.get('issuedelta')}"
                if existing_sanction.get("issuedelta")
                else "\nUnknown issuedelta"
            )
            + (
                f"\n**Link:** https://discord.com/channels/{context["categoryinfo"]["activeguild"]}/{context['overridechannels']['globalchannel']}/{existing_sanction.get('messageid')}"
                if existing_sanction.get("messageid")
                else "\nNo link found"
            ),
        }, existing_sanction.get("messageid")
    return {}, existing_sanction.get("messageid") if existing_sanction else False

async def quickaddsanction(target,action,interaction,link):
    # print(interaction.user.id)
    if not checkrconallowed(interaction.user,getslashcommandoverridesperms("sanctionsomonetf2")):
        await interaction.respond("You are not allowed to use this interaction.",ephemeral = True)
        return
    # link = f"https://discord.com/channels/{context["categoryinfo"]["activeguild"]}/{context["servers"][link[0]]["channelid"]}/{link[1]}"
    interaction_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{interaction.message.id}"
    if action == "unsanction":
        output = await process_sanctionremovetf2(interaction.user.name,target,interaction_link)
    else:
        output = await process_sanctiontf2(False,interaction.user.name,target,action["type"],link,str(action["duration"]),interaction_link)
    if isinstance(output, str):
        await interaction.respond(output)
        return
    await interaction.respond(embed=embedjson("New Sanction:" if action != "unsanction" else "Removed Sanction:", output, interaction))
async def process_sanctiontf2(
    serverid, sender, name, sanctiontype, reason, expiry=None, iscommand=False
):
    name = str(name)
    if len(name.rsplit("->", 1)) > 1:
        name = name.rsplit("->", 1)[1][1:-1]
    matchingplayers = resolveplayeruidfromdb(name, None, True)
    if len(matchingplayers) > 1:
        multistring = "\n" + "\n".join(
            f"{i + 1}) {p['name']} uid: {p['uid']}"
            for i, p in enumerate(matchingplayers[0:10])
        )
        return f"{len(matchingplayers)} players found, please be more specific: {multistring}"
    elif len(matchingplayers) == 0:
        return "No players found"

    player = matchingplayers[0]
    if not serverid:
        serverid = player["lastserverid"]
    existing_messageid = None
    existing_sanction, existing_messageid = pullsanction(player["uid"])
    if existing_sanction:
        return f"{player['name']} already has a sanction!\n{existing_sanction['textversion']}"

    if expiry:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            expiry = int(expiry_date.timestamp())
        except ValueError:
            if expiry.isdigit():
                expiry = int(float(expiry) * 86400 + int(time.time()))
            else:
                try: expiry = int(float(expiry) * 86400 + int(time.time()))
                except: return "Invalid expiry date format. Use yyyy-mm-dd"
    else:
        expiry = None

    expiry_log_text = modifyvalue(expiry, "date") if expiry else None

    global_channel = bot.get_channel(context["overridechannels"]["globalchannel"])
    if global_channel:
        if existing_messageid:
            try:
                existing_message = await global_channel.fetch_message(
                    existing_messageid
                )
                message = await existing_message.reply(
                    f"New {sanctiontype} uploaded by {sender} for player {player['name']} UID: {player['uid']} {'Expiry: ' + expiry_log_text if expiry_log_text else ''} {'Reason: ' + reason if reason else ''} Source: {iscommand if iscommand else 'in game'}"
                )
            except:
                message = await global_channel.send(
                    f"New {sanctiontype} uploaded by {sender} for player {player['name']} UID: {player['uid']} {'Expiry: ' + expiry_log_text if expiry_log_text else ''} {'Reason: ' + reason if reason else ''} Source: {iscommand if iscommand else 'in game'}"
                )
        else:
            message = await global_channel.send(
                f"New {sanctiontype} uploaded by {sender} for player {player['name']} UID: {player['uid']} {'Expiry: ' + expiry_log_text if expiry_log_text else ''} {'Reason: ' + reason if reason else ''} Source: {iscommand if iscommand else 'in game'}"
            )
        message_id = message.id
    else:
        message_id = None
        # str(player["uid"])
    print(
        modifyvalue(
            peopleonline.get(str(player["uid"]), player)["lastseen"], "deltadate"
        )
    )
    lastseen = modifyvalue(
        peopleonline.get(str(player["uid"]), player)["lastseen"], "deltadate"
    )
    setplayeruidpreferences(
        ["banstf2", "sanction"],
        {
            "reason": reason,
            "expiry": expiry,
            "sanctiontype": sanctiontype,
            "messageid": message_id,
            "issuer": sender,
            "issuedelta": lastseen,
            "source": iscommand if iscommand else "in game",
        },
        player["uid"],
    )
    expiry_text = "forever" if expiry is None else modifyvalue(expiry, "date")
    if serverid:
        sendrconcommand(
            serverid,
            f"!reloadpersistentvars {player['uid']}",
            sender=sender,
            prefix=f"New {sanctiontype}",
        )

    # return f"**{sanctiontype.capitalize()}** applied to **{player['name']}** (UID: `{player['uid']}`) until **{expiry_text}**\nReason: {reason}"
    if iscommand:
        return {
            **player,
            **{
                "reason": reason,
                "expiry": expiry,
                "humanexpiry":expiry_text,
                "sanctiontype": sanctiontype,
                "messageid": message_id,
                "issuer": sender,
                "issuedelta": lastseen,
                "source": iscommand if iscommand else "in game",
            },
        }

    return f"{sanctiontype.capitalize()} added to {player['name']} (UID: {player['uid']}) Until {expiry_text}\nReason: {reason}"


async def process_sanctionremovetf2(sender, name, where):
    name = str(name)
    if len(name.rsplit("->", 1)) > 1:
        name = name.rsplit("->", 1)[1][1:-1]

    matchingplayers = resolveplayeruidfromdb(name, None, True)
    if len(matchingplayers) > 1:
        multistring = "\n" + "\n".join(
            f"{i + 1}) {p['name']} uid: {p['uid']}"
            for i, p in enumerate(matchingplayers[0:10])
        )
        return f"{len(matchingplayers)} players found, please be more specific: {multistring}"
    elif len(matchingplayers) == 0:
        return "No players found"
    
    player = matchingplayers[0]
    ban, existing_messageid = pullsanction(player["uid"])
    if ban:
        global_channel = bot.get_channel(context["overridechannels"]["globalchannel"])
        if global_channel:
            if existing_messageid:
                try:
                    existing_message = await global_channel.fetch_message(
                        existing_messageid
                    )
                    message = await existing_message.reply(
                        f"{sender} removed sanction for {player['name']} (UID: {player['uid']}) - Type: {ban['sanctiontype']} - Reason: {ban['reason']} - Source: {where}"
                    )
                except:
                    message = await global_channel.send(
                        f"{sender} removed sanction for {player['name']} (UID: {player['uid']}) - Type: {ban['sanctiontype']} - Reason: {ban['reason']} - Source: {where}"
                    )
            else:
                message = await global_channel.send(
                    f"{sender} removed sanction for {player['name']} (UID: {player['uid']}) - Type: {ban['sanctiontype']} - Reason: {ban['reason']} - Source: {where}"
                )
            message_id = message.id
        else:
            message_id = None

        setplayeruidpreferences(
            ["banstf2", "sanction"], {"messageid": message_id}, player["uid"]
        )

        if player["lastserverid"]:
            sendrconcommand(
                player["lastserverid"],
                f"!reloadpersistentvars {player['uid']}",
                sender=sender,
            )
        
        return ban
    else:
        return f"No sanction found for {player['name']} (UID: `{player['uid']}`)"


@bot.slash_command(
    name="sanctionremovetf2",
    description="Removes a ban from a TF2 player - run in a server channel to apply instantly",
)
async def sanctionremovetf2(
    ctx,
    name: Option(str, "The playername", autocomplete=autocompletenamesanduidsfromdb),
    #         servername: Option(
    #     str,
    #     "The servername (omit for current channel's server)",
    #     required=False,
    #     **({
    #         "choices": list(s.get("name", "Unknown") for s in context["servers"].values())
    #     } if SERVERNAMEISCHOICE == "1" else {
    #         "autocomplete": autocompleteserversfromdb
    #     })
    # ) = None,
):
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("sanctionsomonetf2")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return

    try:
        where = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.interaction.id}"
    except:
        where = "RAN IN A DM"

    await ctx.defer()
    output = await process_sanctionremovetf2(ctx.author.name, name, where)
    if isinstance(output, str):
        await ctx.respond(output)
        return
    await ctx.respond(embed=embedjson("Removing Sanction:", output, ctx))


@bot.slash_command(
    name="sanctiontf1",
    description="Sanctions a tf1 player",
)
async def sanctiontf1(
    ctx,
    name: Option(str, "The playername", autocomplete=autocompletenamesfromtf1bans),
    sanctiontype: Option(str, "The type of sanction to apply", choices=["mute", "ban"]),
    # banlinks:Option(int, "How many links needed for a ban to persist (DON'T USE IF DON'T KNOW)",choices=[1,2,3]),
    reason: Option(str, "The reason for the sanction", required=True),
    expiry: Option(
        str,
        "The expiry date in format yyyy-mm-dd (or enter num days), 'never' is forever (uses gmt time)",

    ) 
):
    """ban somone in tf1 (or mute)"""
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("sanctionsomonetf1")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return
    # banid = name.lsplit("|",1)[0].strip().rsplit(" ",1)[1:-1]
    baninfo = {
        "uploadtime": int(time.time()),
        "uploaded by": ctx.author.name,
        "type": sanctiontype,
        "reason": reason,
    }
    expiry = ("never" != expiry or None) and expiry
    if expiry:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            baninfo["expiry"] = int(expiry_date.timestamp())
        except ValueError:
            if expiry.isdigit():
                baninfo["expiry"] = int(expiry) * 86400 + int(time.time())
            else:
                await ctx.respond(
                    "Invalid expiry date format. Use yyyy-mm-dd or number of days",
                    ephemeral=False,
                )
                return
    else:
        baninfo["expiry"] = None
    print(name)
    print(name.split(" | "))
    if len(name.split(" | ")) != 4:
        await ctx.respond(
            "You have to select one of the options that appear for names, you cannot just put something like 'Lexi'"
        )
        return
    name, ip, uid, lastseen = name.split(" | ")
    global_channel = bot.get_channel(context["overridechannels"]["globalchannel"])
    if global_channel:
        message = await global_channel.send(
            f"New {sanctiontype} uploaded by {ctx.author.name} for player {name} UID: {uid} {'Expiry: ' + modifyvalue(baninfo['expiry'], 'date') if expiry else ''} {'Reason: ' + reason if reason else ''}"
        )
        message_id = message.id
    else:
        message_id = None

    c = postgresem("./data/tf2helper.db")
    c.execute(
        "UPDATE banstf1 SET banlinks = ?, bantype = ?, baninfo = ?, expire = ?, messageid = ? WHERE playername = ? AND playerip = ? AND playeruid = ?",
        (2, sanctiontype, reason, baninfo["expiry"], message_id, name, ip, uid),
    )
    c.execute(
        "SELECT lastserverid FROM banstf1 WHERE playername = ? AND playerip = ? AND playeruid = ?",
        (name, ip, uid),
    )

    serverid = c.fetchone()[0]
    c.commit()
    c.close()
    expiry_text = (
        "forever"
        if baninfo["expiry"] is None
        else modifyvalue(baninfo["expiry"], "date")
    )

    output = {
        "name": name,
        "uid": str(uid),
        "sanctiontype": sanctiontype,
        "reason": reason,
        "expiry": expiry_text,
        "status": "Tried to kick player"
        if sanctiontype == "ban"
        else "The mute happens on map change",
    }

    await ctx.respond(embed=embedjson("New Sanction:", output, ctx))
    if sanctiontype == "ban":
        # print(serverid,f'kick {name}')
        sendrconcommand(str(serverid), f"banip 7200 {ip}" ,sender=ctx.author.name)
    # else: sadly don't know their uid. cannot be bothered to fix tbh I could just kick em but na
    # await (returncommandfeedback(*sendrconcommand(str(serverid),f'!muteplayer {message["kickid"]} {PREFIXES["warning"]}{(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).strftime(f"%-d{'th' if 11 <= datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day % 10, 'th')} of %B %Y")) if list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"] else "never"} rsn {PREFIXES["warning"]}{list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["baninfo"]}'),"fake context",None,True,False), bot.loop)


# if SANCTIONAPIBANKEY != "":
#     @bot.slash_command(
#         name="serverlesssanction",
#         description="Sanctions a offline player, without a server. try saying it 3 times fast",
#     )
#     async def serverlesssanction(
#         ctx,
#         playeroruid: Option(str, "Sanction a name or uid", required=True, choices=["uid", "name"]),
#         who: Option(str, "The playername/uid to sanction", required=True,autocomplete=autocompletenamesanduidsfromdb),

#         sanctiontype: Option(
#             str, "The type of sanction to apply", choices=["mute", "ban"] ),
#         reason: Option(str, "The reason for the sanction", required=True),
#         expiry: Option(str, "The expiry time of the sanction in format yyyy-mm-dd, omit is forever") = None,
#     ):
#         """ mute somone in tf|2, bypassing the servers, so can mute / ban offline people"""
#         global context,messageflush
#         if not checkrconallowed(ctx.author):
#             await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
#             await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#             return
#         if len(who.rsplit("->",1)) > 1: who = who.rsplit("->",1)[1][1:-1]
#         matchingplayers = resolveplayeruidfromdb(who, None,True)
#         if len (matchingplayers) > 1:
#             multistring = "\n" + "\n".join(f"{i+1}) {p['name']} uid: {p['uid']}" for i, p in enumerate(matchingplayers[0:10]))
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


if DISCORDBOTLOGSTATS == "1":

    def tf1pullstats(playerdetails, serverid):
        """displays a person's stats in game to them."""
        # print("running",playerdetails)
        # playerdetails = getjson(playerdetails.replace("♥",'"'))
        playeruid = playerdetails.get("meta", {}).get("entid", False)
        if not playeruid:
            playeruid = playerdetails.get("playeruid", False)
        playername = playerdetails.get("originalname", False)
        if not playername:
            playername = playerdetails.get("name", False)
        playerdiscorduid = playerdetails.get("uid", 0)
        playerresolvedfromuid = False

        if (
            playerdetails.get("originalmessage", False)
            and len(playerdetails["originalmessage"].split(" ")) > 1
        ):
            playerresolvedfromuid = resolveplayeruidfromdb(
                " ".join(playerdetails["originalmessage"].split(" ")[1:]),
                None,
                False,
                True,
            )
            playername = (playerdetails["originalmessage"]).split(" ")[1]
            playerdiscorduid = playerresolvedfromuid[0]["uid"]
        # print(playerresolvedfromuid)
        # recall the rule of sending external commands!
        if not len(str(playerdiscorduid)) > 15 and not playerresolvedfromuid:
            # a few workarounds in play, here, sadly.
            # disabled for now :)
            # sendrconcommand(
            #     serverid,
            #     f"!privatemessage {playeruid} No discord UID found, stats logging disabled",
            # )
            return

        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute(
            "SELECT playername FROM uidnamelinktf1 WHERE playeruid = ? ORDER BY id DESC LIMIT 1",
            (playerdiscorduid,),
        )
        playernamereal = c.fetchone()
        c.execute(
            "SELECT SUM(pilotkills), SUM(duration), SUM(deaths), SUM(titankills) FROM playtimetf1 WHERE playeruid = ?",
            (playerdiscorduid,),
        )
        playerstats = c.fetchone()
        c.execute(
            """
            WITH lag_data AS (
                SELECT *,
                    LAG(leftatunix, 1, 0) OVER (PARTITION BY playeruid, map ORDER BY joinatunix) as prev_left
                FROM playtimetf1
                WHERE playeruid = ?
            ),
            session_groups AS (
                SELECT *,
                    SUM(CASE WHEN joinatunix - prev_left > 450 THEN 1 ELSE 0 END) 
                        OVER (PARTITION BY playeruid, map ORDER BY joinatunix ROWS UNBOUNDED PRECEDING) as session_group
                FROM lag_data
            )
            SELECT matchid, map, MIN(joinatunix) as start_time, SUM(pilotkills) as total_pilotkills
            FROM session_groups
            GROUP BY matchid, map, session_group
            HAVING COUNT(*) = 1 OR (MAX(leftatunix) - MIN(joinatunix) <= 450 * COUNT(*))
            ORDER BY total_pilotkills DESC
            LIMIT 1
        """,
            (playerdiscorduid,),
        )
        bestgame = c.fetchone()
        if not playerstats or not playernamereal:
            sendrconcommand(
                serverid,
                f"!privatemessage {playeruid} Stats for {playername} not found :(",
            )
            return
        playernamereal = playernamereal[0]
        while True:
            colour = random.randint(0, 255)
            # colour = random.choice([254,219,87])
            # dissallowedcolours colours (unreadable)  (too dark)
            if colour not in DISALLOWED_COLOURS:
                break

        output = f"[38;5;{colour}m{playernamereal}{PREFIXES['chatcolour']} has {PREFIXES['stat']}{playerstats[0]} {PREFIXES['chatcolour']}Pilot kills, {PREFIXES['stat']}{playerstats[2]}{PREFIXES['chatcolour']} Deaths, {PREFIXES['stat']}{playerstats[3]}{PREFIXES['chatcolour']} Titan kills and {PREFIXES['stat']}{modifyvalue(int(playerstats[1] if playerstats[1] else 0), 'time')} {PREFIXES['chatcolour']}Time played"
        sendrconcommand(serverid, f"!privatemessage {playeruid} {output}",)
        if bestgame:
            formatted_date = datetime.fromtimestamp(bestgame[2]).strftime(
                f"%-d{'th' if 11 <= datetime.fromtimestamp(bestgame[2]).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(bestgame[2]).day % 10, 'th')} of %B %Y"
            )

            sendrconcommand(
                serverid,
                f"!privatemessage {playeruid} [38;5;{colour}m{playernamereal}{PREFIXES['chatcolour']} had their best game in {PREFIXES['stat']}{MAP_NAME_TABLE.get(bestgame[1], bestgame[1])}{PREFIXES['chatcolour']} with {PREFIXES['stat']}{bestgame[3]}{PREFIXES['chatcolour']} kills on {PREFIXES['stat']}{formatted_date}",
            )

    # @bot.slash_command(name="gunleaderboard",description="Gets leaderboards for a gun")
    # async def retrieveleaderboardgun(
    #     ctx,
    #     Gun: Option(str, "What gun?" choices = list(WEAPON_NAMES.keys())),
    #     # leaderboard: Option(
    #     #     str, "Witch leaderboard, omit for all, more specific data when not ommitted", choices=list(map(lambda x:x["name"],list(filter(lambda x:"name" in x.get("merge","none") ,context["leaderboardchannelmessages"]))))
    #     # ) = None
    # ):
    #     pass
    @bot.slash_command(
        name="pngleaderboard",
        description="Gets pngleaderboard for a player, takes a LONG time to calculate on the wildcard.",
    )
    async def retrieveleaderboard(
        ctx,
        playername: Option(
            str, "Who to get a leaderboard for", autocomplete=autocompletenamesfromdb
        ) = None,
        leaderboard: Option(
            str,
            "What weapon (please select one or pay my power bills)",
            autocomplete=weaponnamesautocomplete,
        ) = None,
        titanfall1: Option(str, "Use titanfall 1 database", choices=["Yes", "No"]) = "No",
        fliptovictims: Option(str, "Flip to victims?", choices=["Yes", "No"]) = "No",
        onlynpcscount: Option(str, "Only show leaderboards for npcs?", choices=["Yes", "No"]) = "No",

    ):
        """return a specific pngleaderboard to a person"""
        await ctx.defer()
        # def getweaponspng(swoptovictims = False,specificweapon=False, max_players=10, COLUMNS=False):
        # timestamp = await asyncio.to_thread(getweaponspng, leaderboard_entry.get("displayvictims", False),leaderboardcategorysshown, maxshown, leaderboard_entry.get("columns", False))
        if playername:
            player = resolveplayeruidfromdb(playername, None, True)
            if not player:
                await ctx.respond(f"{playername} player not found", ephemeral=False)
                return
        else:
            player = [{"uid":None,"name":"Everyone"}]
        searchterm = False
        if leaderboard:
            # tfdb = postgresem("./data/tf2helper.db")
            # c = tfdb
            # c.execute("SELECT DISTINCT cause_of_death FROM specifickilltracker ORDER BY cause_of_death")
            searchterm = list(
                filter(
                    lambda x: leaderboard.lower()
                    in WEAPON_NAMES.get(x["weapon_name"], x["weapon_name"]).lower(),
                    [
                        *ABILITYS_PILOT,
                        *GRENADES,
                        *DEATH_BY_MAP,
                        *MISC_MISC,
                        *MISC_TITAN,
                        *MISC_PILOT,
                        *CORES,
                        *GUNS_TITAN,
                        *GUNS_PILOT,
                        *ABILITYS_TITAN,
                    ],
                )
            )
            if not searchterm:
                searchterm = [
                    {
                        "weapon_name": leaderboard,
                        "png_name": leaderboard,
                        "mods": [],
                        "modsfiltertype": "include",
                        "killedby": ["player"],
                    }
                ]
        # print(searchterm)
        timestamp = await asyncio.to_thread(
            getweaponspng,
            fliptovictims != "No",
            searchterm,
            50 if searchterm else 10,
            False,
            350,
            player[0]["uid"],
            onlynpcscount == "Yes",
            titanfall1 == "Yes"
        )
        cdn_url = f"{GLOBALIP}/cdn/{timestamp}"
        if not timestamp:
            await ctx.respond(
                f"Failed to calculate pngleaderboard - generic error (there is probably no data for {player[0]['name']})"
            )
            return
        image_available = True
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(cdn_url + "TEST") as response:
                    if response.status != 200:
                        image_available = False
            except:
                traceback.print_exc()
                await ctx.respond("Failed to calculate pngleaderboard - cdn error")
                return
        await ctx.respond(
            f"Open in browser for full res (links reset on bot restart, or after some time, request this leaderboard again if that happens)\n{cdn_url}"
        )

        return "bleh"

    @bot.slash_command(
        name="leaderboards", description="Gets leaderboards for a player"
    )
    async def retrieveleaderboard(
        ctx,
        playername: Option(
            str, "Who to get a leaderboard for", autocomplete=autocompletenamesfromdb
        ),
        leaderboard: Option(
            str,
            "Witch leaderboard, omit for all, more specific data when not ommitted",
            choices=list(
                map(
                    lambda x: x["name"],
                    list(
                        filter(
                            lambda x: "name" in x.get("merge", "none"),
                            context["leaderboardchannelmessages"],
                        )
                    ),
                )
            ),
        ) = None,
    ):
        """uses the existing leaderboards in channels.json and finds where the player is, and shows them in it"""
        await ctx.defer()
        threading.Thread(
            target=threadwrap, daemon=True, args=(threadedleaderboard, ctx, playername, leaderboard)
        ).start()
    
    def threadedleaderboard(ctx, playername, leaderboard):
        """Threaded version of leaderboard retrieval"""
        player = resolveplayeruidfromdb(playername, None, True)
        if not player:
            asyncio.run_coroutine_threadsafe(
                ctx.respond(f"{playername} player not found", ephemeral=False),
                bot.loop
            )
            return
            
        if leaderboard is None:
            output = {}
            colour = 0
            for logid in range(len(context["leaderboardchannelmessages"])):
                if "name" in context["leaderboardchannelmessages"][logid].get("merge", ""):
                    result = asyncio.run_coroutine_threadsafe(
                        updateleaderboard(logid, specificuidsearch=str(player[0]["uid"]), compact=True),
                        bot.loop
                    ).result()
                    output[logid] = result
                    if output[logid]:
                        colour = output[logid]["title"]["color"]
        else:
            output = None
            for logid in range(len(context["leaderboardchannelmessages"])):
                if (
                    "name" in context["leaderboardchannelmessages"][logid].get("merge", "")
                    and context["leaderboardchannelmessages"][logid].get("name", "") == leaderboard
                ):
                    output = asyncio.run_coroutine_threadsafe(
                        updateleaderboard(logid, str(player[0]["uid"]), False, 11),
                        bot.loop
                    ).result()
                    
            if not output:
                asyncio.run_coroutine_threadsafe(
                    ctx.respond(
                        f"Leaderboard data not found, or {player[0]['name']} is not in the chosen leaderboard",
                        ephemeral=False
                    ),
                    bot.loop
                )
                return
                
            embed = discord.Embed(
                title=output["title"]["title"],
                color=output["title"]["color"],
                description=output["title"]["description"],
            )
            for field in output["rows"]:
                embed.add_field(
                    name=field["name"], value=field["value"], inline=field["inline"]
                )
            asyncio.run_coroutine_threadsafe(
                ctx.respond(f"leaderboard for **{player[0]['name']}**", embed=embed, ephemeral=False),
                bot.loop
            )
            return
            
        embed = discord.Embed(
            title=f"leaderboards for **{player[0]['name']}**",
            color=colour,
            description="all leaderboards!",
        )
        for entry in output.values():
            if not entry:
                continue
            embed.add_field(
                name=entry["title"]["title"],
                value=entry["rows"][0]["value"],
                inline=False,
            )
        asyncio.run_coroutine_threadsafe(
            ctx.respond(embed=embed, ephemeral=False),
            bot.loop
        )

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
    #     if guild.id != context["categoryinfo"]["activeguild"]:
    #         await ctx.respond("This guild is not the active guild.", ephemeral=False)
    #         return
    #     # if channel exists
    #     if any(server.get("channelid") == channel.id for server in context["servers"].values()):
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
        await asyncio.sleep(120)
        # print("leaderboardchannelmessages",context["leaderboardchannelmessages"])
        if context["overridechannels"]["leaderboardchannel"] == 0:
            return
        print("updating leaderboards")
        for logid in range(len(context["leaderboardchannelmessages"])):
            await asyncio.to_thread(updateleaderboard_threaded, logid)
            await asyncio.sleep(6)
        print("leaderboards updated")

    async def updateleaderboard(
        logid, specificuidsearch=False, compact=False, maxshownoverride=5
    ):
        """updates the leaderboards, also handles people manually requesting a leaderboard"""
        global context
        SEPERATOR = "|"
        now = int(time.time())
        leaderboard_entry = context["leaderboardchannelmessages"][logid].copy()

        leaderboardname = leaderboard_entry.get("name", "Default Leaderboard")
        leaderboarddescription = leaderboard_entry.get("description", "no desc")
        maxshown = leaderboard_entry.get("maxshown", 10)
        leaderboarddcolor = leaderboard_entry.get("color", 0xFF70CB)
        leaderboardid = leaderboard_entry.get("id", 0)
        leaderboardcategorysshown = leaderboard_entry["categorys"]
        if isinstance(leaderboardcategorysshown, list) and GLOBALIP != 0:
            print(f"trying to update pngleaderboard {leaderboardname}")
            try:
                # print("here")
                # individual = leaderboard_entry.get("individual",{})
                # leaderboardcategorysshown = {"CATEGORYS":leaderboardcategorysshown,**individual}
                timestamp = await asyncio.to_thread(
                    getweaponspng,
                    leaderboard_entry.get("displayvictims", False),
                    leaderboardcategorysshown,
                    maxshown,
                    leaderboard_entry.get("columns", False),
                )
                channel = bot.get_channel(
                    context["overridechannels"]["leaderboardchannel"]
                )
                # if leaderboardcategorysshown:
                #     image_name = "_".join(sorted(leaderboardcategorysshown)).upper() + ".png"
                # else:
                #     image_name = "ALL.png"
                cdn_url = f"{GLOBALIP}/cdn/{timestamp}"

                if not timestamp and leaderboardid != 0:
                    old_message = await channel.fetch_message(leaderboardid)
                    await old_message.edit(
                        content="⚠ Could not retrieve leaderboard image. Using last image.",
                        embed=old_message.embeds[0] if old_message.embeds else None,
                    )
                    return
                elif not timestamp:
                    new_message = await channel.send(
                        "Could not calculate leaderboard image for " + leaderboardname
                    )
                    context["leaderboardchannelmessages"][logid]["id"] = new_message.id
                    savecontext()
                    return

                # Check if the image is available before continuing
                image_available = True
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(cdn_url + "TEST") as response:
                            if response.status != 200:
                                image_available = False
                    except:
                        print("FAILED TO CONNECT TO CDN TO SEND LEADERBOARDIMAGE")
                # print("here2")
                embed = discord.Embed(
                    title=leaderboardname,
                    color=leaderboarddcolor,
                    description=f"{leaderboarddescription}\nLast Updated: {getdiscordtimestamp()}",
                )
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
                            await old_message.edit(
                                content="⚠ Could not retrieve leaderboard image. Using last image.",
                                embed=old_message.embeds[0]
                                if old_message.embeds
                                else None,
                            )
                    except discord.NotFound as e:
                        print(
                            "Leaderboard message not found, sending new one.",
                            e,
                            "ID",
                            leaderboardid,
                        )
                        new_message = await channel.send(embed=embed)
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()

                elif not specificuidsearch:
                    # print("here5")
                    if image_available:
                        new_message = await channel.send(embed=embed)
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()
                    else:
                        new_message = await channel.send(
                            "Could not retrieve leaderboard image."
                        )
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()
                return
            except Exception as e:
                traceback.print_exc()
                return

        elif isinstance(leaderboardcategorysshown, list):
            print("skipping cdn leaderboard")
            return
        leaderboarddatabase = leaderboard_entry["database"]
        leaderboardorderby = leaderboard_entry["orderby"]

        leaderboardfilters = leaderboard_entry.get("filters", {})
        leaderboardmerge = leaderboard_entry["merge"]

        indexoverride = leaderboard_entry.get("nameindex", -1)

        nameoverride = False
        serveroverride = False
        tf1nameoverride = False

        if isinstance(leaderboardmerge, str):
            leaderboardmerge = [leaderboardmerge]

        leaderboardmerge = list(leaderboardmerge)
        oldleaderboardmerge = leaderboardmerge.copy()
        # leaderboardmerge = sorted(leaderboardmerge, key = lambda x: x != "name") #jank to make name always come first no longer needed
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "name":
                leaderboardmerge[i] = "playeruid"
                nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "tf1name":
                leaderboardmerge[i] = "playeruid"
                tf1nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "deathname":
                leaderboardmerge[i] = "victim_id"
                nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "server":
                leaderboardmerge[i] = "serverid"
                serveroverride = True

        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb

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
            wherestring = eval(leaderboardfilters).replace('"', "'")
        if not specificuidsearch:
            print("Updating leaderboard:", leaderboardname)

        orderbyiscolumn = leaderboardorderby not in [
            x for x in leaderboardcategorysshown.keys()
        ]

        leaderboardcategorys = list(
            set(
                [
                    *([leaderboardorderby] if orderbyiscolumn else []),
                    *leaderboardmerge,
                    *[
                        col
                        for x in leaderboardcategorysshown.values()
                        for col in x["columnsbound"]
                    ],
                ]
            )
        )
        # print("leaderboardcats",leaderboardcategorys)
        countadd = False
        if "matchcount" in leaderboardcategorys:
            countadd = True
            del leaderboardcategorys[leaderboardcategorys.index("matchcount")]
        # print("leaderboardcategorys",leaderboardcategorys)
        # leaderboardcategorys = sorted(leaderboardcategorys, key=lambda x: list(leaderboardcategorysshown.keys()).index(x) if x in leaderboardcategorysshown else len(leaderboardcategorysshown))
        base_query = (
            f"SELECT {','.join(leaderboardcategorys)} FROM {leaderboarddatabase}"
        )
        # print("wherestring",f"{base_query} WHERE {wherestring}")
        quote = "'"
        query = (
            f"{base_query} WHERE{' (victim_type = ' + quote + 'player' + quote + 'OR victim_type IS NULL)' + 'AND' if leaderboarddatabase == 'specifickilltracker' and not leaderboard_entry.get('allownpcs', False) else ''} {wherestring}"
            if wherestring
            else f"{base_query} {'WHERE (victim_type = ' + quote + 'player' + quote + 'OR victim_type IS NULL)' if (leaderboarddatabase == 'specifickilltracker' and not leaderboard_entry.get('allownpcs', False)) else ''}"
        )
        # print(query)
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
            output.setdefault(
                SEPERATOR.join(list(map(lambda x: str(row[x]), mergeindexes))), []
            ).append(row)
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
                        if isinstance(val, (int, float)) and isinstance(
                            merged[col_name], (int, float)
                        ):
                            merged[col_name] += val
                        elif isinstance(val, str):
                            continue  # Keep the first string
            actualoutput[key] = merged
        # print(actualoutput)
        # print("a",leaderboardcategorysshown)
        # print("b",leaderboardorderby)
        # print("c",leaderboardcategorysshown[leaderboardorderby]["columnsbound"])
        actualoutput = sorted(
            actualoutput.items(),
            key=lambda x: x[1][leaderboardorderby]
            if orderbyiscolumn
            else (
                x[1][leaderboardcategorysshown[leaderboardorderby]["columnsbound"][0]]
                if len(leaderboardcategorysshown[leaderboardorderby]["columnsbound"])
                == 1
                else safe_eval(
                    leaderboardcategorysshown[leaderboardorderby]["calculation"],
                    x[1],
                )
            ),
            reverse=True,
        )

        def swopper(itemname):
            global context
            # print(itemname)
            # print(str(namemap.get(int(itemname), context["serveridnamelinks"].get(str(itemname),itemname))))
            try:
                itemname = int(itemname)
            except:
                return "Some Unknown NPC"
            return str(
                namemap.get(
                    (itemname),
                    context["servers"].get(str(itemname), {}).get("name", itemname),
                )
            )

        displayoutput = []
        nameuidmap = []
        if nameoverride:
            c.execute("SELECT playername, playeruid FROM uidnamelink ORDER BY id")
            namemap = {uid: name for name, uid in c.fetchall()}
            for uid, rowdata in actualoutput:
                uid = uid.split(SEPERATOR)  # horrible jank
                displayname = SEPERATOR.join(list(map(swopper, uid)))
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
                description=f"{leaderboarddescription} **{len(displayoutput)} Entrys**\nLast Updated: {getdiscordtimestamp()}",
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
                displayoutput = displayoutput[playerindex : playerindex + 1]
            else:
                start = playerindex
                n = maxshownoverride
                half = n // 2
                length = len(displayoutput)
                if length <= n:
                    window = displayoutput
                else:
                    start = playerindex - half
                    end = playerindex + half + 1

                    if start < 0:
                        end += -start
                        start = 0

                    if end > length:
                        start -= end - length
                        end = length
                    start = max(0, start)
                    end = min(length, end)

                    window = displayoutput[start:end]
                # print("STARTEND",start,end)
                ioffset = start
                displayoutput = window
                maxshown = n
        fakembed = {"rows": []}
        if not compact:
            fakembed["title"] = {
                "title": f"{leaderboardname}",
                "color": leaderboarddcolor,
                "description": f"{leaderboarddescription} **{(entrycount)} Entrys**",
            }
        else:
            fakembed["title"] = {
                "title": f"{leaderboardname} ***Position: {playerindex + 1}***",
                "color": leaderboarddcolor,
                "description": leaderboarddescription,
            }
        for i, (name, data) in enumerate(displayoutput):
            if i >= maxshown:
                break
            ioffsetted = i + ioffset
            output = {}
            for catname, category in leaderboardcategorysshown.items():
                # print("catname",catname)
                if "calculation" in category.keys():
                    value = eval(category["calculation"], {}, data)
                else:
                    if len(category["columnsbound"]) > 1:
                        output[catname] = (
                            "Cannot bind multiple columns without a calculation function"
                        )
                    value = data[category["columnsbound"][0]]
                value = modifyvalue(
                    value,
                    category.get("format", None),
                    category.get("calculation", None),
                )
                output[catname] = value

            actualoutput = "> \u200b \u200b \u200b " + " ".join(
                [
                    f"{category}: **{value}**"
                    for category, value in list(
                        filter(
                            lambda x: x[0] != oldleaderboardmerge[indexoverride],
                            zip(leaderboardcategorysshown, output.values()),
                        )
                    )
                ]
            )
            # first pull the category names, then send em through the calculator,
            # print(list(leaderboardcategorysshown.keys()), name.split(SEPERATOR)[indexoverride],oldleaderboardmerge[indexoverride])
            # print(list(zip(leaderboardcategorysshown, output.values())))

            if not specificuidsearch:
                embed.add_field(
                    name=f" \u200b {str(ioffsetted + 1)}. ***{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}***",
                    value=f"{actualoutput}",
                    inline=False,
                )
            else:
                fakembed["rows"].append(
                    {
                        "name": f" \u200b {str(ioffsetted + 1)}. **{'*' if playerindex != ioffsetted else ''}{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}{'*' if playerindex != ioffsetted else ''}**",
                        "value": actualoutput,
                        "inline": False,
                    }
                )
        if not data:
            fakembed["rows"].append(
                {
                    "name": "Error",
                    "value": "No data found for this leaderboard",
                    "inline": False,
                }
            )
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
                print(
                    "[38;5;100mLeaderboard message not found, resending a new one",
                    e,
                    "ID",
                    leaderboardid,
                )
                return
                message = await channel.send(embed=embed)
                context["leaderboardchannelmessages"][logid]["id"] = message.id
                savecontext()
        elif not specificuidsearch:
            print(
                "[38;5;100mLeaderboard sobbing message really not found",
                "ID",
                leaderboardid,
            )
            message = await channel.send(embed=embed)
            context["leaderboardchannelmessages"][logid]["id"] = message.id
            savecontext()
        else:
            return fakembed

    def updateleaderboard_threaded(
        logid, specificuidsearch=False, compact=False, maxshownoverride=5
    ):
        """Threaded version of updateleaderboard - runs database and image processing in a thread"""
        global context
        SEPERATOR = "|"
        now = int(time.time())
        leaderboard_entry = context["leaderboardchannelmessages"][logid].copy()

        leaderboardname = leaderboard_entry.get("name", "Default Leaderboard")
        leaderboarddescription = leaderboard_entry.get("description", "no desc")
        maxshown = leaderboard_entry.get("maxshown", 10)
        leaderboarddcolor = leaderboard_entry.get("color", 0xFF70CB)
        leaderboardid = leaderboard_entry.get("id", 0)
        leaderboardcategorysshown = leaderboard_entry["categorys"]

        if isinstance(leaderboardcategorysshown, list) and GLOBALIP != 0:
            try:
                # Run getweaponspng directly (we're already in a thread)
                timestamp = getweaponspng(
                    leaderboard_entry.get("displayvictims", False),
                    leaderboardcategorysshown,
                    maxshown,
                    leaderboard_entry.get("columns", False),
                )
                channel = bot.get_channel(
                    context["overridechannels"]["leaderboardchannel"]
                )
                cdn_url = f"{GLOBALIP}/cdn/{timestamp}"

                if not timestamp and leaderboardid != 0:
                    old_message_future = asyncio.run_coroutine_threadsafe(
                        channel.fetch_message(leaderboardid), bot.loop
                    )
                    old_message = old_message_future.result()
                    edit_future = asyncio.run_coroutine_threadsafe(
                        old_message.edit(
                            content="⚠ Could not retrieve leaderboard image. Using last image.",
                            embed=old_message.embeds[0] if old_message.embeds else None,
                        ),
                        bot.loop,
                    )
                    edit_future.result()
                    return
                elif not timestamp:
                    send_future = asyncio.run_coroutine_threadsafe(
                        channel.send(
                            "Could not calculate leaderboard image for "
                            + leaderboardname
                        ),
                        bot.loop,
                    )
                    new_message = send_future.result()
                    context["leaderboardchannelmessages"][logid]["id"] = new_message.id
                    savecontext()
                    return

                # Check if the image is available using requests instead of aiohttp
                image_available = True
                try:
                    import requests

                    response = requests.get(cdn_url + "TEST", timeout=10)
                    if response.status_code != 200:
                        image_available = False
                except Exception:
                    print("FAILED TO CONNECT TO CDN TO SEND LEADERBOARDIMAGE")
                    image_available = False

                embed = discord.Embed(
                    title=leaderboardname,
                    color=leaderboarddcolor,
                    description=f"{leaderboarddescription}\nLast Updated: {getdiscordtimestamp()}",
                )
                if image_available:
                    embed.set_image(url=cdn_url)

                if leaderboardid != 0 and not specificuidsearch:
                    try:
                        old_message_future = asyncio.run_coroutine_threadsafe(
                            channel.fetch_message(leaderboardid), bot.loop
                        )
                        old_message = old_message_future.result()
                        if image_available:
                            edit_future = asyncio.run_coroutine_threadsafe(
                                old_message.edit(embed=embed, content=None), bot.loop
                            )
                            edit_future.result()
                        else:
                            edit_future = asyncio.run_coroutine_threadsafe(
                                old_message.edit(
                                    content="⚠ Could not retrieve leaderboard image. Using last image.",
                                    embed=old_message.embeds[0]
                                    if old_message.embeds
                                    else None,
                                ),
                                bot.loop,
                            )
                            edit_future.result()
                    except discord.NotFound as e:
                        print(
                            "Leaderboard message not found, sending new one.",
                            e,
                            "ID",
                            leaderboardid,
                        )
                        send_future = asyncio.run_coroutine_threadsafe(
                            channel.send(embed=embed), bot.loop
                        )
                        new_message = send_future.result()
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()

                elif not specificuidsearch:
                    if image_available:
                        send_future = asyncio.run_coroutine_threadsafe(
                            channel.send(embed=embed), bot.loop
                        )
                        new_message = send_future.result()
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()
                    else:
                        send_future = asyncio.run_coroutine_threadsafe(
                            channel.send("Could not retrieve leaderboard image."),
                            bot.loop,
                        )
                        new_message = send_future.result()
                        context["leaderboardchannelmessages"][logid]["id"] = (
                            new_message.id
                        )
                        savecontext()
                return
            except Exception as e:
                traceback.print_exc()
                return

        elif isinstance(leaderboardcategorysshown, list):
            print("skipping cdn leaderboard")
            return

        # Rest of the function (database operations) remains the same
        leaderboarddatabase = leaderboard_entry["database"]
        leaderboardorderby = leaderboard_entry["orderby"]
        leaderboardfilters = leaderboard_entry.get("filters", {})
        leaderboardmerge = leaderboard_entry["merge"]
        indexoverride = leaderboard_entry.get("nameindex", -1)

        nameoverride = False
        serveroverride = False
        tf1nameoverride = False

        if isinstance(leaderboardmerge, str):
            leaderboardmerge = [leaderboardmerge]

        leaderboardmerge = list(leaderboardmerge)
        oldleaderboardmerge = leaderboardmerge.copy()

        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "name":
                leaderboardmerge[i] = "playeruid"
                nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "tf1name":
                leaderboardmerge[i] = "playeruid"
                tf1nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "deathname":
                leaderboardmerge[i] = "victim_id"
                nameoverride = True
        for i, value in enumerate(leaderboardmerge):
            if leaderboardmerge[i] == "server":
                leaderboardmerge[i] = "serverid"
                serveroverride = True

        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb

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
            wherestring = eval(leaderboardfilters).replace('"', "'")
        if not specificuidsearch:
            print("Updating leaderboard:", leaderboardname)

        orderbyiscolumn = leaderboardorderby not in [
            x for x in leaderboardcategorysshown.keys()
        ]

        leaderboardcategorys = list(
            set(
                [
                    *([leaderboardorderby] if orderbyiscolumn else []),
                    *leaderboardmerge,
                    *[
                        col
                        for x in leaderboardcategorysshown.values()
                        for col in x["columnsbound"]
                    ],
                ]
            )
        )

        countadd = False
        if "matchcount" in leaderboardcategorys:
            countadd = True
            del leaderboardcategorys[leaderboardcategorys.index("matchcount")]

        base_query = (
            f"SELECT {','.join(leaderboardcategorys)} FROM {leaderboarddatabase}"
        )
        quote = "'"
        query = (
            f"{base_query} WHERE{' (victim_type = ' + quote + 'player' + quote + 'OR victim_type IS NULL)' + 'AND' if leaderboarddatabase == 'specifickilltracker' and not leaderboard_entry.get('allownpcs', False) else ''} {wherestring}"
            if wherestring
            else f"{base_query} {'WHERE (victim_type = ' + quote + 'player' + quote + 'OR victim_type IS NULL)' if (leaderboarddatabase == 'specifickilltracker' and not leaderboard_entry.get('allownpcs', False)) else ''}"
        )

        c.execute(query, params)
        data = c.fetchall()

        if not data:
            pass

        # add times appeared columns
        if countadd:
            leaderboardcategorys.append("matchcount")

        # Group rows by the merge key
        output = {}
        mergeindexes = []
        for i in leaderboardmerge:
            mergeindexes.append(leaderboardcategorys.index(i))

        output = {}
        for row in data:
            output.setdefault(
                SEPERATOR.join(list(map(lambda x: str(row[x]), mergeindexes))), []
            ).append(row)

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
                        if isinstance(val, (int, float)) and isinstance(
                            merged[col_name], (int, float)
                        ):
                            merged[col_name] += val
                        elif isinstance(val, str):
                            continue  # Keep the first string
            actualoutput[key] = merged

        actualoutput = sorted(
            actualoutput.items(),
            key=lambda x: x[1][leaderboardorderby]
            if orderbyiscolumn
            else (
                x[1][leaderboardcategorysshown[leaderboardorderby]["columnsbound"][0]]
                if len(leaderboardcategorysshown[leaderboardorderby]["columnsbound"])
                == 1
                else safe_eval(
                    leaderboardcategorysshown[leaderboardorderby]["calculation"],
                    x[1],
                )
            ),
            reverse=True,
        )

        def swopper(itemname):
            global context
            try:
                itemname = int(itemname)
            except:
                return "Some Unknown NPC"
            return str(
                namemap.get(
                    (itemname),
                    context["servers"].get(str(itemname), {}).get("name", itemname),
                )
            )

        displayoutput = []
        nameuidmap = []
        if nameoverride:
            c.execute("SELECT playername, playeruid FROM uidnamelink ORDER BY id")
            namemap = {uid: name for name, uid in c.fetchall()}
            for uid, rowdata in actualoutput:
                uid = uid.split(SEPERATOR)
                displayname = SEPERATOR.join(list(map(swopper, uid)))
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
                description=f"{leaderboarddescription} **{len(displayoutput)} Entrys**\nLast Updated: {getdiscordtimestamp()}",
            )

        ioffset = 0
        entrycount = len(displayoutput)
        if specificuidsearch:
            if specificuidsearch not in nameuidmap:
                return False
            playerindex = nameuidmap.index(specificuidsearch)
            if compact:
                ioffset = playerindex
                displayoutput = displayoutput[playerindex : playerindex + 1]
            else:
                start = playerindex
                n = maxshownoverride
                half = n // 2
                length = len(displayoutput)
                if length <= n:
                    window = displayoutput
                else:
                    start = playerindex - half
                    end = playerindex + half + 1

                    if start < 0:
                        end += -start
                        start = 0

                    if end > length:
                        start -= end - length
                        end = length
                    start = max(0, start)
                    end = min(length, end)

                    window = displayoutput[start:end]
                ioffset = start
                displayoutput = window
                maxshown = n

        fakembed = {"rows": []}
        if not compact:
            fakembed["title"] = {
                "title": f"{leaderboardname}",
                "color": leaderboarddcolor,
                "description": f"{leaderboarddescription} **{(entrycount)} Entrys**",
            }
        else:
            fakembed["title"] = {
                "title": f"{leaderboardname} ***Position: {playerindex + 1}***",
                "color": leaderboarddcolor,
                "description": leaderboarddescription,
            }
        for i, (name, data) in enumerate(displayoutput):
            if i >= maxshown:
                break
            ioffsetted = i + ioffset
            output = {}
            for catname, category in leaderboardcategorysshown.items():
                if "calculation" in category.keys():
                    value = eval(category["calculation"], {}, data)
                else:
                    if len(category["columnsbound"]) > 1:
                        output[catname] = (
                            "Cannot bind multiple columns without a calculation function"
                        )
                    value = data[category["columnsbound"][0]]
                value = modifyvalue(
                    value,
                    category.get("format", None),
                    category.get("calculation", None),
                )
                output[catname] = value

            actualoutput = "> \u200b \u200b \u200b " + " ".join(
                [
                    f"{category}: **{value}**"
                    for category, value in list(
                        filter(
                            lambda x: x[0] != oldleaderboardmerge[indexoverride],
                            zip(leaderboardcategorysshown, output.values()),
                        )
                    )
                ]
            )

            if not specificuidsearch:
                embed.add_field(
                    name=f" \u200b {str(ioffsetted + 1)}. ***{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}***",
                    value=f"{actualoutput}",
                    inline=False,
                )
            else:
                fakembed["rows"].append(
                    {
                        "name": f" \u200b {str(ioffsetted + 1)}. **{'*' if playerindex != ioffsetted else ''}{name.split(SEPERATOR)[indexoverride] if oldleaderboardmerge[indexoverride] not in leaderboardcategorysshown.keys() else list(output.values())[list(leaderboardcategorysshown.keys()).index(oldleaderboardmerge[indexoverride])]}{'*' if playerindex != ioffsetted else ''}**",
                        "value": actualoutput,
                        "inline": False,
                    }
                )
        if not data:
            fakembed["rows"].append(
                {
                    "name": "Error",
                    "value": "No data found for this leaderboard",
                    "inline": False,
                }
            )
            if not specificuidsearch:
                embed.add_field(
                    name="Error",
                    value="No data found for this leaderboard",
                    inline=False,
                )

        # Update or send leaderboard message using asyncio.run_coroutine_threadsafe
        channel = bot.get_channel(context["overridechannels"]["leaderboardchannel"])

        if leaderboardid != 0 and not specificuidsearch:
            try:
                message_future = asyncio.run_coroutine_threadsafe(
                    channel.fetch_message(leaderboardid), bot.loop
                )
                message = message_future.result()
                edit_future = asyncio.run_coroutine_threadsafe(
                    message.edit(embed=embed), bot.loop
                )
                edit_future.result()
            except discord.NotFound as e:
                print(
                    "[38;5;100mLeaderboard message not found, resending a new one",
                    e,
                    "ID",
                    leaderboardid,
                )
                return
        elif not specificuidsearch:
            print(
                "[38;5;100mLeaderboard sobbing message really not found",
                "ID",
                leaderboardid,
            )
            send_future = asyncio.run_coroutine_threadsafe(
                channel.send(embed=embed), bot.loop
            )
            message = send_future.result()
            context["leaderboardchannelmessages"][logid]["id"] = message.id
            savecontext()
        else:
            return fakembed

    def sqrt_ceil(n):
        if n < 0:
            raise ValueError("Cannot take the square root of a negative number.")
        x = n
        y = (x + 1) / 2
        while abs(x - y) > 0.00001:
            x = y
            y = (x + n / x) / 2
        int_part = int(y)
        if y > int_part:
            return int_part + 1
        else:
            return int_part

    def getweaponspng(
        swoptovictims=False,
        specificweapon=False,
        max_players=10,
        COLUMNS=False,
        widthoverride=300,
        playeroverride=False,
        canonlybenpcs=False,
        istf1 = False
    ):
        """calculates all the pngleaderboards"""
        global imagescdn
        # print("getting pngleaderboard")
        now = int(time.time() * 100)
        FONT_PATH = "./fonts/DejaVuSans-Bold.ttf"

        if not os.path.isfile(FONT_PATH):
            print(f"Font not found at {FONT_PATH}")
        FONT_SIZE = 16
        LINE_SPACING = 10
        GOLD = (255, 215, 0)
        SILVER = (192, 192, 192)
        BRONZE = (205, 127, 50)
        CURRENT = (255, 0, 255)
        DEFAULT_COLOR = (255, 255, 255)
        IMAGE_DIR = "./gunimages"
        IMAGE_DIR_TF1 = "./gunimagestf1"
        CDN_DIR = "./data/cdn"
        if specificweapon:
            specificweapon = specificweapon.copy()
        timecutoffs = {"main": 0, "cutoff": 86400 * 7}
        if not specificweapon:
            specificweapon = []
        # if "GUNS" in specificweapon:
        #     del specificweapon[specificweapon.index("GUNS")]
        #     specificweapon.extend(GUNS)
        # if "ABILITYS" in specificweapon:
        #     del specificweapon[specificweapon.index("ABILITYS")]
        #     specificweapon.extend(ABILITYS)
        if "GRENADES" in specificweapon:
            del specificweapon[specificweapon.index("GRENADES")]
            specificweapon.extend(GRENADES)
        if "DEATH_BY_MAP" in specificweapon:
            del specificweapon[specificweapon.index("DEATH_BY_MAP")]
            specificweapon.extend(DEATH_BY_MAP)
        if "MISC_MISC" in specificweapon:
            del specificweapon[specificweapon.index("MISC_MISC")]
            specificweapon.extend(MISC_MISC)
        if "MISC_TITAN" in specificweapon:
            del specificweapon[specificweapon.index("MISC_TITAN")]
            specificweapon.extend(MISC_TITAN)
        if "MISC_PILOT" in specificweapon:
            del specificweapon[specificweapon.index("MISC_PILOT")]
            specificweapon.extend(MISC_PILOT)
        if "CORES" in specificweapon:
            del specificweapon[specificweapon.index("CORES")]
            specificweapon.extend(CORES)
        if "GUNS_TITAN" in specificweapon:
            del specificweapon[specificweapon.index("GUNS_TITAN")]
            specificweapon.extend(GUNS_TITAN)
        if "GUNS_PILOT" in specificweapon:
            del specificweapon[specificweapon.index("GUNS_PILOT")]
            specificweapon.extend(GUNS_PILOT)
        if "ABILITYS_TITAN" in specificweapon:
            del specificweapon[specificweapon.index("ABILITYS_TITAN")]
            specificweapon.extend(ABILITYS_TITAN)
        if "ABILITYS_PILOT" in specificweapon:
            del specificweapon[specificweapon.index("ABILITYS_PILOT")]
            specificweapon.extend(ABILITYS_PILOT)

        # if specificweapon.get("CATEGORYS",False):
        #     del specificweapon["CATEGORYS"]
        # os.makedirs(CDN_DIR, exist_ok=True)
        # print(specificweapon)
        if not specificweapon:
            # weapon_images = [f for f in os.listdir(IMAGE_DIR) if (f.startswith("mp_") or f.startswith("melee_")) and f.endswith(".png")]
            tfdb = postgresem("./data/tf2helper.db")
            c = tfdb
            c.execute(
                f"SELECT DISTINCT cause_of_death FROM specifickilltracker{'tf1' if istf1 else ''} ORDER BY cause_of_death"
            )
            output = c.fetchall()
            # print(json.dumps({x["weapon_name"]:x["png_name"] for x in [*ABILITYS_PILOT, *GRENADES, *DEATH_BY_MAP, *MISC_MISC, *MISC_TITAN, *MISC_PILOT, *CORES, *GUNS_TITAN, *GUNS_PILOT, *ABILITYS_TITAN]},indent=4))
            weapon_images = list(
                map(
                    lambda x: {
                        x["weapon_name"]: x["png_name"]
                        for x in [
                            *ABILITYS_PILOT,
                            *GRENADES,
                            *DEATH_BY_MAP,
                            *MISC_MISC,
                            *MISC_TITAN,
                            *MISC_PILOT,
                            *CORES,
                            *GUNS_TITAN,
                            *GUNS_PILOT,
                            *ABILITYS_TITAN,
                        ]
                    }.get(x[0], x[0])
                    + ".png",
                    output,
                )
            )
            # print("\n".join(weapon_images))
            originalweaponnames = dict(
                zip(
                    [os.path.splitext(f)[0] for f in weapon_images],
                    list(map(lambda x: x[0], output)),
                )
            )
            tfdb.close()

        else:
            weapon_images = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")]
        weapon_names = [os.path.splitext(f)[0] for f in weapon_images]

        # print("\n".join(weapon_names))

        if specificweapon:
            weapon_names = [
                w
                for w in list(
                    set(
                        [
                            *weapon_names,
                            *list(map(lambda x: x["weapon_name"], specificweapon)),
                        ]
                    )
                )
                if w in list(map(lambda x: x["png_name"], specificweapon)) or True
            ]  # if no image, who cares! (might break stuff)
            originalweaponnames = dict(zip(weapon_names, weapon_names))
            if not weapon_names:
                pass
                print("No matching weapon images found for the given list.")
                return None
        # print("specificweapon",specificweapon)
        # print("weapon_names2",weapon_names)

        def fetch_kill_data(timecutoff=0):
            timecutoff = int(time.time() - timecutoff)
            tfdb = postgresem("./data/tf2helper.db")
            c = tfdb
            c.execute(
                f"SELECT cause_of_death ,playeruid,weapon_mods FROM specifickilltracker{'tf1' if istf1 else ''} WHERE timeofkill < ? AND (victim_type = 'player' OR victim_type IS NULL)",
                (timecutoff,),
            )
            rows = c.fetchall()
            tfdb.close()
            return rows

        def bvsuggestedthistome(timecutoff=0, swoptovictims=False):
            timecutoff = int(time.time() - timecutoff)
            tfdb = postgresem("./data/tf2helper.db")
            c = tfdb
            if not swoptovictims:
                c.execute(
                    f"SELECT cause_of_death, playeruid, weapon_mods, COUNT(*) as amount, attacker_type FROM specifickilltracker{'tf1' if istf1 else ''} WHERE timeofkill < ? AND (victim_type = 'player' OR victim_type IS NULL) GROUP BY cause_of_death, playeruid, weapon_mods, attacker_type",
                    (timecutoff,),
                )
            else:
                c.execute(
                    f"SELECT cause_of_death, victim_id, weapon_mods, COUNT(*) as amount, attacker_type FROM specifickilltracker{'tf1' if istf1 else ''} WHERE timeofkill < ? AND (victim_type = 'player' OR victim_type IS NULL) GROUP BY cause_of_death, victim_id, weapon_mods, attacker_type",
                    (timecutoff,),
                )

            rows = c.fetchall()
            tfdb.close()
            return rows

        # print("calculated pngleaderboard in", (int(time.time()*100)-now)/100,"seconds")
        # print(specificweapon)
        if specificweapon:
            specificweaponsallowed = list(
                map(lambda x: x["weapon_name"], specificweapon)
            )
            specificweaponsallowedex = list(
                map(lambda x: x.get("boundgun"), specificweapon)
            )
            weapon_kills = {"main": {}, "cutoff": {}}
            for name, cutoff in timecutoffs.items():
                stabsofweapons = bvsuggestedthistome(cutoff, swoptovictims)
                for weapon, killer, mods, stabcount, whomurdered in stabsofweapons:
                    if weapon not in specificweaponsallowed:
                        continue
                    index = specificweaponsallowed.index(weapon)
                    modswanted = specificweapon[index].get("mods", [])
                    modsused = mods.split(" ")
                    if modsused == [""]:
                        modsused = []
                    modsfiltertype = specificweapon[index].get("modswanted", "include")
                    mustbekilledby = specificweapon[index].get("killedby", [])
                    # print(specificweapon[index])
                    # if (
                    #     mustbekilledby
                    #     and whomurdered
                    #     and whomurdered not in mustbekilledby   ###DISABLED ANYONE CAN BE IN THE LEADERBOARDS, EVEN REAPERS :D
                    # ):
                    #     continue
                    if (
                        not (
                            modsfiltertype == "include"
                            and (
                                not modswanted
                                or list(filter(lambda x: x in modsused, modswanted))
                            )
                        )
                        and not (
                            modsfiltertype == "anyof"
                            and len(set([*modswanted, *modsused]))
                            < len([*modswanted, *modsused])
                        )
                        and not (
                            modsfiltertype == "exclude"
                            and len(set([*modswanted, *modsused]))
                            == len([*modswanted, *modsused])
                        )
                        and not (
                            modsfiltertype == "exact"
                            and str(sorted(modswanted)) == str(sorted(modsused))
                        )
                    ):
                        continue
                    if not killer:
                        killer = whomurdered
                    elif canonlybenpcs:
                        continue
                    weapon_kills[name].setdefault(specificweapon[index]["png_name"], {})
                    weapon_kills[name][specificweapon[index]["png_name"]].setdefault(
                        killer, 0
                    )
                    weapon_kills[name][specificweapon[index]["png_name"]][killer] += (
                        stabcount
                    )

                # for weapon, killer, mods, stabcount, whomurdered in stabsofweapons:
                #     if weapon not in specificweaponsallowedex:
                #         continue
                #     index = specificweaponsallowedex.index(weapon)
                #     modswanted = specificweapon[index].get("mods", [])
                #     modsused = mods.split(" ")
                #     if modsused == [""]:
                #         modsused = []
                #     modsfiltertype = specificweapon[index].get("modswanted", "include")
                #     mustbekilledby = specificweapon[index].get("killedby", [])
                #     # print(specificweapon[index])
                #     if (
                #         mustbekilledby
                #         and whomurdered
                #         and whomurdered not in mustbekilledby
                #     ):
                #         continue
                #     if (
                #         not (
                #             modsfiltertype == "include"
                #             and (
                #                 not modswanted
                #                 or list(filter(lambda x: x in modsused, modswanted))
                #             )
                #         )
                #         and not (
                #             modsfiltertype == "anyof"
                #             and len(set([*modswanted, *modsused]))
                #             < len([*modswanted, *modsused])
                #         )
                #         and not (
                #             modsfiltertype == "exclude"
                #             and len(set([*modswanted, *modsused]))
                #             == len([*modswanted, *modsused])
                #         )
                #         and not (
                #             modsfiltertype == "exact"
                #             and str(sorted(modswanted)) == str(sorted(modsused))
                #         )
                #     ):
                #         continue
                #     if not killer:
                #         killer = whomurdered
                #     elif canonlybenpcs:
                #         continue
                #     weapon_kills[name].setdefault(specificweapon[index]["png_name"], {})
                #     weapon_kills[name][specificweapon[index]["png_name"]].setdefault(
                #         killer, 0
                #     )
                #     weapon_kills[name][specificweapon[index]["png_name"]][killer] += (
                #         stabcount
                #     )
        else:
            weapon_kills = {"main": {}, "cutoff": {}}
            for name, cutoff in timecutoffs.items():
                for weapon, killer, mods, stabcount, whomurdered in bvsuggestedthistome(
                    cutoff, swoptovictims
                ):
                    if not killer:
                        killer = whomurdered
                    elif canonlybenpcs:
                        continue
                    weapon_kills[name].setdefault(f"{weapon}", {})
                    weapon_kills[name][f"{weapon}"].setdefault(killer, 0)
                    weapon_kills[name][f"{weapon}"][killer] += stabcount

        # weapon_kills = {"main":{},"cutoff":{}}
        # for name,cutoff in timecutoffs.items():
        #     kill_data = fetch_kill_data(cutoff)

        #     for weapon, attacker, mods in kill_data:
        #         weaponwithmods = " ".join([weapon,mods])
        #         if weapon in list(map(lambda x: x["weapon_name"],specificweapon)):
        #             index = list(map(lambda x: x["weapon_name"],specificweapon)).index(weapon)
        #             # include, the mods in the kill data MUST include the mod in the def (default)
        #             # exact, the mods in the kill data MUST equal the mods in the def
        #             # exclude, there must be no common mods bettween mod list and def
        #             modswanted = (specificweapon[index].get("mods",[]))
        #             modsused = (mods.split(" "))
        #             if modsused == ['']:
        #                 modsused = []
        #             modsfiltertype = specificweapon[index].get("modswanted","include")
        #             modsmatch = False
        #             # modsfiltertype = "exact"
        #             # print(modsfiltertype,modswanted,modsused, not modswanted,modsfiltertype == "include")
        #             if not (modsfiltertype == "include" and (not modswanted or list(filter(lambda x: x in modsused,modswanted)))) and not (modsfiltertype == "anyof" and len(set([*modswanted,*modsused])) < len([*modswanted,*modsused])) and not (modsfiltertype == "exclude" and len(set([*modswanted,*modsused])) == len([*modswanted,*modsused])) and not (modsfiltertype == "exact" and str(sorted(modswanted)) == str(sorted(modsused))):
        #                 # print("continuing")
        #                 continue

        #             # print(list(map(lambda x: x["weapon_name"],specificweapon)).index(weapon))
        #             # print(specificweapon[specificweapon[list(map(lambda x: x["weapon_name"],specificweapon)).index(weapon)])
        #             weapon_kills[name].setdefault(specificweapon[index]["png_name"],[]).append(attacker)

        # def max_kill_count(attacker_list):
        #     counts = {}
        #     for attacker in attacker_list:
        #         counts[attacker] = counts.get(attacker, 0) + 1
        #     return max(counts.values(), default=0)

        # # if not specificweapon:
        # weapon_names.sort(key=lambda w: max_kill_count(weapon_kills["main"].get(w, [])), reverse=True)
        # weapon_names = list(filter(lambda w: weapon_kills["main"].get(w, False) != False, weapon_names))
        # print("weapon_names1",weapon_names)

        # print("these guns",weapon_kills["main"]["mp_weapon_lstar"])
        # print("these pew pews",originalweaponnames)
        # print("ovveride",playeroverride)
        # print("eeeee",weapon_kills["main"][originalweaponnames["mp_weapon_lstar"]][1012640166434])
        # print("www",originalweaponnames["mp_weapon_lstar"])
        # print("wqdqwdq",weapon_names)
        # if not specificweapon:
        if not playeroverride:
            weapon_names = list(
                filter(
                    lambda w: weapon_kills["main"].get(w, False) != False, weapon_names
                )
            )
            weapon_names.sort(
                key=lambda w: max([0, *list(weapon_kills["main"].get(w, {}).values())]),
                reverse=True,
            )

        else:
            # print(playeroverride,list(filter(lambda w: weapon_kills["main"].get(w, {}).get(playeroverride,0) ,weapon_names)))
            # print(weapon_kills["main"]
            # print([playeroverride])
            weapon_names = list(
                filter(
                    lambda w: weapon_kills["main"]
                    .get(originalweaponnames[w], {})
                    .get(playeroverride, 0),
                    weapon_names,
                )
            )
            weapon_names.sort(
                key=lambda w: weapon_kills["main"]
                .get(originalweaponnames[w], {})
                .get(playeroverride, 0),
                reverse=True,
            )
        # print(weapon_names)

        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except (OSError, IOError):
            font = ImageFont.load_default()
        # print("bleh",weapon_names)
        panels = []
        images = {}
        maxheight = 0
        maxwidth = widthoverride
        # print("weapon_names",weapon_names)
        if not COLUMNS:
            COLUMNS = sqrt_ceil(len(weapon_names))
        for weapon in weapon_names:
            try:
                if istf1:
                    tf1_path = os.path.join(IMAGE_DIR_TF1, weapon + ".png")
                    if os.path.exists(tf1_path):
                        img_path = tf1_path
                    else:
                        img_path = os.path.join(IMAGE_DIR, weapon + ".png")
                else:
                    img_path = os.path.join(IMAGE_DIR, weapon + ".png")
                gun_img = Image.open(img_path)
                if gun_img.width > maxwidth:
                    aspect_ratio = gun_img.height / gun_img.width
                    new_height = int(maxwidth * aspect_ratio)
                    gun_img = gun_img.resize((maxwidth, new_height), Image.Resampling.LANCZOS)
            except FileNotFoundError:
                gun_img = Image.new("RGBA", (maxwidth, 128), color=(0, 0, 0, 200))
                draw = ImageDraw.Draw(gun_img)

                text = weapon
                font_path = FONT_PATH  # Replace or leave as None to use default

                font = get_max_font_size(draw, text, maxwidth, 128, font_path)

                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                x = (maxwidth - text_width) // 2
                y = (128 - text_height) // 2

                draw.text((x, y), text, fill=(255, 100, 100, 255), font=font)

            images[weapon] = gun_img
            if gun_img.height > maxheight:
                maxheight = gun_img.height
        for weapon in weapon_names:
            weaponalter = weapon
            if not specificweapon:
                weaponalter = originalweaponnames[weapon]

            counts = {}
            if weaponalter in weapon_kills["main"]:
                for attacker, murdercount in weapon_kills["main"][weaponalter].items():
                    counts.setdefault(
                        attacker, {"kills": murdercount, "killscutoff": 0}
                    )

            if weaponalter in weapon_kills["cutoff"]:
                for attacker, murdercount in weapon_kills["cutoff"][
                    weaponalter
                ].items():
                    counts[attacker]["killscutoff"] = murdercount
            if len(counts) == 0:
                continue

            # counts = {}
            # if weapon in weapon_kills["main"]:
            #     for attacker in weapon_kills["main"][weapon]:
            #         counts.setdefault(attacker,{"kills":0,"killscutoff":0})
            #         counts[attacker]["kills"] = counts[attacker]["kills"] + 1
            # if weapon in weapon_kills["cutoff"]:
            #     for attacker in weapon_kills["cutoff"][weapon]:
            #         counts[attacker]["killscutoff"] = counts[attacker]["killscutoff"] + 1
            # if len(counts) == 0:
            #     continue
            playerinleaderboard = True
            if not playeroverride:
                sorted_players = sorted(
                    counts.items(), key=lambda item: item[1]["kills"], reverse=True
                )[:max_players]
                startindex = 0
                notsubtractedhalf = -1
                sorted_player_index = -1
            else:
                sorted_players = sorted(
                    counts.items(), key=lambda item: item[1]["kills"], reverse=True
                )
                sorted_player_index = functools.reduce(
                    lambda a, b: (a[0] + 1, a[1])
                    if not a[1] and b[0] != playeroverride
                    else (a[0], True),
                    sorted_players,
                    (0, False),
                )
                # print("SORQWDIQWD",sorted_player_index)
                if not sorted_player_index[1]:
                    sorted_player_index = 0
                    playerinleaderboard = False
                else:
                    sorted_player_index = sorted_player_index[0]
                half = max_players // 2
                # print("SORTED INDFEX",sorted_player_index)
                notsubtractedhalf = sorted_player_index
                start = max(0, sorted_player_index - half)
                sorted_player_index = start
                end = start + max_players
                if end > len(sorted_players):
                    end = len(sorted_players)
                    start = max(0, end - max_players)
                sorted_players = sorted_players[start:end]
                startindex = start
            sorted_players_cutoff = sorted(
                counts.items(), key=lambda item: item[1]["killscutoff"], reverse=True
            )

            sorted_players_cutoff = [item[0] for (item) in sorted_players_cutoff]
            num_display = len(sorted_players)
            if playerinleaderboard:
                text_area_height = (FONT_SIZE + LINE_SPACING) * num_display + 10
            else:
                text_area_height = (FONT_SIZE + LINE_SPACING) * 2 + 10

            panel_height = maxheight + text_area_height

            panel = Image.new(
                "RGBA",
                (maxwidth, panel_height),
                (
                    random.randint(0, 50),
                    random.randint(0, 50),
                    random.randint(0, 50),
                    200,
                ),
            )
            draw = ImageDraw.Draw(panel)
            gun_img = images[weapon]
            center_x = (maxwidth - gun_img.width) // 2
            panel.paste(gun_img, (center_x, 0), gun_img)

            # Stretch leftmost column to the left
            if center_x > 0:
                left_column = gun_img.crop((0, 0, 1, gun_img.height))
                left_color = left_column.resize((center_x, gun_img.height))
                panel.paste(left_color, (0, 0), left_color)

            # Stretch rightmost column to the right
            right_fill_width = maxwidth - center_x - gun_img.width
            if right_fill_width > 0:
                right_column = gun_img.crop(
                    (gun_img.width - 1, 0, gun_img.width, gun_img.height)
                )
                right_color = right_column.resize((right_fill_width, gun_img.height))
                panel.paste(right_color, (center_x + gun_img.width, 0), right_color)
            if playerinleaderboard:
                for i, (attacker, data) in enumerate(sorted_players):
                    count = data["kills"]
                    oldkills = data["killscutoff"]
                    resolved = resolveplayeruidfromdb(attacker, "uid", True, istf1)
                    if not playeroverride:
                        name = (
                            resolved[0]["name"] if attacker and resolved else NPC_NAMES.get(attacker,attacker)
                        )
                    else:
                        name = f"{i + 1 + sorted_player_index}) {resolved[0]['name'] if attacker and resolved else NPC_NAMES.get(attacker,attacker)}"
                    delta_kills = count - oldkills
                    previous_index = sorted_players_cutoff.index(attacker)
                    delta = previous_index - i
                    if delta > 0:
                        change_text = f"↑ {delta}"
                        change_color = (0, 200, 0)
                    elif delta < 0:
                        change_text = f"↓ {abs(delta)}"
                        change_color = (200, 0, 0)
                    else:
                        change_text = "–"
                        change_color = (128, 128, 128)
                    # print(i+startindex,sorted_player_index)
                    color = (
                        CURRENT
                        if i + startindex == notsubtractedhalf
                        else GOLD
                        if i + startindex == 0
                        else SILVER
                        if i + startindex == 1
                        else BRONZE
                        if i + startindex == 2
                        else DEFAULT_COLOR
                    )

                    y = maxheight + i * (FONT_SIZE + LINE_SPACING) + 5
                    x = 5
                    base_text = f"{name}: {count}"
                    draw.text((x, y), base_text, font=font, fill=color)
                    x += draw.textlength(base_text, font=font)
                    if delta_kills:
                        plus_text = f" +{delta_kills}"
                        draw.text((x, y), plus_text, font=font, fill=(100, 100, 100))
                    arrow_x = maxwidth - draw.textlength(change_text, font=font) - 10
                    draw.text((arrow_x, y), change_text, font=font, fill=change_color)
            else:
                x = 5
                y = maxheight + 5
                draw.text(
                    (x, y),
                    f"No playerdata found for {resolveplayeruidfromdb(playeroverride, 'uid', True, istf1)[0]['name']}",
                    font=font,
                    fill=(255, 100, 100),
                )
                draw.text(
                    (x, y + (FONT_SIZE + LINE_SPACING)),
                    f"they have never used {WEAPON_NAMES.get(weaponalter, weaponalter)}",
                    font=font,
                    fill=(255, 100, 100),
                )

            panels.append(panel)

        if not panels:
            print("No panels to render.")
            return None

        maxwidth = max(panel.width for panel in panels)
        final_columns = min(COLUMNS, len(panels))
        rows = (len(panels) + final_columns - 1) // final_columns

        row_heights = []
        for row in range(rows):
            row_panels = panels[row * final_columns : (row + 1) * final_columns]
            row_heights.append(max(p.height for p in row_panels))

        canvas_width = final_columns * maxwidth
        canvas_height = sum(row_heights)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        y_offset = 0
        for row in range(rows):
            row_panels = panels[row * final_columns : (row + 1) * final_columns]
            for col, panel in enumerate(row_panels):
                x = col * maxwidth
                canvas.paste(panel, (x, y_offset))
            y_offset += row_heights[row]

        if specificweapon:
            base_name = "_".join(sorted(weapon_names)).upper()
        else:
            base_name = "ALL"
        # pngcounter = (pngcounter + 1) % 9
        # file_path = os.path.join(CDN_DIR, str(pngcounter) + base_name +".png")
        imagetimestamp = int(time.time() * 100)
        img_bytes = BytesIO()
        canvas.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        imagescdn[imagetimestamp] = img_bytes
        print(
            "calculated pngleaderboard in",
            (int(time.time() * 100) - now) / 100,
            "seconds",
        )
        return imagetimestamp
        # canvas.save(file_path, format="PNG")

    def get_max_font_size(draw, text, max_width, max_height, font_path=None):
        # font_size = 1
        # best_font = None

        # while True:
        #     try:
        #         font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
        #     except Exception as e:
        #         print(f"Failed to load font from {font_path}: {e}")
        #         return ImageFont.load_default()

        #     bbox = draw.textbbox((0, 0), text, font=font)
        #     width = bbox[2] - bbox[0]
        #     height = bbox[3] - bbox[1]

        #     if width > max_width or height > max_height:
        #         break  # current font is too big; return previous one

        #     best_font = font
        #     font_size += 1
        return (
            ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
        )
        return best_font if best_font else ImageFont.load_default()

    def modifyvalue(value, format, calculation=None):
        """takes in a value, and makes it prettier, I should add a way to display dates to ti"""
        if format is None or not value:
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
                return f"{value * 3600:.2f}{calculation.split('/')[0].strip()[0].lower()}/{calculation.split('/')[1].strip()[0].lower()}"
        elif format == "server":
            return str(context["servers"].get(str(value), {}).get("name", value))
        elif format == "hammertometres":
            if value == 0:
                return "0"
            else:
                return f"{value / 52.5:.2f}m"
        elif format == "gun":
            # print("gun",value,list(WEAPON_NAMES.keys())[0])
            return str(WEAPON_NAMES.get(value, value))
        elif format == "XperY":
            if value == 0:
                return "0"
            else:
                return f"{value:.2f}{calculation.split('/')[0].strip()[0].lower()}/{calculation.split('/')[1].strip()[0].lower()}"
        elif format == "map":
            return str(
                MAP_NAME_TABLE.get(value, str(MAP_NAME_TABLE.get("mp_" + value, value)))
            )
        elif format == "date":
            return datetime.fromtimestamp(value).strftime(
                f"%-d{'th' if 11 <= datetime.fromtimestamp(value).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(value).day % 10, 'th')} of %B %Y"
            )
        elif format == "deltadate":
            time_diff = int(time.time()) - int(value)
            days = time_diff // 86400
            hours = (time_diff % 86400) // 3600
            minutes = (time_diff % 3600) // 60
            time_ago = f"{days}d {hours}h {minutes}m"
            return time_ago
        return value

    @bot.slash_command(
        name="whois",
        description="Get a player's Aliases",
    )
    async def whois(
        ctx,
        name: Option(
            str, "The playername/uid to Query", autocomplete=autocompletenamesfromdb
        ),
        relaxed: Option(
            bool,
            "Use relaxed matching for confusing characters. Can take a while.",
            required=False,
            default=False,
        ),
    ):
        """command to see history of a player"""
        MAXALIASESSHOWN = 22
        originalname = name
        print("whois command from", ctx.author.id, "to", name)
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute("SELECT playeruid, playername FROM uidnamelink WHERE playeruid != 0")
        data = c.fetchall()

        if not data:
            tfdb.commit()
            tfdb.close()
            asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("No players in the database", ephemeral=False)
            return

        unsortedata = [{"name": x[1], "uid": x[0]} for x in data]

        if relaxed:
            await ctx.defer()
            simplified_name = simplyfy(name)
            data = [x for x in unsortedata if simplified_name in simplyfy(x["name"])]
            data = sorted(data, key=lambda x: len(x["name"]))
            data = sorted(
                data, key=lambda x: not simplyfy(x["name"]).startswith(simplified_name)
            )
            unsortedata = [
                x for x in unsortedata if simplified_name in simplyfy(x["name"])
            ]
        else:
            data = sorted(unsortedata, key=lambda x: len(x["name"]))
            data = sorted(
                data, key=lambda x: not x["name"].lower().startswith(name.lower())
            )
            data = [x for x in data if name.lower() in x["name"].lower()]
            unsortedata = [x for x in unsortedata if name.lower() in x["name"].lower()]

        if len(data) == 0:
            if name.isdigit():
                c.execute(
                    "SELECT playeruid FROM uidnamelink WHERE playeruid = ? AND playeruid != 0", (name,)
                )
                output = c.fetchone()
                if not output:
                    tfdb.commit()
                    tfdb.close()
                    await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
                    await ctx.respond("No players found", ephemeral=False)
                    return
                player = {"uid": output[0]}
            else:
                await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
                await ctx.respond("No players found", ephemeral=False)
                return

        else:
            player = data[0]

        c.execute(
            """
            SELECT playername, firstseenunix, lastseenunix 
            FROM uidnamelink 
            WHERE playeruid = ? AND playeruid != 0 
            ORDER BY id DESC
        """,
            (player["uid"],),
        )
        aliases_raw = list(
            map(
                lambda x: [
                    x[0],
                    int(x[1]) if x[1] else False,
                    int(x[2]) if x[2] else False,
                ],
                c.fetchall(),
            )
        )
        c.execute(
            """
            SELECT SUM(duration)
            FROM playtime
            WHERE playeruid = ? AND playeruid != 0""",
            (player["uid"],),
        )
        totalplaytime = c.fetchone()
        if totalplaytime and totalplaytime[0]:
            totalplaytime = totalplaytime[0]
        else:
            totalplaytime = False
        for i, alias in enumerate(aliases_raw):
            if not alias[1] or not alias[2]:
                aliases_raw[i].append(-1)
                continue
            c.execute(
                """
                SELECT SUM(duration)
                FROM playtime
                WHERE playeruid = ? AND playeruid != 0
                AND (joinatunix > ? OR leftatunix > ?)
                AND joinatunix < ?
            """,
                (player["uid"], alias[1], alias[1], alias[2]),
            )
            timespent = c.fetchone()
            if not timespent or not timespent[0]:
                aliases_raw[i].append(-1)
                continue
            # print([timespent])
            aliases_raw[i].append(int(timespent[0]))
        aliases_raw = functools.reduce(
            lambda a, b: {
                "lastalias": b,
                "aliases": [*a["aliases"], b]
                if not a["lastalias"] or a["lastalias"][0] != b[0]
                else [
                    *a["aliases"][:-1],
                    [b[0], b[1], a["aliases"][-1][2], b[3] + a["aliases"][-1][3]],
                ],
            },
            list(
                filter(
                    lambda x: len(x[0]) < 3
                    or x[0][0] != "("
                    or not x[0][1].isdigit()
                    or x[0][2] != ")",
                    aliases_raw,
                )
            ),
            {"lastalias": False, "aliases": []},
        )["aliases"]

        aliases = []
        names = []
        simplealiases = []
        for name, first, last, playtime in aliases_raw:
            first_str = f"<t:{first}:R>" if first else "unknown"
            last_str = f"<t:{last}:R>" if last else "unknown"
            aliases.append(
                f"{name} *(first seen: {first_str}, last seen: {last_str}, time played: **{modifyvalue(playtime, 'time') if playtime != -1 else 'unknown'}**)*"
            )
            simplealiases.append(
                f"*(first seen: {first_str}, last seen: {last_str}, time played: **{modifyvalue(playtime, 'time') if playtime != -1 else 'unknown'}**)*"
            )
            names.append(name)
        tfdb.commit()
        tfdb.close()

        alsomatching = {}
        for entry in data:
            if entry["uid"] == player["uid"]:
                continue
            alsomatching[entry["uid"]] = entry["name"]
       
        embed = discord.Embed(
            title=f"*Aliases* for uid {player['uid']} ({len(alsomatching.keys()) + 1} match{'es' if len(alsomatching.keys()) > 0 else ''} for '{originalname}')",
            color=0xFF70CB,
            description=f"Most recent to oldest, total playtime **{modifyvalue(totalplaytime, 'time') if totalplaytime else 'unknown'}**",
        )
        sanction, messageid = pullsanction(player["uid"])
        if sanction:
            embed.add_field(
                name=f"Sanction in effect:",
                value=f"\u200bType: `{sanction['sanctiontype']}`  Expires: `{sanction['humanexpire']}`  Reason: `{sanction['reason']}`"
                if not sanction["link"]
                else f"\u200b{sanction['link']}",
                inline=False,
            )
            MAXALIASESSHOWN -= 1
        # for y, x in enumerate(aliases[0:MAXALIASESSHOWN]):
        #     embed.add_field(name=f"Alias {y+1}:", value=f"\u200b {x}", inline=False)
        for y, x in enumerate(simplealiases[0:MAXALIASESSHOWN]):
            embed.add_field(name=f"{names[y]}:", value=f"\u200b {x}", inline=False)

        if len(aliases) > MAXALIASESSHOWN:
            embed.add_field(
                name=f"{len(aliases) - MAXALIASESSHOWN} more alias{'es' if len(aliases) - MAXALIASESSHOWN > 1 else ''}",
                value=f"({', '.join(list(map(lambda x: f'*{x}*', aliases[MAXALIASESSHOWN:])))})"[:1020],
            )

        if len(alsomatching.keys()) > 0:
            embed.add_field(
                name=f"The {len(alsomatching.keys())} other match{'es are:' if len(alsomatching.keys()) > 1 else ' is:'}",
                value=f"({', '.join(list(map(lambda x: f'*{x}*', list(alsomatching.values())[0:20])))}) {'**only first 20 shown**' if len(alsomatching.keys()) > 20 else ''}",
            )

        await ctx.respond(embed=embed, ephemeral=False)

        # await ctx.respond(data, ephemeral=False)
    @bot.slash_command(
        name="getalts",
        description="finds the alts for a player",
    )
    async def altcommand(
        ctx,
        name: Option(
            str, "The playername / uid", autocomplete=autocompletenamesfromdb
        )):
        
        if not checkrconallowed(ctx.author,getslashcommandoverridesperms("getalts")):
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond("You are not allowed to use this command.")
            return
        player = resolveplayeruidfromdb(name,None,True)
        if not player:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond(f"Could not find {name}.")
            return   
        player = player[0]
        # print(json.dumps(searchforalts(player["uid"]),indent=4))
        alts = list(filter(lambda x: True or x != player["uid"] ,searchforalts(player["uid"])["all"]))
        embed = discord.Embed(
            title=f"*Alts* for uid {player['uid']} ({len(alts)} alt{'s' if len(alts) != 1 else ''} for '{player["name"]}')",
            color=0xFF70CB,
            # description=f"maynotprovidecomprehensivelistidk",
        )
        for alt in alts:
            alt = resolveplayeruidfromdb(alt,"uid",False)
            embed.add_field(name=f"{alt[0]["name"]} ({alt[0]["uid"]}):", value=f"\u200b {len(alt)} Aliases", inline=False)
        if not alts:
            embed.add_field(name=f"No alts found", value=f"sorry", inline=False)
        await ctx.respond(embed=embed, ephemeral=False)


    def searchforalts(uid,uidinfo = False):
        if not uidinfo: uidinfo = {"searched":[],"all":[],"searchedips":[]}
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute("SELECT ipinfo FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC",(uid,))
        data = c.fetchone()
        uidinfo["searched"].append(uid)
        if not data or not data[0]:
            return uidinfo
        knownips = list(json.loads(data[0]))
        
        for ip in knownips:
            if ip["ip"] in uidinfo["searchedips"] or not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip["ip"]):
                continue
            uidinfo["searchedips"].append(ip["ip"])
            # print(ip)
            c.execute("SELECT playeruid FROM uidnamelink WHERE ipinfo LIKE ?",(f"%{ip["ip"]}%",))
            uidinfo["all"] = list(set([*uidinfo["all"],*(list(map(lambda x: x[0],c.fetchall())))]))
            
        tfdb.close()
        for uid in filter(lambda x:x not in uidinfo["searched"],uidinfo["all"]):
            uidinfo["searched"].append(uid)  # Mark as searched BEFORE recursing
            uidinfo = searchforalts(uid,uidinfo)
        return uidinfo
        
    
    @bot.slash_command(
        name="togglejoinnotify",
        description="Toggle if you are notified when a player joins",
    )
    async def togglejoinnotify(
        ctx,
        name: Option(
            str, "The playername to toggle", autocomplete=autocompletenamesfromdb
        ),
    ):
        """when a player joins or leaves, this command will allow you to be notified"""
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
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
        c.execute(
            "SELECT * FROM joinnotify WHERE discordidnotify = ? AND uidnotify = ?",
            (ctx.author.id, player["uid"]),
        )
        data = c.fetchone()
        if data is None:
            c.execute(
                "INSERT INTO joinnotify (discordidnotify, uidnotify) VALUES (?,?)",
                (ctx.author.id, player["uid"]),
            )
            await ctx.respond(f"{player['name']} added to notify list", ephemeral=True)
        else:
            c.execute(
                "DELETE FROM joinnotify WHERE discordidnotify = ? AND uidnotify = ?",
                (ctx.author.id, player["uid"]),
            )
            await ctx.respond(
                f"{player['name']} removed from notify list", ephemeral=True
            )
        tfdb.commit()
        tfdb.close()


def getdiscordtimestamp(timestamp=None):
    return f"<t:{timestamp if timestamp else int(time.time())}:R>"


@bot.slash_command(name="help", description="Show help for commands")
async def help(
    ctx,
    command: Option(
        str,
        "The command to get help for",
        required=False,
        choices=list(context["commands"]["botcommands"].keys()),
    ),
):
    """help me"""
    global context
    print("help requested")
    if command is None:
        commands = {}
        
        for key in context["commands"]["botcommands"].keys():
            commands[key] = context["commands"]["botcommands"][key]["description"]

        for slash_command in bot.walk_application_commands():
            if (
                slash_command.name == "help"
                or slash_command.name in context["commands"]["botcommands"].keys()
            ):
                continue

            if slash_command.name == "thrownonrcon" and SHOULDUSETHROWAI != "1":
                continue
            if slash_command.name == "serverlesssanction" and SANCTIONAPIBANKEY == "":
                continue

            commands[slash_command.name] = slash_command.description

        command_items = list(commands.items())
        chunk_size = 12
        
        await ctx.respond("# Help\nUse /help <command> to get help for a specific command", ephemeral=True)

        colors = [
            "\u001b[0;32m",  # Green
            "\u001b[0;34m",  # Blue
            "\u001b[0;35m",  # Magenta
            "\u001b[0;36m",  # Cyan
            "\u001b[0;33m",  # Yellow
            "\u001b[0;31m",  # Red
            # "\u001b[0;37m",  # White
            "\u001b[0;30m"   # Gray
        ]
        reset = "\u001b[0m"
        i = 0 
        while i < len(command_items):
            message = ""
         
            

            for j, (name, desc) in enumerate(command_items[i:]):
                color = colors[j % len(colors)]
                if len(message+ f"{color}{f"{name}:".ljust(len(max(command_items, key = lambda x: len(x[0]))[0])+len(": "))}{reset}{desc}\n") > 1990:
                    break
                i+=1
                message += f"{color}{f"{name}:".ljust(len(max(command_items, key = lambda x: len(x[0]))[0])+len(": "))}{reset}{desc}\n" 
            
            if message:
                await ctx.followup.send(f"```ansi\n{message}```", ephemeral=True)

    else:
        defaults = {
            "description": "No description available",
            "parameters": [],
            "rcon": False,
            "commandparaminputoverride": {},
            "outputfunc": None,
            "regularconsolecommand": False,
        }
        message = f"# {command}\n{context['commands']['botcommands'][command]['description']}\n\n"

        mergeddescriptions = {**defaults, **context["commands"]["botcommands"][command]}
        

        detailed_message = ""
        for key in mergeddescriptions.keys():
            detailed_message += f"**{key}**:\n```json\n{json.dumps(mergeddescriptions[key], indent=4)}\n```\n"
        
        if len(message + detailed_message) > 1900: 
            await ctx.respond(message, ephemeral=True)
            
 
            current_chunk = ""
            for key in mergeddescriptions.keys():
                key_content = f"**{key}**:\n```json\n{json.dumps(mergeddescriptions[key], indent=4)}\n```\n"
                
                if len(current_chunk + key_content) > 1900:
                    if current_chunk:
                        await ctx.followup.send(current_chunk, ephemeral=True)
                    current_chunk = key_content
                else:
                    current_chunk += key_content
            
            if current_chunk:
                await ctx.followup.send(current_chunk, ephemeral=True)
        else:
            await ctx.respond(message + detailed_message, ephemeral=True)


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


def sanctionoverride(data, serverid, statuscode):
    """Overrides the default display for a commandreturn. not really needed anymore as the default display is very very similar to how this works now."""
    embed = discord.Embed(
        title="Sanction Result",
        color=0xFF70CB,
    )

    try:
        embed.add_field(
            name="Targeted Player", value=f"\u200b {data['playername']}", inline=False
        )
        embed.add_field(
            name="Sanction Type", value=f"\u200b {data['Sanctiontype']}", inline=False
        )
        embed.add_field(
            name="Sanction Reason", value=f"\u200b {data['reason']}", inline=False
        )
        embed.add_field(
            name="Sanction Expiry", value=f"\u200b {data['expire']}", inline=False
        )
        embed.add_field(
            name="Targeted player UID", value=f"\u200b {data['UID']}", inline=False
        )
        embed.add_field(
            name="Sanction Issuer", value=f"\u200b {data['issueruid']}", inline=False
        )
    except:
        traceback.print_exc()
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
    """Overrides the default display for /playing to create a nice, pretty list"""
    if len(data) == 0:
        return discord.Embed(
            title=f"Server status for {context['servers'][serverid]['name']}",
            description="No players online",
            color=0xFF70CB,
        )
    else:
        formattedata = {"meta": {}}
        for key, value in data.items():
            if key == "meta":
                formattedata["meta"]["map"] = value[0]
                value[1] = int(value[1])
                formattedata["meta"]["time"] = f"{value[1] // 60}m {value[1] % 60}s"
                # formattedata["meta"]["time"] = f"<t:{int(time.time()+value[1])}:R>"
                continue

            if value[1] not in formattedata.keys():
                formattedata[value[1]] = {
                    "playerinfo": {},
                    "teaminfo": {"score": 0},
                }
            formattedata[value[1]]["playerinfo"][key] = {
                "score": value[0],
                "kills": value[2],
                "deaths": value[3],
            }
            formattedata[value[1]]["teaminfo"]["score"] += value[0]
    embed = discord.Embed(
        title=f"Server status for {context['servers'][serverid]['name']}",
        description=""
        if len(data.keys()) < 22
        else f"__{len(data) - 21} player{'s' if len(data) - 21 > 1 else ''} truncated due to embed limits__",
        color=0xFF70CB,
    )
    if statuscode != 200:
        embed.add_field(name="Error", value=f"\u200b {data} {statuscode}", inline=False)
        return embed
    embed.add_field(
        name="Map", value=f"\u200b {formattedata['meta']['map']}", inline=True
    )
    embed.add_field(
        name="Players", value=f"\u200b {len(data) - 1} players online", inline=True
    )
    embed.add_field(
        name="Time left", value=f"\u200b {formattedata['meta']['time']}", inline=True
    )
    sortedteams = sorted(
        [team for team in formattedata.keys() if team != "meta"],
        key=lambda x: formattedata[x]["teaminfo"]["score"],
        reverse=True,
    )
    sortedvalues = {}
    for team in sortedteams:
        sortedvalues[team] = formattedata[team]
    for team in sortedvalues.keys():
        if team == "meta":
            continue
        embed.add_field(
            name=f"> *Team {team}*",
            value=f"\u200b Score: {formattedata[team]['teaminfo']['score']} | Players: {len(formattedata[team]['playerinfo'])}",
            inline=False,
        )
        for player in sorted(
            formattedata[team]["playerinfo"].keys(),
            key=lambda x: formattedata[team]["playerinfo"][x]["score"],
            reverse=True,
        )[0:10]:
            embed.add_field(
                name=f"\u200b \u200b \u200b \u200b \u200b \u200b {player}",
                value=f"\u200b \u200b \u200b \u200b \u200b \u200b \u200b Score: {formattedata[team]['playerinfo'][player]['score']} | Kills: {formattedata[team]['playerinfo'][player]['kills']} | Deaths: {formattedata[team]['playerinfo'][player]['deaths']}",
                inline=False,
            )
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
#     if guild.id != context["categoryinfo"]["activeguild"]:
#         await ctx.respond("This guild is not the active guild.", ephemeral=False)
#         return
#     if ctx.author.id not in context["RCONallowedusers"]:
#         await ctx.respond("You are not allowed to use this command.", ephemeral=False)
#         return
#     if any(server.get("channelid") == channel.id for server in context["servers"].values()):
#         await ctx.respond("This channel is already bound to a server.", ephemeral=False)
#         return
#     context["overridechannels"]["globalchannel"] = channel.id
#     savecontext()
#     await ctx.respond(f"Global channel bound to {channel.name}.", ephemeral=False)


@bot.slash_command(
    name="widget", description="add a widget to a servers name in discord channel"
)
async def addserverwidget(
    ctx,
    widget: Option(
        str,
        "What should the widget be",
        required=True,
    ),
    servername: Option(
        str,
        "The servername (omit for current channel's server)",
        required=False,
        **(
            {
                "choices": list(
                    s.get("name", "Unknown") for s in context["servers"].values()
                )
            }
            if SERVERNAMEISCHOICE == "1"
            else {"autocomplete": autocompleteserversfromdb}
        ),
    ) = None,
):
    """add a widget to a server name"""
    global context
    serverid = getchannelidfromname(servername, ctx)
    if not checkrconallowed(ctx.author, getslashcommandoverridesperms("changeserverwidget"),serverid=serverid,):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return

    if serverid is None:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond(
            "Server not bound to this channel, could not send command.", ephemeral=False
        )
        return

    context["servers"][serverid]["widget"] = widget
    savecontext()
    await ctx.respond(f"Changed widget to {widget}", ephemeral=False)
    await hideandshowchannels(serverid,True)


@bot.slash_command(name="bindrole", description="Bind a role to the bot.")
async def bind_global_role(
    ctx,
    roletype: Option(
        str,
        "The type of role to bind",
        required=True,
        choices=list(context["overrideroles"].keys()),
    ),
    role: Option(discord.Role, "The role to bind to", required=True),
):
    """binds a role, to give it specific powers on the bot."""
    global context
    guild = ctx.guild
    if guild and guild.id != context["categoryinfo"]["activeguild"]:
        await ctx.respond("This guild is not the active guild.", ephemeral=False)
        return
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("bindrole")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return
    context["overrideroles"][roletype] = role.id
    savecontext()
    await updateroles()
    await ctx.respond(f"Role type {roletype} bound to {role.name}.", ephemeral=False)


@bot.slash_command(name="bindchannel", description="Bind a channel to the bot.")
async def bind_global_channel(
    ctx,
    channeltype: Option(
        str,
        "The type of channel to bind",
        required=True,
        choices=list(context["overridechannels"].keys()),
    ),
    channel: Option(discord.TextChannel, "The channel to bind to", required=True),
):
    """binds a channel to a certain output of the bots, like leaderboards, ban messages, nonowordnotifys"""
    global context
    guild = ctx.guild
    if guild and guild.id != context["categoryinfo"]["activeguild"]:
        await ctx.respond("This guild is not the active guild.", ephemeral=False)
        return
    if not checkrconallowed(ctx.author,getslashcommandoverridesperms("bindchannel")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("You are not allowed to use this command.", ephemeral=False)
        return
    if any(
        server.get("channelid") == channel.id for server in context["servers"].values()
    ):
        await ctx.respond("This channel is already bound to a server.", ephemeral=False)
        return

    if channeltype == "leaderboardchannel":
        if context["overridechannels"]["leaderboardchannel"] == 0:
            context["leaderboardchannelmessages"].extend(
                [
                    {
                        "name": "Pilot kills",
                        "description": "Top 10 players with most pilot kills",
                        "color": 16740555,
                        "database": "playtime",
                        "orderby": "Total kills",
                        "categorys": {
                            "Total kills": {"columnsbound": ["pilotkills"]},
                            "Total score": {"columnsbound": ["scoregained"]},
                            "duration": {
                                "format": "time",
                                "columnsbound": ["duration"],
                            },
                            "Score Per Hour": {
                                "columnsbound": ["scoregained", "duration"],
                                "format": "XperY*3600",
                                "calculation": "scoregained / duration",
                            },
                        },
                        "filters": {},
                        "merge": "name",
                        "maxshown": 10,
                        "id": 0,
                    },
                    {
                        "name": "Frag grenade kills",
                        "description": "frag kills in last week",
                        "color": 16740555,
                        "database": "specifickilltracker",
                        "orderby": "Frag kills",
                        "categorys": {"Frag kills": {"columnsbound": ["matchcount"]}},
                        "filters": "f'cause_of_death = \"mp_weapon_frag_grenade\" AND timeofkill > {int((datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).weekday())).timestamp())}'",
                        "merge": "name",
                        "maxshown": 10,
                        "id": 0,
                    },
                    {
                        "name": "All weapon kills",
                        "categorys": [],
                        "color": 16740555,
                        "id": 0,
                        "description": "top 3 kills with all guns",
                        "maxshown": 3,
                    },
                ]
            )
        context["overridechannels"]["leaderboardchannel"] = channel.id
    elif channel.id != context["overridechannels"]["leaderboardchannel"]:
        for i in range(len(context["leaderboardchannelmessages"])):
            context["leaderboardchannelmessages"][i]["id"] = 0
    context["overridechannels"][channeltype] = channel.id
    savecontext()
    await ctx.respond(
        f"Channel type {channeltype} bound to {channel.name}.", ephemeral=False
    )


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


# @bot.slash_command(
#     name="rconchangeuserallowed",
#     description="toggle if a user is allowed to use RCON commands in dms",
# )
# async def rcon_add_user(ctx, user: Option(discord.User, "The user to add")):
#     global context
#     # return
#     # check if the user is an admin on the discord
#     if user.id in context["RCONallowedusers"] and ctx.author.guild_permissions.administrator:
#         context["RCONallowedusers"].remove(user.id)
#         savecontext()
#         await ctx.respond(
#             f"User {user.name} removed from RCON whitelist.", ephemeral=False
#         )
#     elif ctx.author.guild_permissions.administrator:
#         context["RCONallowedusers"].append(user.id)
#         savecontext()
#         await ctx.respond(f"User {user.name} added to RCON whitelist.", ephemeral=False)
#     else:
#         await ctx.respond(
#             "Only administrators can add users to the RCON whitelist.", ephemeral=False
#         )
@bot.slash_command(
    name="linktf2account", description="link your tf2 account to a discord account"
)
async def linktfaccount(ctx):
    """used generally for nicknames, ingamenamecolours, and helpdc commands that require a special role, like rconrole/coolperksrole"""
    global context, accountlinker
    # accounts = resolveplayeruidfromdb(tf2accountname,None,True)
    linkcode = 0
    while not linkcode or linkcode in accountlinker:
        linkcode = f"!{random.randint(10000, 100000)}"
    accountlinker[linkcode] = {
        "account": ctx.author.id,
        "timerequested": int(time.time() + 300),
        "ctx": ctx,
        "name": ctx.author.display_name,
    }
    await ctx.respond(
        f"Trying to link {ctx.author.nick if hasattr(ctx.author, 'nick') and ctx.author.nick is not None else ctx.author.display_name} '{linkcode}' in any server chat to link in next 5 mins",
        ephemeral=True,
    )


@bot.slash_command(name="tf2ingamesettag", description="Set your tag in tf2")
async def chooseatag(
    ctx, tag: Option(str, f"Enter a 1 - {MAXTAGLEN} character tag, or 'reset' to reset")
):
    """set a tag to appear before your name"""

    # if not checkrconallowed(ctx.author,"coolperksrole"):
    #     await asyncio.sleep (SLEEPTIME_ON_FAILED_COMMAND)
    #     await ctx.respond(f"You do not have the coolperksrole, so cannot use this command :) to get it: {COOLPERKSROLEREQUIRMENTS}", ephemeral=False)
    #     return

    await ctx.respond(settag(tag, ctx.author.id), ephemeral=False)


def settag(tag, discorduid):
    """Sets custom tag for a Discord user that appears in game chat"""
    # return f"2{tag}2"
    """helper for above func"""
    global colourslink
    if tag != "reset" and (len(tag) < 1 or len(tag) > MAXTAGLEN):
        return f"Tags have to be bettween 1 and {MAXTAGLEN} digits"
    warn = ""
    if not pullid(discorduid, "tf"):
        warn = "\n** BUT titanfall account not linked, use /linktf2account to link one, so this tag appears**\n(you don't have to set your tag again after you link)"
    tfdb = postgresem("./data/tf2helper.db")
    tfdb.execute(
        """
        INSERT INTO discorduiddata (discorduid, nameprefix)
        VALUES (?, ?)
        ON CONFLICT(discorduid) DO UPDATE SET nameprefix = excluded.nameprefix
        """,
        (discorduid, str(tag) if tag != "reset" else "reset"),
    )
    tfdb.commit()
    tfdb.close()
    if tag == "reset" and getpriority(colourslink, [discorduid, "nameprefix"]):
        colourslink[discorduid]["nameprefix"] = None
        return f"reset tag {warn}"
    else:
        colourslink.setdefault(discorduid, {}).update({"nameprefix": tag})
    return f"Set prefix to [{tag}] {warn}"


@bot.slash_command(
    name="tf2ingamechatcolour",
    description="put in a normal colour eg: 'red', or a hex colour eg: '#ff30cb' to colour your tf2 name",
)
async def show_color_what(
    ctx,
    colour: Option(str, "Enter a normal/hex color, or 'reset' to reset"),
    teamsetting: Option(
        str,
        "Who sees this",
        required=False,
        choices=["all", "friendly", "enemy", "neutral"],
    ) = "all",
):
    """sets in game chat colour"""

    if not checkrconallowed(ctx.author, getslashcommandoverridesperms("tf2ingamechatcolour","coolperksrole")):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond(
            f"You do not have the coolperksrole, so cannot use this command :) to get it: {COOLPERKSROLEREQUIRMENTS}",
            ephemeral=False,
        )
        return
    await ctx.respond(
        setcolour(colour, ctx.author.id, "choseningamecolour", teamsetting),
        ephemeral=False,
    )


def setcolour(colours, discorduid, type="choseningamecolour", teamsetting="all"):
    """Sets color preferences for Discord user with team-specific settings and validation"""
    """helper function for above"""
    global colourslink
    colourslist = []
    teamsetting = teamsetting.upper()
    teams = ["FRIENDLY", "ENEMY", "NEUTRAL"]
    colours = colours.replace(",", " ")
    for colour in colours.split(" "):
        # print(colour)
        if (
            not re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour)
            and colour.lower() not in CSS_COLOURS.keys()
            and colour != "reset"
        ):
            return "Please enter a **valid** hex color (e.g: '#1A2B3C'), or a valid normal colour, (e.g: 'red')"
        if re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour):
            r = int(colour[1:3], 16)
            g = int(colour[3:5], 16)
            b = int(colour[5:7], 16)
            rgba = [r, g, b]
            colourslist.append(rgba)
        elif colour.lower() in CSS_COLOURS.keys():
            rgba = CSS_COLOURS[colour]
            colourslist.append(rgba)
        else:
            rgba = "reset"
            break
    if teamsetting == "ALL":
        colourslist = {
            **getpriority(colourslink, [discorduid], nofind={}),
            **{x: colourslist for x in teams},
        }
    else:
        colourslist = {
            **getpriority(colourslink, [discorduid], nofind={}),
            teamsetting: colourslist,
        }
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """
        INSERT INTO discorduiddata (discorduid, choseningamecolour)
        VALUES (?, ?)
        ON CONFLICT(discorduid) DO UPDATE SET choseningamecolour = excluded.choseningamecolour
        """,
        (discorduid, json.dumps(colourslist) if rgba != "reset" else "reset"),
    )

    tfdb.commit()
    tfdb.close()
    warn = ""
    if not pullid(discorduid, "tf"):
        warn = "\n**BUT titanfall account not linked, use /linktf2account to link one, so these colours appear**\n(you don't have to set your tag again after you link)"
    if discorduid not in colourslink.keys():
        colourslink[discorduid] = {}
    differences = dict(
        filter(
            lambda x: str(colourslink[discorduid].get(x[0], False)) != str(x[1]),
            colourslist.items(),
        )
    )
    if rgba == "reset":
        colourslink[discorduid] = colourslist
        return f"reset ingame colour for {teamsetting} to default {warn}"
    colourslink[discorduid] = colourslist
    # print(json.dumps(colourslink,indent = 4))
    return f"Set ingame colour to {str({x[0].lower(): ''.join(map(str, x[1])) for x in filter(lambda y: y[0] in teams, differences.items())})[1:-1].replace("'", '') if differences else 'No changes'} {warn}"


@bot.slash_command(
    name="discordtotf2chatcolour",
    description="put in a normal colour eg: 'red', or a hex colour eg: '#ff30cb' to colour your tf2 name",
)
async def show_color_why(
    ctx, colour: Option(str, "Enter a normal/hex color, or 'reset' to reset")
):
    """sets discord colour"""
    global colourslink
    colourslist = []
    colours = colour

    if len(colours.split(" ")) > 1:
        if not checkrconallowed(ctx.author,  getslashcommandoverridesperms("discordtotf2chatcolour","coolperksrole")):
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond(
                f"You do not have the coolperksrole, so cannot do multiple colours. to get it: {COOLPERKSROLEREQUIRMENTS}",
                ephemeral=False,
            )
            return
    for colour in colours.split(" "):
        # print(colour)
        if (
            not re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour)
            and colour.lower() not in CSS_COLOURS.keys()
            and colour != "reset"
        ):
            await ctx.respond(
                "Please enter a **valid** hex color (e.g: '#1A2B3C'), or a valid normal colour, (e.g: 'red')",
                ephemeral=False,
            )
            return
        if re.compile(r"^#([A-Fa-f0-9]{6})$").match(colour):
            r = int(colour[1:3], 16)
            g = int(colour[3:5], 16)
            b = int(colour[5:7], 16)
            rgba = (r, g, b)
        elif colour.lower() in CSS_COLOURS.keys():
            rgba = CSS_COLOURS[colour]
        else:
            rgba = "reset"
            break
        colourslist.append(rgba)
        rgba = "|".join(map(str, colourslist))

    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        """
        INSERT INTO discorduiddata (discorduid, chosencolour)
        VALUES (?, ?)
        ON CONFLICT(discorduid) DO UPDATE SET chosencolour = excluded.chosencolour
        """,
        (ctx.author.id, str(rgba) if rgba != "reset" else "reset"),
    )

    tfdb.commit()
    tfdb.close()
    if ctx.author.id not in colourslink.keys():
        colourslink[ctx.author.id] = {}
    if rgba == "reset":
        colourslink[ctx.author.id]["discordcolour"] = []
        await ctx.respond(f"reset discord -> tf2 colour to default")
        return
    colourslink[ctx.author.id]["discordcolour"] = colourslist
    await ctx.respond(
        f"Set discord -> tf2 colour to {', '.join(map(str, colourslist))}"
    )


# lifted straight from my chat colours thing
def gradient(message, colours, maxlen, stripfirstcolour=False):
    """colours a string as a gradient, ripped straight out of my website"""
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
        colours.append(colours[0])

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
    # coloursmatch = []
    for i in range(len(colours) - 1):
        groupedletters.append([])
        # coloursmatch.append((colours[i],colours[i+1]))
    for i in range(len(actualmessage)):
        groupedletters[int(i / len(actualmessage) * (len(colours) - 1))].append(
            actualmessage[i]
        )
    # print(groupedletters,coloursmatch)

    while overcharlimit:
        # print("here")
        counter = 0
        messagecounter = 0
        firstcolour = stripfirstcolour
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
                # print(colours[i])
                Colour = (
                    colours[i][0]
                    + int(differences[i][0] * (counter2) / (len(letters))),
                    colours[i][1]
                    + int(differences[i][1] * (counter2) / (len(letters))),
                    colours[i][2]
                    + int(differences[i][2] * (counter2) / (len(letters))),
                )
                if firstcolour != True:
                    outputmessage.append(rgb_to_ansi(Colour, 0) + letter)
                else:
                    outputmessage.append(letter)
                    firstcolour = rgb_to_ansi(Colour, 0)
                counter += 1
                counter2 += 1
                messagecounter += 1
        if (not stripfirstcolour and len("".join(outputmessage)) > maxlen) or (
            stripfirstcolour and len(firstcolour) + len("".join(outputmessage)) > maxlen
        ):
            encodelength += 1
            outputmessage = []
        else:
            overcharlimit = False
        if encodelength > maxlen / 2:
            return 2
    if firstcolour:
        return "".join(outputmessage), firstcolour
    return "".join(outputmessage)


@functools.lru_cache(maxsize=None)
def rgb_to_ansi(value, vary=0):
    """conversts an rgb code to an ansi string variance is random variance that is less prominent on brighter,less saturated colours, also directly from my website"""
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


def replace_mentions_with_display_names(message,isresponse):
    """Replace Discord mentions with display names"""
    content = message.content
    for user in message.mentions:
        display_name = user.display_name if user.display_name else user.global_name
        content = content.replace(
            f"<@{user.id}>",
            f"{PREFIXES['stat']}@{display_name}{PREFIXES['chatcolour'] if not isresponse else PREFIXES["commandname"]}",
        )
        content = content.replace(
            f"<@!{user.id}>",
            f"{PREFIXES['stat']}@{display_name}{PREFIXES['chatcolour'] if not isresponse else PREFIXES["commandname"]}",
        )
    # print("cont",content)
    return content


def strip_webhook_formatting(message_content):

    content = re.sub(r'\*\*(.*?)\*\*:', r'\1:', message_content)
    return content

@bot.event
async def on_message(message,isresponse=False): #↖
    """handles capturing a message, colouring it, and sending to the relevant server"""
    global context, discordtotitanfall
    if (message.author == bot.user or message.webhook_id is not None) and not isresponse:
        return
    if REACTONMENTION != "0" and bot.user in message.mentions:
        await message.add_reaction(REACTONMENTION)
    if not any(
        server.get("channelid") == message.channel.id
        for server in context["servers"].values()
    ):
        return
    # print("discord message recieved")
    serverid = [
        key
        for key, server in context["servers"].items()
        if server.get("channelid") == message.channel.id
    ][0]
    # if serverid not in messagestosend.keys():
    #     messagestosend[serverid] = []
    if not (respondedto:= False)  and not isresponse and  message.reference and message.reference.message_id :
        respondedto = await on_message(await message.channel.fetch_message(message.reference.message_id),True)
    
        

    addedmentions = replace_mentions_with_display_names(message,isresponse)
    name = False
    if message.author == bot.user and message.webhook_id is not None and isresponse:
        name,addedmentions = strip_webhook_formatting(addedmentions).split(":",1)
    elif  message.webhook_id is not None and isresponse:
        name = message.author.name
    addedmentionsreallen = f"{(respondedto or "") and "→ "}{addedmentions}{"(REPLY) "if isresponse else "" }"
    initdiscordtotitanfall(serverid)
    if (
        len(
            f"{ANSICOLOUR}{message.author.nick if not name and message.author.nick is not None   else name or message.author.display_name}: {PREFIXES['neutral']}{addedmentionsreallen}"
        )
        > 254
        - bool(context["servers"].get(serverid, {}).get("istf1server", False))
        * tf1messagesizesubtract
    ):
        await message.channel.send("Message too long, cannot send.")
        return
    authornick = computeauthornick(
        message.author.nick
        if  not name and  message.author.nick is not None 
        else name or message.author.display_name,
        message.author.id,
        addedmentionsreallen,
        serverid,
    )

    # dotreacted = None
    # if discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 45:
    #     dotreacted = "🔴"
    # elif discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 5:
    #     dotreacted = "🟡"
    if (
        addedmentions != ""
    ):  # and not context["servers"].get(serverid, {}).get("istf1server",False):
        # print(f"{message.author.nick if message.author.nick is not None else message.author.display_name}: {addedmentions}")
        # print(len(f"{authornick}: {PREFIXES['neutral']}{addedmentions}"),f"{authornick}: {PREFIXES['neutral']}{addedmentions}\033[0m")
        print(
            f"{getpriority(context, ['servers', serverid, 'name'])}:",
            len(
                f"{authornick}{': ' if not bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{PREFIXES['neutral']}{': ' if bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{addedmentionsreallen}"
            ),
            (
                f"{authornick}{': ' if not bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{PREFIXES['neutral']}{': ' if bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{addedmentionsreallen}"
            ),
        )
        if not isresponse:
            if respondedto:
                # discordtotitanfall[serverid]["messages"].append(
                #     {
                #         "id": message.id,
                #         "content": f"{PREFIXES['stat2']}",
                #         # "teamoverride": 4,
                #         # "isteammessage": False,
                #         # "uidoverride": []
                #         # "dotreacted": dotreacted
                #     })
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "id": message.id,
                        "content": f"↓ {respondedto}",
                        # "teamoverride": 4,
                        # "isteammessage": False,
                        # "uidoverride": []
                        # "dotreacted": dotreacted
                    })
            discordtotitanfall[serverid]["messages"].append(
                {
                    "id": message.id,
                    "content": f"{(respondedto or "") and "→ "}{authornick}{': ' if not bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{PREFIXES['neutral']}{': ' if bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{addedmentions}",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    # "uidoverride": []
                    # "dotreacted": dotreacted
                })
        else:
            return f"(REPLY) {authornick}{': ' if not bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{PREFIXES['commandname']}{': ' if bool(context['servers'].get(serverid, {}).get('istf1server', False)) else ''}{addedmentions}"
    if not isresponse:
        if (
            discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 45
        ):  # server crash (likely)
            await reactomessages([message.id], serverid, "🔴")
        elif (
            discordtotitanfall[serverid]["lastheardfrom"] < int(time.time()) - 5
        ):  # changing maps (likely)
            await reactomessages([message.id], serverid, "🟡")
        if message.attachments and SHOULDUSEIMAGES == "1":
            print("creating image")
            if resolvecommandpermsformainbot(serverid,"sendimage") == None:
                return
            elif not resolvecommandpermsformainbot(serverid,"sendimage") or checkrconallowed(author,resolvecommandpermsformainbot(serverid,"sendimage",True),serverid=serverid):
                image = await createimage(message)
                await returncommandfeedback(
                    *sendrconcommand(serverid, f"!sendimage {' '.join(image)}"),
                    message,
                    iscommandnotmessage=False,
                )
        # messagestosend[serverid].append(
        #     f"{message.author.nick if message.author.nick is not None else message.author.display_name}: {PREFIXES['neutral']}{addedmentions}"
        # )


@functools.lru_cache(maxsize=None)
def pullid(uid, force=False, mustbereal=False):
    """converts a tf2 uid to and from discord"""
    global context
    result = None
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    if not force or force == "discord":
        c.execute("SELECT discordid FROM discordlinkdata WHERE uid = ?", (uid,))
        result = c.fetchone()
        if (
            not result
            and not mustbereal
            and resolveplayeruidfromdb(
                uid, uidnameforce="uid", oneuidpermatch=True, istf1=False
            )
        ):
            negative_discord_id = -int(time.time() * 10)
            c.execute(
                "INSERT INTO discordlinkdata (uid, discordid, linktime) VALUES (?, ?, ?)",
                (uid, negative_discord_id, int(time.time())),
            )
            tfdb.commit()
            result = (negative_discord_id,)
        elif not result:
            c.close()
            tfdb.close()
            return False
    if result is None and (not force or force == "tf"):
        c.execute("SELECT uid FROM discordlinkdata WHERE discordid = ?", (uid,))
        result = c.fetchone()
    c.close()
    tfdb.close()
    if not result:
        return False
    return result[0]


def colourmessage(message, serverid):
    """handles all in game name modifications to messages, like tags, muted players seeing their own message, message gradients, impersonations"""
    global discorduidnamelink
    # print("HEREHERHERE")
    if (
        not message.get("metadata", False)
        or not message["metadata"].get("uid", False)
        or not message["metadata"].get("type", False)
        in ["usermessagepfp", "chat_message", "impersonate"]
    ):
        # print("oxoxo",message["metadata"])
        return False
    # print(json.dumps(message,indent=4))
    discorduid = discorduidnamelink.get(message["metadata"]["uid"], False)
    if not discorduid and getpriority(message, ["metadata", "donotcolour"]):
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute(
            "SELECT discordid FROM discordlinkdata WHERE uid = ?",
            (message["metadata"]["uid"],),
        )
        link = c.fetchone()
        discorduidnamelink[message["metadata"]["uid"]] = (
            link[0] if link and link[0] else False
        )
        discorduid = discorduidnamelink.get(message["metadata"]["uid"], False)

    if (
        getpriority(message, ["metadata", "donotcolour"])
        and getpriority(
            colourslink,
            [discorduidnamelink.get(message["metadata"]["uid"], False), "nameprefix"],
        )
        and not any(
            list(
                (
                    dict(
                        filter(
                            lambda x: x[0] in ["FRIENDLY", "NEUTRAL", "ENEMY"],
                            colourslink.get(
                                discorduidnamelink.get(
                                    message["metadata"]["uid"], False
                                ),
                                {},
                            ).items(),
                        )
                    )
                ).values()
            )
        )
    ):
        return False
    # print("HERE",message)
    # I hope this validation works! if donotcolour and only nametag, else "figure it out"
    # getpriority(colourslink,[discorduidnamelink.get(message["metadata"]["uid"],False),"nameprefix"]) and not any(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduidnamelink.get(message["metadata"]["uid"],False),{}).items()))).values()))
    # print("ew")
    if (
        message["metadata"].get("ismuted")
        or message["metadata"].get("type", False) == "impersonate"
    ) and not discorduid:
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute(
            "SELECT discordid FROM discordlinkdata WHERE uid = ?",
            (message["metadata"]["uid"],),
        )
        link = c.fetchone()
        discorduidnamelink[message["metadata"]["uid"]] = (
            link[0] if link and link[0] else False
        )
        discorduid = discorduidnamelink.get(message["metadata"]["uid"], False)
    elif (
        not message["metadata"].get("ismuted")
        and message["metadata"].get("type", False) != "impersonate"
    ):
        if not discorduid:
            tfdb = postgresem("./data/tf2helper.db")
            c = tfdb
            c.execute(
                "SELECT discordid FROM discordlinkdata WHERE uid = ?",
                (message["metadata"]["uid"],),
            )
            link = c.fetchone()
            discorduidnamelink[message["metadata"]["uid"]] = (
                link[0] if link and link[0] else False
            )
            if (not link or not link[0]) and not message["metadata"]["blockedmessage"]:
                # print("eee")
                return False
            elif not link or not link[0]:
                # print("ee")
                return {
                    "both": f"{PREFIXES['neutral']}{message['player']}: {message['messagecontent']}",
                    "messageteam": 4,
                    "uid": str(message["metadata"]["uid"]),
                    "forceblock": False,
                }
            discorduid = link[0]
        # if not colourslink.get(discorduid,False).get("ingamecolour",False) and message["metadata"]["blockedmessage"]:
        #     # print("edwqdqw")
        #     return {"both":f"{PREFIXES['neutral']}{message['player']}: {message['messagecontent']}","messageteam":4,"uid":str(message["metadata"]["uid"]),"forceblock":False}
        if (
            not any(
                map(
                    lambda x: x[1],
                    filter(
                        lambda x: x[0]
                        in ["FRIENDLY", "NEUTRAL", "ENEMY", "nameprefix"],
                        colourslink.get(discorduid, {}).items(),
                    ),
                )
            )
            and not message["metadata"]["blockedmessage"]
        ):
            # print("e")d
            return False
    # print("HEHRHEE")
    authornicks = {}
    # print(message["metadata"].get("type","blegh"))
    # print(json.dumps(message))
    # print(colourslink[discorduid])
    if message["metadata"]["teamtype"] == "not team":
        authornicks["friendly"] = computeauthornick(
            getpriority(readplayeruidpreferences(message["metadata"]["uid"], False),["tf2","nameoverride"]) or message["player"] ,
            discorduid,
            message["messagecontent"],
            serverid,
            "FRIENDLY",
            "FRIENDLY",
            254
            - len(
                f"[111m[TEAM]{' ' if not getpriority(colourslink, [discorduid, 'nameprefix']) else ''}"
            )
            if message["metadata"]["teamtype"] != "not team"
            else 254,
            True,
        )
        authornicks["enemy"] = computeauthornick(
            getpriority(readplayeruidpreferences(message["metadata"]["uid"], False),["tf2","nameoverride"]) or message["player"],
            discorduid,
            message["messagecontent"],
            serverid,
            "ENEMY",
            "ENEMY",
            254
            - len(
                f"[111m[TEAM]{' ' if not getpriority(colourslink, [discorduid, 'nameprefix']) else ''}"
            )
            if message["metadata"]["teamtype"] != "not team"
            else 254,
            True,
        )
    else:
        authornicks["friendly"] = computeauthornick(
            getpriority(readplayeruidpreferences(message["metadata"]["uid"], False),["tf2","nameoverride"]) or message["player"],
            discorduid,
            message["messagecontent"],
            serverid,
            "FRIENDLY",
            "FRIENDLY",
            254
            - len(
                f"[111m[TEAM]{' ' if not getpriority(colourslink, [discorduid, 'nameprefix']) else ''}"
            )
            if message["metadata"]["teamtype"] != "not team"
            else 254,
            True,
        )
    output = {}
    for key, value in authornicks.items():
        output[key] = (
            f"{f'[111m[TEAM]{" " if not getpriority(colourslink, [discorduid, "nameprefix"]) else ""}' if message['metadata']['teamtype'] != 'not team' else ''}{value}: {PREFIXES['neutral']}{message['messagecontent']}"
        )
    # print(output)

    if (
        not any(
            map(
                lambda x: x[1],
                filter(
                    lambda x: x[0] in ["FRIENDLY", "NEUTRAL", "ENEMY", "nameprefix"],
                    colourslink.get(discorduid, {}).items(),
                ),
            )
        )
        and message["metadata"]["blockedmessage"]
    ):
        print("COLOURSLINK", colourslink.get(discorduid))
        output["uid"] = str(message["metadata"]["uid"])
        output["forceblock"] = False
    elif not message["metadata"]["blockedmessage"]:
        # str(message["metadata"]["uid"]),"forceblock":False
        output["uid"] = str(message["metadata"]["uid"])
        output["forceblock"] = True
    if message["metadata"].get("ismuted"):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{output['friendly']}",
                "uidoverride": [getpriority(message, "uid", ["metadata", "uid"])],
            }
        )
        return False
    if MORECOLOURS == "1":
        print(f"OUTPUT[0m {'[0m, '.join([f'{x[0]}: {len(x[1])} {x[1]}' for x in output.items() if not isinstance(x[1],bool)])}")

    return {**output, "messageteam": message["metadata"]["teamint"]}


def computeauthornick(
    name,
    idauthor,
    content,
    serverid=False,
    rgbcolouroverride="DISCORD",
    colourlinksovverride="discordcolour",
    lenoverride=254,
    usetagifathing=False,
):
    """colours a nickname"""
    # print("DETAILS",name,idauthor,content,serverid,colourslink.get(idauthor,{}))
    authornick = 2
    counter = 0
    while authornick == 2 and counter < len(
        [
            RGBCOLOUR[rgbcolouroverride],
            *colourslink.get(idauthor, {}).get(
                colourlinksovverride, [RGBCOLOUR[rgbcolouroverride]]
            ),
        ]
    ):
        # print(counter)
        if not (usetagifathing and getpriority(colourslink, [idauthor, "nameprefix"])):
            authornick = gradient(
                name,
                [
                    RGBCOLOUR[rgbcolouroverride],
                    *colourslink.get(idauthor, {}).get(
                        colourlinksovverride, [RGBCOLOUR[rgbcolouroverride]]
                    )[
                        : len(
                            [
                                RGBCOLOUR[rgbcolouroverride],
                                *colourslink.get(idauthor, {}).get(
                                    colourlinksovverride, [RGBCOLOUR[rgbcolouroverride]]
                                ),
                            ]
                        )
                        - counter
                    ],
                ],
                lenoverride
                - len(f": {PREFIXES['neutral']}{content}")
                - bool(context["servers"].get(serverid, {}).get("istf1server", False))
                * tf1messagesizesubtract,
            )
        else:
            nameof, firstcolour = gradient(
                name,
                [
                    RGBCOLOUR[rgbcolouroverride],
                    *colourslink.get(idauthor, {}).get(
                        colourlinksovverride, [RGBCOLOUR[rgbcolouroverride]]
                    )[
                        : len(
                            [
                                RGBCOLOUR[rgbcolouroverride],
                                *colourslink.get(idauthor, {}).get(
                                    colourlinksovverride, [RGBCOLOUR[rgbcolouroverride]]
                                ),
                            ]
                        )
                        - counter
                    ],
                ],
                lenoverride
                - len(
                    f": {PREFIXES['neutral']}{content}"
                    + " ["
                    + colourslink[idauthor]["nameprefix"]
                    + "]"
                )
                - bool(context["servers"].get(serverid, {}).get("istf1server", False))
                * tf1messagesizesubtract,
                True,
            )
            authornick = (
                firstcolour + "[" + colourslink[idauthor]["nameprefix"] + "] " + nameof
            )
        counter += 1
    if authornick == 2:
        print("MESSAGE TOO LONG IN A WEIRD WAY, BIG PANIC")
        authornick = f"{name}"
    return authornick


# @bot.slash_command(name="bindloggingtochannel", description="Bind logging to an existing channel")
# async def bind_logging_to_channel(ctx, servername: str):
#     global context
#     # get all the server ids and names from context, and present as options
#     guild = ctx.guild
#     if guild.id == activeguild and context["categoryinfo"]["logging_cat_id"]!= 0:
#         await ctx.respond("Logging is already bound to a category.")
#         return


def recieveflaskprintrequests():
    """all tf2 communication is done here"""
    global sansthings
    app = Flask(__name__)
    if SANSURL:
        sansthings = sans(SANSURL,app,bot.loop)
    # def handle_flask_exception(e):
    #     logging.error(
    #         "Flask error during request to %s [%s]: %s",
    #         request.path,
    #         request.method,
    #         str(e),
    #         exc_info=True
    #     )
    #     return "Internal Server Error", 500
    # @app.route("/crash")
    # def crash():
    #     raise RuntimeError("bleh")
    @app.route("/checkpasswordisright", methods=["POST"])
    def checkpassword():
        print("password query recieverd")
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("not accepted")
            return {"message": "sorry, wrong pass"},400
        print("accepted")
        return {"message":"right pass"},200
    @app.route("/playerdetails", methods=["POST"])
    def getplayerdetails():
        """returns a players settings, eg should the server block messages as being modified, do they have any persistentsettings"""
        global context, discorduidnamelink
        data = request.get_json()
        now = int(time.time())
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on playerdetails")
            return {"message": "sorry, wrong pass"}
        discorduid = discorduidnamelink.get(data["uid"], False)
        playername = data.get("name", "")
        if not discorduid:
            tfdb = postgresem("./data/tf2helper.db")
            c = tfdb
            c.execute(
                "SELECT discordid FROM discordlinkdata WHERE uid = ?", (data["uid"],)
            )
            link = c.fetchone()
            if not link:
                pass
                # return {"notfound":True}
            elif link[0]:
                discorduidnamelink[data["uid"]] = link[0] if link[0] else False
                discorduid = link[0]
            else:
                pass
                # return {"notfound":True}
        # if colourslink[str(data["uid"])]:
        # print(colourslink[596713937626595382])
        # print({"output":{"shouldblockmessages":colourslink.get(discorduid,{}).get("ingamecolour",[]) != []},"uid":data["uid"],"otherdata":{x: str(y) for x,y in readplayeruidpreferences(data["uid"],False)["tf2"].items()}})
        # print("HEREEE")
        # print(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduid,{}).items()))).values()))
        # print(any(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduid,{}).items()))).values())),"e")
        # print(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduid,{}).items()))).values()))
        # print(json.dumps({"output":{"shouldblockmessages":any(map(lambda x: x[1],filter(lambda x: x[0] in ["FRIENDLY","NEUTRAL","ENEMY","nameprefix"],colourslink.get(discorduid,{}).items())))},"uid":data["uid"],"otherdata":{**({"nameprefix": colourslink[discorduid]["nameprefix"]} if getpriority(colourslink,[discorduid,"nameprefix"]) and not any(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduid,{}).items()))).values())) else {}),**{x: str(y) for x,y in list(filter(lambda x:  not getpriority(context,["commands","ingamecommands",x[0],"serversenabled"]) or int(data["serverid"]) in getpriority(context,["commands","ingamecommands",x[0],"serversenabled"])  ,readplayeruidpreferences(data["uid"],False).get("tf2",{}).items()))}}},indent=4))

        sanction, messageid = pullsanction(str(data["uid"]))
        # print(sanction)
        if sanction:
    
            sanction["expiry"] = modifyvalue(sanction["expiry"] - now,"time") if  sanction.get("expiry") and sanction["expiry"] - now < 86400*2 else sanction["humanexpire"]

            sanction = {
                "expiry": sanction["expiry"],
                "reason": sanction["reason"],
                "sanctiontype": sanction["sanctiontype"],
            }
        if playername.lower() in context["wordfilter"]["namestokick"]:
            sanction = {
                "expiry": "on name change",
                "reason": "change your name",
                "sanctiontype": "ban",
            }
        nameoverride = {}
        if resolveplayeruidfromdb(data["uid"],"uid",True) and playername == getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]) and getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]) != resolveplayeruidfromdb(data["uid"],"uid",True)[0]["name"]:
            # must override name here!
            print("THE SERVER IS USING THE WRONG NAME FOR",playername)
            nameoverride["botchangingausersnameforcefully"] = resolveplayeruidfromdb(data["uid"],"uid",True)[0]["name"]
        # elif data["actualname"] != playername and data["actualname"] != getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]) and not getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]):
        #     # the nickname has been updated! (this check does not fire always <3 oh well (it does not fire if you set name in the same match you joined))
        #     print("THE SERVER IS USING KIND OF WRONG NAME")
        #     nameoverride["nameoverride"] = resolveplayeruidfromdb(data["uid"],"uid",True)[0]["name"]
        # # print(json.dumps({"output":{"shouldblockmessages":any(map(lambda x: x[1],filter(lambda x: x[0] in ["FRIENDLY","NEUTRAL","ENEMY","nameprefix"],colourslink.get(discorduid,{}).items())))},"uid":data["uid"],"otherdata":{**({"nameprefix": colourslink[discorduid]["nameprefix"]} if getpriority(colourslink,[discorduid,"nameprefix"]) and not any(list((dict(filter(lambda x:x[0] in ["FRIENDLY","NEUTRAL","ENEMY"],colourslink.get(discorduid,{}).items()))).values())) else {}),**{x: str(y) for x,y in list(filter(lambda x: not internaltoggles.get(x[0],False) or (not getpriority(context,["commands","ingamecommands",internaltoggles[x[0]],"serversenabled"]) or int(data["serverid"]) in getpriority(context,["commands","ingamecommands",internaltoggles[x[0]],"serversenabled"]))  ,readplayeruidpreferences(data["uid"],False).get("tf2",{}).items()))},**sanction}},indent=4))
        # print(data["actualname"],playername,getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]),not  getpriority(readplayeruidpreferences(data["uid"], False),["tf2","nameoverride"]))
        # print(json.dumps(,indent=4))
        output= {
            "output": {
                "shouldblockmessages": any(
                    map(
                        lambda x: x[1],
                        filter(
                            lambda x: x[0]
                            in ["FRIENDLY", "NEUTRAL", "ENEMY", "nameprefix"],
                            colourslink.get(discorduid, {}).items(),
                        ),
                    )
                )
            },
            "uid": data["uid"],
            "otherdata": {
                
                **(
                    {"nameprefix": colourslink[discorduid]["nameprefix"]}
                    if getpriority(colourslink, [discorduid, "nameprefix"])
                    and not any(
                        list(
                            (
                                dict(
                                    filter(
                                        lambda x: x[0]
                                        in ["FRIENDLY", "NEUTRAL", "ENEMY"],
                                        colourslink.get(discorduid, {}).items(),
                                    )
                                )
                            ).values()
                        )
                    )
                    else {}
                ),
                **{
                    x: str(y)
                    for x, y in list(
                        filter(
                            lambda x:  internaltoggles.get(x[0], False) #HEH?????
                            and x[1] != "" and (not getpriority(
                                    context,
                                    [
                                        "commands",
                                        "ingamecommands",
                                        internaltoggles[x[0]],
                                        "serversenabled",
                                    ],
                                )
                                or int(data["serverid"])
                                in getpriority(
                                    context,
                                    [
                                        "commands",
                                        "ingamecommands",
                                        internaltoggles[x[0]],
                                        "serversenabled",
                                    ],
                                )
                            ) and getpriority(
                                    context,
                                    [
                                        "commands",
                                        "ingamecommands",
                                        internaltoggles[x[0]],
                                        "sendvaluetoserver",
                                    ],
                                nofind = True),
                            readplayeruidpreferences(data["uid"], False)
                            .get("tf2", {})
                            .items(),
                        )
                    )
                },
                **sanction,
                **nameoverride,
            },
        }
        # print(json.dumps(output["otherdata"],indent=4))
        # print(len(output["otherdata"]))
        # print(json.dumps(internaltoggles,indent=4))
        return output

    @app.route("/getrunningservers", methods=["POST"])
    def getrunningservers():
        """unused"""
        global discordtotitanfall
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on getrunningservers")
            return {"message": "invalid password"}
        print("getting running servers")
        output = {"message": "ok", "servers": {}}
        for key, value in discordtotitanfall.items():
            output["servers"][key] = value["lastheardfrom"]
        return output

    @app.route("/cdn/<filename>", methods=["GET"])
    def pullcdn(filename):
        """returns all pngleaderboards to discord. hosted by the bot so you can edit the links in messages to get around being unable to edit attachments"""
        global imagescdn
        # print("retrieving")
        istest = False
        try:
            filename = int(filename)
        except:
            # traceback.print_exc()
            # print(filename[0:-4])
            if filename[-4:] == "TEST":
                filename = filename[0:-4]
                istest = True
            else:
                print("Only ints are allowed", filename)
                return send_from_directory("./data", "bunny.png")

        if int(filename) not in imagescdn:
            print("Error getting image", filename, list(imagescdn.keys()))
            return send_from_directory("./data", "bunny.png")
        elif istest:
            # print("test sucsess")
            return {"message": "Image might exist"}, 200
        image_data = imagescdn[filename]
        image_data.seek(0)
        cloned = BytesIO(image_data.read())
        cloned.seek(0)
        # del imagescdn[filename]
        if len(imagescdn.keys()) > 30:
            del imagescdn[list(imagescdn.keys())[0]]
        # print("returning file",filename)
        return send_file(cloned, mimetype="image/png")

    @app.route("/stoprequests", methods=["POST"])
    def stoprequests():
        global stoprequestsforserver, messageflush
        data = getjson(request.get_json())
        # print(json.dumps(data,indent=4))
        # print("STOP REQUESTS REQUESTED PANIC")
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on stoprequests")
            return {"message": "invalid password"}
        data["serverid"] = str(data["serverid"])
        initdiscordtotitanfall(data["serverid"])
        print("stopping requests for", data["serverid"])
        # print("REALLY STOPPING REQUESTS")

        output = ""
        try:
            pass
            if data.get("command", False):
                # print("ASKING TO SEND ENDOFSTATS")
                output = tftodiscordcommand(
                    data["command"],
                    data.get("paramaters", False),
                    str(data["serverid"]),
                )
        except:
            traceback.print_exc()
            pass
        # print("ASKING SERVER TO STOP")
        try:
            printduelwinnings(data["serverid"])
        except:
            print("errord")
            traceback.print_exc()
        if not data.get("dontdisablethings"):
            stoprequestsforserver[data["serverid"]] = True
            try:
                messageflush.append(
                    {
                        "timestamp": int(time.time()),
                        "serverid": data["serverid"],
                        "type": 4,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": f"Stopping discord -> Titanfall communication for {context['servers'][data['serverid']]['name']} till next map (to prevent server crash)"
                        + str(
                            output
                        ),  # it should always be a string, but I don't trust it
                        "metadata": {"type": "stoprequestsnotif"},
                        "servername": context["servers"][data["serverid"]]["name"],
                    }
                )
            except Exception as e:
                print([data["serverid"]])
                traceback.print_exc()
        # print("here")
        return {"message": "ok"}

    # @app.route("/stoprequests", methods=["POST"])
    # def stoprequests():
    #     global stoprequestsforserver,messageflush
    #     data = request.get_json()
    #     if data["password"] != SERVERPASS and SERVERPASS != "*":
    #         print("invalid password used on stoprequests")
    #         return {"message": "invalid password"}
    #     # serverid = data["serverid"]
    #     print([data["serverid"]])
    #     print("stopping requests for", data["serverid"])
    #     try:
    #         messageflush.append({
    #             "timestamp": int(time.time()),
    #             "serverid": data["serverid"],
    #             "type": 4,
    #             "globalmessage": False,
    #             "overridechannel": None,
    #             "messagecontent": f"Stopping discord -> Titanfall communication for {context['serveridnamelinks'][data['serverid']]} till next map (to prevent server crash)",
    #             "metadata": {"type":"stoprequestsnotif"},
    #             "servername": context["serveridnamelinks"][data["serverid"]]
    #         })
    #     except:pass
    #     # print()
    #     stoprequestsforserver[data["serverid"]] = True
    #     return {"message": "ok"}

    @app.route("/askformessage", methods=["POST"])
    def askformessage():
        global context, discordtotitanfall
        data = request.get_json()
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on askformessage")
            time.sleep(30)
            return {
                "message": "invalid password",
                "texts": {},
                "commands": {},
                "time": "0",
            }
        serverid = data["serverid"]
        initdiscordtotitanfall(serverid)
        if "commands" in data.keys():
            for key, value in data["commands"].items():
                # print(value,json.dumps(getjson(value),indent=4))
                discordtotitanfall[serverid]["returnids"]["commandsreturn"][key] = (
                    getjson(value)
                )
        ids = list(data.keys())
        if "time" in data.keys():
            timesent = int(data["time"])
            # print(timesent, discordtotitanfall[serverid]["returnids"]["messages"].keys())
            if timesent in discordtotitanfall[serverid]["returnids"]["commands"].keys():
                del discordtotitanfall[serverid]["returnids"]["commands"][timesent]
            if timesent in discordtotitanfall[serverid]["returnids"]["messages"].keys():
                del discordtotitanfall[serverid]["returnids"]["messages"][timesent]
        if len(data.keys()) > 2:
            pass
            # realprint(json.dumps(data, indent=4))
        # print("IDSTOREACTTOO",ids)
        asyncio.run_coroutine_threadsafe(reactomessages(list(ids), serverid), bot.loop)
        if serverid not in stoprequestsforserver.keys():
            stoprequestsforserver[serverid] = False
        timer = 0
        while timer < 50 and (
            not stoprequestsforserver[serverid]
            or discordtotitanfall[serverid]["messages"] != []
        ):
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
                for i in range(len(discordtotitanfall[serverid]["messages"])):
                    discordtotitanfall[serverid]["messages"][i]["id"] = (
                        discordtotitanfall[serverid]["messages"][i].get(
                            "id", str(random.randint(1, 100000000000))
                        )
                    )
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
                textsv2 = {
                    str(i): {
                        "content": value["content"],
                        "validation": str(value["id"]),
                        "teamoverride": value.get("teamoverride", 4),
                        "isteammessage": value.get("isteammessage", False),
                        "uidoverride": ",".join(
                            list(map(lambda x: str(x), value.get("uidoverride", [])))
                        )
                        if not isinstance(value.get("uidoverride", []), (str, int))
                        else f"{value.get('uidoverride', [])}",
                    }
                    for i, value in enumerate(discordtotitanfall[serverid]["messages"])
                }
                textsv3 = packfortextsv3(discordtotitanfall[serverid]["messages"])
                discordtotitanfall[serverid]["messages"] = []
                discordtotitanfall[serverid]["commands"] = []
                now = int(time.time() * 100)
                if len(textvalidation) > 0:
                    discordtotitanfall[serverid]["returnids"]["messages"][now] = (
                        textvalidation
                    )
                if len(sendingcommands) > 0:
                    # print("true")
                    discordtotitanfall[serverid]["returnids"]["commands"][now] = (
                        sendingcommandsids
                    )
                # print(json.dumps(discordtotitanfall, indent=4))
                # print("sending messages and commands to titanfall", texts, sendingcommands)
                # print({a: b for a, b in zip(texts, textvalidation)})
                # print((texts), (textvalidation))
                # print("REALLY STOPPING")
                # if textsv3:
                #     print(json.dumps(textsv3,indent=1))
                return {
                    "texts": dict(zip(textvalidation, texts)),
                    "textsv2": textsv2,
                    # "texts": "%&%&".join(texts),
                    "commands": 
                        dict(zip(sendingcommandsids, sendingcommands))
                    ,
                    # "textvalidation": "%&%&".join(textvalidation),
                    "textsv3": textsv3,
                    "time": str(now),
                }
            time.sleep(0.2)
        stoprequestsforserver[serverid] = False
        # print("STOPPING")
        return {"texts": {}, "commands": {}, "time": "0", "textsv2": {}, "textsv3": {}}

    @app.route("/runcommand", methods=["POST"])
    def runcommandforserver():
        data = getjson(request.get_json())
        # print("PLEASE RUN A COMMAND FOR ME")
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            return {"message": "wrong pass"}
        tftodiscordcommand(data["command"], data["paramaters"], str(data["serverid"]))
        return {"message": "ran command"}

    # @app.route("/autobalancedata", methods=["POST", "GET"])
    # def pullautobalancestats():
    #     if request.method == "POST":
    #         data = getjson(request.get_json())
    #         uids =  list(map(lambda x: int(x),data["players"].keys()))#list(map(lambda x: x["uid"], data["players"]))
    #     else:
    #         return
    #     placeholders = ','.join(['?'] * len(uids))

    # compute stats for the player!
    # len(x[0]) > 15

    # step one, check the len of the discorduid
    @app.route("/duels/<playername>", methods=["GET"])
    def getduelsinaprettyapi(playername):
        istf1 = bool(request.args.get("istf1",False) )
        
        person = resolveplayeruidfromdb(playername,None,True,istf1)
        if not person:
            return {"message":"no one found"} , 404
        person = person[0]
        things = pullduelstats(person["uid"],istf1=istf1)
        return things


    @app.route("/playtime/<playername>", methods=["GET"])
    def getplayerplaytimeinaprettyapi(playername):
        serverid = int(request.args.get("serverid", 0))
        istf1 = bool(request.args.get("istf1",False) )
        
        person = resolveplayeruidfromdb(playername,None,True,istf1)
        if not person:
            return {"message":"no one found"} , 404
        person = person[0]
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        if  not serverid:
            c.execute(f"SELECT matchid, serverid,time,map FROM matchid{"tf1" if istf1 else ""}")
        else:
            c.execute(f"SELECT matchid, serverid,time ,map FROM matchid{"tf1" if istf1 else ""} WHERE serverid = ?",(serverid,))
        # matchids = list(map(lambda x: {"matchid":x[0],"serverid":x[1]} ,c.fetchall()))
        matchids = {}
        matchtimestamplink = {}
        for entry in c.fetchall():
            matchids.setdefault(entry[1],[]).append(entry[0])
            matchtimestamplink[entry[0]] = {"timestamp":entry[2],"map":entry[3]}


        if not serverid:
            c.execute(f"SELECT joinatunix,leftatunix,duration, matchid, serverid  FROM playtime{"tf1" if istf1 else ""} WHERE playeruid = ?",(person["uid"],))
        else:
            c.execute(f"SELECT joinatunix,leftatunix,duration, matchid, serverid FROM playtime{"tf1" if istf1 else ""} WHERE playeruid = ? AND serverid = ?",(person["uid"],serverid))
        # serverid -> matchid
        realplaytime =list( map(lambda x:  {**x[1],"duration":x[1]["leftatunix"] -x[1]["joinatunix"] } if len(reduceoutput) == x[0] + 1 or matchids[x[1]["serverid"]].index(x[1]["matchid"]) + 1 >= len(matchids[x[1]["serverid"]]) or matchids[x[1]["serverid"]][matchids[x[1]["serverid"]].index(x[1]["matchid"]) + 1] != reduceoutput[x[0]+1]["matchid"] else {**x[1],"duration":matchtimestamplink[matchids[x[1]["serverid"]][matchids[x[1]["serverid"]].index(x[1]["matchid"]) + 1]]["timestamp"] -x[1]["joinatunix"],"leftatunix":matchtimestamplink[matchids[x[1]["serverid"]][matchids[x[1]["serverid"]].index(x[1]["matchid"]) + 1]]["timestamp"]} , enumerate(reduceoutput:= functools.reduce(lambda a,b: ([*a,{**b,"joinatunix":matchtimestamplink[b["matchid"]]["timestamp"],"map":matchtimestamplink[b["matchid"]]["map"]}] if not len(a) or a[-1]["matchid"] != b["matchid"] else [*a[:-1],{**a[-1],"leftatunix":b["leftatunix"]}]) ,list(map(lambda x: {"joinatunix":x[0],"leftatunix":x[1],"duration":x[2],"matchid":x[3],"serverid":x[4],"servername":context["servers"].get(str(x[4]),{"name":"Unknown server"})["name"]} ,c.fetchall())),[]))))
        # format = [{"started":timestamp,"stopped":timestamp,"serverid":serverid,"matchid":matchid}]
        return realplaytime
    @app.route("/players/<playeruid>", methods=["GET", "POST"])
    def getplayerstats(playeruid):
        return getstats(playeruid)

    # @app.route("/players/<playeruid>", methods=["GET", "POST"])
    # def getplayerstats(playeruid):
    #     tfdb = postgresem("./data/tf2helper.db")
    #     c = tfdb
    #     try:
    #         output = resolveplayeruidfromdb(playeruid, None, True)[0]
    #         name = output["name"]
    #         playeruid = output["uid"]
    #     except:
    #         name = "unknown"
    #         return {"sob": "sobbing Unknown player"}, 404

    #     messages = {}
    #     output = {"name": name, "uid": str(playeruid), "total": {}}
    #     now = datetime.now()
    #     one_week_ago = int((now - timedelta(days=7)).timestamp())

    #     # Total deaths
    #     c.execute("SELECT COUNT(*) FROM specifickilltracker WHERE victim_id = ?", (playeruid,))
    #     total_deaths = float(c.fetchone()[0] or 0)
    #     # Recent deaths (past week)
    #     c.execute("SELECT COUNT(*) FROM specifickilltracker WHERE victim_id = ? AND timeofkill >= ?",
    #             (playeruid, one_week_ago))
    #     recent_deaths = float(c.fetchone()[0] or 0)
    #     # Total kills
    #     c.execute("SELECT COUNT(*) FROM specifickilltracker WHERE playeruid = ?", (playeruid,))
    #     total_kills = float(c.fetchone()[0] or 0)
    #     # Recent kills (past week)
    #     c.execute("SELECT COUNT(*) FROM specifickilltracker WHERE playeruid = ? AND timeofkill >= ?",
    #             (playeruid, one_week_ago))
    #     recent_kills = float(c.fetchone()[0] or 0)

    #     # KD ratio calculations
    #     kd = round(total_kills / total_deaths, 2) if total_deaths else round(total_kills, 2)
    #     recent_kd = round(recent_kills / recent_deaths, 2) if recent_deaths else round(recent_kills, 2)
    #     kd_difference = round(recent_kd - kd, 2)

    #     # Top 3 weapons with recent kills
    #     c.execute("""
    #         SELECT cause_of_death, COUNT(*) as kill_count
    #         FROM specifickilltracker
    #         WHERE playeruid = ?
    #         GROUP BY cause_of_death
    #         ORDER BY kill_count DESC
    #         LIMIT 3
    #     """, (playeruid,))
    #     top_weapons = []
    #     for weapon in c.fetchall():
    #         weapon_name = weapon[0]
    #         total_weapon_kills = float(weapon[1])
    #         # Recent kills for this weapon
    #         c.execute("""
    #             SELECT COUNT(*)
    #             FROM specifickilltracker
    #             WHERE playeruid = ?
    #             AND cause_of_death = ?
    #             AND timeofkill >= ?
    #         """, (playeruid, weapon_name, one_week_ago))
    #         output["total"]["recent_weapon_kills"] = float(c.fetchone()[0] or 0)
    #         top_weapons.append((weapon_name, total_weapon_kills, output["total"]["recent_weapon_kills"]))

    #     # Most recent weapon
    #     c.execute("""
    #         SELECT cause_of_death
    #         FROM specifickilltracker
    #         WHERE playeruid = ?
    #         ORDER BY timeofkill DESC
    #         LIMIT 1
    #     """, (playeruid,))
    #     recent_weapon = c.fetchone()
    #     recent_weapon_data = None
    #     if recent_weapon:
    #         weapon_name = recent_weapon[0]
    #         # Total kills with this weapon
    #         c.execute("""
    #             SELECT COUNT(*)
    #             FROM specifickilltracker
    #             WHERE playeruid = ? AND cause_of_death = ?
    #         """, (playeruid, weapon_name))
    #         total_weapon_kills = float(c.fetchone()[0] or 0)
    #         # Recent kills for this weapon
    #         c.execute("""
    #             SELECT COUNT(*)
    #             FROM specifickilltracker
    #             WHERE playeruid = ?
    #             AND cause_of_death = ?
    #             AND timeofkill >= ?
    #         """, (playeruid, weapon_name, one_week_ago))
    #         output["total"]["recent_weapon_kills"] = float(c.fetchone()[0] or 0)
    #         recent_weapon_data = (weapon_name, total_weapon_kills, output["total"]["recent_weapon_kills"])

    #     # Playtime and KPH
    #     c.execute("""
    #         SELECT
    #             COALESCE(SUM(duration), 0) AS total_time_playing,
    #             COALESCE(SUM(pilotkills), 0) AS total_pilot_kills
    #         FROM playtime
    #         WHERE playeruid = ?
    #     """, (playeruid,))
    #     kph_data = c.fetchone()
    #     total_playtime = float(kph_data[0] if kph_data else 0)
    #     total_kph_kills = float(kph_data[1] if kph_data else 0)
    #     # Recent playtime and kills (past week)
    #     c.execute("""
    #         SELECT
    #             COALESCE(SUM(duration), 0) AS recent_playtime,
    #             COALESCE(SUM(pilotkills), 0) AS recent_kills
    #         FROM playtime
    #         WHERE playeruid = ? AND joinatunix >= ?
    #     """, (playeruid, one_week_ago))
    #     recent_kph_data = c.fetchone()
    #     recent_playtime = float(recent_kph_data[0] if recent_kph_data else 0)
    #     recent_kph_kills = float(recent_kph_data[1] if recent_kph_data else 0)

    #     # Calculate KPH values
    #     all_time_kph = round(total_kph_kills / (total_playtime / 3600), 2) if total_playtime else 0.0
    #     past_week_kph = round(recent_kph_kills / (recent_playtime / 3600), 2) if recent_playtime else 0.0
    #     kph_difference = round(past_week_kph - all_time_kph, 2)

    #     # Format time played (as hours and minutes)
    #     def format_time(seconds):
    #         hours = int(seconds // 3600)
    #         mins = int((seconds % 3600) // 60)
    #         return f"{hours}h {mins}m"

    #     # Color selection
    #     while True:
    #         colour = random.randint(0, 255)
    #         if colour not in DISALLOWED_COLOURS:
    #             break

    #     # Formatting function to omit trailing zeros
    #     def fmt(val):
    #         if isinstance(val, float):
    #             return f"{val:.2f}".rstrip('0').rstrip('.') if '.' in f"{val:.2f}" else str(int(val))
    #         return str(val)

    #     def format_stat(total, recent, is_positive=True, is_ratio=False, is_time=False):
    #         if is_ratio:
    #             sign = "+" if recent >= 0 else ""
    #             color_code = 46 if recent >= 0 else 196
    #             return f"{PREFIXES['stat']}{fmt(total)}{PREFIXES['chatcolour']} ([38;5;{color_code}m{sign}{fmt(recent)}[0m)"
    #         if is_time:
    #             color_code = 46 if is_positive else 196
    #             if recent > 0:
    #                 return f"{PREFIXES['stat']}{format_time(total)}{PREFIXES['chatcolour']} [38;5;{color_code}m+{format_time(recent)}[0m"
    #             return f"{PREFIXES['stat']}{format_time(total)}{PREFIXES['chatcolour']}"
    #         color_code = 46 if is_positive else 196
    #         if recent > 0:
    #             return f"{PREFIXES['stat']}{fmt(total)}{PREFIXES['chatcolour']} [38;5;{color_code}m+{fmt(recent)}[0m"
    #         return f"{PREFIXES['stat']}{fmt(total)}{PREFIXES['chatcolour']}"

    #     # Main stats message
    #     messages["0"] = (
    #         f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} has "
    #         f"{format_stat(total_kills, recent_kills)} kills and "
    #         f"{format_stat(total_deaths, recent_deaths, False)} deaths "
    #         f"(KD: {format_stat(kd, kd_difference, is_ratio=True)}, "
    #         f"KPH: {format_stat(all_time_kph, kph_difference, is_ratio=True)} k/hour, "
    #         f"{format_stat(total_playtime, recent_playtime, is_time=True)} playtime)"
    #     )

    #     # Top 3 weapons
    #     colourcodes = ["[38;5;226m", "[38;5;251m", "[38;5;208m"]
    #     top3guns = ""
    #     for enum, weapon in enumerate(top_weapons):
    #         weapon_name = WEAPON_NAMES.get(weapon[0], weapon[0])
    #         stat_str = format_stat(weapon[1], weapon[2])
    #         top3guns += (
    #             f"[38;5;{colour}m{enum+1}) {colourcodes[enum]}{weapon_name}{PREFIXES['chatcolour']} kills: "
    #             f"{stat_str}   "
    #         )
    #     if top3guns:
    #         messages["1"] = top3guns

    #     # Most recent weapon
    #     if recent_weapon_data:
    #         weapon_name = WEAPON_NAMES.get(recent_weapon_data[0], recent_weapon_data[0])
    #         stat_str = format_stat(recent_weapon_data[1], recent_weapon_data[2])
    #         messages["2"] = (
    #             f"[38;5;{colour}mMost recent weapon: "
    #             f"{PREFIXES['stat']}{weapon_name}{PREFIXES['chatcolour']} kills: {stat_str}"
    #         )

    #     tfdb.close()
    #     return {**output, **messages}
    
    @app.route("/data", methods=["POST"])
    def onkilldata(data = None):
        # takes input directly from (slightly modified) nutone (https://github.com/nutone-tf) code for this to work is not on the github repo, so probably don't try using it.
        global context, messageflush, consecutivekills, lexitoneapicache, maxkills
        if not data:
            data = request.get_json()
        
            if data["password"] != SERVERPASS and SERVERPASS != "*"  :
                print("invalid password used on data")
                return {"message": "invalid password"}
        realonkilldata(data)
        return {"message":"ok"}


    @app.route("/servermessagein", methods=["POST"])
    def printmessage():
        global messageflush, lastmessage, messagecounter, context
        data = request.get_json()
        addtomessageflush = True
        if data["password"] != SERVERPASS and SERVERPASS != "*":
            print("invalid password used on printmessage")
            return {"message": "invalid password"}
        newmessage = {}
        if context["categoryinfo"]["logging_cat_id"] == 0:
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
            data["type"] += 2  # set the type to a one that does not need a player
        newmessage["serverid"] = data["serverid"]
        newmessage["type"] = data["type"]
        newmessage["timestamp"] = data["timestamp"]
        newmessage["globalmessage"] = (
            data["globalmessage"] if "globalmessage" in data.keys() else False
        )
        newmessage["overridechannel"] = (
            data["overridechannel"] if data["overridechannel"] != "None" else None
        )
        if newmessage["overridechannel"] is not None:
            newmessage["globalmessage"] = True
        elif newmessage["globalmessage"] == True:
            newmessage["overridechannel"] = "globalchannel"
        if (
            newmessage["overridechannel"]
            and newmessage["overridechannel"] not in context["overridechannels"].keys()
        ):
            print(
                "invalid override channel, valid channels are",
                context["overridechannels"].keys(),
                "not",
                newmessage["overridechannel"],
            )
            newmessage["overridechannel"] = None
            newmessage["globalmessage"] = False
            addtomessageflush = False
        elif (
            newmessage["globalmessage"]
            and newmessage["overridechannel"] not in context["overridechannels"].keys()
        ):
            print("Override channel is not bound to a channel")
            newmessage["overridechannel"] = None
            newmessage["globalmessage"] = False
            addtomessageflush = False
        newmessage["messagecontent"] = data["messagecontent"].strip()
        if not newmessage["globalmessage"]:
            pass
            # print("message request from", newmessage["serverid"], newmessage["servername"])
        else:
            pass
            # print("global message request from", newmessage["serverid"], newmessage["servername"],"True" if addtomessageflush else "False")
        newmessage["metadata"] = {"type": None}
        # print(list(data.keys()))
        if "metadata" in data.keys() and data["metadata"] != "None":
            data["metadata"] = getjson(data["metadata"])
            newmessage["metadata"] = data["metadata"]
            if data["metadata"]["type"] == "connect":
                onplayerjoin(data["metadata"]["uid"], data["serverid"], data["player"])
            elif data["metadata"]["type"] == "disconnect":
                onplayerleave(data["metadata"]["uid"], data["serverid"])
        if addtomessageflush:
            # print(json.dumps(newmessage,indent =4))

            try:
                returnable = colourmessage(newmessage, data["serverid"])
            except:
                returnable = False
                traceback.print_exc()
            messageflush.append(newmessage)
        messagecounter += 1
        lastmessage = time.time()

        if newmessage["serverid"] not in context["servers"]:
            context["servers"][newmessage["serverid"]] = {
                "name": newmessage["servername"],
                "istf1server": False,
            }
            savecontext()

        if (
            newmessage["serverid"] not in context["servers"]
            or "channelid" not in context["servers"][newmessage["serverid"]]
        ):
            # Get guild and category
            guild = bot.get_guild(context["categoryinfo"]["activeguild"])
            category = guild.get_channel(context["categoryinfo"]["logging_cat_id"])
        if returnable:
            return {"message": "success", **returnable}
        return {"message": "success"}
    CORS(app, resources={r"/*": {"origins": "*"}})
    serve(app, host="0.0.0.0", port=PORT, threads=40, connection_limit=200)  # prod
    # app.run(host="0.0.0.0", port=3451)  #dev


async def createchannel(guild, category, servername, serverid):
    global context
    print("Creating channel...")
    normalized_servername = servername.lower().replace(" ", "-")
    # check if channel name already exists, if so use that
    if any(
        normalized_servername == channel.name.lower() for channel in category.channels
    ):
        channel = discord.utils.get(category.channels, name=normalized_servername)
        if serverid not in context["servers"]:
            context["servers"][serverid] = {}
        context["servers"][serverid]["channelid"] = channel.id
        context["servers"][serverid]["roles"] = {
                "rconrole": "rconrole",
                "coolperksrole": "coolperksrole"
            }
        context["servers"][serverid]["ishidden"] = False
        savecontext()
        return
    channel = await guild.create_text_channel(servername, category=category)
    if serverid not in context["servers"]:
        context["servers"][serverid] = {}
    context["servers"][serverid]["channelid"] = channel.id
    context["servers"][serverid]["roles"] = {
            "rconrole": "rconrole",
            "coolperksrole": "coolperksrole"
        }
    context["servers"][serverid]["ishidden"] = False

    savecontext()
    await hideandshowchannels(serverid,True)

async def reactomessages(messages, serverid, emoji="🟢"):
    # print(messages,"wqdqw")
    for message in messages:
        # print("run")
        if (
            message == "serverid"
            or message == "commands"
            or message == "time"
            or message == "password"
        ):
            continue
        # print("run2")
        # print(message,"owo")
        message = await bot.get_channel(
            context["servers"][serverid]["channelid"]
        ).fetch_message(int(message))
        # print("reacting to message")
        # if the bot has reacted with "🔴" remove it.
        # if "🔴" in [reaction.emoji for reaction in message.reactions] or "🟡" in [reaction.emoji for reaction in message.reactions]:
        #     await message.clear_reactions()
        await message.add_reaction(emoji)


async def changechannelname(guild, servername, serverid):
    global context
    print("Changing channel name...")
    channel = guild.get_channel(context["servers"][serverid]["channelid"])
    await channel.edit(name=servername)
    if serverid not in context["servers"]:
        context["servers"][serverid] = {}
    context["servers"][serverid]["name"] = servername
    context["servers"][serverid]["widget"] = False
    context["servers"][serverid]["roles"] = {
        "rconrole": "rconrole",
        "coolperksrole": "coolperksrole",
    }
    savecontext()

    # return channel


def get_ordinal(i):  # Shamelessly stolen
    SUFFIXES = {1: "st", 2: "nd", 3: "rd"}
    # Adapted from https://codereview.stackexchange.com/questions/41298/producing-ordinal-numbers
    if 10 <= i % 100 <= 20:
        return "th"
    else:
        return SUFFIXES.get(i % 10, "th")


def getmessagewidget(metadata, serverid, messagecontent, message):
    """Processes and formats game messages for Discord display with player status and team info"""
    global context
    output = messagecontent
    player = str(message.get("player", "Unknown player"))

    if getpriority(
        colourslink,
        [
            discorduidnamelink.get(getpriority(message, ["metadata", "uid"]), False),
            "nameprefix",
        ],
    ):
        player = f"[{colourslink[discorduidnamelink.get(getpriority(message, ['metadata', 'uid']), False)]['nameprefix']}] {player}"
    # print("metadata",metadata)
    if metadata.get("teamtype", "not team") != "not team":
        player = f"{player} {metadata.get('teamtype', 'not team')}"
    if metadata.get("isalive", "unknown") != "unknown" and not metadata.get(
        "isalive", "unknown"
    ):
        player = f"{player} [DEAD]"
    if metadata.get("forcedprefix", False):
        player = f"{metadata["forcedprefix"]} {player}"
    if metadata.get("ismuted", False):
        player = f"{player} [MUTED BY SANCTION]"

    if not metadata["type"]:
        pass
    elif metadata["type"] == "impersonate" and SHOWIMPERSONATEDMESSAGESINDISCORD == "1":
        player = f"{player} [IMPERSONATED]"
    elif metadata["type"] == "connect" and DISCORDBOTLOGSTATS == "1":
        pass
        uid = metadata["uid"]
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute(
            "SELECT count FROM joincounter WHERE playeruid = ? AND serverid = ?",
            (uid, serverid),
        )
        data = c.fetchone()
        c.execute(
            "SELECT leftatunix,joinatunix FROM playtime WHERE playeruid = ? AND serverid = ?",
            (uid, serverid),
        )
        data2 = c.fetchall()

        if data:
            data = data[0]
            output += f"\n({data}{ANSI_COLOURS["cyan"]}{get_ordinal(data)}{ANSI_COLOURS["reset"]} time joining"
            if data2:
                data2 = sum(list(map(lambda x: x[0] - x[1], data2)))
                output += f" - {data2 // 3600}h {data2 // 60 % 60}m time playing"
            output += ")"
        try:
            if getpriority(message, ["metadata", "uid"]):
                # print(getpriority(message,["metadata","uid"]))
                sanction = process_matchingtf2(
                    getpriority(message, ["metadata", "uid"])
                )
                if sanction and not isinstance(sanction, str):
                    # asyncio.run_coroutine_threadsafe(channel.fetch_message(leaderboardid), bot.loop)
                    channel = (
                        bot.get_channel(context["servers"][serverid]["channelid"])
                        if (
                            serverid in context["servers"]
                            and "channelid" in context["servers"][serverid]
                        )
                        else bot.get_channel(context["overridechannels"][serverid])
                    )
                    # print(channel,channel.name,sanction)
                    asyncio.run_coroutine_threadsafe(
                        channel.send(
                            embed=embedjson(f"Sanction enforced for {player}", sanction)
                        ),
                        bot.loop,
                    )
            if str(message.get("player", "Unknown player")).lower() in context["wordfilter"]["namestokick"]:
                    asyncio.run_coroutine_threadsafe(
                        channel.send(
                            (f"Name rule enforced for {player} (change your name)")
                        ),
                        bot.loop,
                    )
        except Exception as e:
            traceback.print_exc()
            print(e)
    elif metadata["type"] in ["command", "botcommand", "tf1command"]:
        if DISCORDBOTLOGCOMMANDS != "1":
            return "", player
        output = f"""> {context["servers"].get(serverid, {}).get("name", "Unknown server").ljust(30)} {(message["player"] + ":").ljust(20)} {message["messagecontent"]}"""
    # elif metadata["type"] == "tf1command":
    #     if DISCORDBOTLOGCOMMANDS != "1":
    #         return "",player
    #     output = f"""> {context['serveridnamelinks'].get(serverid,'Unknown server').ljust(50)} {message['messagecontent']}"""

    elif metadata["type"] == "disconnect":
        pass
    return output, player


def filterquotes(inputstr):
    return re.sub(
        r"(?<!\\)\\(?!\\)",
        r"\\\\",
        inputstr.replace('"', "'")
        .replace("wqdwqqwdqwdqwdqw$", "")
        .replace("\n", r"\n"),
    )


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
tf1servercontext = {}

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


def interpstatus(log):
    """for use with "status" command"""
    m = re.search(r"map\s*:\s*(\S+)", log)
    map_name = m.group(1) if m else None
    players = {}
    for line in log.splitlines():
        if "#" in line and '"' in line:
            m1 = re.search(r'#\s*(\d+)\s+\d+\s+"([^"]+)"', line)
            if not m1:
                continue
            userid, name = m1.group(1), m1.group(2)
            m2 = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?=\[)", line)
            ip = m2.group(1) if m2 else None

            players[userid] = {"name": name, "ip": ip}

    return {"map": map_name, **players}


def tf1readsend(serverid, checkstatus):
    """all discord <-> tf1 comms go through here"""
    # don't even bother trying to send anything or read anything if the server is offline!
    global discordtotitanfall, context, reactedyellowtoo, titanfall1currentlyplaying

    commands = {}
    offlinethisloop = False
    now = int(
        (time.time()) * 100
    )  # increased by 8 seconds, to increase the time it takes for a yellow dot to be reacted
    for command in list(discordtotitanfall[serverid]["commands"]):
        command = {**command}
        if command["command"][0] != "!":
            commands[command["id"]] = {
                "type": "rcon",
                "command": command["command"],
                "id": command["id"],
            }
            continue
        # print(command)
        command["command"] = command["command"][1:]
        command["command"] = command["command"].split(" ")
        # print("COMMAND",command)
        commands[command["id"]] = {
            "type": "rpc",
            "command": command["command"][0],
            "id": command["id"],
            "args": command["command"][1:],
        }
    inputstring = {}
    if discordtotitanfall[serverid]["lastheardfrom"] > int(time.time()) - 6:
        # if discordtotitanfall[serverid].get("serveronline",False):

        # print("HERHE",discordtotitanfall[serverid]["messages"])
        # print(discordtotitanfall)
        messages = False
        toolongmessages = []
        for message in discordtotitanfall[serverid]["messages"]:
            messages = True
            message["id"] = message.get("id", str(random.randint(0, 9999999)))
            if (
                str(message["id"])
                in discordtotitanfall[serverid]["returnids"]["messages"].keys()
            ):
                continue  # TRADEOFF HERE. EITHER I SEND IT EACH RCON CALL (and don't update the timestamp) OR I do what I do here and only send it once, wait untill yellow dot cleaner comes, then send again.
            if len(message["content"]) > tf1messagesizeadd:
                toolongmessages.append(message["id"])
            commands[message["id"]] = {
                "type": "msg",
                "command": "sendmessage",
                "id": message["id"],
                "args": (
                    f"{"placeholder" if not message.get('uidoverride', []) else ""}{','.join(list(map(lambda x: str(x), message.get('uidoverride', [])))) if not isinstance(message.get('uidoverride', []), (str, int)) else f'{message.get("uidoverride", [])}'}"
                )
                + " "
                + (message["content"][0:tf1messagesizeadd]),
            }
        if (
            len(discordtotitanfall[serverid]["returnids"]["messages"].keys()) != -1
            and messages
        ):  # and discordtotitanfall[serverid]["serveronline"]:
            for messageid in list(
                map(
                    lambda x: str(x["id"]),
                    list(
                        filter(lambda x: True, discordtotitanfall[serverid]["messages"])
                    ),
                )
            ):
                discordtotitanfall[serverid]["returnids"]["messages"].setdefault(
                    messageid, [now]
                )
            # print("RETURNIDS",discordtotitanfall[serverid]["returnids"]["messages"])
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
        with Client(
            discordtotitanfall[serverid]["ip"].rsplit(":", 1)[0],
            int(discordtotitanfall[serverid]["ip"].rsplit(":", 1)[1]),
            passwd=TF1RCONKEY,
            timeout=2,
        ) as client:
            if checkstatus or len(commands) > 0 or True:
                client.run("sv_cheats", "1")
            if checkstatus:
                # playingpollidentity
                statusoutput = client.run("script", 'Lrconcommand("playingpoll")')
                # print("Here")
                # print(statusoutput)
                if "OUTPUT<" in statusoutput and "/>ENDOUTPUT" in statusoutput:
                    # print("STATUS",statusoutput)
                    statusoutput = "".join(
                        "".join(
                            "".join(statusoutput.split("BEGINMAINOUT", 1)[1]).split(
                                "OUTPUT<", 1
                            )[1]
                        ).rsplit("/>ENDOUTPUT", 1)[0]
                    )
                    # statusoutput = statusoutput.replace("☻",'"')
                    statusoutput = getjson(statusoutput)
                    # print(statusoutput)
                    # print(json.dumps(statusoutput,indent=4))
                else:
                    titanfall1currentlyplaying[serverid] = []
                # print((statusoutput))
                peopleonserver = len(statusoutput.keys()) - 1
                titanfall1currentlyplaying[serverid] = [
                    statusoutput[x][0]
                    for x in list(filter(lambda x: x != "meta", statusoutput.keys()))
                ]
                # print("ONLINE",serverid,"ONLINE",bool (len(statusoutput.keys()) -1),statusoutput)

                if not discordtotitanfall[serverid].get("serveronline") and not (
                    len(statusoutput.keys()) - 1
                ):
                    # print("MEOW")
                    offlinethisloop = True
                    # return
                discordtotitanfall[serverid]["serveronline"] = bool(
                    len(statusoutput.keys()) - 1
                )
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
                # print("sending messages and commands to tf1",commands)

                for w, command in commands.items():
                    # print(json.dumps(command,indent=4))
                    otherquotemark = "'"
                    quotationmark = '"'
                    if command["type"] == "rcon":
                        # print("beep boop")
                        inputstring[command["id"]] = client.run(
                            *command["command"].split(" ")
                        )
                        # print("I managed it!")
                        # print(inputstring[command["id"]])
                        continue

                    # print("BEEP BOOP",filterquotes("".join(command["args"])))
                    # print("CMDARGS",[command["args"]])
                    # print("CMDARGS", "[" + otherquotemark + (otherquotemark + "," + otherquotemark.join(command["args"].split(" ")) + otherquotemark)if isinstance(command["args"], str) else "[" + ",".join(f"{otherquotemark}{arg}{otherquotemark}" for arg in command["args"]) + "]")
                    if command["command"] != "playingpoll":
                        pass
                        # print("script", f'Lrconcommand("{filterquotes(command["command"])}"{","+quotationmark+filterquotes("".join(command["args"]) if isinstance(command["args"], str) else " ".join(command["args"]))+quotationmark if "args" in command.keys() else "" },"{command["id"] }")')
                    inputstring[command["id"]] = client.run(
                        "script",
                        f'Lrconcommand("{filterquotes(command["command"])}"{"," + quotationmark + filterquotes("".join(command["args"]) if isinstance(command["args"], str) else " ".join(command["args"])) + quotationmark if "args" in command.keys() else ""},"{command["id"]}")',
                    )  # {","+quotationmark+filterquotes(command["name"])+quotationmark if "name" in command.keys() else "" })')
                    # print(inputstring[command["id"]])
            outputstring = client.run("script Lpulldata()")
            if checkstatus or len(commands) > 0 or True:
                client.run("sv_cheats", "0")
    except ConnectionRefusedError as e:
        # print(serverid,"CORE BROKEY SOB",e)
        outputstring = ""
        status = ""
        discordtotitanfall[serverid]["serveronline"] = False
        pass
    except Exception as e:
        # print(serverid,"CORE BROKEY SOB",e)

        outputstring = ""
        status = ""
        discordtotitanfall[serverid]["serveronline"] = False
        # return False
        # traceback.print_exc()
    else:
        if not offlinethisloop:
            discordtotitanfall[serverid]["lastheardfrom"] = int(time.time())
    # print("I got here!")
    # print("outputstring",inputstring)

    try:
        if "|" in outputstring:
            accumulator = 0
            outputs = []
            addone = "{["
            takeone = "}]"
            begin = -1
            quoteflag = False
            for i, char in enumerate(outputstring):
                init = accumulator
                if char in addone:
                    if not accumulator:
                        # print("BEGIN SET",i)
                        begin = i
                    accumulator += 1

                elif char in takeone:
                    accumulator -= 1
                # if init != accumulator:
                # print("CHAR",char,accumulator)
                if begin != -1 and not accumulator and char in takeone:
                    # print("SLICE",begin,i+1)
                    outputs.append(getjson(outputstring[begin : i + 1]))
            # print("MEOW")
            outputs = outputs[1:]
            # print(json.dumps(outputs,indent=4))

            # print(outputstring)
            # print(outputstring)
            # outputs = functools.reduce(lambda a,b:{**a,"now":a["now"]+1,"begin":a["begin"] if a["acc"] != 0 or b not in '{["' else a["now"] ,"acc":a["acc"]+int(b in '{["')- int (b in '"]}'),"firstacc":a["firstacc"] if b not in '{["' else False} if (a["acc"] != 1 and b not in '"]}' and a["firstacc"] is not False) else {**a,"now":a["now"]+1,"acc":0,"outputs":[*a["outputs"],outputstring[a["begin"]:a["now"]]]},outputstring,{"acc":0,"firstacc":True,"outputs":[],"begin":0,"now":0})["outputs"]
            # print("OUTPUTCORE",json.dumps(outputs,indent=4))

            for output in outputs:
                # print("out",output)
                # print(json.dumps(output,indent=4))
                # print(output)
                output = {
                    "id": output[2] if len(output) > 2 else 0,
                    "commandtype": output[0],
                    "data": output[1],
                }
                # print(output)
                if output["commandtype"] == "msg":
                    # print("here")
                    messageflush.append(
                        {
                            **{
                                "timestamp": int(time.time()),
                                "serverid": serverid,
                                "type": 3,
                                "globalmessage": False,
                                "overridechannel": None,
                                # "messagecontent": output["data"],
                                # "metadata": {"type":"chat_message"},
                                "servername": context["servers"][serverid]["name"],
                            },
                            **output["data"],
                        }
                    )

                # print(output["commandtype"])
                elif output["commandtype"] == "smsg":
                    # print("here, they tried to connect")
                    messageflush.append(
                        {
                            "timestamp": int(time.time()),
                            "serverid": serverid,
                            "type": 4,
                            "globalmessage": False,
                            "overridechannel": None,
                            "messagecontent": output["data"],
                            "metadata": {"type": "connecttf1"},
                            "servername": context["servers"][serverid]["name"],
                        }
                    )
                # if COMMANDDICT.get(output["commandtype"],False):
                #     COMMANDDICT[output["commandtype"]](output["command"],serverid)
                # if output["commandtype"] == "stats":
                #     print("STATS REQUESTED POG")
                #     tf1pullstats(getjson(output["command"].replace("♥",'"')),serverid)
                elif output["commandtype"] in context["commands"]["ingamecommands"]:
                    tftodiscordcommand(output["commandtype"], output["data"], serverid)
                # if output["commandtype"] == ""
    except Exception as e:
        print("read brokey")
        traceback.print_exc()

        # print("outputs",outputs)

    idlist = {}
    messagelist = {}
    for index, commandid in enumerate(discordtotitanfall[serverid]["commands"]):
        idlist[commandid["id"]] = index
    for index, commandid in enumerate(discordtotitanfall[serverid]["messages"]):
        messagelist[commandid.get("id", random.randint(0, 1000000))] = index
    messageflag = False
    ids = []
    # print(discordtotitanfall[serverid]["commands"])
    senttoolongmessages = []
    for key, value in inputstring.items():
        origval = value
        funcprint = None
        # print("rawout",value)
        if "OUTPUT<" in value and "/>ENDOUTPUT" in value:
            value = "".join(
                "".join(
                    "".join(value.split("BEGINMAINOUT")[1:]).split("OUTPUT<")[1:]
                ).split("/>ENDOUTPUT")[:-1]
            )
            value = value.replace("☻", '"')
            oldoldvalue = value
            value = getjson(value)
            if isinstance(value, str):
                value = value[0:800]
            elif isinstance(value, bool):
                value = str(value)

        else:
            if commands[key]["command"] == "status":
                value = interpstatus(value)
            else:
                value = value[0:800]
        if "FUNCRETURN<" in origval and "/>FUNCRETURN" in origval:
            funcprint = "".join(
                "".join(
                    "".join(origval.split("BEGINMAINOUT")[:1]).split("FUNCRETURN<")[1:]
                ).split("/>FUNCRETURN")[:-1]
            )[0:500]
            if len(funcprint) == 0:
                funcprint = None
        # print("BEEP BOOOOP","".join("".join("".join(origval.split("BEGINMAINOUT")[:1]).split("FUNCRETURN<")[1:]).split("/>FUNCRETURN")[:-1])[0:500])
        # print("output from server:",value,funcprint)
        # print("funcout",funcprint)
        if commands[key]["type"] == "msg" and (value != "sent!" or messageflag):
            continue
        elif commands[key]["type"] == "msg" and value == "sent!":
            # messageflag = True
            if key in toolongmessages:
                senttoolongmessages.append(key)
            # print("BOOP",key,discordtotitanfall[serverid]["returnids"]["messages"][now])
            try:
                # del discordtotitanfall[serverid]["returnids"]["messages"][now]
                del discordtotitanfall[
                    serverid
                ][
                    "returnids"
                ][
                    "messages"
                ][
                    str(key)
                ]  # [discordtotitanfall[serverid]["returnids"]["messages"][now].index(key)]
                # if len(discordtotitanfall[serverid]["returnids"]["messages"][now]) == 0:
                # del discordtotitanfall[serverid]["returnids"]["messages"][now]
            except Exception as e:
                print("crash while deleting key", e)
            ids.append(commands[key]["id"])
            # print("HEREEEE SENT IT I THINK MABYE")
            discordtotitanfall[serverid]["messages"][messagelist[key]] = False
            continue
        # print(key,"key")
        if funcprint and not isinstance(value, dict):
            funcoutput = {"output": {"output": value}, "statuscode": 200}
            # if funcprint and not isinstance(value,dict):
            # print("HERE")
            funcoutput["output"]["funcprint"] = funcprint
        else:
            funcoutput = {"output": value, "statuscode": 200}

        discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)] = (
            funcoutput
        )
        # discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)]["output"] = value
        # discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(key)]["statuscode"] = "0"
        # print(discordtotitanfall[serverid]["commands"])
        try:
            discordtotitanfall[serverid]["commands"][idlist[key]] = "hot potato"
        except:
            print("race condition probably")
    discordtotitanfall[serverid]["commands"] = list(
        filter(lambda x: x != "hot potato", discordtotitanfall[serverid]["commands"])
    )
    discordtotitanfall[serverid]["messages"] = list(
        filter(lambda x: x, discordtotitanfall[serverid]["messages"])
    )
    asyncio.run_coroutine_threadsafe(reactomessages(list(ids), serverid), bot.loop)
    # discordtotitanfall[serverid]["serveronline"] = not offlinethisloop
    if senttoolongmessages:
        asyncio.run_coroutine_threadsafe(
            reactomessages(senttoolongmessages, serverid, "✂️"), bot.loop
        )

    return True


# test if ; breaks things and ()
def tf1relay():
    """Main TF1 relay loop handling server communication and message processing"""
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
    for server, serverdata in context["servers"].items():
        value = serverdata.get("istf1server", False)
        if value:
            initdiscordtotitanfall(server)
            servers.append(server)
            discordtotitanfall[server]["ip"] = value
            # print(context["istf1server"],value,discordtotitanfall[server]["ip"].split(":")[0], discordtotitanfall[server]["ip"].split(":")[1])
            # discordtotitanfall[server]["client"] = Client(discordtotitanfall[server]["ip"].split(":")[0], discordtotitanfall[server]["ip"].split(":")[1], passwd=TF1RCONKEY,timeout=1.5)
    # i = 0
    # while True:
    #     time.sleep(1)
    #     for server in servers:
    #         # print("boop")
    #         # print("meow",server)
    #         if (
    #             discordtotitanfall[server].get("serveronline", True) == True
    #             or i % 20 == 0
    #         ):
    #             # print(discordtotitanfall[server].get("serveronline", True))
    #             # try:print((discordtotitanfall[server]["serveronline"]))
    #             # except:print(list(discordtotitanfall[server].keys()))
    #             try:
    #                 threading.Thread(
    #                         target=threadwrap,
    #                         daemon=True,
    #                         args=(
    #                             tf1readsend,
    #                             server,
    #                             i % 20 == 0,

    #                         ),
    #                     ).start()
        
    #             except:
    #                 traceback.print_exc()
    #                 return
    #     i += 1

        # response = discordtotitanfall[server]["client"].run('sv_cheats1;script Lrconcommand("sendmessage","OWOWOOWOWOOW")')
    for server in servers:

            threading.Thread(
                    target=threadwrap,
                    daemon=True,
                    args=(
                        runtf1server,
                        server

                    ),
                ).start()

def runtf1server(server):
    i = 0
    while True:
        time.sleep(0.5)
        if (
            discordtotitanfall[server].get("serveronline", True) == True
            or i % 20 == 0
        ):
            
            try:
                tf1readsend(server,i % 20 == 0)
            except Exception as e:
                traceback.print_exc()
        i += 1


def messageloop():
    """Main message processing loop handling Discord message flushing, channel creation, and message batching"""
    global \
        messageflush, \
        lastmessage, \
        discordtotitanfall, \
        context, \
        messageflushnotify, \
        reactedyellowtoo
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
                        user.send(
                            discord.utils.escape_mentions(message["sendingmessage"])
                        ),
                        bot.loop,
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
                        (
                            message["serverid"] not in context["servers"]
                            or "channelid"
                            not in context["servers"][message["serverid"]]
                        )
                        and not addflag
                        and message["serverid"] != "-100"
                    ):
                        addflag = True
                        # print(message)
                        # print(list( context["servers"].keys()),   message["serverid"])

                        guild = bot.get_guild(context["categoryinfo"]["activeguild"])
                        category = guild.get_channel(context["categoryinfo"]["logging_cat_id"])
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
                        message["serverid"] in context["servers"]
                        and "channelid" in context["servers"][message["serverid"]]
                        and message["servername"]
                        not in [s.get("name") for s in context["servers"].values()]
                        and not addflag
                    ):
                        addflag = True
                        guild = bot.get_guild(context["categoryinfo"]["activeguild"])
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
                    # print(json.dumps(messageflush,indent=4))
                    message.setdefault("globalmessage", False)
                    message.setdefault("type", 3)
                    message.setdefault("overridechannel", None)
                    message["messagecontent"] = str(message.get("messagecontent"))
                    # print("MESSAGE",message)
                    messagewidget, playername = getmessagewidget(
                        message["metadata"],
                        message["serverid"],
                        message["messagecontent"],
                        message,
                    )
                    if messagewidget == "":
                        # print("here")
                        continue
                    if (
                        message["serverid"] not in output.keys()
                        and not message["globalmessage"]
                    ):
                        # print("a")
                        output[message["serverid"]] = []
                    elif (
                        message["globalmessage"]
                        and message["overridechannel"] not in output.keys()
                    ):
                        # print("b")
                        output[message["overridechannel"]] = []
                    if ("\033[") in messagewidget:
                        print("colour codes found in message")
                        while "\033[" in messagewidget:
                            startpos = messagewidget.index("\033[")
                            if "m" not in messagewidget[startpos:]:
                                break
                            endpos = messagewidget[startpos:].index("m") + startpos
                            messagewidget = (
                                messagewidget[:startpos] + messagewidget[endpos + 1 :]
                            )

                    messageadders = {
                        "pfp": message["metadata"].get("pfp", None),
                        "name": playername,
                        "type": message["metadata"]["type"],
                        "uid": message["metadata"].get("uid", None),
                        "originalname": str(message.get("player", False)),
                        "meta": message.get("metadata", {}),
                        "originalmessage": message.get("messagecontent", False),
                        "timestamp": message.get("timestamp",None)
                    }
                    if (
                        message["metadata"]["type"] in ["usermessagepfp", "impersonate"]
                        and USEDYNAMICPFPS == "1"
                    ):
                        message["type"] = 3
                    # else: messageadders = {"type":message["metadata"]["type"]}
                    if message["type"] == 1:
                        # print("c")
                        output[
                            message["serverid"]
                            if not message["globalmessage"]
                            else message["overridechannel"]
                        ].append(
                            {
                                "message": f"**{playername}**: {messagewidget}",
                                **messageadders,
                                "messagecontent": messagewidget,
                                "oserverid": message["serverid"],
                            }
                        )
                        # print(f"**{playername}**:  {messagewidget}")
                    elif message["type"] == 2:
                        # print("d")
                        output[
                            message["serverid"]
                            if not message["globalmessage"]
                            else message["overridechannel"]
                        ].append(
                            {
                                "message": f"""```ansi\n{ANSI_COLOURS["cyan"]}{playername}{ANSI_COLOURS["reset"]} {messagewidget}```""",
                                **messageadders,
                                "messagecontent": messagewidget,
                                "oserverid": message["serverid"],
                            }
                        )
                        # print(f"""{playername} {messagewidget}""")
                    elif message["type"] == 3:
                        # print("e")
                        output[
                            message["serverid"]
                            if not message["globalmessage"]
                            else message["overridechannel"]
                        ].append(
                            {
                                "message": f"{messagewidget}",
                                **messageadders,
                                "messagecontent": messagewidget,
                                "oserverid": message["serverid"],
                            }
                        )
                        # print(f"{messagewidget}")
                    elif message["type"] == 4:
                        # print("f")
                        output[
                            message["serverid"]
                            if not message["globalmessage"]
                            else message["overridechannel"]
                        ].append(
                            {
                                "message": f"```{messagewidget}```",
                                **messageadders,
                                "messagecontent": messagewidget,
                                "oserverid": message["serverid"],
                            }
                        )
                        # print(f"{messagewidget}")
                    else:
                        print("type of message unkown")
                        continue
                    realprint("\033[0m", end="")
                # if output:
                #     print("sending output",json.dumps(output, indent=4))
                for serverid in output.keys():
                    for key, message in enumerate(output[serverid]):
                        # print(json.dumps(message,indent=4))
                        # extra functions hooked onto messages
                        # asyncio.run_coroutine_threadsafe(colourmessage(message,serverid),bot.loop)
                        asyncio.run_coroutine_threadsafe(
                            checkverify(message, message["oserverid"]), bot.loop
                        )
                        threading.Thread(
                            target=threadwrap,
                            daemon=True,
                            args=(
                                tftodiscordcommand,
                                False,
                                message,
                                message["oserverid"],
                            ),
                        ).start()
                        threading.Thread(
                            target=threadwrap,
                            daemon=True,
                            args=(savemessages, message, serverid),
                        ).start()
                        isbad = checkifbad(message)
                        if isbad[0]:
                            print("horrible message found")
                            output[serverid][key]["isbad"] = isbad
                    # print("OUTPUT",output)
                    # print("sending to", serverid)
                    if (
                        serverid not in context["servers"]
                        or "channelid" not in context["servers"][serverid]
                    ) and serverid not in context["overridechannels"].keys():
                        print("channel not in bots known channels")
                        continue
                    channel = (
                        bot.get_channel(context["servers"][serverid]["channelid"])
                        if (
                            serverid in context["servers"]
                            and "channelid" in context["servers"][serverid]
                        )
                        else bot.get_channel(context["overridechannels"][serverid])
                    )
                    if channel is None:
                        print("channel not found")
                        continue
                    # # to save my sanity, I'm going to throw the order out for pfp messages, so I can group them and make them a wee bit more compact, if somone is REALLY sending a lot of messages
                    userpfpmessages = {}
                    for message in list(
                        filter(
                            lambda x: x["type"] in ["usermessagepfp", "impersonate"]
                            and USEDYNAMICPFPS == "1",
                            output[serverid],
                        )
                    ):
                        if (
                            not message["pfp"]
                            or not message["name"]
                            or not message["uid"]
                        ):
                            print("VERY BIG ERROR, PLEASE LOOK INTO IT", message)
                            if not message.get("pfp"):
                                message["pfp"] = "player has no model :("
                            else:
                                continue
                        userpfpmessages.setdefault(
                            message["name"],
                            {
                                "messages": [],
                                "pfp": message["pfp"],
                                "uid": message["uid"],
                                "originalname": message["originalname"],
                            },
                        )
                        userpfpmessages[message["name"]]["messages"].append(
                            {
                                **message,
                                "message": message["message"],
                                "isbad": message.get("isbad", [0, 0]),
                                "messagecontent": message["messagecontent"],
                            }
                        )

                    asyncio.run_coroutine_threadsafe(
                        sendpfpmessages(channel, userpfpmessages, serverid), bot.loop
                    )
                    # print("output",output)
                    asyncio.run_coroutine_threadsafe(
                        outputmsg(channel, output, serverid, USEDYNAMICPFPS), bot.loop
                    )
                messageflush = []
                lastmessage = time.time()
            now = int(time.time() * 100)
            # WHAT ON EARTH IS THIS AND HOW ON EARTH DOES IT WORK
            for serverid in discordtotitanfall.keys():
                iterator = 0
                while iterator < len(
                    discordtotitanfall[serverid]["returnids"]["messages"].keys()
                ):
                    key = list(
                        discordtotitanfall[serverid]["returnids"]["messages"].keys()
                    )[iterator]
                    value = [
                        int(x)
                        for x in discordtotitanfall[serverid]["returnids"]["messages"][
                            key
                        ]
                    ]
                    # print("key",key)
                    iterator += 1

                    if type(key) == int and int(key) < now - 300:
                        if len(value) > 0:
                            reactedyellowtoo.extend(value)
                            reactedyellowtoo = reactedyellowtoo[-200:]
                            # print("running this",value,serverid,key,now)
                            asyncio.run_coroutine_threadsafe(
                                reactomessages(value, serverid, "🟡"), bot.loop
                            )
                        del discordtotitanfall[serverid]["returnids"]["messages"][key]
                        iterator -= 1
                    elif type(key) == str and value[0] < now - 300:
                        reactedyellowtoo.extend(value)
                        reactedyellowtoo = reactedyellowtoo[-200:]
                        # print("running this2",value,serverid,key,now)
                        asyncio.run_coroutine_threadsafe(
                            reactomessages([key], serverid, "🟡"), bot.loop
                        )
                        del discordtotitanfall[serverid]["returnids"]["messages"][key]
                        iterator -= 1
                    # print(type(key) == str,value[0] - (now - 300))

        except Exception as e:
            time.sleep(3)
            traceback.print_exc()
            print("bot not ready", e)
        time.sleep(0.1)


def sendthingstoplayer(outputstring, serverid, statuscode, uidoverride):
    """Sends messages to specific players in-game via server communication"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    discordtotitanfall[serverid]["messages"].append(
        {
            # "id": str(int(time.time()*100)),
            "content": f"{PREFIXES['discord']}TF|{1 + int(not (istf1))} output: {outputstring}",
            # "teamoverride": 4,
            # "isteammessage": False,
            "uidoverride": [uidoverride],
            # "dotreacted": dotreacted
        }
    )
    discordtotitanfall[serverid]["messages"].append(
        {
            # "id": str(int(time.time()*100)),
            "content": f"{PREFIXES['discord']}Statuscode: {statuscode}",
            # "teamoverride": 4,
            # "isteammessage": False,
            "uidoverride": [uidoverride],
            # "dotreacted": dotreacted
        }
    )

def resolvecommandpermsformainbot(serverid,command,returndenys = False):
    # print("wdqdq",command)
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    # print(command,getpriority(tfcommandspermissions,[serverid,internaltoggles.get(command)]))
    if not istf1 and not (getpriority(tfcommandspermissions,[serverid,"commands"])) and time.time() > getpriority(tfcommandspermissions,[serverid,"laststatspull"],nofind = 0) + 3:
        tfcommandspermissions.setdefault(serverid,{})["laststatspull"] = int(time.time())
        if not serverid:
            print("big panic when reloading commands",serverid,str(inspect.currentframe().f_back.f_code.co_name))
            return None
        print("reloading commands for",serverid)
        sendrconcommand(
            serverid,
            f"!reloadtfcommandlist",
            sender=None,
        )
        return None # Panic here
    elif not istf1 and not (getpriority(tfcommandspermissions,[serverid,"commands"])) :
        return None
    # print(command)
    # print(tfcommandspermissions[serverid].get(command) != "None" and tfcommandspermissions[serverid]["commands"].get(command,False))
    allow = getpriority(tfcommandspermissions,[serverid,"commands",command,"permsneeded"]) == "everyone" or getpriority(tfcommandspermissions,[serverid,"commands",command,"permsneeded"]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",command,"permsneeded"],nofind = False)
    deny = getpriority(tfcommandspermissions,[serverid,"commands",command,"deniedperms"]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",command,"deniedperms"],nofind = False)
    # print({"allow":allow,"deny":deny})
    return (allow or ("disallowed" if deny else allow)) if not returndenys else json.dumps({"allow":allow,"deny":deny})
def resolvecommandperms(serverid,command,returndenys = False):
    # print(command,getpriority(tfcommandspermissions,[serverid,internaltoggles.get(command)]))
    # print([serverid,matchid])
    # deniedperms permsneeded
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    if not istf1 and not getpriority(tfcommandspermissions,[serverid,"commands"]) and time.time() > getpriority(tfcommandspermissions,[serverid,"laststatspull"],nofind = 0) + 3:
        tfcommandspermissions.setdefault(serverid,{})["laststatspull"] = int(time.time())
        if not serverid:
            print("big panic when reloading commands",serverid,str(inspect.currentframe().f_back.f_code.co_name))
            return None
        print("reloading commands for",serverid)
        sendrconcommand(
            serverid,
            f"!reloadtfcommandlist",
            sender=None,
        )
        return True # should not resolve
    elif not istf1 and not getpriority(tfcommandspermissions,[serverid,"commands"]):
        return None
    # print([command,getpriority(tfcommandspermissions,[serverid,"discordcommands",internaltoggles.get(command)])])
    # print([command,( context["commands"]["ingamecommands"][command].get("run") == "functionless" and getpriority(tfcommandspermissions,[serverid,"commands",internaltoggles.get(command)]) ) or (context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",internaltoggles.get(command)]) ) or context["commands"]["ingamecommands"][command].get("permsneeded", False),context["commands"]["ingamecommands"][command].get("permsneeded", False)])
    # print(internaltoggles)
    # command.get("alias",command)
    allow = ((context["commands"]["ingamecommands"][command].get("run") == "functionless" and  getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) == "everyone" or  context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) == "everyone")) or (( context["commands"]["ingamecommands"][command].get("run") == "functionless" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) ) or (context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) != "None" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) ) or context["commands"]["ingamecommands"][command].get("permsneeded", False))
    deny =  (( context["commands"]["ingamecommands"][command].get("run") == "functionless" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"deniedperms"]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"deniedperms"]) ) or (context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command),"deniedperms"]) != "None" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command),"deniedperms"]) ) or context["commands"]["ingamecommands"][command].get("deniedperms", False))

    # if (context["commands"]["ingamecommands"][command].get("run") == "functionless" and  getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command),"permsneeded"]) == "everyone" or  context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command)]) == "everyone"):
    #     return {"allow":False
    # # print( ( context["commands"]["ingamecommands"][command].get("run") == "functionless" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command)]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command)]) ) or (context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command)]) != "None" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command)]) ) or context["commands"]["ingamecommands"][command].get("permsneeded", False))
    # return (( context["commands"]["ingamecommands"][command].get("run") == "functionless" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command)]) != "None" and getpriority(tfcommandspermissions,[serverid,"commands",context["commands"]["ingamecommands"][command].get("alias",command)]) ) or (context["commands"]["ingamecommands"][command].get("run") != "functionless" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command)]) != "None" and getpriority(tfcommandspermissions,[serverid,"discordcommands",context["commands"]["ingamecommands"][command].get("alias",command)]) ) or context["commands"]["ingamecommands"][command].get("permsneeded", False))
    # only checks functionless commands against the thing tf sent, because uh uh uh they are the only ones that should corrolate to a tf command directly
    # print({"allow":allow,"deny":deny})
    return (allow or ("disallowed" if deny else False)) if not returndenys else json.dumps({"allow":allow,"deny":deny})
keyletter = "!"

def tftodiscordcommand(specificommand, command, serverid):
    """Handles all commands from TF2 to Discord, processing in-game commands and routing to Discord functions"""  # handles all commands in !helpdc, and generally most recent tf2 commands that execute stuff on discord
    global context
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    # if specificommand:
    #     print(
    #         "server command requested for",
    #         getpriority(context, ["servers", serverid, "name"]),
    #         specificommand,
    #     )
    # return

    servercommand = specificommand != False
    # if not specificommand and command["originalmessage"][1:].split(" ")[0] in (
    #     "togglebrute",
    #     "togglestats",
    #     "toggleexpi",
    #     "togglephase",
    #     "togglearcher",
    #     "togglefpanims",
    # ):
    #     discordtotitanfall[serverid]["messages"].append(
    #         {
    #             "content": f"{PREFIXES['discord']}{PREFIXES['warning']}{command['originalmessage'][1:].split(' ')[0]} no longer exists - type {PREFIXES['commandname']}'!toggle' {PREFIXES['warning']}for more info",
    #             "uidoverride": [getpriority(command, "uid", ["meta", "uid"])],
    #         }
    #     )

    # print("HERE")
    # print("HERE", not specificommand,command.get("originalmessage",False) ,command["originalmessage"][0] == keyletter,command["originalmessage"][1:].split(" ")[0] in REGISTEREDTFTODISCORDCOMMANDS.keys() ,("tf1" if context["servers"].get(serverid, {}).get("istf1server", False) else "tf2") in  REGISTEREDTFTODISCORDCOMMANDS[command["originalmessage"][1:].split(" ")[0]]["games"] and command.get("type",False) in ["usermessagepfp","chat_message","command","tf1command"])
    # print(not specificommand and command.get("originalmessage",False) and command["originalmessage"][0] == keyletter and command["originalmessage"][1:].split(" ")[0] in REGISTEREDTFTODISCORDCOMMANDS.keys() and ("tf1" if context["servers"].get(serverid, {}).get("istf1server", False) else "tf2") in REGISTEREDTFTODISCORDCOMMANDS[command["originalmessage"][1:].split(" ")[0]]["games"] and command.get("type",False) in ["usermessagepfp","chat_message","command","tf1command"])
    if (
        not specificommand
        and command.get("originalmessage", False)
        and command["originalmessage"][0] == keyletter
        and command["originalmessage"][1:].split(" ")[0]
        in context["commands"]["ingamecommands"].keys()
        and (
            "tf1"
            if context["servers"].get(serverid, {}).get("istf1server", False)
            else "tf2"
        )
        in context["commands"]["ingamecommands"][
            command["originalmessage"][1:].split(" ")[0]
        ]["games"]
        and command.get("type", False)
        in ["usermessagepfp", "chat_message", "command", "tf1command"]
        and (
            not context["commands"]["ingamecommands"][
                command["originalmessage"][1:].split(" ")[0]
            ].get("serversenabled", False)
            or int(serverid)
            in context["commands"]["ingamecommands"][
                command["originalmessage"][1:].split(" ")[0]
            ]["serversenabled"]
        )
        and context["commands"]["ingamecommands"][
            command["originalmessage"][1:].split(" ")[0]
        ].get("run")
        != "togglestat"
    ):
        specificommand = command["originalmessage"][1:].split(" ")[0].lower()
        print(
            "client command requested for",
            getpriority(context, ["servers", serverid, "name"]),
            specificommand,
        )
        commandargs = command["originalmessage"][1:].split(" ")[1:]
        # print("what",resolvecommandperms(serverid,specificommand))
        # print( "e",context["commands"]["ingamecommands"][specificommand].get("permsneeded",False) and not checkrconallowedtfuid(getpriority(command,"uid",["meta","uid"]),context["commands"]["ingamecommands"][specificommand].get("permsneeded",False)))
        if resolvecommandperms(serverid,specificommand) and not checkrconallowedtfuid(
            getpriority(command, "uid", ["meta", "uid"]),
            resolvecommandperms(serverid,specificommand,True),
            serverid=serverid,
        ):
            if (
                resolvecommandperms(serverid,specificommand)
                == "coolperksrole"
            ):
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}To use {specificommand} go to {COOLPERKSROLEREQUIRMENTS}",
                        "uidoverride": [getpriority(command, "uid", ["meta", "uid"])],
                    }
                )
                return
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['discord']}You don't have permission to run {PREFIXES["commandname"]}{specificommand}{PREFIXES["chatcolour"]}, you need {PREFIXES["commandname"]}{translaterole(serverid,resolvecommandperms(serverid,specificommand))}",
                    "uidoverride": [getpriority(command, "uid", ["meta", "uid"])],
                }
            )
            return
        if (
            specificommand in context["commands"]["ingamecommands"] 
            and bool(getpriority(command, ["meta", "blockedcommand"]))
            != bool(
                context["commands"]["ingamecommands"][specificommand].get("shouldblock")  and int(serverid) in context["commands"]["ingamecommands"][specificommand].get("serversenabled",[int(serverid)])
            )
            and specificommand != "toggle"
        ) or (
            specificommand == "toggle" #I noticed that this messes up if you do !toggle <NONTOGGLECOMMAND EG "nessify">, but the titanfall servers mess up too, and that is hard to fix, so if they both mess up, is fine

            and command["originalmessage"].split(" ")[1:]
            and command["originalmessage"].split(" ")[1:][0] in context["commands"]["ingamecommands"]
            and bool(getpriority(command, ["meta", "blockedcommand"]))
            != bool(
                context["commands"]["ingamecommands"][
                    command["originalmessage"].split(" ")[1:][0]
                ].get("shouldblock")and int(serverid) in context["commands"]["ingamecommands"][
                    command["originalmessage"].split(" ")[1:][0]
                ].get("serversenabled",[int(serverid)])
            )
        ):
            print("the server messed up with blocking commands",serverid)
            # HARDCODING !toggle to check next command - I don't like it but is alright
            # huh? this if statment confuses me.. oh actually no, it's telling the server off if it gets blocking wrong but why does it only run here? surely it should always run? put it here as that seems better
            # tf1 does not support blocking commands yet, from discord. nor does it have any, due to it using a better command system, so a lot of the commands can run directly on tf1
            # this breaks on toggel commands when they use a different value from toggle's block value. how to fix in a clean way? I am not too sure.
            senddiscordcommands(0, serverid, 0)

    elif specificommand:
        pass
    else:
        return
    initdiscordtotitanfall(serverid)

    if context["commands"]["ingamecommands"][specificommand]["run"] == "togglestat":
        # print(specificommand)
        # print("HERE HERE HERE HERE HERE HERE")
        togglestats(
            command, specificommand, serverid
        )  # this code should not run anymore, unless a server directly asks to run it. users themselves cannot run this command :) (replaced with !toggle)

    elif context["commands"]["ingamecommands"][specificommand]["run"] == "functionless":
        # pass
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}Running {keyletter}{getpriority(context['commands']['ingamecommands'][getpriority(command, 'originalmessage', 'messagecontent').split(keyletter, 1)[1].split(' ', 1)[0]], 'alias', nofind=getpriority(command, 'originalmessage', 'messagecontent').split(keyletter, 1)[1].split(' ', 1)[0])}",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(command, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )
        # print("command",f"{keyletter}{getpriority(context["commands"]["ingamecommands"][getpriority(command, 'originalmessage','messagecontent').split(keyletter,1)[1].split(" ",1)[0]],"alias",nofind=getpriority(command, 'originalmessage','messagecontent').split(keyletter,1)[1])} {getpriority(command, 'originalmessage','messagecontent').split(" ",1)[1:]}")
        asyncio.run_coroutine_threadsafe(
            returncommandfeedback(
                *sendrconcommand(
                    serverid,
                    (
                        f"!{getpriority(context['commands']['ingamecommands'][getpriority(command, 'originalmessage', 'messagecontent').split(keyletter, 1)[1].split(' ', 1)[0]], 'alias', nofind=getpriority(command, 'originalmessage', 'messagecontent').split(keyletter, 1)[1].split(' ', 1)[0])} {' '.join(getpriority(command, 'originalmessage', 'messagecontent').split(' ', 1)[1:])}"
                    ),
                    sender=getpriority(command, "originalname", "name"),
                ),
                "fake context",
                sendthingstoplayer,
                True,
                True,
                getpriority(command, "uid", ["meta", "uid"]),
            ),
            bot.loop,
        )
    # print(specificommand)
    elif context["commands"]["ingamecommands"][specificommand]["run"] == "thread":
        threading.Thread(
            target=threadwrap,
            daemon=True,
            args=(
                globals()[
                    context["commands"]["ingamecommands"][specificommand]["function"]
                ],
                command,
                serverid,
                servercommand,
            ),
        ).start()
    elif context["commands"]["ingamecommands"][specificommand]["run"] == "async":
        asyncio.run_coroutine_threadsafe(
            globals()[
                context["commands"]["ingamecommands"][specificommand]["function"]
            ](command, serverid, servercommand),
            bot.loop,
        )
    elif context["commands"]["ingamecommands"][specificommand]["run"] == "seq":
        returnvalue = globals()[
            context["commands"]["ingamecommands"][specificommand]["function"]
        ](command, serverid, servercommand)
        return returnvalue

async def ingameleaderboard(message,serverid,isfromserver):
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    command = message["originalmessage"].split(" ", 1)
    player = [{"uid":None}]
    if len(command) == 2:
        player = resolveplayeruidfromdb(command[1],True,False)
        if not player:
            discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You specified {command[1]} However that name does not exist in the database",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
            )
            return
    discordtotitanfall[serverid]["messages"].append(
    {
        "content": f"{PREFIXES['discord']}{f"Calculating leaderboard for {player[0]["name"]}" if player[0]["uid"] else "Calculating leaderboard"}",
        "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
    }
    )
    timestamp = await asyncio.to_thread(
                getweaponspng,
                False,
                False,
                10,
                False,
                350,
                player[0]["uid"],
            )
    cdn_url = f"{GLOBALIP}/cdn/{timestamp}"
    if not timestamp:
        discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}Failed to calculate leaderboard - the function crashed",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        }
        )
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(cdn_url + "TEST") as response:
                if response.status != 200:
                    discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}Failed to calculate pngleaderboard - cdn error",
                        "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    }
                    )
                    return   
        except:
            traceback.print_exc()
            discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Failed to calculate pngleaderboard - cdn error",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
            )
            return
    discordtotitanfall[serverid]["messages"].append(
    {
        "content": f"{PREFIXES['discord']}Open leaderboard in browser (open console and copy link):\n{PREFIXES["stat"]}{cdn_url}",
    }
    )

def registernewaccept(uid,matchid,additionaldata,function):
    global registeredaccepts
    registeredaccepts.setdefault(str(matchid),{}).setdefault(str(uid),[]).append({"additional":additionaldata,"func":function})
    if  len(registeredaccepts[str(matchid)][str(uid)]) == 1:
        return "!accept"
    else:
        return f"!accept {len(registeredaccepts[str(matchid)][str(uid)])}"

def acceptsomething(message,serverid,isfromserver):
    accept = message["originalmessage"].split(" ", 1)
    acceptednumber = 1
    if len(accept) == 2 and accept[1].isdigit():
        acceptednumber = int(accept[1])
    elif len(accept) == 2:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You have to use a number as the second arg (!accept 2)",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )    
        return
    acceptednumber -= 1
    if  len(getpriority(registeredaccepts,[peopleonline.get(str(getpriority(message, "uid", ["meta", "uid"])),{}).get("matchid"),str(getpriority(message, "uid", ["meta", "uid"]))],nofind = [])) <= acceptednumber:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You have nothing to accept / you put in an invalid number",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    if not getpriority(registeredaccepts,[peopleonline.get(str(getpriority(message, "uid", ["meta", "uid"])),{}).get("matchid"),str(getpriority(message, "uid", ["meta", "uid"]))],nofind = [])[acceptednumber]:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You already accepted this!",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    getpriority(registeredaccepts,[peopleonline.get(str(getpriority(message, "uid", ["meta", "uid"])),{}).get("matchid"),str(getpriority(message, "uid", ["meta", "uid"]))],nofind = [])[acceptednumber]["func"](getpriority(registeredaccepts,[peopleonline.get(str(getpriority(message, "uid", ["meta", "uid"])),{}).get("matchid"),str(getpriority(message, "uid", ["meta", "uid"]))],nofind = [])[acceptednumber]["additional"])
    registeredaccepts[peopleonline.get(str(getpriority(message, "uid", ["meta", "uid"])),{}).get("matchid")][str(getpriority(message, "uid", ["meta", "uid"]))][acceptednumber] = False
@on("nutone")
def duelcallback(kill):
    global currentduels
    # print(json.dumps(kill,indent=4))
    # print(json.dumps(potentialduels,indent=4))
    if not potentialduels.get(kill["match_id"]) or not kill.get("victim_id") or not kill.get("attacker_id") or kill.get("victim_type") != "player" or str(kill["attacker_id"]) not in  getpriority(potentialduels,[kill["match_id"],str(kill["victim_id"])],nofind = []) :
        # print("here1")
        return # a duel has been requested, and may or may not exist
        # print("this one counts!")
    istf1 = context["servers"].get(kill["server_id"], {}).get("istf1server", False)
    if getpriority(currentduels,[kill["server_id"],kill["match_id"],kill["victim_id"],kill["attacker_id"]]):
        whogoesfirst = ("victim_id","attacker_id")
    elif getpriority(currentduels,[kill["server_id"],kill["match_id"],kill["attacker_id"],kill["victim_id"]]):
        whogoesfirst = ("attacker_id","victim_id")
    else:
        # print("here2")
        return # duel no exist
    currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]][kill["attacker_id"]] +=1
    # print("I got here")
    equalkills = not currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]][kill["attacker_id"]] - currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]][kill["victim_id"]]
    if not istf1:
        discordtotitanfall[kill["server_id"]]["messages"].append({"content": f"{PREFIXES['duel']}{f" {PREFIXES["commandname"]}vs ".join(list(functools.reduce(lambda a,x:[a[0]+1,[*a[1],f"{PREFIXES[("green" if not a[0]  else "warning") if not equalkills else "silver"]}{resolveplayeruidfromdb(x[0],"uid",False,istf1)[0]["name"]}: {PREFIXES["stat"]}{x[1]} {PREFIXES['chatcolour']}kill{x[1]-1 and "s" or ""}"]],sorted(list(currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]].items()),key =lambda x: x[1],reverse = True),[0,[]])[1]))}","uidoverride": [getpriority(kill,"attacker_entid","attacker_id"),getpriority(kill,"victim_entid","victim_id")],})
    else:
        print([getpriority(kill,"victim_id")],[getpriority(kill,"attacker_id")])
        discordtotitanfall[kill["server_id"]]["messages"].append({"content": f"{PREFIXES['duel']}{f" {PREFIXES["commandname"]}vs ".join(list(functools.reduce(lambda a,x:[a[0]+1,[*a[1],f"{PREFIXES[("green" if not a[0]  else "warning") if not equalkills else "silver"]}{resolveplayeruidfromdb(x[0],"uid",False,istf1)[0]["name"]}: {PREFIXES["stat"]}{x[1]} {PREFIXES['chatcolour']}kill{x[1]-1 and "s" or ""}"]],sorted(list(currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]].items()),key =lambda x: x[1],reverse = True),[0,[]])[1]))}","uidoverride": [getpriority(kill,"victim_id")],})
        discordtotitanfall[kill["server_id"]]["messages"].append({"content": f"{PREFIXES['duel']}{f" {PREFIXES["commandname"]}vs ".join(list(functools.reduce(lambda a,x:[a[0]+1,[*a[1],f"{PREFIXES[("green" if not a[0]  else "warning") if not equalkills else "silver"]}{resolveplayeruidfromdb(x[0],"uid",False,istf1)[0]["name"]}: {PREFIXES["stat"]}{x[1]} {PREFIXES['chatcolour']}kill{x[1]-1 and "s" or ""}"]],sorted(list(currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]].items()),key =lambda x: x[1],reverse = True),[0,[]])[1]))}","uidoverride": [getpriority(kill,"attacker_id")],})
    # print(f"{PREFIXES['duel']}{" vs ".join(list(map(lambda x:f"{PREFIXES["green" if x[0] == kill["attacker_id"] else "warning"]}{resolveplayeruidfromdb(x[0],None,False)[0]["name"]}: {x[1]} kill{x[1]-1 and "s" or ""}",sorted(list(currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]].items()),key =lambda x: x[1],reverse = True))))}")
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute("UPDATE duels SET initiatorscore = ?, receiverscore = ? WHERE initiator = ? AND receiver = ? AND matchid = ?",
    (currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]][kill[whogoesfirst[0]]],currentduels[kill["server_id"]][kill["match_id"]][kill[whogoesfirst[0]]][kill[whogoesfirst[1]]][kill[whogoesfirst[1]]],kill[whogoesfirst[0]],kill[whogoesfirst[1]],kill["match_id"]))
    tfdb.commit()
    tfdb.close()

def printduelwinnings(serverid):
    print("calculating duel stats")
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    # print(mostrecentmatchids.get(serverid))
    # print( getpriority(currentduels,[serverid,mostrecentmatchids.get(serverid)]))
    # print(currentduels)
    if not( matchid:= mostrecentmatchids.get(serverid) )or not getpriority(currentduels,[serverid,matchid]):
        return
    print("duels found")
    for attacker in currentduels[serverid][matchid]:
        for otherperson in currentduels[serverid][matchid][attacker]:
            if currentduels[serverid][matchid][attacker][otherperson][attacker] > currentduels[serverid][matchid][attacker][otherperson][otherperson]:
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{resolveplayeruidfromdb(attacker,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]} won the duel against {PREFIXES["stat"]}{resolveplayeruidfromdb(otherperson,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]}! ({currentduels[serverid][matchid][attacker][otherperson][attacker]}:{currentduels[serverid][matchid][attacker][otherperson][otherperson]})",
                        # "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    }
                )   
            elif currentduels[serverid][matchid][attacker][otherperson][attacker] == currentduels[serverid][matchid][attacker][otherperson][otherperson]:
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{resolveplayeruidfromdb(attacker,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]} tied in the duel against {PREFIXES["stat"]}{resolveplayeruidfromdb(otherperson,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]}! ({currentduels[serverid][matchid][attacker][otherperson][attacker]}:{currentduels[serverid][matchid][attacker][otherperson][otherperson]})",
                        # "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    }
                )   
            elif currentduels[serverid][matchid][attacker][otherperson][attacker] < currentduels[serverid][matchid][attacker][otherperson][otherperson]:
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{resolveplayeruidfromdb(attacker,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]} lost the duel against {PREFIXES["stat"]}{resolveplayeruidfromdb(otherperson,"uid",True,istf1)[0]["name"]}{PREFIXES["chatcolour"]}! ({currentduels[serverid][matchid][attacker][otherperson][attacker]}:{currentduels[serverid][matchid][attacker][otherperson][otherperson]})",
                        # "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    }
                )   
            else:
                print("sob")
def startaduel(who):
    global currentduels
    # print(mostrecentmatchids)
    # print(json.dumps(currentduels,indent=4))

    for serverid in currentduels:
        for matchid in currentduels[serverid]:
            if mostrecentmatchids.get(serverid) and mostrecentmatchids.get(serverid) != matchid:
                # print(mostrecentmatchids.get(serverid),matchid)
                currentduels[serverid][matchid] = None

    istf1 = context["servers"].get(who["serverid"], {}).get("istf1server", False)
    person1 = resolveplayeruidfromdb(who["inituid"],"uid",True,istf1)[0]
    person2 = resolveplayeruidfromdb(who["otheruid"],"uid",True,istf1)[0]
    # print(person1,person2)
    # print(who["inituid"],who["otheruid"])
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute("SELECT initiatorscore, receiverscore FROM duels WHERE initiator = ? AND receiver = ? AND matchid = ?",
    (who["inituid"],who["otheruid"],who["matchid"]))
    currentstabs = (c.fetchone())
    if not currentstabs:
        c.execute("SELECT initiatorscore, receiverscore FROM duels WHERE receiver = ? AND initiator = ? AND matchid = ?",(who["inituid"],who["otheruid"],who["matchid"]))
        currentstabs = (c.fetchone())
        if currentstabs:
            person1, person2 = person2, person1
            currentstabs = list(currentstabs)
        else:
            currentstabs = [0,0]

    c.execute("INSERT INTO duels (initiator,receiver,matchid,initiatorscore,receiverscore,serverid,isfinished) VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",(who["inituid"],who["otheruid"],who["matchid"],0,0,who["serverid"],(0 if not istf1 else 1)))
    c.execute("SELECT initiatorscore, receiverscore FROM duels WHERE initiator = ? AND receiver = ? AND matchid = ?",
    (who["inituid"],who["otheruid"],who["matchid"]))
    
    
    tfdb.commit()
    tfdb.close()
    deep_set(currentduels,[who["serverid"],who["matchid"],str(person1["uid"]),str(person2["uid"])],{str(person1["uid"]):currentstabs[0],str(person2["uid"]):currentstabs[1]})
    # print(json.dumps(currentduels,indent=4))
    if not istf1:
        sendrconcommand(
            who["serverid"],
            f"!highlightplayerforduels {who["otheruid"]} {who["inituid"]}",
            sender=None,
        )
        sendrconcommand(
            who["serverid"],
            f"!highlightplayerforduels {who["inituid"]} {who["otheruid"]}",
            sender=None,
        )
    if currentstabs != [0,0]:
        discordtotitanfall[who["serverid"]]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Resuming existing duel bettween {PREFIXES["stat"]}{person1["name"]}{PREFIXES["chatcolour"]} and {PREFIXES["stat"]}{person2["name"]}{PREFIXES["chatcolour"]}",
                "uidoverride": [who["otheruid"],who["inituid"]],
            }
        )
    discordtotitanfall[who["serverid"]]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{person2["name"]}{PREFIXES["chatcolour"]} has agreed to duel {PREFIXES["stat"]}{person1["name"]}{PREFIXES["chatcolour"]}!",
            # "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        }
    )
def duelsomone(message,serverid,isfromserver):
    global potentialduels
    """Duels!"""

    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    command = message["originalmessage"].split(" ", 1)
    if len(command) == 1:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to specify a name, or part of one to duel a player",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    person = command[1]
    print(f"duelsearch {json.dumps(peopleonline,indent=4)}")
    print("morestuff",[serverid],mostrecentmatchids,person.lower())
    duelymatches = dict(filter(lambda x: person.lower() in x[1]["name"].lower() and x[1]["serverid"] == serverid and mostrecentmatchids.get(serverid,x[1]["matchid"]) == mostrecentmatchids.get(serverid,x[1]["matchid"]), peopleonline.items()))
    
    # print(duelymatches)
    if  (cannotduelyourself := str(getpriority(message, "uid", ["meta", "uid"])) in duelymatches and False) or (toomany := (len(duelymatches) > 1)) or not len(duelymatches) :
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{person}{PREFIXES["chatcolour"]} {("does not match anyone on the server - perhaps wait a bit for the bot to discover people" if not toomany else f"matches {", ".join(map(lambda x:x["name"],duelymatches.values()))}") if not cannotduelyourself else "matches yourself - you cannot duel yourself!"}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    # print(potentialduels)
    if list(duelymatches.keys())[0] not in getpriority(potentialduels,[list(duelymatches.values())[0]["matchid"],(str(getpriority(message, "uid", ["meta", "uid"])))],nofind = []):
        command = registernewaccept(list(duelymatches.keys())[0],list(duelymatches.values())[0]["matchid"],{"matchid":list(duelymatches.values())[0]["matchid"],"inituid":str(getpriority(message, "uid", ["meta", "uid"])),"otheruid":list(duelymatches.keys())[0],"serverid":serverid},startaduel)
        discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}Requesting a duel with {PREFIXES["stat"]}{list(duelymatches.values())[0]["name"]}{PREFIXES["chatcolour"]}, tell them to type '{PREFIXES["commandname"]}{command}{PREFIXES["chatcolour"]}' to accept!",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        })
        discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{(getpriority(message,"originalname","name"))}{PREFIXES["chatcolour"]} wants to duel with you, type '{PREFIXES["commandname"]}{command}{PREFIXES["chatcolour"]}' to accept!",
            "uidoverride": [list(duelymatches.keys())[0]],
        })
        potentialduels.setdefault(list(duelymatches.values())[0]["matchid"],{})
        potentialduels[list(duelymatches.values())[0]["matchid"]].setdefault(list(duelymatches.keys())[0],[]) .append( str(getpriority(message, "uid", ["meta", "uid"])))
        potentialduels[list(duelymatches.values())[0]["matchid"]].setdefault(str(getpriority(message, "uid", ["meta", "uid"])),[]) .append( list(duelymatches.keys())[0])

        # print(json.dumps(currentduels,indent=4))
    else:
        discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}You are already dueling / requesting a duel from {PREFIXES["stat"]}{list(duelymatches.values())[0]["name"]}",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        })
def duelstats(message, serverid, isfromserver):
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    command = message["originalmessage"].split(" ", 1)
    player = [{"uid":getpriority(message, "uid", ["meta", "uid"]),"name":getpriority(message,"originalname","name")}]
    if len(command) == 2:
        if command[1].lower() != "global":

            player = resolveplayeruidfromdb(command[1],None,True,istf1)
    if not player:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}{PREFIXES["stat"]}{command[1]}{PREFIXES["chatcolour"]} does not match any known players",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    
    duelinfo = reversed(pullduelstats(player[0]["uid"],limit = 9 if command[0] != keyletter+"bigduels" else 99,istf1=istf1))
    lastdate = None
    if duelinfo:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']} {"Global Duels stats" if not player[0]["uid"] else f"Duels stats for {PREFIXES["stat"]}{player[0]["name"]}"}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
    for duel in duelinfo:
        # print(json.dumps(duel,indent=4))
        winnercolour = (duel["draw"] and PREFIXES["silver"]) or PREFIXES["green"]
        losercolour = (duel["draw"] and PREFIXES["silver"]) or PREFIXES["warning"]
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{winnercolour}{resolveplayeruidfromdb(duel["winner"]["uid"],"uid",False,istf1)[0]["name"]} {PREFIXES["commandname"]}vs {losercolour}{resolveplayeruidfromdb(duel["loser"]["uid"],"uid",False,istf1)[0]["name"]} {PREFIXES["stat"]}{duel["winner"]["score"]} : {duel["loser"]["score"]} {f"{PREFIXES["stat2"]}({duel["humantimestamp"]}) and before" if lastdate != duel["humantimestamp"] else ""}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        lastdate =  duel["humantimestamp"]



def pullduelstats(who = None, **kwargs):
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    limit = kwargs.get("limit",99999)
    istf1 = kwargs.get("istf1",False)
    if not who:
        c.execute(f"""SELECT d.initiator, d.receiver, d.matchid, d.initiatorscore, d.receiverscore, m.map, m.time 
                      FROM duels d 
                      JOIN matchid{"tf1" if istf1 else ""} m ON d.matchid = m.matchid ORDER BY m.time DESC
                      """)

    else:
        c.execute(f"""SELECT d.initiator, d.receiver, d.matchid, d.initiatorscore, d.receiverscore, m.map, m.time 
                     FROM duels d 
                     JOIN matchid{"tf1" if istf1 else ""} m ON d.matchid = m.matchid 
                     WHERE d.initiator = ? OR d.receiver = ? ORDER BY m.time DESC""", (who, who))

    # modifyvalue value "date"

    allduels = list(map(lambda x: {**x ,"draw":x["initiatorscore"] == x["receiverscore"] ,"winner":max([{"uid":x["initiator"],"score":x["initiatorscore"]},{"uid":x["receiver"],"score":x["receiverscore"]}],key = lambda x: x["score"]),"loser":min([{"uid":x["receiver"],"score":x["receiverscore"]},{"uid":x["initiator"],"score":x["initiatorscore"]}],key = lambda x: x["score"])}, reversed([{"initiator":x[0],"receiver":x[1],"matchid":x[2],"initiatorscore":x[3],"receiverscore":x[4],"map":x[5],"timestamp":x[6],"humantimestamp":modifyvalue(x[6],"date")} for x in c.fetchall()[:limit]])))
    tfdb.close()
    # print(json.dumps(allduels,indent=4))
    return allduels

def pingperson(message, serverid, isfromserver):
    """Ping somone on the discord"""
    global knownpeople
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    command = message["originalmessage"].split(" ", 1)
    # need to pull closest person..
    if len(command) == 1:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to specify a name, or part of one to ping",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return

    searchterm = command[1].strip()
    # okay, we got rid of that. now uhm need to order people
    # print(list(map(simplyfy,knownpeople[596713937626595382].values())))
    matches = list(
        filter(
            lambda b: any(
                simplyfy(searchterm) in simplyfy(val) for val in b[1].values() if val
            ),
            knownpeople.items(),
        )
    )

    # sort by length, then beginswith, then probably recently spoken, but I don't track that :l
    # I'll try len, then in the linkeddb then beginswith
    # for match in matches:
    #     if not match[1]["name"]:
    #         print("eee",match)
    matches.sort(key=lambda x: len(x[1]["name"] or ""))
    matches.sort(key=lambda x: (not pullid(x[0], "tf", True)))
    matches.sort(
        key=lambda x: (
            bool(
                x[1]["name"] and simplyfy(x[1]["name"]).startswith(simplyfy(searchterm))
            )
            * 4
            + 2
            * bool(
                x[1]["nick"] and simplyfy(x[1]["nick"]).startswith(simplyfy(searchterm))
            )
            + (
                bool(
                    x[1]["username"]
                    and simplyfy(x[1]["username"]).startswith(simplyfy(searchterm))
                )
                * 1
            )
        ),
        reverse=True,
    )
    matches.sort(
        key=lambda x: (
            not x[1]["nick"] or simplyfy(searchterm) != simplyfy(x[1]["nick"])
        )
        and (not x[1]["name"] or simplyfy(searchterm) != simplyfy(x[1]["name"]))
        and (not x[1]["username"] or simplyfy(searchterm) != simplyfy(x[1]["username"]))
    )
    # 11 lines
    matches = dict(matches)
    if not matches:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}No matches found for {PREFIXES['commandname']}{searchterm}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    if command[0].split(keyletter)[1] != "ping":
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}{len(matches)}{PREFIXES['chatcolour']} Match{'es' if len(matches) != 1 else ''} for {PREFIXES['commandname']}{searchterm}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        cmdcounter = 0
        for item, thing in list(matches.items())[:10]:
            match = thing
            cmdcounter += 1
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['discord']}{PREFIXES['gold']}{cmdcounter}) {PREFIXES['commandname' if cmdcounter == 1 else 'stat2']}{match['name']} {PREFIXES['chatcolour']}{'- ' + PREFIXES['commandname' if cmdcounter == 1 else 'stat2'] + ' ' + match['nick'] + ' ' if match['nick'] else ''}- {match['username']}",
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                }
            )
        return
    key = list(matches.keys())[0]
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}Pinging {PREFIXES['commandname']}{matches[key]['name']} {PREFIXES['chatcolour']}{'- ' + PREFIXES['commandname'] + ' ' + matches[key]['nick'] if matches[key]['nick'] else ''}",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        }
    )
    # print(message["meta"])
    messageflush.append(
        {
            "player": getpriority(message, "originalname", "name"),
            "metadata": {
                **message["meta"],
                "allowmentions": True,
                "type": "usermessagepfp",
            },
            "serverid": serverid,
            "type": 1,
            "timestamp": int(time.time()),
            "messagecontent": f"<@{list(matches.keys())[0]}>",
            "globalmessage": False,
            "overridechannel": None,
            "servername": context["servers"][serverid]["name"],
        }
    )
    # we have got here, and we have not pinged anyone. I'm not too sure how to make this command work amazingly
    # so that you don't ping the wrong person
    # it's a bit complicated
    # like I could run a llm but that feels wasteful?
    # I could just yolo it
    # I could make this something like !ping t <name>, then actual is !ping name
    # tbh I should probably just have support for command aliases, but it's.. a bit late for that now?,
    # unless I make them somehow invisible to everything but !help...
    # I've got this!


def addsanction(message, serverid, isfromserver):
    future = asyncio.run_coroutine_threadsafe(
        process_sanctiontf2(
            serverid,
            message["sender"],
            str(message["uid"]),
            message["sanctiontype"],
            message["reason"],
            str(message["expiry"]),
        ),
        bot.loop,
    )
    result = future.result()
    for msg in result.split("\n"):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}{msg}",
            }
        )
    sendrconcommand(
        serverid, f"!reloadpersistentvars {message['uid']}", sender=message["sender"]
    )


def autobalance(message, serverid, isfromserver):
    asyncio.run_coroutine_threadsafe(
        returncommandfeedback(
            *sendrconcommand(
                serverid,
                f"!playerfinder",
                sender=getpriority(message, "originalname", "name"),
            ),
            "fake context",
            autobalanceoverride,
            True,
            False,
        ),
        bot.loop,
    )


def autobalanceoverride(data, serverid, statuscode):
    data = getjson(data)
    print(json.dumps(data, indent=4))
    # playerinfo = {}
    # for uid,playerdata in data.items():
    #     if not uid.isdigit():
    #         continue
    #     playerinfo[uid] = playerdata[1]
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    placeholders = ",".join(["?"] * len(data))
    c.execute(
        f"""
    WITH session_durations AS (
        SELECT
            playeruid,
            matchid,
            pilotkills,
            (leftatunix - joinatunix) AS session_duration
        FROM playtime
        WHERE leftatunix > joinatunix
        AND playeruid IN ({placeholders})
    ),
    match_stats AS (
        SELECT
            playeruid,
            matchid,
            SUM(pilotkills) AS total_pilotkills,
            SUM(session_duration) AS total_playtime_seconds
        FROM session_durations
        GROUP BY playeruid, matchid
        HAVING SUM(session_duration) > 0
    ),
    match_kph AS (
        SELECT
            playeruid,
            matchid,
            total_pilotkills,
            total_playtime_seconds,
            1.0 * total_pilotkills * 3600 / total_playtime_seconds AS kills_per_hour
        FROM match_stats
    ),
    ranked_matches AS (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY playeruid ORDER BY kills_per_hour DESC) AS match_rank,
            COUNT(*) OVER (PARTITION BY playeruid) AS total_matches
        FROM match_kph
    ),
    filtered_matches AS (
        SELECT
            *,
            CASE
                WHEN total_matches < 5 THEN total_matches
                ELSE CAST(total_matches * 0.4 + 0.9999999 AS INTEGER)
            END AS matches_to_include
        FROM ranked_matches
    ),
    top_matches_data AS (
        SELECT
            playeruid,
            MAX(matches_to_include) AS matches_used,
            SUM(total_pilotkills) AS total_kills_top,
            SUM(total_playtime_seconds) AS total_seconds_top
        FROM filtered_matches
        WHERE match_rank <= matches_to_include
        GROUP BY playeruid
    )
    SELECT
        playeruid,
        ROUND((total_kills_top * 3600.0) / NULLIF(total_seconds_top, 0), 2) AS kph,
        matches_used
    FROM top_matches_data;
    """,
        tuple(map(int, data)),
    )

    results = c.fetchall()
    tfdb.close()

    stats_list = sorted(
        [
            {
                "uid": str(row[0]),
                "kph": float(row[1]) if row[1] is not None else 0.0,
                "gamesplayed": row[2],
            }
            for row in results
        ],
        key=lambda x: -x["kph"],
    )
    searchablestats = {x["uid"]: x for x in stats_list}
    # zippp ittt
    # this is half meant to support more than two teams, but lets be honest, we're not getting that update any time soon
    outputtedteams = [[], []]
    teamchecker = 0
    for stat in stats_list[0:-1]:
        outputtedteams[teamchecker].append(
            {**stat, "originalteam": data[str(stat["uid"])]["team"]}
        )
        teamchecker += 1
        teamchecker = teamchecker % len(outputtedteams)
    outputtedteams[len(outputtedteams) - 1].append(
        {**stats_list[-1], "originalteam": data[str(stats_list[-1]["uid"])]["team"]}
    )
    if functools.reduce(
        lambda a, b: a + 1 * (b["originalteam"] == 2), outputtedteams[0], 0
    ) < functools.reduce(
        lambda a, b: a + 1 * (b["originalteam"] == 2), outputtedteams[1], 0
    ):
        outputtedteams = outputtedteams[::-1]

    # print(json.dumps({"2":{x["uid"]:x for x in outputtedteams[0]},"3":{x["uid"]:x for x in outputtedteams[1]}},indent = 4))
    # time.sleep(10)
    # return {"message": "ok", "stats": {"2":{x["uid"]:{**x,"uid":str(x["uid"])} for x in outputtedteams[0]},"3":{x["uid"]:{**x,"uid":str(x["uid"])} for x in outputtedteams[1]}}}
    playernamecache = {}
    # print(json.dumps(data,indent=4))
    for player in data:
        playername = player
        playername = resolveplayeruidfromdb(player, "uid", True)
        if playername:
            playername = playername[0].get("name", player)
        playernamecache[player] = playername
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}{PREFIXES['stat']}TEAMBALANCE{PREFIXES['neutral']} Names in {PREFIXES['warning']}this colour{PREFIXES['neutral']} are people you have interacted with recently"
        }
    )

    # discordtotitanfall[serverid]["messages"].append(
    #     {
    #         "content": f"{PREFIXES['discord']}Below is the new teambalance, along with each players weight"
    #     }
    # )
    for teamint, team in enumerate(outputtedteams):
        for player in team:
            # if player["uid"] != "1012640166434":
            #     continue
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['stat']}Your team: {', '.join(functools.reduce(lambda a, b: {'lastcolour': PREFIXES['warning'] if b in data[player['uid']]['scary'] else PREFIXES['friendly'], 'output': [*a['output'], f'{(PREFIXES["warning"] if b in data[player["uid"]]["scary"] else PREFIXES["friendly"]) if (PREFIXES["warning"] if b in data[player["uid"]]["scary"] else PREFIXES["friendly"]) != a["lastcolour"] else ""}{playernamecache[b]}:{searchablestats[b]["kph"]:.2f}']}, list(map(lambda x: x['uid'], outputtedteams[teamint])), {'lastcolour': False, 'output': []})['output'])}",
                    "uidoverride": [player["uid"]],
                }
            )
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['stat']}Enemy team: {', '.join(functools.reduce(lambda a, b: {'lastcolour': PREFIXES['warning'] if b in data[player['uid']]['scary'] else PREFIXES['enemy'], 'output': [*a['output'], f'{(PREFIXES["warning"] if b in data[player["uid"]]["scary"] else PREFIXES["enemy"]) if (PREFIXES["warning"] if b in data[player["uid"]]["scary"] else PREFIXES["enemy"]) != a["lastcolour"] else ""}{playernamecache[b]}:{searchablestats[b]["kph"]:.2f}']}, list(map(lambda x: x['uid'], outputtedteams[abs(teamint - 1)])), {'lastcolour': False, 'output': []})['output'])}",
                    "uidoverride": [player["uid"]],
                }
            )

    threading.Thread(
        target=threadwrap, daemon=True, args=(autobalancerun, outputtedteams, serverid)
    ).start()
    return defaultoverride(data, serverid, statuscode)



def autobalancerun(outputtedteams, serverid):
    # discordtotitanfall[serverid]["messages"].append({
    #     "content":f"{PREFIXES['discord']} Balance in {PREFIXES["warning"]}10{PREFIXES["neutral"]} seconds"})
    # time.sleep(5)
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']} Balance in {PREFIXES['warning']}5{PREFIXES['neutral']} seconds"
        }
    )
    time.sleep(5)
    discordtotitanfall[serverid]["messages"].append(
        {"content": f"{PREFIXES['discord']} Trying to balance now"}
    )
    sendrconcommand(
        serverid,
        f"!bettertb {' '.join([f'2 {x["uid"]}' for x in outputtedteams[0]])} {' '.join([f'3 {x["uid"]}' for x in outputtedteams[1]])}",
        sender=None,
    )


# nocaros stuff


def nocarobalance(message, serverid, isfromserver):
    if not (
        result := nocarocompleterequest(
            getpriority(message, "uid", ["meta", "uid"]),
            serverid,
            context["servers"].get(serverid, {}).get("istf1server", False),
            "user/balance",
        )
    ):
        return
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['nocaro']}{PREFIXES['commandname']}{getpriority(message, 'originalname', 'name')}{PREFIXES['chatcolour']} has {PREFIXES['stat']}{int(result['text']):,}{PREFIXES['chatcolour']} bouge buck{(int(result['text']) - 1 and 's') or ''}",
            # "uidoverride": getpriority(message,"uid",["meta","uid"])
        }
    )


def nocaroslots(message, serverid, isfromserver):
    if (
        not len(getpriority(message, "originalmessage").split(" ", 1)[1:])
        or not (getpriority(message, "originalmessage").split(" ", 1)[1]).isdigit()
        or abs(bet := int(getpriority(message, "originalmessage").split(" ", 1)[1]))
        != float(getpriority(message, "originalmessage").split(" ", 1)[1])
    ):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Error: you must specify a bet value! (eg !slots 50)",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )
        return
    if not (
        result := nocarocompleterequest(
            getpriority(message, "uid", ["meta", "uid"]),
            serverid,
            context["servers"].get(serverid, {}).get("istf1server", False),
            "games/slots",
            {"bet": bet},
        )
    ):
        return
    keys = [
        "[38;2;254;0;0m• ",
        "[38;2;0;254;0m↑ ",
        "[38;2;100;100;254m↓ ",
        "[38;2;254;254;0m→",
        "[38;2;254;0;254m←",
        "[38;2;51;114;110m§",
    ]
    for slot in result["json"]["spinners"]:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}{' '.join(list(map(lambda x: keys[x], slot)))}",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )
        time.sleep(1)
    if not result["json"]["winner"]:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Nothing, you lose {PREFIXES['stat']}{bet}{PREFIXES['chatcolour']} bouge bucks.",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )
    elif result["json"].get("jackpot"):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}What the fuck? You got the gunga jackpot! You win {PREFIXES['stat']}{result['json']['amount_won']}{PREFIXES['chatcolour']} bouge bucks!",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )

    elif result["json"]["spinners"][-1].count(
        max(
            set(result["json"]["spinners"][-1]),
            key=result["json"]["spinners"][-1].count,
        )
    ) == len(result["json"]["spinners"][-1]):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Jackpot! You get {PREFIXES['stat']}{result['json']['amount_won']}{PREFIXES['chatcolour']} bouge bucks!!!",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )
    elif (
        result["json"]["spinners"][-1].count(
            max(
                set(result["json"]["spinners"][-1]),
                key=result["json"]["spinners"][-1].count,
            )
        )
        == len(result["json"]["spinners"][-1]) - 1
    ):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Nice, you get {PREFIXES['stat']}{result['json']['amount_won']}{PREFIXES['chatcolour']} bouge bucks.",
                "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
            }
        )


def nocaromap(message, serverid, isfromserver):
    if not (
        result := nocarocompleterequest(
            getpriority(message, "uid", ["meta", "uid"]),
            serverid,
            context["servers"].get(serverid, {}).get("istf1server", False),
            "user/map",
        )
    ):
        return
    if int(result["text"]) == 0:
        output = "your map was so bad you got nothing out of it."
    elif int(result["text"]) > 99:
        output = f"you maped and it was a banger, you still didn't get any money but you got {PREFIXES['stat']}{result['text']}{PREFIXES['chatcolour']} bouge bucks!"
    else:
        output = f"you maped for money but got {PREFIXES['stat']}{result['text']}{PREFIXES['chatcolour']} bouge buck{(int(result['text']) - 1 and 's') or ''} instead."
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['nocaro']}{output}",
            "uidoverride": getpriority(message, "uid", ["meta", "uid"]),
        }
    )


def nocarocompleterequest(uid, serverid, istf1, route, extra_querys={}):
    if not NOCAROAUTH:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Error: {PREFIXES['warning']}No auth key provided for Nocaro - Server error",
                "uidoverride": uid,
            }
        )
        return
    if istf1 and len(str(uid)) > 15:
        discorduid = uid
    elif istf1:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Error: {PREFIXES['warning']}Discord not linked - cannot use Nocaro right now",
                "uidoverride": uid,
            }
        )
    elif not (discorduid := pullid(uid, "discord", True)):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Error: Discord not linked - use {PREFIXES['warning']}/linktf2account",
                "uidoverride": uid,
            }
        )
        return
    r = requests.get(
        f"{NOCAROENDPOINT}{route}",
        params={**extra_querys, "user_id": discorduid},
        timeout=10,
        headers={"authentication": NOCAROAUTH},
    )

    if not r.ok and r.status_code != 403:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Error: {PREFIXES['warning']}{r.reason} {PREFIXES['chatcolour']}(code: {PREFIXES['warning']}{r.status_code}{PREFIXES['chatcolour']})",
                "uidoverride": uid,
            }
        )
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}Extended error: {PREFIXES['warning']}{r.text}",
                "uidoverride": uid,
            }
        )
        return
    if r.status_code == 403:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['nocaro']}You must run {PREFIXES['warning']}/apiconsent {PREFIXES['chatcolour']}on Nocaro to allow the commands to work here",
                "uidoverride": uid,
            }
        )
        return
    return {
        "ok": r.ok,
        "code": r.status_code,
        "status": r.reason,
        "json": r.json(),
        "text": r.text,
    }


def ingamesetusercolour(message, serverid, isfromserver):
    """Handles in-game color setting commands from players"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    name = getpriority(message, "originalname", "name")
    teamspecify = False
    teams = {
        "all": "all",
        "friendly": "friendly",
        "enemy": "enemy",
        "neutral": "neutral",
        "f": "friendly",
        "e": "enemy",
    }
    if len(message.get("originalmessage", "w").split(" ")) == 1:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to specify colours! put in a normal colour eg: 'red', or a hex colour eg: '#ff30cb' to choose, after the command",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    if (
        len(message.get("originalmessage", "w").split(" ")) == 2
        and message.get("originalmessage", "w").split(" ")[1].lower() in teams
    ):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to specify colours as well as a team! eg: 'friendly red' or 'enemy #ff30cb'",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    elif (
        len(message.get("originalmessage", "w").split(" ")) > 2
        and message.get("originalmessage", "w").split(" ")[1].lower() in teams
    ):
        teamspecify = True

    name = resolveplayeruidfromdb(name, None, True)
    if not name:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {getpriority(message, 'originalname', 'name')} could not be found in db",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    name = name[0]
    discorduid = pullid(name["uid"], "discord")
    if not discorduid:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {name} does not have a discord account linked - use /linktf2account on discord!",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return

    colours = " ".join(message["originalmessage"].split(" ")[1 + int(teamspecify) :])
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}{setcolour(colours, discorduid, 'choseningamecolour', 'all' if not teamspecify else teams[message.get('originalmessage', 'w').split(' ')[1].lower()])}",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        }
    )

    sendrconcommand(
        serverid,
        f"!reloadpersistentvars {getpriority(message, 'uid', ['meta', 'uid'], 'originalname', 'name')}",
        sender=getpriority(message, "originalname"),
    )


def ingamesetusertag(message, serverid, isfromserver):
    """Handles in-game tag setting commands from players"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    name = getpriority(message, "originalname", "name")

    if len(message.get("originalmessage", "w").split(" ")) == 1:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to specify a tag",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return

    name = resolveplayeruidfromdb(name, None, True)
    if not name:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {' '.join(message['originalmessage'].split(' ')[1:])} could not be found",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    name = name[0]
    discorduid = pullid(name["uid"], "discord")
    if not discorduid:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {name} does not have a discord account linked - use /linktf2account on discord!",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return

    colours = " ".join(message["originalmessage"].split(" ")[1:])
    # if len(colours) < 1 or len(colours) > 6:
    #     discordtotitanfall[serverid]["messages"].append(
    #     {
    #         "content":f"{PREFIXES['discord']}{colours} is too long, it must be bettween 1 and 6 chars or type 'reset' as the arg to reset it",
    #         "uidoverride": [getpriority(message,"uid",["meta","uid"])]
    #     }
    #     )
    #     return
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}{settag(colours, discorduid)}",
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
        }
    )

    sendrconcommand(
        serverid,
        f"!reloadpersistentvars {getpriority(message, 'uid', ['meta', 'uid'], 'originalname', 'name')}",
        sender=getpriority(message, "originalname"),
    )
def wallhackingame(message, serverid, isfromserver):
    if len(message.get("originalmessage", "w").split(" ")) < 2:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to send a name, and optionally the type of highlight",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    asyncio.run_coroutine_threadsafe(
        returncommandfeedback(
            *sendrconcommand(
                serverid,
                (
                    f"!wallhack {getpriority(message, "uid", ["meta", "uid"])} {message.get("originalmessage", "w").split(" ")[1]}"
                ),
                sender=getpriority(message, "originalname", "name"),
            ),
            "fake context",
            sendthingstoplayer,
            True,
            True,
            getpriority(message, "uid", ["meta", "uid"]),
        ),
        bot.loop,
    )
def sendsoundfromingame(message, serverid, isfromserver):
    if len(message.get("originalmessage", "w").split(" ")) < 3:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}You need to send a name, a sound, and optionally the number of times",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    # print("bw",message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))])
    if not completesound(" ".join(message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))])):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Could not find {" ".join(message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))])}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    number = 1
    if len(message.get("originalmessage", "w").split(" ")) > 3 and message.get("originalmessage", "w").split(" ")[-1].isdigit():
        number = message.get("originalmessage", "w").split(" ")[3]
    print(f"!sendsound {message.get("originalmessage", "w").split(" ")[1]} {completesound(" ".join(message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))]))[0]} {number}")
    # sendrconcommand(serverid,f"!sendsound {message.get("originalmessage", "w").split(" ")[1]} {completesound(" ".join(message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))]))[0]} {number}",sender=getpriority(message, "originalname", "name"))
    asyncio.run_coroutine_threadsafe(
        returncommandfeedback(
            *sendrconcommand(
                serverid,
                (
                    f"!sendsound {message.get("originalmessage", "w").split(" ")[1]} {completesound(" ".join(message.get("originalmessage", "w").split(" ")[2:max(3,len(message.get("originalmessage", "w").split(" "))-int(message.get("originalmessage", "w").split(" ")[-1].isdigit()))]))[0]} {number}"
                ),
                sender=getpriority(message, "originalname", "name"),
            ),
            "fake context",
            sendthingstoplayer,
            True,
            True,
            getpriority(message, "uid", ["meta", "uid"]),
        ),
        bot.loop,
    )
def shownamecolours(message, serverid, isfromserver):
    """Shows available color options to players in-game"""
    # print("HERHEHRHE")
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    name = getpriority(message, "originalname", "name")
    if len(message.get("originalmessage", "w").split(" ")) > 1:
        name = " ".join(message["originalmessage"].split(" ")[1:])
    name = resolveplayeruidfromdb(name, None, True)
    if not name:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {' '.join(message['originalmessage'].split(' ')[1:])} could not be found",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    name = name[0]
    discorduid = pullid(name["uid"], "discord")
    if not discorduid:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Name: {name} does not have a discord account linked",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return

    for colour in RGBCOLOUR:
        colourtype = colour
        if colour == "DISCORD":
            colourtype = "discordcolour"
            messageout = f"{PREFIXES['discord']}{PREFIXES['discordcolour']}{colour}: "
        else:
            messageout = f"{PREFIXES['discord']}{PREFIXES[colour.lower()]}{colour}: "

        messageout += computeauthornick(
            name["name"],
            discorduid,
            messageout,
            False,
            colour,
            colourtype,
            254,
            colour != "DISCORD",
        )
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": messageout,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )


def checkbantf1(message, serverid, isfromserver):
    """Checks and processes TF1 ban status for players"""
    # print("CHECKING BANNNS")
    if int(message["uid"]) in context["overriderolesuids"].get(translaterole(serverid, "rconrole"), []):
        sendrconcommand(
            serverid,
            f"!promote {message["uid"]} 1",
            sender=None,
        )
    c = postgresem("./data/tf2helper.db")
    c.execute(
        "SELECT id FROM banstf1 WHERE playerip = ? AND playername = ? AND playeruid = ?",
        (message["ip"], message["name"], int(message["uid"])),
    )
    playerid = c.fetchall()
    if playerid:
        playerid = playerid[0][0]
        c.execute(
            "UPDATE banstf1 SET lastseen = ?, lastserverid = ? WHERE id = ?",
            (int(time.time()), serverid, playerid),
        )
    else:
        c.execute(
            "INSERT INTO banstf1 (playerip,playername,playeruid,lastseen,lastserverid) VALUES (?,?,?,?,?) RETURNING id",
            (
                message["ip"],
                message["name"],
                message["uid"],
                int(time.time()),
                serverid,
            ),
        )
        playerid = c.fetchone()[0]
    c.commit()
    c.execute(
        "SELECT playerip, playername, playeruid,bantype, banlinks, baninfo, expire, id FROM banstf1"
    )
    # banlinks is what must be the same for ban to carry through. imo is better as a number tho
    bans = list(
        map(
            lambda x: {
                "ip": x[0],
                "name": x[1],
                "uid": x[2],
                "bantype": x[3],
                "banlinks": x[4],
                "baninfo": x[5],
                "expire": x[6],
                "exhaustion": 0,
                "id": x[7],
            },
            list(c.fetchall()),
        )
    )
    # print(bans)
    # print("MEOW")
    if message["name"].lower() in context["wordfilter"]["namestokick"]:
        sendrconcommand(
            serverid,
            f"banip 60 {message['ip']} You are banned for 60s Change your name then rejoin",
        )
    bannedpeople = findallbannedpeople(
        bans,
        list(
            filter(
                lambda x: x["bantype"]
                and (x["expire"] is None or x["expire"] > int(time.time())),
                bans,
            )
        ),
        10,
    )
    # print("DONE")
    # print(json.dumps(bannedpeople,indent=4))
    # print("ee",e)
    # print("eeeeeee",bannedpeople)
    # print([playerid])
    # print(list(filter(lambda x: playerid == x["id"],bannedpeople)))
    if list(filter(lambda x: playerid == x["id"], bannedpeople)):
        # print("MEOW")
        # they're banned! or muted, depends
        print(
            "Sanction enforced for",
            message["name"],
            "baninfo:",
            json.dumps(
                list(filter(lambda x: playerid == x["id"], bannedpeople))[0], indent=4
            ),
        )
        if "ban" in list(
            map(
                lambda x: x["bantype"],
                filter(lambda x: playerid == x["id"], bannedpeople),
            )
        ):
            # print("eee",list(filter(lambda x: playerid == x["id"],bannedpeople)))
            # print(f"banreason {list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["baninfo"]}")
            # print(f'!rcon kickid {message["kickid"]} {list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["baninfo"]}'),"fake context")
            # print(f'kickid {message["kickid"]} You are banned: {list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["baninfo"]} Expires: {(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).strftime(f"%-d{'th' if 11 <= datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day % 10, 'th')} of %B %Y")) if list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"] else "never"}')
            # asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,f'kickid {message["kickid"]} You are banned: {list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["baninfo"]} Expires: {(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).strftime(f"%-d{'th' if 11 <= datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"]).day % 10, 'th')} of %B %Y")) if list(filter(lambda x: playerid == x["id"],bannedpeople))[0]["expire"] else "never"}'),"fake context",None,True,False), bot.loop)
            sendrconcommand(
                serverid,
                f"banip 7200 {message['ip']} You are banned: {list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['baninfo']} Expires: {(datetime.fromtimestamp(list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['expire']).strftime(f'%-d{"th" if 11 <= datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"], bannedpeople))[0]["expire"]).day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"], bannedpeople))[0]["expire"]).day % 10, "th")} of %B %Y')) if list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['expire'] else 'never'}",
                sender=None,
            )

            return
        # print("e",list(filter(lambda x: playerid == x["id"],bannedpeople)))
        sendrconcommand(
            serverid,
            f"!muteplayer {message['kickid']} {PREFIXES['warning']}{(datetime.fromtimestamp(list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['expire']).strftime(f'%-d{"th" if 11 <= datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"], bannedpeople))[0]["expire"]).day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(datetime.fromtimestamp(list(filter(lambda x: playerid == x["id"], bannedpeople))[0]["expire"]).day % 10, "th")} of %B %Y')) if list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['expire'] else 'never'} rsn {PREFIXES['warning']}{list(filter(lambda x: playerid == x['id'], bannedpeople))[0]['baninfo']}",
            sender=None,
        )


def findallbannedpeople(potentialbans, originalbans, bandepth):
    """Recursively finds all banned players using ban depth tracking"""
    newbans = []
    keeppotential = []
    for potential in potentialbans:
        matched = False
        for originalban in filter(lambda x: x["exhaustion"] <= bandepth, originalbans):
            if potential["ip"] == originalban["ip"] or (
                str(potential["uid"]) == str(originalban["uid"])
                and len(str(potential["uid"])) >= 10
            ):
                newbans.append(
                    {
                        **potential,
                        "banlinks": originalban["banlinks"],
                        "bantype": originalban["bantype"],
                        "baninfo": originalban["baninfo"],
                        "expire": originalban["expire"],
                        "exhaustion": originalban["exhaustion"] + 1,
                        "origbanid": getpriority(originalban, "origbanid", "id"),
                    }
                )
                matched = True
                break
        if not matched:
            keeppotential.append(potential)
    if newbans:
        return findallbannedpeople(keeppotential, [*newbans, *originalbans], bandepth)
    else:
        return originalbans


def displayendofroundstats(message, serverid, isfromserver):
    """Calculates and displays comprehensive end-of-round statistics including kills, deaths, and performance metrics"""
    # print("HEREEE")
    global maxkills, lexitoneapicache
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)

    if not isfromserver:
        tfdb = postgresem("./data/tf2helper.db")
        c = tfdb
        c.execute(
            """SELECT matchid
        FROM matchid
        WHERE serverid = ?
        ORDER BY time DESC
        LIMIT 1;""",
            (serverid,),
        )
        matchid = c.fetchone()
        if matchid:
            matchid = matchid[0]
        tfdb.close()
    else:
        matchid = message.get("matchid", False)
        #     messageflush.append({
        #     "timestamp": int(time.time()),
        #     "serverid": data["server_id"],
        #     "type": 3,
        #     "globalmessage": False,
        #     "overridechannel": None,
        #     "messagecontent": f"{data.get('attacker_name', data['attacker_type'])} killed {data.get('victim_name', data['victim_type'])} with {WEAPON_NAMES.get(data['cause_of_death'], data['cause_of_death'])}",
        #     "metadata": {"type":"killfeed"},
        #     "servername": context["serveridnamelinks"][data["server_id"]]
        # })
    # discordtotitanfall[serverid]["messages"].append(
    # {
    #     "id": int(time.time()*100),
    #     "content":str("eeee"),
    #     "teamoverride": 4,
    #     "isteammessage": False,
    #     "uidoverride": []
    #     # "dotreacted": dotreacted
    # }
    # )
    # we'll want the matchid - I'll just send it as a weird custom param
    while True:
        colour = random.randint(0, 255)
        # colour = random.choice([254,219,87])
        # dissallowedcolours colours (unreadable)  (too dark)
        if colour not in DISALLOWED_COLOURS:
            break

    # matchid = message.get("matchid",False)
    # if not matchid:
    #     matchid = getpriority(message,"originalmessage").split(" ")[1]

    # discordtotitanfall[serverid]["messages"].append(
    # {
    # # "id": str(int(time.time()*100)),
    # "content":"begin",
    # # "teamoverride": 4,
    # # "isteammessage": False,
    # # "uidoverride": [getpriority(message,"uid",["meta","uid"])]
    # }
    # )
    # pull stats
    # playercontext[serverid][player["uid"]][player["name"]][matchid].append({
    # playercontext[serverid][player["uid"]][player["name"]][matchid] = [{
    # playercontext is not really a good varible for this, if somone crashed it won't accumulate, right? na it does, past me is AWESOME
    # pull killstreaks
    # maxkills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)
    # what I would want to display is likely:
    # TOP KD (second top, too)
    # TOP KILLS PER MINUTE (second top, too)
    # MOST DEATHS
    # BEST GUN //nutone could cache it tho (second top, too)
    # NPC KILLS AGAINST PLAYERS //nutone could cache it tho
    # TOP KILLSTREAK (second top, too)
    # TOTAL KILLS
    # TOTAL DEATHS
    matchdata = {}
    colour = f"[38;5;{colour}m"

    output = {"header": f"{colour}Match stats:"}
    stringslist = {"general": [], "personal": []}
    if not istf1:
        pass  # quering this db takes a long time, and doing this is really time sensitive
        # I do want this though..
        # try:
        #     tfdb = postgresem("./data/tf2helper.db")
        #     c = tfdb

        #     c.execute(
        #         """
        #         SELECT cause_of_death, COUNT(*) as kill_count
        #         FROM specifickilltracker
        #         WHERE match_id = ?
        #         GROUP BY cause_of_death
        #         ORDER BY kill_count DESC
        #         LIMIT 3
        #         """,
        #         (matchid,)
        #     )

        #     top_weapons = c.fetchall()
        #     matchdata["topguns"] = {x[0]:x[1] for x in top_weapons}
        # except sqlite3.OperationalError:
        #     print("sob")
        #     pass
        # c.close()
        # tfdb.close()
    # str(x[0]+1)+') '
    #     lexitoneapicache[list(lexitoneapicache.keys())[-1]].extend(
    #  [
    #         {
    #             "victimtype": "player",
    #             "attackertype": "player",
    #             "weapon": "titan_execution",
    #             "victimtitan": "ion",
    #             "attackertitan": "ion",
    #             "victimname": "LexiGlasss",
    #             "attackername": "LexiGlasss"
    #         },
    #                 {
    #             "victimtype": "player",
    #             "attackertype": "player",
    #             "weapon": "titan_execution",
    #             "victimtitan": "ion",
    #             "attackertitan": "ronin",
    #             "victimname": "LexiGlasss",
    #             "attackername": "LexiGlasss"
    #         },
    #                 {
    #             "victimtype": "player",
    #             "attackertype": "player",
    #             "weapon": "titan_execution",
    #             "victimtitan": "ion",
    #             "attackertitan": "ronin",
    #             "victimname": "LexiGlasss",
    #             "attackername": "LexiGlasss"
    #         }
    #     ])

    maxshow = 1
    moremaxshow = 3
    if matchid in maxkills:
        print("MAXKILLS MATCHID", maxkills[matchid])
        # print("bleh",json.dumps(flattendict(maxkills[matchid]),indent=4))
        # maxkills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)
        matchdata["ks"] = sorted(
            list(
                functools.reduce(
                    lambda a, b: {**a, b[0]: max(b[1].values())}
                    if max(b[1].values()) > 1
                    else a,
                    maxkills[matchid].items(),
                    {},
                ).items()
            ),
            key=lambda x: x[1],
            reverse=True,
        )[:moremaxshow]
        # matchdata["ks"] = list(({x[0]:x[-1] for x in filter(lambda x: x[-1] > 0,sorted(flattendict(maxkills[matchid]),key = lambda x: x[-1],reverse=True))}).items())[:moremaxshow]
        if matchdata["ks"]:
            output["ks"] = (
                f"{colour}Highest killstreak{PREFIXES['chatcolour']}: {', '.join(list(map(lambda x: PREFIXES['stat'] + str(x[0] + 1) + ') ' + x[1][0] + ': ' + PREFIXES['stat'] + str(x[1][1]) + PREFIXES['chatcolour'] + '', enumerate(matchdata['ks']))))}"
            )
    # print("API",json.dumps(lexitoneapicache,indent=4))
    if matchid in lexitoneapicache:
        # for kill in lexitoneapicache[matchid]:
        # I am working under the assumption that I KNOW what titan both are
        matchdata["npckillsagainstplayers"] = dict(
            sorted(
                functools.reduce(
                    lambda a, b: {**a, b["victimname"]: a.get(b["victimname"], 0) + 1}
                    if b["victimtype"] in ["npc_titan", "player"]
                    and b["attackertype"]
                    in [
                        "npc_soldier",
                        "npc_spectre",
                        "npc_super_spectre",
                        "npc_stalker",
                        "worldspawn",
                        "trigger_hurt",
                        "prop_dynamic",
                    ]
                    else a,
                    lexitoneapicache[matchid],
                    {},
                ).items(),
                key=lambda x: x[1],
                reverse=True,
            )
        )
        matchdata["tnpckillsagainstplayers"] = functools.reduce(
            lambda a, b: a + b, matchdata["npckillsagainstplayers"].values(), 0
        )
        matchdata["titankds"] = dict(
            sorted(
                list(
                    functools.reduce(
                        lambda a, b: (
                            {
                                **a,
                                b["attackertitan"]: {
                                    "kills": a.get(b["attackertitan"], {}).get(
                                        "kills", 0
                                    )
                                    + 1,
                                    "deaths": a.get(b["attackertitan"], {}).get(
                                        "deaths", 0
                                    ),
                                },
                                b["victimtitan"]: {
                                    "kills": a.get(b["victimtitan"], {}).get(
                                        "kills", 0
                                    ),
                                    "deaths": a.get(b["victimtitan"], {}).get(
                                        "deaths", 0
                                    )
                                    + 1,
                                },
                            }
                            if b["attackertitan"] != b["victimtitan"]
                            else {
                                **a,
                                b["attackertitan"]: {
                                    "kills": a.get(b["attackertitan"], {}).get(
                                        "kills", 0
                                    )
                                    + 1,
                                    "deaths": a.get(b["attackertitan"], {}).get(
                                        "deaths", 0
                                    )
                                    + 1,
                                },
                            }
                        )
                        if (
                            b["attackertitan"] != "null"
                            and b["attackertitan"] != None
                            and b["victimtitan"] != "null"
                            and b["victimtitan"] != None
                        )
                        else a,
                        lexitoneapicache[matchid],
                        {},
                    ).items()
                ),
                key=lambda x: x[1]["kills"] / max(x[1]["deaths"], 1),
                reverse=True,
            )
        )
        matchdata["topweapons"] = dict(
            sorted(
                functools.reduce(
                    lambda a, b: {**a, b["weapon"]: a.get(b["weapon"], 0) + 1}
                    if b["attackertype"] in ["npc_titan", "player"]
                    and b["victimtype"] in ["npc_titan", "player"]
                    else a,
                    lexitoneapicache[matchid],
                    {},
                ).items(),
                key=lambda x: x[1],
                reverse=True,
            )
        )
        # print("titankds",matchdata["titankds"])
        # print(functools.reduce(lambda a,b: ({**a,b["attackertitan"]:{"kills":a.get(b["attackertitan"],{}).get("kills",0)+1, "deaths":a.get(b["attackertitan"],{}).get("deaths",0)},b["victimtitan"]:{"kills":a.get(b["victimtitan"],{}).get("kills",0), "deaths":a.get(b["victimtitan"],{}).get("deaths",0)+1}} if  b["attackertitan"] != b["victimtitan"] else {**a,b["attackertitan"]:{"kills":a.get(b["attackertitan"],{}).get("kills",0)+1, "deaths":a.get(b["attackertitan"],{}).get("deaths",0)+1}} )if (b["attackertitan"] != "null" and b["attackertitan"] != None and b["victimtitan"] != "null" and b["victimtitan"] != None) else a, lexitoneapicache[matchid],{}))

        if matchdata["titankds"]:
            output["tkd"] = (
                f"{colour}Titan kds{PREFIXES['chatcolour']}: {', '.join(list(map(lambda x: PREFIXES['stat'] + str(x[0] + 1) + ') ' + TITAN_NAMES.get(x[1][0], x[1][0]) + ': ' + PREFIXES['stat'] + str(int((x[1][1]['kills'] / max(x[1][1]['deaths'], 1)) * 100) / 100) + PREFIXES['chatcolour'] + '', enumerate(list(matchdata['titankds'].items())[:moremaxshow]))))} "
                + (
                    f"{PREFIXES['stat2']}Lowest) {list(matchdata['titankds'].keys())[-1]}: {int((list(matchdata['titankds'].values())[-1]['kills'] / list(matchdata['titankds'].values())[-1]['deaths']) * 100) / 100}"
                    if len(matchdata["titankds"].keys()) > moremaxshow
                    else ""
                )
            )
        if matchdata["topweapons"]:
            output["tg"] = (
                f"{colour}Top guns{PREFIXES['chatcolour']}: {', '.join(list(map(lambda x: PREFIXES['stat'] + '' + WEAPON_NAMES.get(x[1][0], x[1][0]) + ': ' + PREFIXES['stat'] + str(x[1][1]) + PREFIXES['chatcolour'] + ' kill' + ('s' if x[1][1] - 1 else ''), enumerate(list((matchdata['topweapons']).items())[:3]))))}"
            )
    if serverid in playercontext:
        for playerdata in playercontext[serverid].values():
            for playername, datafrommatch in playerdata.items():
                datafrommatch = list(
                    filter(lambda x: x[0] == matchid, datafrommatch.items())
                )
                if not datafrommatch:
                    continue
                datafrommatch = datafrommatch[0]
                kills = functools.reduce(
                    lambda a, b: a + b["kills"], datafrommatch[1], 0
                )
                deaths = functools.reduce(
                    lambda a, b: a + b["deaths"], datafrommatch[1], 0
                )
                timeplayed = functools.reduce(
                    lambda a, b: a + b["endtime"] - b["joined"], datafrommatch[1], 0
                )
                matchdata.setdefault("kpm", {})
                matchdata.setdefault("kills", {})
                matchdata.setdefault("deaths", {})
                matchdata.setdefault("kd", {})
                matchdata.setdefault("tkills", 0)
                matchdata.setdefault("tdeaths", 0)
                # matchdata["kills"][playername] = kills // who cares!
                matchdata["tkills"] += kills
                matchdata["tdeaths"] += deaths
                matchdata["deaths"][playername] = deaths
                matchdata["kpm"][playername] = float(
                    f"{(kills / (timeplayed / 60) if timeplayed else 0):.2f}"
                )
                matchdata["kd"][playername] = float(
                    f"{(kills / deaths if deaths else kills):.2f}"
                )

        if "kd" in matchdata:
            matchdata["kd"] = dict(
                sorted(matchdata["kd"].items(), key=lambda x: x[1], reverse=True)
            )
        if "kpm" in matchdata:
            matchdata["kpm"] = dict(
                sorted(matchdata["kpm"].items(), key=lambda x: x[1], reverse=True)
            )
        if "deaths" in matchdata:
            matchdata["deaths"] = dict(
                sorted(matchdata["deaths"].items(), key=lambda x: x[1], reverse=True)
            )

        if matchdata.get("tkills"):
            stringslist["general"].append(
                f"{colour}Total kills: {PREFIXES['stat']}{matchdata['tkills']}"
            )
        if matchdata.get("tdeaths"):
            stringslist["general"].append(
                f"{colour}Total deaths: {PREFIXES['stat']}{matchdata['tdeaths']}"
            )
        # print(list(matchdata["kd"].values()))
        if matchdata.get("kd", False) and max(matchdata["kd"].values()) > 0:
            stringslist["personal"].append(
                f"{colour}K/D: {', '.join(list(map(lambda x: PREFIXES['stat'] + '' + str(x[1][0]) + ': ' + str(x[1][1]) + PREFIXES['chatcolour'] + '', enumerate(list(matchdata['kd'].items())[:maxshow]))))}"
            )
        if matchdata.get("kpm", False) and max(matchdata["kpm"].values()) > 0:
            stringslist["personal"].append(
                f"{colour}K/min: {', '.join(list(map(lambda x: PREFIXES['stat'] + '' + str(x[1][0]) + ': ' + str(x[1][1]) + PREFIXES['chatcolour'] + '', enumerate(list(matchdata['kpm'].items())[:maxshow]))))}"
            )
        if matchdata.get("deaths", False) and max(matchdata["deaths"].values()) > 0:
            stringslist["personal"].append(
                f"{colour}Deaths: {', '.join(list(map(lambda x: PREFIXES['stat'] + '' + str(x[1][0]) + ': ' + str(x[1][1]) + PREFIXES['chatcolour'] + '', enumerate(list(matchdata['deaths'].items())[:maxshow]))))}"
            )

        # output["general"] = f"{colour}General {PREFIXES['chatcolour']}Total kills: {PREFIXES['stat']}{matchdata['tkills']}{PREFIXES['chatcolour']} | Total Deaths: {PREFIXES['stat']}{matchdata['tdeaths']} "
        # output["top"] =  f"{colour}Top players {PREFIXES['chatcolour']}K/D: {', '.join(list(map(lambda x: PREFIXES['stat']+    ''    +x[1][0]+': '+str(x[1][1])+PREFIXES['chatcolour']+'',enumerate(list(matchdata['kd'].items())[:maxshow]))))} {PREFIXES['chatcolour']}| K/min: {', '.join(list(map(lambda x: PREFIXES['stat']+    ''    +x[1][0]+': '+str(x[1][1])+PREFIXES['chatcolour']+'',enumerate(list(matchdata['kpm'].items())[:maxshow]))))} {PREFIXES['chatcolour']}| Deaths: {', '.join(list(map(lambda x: PREFIXES['stat']+    ''    +x[1][0]+': '+str(x[1][1])+PREFIXES['chatcolour']+'',enumerate(list(matchdata['deaths'].items())[:maxshow]))))} "
    if matchid in lexitoneapicache:
        # if "general" in output:
        if matchdata["tnpckillsagainstplayers"]:
            stringslist["general"].append(
                f"{colour}NPC kills: {PREFIXES['stat']}{matchdata['tnpckillsagainstplayers']}"
            )
        if (
            matchdata["npckillsagainstplayers"]
            and max(matchdata["npckillsagainstplayers"].values()) > 0
        ):
            # output["top"] = output["top"] +f"| Npc Deaths: {', '.join(list(map(lambda x: PREFIXES['stat']+    ''    +x[1][0]+': '+str(x[1][1])+PREFIXES['chatcolour']+'',enumerate(list(matchdata['npckillsagainstplayers'].items())[:maxshow]))))}"
            stringslist["personal"].append(
                f"{colour}NPC deaths: {', '.join(list(map(lambda x: PREFIXES['stat'] + '' + str(x[1][0]) + ': ' + str(x[1][1]) + PREFIXES['chatcolour'] + '', enumerate(list(matchdata['npckillsagainstplayers'].items())[:maxshow]))))}"
            )

    for key, value in stringslist.items():
        if value:
            output[key] = f"{colour} | ".join(value)
    if len(output) < 2:
        return ""
    for key, value in output.items():
        if key not in ["general", "ks", "topweapons"]:
            continue
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(i)+str(int(time.time()*100)),
                "content": value,
                "teamoverride": 4,
                "isteammessage": False,
                # "uidoverride": [getpriority(message,"uid",["meta","uid"])]
            }
        )
    # return top_weapons
    # print("MATCHDATA",json.dumps(matchdata,indent=4))
    #     messageflush.append({
    #     "timestamp": int(time.time()),
    #     "serverid": serverid,
    #     "type": 4,
    #     "globalmessage": False,
    #     "overridechannel": None,
    #     "messagecontent": "\n".join(list(output.values())),
    #     "metadata": {"type":"endofroundstats"},
    #     "servername": context["serveridnamelinks"][serverid]
    # })
    return "\n" + "\n".join(list(output.values()))
    print(json.dumps(output, indent=4))
    print(json.dumps(matchdata, indent=4))
    # discordtotitanfall[serverid]["messages"].append(
    # {
    # # "id": str(int(time.time()*100)),
    # "content":"end",
    # # "teamoverride": 4,
    # # "isteammessage": False,
    # # "uidoverride": [getpriority(message,"uid",["meta","uid"])]
    # }
    # )

def changename(message, serverid, isfromserver):
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    if not message["originalmessage"].split(" ")[1:]:
        # reset
        sendrconcommand(
            serverid,
            f"!forcesomonesname {getpriority(message,"uid",["meta","uid"])} {resolveplayeruidfromdb(getpriority(message,"uid",["meta","uid"]), None, True, istf1)[0]["name"]}",
            sender=getpriority(message,"originalname","name"),
        )
    togglepersistentvar(message, serverid, isfromserver)


def togglepersistentvar(message, serverid, isfromserver):
    """Toggles persistent server variables like stats tracking and notifications"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    args = message["originalmessage"].split(" ")[1:]
    if faketoggle := (message["originalmessage"].split(" ")[0] != f"{keyletter}toggle"): # fake the toggle to the server :)
        args.insert(0, message["originalmessage"].split(" ")[0][1:]) 
        

    



            
   
    
    if (commandnotenabledonthisserver := (
            len(args) and
             int(serverid) not in getpriority(
        context,
        [
            "commands",
            "ingamecommands",
            args[0],
            "serversenabled",
        ],nofind=[int(serverid)])
        )) or (len(args) and getpriority(context,["commands","ingamecommands",args[0]]) and  resolvecommandperms(serverid,args[0]) and not checkrconallowedtfuid( getpriority(message, "uid", ["meta", "uid"]), resolvecommandperms(serverid,args[0],True),serverid=serverid,))or (not len(args) or (args[0] not in [
        *list(
            map(
                lambda x: x[0],
                filter(
                    lambda x: x[1].get("run") == "togglestat",
                    context["commands"]["ingamecommands"].items(),
                ),
            )
        )] and not faketoggle)):
        # we need to find all the toggle commands! they all run toggle stats.
        cmdcounter = 0
        if not commandnotenabledonthisserver or not len(args):
            for name, command in context["commands"]["ingamecommands"].items():
                if (
                    command.get("run") == "togglestat"
                    and ("tf1" if istf1 else "tf2") in command["games"]
                    and (
                        not resolvecommandperms(serverid,name)
                        or checkrconallowedtfuid(
                            getpriority(message, "uid", ["meta", "uid"]),
                            resolvecommandperms(serverid,name,True),
                            serverid=serverid,
                        )
                    )
                    and (
                        not command.get("serversenabled", False)
                        or int(serverid) in command["serversenabled"]
                    )

                    and not command.get("alias")
                ):

                    cmdcounter += 1
                    discordtotitanfall[serverid]["messages"].append(
                        {
                            # "id": str(i) + str(int(time.time()*100)),
                            "content": f"{PREFIXES['discord']}{PREFIXES['gold']}{cmdcounter}) {PREFIXES['bronze'] + resolvecommandperms(serverid,name) + ' ' if resolvecommandperms(serverid,name) else ''}{PREFIXES['commandname'] if not istf1 else PREFIXES['commandname']}{keyletter}toggle {name}{PREFIXES['chatcolour'] if not cmdcounter % 2 else PREFIXES['offchatcolour']}: {command['description']}",
                            # "teamoverride": 4,
                            # "isteammessage": False,
                            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                            # "dotreacted": dotreacted
                        }
                    )
        else:
            cmdcounter+=1
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(i) + str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']}{PREFIXES['warning']}Could not toggle {args[0]}{PREFIXES['chatcolour']} - it is not enabled on this server",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    # "dotreacted": dotreacted
                }
            )
        if len(args) and getpriority(context,["commands","ingamecommands",args[0]]) and  resolvecommandperms(serverid,args[0]) and not checkrconallowedtfuid( getpriority(message, "uid", ["meta", "uid"]), resolvecommandperms(serverid,args[0],True),serverid=serverid,) and not commandnotenabledonthisserver:
            cmdcounter+=1
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(i) + str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']}{PREFIXES['warning']}Could not toggle {args[0]}{PREFIXES['chatcolour']} - you need {PREFIXES['commandname']}{translaterole(serverid,resolvecommandperms(serverid,args[0]))}",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    # "dotreacted": dotreacted
                }
            )
        if args and (args[0] not in [
            *list(
                map(
                    lambda x: x[0],
                    filter(
                        lambda x: x[1].get("run") == "togglestat",
                        context["commands"]["ingamecommands"].items(),
                    ),
                )
            ),
            "help",
            "h",
        ] and not faketoggle):
            cmdcounter += 1
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}{PREFIXES['warning']} Could not find the toggle for {args[0]}",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    # "dotreacted": dotreacted
                }
            )
        if cmdcounter > 11 - bool(
            args
            and args[0]
            not in [
                *list(
                    map(
                        lambda x: x[0],
                        filter(
                            lambda x: x[1].get("run") == "togglestat",
                            context["commands"]["ingamecommands"].items(),
                        ),
                    )
                )
            ]
            and args[0] not in ["help", "h"]
        ):
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}[38;5;201m[{cmdcounter - 10}]{PREFIXES['warning']} More command{'s' if cmdcounter - 10 > 1 else ''} hidden above.{PREFIXES['commandname']} open chat box and press up arrow {PREFIXES['warning']}to see them!",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    # "dotreacted": dotreacted
                }
            )
        return
    togglestats(message, context["commands"]["ingamecommands"][args[0]].get("alias",args[0]), serverid," ".join(args[1:]))


def showingamesettings(message, serverid, isfromserver):
    """Displays current server settings and configuration to players"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    if len(message.get("originalmessage", "w").split(" ")) > 1:
        account = resolveplayeruidfromdb(
            (" ".join(message["originalmessage"].split(" ")[1:])), None, True, istf1
        )
        if not account:
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['discord']}Specified player not found {'(They might not have discord linked)' if istf1 else ''}",
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                }
            )
            return
        name = account[0]["name"]
        uid = account[0]["uid"]
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}Showing settings for {name}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )

    else:
        name = getpriority(message, "originalname", "name")
        uid = getpriority(message, "uid", ["meta", "uid"])
        if not istf1:
            sendrconcommand(
                serverid,
                f"!reloadpersistentvars {getpriority(message, 'uid', ['meta', 'uid'], 'originalname', 'name')}",
                sender=getpriority(message, "originalname"),
            )

    if istf1 and not len(str(getpriority(message, "uid", ["meta", "uid"]))) > 15:
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}No discord account linked, cannot pull settings",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )
        return
    preferencesuid = getpriority(
        readplayeruidpreferences(uid, istf1), ["tf1" if istf1 else "tf2"]
    )
    if not preferencesuid:
        preferencesuid = {}
    discorduid = pullid(uid, "discord")
    discordstats = {}
    if discorduid:
        c = postgresem("./data/tf2helper.db")
        c.execute(
            "SELECT discorduid, chosencolour,choseningamecolour, nameprefix FROM discorduiddata WHERE discorduid = ?",
            (discorduid,),
        )
        output = c.fetchall()
        c.close()
        # print(output)
        teams = ["FRIENDLY", "ENEMY", "NEUTRAL"]
        discordstats = {
            x[0]: {
                "nameprefix": (x[3]) if x[3] and x[3] != "reset" else None,
                "discordcolour": list(
                    map(
                        lambda y: tuple(map(int, y.strip("()").split(","))),
                        x[1].split("|"),
                    )
                )
                if x[1] is not None and x[1] != "reset"
                else [],
                **(
                    (
                        {
                            team: (
                                list(
                                    map(
                                        lambda y: tuple(
                                            map(int, y.strip("()").split(","))
                                        ),
                                        x[2].split("|"),
                                    )
                                )
                            )
                            for team in teams
                        }
                        if "[" not in x[2]
                        else json.loads(x[2])
                    )
                    if x[2] is not None and x[2] != "reset"
                    else {}
                ),
            }
            for x in output
        }

    else:
        discorduid = None
    cmdcounter = 0
    if not any(
        list(map(lambda x: x if x != False else True, {
            **preferencesuid,
            **(discordstats.get(discorduid, {}) if discorduid else {}),
        }.values()))
    ):
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(i) + str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}No settings found for {PREFIXES['commandname']}{name}",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )
    for name, command in {
        **preferencesuid,
        **(discordstats.get(discorduid, {}) if discorduid else {}),
    }.items():
        if command in (None, []):
            continue
        cmdcounter += 1
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(i) + str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}{PREFIXES['gold']}{cmdcounter}) {PREFIXES['commandname'] if not istf1 else PREFIXES['commandname']}{name}{PREFIXES['chatcolour'] if not cmdcounter % 2 else PREFIXES['offchatcolour']}: {command}",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )
    if cmdcounter > 11:
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}[38;5;201m[{cmdcounter - 10}]{PREFIXES['warning']} More Setting{'s' if cmdcounter - 10 > 1 else ''} hidden above.{PREFIXES['commandname']} open chat box and press up arrow {PREFIXES['warning']}to see them!",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )


def togglestats(message, togglething, serverid,overridename = None):
    """Toggles various statistics tracking features for players"""
    # print(togglething,serverid)
    internaltoggle = context["commands"]["ingamecommands"][togglething].get(
        "internaltoggle", togglething
    )
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    if istf1 and not len(str(getpriority(message, "uid", ["meta", "uid"]))) > 15:
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}No discord account linked, cannot toggle {togglething} (the server has no way of knowing who you are)",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )
        return

    preferences = readplayeruidpreferences(
        getpriority(message, "uid", ["meta", "uid"]), istf1
    )
    
    shouldset = overridename if overridename != None else getpriority(preferences, ["tf1" if istf1 else "tf2", internaltoggle])
    if shouldset == None:
        shouldset = False

    setplayeruidpreferences(
        ["tf1" if istf1 else "tf2", internaltoggle],
        (not shouldset if isinstance(shouldset,bool) else shouldset),
        getpriority(message, "uid", ["meta", "uid"]),
        istf1,
    )
    if context["commands"]["ingamecommands"][togglething].get("description", False):
        discordtotitanfall[serverid]["messages"].append(
            {
                "content": f"{PREFIXES['discord']}(desc) {context['commands']['ingamecommands'][togglething]['description']}",
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            }
        )

    discordtotitanfall[serverid]["messages"].append(
        {
            # "id": str(int(time.time()*100)),
            "content": f"{PREFIXES['discord']}Toggled {togglething} - is now {PREFIXES['stat']}{(not shouldset if isinstance(shouldset,bool) else shouldset)}",
            # "teamoverride": 4,
            # "isteammessage": False,
            "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
            # "dotreacted": dotreacted
        }
    )
    if not istf1:
        sendrconcommand(
            serverid,
            f"!reloadpersistentvars {getpriority(message, 'uid', ['meta', 'uid'], 'originalname', 'name')}",
            sender=getpriority(message, "originalname"),
        )
    for stat in context["commands"]["ingamecommands"][togglething].get(
        "extendeddesc", []
    ):
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}{PREFIXES['offchatcolour']}{stat}",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )


# def throwplayer(message,serverid,isfromserver):
#     # print("RUNNNING THROW")
#     # asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,f'!throw {}',"fake context",None,True,False), bot.loop)
#     # asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,f'!throw {" ".join(getpriority(message,"originalmessage").split(" ")[1:])}'),"fake context",None,True,False), bot.loop)
#     # asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid,f'!throw {" ".join(getpriority(message,"originalmessage").split(" ")[1:])}'),"fake context",None,True,False), bot.loop)
#     # human = (f'{" ".join(getpriority(message, "originalmessage").split(" ")[1:])}')
#     asyncio.run_coroutine_threadsafe(returncommandfeedback(*sendrconcommand(serverid, f'!throw {" ".join(getpriority(message, "originalmessage").split(" ")[1:])}'), "fake context", None, True, False), bot.loop)


def ingamehelp(message, serverid, isfromserver):
    """Displays help information for in-game commands to players"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    backslash = ""
    # uid = getpriority(message,"uid",["meta","uid"])
    commandoverride = False
    if len(getpriority(message, "originalmessage", "type").split(" ")) > 1:
        commandoverride = getpriority(message, "originalmessage", "type").split(" ")[1]
    if not commandoverride:
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}Help menu for the discord bot",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                # "dotreacted": dotreacted
            }
        )
    cmdcounter = 0
    for i, (name, command) in enumerate(context["commands"]["ingamecommands"].items()):
        # print("CHECKING COMMAND", (getpriority(command,"uid",["meta","uid"])),command)
        # print("tf1" if istf1 else "tf2","tf1" if istf1 else "tf2" in command["games"])
        # print("BLEH",(not command.get("permsneeded",False) or checkrconallowedtfuid(getpriority(message,"uid",["meta","uid"]))))
        # print(  (not command.get("permsneeded",False) or checkrconallowedtfuid(getpriority(message,"uid",["meta","uid"])),command.get("permsneeded",False)) )
        if (
            name != "helpdc"
            and ((not commandoverride and not command.get("hiddencommand", False)) or (commandoverride and commandoverride.lower() in name))
            and ("tf1" if istf1 else "tf2") in command["games"]
            and (
                not resolvecommandperms(serverid,name)
                or checkrconallowedtfuid(
                    getpriority(message, "uid", ["meta", "uid"]),
                    resolvecommandperms(serverid,name,True),
                    serverid=serverid,
                )
            )
            and (
                not command.get("serversenabled", False)
                or int(serverid) in command["serversenabled"]
            )
            and command.get("run") != "togglestat"
            and not command.get("alias")
        ):
            cmdcounter += 1
            extra = False
            if command.get("aliases"):
                extra = ", ".join(command["aliases"])
            # print(name,resolvecommandperms(serverid,name))
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(i) + str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']}{PREFIXES['gold']}{cmdcounter}) {PREFIXES['bronze'] + resolvecommandperms(serverid,name) + ' ' if resolvecommandperms(serverid,name) else ''}{PREFIXES['commandname']}{name}{', ' + extra if extra else ''}{PREFIXES['chatcolour'] if not cmdcounter % 2 else PREFIXES['offchatcolour']}: {command['description']}",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"])],
                    # "dotreacted": dotreacted
                }
            )
    if cmdcounter > 11:
        discordtotitanfall[serverid]["messages"].append(
            {
                # "id": str(int(time.time()*100)),
                "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}[38;5;201m[{cmdcounter - 10}]{PREFIXES['warning']} More command{'s' if cmdcounter - 10 > 1 else ''} hidden above.{PREFIXES['commandname']} open chat box and press up arrow {PREFIXES['warning']}to see them!",
                # "teamoverride": 4,
                # "isteammessage": False,
                "uidoverride": ([getpriority(message, "uid", ["meta", "uid"])]),
                # "dotreacted": dotreacted
            }
        )


def recievetitanfallcommands(message, serverid, isfromserver):
    global tfcommandspermissions
    # print(json.dumps(message,indent=4))
    tfcommandspermissions[serverid] = {**tfcommandspermissions.get(serverid,{}),**message}# dict(map(lambda x: [x[0],list(x[1].keys())], message.items()))
    # print(json.dumps(tfcommandspermissions[serverid],indent=4))
    hasoverriden = False
    for command,perms in tfcommandspermissions[serverid].get("discordcommands",{}).items():
        # print(command,perms)
        # override serversenabled
        if int(serverid) in getpriority(context,["commands","ingamecommands",command,"serversenabled"],nofind = [int(serverid)]):
            continue
        # at this point, we must override serversenabled (HORRIBLE SOLOUTION THIS IS GLOBAL WHAT WAS I THINKING WAIT WTF BIGGEST BRAIN FART IT'S NOT YOU DINGUS)
        hasoverriden = True
        context["commands"]["ingamecommands"][command]["serversenabled"].append(int(serverid))
    if hasoverriden:
        print("I overrided something!")

    print("Loaded commands for",serverid)

def senddiscordcommands(message, serverid, isfromserver):
    """Sends Discord-specific commands from in-game chat"""
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    print(
        "COMMANDS REQUESTED FROM",serverid,
        f"!senddiscordcommands {' '.join(functools.reduce(lambda a, b: [*a, b[0], str(int(b[1].get("shouldblock")))],filter(lambda x: int (serverid) in x[1].get("serversenabled",[int(serverid)]) and (not x[1].get("games") or ("tf1" if istf1 else "tf2") in x[1]["games"] ) ,context['commands']['ingamecommands'].items()), []))}",
    )
    sendrconcommand(
        serverid,
        f"!senddiscordcommands {' '.join(functools.reduce(lambda a, b: [*a, b[0], str(int(b[1].get("shouldblock")))],filter(lambda x: int (serverid) in x[1].get("serversenabled",[int(serverid)]) and (not x[1].get("games") or ("tf1" if istf1 else "tf2") in x[1]["games"] ) ,context['commands']['ingamecommands'].items()), []))}",
        sender=None,
    )
def natterforcoolperks(message, serverid, isfromserver):
    """Natters someone for the coolperks role"""

    # print("meow")
    if context.get("coolperksnatter").isdigit() and not int(context.get("coolperksnatter")):
        return

    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)

    # checks
    # print(json.dumps(message, indent=4))

    # player does not have coolperksrole
    # player has more than like 5 mins playtime
    # someone with a good kd is not on the server

    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    c.execute(
        f"SELECT COALESCE(SUM(duration), 0) FROM playtime{'tf1' if istf1 else ''} WHERE playeruid = ?",
        (getpriority(message, 'uid', ['meta', 'uid'], 'name'),)
    )

    timeplayed = c.fetchone()
    # print( checkrconallowedtfuid(getpriority(message, 'uid', ['meta', 'uid']), 'coolperksrole', serverid=serverid))
    # print(((not timeplayed or not timeplayed[0] or timeplayed[0] < 1800) and not istf1))
    if (
        checkrconallowedtfuid(getpriority(message, 'uid', ['meta', 'uid']), 'coolperksrole', serverid=serverid)
        # or somoneisreallygoodontheserver
        # or playtimeissmol
        or ((not timeplayed or not timeplayed[0] or timeplayed[0] < 1800) and not istf1)
    ):
        pass
        return
    if  getpriority(
            readplayeruidpreferences(
                getpriority(message, "uid", ["meta", "uid"], "name"), istf1
            ),
            ["tf1" if istf1 else "tf2", "adblock"],
        ):
        return
        # print("adblock enabled")
    # print(getpriority(message, 'uid', ['meta', 'uid'], 'name'),"natter")
    # time.sleep(10)
    discordtotitanfall[serverid]["messages"].append({
        "content": f"{context["coolperksnatter"]}",
        "uidoverride": [getpriority(message, 'uid', ['meta', 'uid'], 'name')],
    })

# Go to https://ko-fi.com/dyslexi or boost the server (preferably the former)
def killstatfortf1(message, serverid, isfromserver):
    # print(json.dumps(message,indent=4))
    if len(message.get("attacker_id","")) < 15:
        return
    message["server_id"] = serverid
    message["istf1"] = context["servers"].get(serverid, {}).get("istf1server", False)
    realonkilldata(message)

def realonkilldata(data):
    istf1 = context["servers"].get(data["server_id"], {}).get("istf1server", False)
    if SENDKILLFEED == "1" and (data.get("victim_type", False) == "player"):
        print(
            f"{data.get('attacker_name', data['attacker_type'])} killed {data.get('victim_name', data['victim_type'])} with {data['cause_of_death']} using mods {' '.join(data.get('modsused', []))}"
        )
        messageflush.append(
            {
                "timestamp": int(time.time()),
                "serverid": data["server_id"],
                "type": 3,
                "globalmessage": False,
                "overridechannel": None,
                "messagecontent": f"{data.get('attacker_name', data['attacker_type'])} killed {data.get('victim_name', data['victim_type'])} with {WEAPON_NAMES.get(data['cause_of_death'], data['cause_of_death'])}",
                "metadata": {"type": "killfeed"},
                "servername": context["servers"][data["server_id"]]["name"],
            }
        )

    if (
        KILLSTREAKNOTIFYTHRESHOLD
        and data.get("attacker_type", False)
        not in ["npc_soldier", "npc_stalker", "npc_spectre", "npc_super_spectre"]
        and (
            (data.get("victim_type", False) == "player")
            # or (data.get("victim_type", False) == "npc_titan")   CHanged while faketone is a bit funky with auto titans yaya ejects no longer coutn sob sob
        )
        and data.get("match_id", False)
        and getpriority(data, "attacker_name", "attacker_type")
    ):
        # print("CORE KILLSTREAKS COUNTED")
        if len(consecutivekills.keys()) > 50:
            del consecutivekills[list(consecutivekills.keys())[0]]
        if len(maxkills.keys()) > 50:
            del maxkills[list(maxkills.keys())[0]]
        consecutivekills.setdefault(data["match_id"], {})
        consecutivekills[data["match_id"]].setdefault(
            getpriority(data, "attacker_name", "attacker_type"), {}
        )
        consecutivekills[data["match_id"]][
            getpriority(data, "attacker_name", "attacker_type")
        ].setdefault(data.get("attacker_id", 1), 0)
        # print(data.get("attacker_titan",False),data.get("victim_titan",False))
        # print(bool(data.get("victim_titan",False)if data.get("victim_titan",False) != "null" else False))
        if (
            bool(
                data.get("attacker_titan", False)
                if data.get("attacker_titan", False) != "null"
                else False
            )
            == bool(
                data.get("victim_titan", False)
                if data.get("victim_titan", False) != "null"
                else False
            )
            or bool(
                data.get("victim_titan", False)
                if data.get("victim_titan", False) != "null"
                else False
            )
            or (data.get("victim_type", False) == "npc_titan")

            # or True
        ):
            # print("this crill counted")
            consecutivekills[data["match_id"]][
                getpriority(data, "attacker_name", "attacker_type")
            ][data.get("attacker_id", 1)] += 1
            # maxkills = setlotsofdefault(maxkills,max(consecutivekills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)],int(getpriority(maxkills,[data["match_id"],getpriority(data,"attacker_name","attacker_type"),data.get("attacker_id",1)]))),data["match_id"],getpriority(data,"attacker_name","attacker_type"),data.get("attacker_id",1))
            maxkills.setdefault(data["match_id"], {}).setdefault(
                getpriority(data, "attacker_name", "attacker_type"), {}
            )[data.get("attacker_id", 1)] = max(
                consecutivekills[data["match_id"]][
                    getpriority(data, "attacker_name", "attacker_type")
                ][data.get("attacker_id", 1)],
                maxkills.get(data["match_id"], {})
                .get(getpriority(data, "attacker_name", "attacker_type"), {})
                .get(data.get("attacker_id", 1), 0),
            )
            if (
                consecutivekills[data["match_id"]][
                    getpriority(data, "attacker_name", "attacker_type")
                ][data.get("attacker_id", 1)]
                >= KILLSTREAKNOTIFYTHRESHOLD
                and not (
                    consecutivekills[data["match_id"]][
                        getpriority(data, "attacker_name", "attacker_type")
                    ][data.get("attacker_id", 1)]
                    - KILLSTREAKNOTIFYTHRESHOLD
                )
                % KILLSTREAKNOTIFYSTEP
            ):
                # print("adding")
                messageflush.append(
                    {
                        "timestamp": int(time.time()),
                        "serverid": data["server_id"],
                        "type": 3,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": (
                            KILL_STREAK_MESSAGES["killstreakbegin"][
                                (
                                    consecutivekills[data["match_id"]][
                                        getpriority(
                                            data, "attacker_name", "attacker_type"
                                        )
                                    ][data.get("attacker_id", 1)]
                                    - KILLSTREAKNOTIFYTHRESHOLD
                                )
                                // KILLSTREAKNOTIFYSTEP
                            ]
                            if len(KILL_STREAK_MESSAGES["killstreakbegin"])
                            > (
                                consecutivekills[data["match_id"]][
                                    getpriority(
                                        data, "attacker_name", "attacker_type"
                                    )
                                ][data.get("attacker_id", 1)]
                                - KILLSTREAKNOTIFYTHRESHOLD
                            )
                            // KILLSTREAKNOTIFYSTEP
                            else KILL_STREAK_MESSAGES["killstreakbegin"][-1]
                        )
                        .replace(
                            "/attacker/",
                            getpriority(data, "attacker_name", "attacker_type"),
                        )
                        .replace(
                            "/victim/",
                            data.get(
                                "victim_name", "UNKNOWN VICTIM SOMETHING IS BROKEY"
                            ),
                        )
                        .replace(
                            "/ks/",
                            str(
                                consecutivekills[data["match_id"]][
                                    getpriority(
                                        data, "attacker_name", "attacker_type"
                                    )
                                ][data.get("attacker_id", 1)]
                            ),
                        )
                        .replace(
                            "/gun/",
                            WEAPON_NAMES.get(
                                getpriority(data, "cause_of_death"),
                                getpriority(data, "cause_of_death"),
                            ),
                        ),
                        "metadata": {"type": "killfeed"},
                        "servername": context["servers"][data["server_id"]]["name"],
                    }
                )

        # print("THIS HERE", getpriority(consecutivekills,[data["match_id"],data.get("victim_id",1),data.get("victim_name",False)]))
        if (
            getpriority(
                consecutivekills,
                [
                    data["match_id"],
                    data.get("victim_name", 1),
                    data.get("victim_id", False),
                ],
            )
            and getpriority(
                consecutivekills,
                [
                    data["match_id"],
                    data.get("victim_name", 1),
                    data.get("victim_id", False),
                ],
            )
            >= KILLSTREAKNOTIFYTHRESHOLD
            and data.get("victim_type", False) == "player"
        ):
            pass
            if data.get("attacker_id", False) == data.get("victim_id", False):
                messageflush.append(
                    {
                        "timestamp": int(time.time()),
                        "serverid": data["server_id"],
                        "type": 3,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": random.choice(
                            [
                                *KILL_STREAK_MESSAGES["killstreakended"],
                                *KILL_STREAK_MESSAGES["killstreakselfended"],
                            ]
                        )
                        .replace(
                            "/attacker/",
                            getpriority(data, "attacker_name", "attacker_type"),
                        )
                        .replace(
                            "/victim/",
                            data.get(
                                "victim_name", "UNKNOWN VICTIM SOMETHING IS BROKEY"
                            ),
                        )
                        .replace(
                            "/ks/",
                            str(
                                getpriority(
                                    consecutivekills,
                                    [
                                        data["match_id"],
                                        data.get("victim_name", 1),
                                        data.get("victim_id", False),
                                    ],
                                )
                                - 1
                            ),
                        )
                        .replace(
                            "/gun/",
                            WEAPON_NAMES.get(
                                getpriority(data, "cause_of_death"),
                                getpriority(data, "cause_of_death"),
                            ),
                        ),
                        "metadata": {"type": "killfeed"},
                        "servername": context["servers"][data["server_id"]]["name"],
                    }
                )
            else:
                messageflush.append(
                    {
                        "timestamp": int(time.time()),
                        "serverid": data["server_id"],
                        "type": 3,
                        "globalmessage": False,
                        "overridechannel": None,
                        "messagecontent": random.choice(
                            [*KILL_STREAK_MESSAGES["killstreakended"]]
                        )
                        .replace(
                            "/attacker/",
                            getpriority(data, "attacker_name", "attacker_type"),
                        )
                        .replace(
                            "/victim/",
                            data.get(
                                "victim_name", "UNKNOWN VICTIM SOMETHING IS BROKEY"
                            ),
                        )
                        .replace(
                            "/ks/",
                            str(
                                getpriority(
                                    consecutivekills,
                                    [
                                        data["match_id"],
                                        data.get("victim_name", 1),
                                        data.get("victim_id", False),
                                    ],
                                )
                            ),
                        )
                        .replace(
                            "/gun/",
                            WEAPON_NAMES.get(
                                getpriority(data, "cause_of_death"),
                                getpriority(data, "cause_of_death"),
                            ),
                        ),
                        "metadata": {"type": "killfeed"},
                        "servername": context["servers"][data["server_id"]]["name"],
                    }
                )
            # their killstreak ended!
            consecutivekills[data["match_id"]][data.get("victim_name", 1)][
                data.get("victim_id", False)
            ] = 0
        elif data.get("victim_type", False) == "player" and getpriority(
            consecutivekills,
            [
                data["match_id"],
                data.get("victim_name", 1),
                data.get("victim_id", False),
            ],
        ):
            consecutivekills[data["match_id"]][data.get("victim_name", 1)][
                data.get("victim_id", False)
            ] = 0
        # print("dataaaaa",consecutivekills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)],(consecutivekills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)] - KILLSTREAKNOTIFYTHRESHOLD)%KILLSTREAKNOTIFYSTEP,consecutivekills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)] > KILLSTREAKNOTIFYTHRESHOLD , not (consecutivekills[data["match_id"]][getpriority(data,"attacker_name","attacker_type")][data.get("attacker_id",1)] - KILLSTREAKNOTIFYTHRESHOLD)%KILLSTREAKNOTIFYSTEP )
        # kill streak notify!
        # print("I got here")
    if len(lexitoneapicache.keys()) > 30:  # probably a safe amount
        del lexitoneapicache[list(lexitoneapicache.keys())[0]]
    if data.get("match_id", False):
        lexitoneapicache.setdefault(data.get("match_id", None), []).append(
            {
                "victimtype": data.get("victim_type", None),
                "attackertype": data.get("attacker_type", None),
                "weapon": data.get("cause_of_death", None),
                "victimtitan": data.get("victim_titan", None),
                "attackertitan": data.get("attacker_titan", None),
                "victimname": data.get("victim_name", None)
                if data.get("victim_name", None)
                else data.get("victim_type", None),
                "attackername": data.get("attacker_name", None)
                if data.get("attacker_name", None)
                else data.get("attacker_type", None),
                # "victimweapon":data.get("victim_current_weapon", None),
            }
        )
    try:
        callback("nutone",data)
    except:
        traceback.print_exc()
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        f"""
        INSERT INTO specifickilltracker{"tf1" if istf1 else ""} (
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
            victim_y,
            weapon_mods,
            victim_type,
            attacker_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("server_id", None),
            data.get("attacker_z", None),
            data.get("attacker_x", None),
            data.get("attacker_y", None),
            data.get("victim_id", None),
            data.get("victim_name", None)
            if data.get("victim_name", None)
            else data.get("victim_type", None),
            data.get("victim_offhand_weapon_2", None),
            data.get("attacker_titan", None),
            data.get("map", None),
            data.get("attacker_offhand_weapon_1", None),
            data.get("attacker_offhand_weapon_2", None),
            data.get("victim_offhand_weapon_1", None),
            data.get("attacker_weapon_3", None),
            data.get("attacker_name", None)
            if data.get("attacker_name", None)
            else data.get("attacker_type", None),
            data.get("match_id", None),
            data.get("victim_titan", None),
            data.get("distance", None),
            data.get("victim_current_weapon", None),
            data.get("victim_z", None),
            data.get("attacker_weapon_2", None),
            data.get("game_time", None),
            data.get("attacker_current_weapon", None),
            data.get("victim_weapon_3", None),
            data.get("attacker_id", None),
            data.get("game_mode", None),
            data.get("victim_x", None),
            data.get("attacker_weapon_1", None),
            data.get("victim_weapon_1", None),
            data.get("victim_weapon_2", None),
            data.get("timeofkill", None),
            data.get("cause_of_death", None),
            data.get("victim_y", None),
            " ".join(data.get("modsused", [])),
            data.get("victim_type", None),
            data.get("attacker_type", None),
        ),
    )
    tfdb.commit()
    c.close()
    tfdb.close()
    return {"message": "ok"}
def calcstats(message, serverid, isfromserver):
    """Processes in-game stats requests and formats statistical data for display"""
    # print("e",message)
    istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
    # print(isfromserver,readplayeruidpreferences(getpriority(message,"uid",["meta","uid"]),istf1) )
    # print("BLEHHHH",getpriority(message,"uid",["meta","uid"],"name"))
    if (
        isfromserver
        and getpriority(
            readplayeruidpreferences(
                getpriority(message, "uid", ["meta", "uid"], "name"), istf1
            ),
            ["tf1" if istf1 else "tf2", "togglestats"],
        )
        == True
    ):
        # print("HERE")
        return
        # discordtotitanfall[serverid]["messages"].append(
        #     {
        #         "id": random.randint(0,53353),
        #         "content":"disabled stats",
        #         "teamoverride": 4,
        #         "isteammessage": False,
        #         "uidoverride": []
        #         # "dotreacted": dotreacted
        #     }
        #     )
        #  readplayeruidpreferences(getpriority(message,"uid",["meta","uid"]),istf1)

    # print("OPOWOWOOWOWOOWOWOOWOWOWO")
    if istf1 and False:
        tf1pullstats(message, serverid)
    else:
        if len(message.get("originalmessage", "w").split(" ")) > 1:
            output = getstats(" ".join(message["originalmessage"].split(" ")[1:]),isfromserver,istf1)
        else:
            # print(getpriority(message,"originalname","name"))
            output = getstats(str(getpriority(message, "originalname", "name")),isfromserver,istf1)
        # if not isfromserver:
        #     name = resolveplayeruidfromdb(
        #         getpriority(message, "originalname", "name"), None, True, istf1
        #     )
        #     if name:
        #         name = name[0]["uid"]
        #     else:
        #         return
        
        if "sob" in output.keys():
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(int(time.time()*100)),
                    "content": f"{PREFIXES['discord']} player not found :(",
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"],"name")],
                    # "dotreacted": dotreacted
                }
            )
            return
        # print(json.dumps(output,indent=4))
        for i, (key, stat) in enumerate(output.items()):
            # print(stat)
            if not key.isdigit():
                continue
            # print("KEpt")
            discordtotitanfall[serverid]["messages"].append(
                {
                    # "id": str(i)+str(int(time.time()*100)),
                    "content": stat,
                    # "teamoverride": 4,
                    # "isteammessage": False,
                    "uidoverride": [getpriority(message, "uid", ["meta", "uid"],"name")]
                    if not len(message.get("originalmessage", "w").split(" ")) > 1
                    else [],
                    # "dotreacted": dotreacted
                }
            )


def savemessages(message, serverid):
    """Saves chat messages to database for logging and persistence"""
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb

    c.execute(
        """INSERT INTO messagelogger (message,type,serverid)
            VALUES (?,?,?)
        """,
        (json.dumps(message), message.get("type", "Unknown type"), serverid),
    )

    tfdb.commit()
    tfdb.close()

async def checkverify(message, serverid):
    global accountlinker
    if not accountlinker:
        return

    uid = message.get("uid", None)
    name = message.get("originalname", None)
    content = message.get("originalmessage", None)
    if not all([uid, name, content]):
        return
    # verify_data = accountlinker.get(uid, None)
    # if not verify_data:
    #     return
    verify_data = accountlinker.get(str(content).strip(), False)
    if not verify_data or int(time.time()) > verify_data["timerequested"]:
        return
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    pullid.cache_clear()
    c.execute(
        """INSERT INTO discordlinkdata (uid, discordid, linktime)
            VALUES (?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET discordid=excluded.discordid, linktime=excluded.linktime
        """,
        (uid, verify_data["account"], int(time.time())),
    )

    tfdb.commit()
    tfdb.close()
    await verify_data["ctx"].followup.send(
        f"linked <@{verify_data['account']}> to **{name}** (UID `{uid}`)",
        ephemeral=True,
    )
    initdiscordtotitanfall(serverid)
    discordtotitanfall[serverid]["messages"].append(
        {
            "content": f"{PREFIXES['discord']}Linked {PREFIXES['commandname']}{name}{PREFIXES['chatcolour']} to discord account {PREFIXES['commandname']}{verify_data['name']}",
            "uidoverride": [uid],
        }
    )
    del accountlinker[str(content).strip()]


def checkifbad(message):
    """Checks messages against profanity filter and banned word lists"""
    global context
    if message["type"] not in FILTERNAMESINMESSAGES.split(","):
        return [0, 0]
    lowered = message["originalmessage"].lower()
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
                    traceback.print_exc()
                    continue
            else:
                if word.lower() in text:
                    return word
        return False

    if checknono(banwords, lowered):
        # print("here")
        return [2, checknono(banwords, lowered)]
    elif checknono(notifywords, lowered):
        # print("here2",checknono(notifywords, lowered))
        return [1, checknono(notifywords, lowered)]
    if message.get(
        "name"
    ):  # disable name check #it's enabled now, but only for ban words
        # print("MESSAGENAME",message["name"])
        name_lowered = message["name"].lower()
        if checknono(banwords, name_lowered):
            # print("here3")
            return [2, checknono(banwords, name_lowered)]
        elif checknono(notifywords, name_lowered) and False:  # see!
            # print("here4")
            return [1, checknono(notifywords, name_lowered)]

    return [0, 0]


async def outputmsg(channel, output, serverid, USEDYNAMICPFPS):
    global context

    content = [
        (
            discord.utils.escape_mentions(x["message"])
            if not x["meta"].get("allowmentions", False)
            else x["message"]
        )
        for x in output[serverid]
        if (x["type"] not in ["usermessagepfp", "impersonate"] or USEDYNAMICPFPS != "1")
    ]

    if not content:
        return
    if MORECOLOURS == "1":
        print(
            f"{PREFIXES['stat']}{getpriority(context, ['servers', serverid, 'name'])}: {PREFIXES['neutral']}{f'\n{getpriority(context, ["servers", serverid, "name"])}: '.join(content)}"
        )
    else:
        print(
            f"{getpriority(context, ['servers', serverid, 'name'])}: {f'\n{getpriority(context, ["servers", serverid, "name"])}: '.join(content)}"
        )

    message = await channel.send(("\n".join(content)))
    # print(f"Sent message ID: {message.id}")
    # print("OUTPUT",output[serverid])
    # print("qeqw",output)
    await checkfilters(output[serverid], message)


async def checkfilters(messages, message):
    try:
        global context
        # print(messages)
        message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        notify_channel_id = context["overridechannels"].get("wordfilternotifychannel")
        notify_channel = (
            bot.get_channel(notify_channel_id) if notify_channel_id else None
        )

        if not notify_channel:
            return


        bad_msg = next((x for x in messages if x.get("isbad", [0, 0])[0] == 2), None)
        if bad_msg:
            sanctionalreadyfoundmessage = ""
            print("BAN MESSAGE FOUND", json.dumps(bad_msg, indent=4))
            if (
                bad_msg["originalname"]
                and bad_msg.get("uid", False)
                and bad_msg["messagecontent"]
            ):
                sanction, messageid =  pullsanction(bad_msg["uid"])
                
                if sanction:
                    sanctionalreadyfoundmessage = f"\n    __ALREADY SANCTIONED__ Link: {sanction["link"]}"


                select = discord.ui.Select(
                    placeholder="Buttons!",
                    custom_id=f"moderation_dropdown_{bad_msg['uid']}_{bad_msg["oserverid"]}_{message.id}",
                    options=[
                        discord.SelectOption(label="1 hour mute", value="mute_h_1", emoji="🔇"),
                        discord.SelectOption(label="1 day mute", value="mute_1", emoji="🔇"),         
                        discord.SelectOption(label="7 day mute", value="mute_7", emoji="🔇"),         
                        discord.SelectOption(label="30 day mute", value="mute_30", emoji="🔇"),
                        discord.SelectOption(label="60 day mute", value="mute_60", emoji="🔇"),
                        discord.SelectOption(label="1 hour ban", value="ban_h_1", emoji="🔨"),
                        discord.SelectOption(label="1 day ban", value="ban_1", emoji="🔨"),
                        discord.SelectOption(label="7 day ban", value="ban_7", emoji="🔨"),      
                        discord.SelectOption(label="30 day ban", value="ban_30", emoji="🔨"),
                        discord.SelectOption(label="60 day ban", value="ban_60", emoji="🔨"),
                        *((discord.SelectOption(label = "remove sanction (to add new one)",value = "unsanction",emoji = "⛓️‍💥")) if sanction else ())
                    ]
                )

                view = discord.ui.View(timeout=None)
                view.add_item(select)
                
                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Ban word found**
    Sent by: **{bad_msg["originalname"]}{sanctionalreadyfoundmessage}**
    UID: **{bad_msg["uid"]}**
    Message: "{getpriority(bad_msg, "originalmessage", "messagecontent", "message")}"
    Found pattern: "{bad_msg["isbad"][1]}"
    Message Link: {message_link}"""),
                    view= not context["servers"].get(bad_msg["oserverid"], {}).get("istf1server", False) and view or None
                )
            else:
                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Ban word found**
    Message: "{getpriority(bad_msg, "originalmessage", "messagecontent", "message")}"
    Found pattern: "{bad_msg["isbad"][1]}"
    Message Link: {message_link}""")
                )

        notify_msg = next((x for x in messages if x.get("isbad", [0.0])[0] == 1), None)
        # print("HERE")
        if notify_msg:
            sanctionalreadyfoundmessage = ""
            print("NOTIFY MESSAGE FOUND", json.dumps(notify_msg, indent=4))

            # print("HERE2")
            if (
                notify_msg["originalname"]
                and notify_msg.get("uid", False)
                and notify_msg["messagecontent"]
            ):
                sanction, messageid =  pullsanction(notify_msg["uid"])
                if sanction:
                    sanctionalreadyfoundmessage = f"\n    __ALREADY SANCTIONED__ Link: {sanction["link"]}"
                # print("HERE3")

                select = discord.ui.Select(
                    placeholder="Buttons!",
                    custom_id=f"moderation_dropdown_{notify_msg['uid']}_{notify_msg["oserverid"]}_{message.id}",
                    options=[
                        discord.SelectOption(label="1 hour mute", value="mute_h_1", emoji="🔇"),
                        discord.SelectOption(label="1 day mute", value="mute_1", emoji="🔇"),         
                        discord.SelectOption(label="7 day mute", value="mute_7", emoji="🔇"),         
                        discord.SelectOption(label="30 day mute", value="mute_30", emoji="🔇"),
                        discord.SelectOption(label="60 day mute", value="mute_60", emoji="🔇"),
                        discord.SelectOption(label="1 hour ban", value="ban_h_1", emoji="🔨"),
                        discord.SelectOption(label="1 day ban", value="ban_1", emoji="🔨"),
                        discord.SelectOption(label="7 day ban", value="ban_7", emoji="🔨"),      
                        discord.SelectOption(label="30 day ban", value="ban_30", emoji="🔨"),
                        discord.SelectOption(label="60 day ban", value="ban_60", emoji="🔨"),
                        *((discord.SelectOption(label = "remove sanction (to add new one)",value = "unsanction",emoji = "⛓️‍💥")) if sanction else ())
                    ]
                )

                view = discord.ui.View(timeout=None)
                view.add_item(select)
                
                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Filtered word found**
    Sent by: **{notify_msg["originalname"]}{sanctionalreadyfoundmessage}**
    UID: **{notify_msg["uid"]}**
    Message: "{getpriority(notify_msg, "originalmessage", "messagecontent", "message")}"
    Found pattern: "{notify_msg["isbad"][1]}"
    Message Link: {message_link}"""),
                    view= not context["servers"].get(notify_msg["oserverid"], {}).get("istf1server", False) and view or None
                )
            else:
                # print("HERE4")

                # print("NOTIFY",notify_msg)
                await notify_channel.send(
                    discord.utils.escape_mentions(f""">>> **Filtered word found**
    Message: "{getpriority(notify_msg, "originalmessage", "messagecontent", "message")}"
    Found pattern: "{notify_msg["isbad"][1]}"
    Message Link: {message_link}""")
                )
            # print("HERE5")
    except Exception as e:
        print("ERROR", e)
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




# PFPROUTE
async def sendpfpmessages(channel, userpfpmessages, serverid):
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
        actualwebhooks = {"ChatBridge": webhook, "ChatBridge2": webhook2}
        for username, value in userpfpmessages.items():
            # print("Sending as:", username)
            # print("Message:", "\n".join(value["messages"]))
            pilotstates.setdefault(
                serverid, {"uid": -1, "model": None, "webhook": "ChatBridge"}
            )
            if (
                pilotstates[serverid]["uid"] == value["uid"]
                and str(value["pfp"]) != pilotstates[serverid]["model"]
            ):
                if pilotstates[serverid]["webhook"] == "ChatBridge":
                    pilotstates[serverid]["webhook"] = "ChatBridge2"
                else:
                    pilotstates[serverid]["webhook"] = "ChatBridge"
            pilotstates[serverid] = {
                "uid": value["uid"],
                "model": str(value["pfp"]),
                "webhook": pilotstates[serverid]["webhook"],
            }
            # print("here")
            pfperror = False
            pfp = MODEL_DICT.get(
                str(value["pfp"]),
                random.choices(
                    list(UNKNOWNPFPS.keys()),
                    weights=list(map(lambda x: x["weight"], UNKNOWNPFPS.values())),
                )[0],
            )
            if pfp in UNKNOWNPFPS and (
                str(value["pfp"].startswith("true"))
                or str(value["pfp"].startswith("false"))
            ):
                print("FALLING BACK TO GUESSING", value["pfp"])
                # username = f"{username} pfperror {value['pfp']}"
                for model, valuew in MODEL_DICT.items():
                    if str(value["pfp"])[6:] in model:
                        pfp = valuew
                        print("setting pfp too", pfp)

                        break
                else:
                    pfperror = f"-# {value['pfp']}".replace('"', "").replace("$", "")
            # print(json.dumps(value["messages"],indent=4))
            # print("SENDING PFP MESSAGE","\n".join(list(map(lambda x: x["message"],value["messages"]))),f'{PFPROUTE}{pfp}')

            async with aiohttp.ClientSession() as session:
                # print(pilotstates[serverid])
                if MORECOLOURS == "1":
                    print(
                        f"{PREFIXES['stat']}{getpriority(context, ['servers', serverid, 'name'])}: {PREFIXES['neutral']}{username[0:80]}: {f'\n{getpriority(context, ["servers", serverid, "name"])}: {username[0:80]}: '.join(list(map(lambda x: discord.utils.escape_mentions(x['message']) if not x['meta'].get('allowmentions', False) else x['message'], value['messages'])))}"
                    )
                else:
                    print(
                        f"{getpriority(context, ['servers', serverid, 'name'])}: {username[0:80]}: {f'\n{getpriority(context, ["servers", serverid, "name"])}: {username[0:80]}: '.join(list(map(lambda x: discord.utils.escape_mentions(x['message']) if not x['meta'].get('allowmentions', False) else x['message'], value['messages'])))}"
                    )

                # print(f"Tf -> Discord\n{username[0:80]}: {f"\n{username[0:80]}: ".join(list(map(lambda x: discord.utils.escape_mentions(x["message"]) if not x["meta"].get("allowmentions",False) else x["message"] ,value["messages"])))}")
                message = await actualwebhooks[
                    pilotstates[serverid]["webhook"]
                ].send(
                    (
                        "\n".join(
                            list(
                                map(
                                    lambda x: discord.utils.escape_mentions(
                                        x["message"]
                                    )
                                    if not x["meta"].get("allowmentions", False)
                                    else x["message"],
                                    value["messages"],
                                )
                            )
                        )
                        + f"{'\n' + pfperror if pfperror else ''}"
                    ),  # +" "+pilotstates[serverid]["webhook"],
                    username=f"{username[0:80]}",
                    avatar_url=f"{PFPROUTE}{pfp}",
                    wait=True,
                )
            await checkfilters(
                list(
                    map(
                        lambda x: {
                            **x,
                            "isbad": x["isbad"],
                            "messagecontent": x["messagecontent"],
                            "message": f"{username}: {x['message']}",
                            "originalname": value["originalname"],
                            "uid": value["uid"],
                        },
                        value["messages"],
                    )
                ),
                message,
            )
    except Exception as e:
        print("WEBHOOK CRASH", e)
        traceback.print_exc()


def initdiscordtotitanfall(
    serverid,
):  # before I knew about setdefault and .keys() being useless
    """Initializes server communication data structures"""
    global discordtotitanfall
    # print(serverid,"here")
    if serverid not in discordtotitanfall.keys():
        discordtotitanfall[serverid] = {"messages": [], "commands": []}
    if "messages" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["messages"] = []
    if "commands" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["commands"] = []
    if "returnids" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["returnids"] = {
            "messages": {},
            "commands": {},
            "commandsreturn": {},
        }
    if "lastheardfrom" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["lastheardfrom"] = 0
    if "onlinestatus" not in discordtotitanfall[serverid].keys():
        discordtotitanfall[serverid]["onlinestatus"] = False
    discordtotitanfall[serverid].setdefault("currentplayers", {})


def getchannelidfromname(name, ctx):
    """Resolves Discord channel ID from channel name using context"""
    for key, server in sorted(
        context["servers"].items(), key=lambda x: len(x[1].get("name", ""))
    ):
        value = server.get("name", "Unknown")
        if name and name.lower() in value.lower():
            print("default server overridden, sending to", value.lower())
            return key
    if any(
        server.get("channelid") == ctx.channel.id
        for server in context["servers"].values()
    ):
        for key, server in context["servers"].items():
            if server.get("channelid") == ctx.channel.id:
                return key
    # print("could not find overridden server")


def sendrconcommand(serverid, command, **kwargs):
    """Runs command on server"""
    global discordtotitanfall
    initdiscordtotitanfall(serverid)
    commandid = random.randint(0, 100000000000000)
    discordtotitanfall[serverid]["commands"].append(
        {"command": command, "id": commandid}
    )
    if kwargs.get("sender", False) is not False:
        threading.Thread(
            target=threadwrap,
            daemon=True,
            args=(
                notifydebugchat,
                serverid,
                f"{f'{kwargs.get("sender")} ran' if kwargs.get('sender') else ''} {command} on {PREFIXES['stat']}{context['servers'].get(serverid, {'name': 'UNKNOWN SERVER'})['name']}",
                kwargs.get("prefix", str(inspect.currentframe().f_back.f_code.co_name)),
            ),
        ).start()
    return serverid, commandid, command


def getjson(data):  # ty chatgpt
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            if  isinstance(parsed, int) :
                return data
                # print([parsed,data])
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
        title=f"Command sent to server: *{context['servers'][serverid]['name']}*",
        description=f"Status code: {statuscode}",
        color=0xFF70CB,
    )
    if type(data) == str:
        embed.add_field(name="> Output:", value=f"```{data}```", inline=False)
    else:
        for key, value in data.items():
            embed.add_field(
                name=f"> {key}:",
                value=f"```json\n{json.dumps(value, indent=4)}```",
                inline=False,
            )
    return embed


@functools.lru_cache(maxsize=None)
def simplyfy(text):
    if not text:
        return text
    charmap = functools.reduce(
        lambda a, b: {**a, **dict(zip(b[1], [b[0]] * len(b[1])))},
        LOOKALIKES.items(),
        {},
    )
    return "".join(list(map(lambda x: charmap.get(x, x).lower(), text)))


@functools.lru_cache(maxsize=None)
def resolveplayeruidfromdb(
    name, uidnameforce=None, oneuidpermatch=False, istf1=False, **kwargs
):
    """Searches for players by name or UID with fuzzy matching, sorting by relevance and recency"""
    relaxed = kwargs.get("relaxed", False)
    name = str(name)

    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    data = []
    if uidnameforce != "uid":
        name_like = f"%{name}%"
        query = f"""
            SELECT playeruid, playername, lastseenunix, lastserverid FROM uidnamelink{"tf1" if istf1 else ""}
            WHERE LOWER(playername) LIKE LOWER(?) AND playeruid != 0
            ORDER BY id DESC, playername COLLATE NOCASE
        """
        c.execute(query, (name_like,))
        data = list(c.fetchall())

    if (uidnameforce != "name" or not data) and name.isdigit():
        c.execute(
            f"""
            SELECT playeruid, playername, lastseenunix, lastserverid FROM uidnamelink{"tf1" if istf1 else ""}
            WHERE playeruid = ? AND playeruid != 0
            ORDER BY id DESC
        """,
            (name,),
        )
        
        data.extend(list(c.fetchall()))


        # if istf1 is None:
        #     c.execute(f"""
        #         SELECT playeruid, playername, lastseenunix, lastserverid FROM uidnamelink{'tf1' if True else ''}
        #         WHERE playeruid = ?
        #         ORDER BY id DESC
        #     """, (name,))
        #     datacompare = c.fetchall()
        #     if len(data) and len(datacompare) and int(bool(max(data,key = lambda x: 0 if not x[2] else x[2])[2])) < int(bool(max(datacompare,key = lambda x: 0 if not x[2] else x[2])[2])): data = datacompare
        #     else:data = datacompare
        name = str(name)

    if not data and not relaxed:
        tfdb.close()
        return []
    elif not data:
        c.execute(
            f"""SELECT playeruid, playername, lastseenunix, lastserverid FROM uidnamelink{"tf1" if istf1 else ""}"""
        )
        data = c.fetchall()
        for uid, pname, lastseen, lastserverid in data:
            if (
                not oneuidpermatch
                or uid not in seen_uids
                and simplyfy(name) in simplyfy(pname)
            ):
                results.append(
                    {
                        "name": pname,
                        "uid": (uid),
                        "lastseen": lastseen if lastseen else 0,
                        "lastserverid": str(lastserverid)
                        if lastserverid
                        else lastserverid,
                    }
                )
                seen_uids.add(uid)

        results.sort(
            key=lambda x: len(x["name"])
            if int(time.time()) - x["lastseen"] < 86400 * 3
            else int(time.time()) - x["lastseen"]
        )
        results.sort(
            key=lambda x: simplyfy(x["name"]).startswith(simplyfy(name)), reverse=True
        )
        results.sort(key=lambda x: simplyfy(x["name"]) == simplyfy(name), reverse=True)
    else:
        seen_uids = set()
        results = []
        # print(data)
        for uid, pname, lastseen, lastserverid in data:
            if not oneuidpermatch or uid not in seen_uids:
                results.append(
                    {
                        "name": pname,
                        "uid": (uid),
                        "lastseen": lastseen if lastseen else 0,
                        "lastserverid": str(lastserverid)
                        if lastserverid
                        else lastserverid,
                    }
                )
                seen_uids.add(uid)

        # results.sort(key=lambda x: len(x["name"]) - x["name"].lower().startswith(name.lower()) * 50)
        # print(json.dumps(results,indent=4))
        results.sort(
            key=lambda x: len(x["name"])
            if int(time.time()) - x["lastseen"] < 86400 * 3
            else int(time.time()) - x["lastseen"]
        )
        # results.sort(key = lambda x: int(x["lastseen"]),reverse=True)
        results.sort(
            key=lambda x: x["name"].lower().startswith(name.lower()), reverse=True
        )
        results.sort(key=lambda x: x["name"].lower() == name.lower(), reverse=True)
    tfdb.close()

    return results


def notifydebugchat(affectedserver, message, prefix="Commandnotify"):
    # print(json.dumps(discordtotitanfall,indent=4))
    # print("WOA",list(map(lambda x: max(resolveplayeruidfromdb(str(pullid(x,"tf")),"uid",True),resolveplayeruidfromdb(str(x),"uid",True,True),key = lambda x: x[0]["lastseen"] if x else 0) if pullid(x,"tf") else False ,context["overriderolesuids"].get("debugchat",[]))))
    # print("WOA",list(map(lambda x: (resolveplayeruidfromdb(str(pullid(x,"tf")),"uid",True),resolveplayeruidfromdb(str(x),"uid",True,True)) if pullid(x,"tf") else False ,context["overriderolesuids"].get("debugchat",[]))))
    # print("PRETTY",(functools.reduce(lambda a,b:{**a,b[0]["lastserverid"]:[*a.get(b[0]["lastserverid"],[]),b[0]["uid"]]},filter(lambda x: x and x[0]["uid"] in discordtotitanfall[x[0]["lastserverid"]]["currentplayers"] ,map(lambda x: max(resolveplayeruidfromdb(str(pullid(x,"tf")),"uid",True),resolveplayeruidfromdb(str(x),"uid",True,True),key = lambda x: x[0]["lastseen"] if x else 0) if pullid(x,"tf") else False ,context["overriderolesuids"].get("debugchat",[]))),{})))
    for serverid, uidlist in functools.reduce(
        lambda a, b: {
            **a,
            b[0]["lastserverid"]: [*a.get(b[0]["lastserverid"], []), b[0]["uid"]],
        },
        filter(
            lambda x: x
            and (
                NOTIFYCOMMANDSONALLSERVERSDEBUG
                or x[0]["lastserverid"] == affectedserver
            )
            and x[0]["lastserverid"] in discordtotitanfall
            and x[0]["uid"]
            in discordtotitanfall[x[0]["lastserverid"]]["currentplayers"]
            and not getpriority(readplayeruidpreferences(x[0]["uid"],False),["tf2","debugchat"])
            and not getpriority(readplayeruidpreferences(x[0]["uid"],True),["tf1","debugchat"])
            ,
            map(
                lambda x: list(
                    map(
                        lambda y: {**y, "uid": str(y["uid"])},
                        max(
                            resolveplayeruidfromdb(str(pullid(x, "tf")), "uid", True),
                            resolveplayeruidfromdb(str(x), "uid", True, True),
                            key=lambda x: x[0]["lastseen"] if x else 0,
                        ),
                    )
                )
                if pullid(x, "tf")
                else False,
                context["overriderolesuids"].get("debugchat", []),
            ),
        ),
        {},
    ).items():
        istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
        if istf1:
            for uid in uidlist:
                discordtotitanfall[serverid]["messages"].append(
                    {
                        "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}{prefix}{PREFIXES['offchatcolour']} {message}",
                        "uidoverride": [uid],
                    }
                )
        else:
            # print("here",[serverid],[uidlist])
            discordtotitanfall[serverid]["messages"].append(
                {
                    "content": f"{PREFIXES['discord']}{PREFIXES['commandname']}{prefix}:{PREFIXES['offchatcolour']} {message}",
                    "uidoverride": uidlist,
                }
            )


async def returncommandfeedback(
    serverid,
    id,
    command,
    ctx,
    overridemsg=defaultoverride,
    iscommandnotmessage=True,
    logthiscommand=True,
    extraargsintofunction=None,
):
    """Once command has been sent, this function is responsible for catching the output of the command
    the only reason it knows what command has been ran is for logging
    huh wait have I wasted a ton of time needlessly using this function? I think I have... ohno... that's annoying!
    ya like seriously so many commands don't have outputs..
    I'll fix this in time
    fixed"""
    if not overridemsg:
        overridemsg = defaultoverride
    i = 0
    while i < 200:
        await asyncio.sleep(0.05)
        if (
            str(id)
            in discordtotitanfall[serverid]["returnids"]["commandsreturn"].keys()
        ):
            if logthiscommand:
                print(
                    discordtotitanfall[serverid]["returnids"]["commandsreturn"][str(id)]
                )
            if overridemsg:
                try:
                    if extraargsintofunction == None:
                        realmessage = overridemsg(
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["output"],
                            serverid,
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["statuscode"],
                        )
                    else:
                        realmessage = overridemsg(
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["output"],
                            serverid,
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["statuscode"],
                            extraargsintofunction,
                        )

                    if not realmessage:
                        overridemsg = None
                        return
                except Exception as e:
                    print("error in overridemsg", e)
                    traceback.print_exc()
                    overridemsg = None
                    try:
                        realmessage = defaultoverride(
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["output"],
                            serverid,
                            discordtotitanfall[serverid]["returnids"]["commandsreturn"][
                                str(id)
                            ]["statuscode"],
                        )
                        overridemsg = True
                    except Exception as e:
                        print("error in defaultoverride", e)
                        overridemsg = None
            if iscommandnotmessage and not isinstance(ctx, str) and not (command.replace("!","").replace("/","").lower()).startswith("playingpoll"):
                try:
                    await ctx.respond(
                        f"Command sent to server: **{context['servers'][serverid]['name']}**."
                        + f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]['output']}```"
                        if overridemsg is None
                        else "",
                        embed=realmessage if overridemsg is not None else None,
                        ephemeral=False,
                    )
                except:
                    traceback.print_exc()
                    await ctx.reply(
                        f"Command sent to server: **{context['servers'][serverid]['name']}**."
                        + f"```{discordtotitanfall[serverid]['returnids']['commandsreturn'][str(id)]['output']}```"
                        if overridemsg is None
                        else "",
                        embed=realmessage if overridemsg is not None else None,
                    )
            elif not isinstance(ctx, str):
                await reactomessages([ctx.id], serverid, "🟢")

            break

        i += 1
    else:
        if not isinstance(ctx, str):
            if iscommandnotmessage:
                try:
                    await ctx.respond(
                        "Command response timed out - server is unresponsive",
                        ephemeral=False,
                    )
                except:
                    traceback.print_exc()
                    await ctx.reply(
                        "Command response timed out - server is unresponsive"
                    )

            else:
                await reactomessages([ctx.id], serverid, "🔴")


def getslashcommandoverridesperms(commandname,default = "rconrole"):
    if not context.setdefault("slashcommandoverrides").get(commandname):
        context["slashcommandoverrides"][commandname] = default
        savecontext()
    return context["slashcommandoverrides"][commandname]

def checkrconallowed(author, typeof="rconrole", **kwargs):
    """Checks if Discord user has RCON permissions based on roles"""
    serverid = kwargs.get("serverid", False)
    typeof = getjson(typeof)
    if not isinstance(typeof, dict):
        typeof = {"allow":typeof,"deny":False}
    # print(typeof)
    global context
    # if typeof == "everyone": return True
    # if typeof == "noone": return False

    # if author.id not in context["RCONallowedusers"]:
    #     return False
    # author.guild_permissions.administrator (THERE IS A "and False" here, it used to be "and author.guild_permissions.administrator")
    # first TRUE used to be (not hasattr(author, "roles") or not author.roles). but this fails in alternate guilds
    # print((hasattr(author, "roles") and functools.reduce(
    #             lambda a, x: a or x in list(map(lambda w: w.id, author.roles or [])),
    #             [context["overrideroles"][translaterole(serverid, typeof["deny"])]]
    #             if isinstance(context["overrideroles"][translaterole(serverid, typeof["deny"])], int)
    #             else context["overrideroles"][translaterole(serverid, typeof["deny"])],
    #             False,
    #         )))
    # print( not typeof["deny"] or typeof["deny"] != "everyone" or not context["overriderolesuids"].get(translaterole(serverid, typeof["deny"]) or author.id not in context["overriderolesuids"][translaterole(serverid, typeof["deny"])]))
    return not typeof["allow"] or (context["overriderolesuids"].get(translaterole(serverid, typeof["allow"])) and ((True and author.id in context["overriderolesuids"][translaterole(serverid, typeof["allow"])]) or (
        hasattr(author, "roles")
        and (
            (typeof["allow"] == "rconrole" and False)
            or (typeof["allow"] == "coolperksrole" and OVVERRIDEROLEREQUIRMENT == "1")
            or functools.reduce(
                lambda a, x: a or x in list(map(lambda w: w.id, author.roles or [])),
                [context["overrideroles"][translaterole(serverid, typeof["allow"])]]
                if isinstance(context["overrideroles"][translaterole(serverid, typeof["allow"])], int)
                else context["overrideroles"][translaterole(serverid, typeof["allow"])],
                False,
            )
        )
    ))) and ( ( not typeof["deny"] or typeof["deny"] == "everyone" or not context["overriderolesuids"].get(translaterole(serverid, typeof["deny"]) or author.id not in context["overriderolesuids"][translaterole(serverid, typeof["deny"])]))or (hasattr(author, "roles") and not functools.reduce(
                lambda a, x: a or x in list(map(lambda w: w.id, author.roles or [])),
                [context["overrideroles"][translaterole(serverid, typeof["deny"])]]
                if isinstance(context["overrideroles"][translaterole(serverid, typeof["deny"])], int)
                else context["overrideroles"][translaterole(serverid, typeof["deny"])],
                False,
            )) )


# command slop
def translaterole(serverid, role):
    if not serverid:
        return role
    return context["servers"][serverid]["roles"].get(role, role)


@functools.lru_cache(maxsize=None)
def checkrconallowedtfuid(uid, typeof="rconrole", **kwargs):
    typeof = getjson(typeof)
    if not isinstance(typeof, dict):
        typeof = {"allow":typeof,"deny":False}
    # if typeof == "everyone": return True
    # if typeof == "noone": return False
    serverid = kwargs.get("serverid", False)
    """Checks if TF UID has RCON permissions for server administration"""
    global context
    # return False
    if OVVERRIDEROLEREQUIRMENT == "1" and typeof["allow"] == "coolperksrole":
        return True
    # print("CHECKING UID",uid)
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute("SELECT discordid FROM discordlinkdata WHERE uid = ?", (uid,))
    result = c.fetchone()

    if result is None:
        c.execute("SELECT discordid FROM discordlinkdata WHERE discordid = ?", (uid,))
        result = c.fetchone()
        # if result is None:
        #     return False

    discordid = result[0] if result else None
    # print( discordid in context["overriderolesuids"].get(
    #     translaterole(serverid, typeof), []
    # ))
    # print("meow")
    # print(result,typeof["deny"],discordid not in context["overriderolesuids"].get(
    #     translaterole(serverid, typeof["deny"]), []
    # ))
    return (not typeof["allow"] or typeof["allow"] == "everyone" or  result and discordid in context["overriderolesuids"].get(
        translaterole(serverid, typeof["allow"]), []
    )) and (not result or not typeof["deny"] or discordid not in context["overriderolesuids"].get(
        translaterole(serverid, typeof["deny"]), []
    )) and typeof["deny"] != "everyone"


def create_dynamic_command(
    command_name,
    description=None,
    rcon=False,
    parameters=[],
    commandparaminputoverride={},
    outputfunc=None,
    regularconsolecommand=False,
):
    """Dynamically creates Discord slash commands with RCON support, parameter validation, and custom output processing"""
    param_list = []
    for param in parameters:
        pname = param["name"]
        ptype = param["type"]
        pdesc = param.get("description", "")
        prequired = param.get("required", True)
        autocomplete = (
            globals().get(param.get("autocompletefunc", None))
            if param.get("autocompletefunc", None)
            and callable(globals().get(param.get("autocompletefunc", None)))
            else None
        )
        autocompplete = autocomplete.__name__ if autocomplete is not None else None
        if "choices" in param and param["choices"]:
            pchoices = param["choices"]
            param_str = f'{pname}: Option({ptype}, "{pdesc}", choices={pchoices}, required={prequired})'
        else:
            param_str = f'{pname}: Option({ptype}, "{pdesc}", required={prequired}, autocomplete = {autocompplete})'
        if not prequired:
            param_str += " = None"
        param_list.append(param_str)
    # SERVERNAMEISCHOICE
    if SERVERNAMEISCHOICE == "1":
        servername_param = f'servername: Option(str, "The servername (omit for current channel\'s server)", required=False ,choices=list(s.get("name", "Unknown") for s in context["servers"].values())) = None'
    else:
        servername_param = f'servername: Option(str, "The servername (omit for current channel\'s server)", required=False,autocomplete=autocompleteserversfromdb) = None'
    param_list.append(servername_param)
    params_signature = ", ".join(param_list)
    # print(commandparaminputoverride)
    quotationmark = '"'
    if not regularconsolecommand:
        command_parts = [f'"!{command_name}"'] + [
            f'{"(" + quotationmark + commandparaminputoverride[param["name"]] + " " + quotationmark + "if bool(" + param["name"] + ") else " + quotationmark + quotationmark + ") +" if param["name"] in list(commandparaminputoverride.keys()) else ""}(str({param["name"]}) if bool({param["name"]}) else "")'
            for param in parameters
        ]
    else:
        command_parts = [
            f'{"(" + quotationmark + commandparaminputoverride[param["name"]] + " " + quotationmark + "if bool(" + param["name"] + ") else " + quotationmark + quotationmark + ") +" if param["name"] in list(commandparaminputoverride.keys()) else ""}(str({param["name"]}) if bool({param["name"]}) else "")'
            for param in parameters
        ]
    if "appendtoend" in commandparaminputoverride.keys():
        command_parts.append(commandparaminputoverride["appendtoend"])
    # print(command_name,command_parts)
    command_expr = " + ' ' + ".join(command_parts)
    # print(command_expr)

    # print(parameters[0]["name"] if len(parameters) > 0 else None,list(commandparaminputoverride.keys()))

    dict_literal = (
        "{" + ", ".join([f'"{p["name"]}": {p["name"]}' for p in parameters]) + "}"
    )

    # print(dict_literal)
    outputfunc_expr = outputfunc.__name__ if outputfunc is not None else None
    # this code here HURTS MY HEAD but is incredibly cool in the way it works
    func_code = f'''
@bot.slash_command(name="{command_name}", description="{description}")
async def {command_name}(ctx, {params_signature}):
    global messageflush, context
    serverid = getchannelidfromname(servername, ctx)
    if serverid is None:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Server not bound to this channel, could not send command.", ephemeral=False)
        return
    if resolvecommandpermsformainbot(serverid,"{command_name}") == None:
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond("Command response timed out - server is unresponsive", ephemeral=False)
        return
    if (resolvecommandpermsformainbot(serverid,"{command_name}") and checkrconallowed(ctx.author,resolvecommandpermsformainbot(serverid,"{command_name}",True),serverid=serverid)):
        pass #this stuff hurts my brain. good enough IF YOU ARE ALLOWED
    elif (resolvecommandpermsformainbot(serverid,"{command_name}")) or {rcon} and not checkrconallowed(ctx.author,serverid=serverid):
        await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
        await ctx.respond(f"You are not allowed to use this command, you need **{{translaterole(serverid,"rconrole") if not resolvecommandpermsformainbot(serverid,"{command_name}") else translaterole(serverid,resolvecommandpermsformainbot(serverid,"{command_name}"))}}**", ephemeral=False)
        return
    params = {dict_literal}
    print("DISCORDCOMMAND {command_name} command from", ctx.author.name, "with parameters:", params," to server:", servername)
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
        "metadata": {{"type":"botcommand"}},
        "servername" :context["servers"][serverid]["name"],
        "player":  f"`BOT COMMAND` sent by {{ctx.author.name}}"
    }})
    await returncommandfeedback(*sendrconcommand(serverid, command, sender = ctx.author.name), ctx, {outputfunc_expr})
'''

    exec(func_code, globals())
    return globals()[command_name]


for command_name, command_info in context["commands"]["botcommands"].items():
    create_dynamic_command(
        command_name=command_name,
        description=command_info["description"]
        if "description" in command_info
        else "No description available",
        parameters=command_info["parameters"] if "parameters" in command_info else [],
        rcon=command_info["rcon"] if "rcon" in command_info else False,
        commandparaminputoverride=command_info["commandparaminputoverride"]
        if "commandparaminputoverride" in command_info
        else {},
        outputfunc=globals().get(command_info["outputfunc"])
        if "outputfunc" in command_info
        and callable(globals().get(command_info["outputfunc"]))
        else None,
        regularconsolecommand=command_info["regularconsolecommand"]
        if "regularconsolecommand" in command_info
        else False,
    )
# Sans fight
if SANSURL:
    @bot.slash_command(name="giftnonrcon", description="Give yourself a gun! that easy!")
    async def giftnonrcon(
        ctx,
        player: Option(
            str, "Player to gift", autocomplete=autocompletenamesfromingame
        ),
        weapon: Option(
            str, "Weapon to gift to player", autocomplete=weaponnamesautocomplete
        ),
        mods: Option(
            str, "Weapon mods (comma or space separated)", required=False
        ) = None,
    ):
        global sansthings, lasttimethrown
        realweapon = False
        unsure = False
        for pewpew,vanity in WEAPON_NAMES.items():
            if vanity == weapon: realweapon = pewpew
        if not realweapon:
            await ctx.respond("weapon not found", ephemeral=False)
            unsure = True
            realweapon = weapon
        player = player[:20]
        weapon = realweapon[:40]
        mods = mods[:20] if mods else None
        if  len(list(filter(lambda x: x.isalpha() or x in ", -_" or x.isdigit() ,list(player+weapon)))) != len(list(player+weapon)):
            await ctx.respond("mods or player not in a-z", ephemeral=False)
        mods_str = f" with mods: {mods}" if mods else ""
        print(f"Gift command from {ctx.author.id} for {player} with {weapon}{mods_str}")
        serverid = getchannelidfromname(None, ctx)
        if serverid is None:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond(
                "Server not bound to this channel, could not send command.",
                ephemeral=False,
            )
            return
        # Check cooldown similar to thrownonrcon
        if (
            ctx.author.id in lasttimethrown["passes"].keys()
            and lasttimethrown["passes"][ctx.author.id] > time.time() - 60
        ):
            print("User has been allowed recently")
            await ctx.defer(ephemeral=False)
            weapon_with_mods = f"{weapon}{f' with mods: {mods}' if mods else ''}"
            await ctx.respond(f"**{weapon_with_mods} gifted to {player}** (verification bypass - recently completed challenge)", ephemeral=False)
            sendrconcommand( #is a bit hard for this one, sadly :( (perms)
            serverid,
            f'sv_cheats 1;  script CheckWeaponId(discordlogmatchplayers("{player}")[0],"{weapon}"{mods and (f",{str(mods.split(",") if "," in mods else mods.split(" ")).replace("'",'"')}") or "" }); sv_cheats 0',
            sender=ctx.author.name,
            )
            return

        if lasttimethrown["globalcounter"] > time.time() - 0:
            await ctx.respond(
                "This command is on cooldown, try again in "
                + str(int(0 - (time.time() - lasttimethrown["globalcounter"])))
                + " seconds.",
                ephemeral=False,
            )
            return

        await ctx.defer(ephemeral=False)
        original_message = await ctx.interaction.original_response()
        challenge = sansthings.createchallenge(maxtries=-1)

        challenge_url = await challenge.__anext__()
        await ctx.respond("meow", ephemeral=False)
        thread = await original_message.create_thread(
            name=f"Gift Verification: {ctx.author.display_name} | {challenge_url}",
            auto_archive_duration=60,
        )

        weapon_display = f"{weapon}{f' with mods: {mods}' if mods else ''}"
        await thread.send(f"""
To gift `{weapon_display}` to `{player}`, you must complete this Captcha:
Challenge URL: {challenge_url}
-# (Select normal mode - otherwise will not be valid)
{"" if not unsure else f"> `{weapon}` might not exist, trying to gift anyways"}
""")
        challenge_completed = False
        try:
            async for game_data in challenge:
                if game_data:
                    await thread.send(f"Result found:\n```json\n{json.dumps({"winstate":game_data["condition"],"time taken":modifyvalue(int(float(game_data["time"])),"time"), "validresult":game_data["valid"]}, indent=2)}\n```")
                    if game_data.get('condition') == 'lucky' and game_data.get('valid', False):
                        challenge_completed = True
                        await thread.send("** completed successfully!** Gift command approved.")
                        lasttimethrown["passes"][ctx.author.id] = time.time()
                        lasttimethrown["globalcounter"] = time.time()
                        await thread.send(f"**{weapon_display} gifted to {player}!**")
                        # print(f'sv_cheats 1;  script CheckWeaponId(discordlogmatchplayers("{player}")[0],"{weapon}"{mods and (f",{mods.split(",") if "," in mods else mods.split(" ")}") or "" }); sv_cheats 0')
                        sendrconcommand( #same story (perms)
                        serverid,
                        f'sv_cheats 1;  script CheckWeaponId(discordlogmatchplayers("{player}")[0],"{weapon}"{mods and (f",{str(mods.split(",") if "," in mods else mods.split(" ")).replace("'",'"')}") or "" }); sv_cheats 0',
                        sender=ctx.author.name,
                        )
                        break

        except Exception as e:
            await thread.send(f"**Error monitoring challenge:** {str(e)}")
            traceback.print_exc()
        if not challenge_completed:
            await thread.send(f"**Challenge failed or timed out!** {weapon_display} gift to {player} denied.")
            lasttimethrown["globalcounter"] = time.time()


# THROW AI NON SLOP
if SHOULDUSETHROWAI == "1":
    print("ai throw enabled")
    lasttimethrown = {"specificusers": {}, "globalcounter": 0, "passes": {}}
    aibotmessageresponses = {}

    @bot.slash_command(name="thrownonrcon", description="non rcon throw command")
    async def getuid(
        ctx,
        playername: Option(
            str, "Who gets thrown", autocomplete=autocompletenamesfromingame
        ),
        # servername: Option(
        #     str, "The servername (omit for current channel's server)", required=False
        # ) = None,
    ):
        global \
            context, \
            discordtotitanfall, \
            lasttimethrown, \
            aibotmessageresponses, \
            messageflush

        servername = None
        messagehistory = []
        keyaireply = random.randint(1, 10000000000000)
        aibotmessageresponses[keyaireply] = []
        print("thrownonrcon command from", ctx.author.id, "to", playername)
        serverid = getchannelidfromname(servername, ctx)
        if serverid is None:
            await asyncio.sleep(SLEEPTIME_ON_FAILED_COMMAND)
            await ctx.respond(
                "Server not bound to this channel, could not send command.",
                ephemeral=False,
            )
            return
        messageflush.append(
            {
                "timestamp": int(time.time()),
                "serverid": serverid,
                "type": 3,
                "globalmessage": True,
                "overridechannel": "commandlogchannel",
                "messagecontent": "!thrownonrcon",
                "metadata": {"type": "botcommand"},
                "servername": context["servers"][serverid]["name"],
                "player": f"`BOT COMMAND` sent by {ctx.author.name}",
            }
        )
        if (
            ctx.author.id in lasttimethrown["passes"].keys()
            and lasttimethrown["passes"][ctx.author.id] > time.time() - 60
        ):
            print("has been allowed recently")
            await ctx.defer(ephemeral=False)
            await returncommandfeedback(
                *sendrconcommand( #same here (perms)
                    serverid, f"!throw {playername}", sender=ctx.author.name
                ),
                ctx,
            )
            return
        if lasttimethrown["globalcounter"] > time.time() - 60:
            await ctx.respond(
                "This command is on cooldown, try again in "
                + str(int(60 - (time.time() - lasttimethrown["globalcounter"])))
                + " seconds.",
                ephemeral=False,
            )
            return

        await ctx.defer(ephemeral=False)

        original_message = await ctx.interaction.original_response()

        # Create a thread attached to the original message.
        await ctx.respond("creating thread", ephemeral=False)
        threade = await original_message.create_thread(
            name=f"throw request for {ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}",
            auto_archive_duration=60,
        )

        # Notify the channel that the thread has been created.
        # await ctx.followup.send(f"Thread created: {thread.mention}", ephemeral=False)

        # Set up waiting for messages from the original user in the thread.
        count = 0
        start_time = time.time()
        # response = requests.post("http://localhost:11434/api/generate", json = {"prompt": question,"model":"mistral","stream":True,"seed":0,"temperature":1,"options":{"num_predict":-1}})

        await threade.send("""Justify your use of this command:
- you have 5 messages to do so, after witch, it auto denys
- Only send one message at a time, and wait for response (it can take a while, ai is hard).
- messages that are being processed are marked by a 🟢
- if you fail, you must wait a short while before asking again.
- if you succeed, you are allowed to freely use the command for 60 seconds""")
        while count < 5 and (time.time() - start_time < 15 * 60):

            def check(m):
                return m.author.id == ctx.author.id and m.channel.id == threade.id

            remaining_time = 15 * 60 - (time.time() - start_time)
            try:
                message = await bot.wait_for(
                    "message", timeout=remaining_time, check=check
                )
                await message.add_reaction("🟢")
                if count != len(aibotmessageresponses[keyaireply]):
                    await message.reply(f"Text not used, wait for response")
            except asyncio.TimeoutError:
                break

            messagehistory.append(
                f"{ctx.author.nick if ctx.author.nick is not None else ctx.author.display_name}: {message.content}"
            )
            newline = "\n"
            historyinfo = (
                f"""
The users history of using this command, from oldest to newest is:
{newline.join(list(map(lambda a: f"button {a['button']}: Time since: {str(int((time.time() - a['timestamp']) // 60)) + ' minutes ago' if (time.time() - a['timestamp']) < 86400 else '> 1 day'} because {a['one_word_reason']}", list(filter(lambda a: time.time() - a["timestamp"] < 172800, lasttimethrown["specificusers"][ctx.author.id][-10:])))))}
"""
                if ctx.author.id in lasttimethrown["specificusers"].keys()
                and len(lasttimethrown["specificusers"][ctx.author.id]) > 1
                else ""
            )
            prompt = f'''<SYSTEM MESSAGE>
You are a AI model, choosing one of three choices, "allow_request", "deny_request" and "more_information_needed". You should also give a reason for your choice.
To inform your choices, you are given an array of user messages, in chronological order, formatted ["username: messagecontent",...], as such, you should place most importance on the later user past messages.
The user is asking to use a command on a titanfall 2 sever. this command throws a targeted player into the air, in the game Titanfall 2. Your role is to be skeptical that the user needs to use this command, due to the fact that it can be seen as unfair or even unfun by the targeted player(s).
If the user has a reason that you deem would bring GREAT value however, don't hesitate to press the "allow_request button". This will allow the command to be executed. HOWEVER YOU SHOULD HAVE EXTREME PREJUDICE AGAINST USING THIS BUTTON. ALMOST NEVER ALLOW IT, ESPECIALLY IF THE USER HAS BEEN ALLOWED OR DENIED RECENTLY.
If you believe the user might make a good case to deserve using the command, with good reasoning, press "more_information_needed".
If you believe the user is trying to mislead you (they probably are), is undeserving, is too rude, is trying to get a competitive advantage, or simply have the feeling of being powerful, press "deny_request".
ENQUIRE A LOT ABOUT LARGE CLAIMS. the user is probably LYING. and so you should "more_information_needed"

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
{"The last time the user tried to use this command was: " + str(int(time.time() - lasttimethrown["specificusers"][ctx.author.id][-1]["timestamp"])) + " seconds ago, and you responded " + lasttimethrown["specificusers"][ctx.author.id][-1]["button"] + " due to " + lasttimethrown["specificusers"][ctx.author.id][-1]["one_word_reason"] if ctx.author.id in lasttimethrown["specificusers"].keys() else "This is the first time the user has tried to use this command. (since bot restart)"}
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
{newline.join(list(map(lambda x: str(x), aibotmessageresponses[keyaireply])))}
'''  # TO BE DONE, SAY HOW MANY DENYS AND HOW MANY ALLOWS, AND HOW MANY WERE IN PAST HOUR. LEARN ABOUT SANDBOXING IMPLEMENT THE SHORT TIME WHITELIST, AND ALSO THE 60 SECONDS DENY
            # print(f'{"The last time the user tried to use this command was: " + str(time.time()-lasttimethrown["specificusers"][ctx.author.id][-1]["timestamp"]) + " seconds ago, and it was " + lasttimethrown["specificusers"][ctx.author.id][-1]["button"] if ctx.author.id in lasttimethrown["specificusers"].keys() else "This is the first time the user has tried to use this command. since bot restart"}')
            print(prompt)
            threading.Thread(
                target=threadwrap,
                daemon=True,
                args=(respondtotext, message, prompt, keyaireply),
            ).start()
            count += 1

            while count != len(aibotmessageresponses[keyaireply]):
                await asyncio.sleep(0.3)
                # print(aibotmessageresponses)
            if aibotmessageresponses[keyaireply][-1]["button"] == "deny_request":
                if ctx.author.id not in lasttimethrown["specificusers"].keys():
                    lasttimethrown["specificusers"][ctx.author.id] = []
                lasttimethrown["specificusers"][ctx.author.id].append(
                    {
                        "button": "deny_request",
                        "timestamp": time.time(),
                        "one_word_reason": aibotmessageresponses[keyaireply][-1][
                            "reasononeword"
                        ],
                    }
                )
                await threade.send(
                    "# request denied, run the command again, and try be more persuasive :)"
                )
                # await ctx.respond("request denied", ephemeral=False)
                del aibotmessageresponses[keyaireply]
                return
            elif aibotmessageresponses[keyaireply][-1]["button"] == "allow_request":
                if ctx.author.id not in lasttimethrown["specificusers"].keys():
                    lasttimethrown["specificusers"][ctx.author.id] = []
                lasttimethrown["specificusers"][ctx.author.id].append(
                    {
                        "button": "allow_request",
                        "timestamp": time.time(),
                        "one_word_reason": aibotmessageresponses[keyaireply][-1][
                            "reasononeword"
                        ],
                    }
                )
                lasttimethrown["passes"][ctx.author.id] = time.time()

                await threade.send("# request allowed, executing command")
                await returncommandfeedback(
                    *sendrconcommand( #also here (perms)
                        serverid, f"!throw {playername}", sender=ctx.author.name
                    ),
                    message,
                )
                del aibotmessageresponses[keyaireply]
                return
            elif (
                aibotmessageresponses[keyaireply][-1]["button"]
                == "more_information_needed"
            ):
                print(
                    "more info needed", aibotmessageresponses[keyaireply][-1]["button"]
                )
                pass
            # print("there")
        await threade.send("timeout, request denied")
        del aibotmessageresponses[keyaireply]

    def respondtotext(message, prompt, keyaireply):
        global aibotmessageresponses
        print("generating")
        try:
            # print(f"http://{LOCALHOSTPATH}:11434/api/generate")
            response = requests.post(
                f"http://{LOCALHOSTPATH}:11434/api/generate",
                json={
                    "prompt": prompt,
                    "model": DISCORDBOTAIUSED,
                    "stream": False,
                    "keep_alive": "12000m",
                    "seed": 0,
                    "temperature": 1,
                    "options": {"num_predict": -1},
                },
            )
            print(response.json()["response"])
            output = response.json()["response"]
            output = output[output.index("</think>") + 8 :].strip()
            output = json.loads(output)
            aibotmessageresponses[keyaireply].append((output))
            print("done, responding")
        except Exception as e:
            print("ai crashed, error is:", e)
            traceback.print_exc()
            output = {
                "button": "deny_request",
                "reason": "ai broken. " + str(e),
                "reasononeword": "broken",
            }
            aibotmessageresponses[keyaireply].append(output)
        asyncio.run_coroutine_threadsafe(aireplytouser(message, output), bot.loop)

    async def aireplytouser(message, output):
        await message.reply(
            f"**button pressed by AI:**```{output['button']}``` \n**Reason:** ```{output['reason']}```\n**Short reason:**```{output['reasononeword']}```"
        )


# joinleave logging stuff
playercontext = {}
matchids = []
playerjoinlist = {}
peopleonline = {}


def checkandaddtouidnamelink(uid, playername, serverid, istf1=False,playerinfo={}):
    
    """Updates player UID-name mapping in database with timestamp tracking"""
    global playercontext
    # print("PLAYERINFO",json.dumps(playerinfo))
    now = int(time.time())
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        f"SELECT id, playername, ipinfo, lastserverid FROM uidnamelink{'tf1' if istf1 else ''} WHERE playeruid = ? ORDER BY id DESC LIMIT 1",
        (uid,),
    )
    row = c.fetchone()
    
    if row:
        last_id, last_name, ipinfo, lastserverid = row
        if ipinfo:
            ipinfo = json.loads(ipinfo)

        if not istf1 and playerinfo and playerinfo.get("ipaddr") and re.match(r'^(\d{1,3}\.){3}\d{1,3}$', playerinfo.get("ipaddr")):
            if ipinfo:
                if getpriority(ipinfo[-1],"ip") == playerinfo["ipaddr"]:
                    # print("this")
                    ipinfo[-1]["last"] = now
                else:
                    # print("that")
                    ipinfo.append({"ip":playerinfo["ipaddr"],"first":now,"last":now})
            else:
                # print("woa")
                ipinfo = [{"ip":playerinfo["ipaddr"],"first":now,"last":now}]

        if int(serverid) != lastserverid:
            resolveplayeruidfromdb.cache_clear()
        if str(playername) == str(last_name):
            c.execute(
                f"UPDATE uidnamelink{'tf1' if istf1 else ''} SET lastseenunix = ?, lastserverid = ?, ipinfo = ?  WHERE id = ?",
                (now, int(serverid), json.dumps(ipinfo) if ipinfo else None, last_id),
            )
        else:
            resolveplayeruidfromdb.cache_clear()
            c.execute(
                f"INSERT INTO uidnamelink{'tf1' if istf1 else ''} (playeruid, playername, firstseenunix, lastseenunix, lastserverid, ipinfo) VALUES (?, ?, ?, ?, ?, ?)",
                (uid, playername, now, now, int(serverid), json.dumps(ipinfo) if ipinfo else None),
            )
    else:
        resolveplayeruidfromdb.cache_clear()
        c.execute(
            f"INSERT INTO uidnamelink{'tf1' if istf1 else ''} (playeruid, playername, firstseenunix, lastseenunix, lastserverid, ipinfo) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, playername, now, now, int(serverid), json.dumps({playerinfo["ipaddr"]:{"first":now,"last":now}}) if playerinfo.get("ipaddr") else None),
        )
    tfdb.commit()
    tfdb.close()


def onplayerjoin(uid, serverid, nameof=False):
    """Handles player join events, updates databases, sends notifications, and manages join counters"""
    global context, messageflushnotify, playerjoinlist
    istf1 = (
        context["servers"].get(serverid, {}).get("istf1server", False)
    )  # {"tf2" if istf1 else ""}
    if istf1:
        return
    # print("joincommand", uid, serverid)
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute("SELECT discordidnotify FROM joinnotify WHERE uidnotify = ?", (uid,))
    discordnotify = c.fetchall()
    c.execute(
        "SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",
        (uid,),
    )
    # c.execute("SELECT playername FROM uidnamelink WHERE playeruid = ?",(uid,))
    playernames = c.fetchall()
    if playernames:
        playernames = [x[0] for x in playernames]
    if nameof not in playernames or not playernames:
        # c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(uid,nameof))
        checkandaddtouidnamelink(uid, nameof, serverid)
        tfdb.commit()
    if nameof:
        playername = nameof
    else:
        playername = f"Unknown user by uid {uid}"
    # print(f"{uid}{playername}",playerjoinlist)
    if (
        f"{uid}{playername}" in playerjoinlist.keys()
        and playerjoinlist[f"{uid}{playername}"]
    ):
        print("already in list")
        return
    c.execute(
        "SELECT count FROM joincounter WHERE playeruid = ? AND serverid = ?",
        (uid, serverid),
    )
    count = c.fetchone()
    if count:
        count = count[0] + 1
        c.execute(
            "UPDATE joincounter SET count = ? WHERE playeruid = ? AND serverid = ?",
            (count, uid, serverid),
        )
    else:
        c.execute(
            "INSERT INTO joincounter (playeruid,serverid,count) VALUES (?,?,1)",
            (uid, serverid),
        )
    tfdb.commit()

    if discordnotify:
        discordnotify = [x[0] for x in discordnotify]
    servername = context["servers"][serverid]["name"]

    playerjoinlist[f"{uid}{playername}"] = True
    for discordid in discordnotify:
        print("notifying join", discordid)
        messageflushnotify.append(
            {
                "servername": servername,
                "player": playername,
                "userid": discordid,
                "sendingmessage": f"[JOINNOTIFY] {playername} has joined {servername}, disable this with /togglejoinnotify",
            }
        )
    tfdb.close()


def onplayerleave(uid, serverid):
    """Handles player disconnect events and updates tracking databases"""
    global context, messageflushnotify, playercontext
    istf1 = (
        context["servers"].get(serverid, {}).get("istf1server", False)
    )  # {"tf2" if istf1 else ""}
    if istf1:
        return
    print("leavecommand", uid, serverid)
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute("SELECT discordidnotify FROM joinnotify WHERE uidnotify = ?", (uid,))
    discordnotify = c.fetchall()
    c.execute(
        "SELECT playername FROM uidnamelink WHERE playeruid = ? ORDER BY id DESC LIMIT 1",
        (uid,),
    )
    playername = c.fetchone()
    if playername:
        playername = playername[0]
    else:
        playername = f"Unkown user by uid {uid}"
    if discordnotify:
        discordnotify = [x[0] for x in discordnotify]
    servername = context["servers"][serverid]["name"]
    if (
        f"{uid}{playername}" in playerjoinlist.keys()
        and not playerjoinlist[f"{uid}{playername}"]
    ):
        return
    playerjoinlist[f"{uid}{playername}"] = False
    for discordid in discordnotify:
        print("notifying leave", discordid)
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
    """Saves detailed kill/death statistics to database with weapon and position data"""
    # 1 is normal, they just left
    # 2 is map change
    # 3 is server crash
    # 4 is tempory save
    global playercontext
    # print("saving playerinfo",saveinfo)
    istf1 = (
        context["servers"].get(saveinfo["serverid"], {}).get("istf1server", False)
    )  # {"tf2" if istf1 else ""}
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    # params = (
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"],
    #     saveinfo["endtype"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["score"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["titankills"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["kills"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["deaths"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["endtime"] - playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["joined"],
    #     playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["idoverride"],
    # )

    # print("Params before execute:", params)
    try:
        c.execute(
            f"SELECT playername FROM uidnamelink{'tf1' if istf1 else ''} WHERE playeruid = ? ORDER BY id DESC LIMIT 1",
            (
                playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
                    saveinfo["matchid"]
                ][saveinfo["index"]]["uid"],
            ),
        )
        playernames = c.fetchall()
        if playernames:
            playernames = [x[0] for x in playernames]
        if (
            playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
                saveinfo["matchid"]
            ][saveinfo["index"]]["name"]
            not in playernames
            or not playernames
        ):
            # c.execute("INSERT INTO uidnamelink (playeruid,playername) VALUES (?,?)",(playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["uid"],playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][saveinfo["matchid"]][saveinfo["index"]]["name"]))

            checkandaddtouidnamelink(
                playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
                    saveinfo["matchid"]
                ][saveinfo["index"]]["uid"],
                playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
                    saveinfo["matchid"]
                ][saveinfo["index"]]["name"],
                saveinfo["serverid"],
                istf1,
                playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                    saveinfo["name"]
                ][saveinfo["matchid"]][saveinfo["index"]]
            )
        if (
            playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
                saveinfo["matchid"]
            ][saveinfo["index"]]["idoverride"]
            != 0
        ):
            c.execute(
                f"UPDATE playtime{'tf1' if istf1 else ''} SET leftatunix = ?, endtype = ?, scoregained = ?, titankills = ?, pilotkills = ?, deaths = ?, duration = ? WHERE id = ?",
                (
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["endtime"],
                    saveinfo["endtype"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["score"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["titankills"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["kills"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["deaths"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["endtime"]
                    - playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["joined"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["idoverride"],
                ),
            )
            lastrowid = playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                saveinfo["name"]
            ][saveinfo["matchid"]][saveinfo["index"]]["idoverride"]
        else:
            c.execute(
                f"INSERT INTO playtime{'tf1' if istf1 else ''} (playeruid,joinatunix,leftatunix,endtype,serverid,scoregained,titankills,pilotkills,npckills,deaths,map,duration,matchid,timecounter ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
                (
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["uid"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["joined"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["endtime"],
                    saveinfo["endtype"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["serverid"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["score"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["titankills"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["kills"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["npckills"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["deaths"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["map"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["endtime"]
                    - playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["joined"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["matchid"],
                    playercontext[saveinfo["serverid"]][saveinfo["uid"]][
                        saveinfo["name"]
                    ][saveinfo["matchid"]][saveinfo["index"]]["timecounter"],
                ),
            )
            lastrowid = c.fetchone()[0]
    except Exception as e:
        print("error in saving", e)
        traceback.print_exc()
        return 0
    if saveinfo["endtype"] == 1 or saveinfo["endtype"] == 2:
        playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
            saveinfo["matchid"]
        ][saveinfo["index"]]["playerhasleft"] = True
    if saveinfo["endtype"] != 4:
        pass
    playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
        saveinfo["matchid"]
    ][saveinfo["index"]]["mostrecentsave"] = True
    playercontext[saveinfo["serverid"]][saveinfo["uid"]][saveinfo["name"]][
        saveinfo["matchid"]
    ][saveinfo["index"]]["idoverride"] = lastrowid

    tfdb.commit()
    tfdb.close()
    return lastrowid


def addmatchtodb(matchid, serverid, currentmap):
    """Adds match information to database for tracking game sessions"""
    global matchids, playercontext, currentduels, potentialduels
    istf1 = (
        context["servers"].get(serverid, {}).get("istf1server", False)
    )  # {'tf1' if istf1 else ''}
    # print("adding match to db",matchid,serverid)
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    c.execute(
        f"SELECT matchid FROM matchid{'tf1' if istf1 else ''} WHERE matchid = ?",
        (str(matchid),),
    )
    matchidcheck = c.fetchone()
    if matchidcheck:
        if serverid not in playercontext.keys():
            playercontext[serverid] = {}
        # print("already in db, loading data")
        c.execute(
            f"SELECT playeruid,joinatunix,leftatunix,endtype,serverid,scoregained,titankills,pilotkills,npckills,deaths,map,duration,id,timecounter FROM playtime{'tf1' if istf1 else ''} WHERE matchid = ?",
            (str(matchid),),
        )
        matchdata = c.fetchall()
        c.execute(
            f"SELECT playername,playeruid FROM uidnamelink{'tf1' if istf1 else ''}"
        )
        playernames = c.fetchall()
        playernames = {str(x[1]): x[0] for x in playernames}
        for player in matchdata:
            player = list(player)
            player[0] = str(player[0])
            player[4] = str(player[4])
            # print("loading player data",player[0])
            if player[0] not in playercontext[serverid]:
                playercontext[serverid][player[0]] = {}
            if (
                player[0] in playernames.keys()
                and playernames[player[0]]
                not in playercontext[serverid][player[0]].keys()
            ):
                playercontext[serverid][player[0]][playernames[player[0]]] = {}
            else:
                pass
                # print("panic")
                # print(player[0],playernames[player[0]],playercontext[serverid][player[0]],playernames, player[0] in playernames.keys(),playernames[player[0]] not in playercontext[serverid][player[0]].keys())
                # print(list(playernames.keys()),[ player[0]])
                continue
            if (
                matchid
                not in playercontext[serverid][player[0]][playernames[player[0]]]
            ):
                playercontext[serverid][player[0]][playernames[player[0]]][matchid] = []
            playercontext[serverid][player[0]][playernames[player[0]]][matchid].append(
                {
                    "uid": player[0],
                    "name": playernames[player[0]],
                    "joined": player[1],
                    "endtime": player[2],
                    "serverid": player[4],
                    "score": player[5],
                    "titankills": player[6],
                    "kills": player[7],
                    "npckills": player[8],
                    "deaths": player[9],
                    "map": player[10],
                    "idoverride": player[12],
                    "matchid": matchid,
                    "playerhasleft": player[3] == 1,
                    "mostrecentsave": True,
                    "loadedfromsave": True,
                    "timecounter": player[13],
                }
            )
        matchids.append(matchid)
        c.execute("SELECT initiator, receiver, initiatorscore, receiverscore FROM duels WHERE matchid = ?",(str(matchid),))
        currentstabs = (c.fetchall())
        for duel in currentstabs:
            potentialduels.setdefault(matchid,{}).setdefault(str(duel[0]),[]).append(str(duel[1]))
            potentialduels.setdefault(matchid,{}).setdefault(str(duel[1]),[]).append(str(duel[0]))
            currentduels.setdefault(serverid,{}).setdefault(matchid,{}).setdefault(str(duel[0]),{}).setdefault(str(duel[1]),{str(duel[0]):duel[2],str(duel[1]):duel[3]})
        #     print("e")
        # print(json.dumps(currentduels,indent = 4))
        return
    c.execute(
        f"INSERT INTO matchid{'tf1' if istf1 else ''} (matchid,serverid,map,time) VALUES (?,?,?,?)",
        (matchid, serverid, currentmap, int(time.time())),
    )


    tfdb.commit()
    tfdb.close()
    matchids.append(matchid)
    asyncio.run_coroutine_threadsafe(hideandshowchannels(serverid), bot.loop)


def playerpolllog(data, serverid, statuscode):
    """Processes server player poll data and manages join/leave events with database updates"""
    # print("playerpoll",serverid,statuscode)
    Ithinktheplayerhasleft = 90
    global discordtotitanfall, playercontext, playerjoinlist, matchids, peopleonline,mostrecentmatchids
    # save who is playing on the specific server into playercontext.
    # dicts kind of don't support composite primary keys..
    # use the fact that theoretically one player can be on just one server at a time
    # playerid+playername = primary key. this is because of the edge case where people join one server on one account twice because.. well they do that sometimes
    # print(data,serverid,statuscode)
    # sendrconcommand(
    #     "23",
    #     f"!highlightplayertoplayer 1012640166434 2509670718",
    #     sender=None,
    # )
    # sendrconcommand(
    #     "23",
    #     f"!highlightplayertoplayer 2509670718 1012640166434",
    #     sender=None,
    # )
    istf1 = (
        context["servers"].get(serverid, {}).get("istf1server", False)
    )  # {"tf2" if istf1 else ""}
    # print("DATA",serverid,data)
    # if not data: print("true")
    # print(data)
    if not istf1:
        currentmap = data["meta"][0]
        matchid = data["meta"][2]
    else:
        currentmap = data["meta"]["map"]
        matchid = data["meta"]["matchid"]
    if matchid not in matchids:
        addmatchtodb(matchid, serverid, currentmap)
    now = int(time.time())
    # players = [lambda x: {"uid":x[0],"score":x[1][0],"team":x[1][1],"kills":x[1][2],"deaths":x[1][3],"name":x[1][4],"titankills":x[1][5],"npckills":x[1][6]} for x in list(filter(lambda x: x[0] != "meta",list(data.items())))]
    if not istf1:
        players = [
            {
                "uid": x[0],
                "score": x[1][0],
                "team": x[1][1],
                "kills": x[1][2],
                "deaths": x[1][3],
                "name": x[1][4],
                "titankills": x[1][5],
                "npckills": x[1][6],
                "timecounter": x[1][7],
                "ipaddr": x[1][8] if len(x[1]) > 8 else False
            }
            for x in list(filter(lambda x: x[0] != "meta", list(data.items())))
        ]
    else:
        players = [
            {
                "uid": str(x[0]),
                "score": x[1][1],
                "team": "UNKNOWN TEAM, UNUSED VAR",
                "kills": x[1][2],
                "deaths": x[1][3],
                "name": x[1][0],
                "titankills": x[1][4],
                "npckills": x[1][6],
                "timecounter": x[1][6],
                "ipaddr": False
            }
            for x in filter(lambda x: x[0] != "meta" and len(x[0]) > 15, data.items())
        ]
        if data.get("meta", False):
            metadata = data["meta"].copy()
            metadata["matchid"] = data["meta"]["matchid"]
            data["meta"] = [
                metadata["map"],
                50,
                metadata["matchid"],
            ]  # 50 is a placeholder for actual time left!
        newplayers = {}
        for index,player in enumerate(players):
            if not resolveplayeruidfromdb(data["uid"],"uid",True) or player["name"] != getpriority(readplayeruidpreferences(player["uid"], False),["tf2","nameoverride"]) or getpriority(readplayeruidpreferences(player["uid"], False),["tf2","nameoverride"]) == resolveplayeruidfromdb(player["uid"],"uid",True)[0]["name"]:
                # this player is bad. I trust /playerdetails to fix it soon, so I am just going to pretend I did not see em
                newplayers.append(player)
    # print(players)
    discordtotitanfall[serverid]["currentplayers"] = dict(
        map(lambda x: [str(x["uid"]), x["name"]], players)
    )
    peopleonline = {
        **peopleonline,
        **dict(
            map(
                lambda x: [str(x["uid"]), {"name": x["name"], "lastseen": now,"serverid":serverid,"matchid":matchid}], players
            )
        ),
    }
    # print(json.dumps(peopleonline,indent=4))
    mostrecentmatchids[serverid] = matchid
    # print(peopleonline)

    # playercontext[pinfo["uid"]+pinfo["name"]] = {"joined":now,"map":map,"name":pinfo["name"],"uid":pinfo["uid"],"idoverride":0,"endtime":0,"serverid":serverid,"kills":0,"deaths":0,"titankills":0,"npckills":0,"score":0}
    # print(list(map(lambda x: x["name"],players)))
    uids = list(set([*list(map(lambda x: x["uid"], players))]))
    names = list(set([*list(map(lambda x: x["name"], players))]))
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
            checkandaddtouidnamelink(player["uid"], player["name"], serverid, istf1, player)
            playercontext[serverid][player["uid"]][player["name"]][matchid] = [
                {  # ON FIRST MAP JOIN
                    "joined": player[
                        "timecounter"
                    ],  # FOR BOTH JOINED CASES, TEST CHANGINT IT TO INT(PLAYER["TIMECOUNTER"])
                    "map": currentmap,
                    "name": player["name"],
                    "uid": player["uid"],
                    "idoverride": 0,
                    "endtime": now + 1,
                    "serverid": serverid,
                    "kills": 0,
                    "deaths": 0,
                    "titankills": 0,
                    "npckills": 0,
                    "score": 0,
                    "matchid": matchid,
                    "mostrecentsave": False,
                    "playerhasleft": False,
                    "timecounter": player["timecounter"],
                    "ipaddr":player["ipaddr"]
                }
            ]
        elif (
            playercontext[serverid][player["uid"]][player["name"]][matchid][-1][
                "playerhasleft"
            ]
            or playercontext[serverid][player["uid"]][player["name"]][matchid][-1][
                "timecounter"
            ]
            != player["timecounter"]
        ):
            # print("here2")
            if not playercontext[serverid][player["uid"]][player["name"]][matchid][
                -1
            ].get("loadedfromsave", False):
                onplayerjoin(player["uid"], serverid, player["name"])
            checkandaddtouidnamelink(player["uid"], player["name"], serverid, istf1, player)
            # ohgodIamreadyingthisWHATONEARTH how does it know to save? oh because it keeps accumulating iirc.. but timecounter???
            # print("beep boop",playercontext[serverid][player["uid"]][player["name"]][matchid][-1].get("loadedfromsave",False),playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["playerhasleft"], playercontext[serverid][player["uid"]][player["name"]][matchid][-1]["timecounter"] != player["timecounter"])
            playercontext[serverid][player["uid"]][player["name"]][matchid].append(
                {  # ON JOINING AFTER LEAVING
                    "joined": player["timecounter"],
                    "map": currentmap,
                    "name": player["name"],
                    "uid": player["uid"],
                    "idoverride": 0,
                    "endtime": now + 1,
                    "serverid": serverid,
                    "kills": 0,
                    "deaths": 0,
                    "titankills": 0,
                    "npckills": 0,
                    "score": 0,
                    "matchid": matchid,
                    "mostrecentsave": False,
                    "playerhasleft": False,
                    "timecounter": player["timecounter"],
                    "ipaddr":player["ipaddr"]
                }
            )
        else:
            # print("here3")
            playercontext[serverid][player["uid"]][player["name"]][matchid][
                -1
            ] = {  # ON NOT LEAVING
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
                for index, value4 in enumerate(value3):
                    if (
                        now - value4["endtime"] < Ithinktheplayerhasleft
                        and matchidofsave == matchid
                        and index == len(value3) - 1
                    ):
                        # print("not saving1", uid, name, matchidofsave)
                        continue

                    if (
                        value3[-1]["mostrecentsave"] == True
                        and (value3[-1]["playerhasleft"] == True and False)
                        or matchidofsave != matchid
                    ):
                        #### CURRENTLY DISABLED FIRST CHECK FOR BETTER END OF ROUND STATS - PLAYERS ONLY GET DELETED ON MAP CHANGE. I HOPE THIS DOES NOT BREAK ANYTHING.
                        # print("not saving2", uid, name, matchidofsave)
                        # Mark for deletion
                        to_delete.append((uid, name, matchidofsave))
                        continue
                    # print("here4")
                    if value4["mostrecentsave"] == False:
                        print("SAVING", uid, name, matchidofsave, index)
                        if matchid != matchidofsave:
                            savestats(
                                {
                                    "uid": uid,
                                    "name": name,
                                    "matchid": matchidofsave,
                                    "endtype": 2,
                                    "index": index,
                                    "serverid": serverid,
                                }
                            )
                        elif matchid == matchidofsave:
                            if index == len(value3) - 1:
                                onplayerleave(uid, serverid)
                            savestats(
                                {
                                    "uid": uid,
                                    "name": name,
                                    "matchid": matchidofsave,
                                    "endtype": 1,
                                    "index": index,
                                    "serverid": serverid,
                                }
                            )

    # Perform deletions after the loop
    for uid, name, matchidofsave in to_delete:
        # print("deleting", uid, name, matchidofsave)
        try:
            if playercontext[serverid][uid][name].get(matchidofsave):
                del playercontext[serverid][uid][name][matchidofsave]
            if not playercontext[serverid][uid][name]:
                del playercontext[serverid][uid][name]
            if not playercontext[serverid][uid]:
                del playercontext[serverid][uid]
        except KeyError:
            # sorted, just remove the print of the execution!
            # traceback.print_exc()
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
    # print("players",players)
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


def threadwrap(function, *args):
    """Thread wrapper function for safe async execution"""
    try:
        function(*args)
    except Exception as e:
        print(f"Exception in thread {threading.current_thread().name}: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        traceback.print_exc()
        print(f"Thread {threading.current_thread().name} interrupted")
    finally:
        pass


def flattendict(current, path=[], result=[]):
    """Recursively flattens nested dictionaries into dot-notation paths"""
    if isinstance(current, dict):
        for k, v in current.items():
            flattendict(v, path + [k], result)
    else:
        result.append(path + [current])

    return result


def packfortextsv3(texts, output={}):
    """Packs text data for efficient transmission with compression"""
    if not len(texts):
        # print(texts)
        return output
    return {
        "content": texts[0]["content"],
        "validation": str(texts[0]["id"]),
        "teamoverride": texts[0].get("teamoverride", 4),
        "isteammessage": texts[0].get("isteammessage", False),
        "uidoverride": ",".join(
            list(map(lambda x: str(x), texts[0].get("uidoverride", [])))
        )
        if not isinstance(texts[0].get("uidoverride", []), (str, int))
        else f"{texts[0].get('uidoverride', [])}",
        "nextmessage": packfortextsv3(texts[1:]) if len(texts[1:]) else None,
    }


def getpriority(ditionary, *priority, **kwargs):
    """Gets dictionary value using priority-based key lookup with fallbacks"""
    for route in priority:
        output = ditionary.copy()
        if isinstance(route, str):
            route = [route]
        for place in route:
            output = output.get(place, {})
        if output != {}:
            return output
    return kwargs.get("nofind", None)


def setlotsofdefault(dicto, value, *nests):
    """Sets nested dictionary values with automatic creation of intermediate keys"""
    if not nests:
        return value
    if len(nests) == 1:
        return dicto.setdefault(nests[0], value)
    return setlotsofdefault(dicto.setdefault(nests[0], {}), value, *nests[1:])


def load_extensions():
    """Load optional extension modules"""
    extensions_dir = "extensions"
    if not os.path.exists(extensions_dir):
        return

    for filename in os.listdir(extensions_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(
                    f"extensions.{module_name}",
                    f"{extensions_dir}/{filename}"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'setup'):
                    module.setup(bot, postgresem, globals())
                    print(f"Loaded extension: {module_name}")
            except Exception as e:
                print(f"Failed to load extension {module_name}: {e}")
                traceback.print_exc()


@tasks.loop(seconds=360)
async def updatechannels():
    global context, discordtotitanfall
    # print("MEOWOWOW")
    # await asyncio.sleep(30)
    # print("running server activity update")
    for serverid in context["servers"].keys():
        initdiscordtotitanfall(serverid)
        istf1 = context["servers"].get(serverid, {}).get("istf1server", False)
        server = context["servers"][serverid]
        addwidget = context["servers"][serverid].get("widget", "")
        if not addwidget:
            addwidget = ""
        elif addwidget != "":
            addwidget += "┃"
        if "channelid" not in server:
            continue
        channel = bot.get_channel(server["channelid"])
        serverlastheardfrom = getpriority(
            discordtotitanfall, [serverid, "lastheardfrom"]
        )
        # print("lastheardfrom",serverlastheardfrom)
        # print(json.dumps(discordtotitanfall))
        if not serverlastheardfrom:
            serverlastheardfrom = 0
        # print(serverid,time.time() - serverlastheardfrom > 180,"🟢" not in channel.name)
        if (
            (time.time() - serverlastheardfrom > 180 and "🟢" not in channel.name)
            or (time.time() - serverlastheardfrom < 180 and "🟢" in channel.name)
            and (
                not istf1
                and (
                    not len(discordtotitanfall[serverid]["currentplayers"])
                    and "🟢" not in channel.name
                    and not istf1
                )
                or (
                    len(discordtotitanfall[serverid]["currentplayers"])
                    and "🟢" in channel.name
                    and not istf1
                )
            )
        ):
            continue
        if (time.time() - serverlastheardfrom > 180) or (
            not istf1 and not len(discordtotitanfall[serverid]["currentplayers"])
        ):
            # print("editing here2")
            await channel.edit(name=f"{addwidget}{server['name']}")
        elif (time.time() - serverlastheardfrom < 180) and (
            istf1 or len(discordtotitanfall[serverid]["currentplayers"])
        ):
            # print("editing here")
            await channel.edit(name=f"🟢{addwidget}{server['name']}")


def playerpoll():
    """Polls server for current player list and updates databases"""
    global discordtotitanfall, playercontext, context
    Ithinktheserverhascrashed = 180
    autosaveinterval = 120
    pinginterval = 10
    # if the player leaves and rejoins, continue their streak.
    # if the server does not respond for this time, assume it crashed.
    counter = 0
    while True:
        shouldIsave = True
        counter += 1
        # print("counter",counter,autosaveinterval/pinginterval)
        if not counter % int(autosaveinterval / pinginterval):
            # print("autosaving")
            for serverid, data in playercontext.items():
                for uid, value in data.items():
                    for name, value2 in value.items():
                        for matchid, value3 in value2.items():
                            if value3[-1]["mostrecentsave"] == False:
                                # print("here")
                                savestats(
                                    {
                                        "uid": uid,
                                        "name": name,
                                        "matchid": matchid,
                                        "endtype": 4,
                                        "index": -1,
                                        "serverid": serverid,
                                    }
                                )
                                playercontext[serverid][uid][name][matchid][-1][
                                    "mostrecentsave"
                                ] = True

        # poll time
        # I want to iterate through all servers, and ask them what they are up too.
        for serverid, data in discordtotitanfall.items():
            server = context["servers"][serverid]
            if not serverid:
                print("WTF PANIC PANIC INVALID SERVERID")
            # print(discordtotitanfall)
            if server.get("istf1server", False) and not discordtotitanfall.get(
                serverid, {}
            ).get("serveronline", False):
                continue
            # print(discordtotitanfall.get(serverid,{}).get("serveronline",False))
            # print(serverid,"going")
            if time.time() - data["lastheardfrom"] > Ithinktheserverhascrashed:
                continue
            else:
                shouldIsave = False
                asyncio.run_coroutine_threadsafe(
                    returncommandfeedback(
                        *sendrconcommand(serverid, "!playingpoll"),
                        "fake context",
                        playerpolllog,
                        True,
                        False,
                    ),
                    bot.loop,
                )
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
        if any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
        ):
            image_bytes = await attachment.read()
            ascii_art = fitimage(
                image_bytes, output_width=80, ascii_char="~", maxlen=249
            )
            lenarray = [len(s) for s in ascii_art]
            length = min(lenarray)
            if lenarray.count(length) > 1:
                secondshortest = min(lenarray)
            else:
                secondshortest = min([x for x in lenarray if x != length])
            for i in range(len(ascii_art)):
                if len(ascii_art[i]) == length:
                    # print(length)
                    ascii_art[i] = (
                        ascii_art[i]
                        + ANSICOLOUR
                        + "-"
                        + (
                            message.author.nick
                            if message.author.nick is not None
                            else message.author.display_name
                        ).replace(" ", "_")
                    )
                    length = -1
                elif len(ascii_art[i]) == secondshortest:
                    ascii_art[i] = (
                        ascii_art[i]
                        + ANSICOLOUR
                        + "-"
                        + ("Image from discord").replace(" ", "_")
                    )
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


def getstats(playeruid,isfromserver = False,istf1 = False):
    """Comprehensive player statistics calculator with kill/death ratios, rankings, and weapon usage data"""
    # print(int(time.time()))
    tfdb = postgresem("./data/tf2helper.db")
    c = tfdb
    # print(int(time.time()/))
    now = int(time.time())
    timeoffset = 86400
    try:
        output = resolveplayeruidfromdb(playeruid, None, True, istf1)
        if not output:
            return {"sob": "unknown player"}
        output = output[0]
        name = output["name"]
        playeruid = output["uid"]
        lastserverid = output["lastserverid"]
    except:
        traceback.print_exc()
        name = "unknown"
        return {"sob": "sobbing Unknown player"}
    messages = {}
    output = {"name": name, "uid": str(playeruid), "total": {}}
    c.execute(
        f"SELECT * FROM specifickilltracker{'tf1' if istf1 else ''} WHERE victim_id = ? AND (victim_type = 'player' OR victim_type IS NULL)",
        (playeruid,),
    )
    output["total"]["deaths"] = len(c.fetchall())
    c.execute(
        f"SELECT * FROM specifickilltracker{'tf1' if istf1 else ''} WHERE playeruid = ? AND (victim_type = 'player' OR victim_type IS NULL)",
        (playeruid,),
    )
    output["total"]["kills"] = len(c.fetchall())
    c.execute(
        f"SELECT * FROM specifickilltracker{'tf1' if istf1 else ''} WHERE playeruid = ? AND timeofkill > ? AND (victim_type = 'player' OR victim_type IS NULL)",
        (playeruid, now - timeoffset),
    )
    output["total"]["killstoday"] = len(c.fetchall())
    c.execute(
        f"SELECT * FROM specifickilltracker{'tf1' if istf1 else ''} WHERE victim_id = ? AND timeofkill > ? AND (victim_type = 'player' OR victim_type IS NULL)",
        (playeruid, now - timeoffset),
    )
    output["total"]["deathstoday"] = len(c.fetchall())
    c.execute(
        f"""
        WITH player_kills AS (
            SELECT playeruid, COUNT(*) AS kill_count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) AS position
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE timeofkill > ?
            AND (victim_type = 'player' OR victim_type IS NULL)
            GROUP BY playeruid
        )
        SELECT position
        FROM player_kills
        WHERE playeruid = ?
    """,
        (now - timeoffset, playeruid),
    )
    killspos = c.fetchone()
    output["total"]["killslasthourpos"] = killspos[0] if killspos else None

    c.execute(
        f"""
        WITH player_deaths AS (
            SELECT victim_id, COUNT(*) AS death_count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) AS position
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE timeofkill > ?
            AND (victim_type = 'player' OR victim_type IS NULL)
            GROUP BY victim_id
        )
        SELECT position
        FROM player_deaths
        WHERE victim_id = ?
    """,
        (now - timeoffset, playeruid),
    )
    killspos = c.fetchone()
    output["total"]["deathslasthourpos"] = killspos[0] if killspos else None

    c.execute(
        f"""
        WITH player_kills AS (
            SELECT playeruid, COUNT(*) AS kill_count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) AS position
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE (victim_type = 'player' OR victim_type IS NULL)
            GROUP BY playeruid
        )
        SELECT position
        FROM player_kills
        WHERE playeruid = ?
    """,
        (playeruid,),
    )
    killspos = c.fetchone()
    output["total"]["killspos"] = killspos[0] if killspos else None

    c.execute(
        f"""
        WITH recent_weapon AS (
            SELECT cause_of_death
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE playeruid = ?
            AND (victim_type = 'player' OR victim_type IS NULL)
            ORDER BY timeofkill DESC
            LIMIT 1
        ),
        weapon_kills AS (
            SELECT playeruid, COUNT(*) AS kill_count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) AS position
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE cause_of_death = (SELECT cause_of_death FROM recent_weapon)
            AND (victim_type = 'player' OR victim_type IS NULL)
            GROUP BY playeruid
        )
        SELECT position
        FROM weapon_kills
        WHERE playeruid = ?
    """,
        (playeruid, playeruid),
    )
    killspos = c.fetchone()
    output["total"]["recentweaponkillspos"] = killspos[0] if killspos else None

    c.execute(
        f"""
        WITH player_deaths AS (
            SELECT victim_id, COUNT(*) AS death_count,
                   RANK() OVER (ORDER BY COUNT(*) DESC) AS position
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE (victim_type = 'player' OR victim_type IS NULL)
            GROUP BY victim_id
        )
        SELECT position
        FROM player_deaths
        WHERE victim_id = ?
    """,
        (playeruid,),
    )
    killspos = c.fetchone()
    output["total"]["deathspos"] = killspos[0] if killspos else None

    c.execute(
        f"""
        SELECT cause_of_death, COUNT(*) as kill_count
        FROM specifickilltracker{'tf1' if istf1 else ''}
        WHERE playeruid = ?
        AND (victim_type = 'player' OR victim_type IS NULL)
        GROUP BY cause_of_death
        ORDER BY kill_count DESC
        LIMIT 3
    """,
        (playeruid,),
    )
    top_weapons = c.fetchall()
    c.execute(
        f"""
        SELECT matchid, SUM(pilotkills) AS total_pilotkills
        FROM playtime{'tf1' if istf1 else ''}
        WHERE playeruid = ?
        GROUP BY matchid
        ORDER BY total_pilotkills DESC
        LIMIT 1
    """,
        (playeruid,),
    )

    c.execute(
        f"""
        SELECT matchid, map, MIN(joinatunix) as start_time, SUM(pilotkills) as total_pilotkills
        FROM playtime{'tf1' if istf1 else ''}
        WHERE playeruid = ?
        GROUP BY matchid, map
        ORDER BY total_pilotkills DESC
        LIMIT 1
    """,
        (playeruid,),
    )
    bestgame = c.fetchone()
    c.execute(
        f"""
        SELECT 
            COALESCE(SUM(duration), 0) AS total_time_playing,
            COALESCE(SUM(pilotkills), 0) AS total_pilot_kills
        FROM playtime{'tf1' if istf1 else ''}
        WHERE playeruid = ?
    """,
        (playeruid,),
    )
    kph = c.fetchone()
    timeplayed = "unknown"
    if not kph or not kph[0]:
        killsperhour = 0
    else:
        killsperhour = int((kph[1] / (kph[0] / 3600)) * 100) / 100
        timeplayed = modifyvalue(kph[0], "time")
    currentgun = False
    # if request.method == "POST" and "current_weapon" in request.get_json():
    #     print("ASDASDASDASDASSDAS",request.get_json()["current_weapon"])
    #     c.execute("SELECT COUNT(*) as kill_count FROM specifickilltracker WHERE playeruid = ? AND cause_of_death = ?",(playeruid,request.get_json()["current_weapon"]))
    #     currentgun = c.fetchone()
    #     if not currentgun:
    #         currentgun = False
    #     else:
    # print("HEREEE")
    # top_weapons.append( (request.get_json()["current_weapon"],currentgun[0]))
    # print(currentgun)
    # output["total"]["top_weapons"] = top_weapons
    c.execute("""
    SELECT
        SUM(CASE
                WHEN matchid != ? AND
                    ((initiator=? AND initiatorscore>receiverscore) OR
                    (receiver=?   AND receiverscore>initiatorscore))
                THEN 1 ELSE 0
            END) AS wins,
        SUM(CASE
                WHEN matchid != ? AND
                    ((initiator=? AND initiatorscore<receiverscore) OR
                    (receiver=?   AND receiverscore<initiatorscore))
                THEN 1 ELSE 0
            END) AS losses,
        SUM(CASE
                WHEN matchid != ? AND
                    (initiator=? OR receiver=?) AND
                    initiatorscore=receiverscore
                THEN 1 ELSE 0
            END) AS draws,
        SUM(CASE
                WHEN (initiator=? OR receiver=?)
                THEN 1 ELSE 0
            END) AS duels
    FROM duels
    """, (str(isfromserver or mostrecentmatchids.get(lastserverid) or True),playeruid, playeruid,str(isfromserver or mostrecentmatchids.get(lastserverid) or True),playeruid, playeruid,str(isfromserver or mostrecentmatchids.get(lastserverid) or True),playeruid, playeruid,playeruid,playeruid))
    # print(isfromserver or mostrecentmatchids.get(lastserverid))
    duelstats = (c.fetchone() or [0,0,0,0] )
    duelstats = {"win":duelstats[0],"defeat":duelstats[1],"draw":duelstats[2],"total duel":duelstats[3]}
    output["duelstats"] = duelstats
    c.execute(
        f"""
        SELECT cause_of_death, COUNT(*) as kill_count
        FROM specifickilltracker{'tf1' if istf1 else ''}
        WHERE playeruid = ?
        AND (victim_type = 'player' OR victim_type IS NULL)
        AND cause_of_death = (
            SELECT cause_of_death
            FROM specifickilltracker{'tf1' if istf1 else ''}
            WHERE playeruid = ?
            AND (victim_type = 'player' OR victim_type IS NULL)
            ORDER BY timeofkill DESC
            LIMIT 1
        )
        GROUP BY cause_of_death
    """,
        (playeruid, playeruid),
    )
    output["total"]["recent_weapon_kills"] = c.fetchone()

    if output["total"]["deaths"] != 0:
        kd = output["total"]["kills"] / output["total"]["deaths"]
    else:
        kd = 1
    kd = int(kd * 100) / 100
    # print("getting killdata for",name,playeruid,output)
    while True:
        colour = random.randint(0, 255)
        # colour = random.choice([254,219,87])
        # dissallowedcolours colours (unreadable)  (too dark)
        if colour not in DISALLOWED_COLOURS:
            break
    offset = 1
    backslash = ""
    messages["0"] = (
        f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} has {PREFIXES['stat']}{output['total']['kills']}{' ' + PREFIXES['stat2'] + '#' + str(output['total']['killspos']) if output['total']['killspos'] else ''} {PREFIXES['chatcolour']}kills and {PREFIXES['stat']}{output['total']['deaths']}{' ' + PREFIXES['stat2'] + '#' + str(output['total']['deathspos']) if output['total']['deathspos'] else ''} {PREFIXES['chatcolour']}deaths ({PREFIXES['stat']}{kd}{PREFIXES['chatcolour']} k/d, {PREFIXES['stat']}{killsperhour}{PREFIXES['chatcolour']} k/hour, {PREFIXES['stat']}{timeplayed}{PREFIXES['chatcolour']} playtime)"
    )
    # print("e",bestgame)
    if bestgame:
        formatted_date = datetime.fromtimestamp(bestgame[2]).strftime(
            f"%-d{'th' if 11 <= datetime.fromtimestamp(bestgame[2]).day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(datetime.fromtimestamp(bestgame[2]).day % 10, 'th')} of %B %Y"
        )

        offset += 1
        messages["1"] = (
            f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} had their best game on {PREFIXES['stat']}{MAP_NAME_TABLE.get(bestgame[1], bestgame[1])}{PREFIXES['chatcolour']} with {PREFIXES['stat']}{bestgame[3]}{PREFIXES['chatcolour']} kills on {PREFIXES['stat']}{formatted_date}"
        )
    colourcodes = [PREFIXES["gold"], PREFIXES["silver"], PREFIXES["bronze"]]
    topguns = []
    for enum, weapon in enumerate(top_weapons):
        if not weapon:
            continue
        # messages[str(offset)] = f"[38;5;{colour}m{enum+1}) {colourcodes[enum]}{WEAPON_NAMES.get(weapon[0],weapon[0])}{PREFIXES['chatcolour']} kills: {PREFIXES['stat']}{weapon[1]}"
        # offset +=1
        topguns.append(
            f"{colourcodes[enum]}{WEAPON_NAMES.get(weapon[0], weapon[0])}: {PREFIXES['stat']}{weapon[1]}{PREFIXES['chatcolour']} kills"
        )

    if topguns:
        messages[str(offset)] = f"[38;5;{colour}mTop 3 guns: " + ", ".join(topguns)
        offset += 1
    # [38;5;244m
    if output["total"]["recent_weapon_kills"]:
        messages[str(offset)] = (
            f"[38;5;{colour}mMost recent weapon: {PREFIXES['stat']}{WEAPON_NAMES.get(output['total']['recent_weapon_kills'][0], output['total']['recent_weapon_kills'][0])}: {PREFIXES['stat']}{output['total']['recent_weapon_kills'][1]}{' ' + PREFIXES['stat2'] + '#' + str(output['total']['recentweaponkillspos']) if output['total']['recentweaponkillspos'] else ''} {PREFIXES['chatcolour']}kills"
        )
        offset += 1
    messages[str(offset)] = (
        f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} has {PREFIXES['stat']}{output['total']['killstoday']}{' ' + PREFIXES['stat2'] + '#' + str(output['total']['killslasthourpos']) if output['total']['killslasthourpos'] else ''}{PREFIXES['chatcolour']} kill{'s' if output['total']['killstoday'] != 1 else ''} today and {PREFIXES['stat']}{output['total']['deathstoday']}{' ' + PREFIXES['stat2'] + '#' + str(output['total']['deathslasthourpos']) if output['total']['deathslasthourpos'] else ''} {PREFIXES['chatcolour']}death{'s' if output['total']['deathstoday'] != 1 else ''} today"
    )
    offset += 1
    if output["duelstats"]["total duel"]:
        messages[str(offset)] = (
            f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} duel stats are: {", ".join(list(map(lambda x: f"{PREFIXES['stat']}{x[1]}{PREFIXES["chatcolour"]} {x[0]}{"s" if x[1] -1 else ""}", output["duelstats"].items())))} "
        )
        offset += 1
    else:
        messages[str(offset)] = (
            f"[38;5;{colour}m{name}{PREFIXES['chatcolour']} has no duels, use {PREFIXES["commandname"]}!duel <name>{PREFIXES["chatcolour"]} to duel a player!"
        )
        offset += 1


    # if len(messages):
    # output["messages"] = messages
    print("stats: name", name, "colour", colour)
    # print("EEEEEEEEEE")
    return {**output, **messages}


def fitimage(image_bytes, output_width=30, ascii_char="█", maxlen=249):
    """Converts image to ASCII art with width constraints and character limits"""
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


def lotsofmathscreatingimage(
    image_bytes, output_width=80, ascii_char="█", max_height=11
):
    """Complex image to ASCII conversion with mathematical scaling and height limits"""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_width, original_height = image.size
    computed_height = int((original_height / original_width) * output_width)
    if computed_height > max_height:
        output_height = max_height
        output_width = int((original_width / original_height) * max_height)
    else:
        output_height = computed_height
    output_width *= 1.8
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
                colored_char = f"[38;5;{ansi}m{ascii_char}"
                lastansi = ansi
            else:
                colored_char = ascii_char
            row_chars += colored_char
            idx += 1
        ascii_art.append(row_chars)
    return ascii_art


logging.basicConfig(
    filename="./data/errors.txt",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """Global exception handler that logs uncaught exceptions to file with stack traces"""
    # if issubclass(exc_type, KeyboardInterrupt):
    #     sys.__excepthook__(exc_type, exc_value, exc_traceback)
    #     return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = log_uncaught_exceptions

# REGISTEREDTFTODISCORDCOMMANDS = { #shouldblock is not implemented, it likely never will be nevermind that is false
#     "stats": {
#         "games": ["tf1", "tf2"],
#         "function": calcstats,
#         "run": "thread",
#         "description": "display your stats. do !stats lexi for a specific player",
#         "shouldblock":False,
#         "rcon":False
#     },
#     "togglestats": {
#         "games": ["tf1", "tf2"],
#         "function": togglestats,
#         "run": "thread",
#         "description": "toggle auto showing of stats on map change / join",
#         "shouldblock":True,
#         "rcon":False
#     },
#     "helpdc": {
#         "games": ["tf1", "tf2"],
#         "function": ingamehelp,
#         "run": "thread",
#         "description": "Get help on commands that exec on the discord bot",
#         "shouldblock":False,
#         "rcon":False
#     },
#     "getdiscordcommands": {
#         "games": [],
#         "function": senddiscordcommands,
#         "run": "thread",
#         "description": "Internal function for pulling shouldblock values",
#         "shouldblock":True,
#         "rcon":False
#     },
#     "throw":{
#         "games": ["tf2"],
#         "function": throwplayer,
#         "run": "thread",
#         "description": "Throw somone, you meanie",
#         "shouldblock":True,
#         "rcon":True
#     }
# impersonate :O
# "bettertb": {
#     "games": ["tf2"],
#     "function": bettertb,
#     "run": "thread",
#     "description": "betterteambal",
#     "shouldblock":False
# },
# "stoprequests": {
#     "games": [],
#     "function": stoprequests,
#     "run": "thread",
#     "description": "stop requests for a server",
#     "shouldblock":False
# },
# "onplayerkilled": {
#     "games": [],
#     "function": stoprequests,
#     "run": "thread",
#     "description": "stop requests for a server",
#     "shouldblock":False
# }

# }


# def tf1inputemulator():
#     while True:
#         content = input("ENTER MESSAGE: ")
#         messageflush.append({
#         "timestamp": int(time.time()),
#         "serverid": "304",
#         "type": 3,
#         "player":"fake lexi sending fake commands",
#         "globalmessage": True,
#         "overridechannel": "commandlogchannel",
#         "messagecontent": content,
#         "metadata": {"type":"tf1command"},
#         "servername" :context["serveridnamelinks"]["304"]
#         })


# def ensure_id_autoincrement_for_all_tables(db: postgresem):
#     # Get all tables with an 'id' column of integer type
#     db.execute("""
#         SELECT table_name
#         FROM information_schema.columns
#         WHERE column_name = 'id'
#           AND data_type IN ('integer', 'bigint')
#           AND table_schema = 'public';
#     """)
#     tables = [row[0] for row in db.fetchall()]

#     for table in tables:
#         print(f"Checking table '{table}'...")
#         db.execute(f"""
#             SELECT column_default
#             FROM information_schema.columns
#             WHERE table_name = %s
#               AND column_name = 'id';
#         """, (table,))
#         default = db.fetchone()

#         if default and default[0] and 'nextval' in default[0]:
#             print(f"  Table '{table}': id column is already auto-incrementing.")
#             continue

#         print(f"  Setting up auto-increment for '{table}.id'...")

#         seq_name = f"{table}_id_seq"

#         # Create sequence if not exists
#         try:
#             db.execute(f"""
#                 DO $$
#                 BEGIN
#                     IF NOT EXISTS (
#                         SELECT 1 FROM pg_class
#                         WHERE relkind = 'S' AND relname = '{seq_name}'
#                     ) THEN
#                         CREATE SEQUENCE {seq_name};
#                     END IF;
#                 END
#                 $$;
#             """)
#             # No fetch here!

#             # Alter the id column to use the sequence as default
#             db.execute(f"""
#                 ALTER TABLE {table}
#                 ALTER COLUMN id SET DEFAULT nextval('{seq_name}');
#             """)
#             # No fetch here!

#             # Set sequence value to max existing id to avoid conflicts
#             db.execute(f"""
#                 SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table}), 0));
#             """)
#             # This is a SELECT, fetch one to complete transaction
#             db.fetchone()

#             db.commit()
#         except:
#             db.commit()
#             print("failed")
#         print(f"  Auto-increment setup complete for '{table}'.")

# ensure_id_autoincrement_for_all_tables(db)
# db.execute(f"INSERT INTO matchid{'tf1' if True else ''} (matchid,serverid,map,time) VALUES (?,?,?,?)",("wqdq","123","thaw",int(time.time())))
# db.execute("""
# SELECT column_default
# FROM information_schema.columns
# WHERE table_name = 'messagelogger' AND column_name = 'id';""")
# print(db.fetchall())


if DISCORDBOTLOGSTATS == "1":
    threading.Thread(target=threadwrap, daemon=True, args=(playerpoll,)).start()
threading.Thread(target=threadwrap, daemon=True, args=(messageloop,)).start()
threading.Thread(
    target=threadwrap, daemon=True, args=(recieveflaskprintrequests,)
).start()
threading.Thread(target=threadwrap, daemon=True, args=(tf1relay,)).start()
# threading.Thread(target=threadwrap(tf1inputemulator).start()
for serverid in context["servers"]:
    tfcommandspermissions.setdefault(serverid,{})["laststatspull"] = int(time.time())
    sendrconcommand(
        serverid,
        f"!reloadtfcommandlist",
        sender=None,
    )

def shutdown_handler(sig, frame):
    """Handles graceful shutdown signals and cleanup operations"""
    asyncio.get_event_loop().create_task(bot.close())


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)
bot.run(TOKEN)
