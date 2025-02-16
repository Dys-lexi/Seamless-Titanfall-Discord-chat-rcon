# Seamless Titanfall <-> Discord chat relay and rcon
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
