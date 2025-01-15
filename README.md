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
    volumes:
      - ./discord/data:/app/data:rw
    restart: always
```
