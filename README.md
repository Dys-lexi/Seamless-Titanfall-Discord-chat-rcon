# Seamless Titanfall <-> Discord chat relay, rcon and custom commands
A mod / discord bot that relays titanfall messages to discord, discord messages to titanfall, and allows rcon to send console commands to titanfall

you'll have to create a discord bot at discord developers to use this, and put token in

### A docker compose could look like this
```
discordlog:
    << : *logging
    build: ./discord
    container_name: discordlog
    environment:
      - DISCORD_BOT_TOKEN= PUT YOUR DISCORD TOKEN HERE
      - DISCORD_BOT_PASSWORD=scarypassword
      - SHOULDUSEIMAGES=1
    volumes:
      - ./discord/data:/app/data:rw
    restart: always
```
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

To add your own custom commands, the top of logger.nut provides some help.
without a dedicated / command, to call them you can do /rcon cmd:!yourcommand yourcommandparam1 yourcommandparam2...

to make a command on discord, edit the commands.json file.

an example is:

```
    "ban": {
        "description": "bans a player",
        "parameters": [
            {
                "name": "playername",
                "type": "str",
                "description": "The player name",
                "required": true
            },
            {
                "name": "duration",
                "type": "str",
                "description": "duration of ban",
                "required": true,
                "choices": ["permanent", "two weeks"]
            },
            {
                "name": "reason",
                "type": "str",
                "description": "The reason for the kick",
                "required": false
            }
        ],
        "rcon": true,
        "outputfunc": false
    }
```

