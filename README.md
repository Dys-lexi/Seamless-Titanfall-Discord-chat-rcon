# Seamless Titanfall <-> Discord chat relay, rcon, custom commands and leaderboards

## Supports both Northstar and R1delta

Message @dyslexi on discord for how to use this, as you'll probably need to be shown the ropes

The mod (not bot (that is for both)) here is only for titanfall 2 (the titanfall one version is [here](https://github.com/Dys-lexi/R1deltachatcommands))

A mod / discord bot that relays titanfall messages to discord, discord messages to titanfall, allows rcon to send console commands to titanfall, custom commands that you can create - (a few come already with the mod) and leaderboards

(also optionally supports sending ascii images to titanfall, and a ai version of /throw that requires perswading an ai to use)

you'll have to create a discord bot at discord developers to use this, and put token into DISCORD_BOT_TOKEN

## Docker

### A docker compose could look like this - the values here are the default values

```
discordlog:
    << : *logging
    build: ./discord
    container_name: discordlog
    environment:
      - DISCORD_BOT_TOKEN=PUT YOUR DISCORD TOKEN HERE
      - DISCORD_BOT_PASSWORD=scarypassword #only really used if you port forward the bot, elsewise don't worry about it, and keep as default (must be the same as in the mod.json)
      - SHOULDUSEIMAGES=0 #allow discord images to be turned into text and relayed
      - DISCORD_BOT_USE_THROWAI=0 #allow the use of the non rcon throw command, (requires ollama + ai model installed)
      - DISCORD_BOT_LOCALHOST_PATH=host.docker.internal #right now used only for throwai. don't worry about it if not using
      - DISCORD_BOT_AI_USED=deepseek-r1 #llm to use (default is deepseek-r1)
      - DISCORD_BOT_LOG_STATS=1 # log player's time played, and some basic stats
      - DISCORD_BOT_LEADERBOARD_UPDATERATE=300 # how often leaderboards update
      - DISCORD_BOT_LOG_COMMANDS=1 #log command usage. needs bindchannel for commands to be set. (commands are messages beginning with ! or /)
      - DISCORD_BOT_SERVERNAME_IS_CHOICE=0 #determines when specifiying a servername in a command if it's a choice, or an entered string.
      - TF1_RCON_PASSWORD="" #RCON Password for tf1 chat relay. when blank, completly disables relay
      - USE_DYNAMIC_PFPS="1" #FANCY new way of chat bridging.
      - PFP_ROUTE="https://raw.githubusercontent.com/Dys-lexi/TitanPilotprofiles/main/avatars/" #Url used for pfps
      - FILTER_NAMES_IN_MESSAGES="usermessagepfp,chat_message,command,tf1command,botcommand" #What types of messages should the bot run the nonoword filter on
      - SEND_KILL_FEED="1" #should the bot send the kill feed in the relay?
      - OVERRIDE_IP_FOR_CDN_LEADERBOARD="use_actual_ip" #options = useactualip,if you have no domain, a domain name eg https://xyz.com or hidden to disable this. you'll need to port forward.
      - COOL_PERKS_REQUIREMENT="You need something or other to get this"#message displayed when user does not have the role required for cool perks.
      - SHOW_IMPERSONATED_MESSAGES_IN_DISCORD="1" # display an IMPERSONATED tag after an impersonated message, only in discord
      - KILL_STREAK_NOTIFY_THRESHOLD="5" #min kill requirment to start a killstreak. set to "0" to disable.
      - KILL_STREAK_NOTIFY_STEP="5" #how many kills needed for the next ks notification
    volumes:
      - ./discord/data:/app/data:rw
    restart: always
    extra_hosts: #you may need this argument to send requests to ollama for throwai.
      - "host.docker.internal:host-gateway"
```

### Convars

For each server you'll _need_:

```
+discordloggingserverid 1234
```

this should be unique.

And you'll most likely _want_:

```
+discordloggingservername Channel_Name_In_Discord
-allowlocalhttp
```

- Check the mod.json file for configuration on other things, like url of discord bot

## Discord bot

### In-discord Setup

- Use ```/bindloggingtocategory``` to make a category in a discord server, where the titanfall servers will log too
- Use ```/bindrole``` to set a role as the admin role (and coolperksrole)
- Use ```/bindchannel``` if you intend to use leaderboards, globalchannel, and commandlogging. these go in seperate channels.
- Use ```/help``` to see commands


### Custom Commands

To add your own custom commands, the top of logger.nut provides some help.
without a dedicated / command, to call them you can do /rcon cmd:!yourcommand yourcommandparam1 yourcommandparam2...

to make a /command on discord, edit the commands.json file.

A more complex example is:

```
"sanctionban": {
    "description": "Sanction a player",
    "parameters": [
        {
            "name": "playername",
            "type": "str",
            "description": "The player name",
            "required": true
        },
        {
            "name": "reason",
            "type": "str",
            "description": "The reason for the sanction",
            "required": true
        },
        {
            "name": "sanctiontype",
            "type": "str",
            "description": "The type of sanction to apply",
            "required": true,
            "choices": [
                "mute",
                "ban"
            ]
        },
        {
            "name": "expiry",
            "type": "str",
            "description": "The expiry time of the sanction in format yyyy-mm-dd, omit is forever",
            "required": false
        }
    ],
    "rcon": true,
    "commandparaminputoverride": {
        "reason" : "-reason",
        "sanctiontype" : "-type",
        "expiry" : "-expire",
        "appendtoend": "'-issuer '+ctx.author.name"
    },
    "outputfunc": "sanctionoverride",
    "regularconsolecommand": false

}
```

All options are fully optional, meaning a command can just look like this:

```
"playing": {

}
```

This will just run the "playing" command on the server, passing no paramaters, will be available to all uses, with no special formatting of the output, or command description. (regularconsolecommand makes it run like a normal console command, like "quit" closing the game)

### Custom Leaderboards

- Make sure DISCORD_BOT_LOG_STATS is set to "1" (default)

- use /bindleaderboardchannel to bind an existing channel to have the leaderboards sent in

leaderboards are defined in channels.json under leaderboardchannelmessages

A more complex example is:

```
{
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
            "format": "scoreperhour",
            "calculation": "scoregained / duration"
        }
    },
    "filters": {
        "serverid": [
            21,
            20,
            26
        ]
    },
    "merge": "name",
    "maxshown": 10,
    "id": 0
}
```

A simpler example could be:

```
{
    "name": "Pilot kills",
    "description": "Top 10 players with most pilot kills",
    "database": "playtime",
    "orderby": "pilotkills",
    "categorys": {
        "Total kills": {
            "columnsbound": [
                "pilotkills"
            ]
        }
    },
    "merge": "name",
}
```
- name OPTIONAL - name of leaderboard, appears at top of embed
- description OPTIONAL - appears below name
- color OPTIONAL - hex colour in decimal, color of embed
- database REQUIRED - database to use (check tf2helper.db)
- orderby REQUIRED - What the data should be ordered by. can either be a column name in the sql table (eg pilotkills or duration) or a name of a category eg ("Kills Per Hour" or "Total kills")
- categorys REQUIRED - "CategoryName REQUIRED" : {"columnsbound": ["Sql Column1","Sql Column2"], "format OPTIONAL":"How data should be formatted (only "time", "XperY", "XperY*3600" exist atm)","calculation OPTIONAL":"Sql column1 OPERATOR Sql Column2} without a calcuation defined, only one column can be used. with one, any amount of columns can be used
- filters OPTIONAL - WHERE Sql Column IN values, any amount can be used, if is a string can also be just a sql statement eg:
```"filters": "f'cause_of_death = \"mp_weapon_frag_grenade\" AND timeofkill > {int((datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).weekday())).timestamp())}'",
```
- merge REQUIRED - What Sql Column defines witch rows are grouped. eg "Uid" would group all rows with the same uid, adding all stats together. "map" would group everything on the same map together. only integer columns are added right now, string columns take the first instance. also controls the name of each category
- maxshown OPTIONAL - how many spots to display in leaderboard
- id OPTIONAL - set this to 0. is managed by the bot (is the messageid, so it knows what message to edit) not including defaults it to 0

### induvidual kill tracking
you'll need this mod on the server:
https://github.com/Dys-lexi/nutone-server

(it's nutone but ever so slightly changed (pretty well changed now))

set the url to the discordbot in the mod.json, make sure log stats is on (a env var for bot), and done! (it's probably not that simple idk)