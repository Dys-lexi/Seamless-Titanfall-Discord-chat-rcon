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

to make a /command on discord, edit the commands.json file.

an more complex example is:

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
    "outputfunc": "sanctionoverride"

}
```
all options but "description" are optional, meaning a command can just look like this:

```
"playing": {
    "description": "List players on a server"
}
``` 