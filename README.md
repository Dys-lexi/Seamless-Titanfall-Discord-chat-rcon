# Seamless Titanfall <-> Discord chat relay, rcon and custom commands
A mod / discord bot that relays titanfall messages to discord, discord messages to titanfall, and allows rcon to send console commands to titanfall, or custom commands that you can create - (a few come already with the mod)

(also optionally supports sending ascii images to titanfall, and a ai version of /throw that requires perswading an ai to use)

you'll have to create a discord bot at discord developers to use this, and put token in

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
For each server you'll *need*:
```
+discordloggingserverid 1234
```
this should be unique.

And you'll most likely *want*:
```
+discordloggingservername Channel_Name_In_Discord
-allowlocalhttp
```
    


Check the mod.json file for configuration on other things.

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