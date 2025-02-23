global function discordloggetuid

discordlogcommand function discordloggetuid(discordlogcommand commandin) {
    if (discordlogcheck("getuid", commandin)){
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
        commandin.returnmessage = "UID for " + players[0].GetPlayerName() + " is " + players[0].GetUID()
        commandin.returncode = 200
    }
    
    return commandin;
}