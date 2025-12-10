global function discordlogsendsoundtoplayer

discordlogcommand function discordlogsendsoundtoplayer(discordlogcommand commandin) {
    if (commandin.commandargs.len() != 2 && commandin.commandargs.len() != 3)
    {
        commandin.returnmessage = "Wrong number of args";
        commandin.returncode = 400
        return commandin;
    }
    array<entity> players = discordlogmatchplayers(commandin.commandargs[0])
    if (players.len() == 0 && commandin.commandargs[0] != "all"){
        commandin.returnmessage = "No players found"
        commandin.returncode = 401
    }
    else if (players.len() > 1 && commandin.commandargs[0] != "all"){
        commandin.returnmessage = "Multiple players found"
        commandin.returncode = 402
    }
    else {
        if (commandin.commandargs[0] == "all"){
            players = GetPlayerArray()
            commandin.returnmessage = "Playing "+ commandin.commandargs[1]+ " to " + players.len() + " players"  
        }else{
            commandin.returnmessage = "Playing "+ commandin.commandargs[1]+ " to " + players[0].GetPlayerName()       
        }
        
        // EmitSoundOnEntityOnlyToPlayer(players[0],players[0],split(commandin.commandargs[1],"|")[1])
        int times = 1
        if  (commandin.commandargs.len() == 3){
            times = commandin.commandargs[2].tointeger()
        }
        string thing = commandin.commandargs[1]
        if (split(commandin.commandargs[1],"|").len() == 2){
            thing = split(commandin.commandargs[1],"|")[1]
        }
        foreach (player in players){
        thread threadedspam(player,thing,times)}
        commandin.returncode = 200
    }
    return commandin;
}

void function threadedspam(entity player, string sound, int times){
    for (int i = 0; i < times; i++){
        if (!IsValid(player)){
            return
        }
        float handle = EmitSoundOnEntityOnlyToPlayer(player,player,sound)
        wait handle
    }

}