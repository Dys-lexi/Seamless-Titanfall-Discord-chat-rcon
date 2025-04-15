global function getconvar

discordlogcommand function getconvar(discordlogcommand commandin) {
    if (discordlogcheck("getconvar", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
    if (commandin.commandargs.len() != 1)
    {
        commandin.returnmessage = "Wrong number of args";
        commandin.returncode = 400
        return commandin;
    }
    string convar = GetConVarString(commandin.commandargs[0]);
    if (convar == "")
    {
        commandin.returnmessage = "Convar not found, or is empty";
        commandin.returncode = 404
        return commandin;
    }
    commandin.returnmessage = "Convar: " + commandin.commandargs[0] + " = " + convar;
    commandin.returncode = 200

    return commandin;
}


// GetConVarString("admin_lvl" + i)