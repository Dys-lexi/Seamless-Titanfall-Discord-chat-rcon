# Seamless Titanfall <-> Discord chat relay, rcon and custom commands
A mod / discord bot that relays titanfall messages to discord, discord messages to titanfall, and allows rcon to send console commands to titanfall, or custom commands that you can create! (a few come already with the mod)

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

*The servername paramater of commands is only updated on bot restart. either restart bot, or just use the commands in the designated channel for a titanfall server*

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
    "outputfunc": "sanctionoverride"

}
```
All options but are optional, meaning a command can just look like this:

```
"playing": {

}
``` 
This will just run the "playing" command on the server, passing no paramaters, will be available to all uses, with no special formatting of the output, or command description