global function discordlogsendsoundtoplayer

discordlogcommand function discordlogsendsoundtoplayer(discordlogcommand commandin) {
    if (commandin.commandargs.len() != 2 && commandin.commandargs.len() != 3)
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
        commandin.returnmessage = "Playing "+ commandin.commandargs[1]+ "to" + players[0].GetPlayerName()
        // EmitSoundOnEntityOnlyToPlayer(players[0],players[0],split(commandin.commandargs[1],"|")[1])
        int times = 1
        if  (commandin.commandargs.len() == 3){
            times = commandin.commandargs[2].tointeger()
        }
        thread threadedspam(players[0],split(commandin.commandargs[1],"|")[1],times)
        commandin.returncode = 200
    }
    return commandin;
}

void function threadedspam(entity player, string sound, int times){
    for (int i = 0; i < times; i++){
        float handle = EmitSoundOnEntityOnlyToPlayer(player,player,sound)
        wait handle
    }

}