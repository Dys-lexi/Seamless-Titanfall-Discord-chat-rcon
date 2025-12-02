global function discordlogkickplayer_init
global function discordlogkickplayer

void function discordlogkickplayer_init()
{
	AddDiscordRconCommand( discordlogkickplayer )
}

discordlogcommand function discordlogkickplayer(discordlogcommand commandin) {
    if (discordlogcheck("kick", true, commandin)){
            return commandin;
    }
    commandin.commandmatch = true
    if (commandin.commandargs.len() < 1)
    {
        commandin.returnmessage = "Wrong number of args";
        commandin.returncode = 400
        return commandin;
    }
    array<entity> players = discordlogmatchplayers(commandin.commandargs[0])
    if (players.len() == 0){
        commandin.returnmessage = "No players found"
        commandin.returncode = 401
    }
    else if (players.len() > 1){
        commandin.returnmessage = "Multiple players found"
        commandin.returncode = 402
    }
    else {
        commandin.returnmessage = "Kicking " + players[0].GetPlayerName()
        string reason = "You were kicked :( swwy"
        if (commandin.commandargs.len() > 1){
            reason = ""
            for (int i = 1; i < commandin.commandargs.len(); i++){
                reason += commandin.commandargs[i] + " "
            }
            
        }
        NSDisconnectPlayer(players[0], reason)
        commandin.returncode = 200
    }
    return commandin;
}
