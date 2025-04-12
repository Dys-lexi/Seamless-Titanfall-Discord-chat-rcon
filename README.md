# Seamless Titanfall <-> Discord chat relay, rcon and custom commands

A mod / discord bot that relays titanfall messages to discord, discord messages to titanfall, and allows rcon to send console commands to titanfall, or custom commands that you can create - (a few come already with the mod)

(also optionally supports sending ascii images to titanfall, and a ai version of /throw that requires perswading an ai to use)

you'll have to create a discord bot at discord developers to use this, and put token in

## Docker

### A docker compose could look like this

```
discordlog:
    << : *logging
    build: ./discord
    container_name: discordlog
    environment:
      - DISCORD_BOT_TOKEN=PUT YOUR DISCORD TOKEN HERE
      - DISCORD_BOT_PASSWORD=scarypassword
      - SHOULDUSEIMAGES=0 #allow discord images to be turned into text and relayed
      - DISCORD_BOT_USE_THROWAI=0 #allow the use of the non rcon throw command, (requires ollama + ai model installed)
      - DISCORD_BOT_LOCALHOST_PATH=host.docker.internal #right now used only for throwai. don't worry about it if not using
      - DISCORD_BOT_AI_USED=deepseek-r1 #llm to use (default is deepseek-r1)
      - DISCORD_BOT_LOG_STATS=1 # log player's time played, and some basic stats
      - DISCORD_BOT_LEADERBOARD_UPDATERATE # how often leaderboards update
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

- Check the mod.json file for configuration on other things.

## Discord bot

### In-discord Setup

- Use ```/bindloggingtocategory``` to make a category in a discord server, where the titanfall servers will log too
- Use ```/rconchangeuserallowed``` to add a user (probably yourself) to rcon list
- Use ```/blindglobalchannel``` if you intend to use the globalchannel message stuff. (titanfall servers can optionally choose to send a message to it, for example bans can be sent here)
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
name OPTIONAL - name of leaderboard, appears at top of embed
description OPTIONAL - appears below name
color OPTIONAL - hex colour in decimal, color of embed
database REQUIRED - database to use (check tf2helper.db)
orderby REQUIRED - What the data should be ordered by. can either be a column name in the sql table (eg pilotkills or duration) or a name of a category eg ("Kills Per Hour" or "Total kills")
categorys REQUIRED - "CategoryName REQUIRED" : {"columnsbound": ["Sql Column1","Sql Column2"], "format OPTIONAL":"How data should be formatted (only "time", "XperY", "XperY*3600" exist atm)","calculation OPTIONAL":"Sql column1 OPERATOR Sql Column2}
without a calcuation defined, only one column can be used. with one, any amount of columns can be used
filters OPTIONAL - WHERE Sql Column IN values, and amount can be used
merge REQUIRED - What Sql Column defines witch rows are grouped. eg "Uid" would group all rows with the same uid, adding all stats together. "map" would group everything on the same map together. only integer columns are added right now, string columns take the first instance. also controls the name of each category
maxshown OPTIONAL - how many spots to display in leaderboard
id OPTIONAL - set this to 0. is managed by the bot (is the messageid, so it knows what message to edit) not including defaults it to 0