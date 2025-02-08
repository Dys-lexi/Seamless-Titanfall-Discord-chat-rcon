global function discordlogsanction



discordlogcommand function discordlogsanction(discordlogcommand commandin) {
    if (discordlogcheck("sanctionban", commandin)){
            return commandin;
    }


    // main bit, first is to check if this this command was called


    if (GetConVarBool("discordloggingenablesanctionapicommand") == false)
    {
        commandin.returnmessage = "Sanction API is disabled.";
        return commandin;
    }
    commandin.commandmatch = true
    if (commandin.commandargs.len() < 1)
    {
        commandin.returnmessage = "Not enough arguments.";
        return commandin;
    }
    array<string> playernames = [];
    string UID
    string IP
    array<entity> players = GetPlayerArray()
    foreach (entity player in players)
    {
        if (player != null)
        {
            string playername = player.GetPlayerName()
            if (playername.tolower().find(commandin.commandargs[0].tolower()) != null)
            {
                playernames.append(playername)
                UID = player.GetUID()
                IP = split(player.GetIPString(), ":]")[2]
                
            }
        }
    }
    if (playernames.len() > 1)
    {
        commandin.returnmessage = "Multiple players found with that name, no action taken.";
        return commandin;
    }
    else if (playernames.len() == 0)
    {
        commandin.returnmessage = "No player found with that name.";
        return commandin;
    }
    string playername = playernames[0]
    string expire = "";
	string reason = "";
    string issueruid = "";
    int SanctionType=-1;
	for(int i = 1; i < commandin.commandargs.len()-1; i++)
	{
		switch( commandin.commandargs[i] )
			{
				case "-type":
					if(commandin.commandargs[i+1]=="mute")
					{
						SanctionType = 0
					}else if(commandin.commandargs[i+1]=="ban")
					{
						SanctionType = 1
					}
					else{
						
						commandin.returnmessage = "Sanction type has to be ban or mute.";
                        return commandin;
					}
					break
				case "-expire":
					expire = commandin.commandargs[i+1]
					break
                case "-issuer":
                    issueruid = commandin.commandargs[i+1]
                    break
				case "-reason":
                        for(int y = i+1; y < commandin.commandargs.len(); y++)
                        {
                            if(commandin.commandargs[y]=="-expire" || commandin.commandargs[y]=="-reason" || commandin.commandargs[y]=="-type" || commandin.commandargs[y]=="-issuer")
                            {
                                i = y-1;
                                y=commandin.commandargs.len()
                            }
                            else
                            {
                                reason+=commandin.commandargs[y]+" "
                            }
                        }				
					break
			}
	}
    if (SanctionType == -1)
    {
        commandin.returnmessage = "No sanction type specified. (use -type <ban/mute>)";
        return commandin;
    }
    if (reason == "")
    {
        commandin.returnmessage = "No reason specified. (use -reason <reason>)";
        return commandin;
    }
    string expiresat = "never"
    if (expire != "")
    {
        expiresat = expire
    }
    if (issueruid == "")
    {
        commandin.returnmessage = "No issuer specified";
        return commandin;
    }

    // UploadToDatabase(playername, UID, SanctionType.tostring(), "DISCORD_ISSUED_BAN_TEMP", expire, reason, IP)
    commandin.returnmessage = "Sanction issued to "+playername+" with type: "+SanctionType.tostring()+" reason: "+reason + "issued by: "+issueruid+" expires at: "+expiresat;
    return commandin;
}