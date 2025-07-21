global function discordloghostiletitanfall

discordlogcommand function discordloghostiletitanfall(discordlogcommand commandin) {
    if (discordlogcheck("hostiletf", commandin)){
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
        return commandin
    }
    string playersranon = ""
    int notatitan = 0
    foreach (player in players){
        if ( !(player.IsTitan()) ){
            notatitan +=1
            continue
        }
        playersranon += player.GetPlayerName() + ", "
        Remote_CallFunction_NonReplay( player, "ServerCallback_TitanFallWarning", true )


    }
    if (playersranon == ""){
        commandin.returnmessage = "Everyone was a pilot ("  + notatitan + "/" + players.len() + ")"
        commandin.returncode = 402
        return commandin
    }
    
    playersranon = playersranon.slice(0,playersranon.len()-2)
    commandin.returnmessage = "Ran hostiletf on "+ playersranon + " (" + (players.len()-notatitan) + "/" + players.len() + ")" 
    commandin.returncode = 200
    
    
    return commandin;
}