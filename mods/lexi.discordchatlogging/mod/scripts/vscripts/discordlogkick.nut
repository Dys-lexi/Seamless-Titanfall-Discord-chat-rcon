global function discordlogkickplayer

discordlogcommand function discordlogkickplayer(discordlogcommand commandin) {
    if (discordlogcheck("kick", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
    if (commandin.commandargs.len() != 1)
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
        NSDisconnectPlayer(players[0],"You were kicked :( swwy")
        commandin.returncode = 200
    }
    return commandin;
}
