global function discordlogtoggleadmin

discordlogcommand function discordlogtoggleadmin(discordlogcommand commandin) {
    if (discordlogcheck("toggleadmin", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
    if (commandin.commandargs.len() != 1 && commandin.commandargs.len() != 2)
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

        if (commandin.commandargs.len() == 1){
            print("resizing")
            commandin.commandargs.resize(2,"1")
        }
        print("commandin.commandargs[1]: " + commandin.commandargs[1])
        bool foundadmin = false
        for (int i = 1; i < 4; i++){


        string uids = GetConVarString("admin_lvl" + i)
        print("uids: " + uids)
        if (uids.find(players[0].GetUID()) != null){
            print("meow" + uids.find(players[0].GetUID()))
            uids = StringReplace(uids, players[0].GetUID() , "")
            SetConVarString("admin_lvl" + i, uids)
            commandin.returnmessage = "Removed " + players[0].GetPlayerName() + " from admin lvl " + i
            commandin.returncode = 201
            foundadmin = true
        }}
        if (!foundadmin){
            string uids = GetConVarString("admin_lvl" + commandin.commandargs[1])
            uids += players[0].GetUID() + ","
            SetConVarString("admin_lvl" + commandin.commandargs[1], uids)
            commandin.returnmessage = "Added " + players[0].GetPlayerName() + " to admin lvl " + commandin.commandargs[1]
            commandin.returncode = 200
        }

    }

    return commandin;
}


// serverdetails.currentlyplaying = GetConVarString("discordlogpreviousroundplayers")

// SetConVarString("discordlogpreviousroundplayers",uids)