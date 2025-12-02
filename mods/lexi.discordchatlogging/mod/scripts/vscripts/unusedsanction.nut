/*
global function discordlogsanctioninit
global function discordlogsanction


global function discordlogsanctionremove

void function discordlogsanctioninit()
{
	AddDiscordRconCommand( discordlogsanction )
	AddDiscordRconCommand( discordlogsanctionremove )
}

discordlogcommand function discordlogsanctionremove(discordlogcommand commandin) {
    if (discordlogcheck("sanctionbanremove", true, commandin)){
            return commandin;
    }

      if (GetConVarBool("discordloggingenablesanctionapicommand") == false || SANCTIONAPI_ENABLED == false)
    {
        commandin.returnmessage = "Sanction API is disabled.";
        return commandin;
    }
    commandin.commandmatch = true

    if (commandin.commandargs.len() != 2)
    {
        commandin.returnmessage = "Wrong number of args";
        return commandin;
    }

    // bool function SanctionRemoveCMD(entity player, array < string > args) {
    return commandin;

    HttpRequest request
    request.headers["x-api-key"] <- [""]
    request.method = HttpRequestMethod.DELETE
    request.url = "http://1"
    if(commandin.commandargs[0]=="uid")
    { 
        request.queryParameters[ "UID" ] <- [ commandin.commandargs[1] ]
    }else{
        request.queryParameters[ "PlayerName" ] <- [ commandin.commandargs[1] ]
    }
    void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse message )
    {
        // DPrint(message.body)
        commandin.returnmessage = message.body
        command.
    }
    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
        // DPrint(failure.errorMessage)
    }
    NSHttpRequest( request, onSuccess, onFailure)
    return true

}



discordlogcommand function discordlogsanction(discordlogcommand commandin) {
    if (discordlogcheck("sanctionban", true, commandin)){
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
    string realsanctiontype = ""
	for(int i = 1; i < commandin.commandargs.len()-1; i++)
	{
		switch( commandin.commandargs[i] )
			{
				case "-type":
					if(commandin.commandargs[i+1]=="mute")
					{
						SanctionType = 0
                        realsanctiontype = "mute"
					}else if(commandin.commandargs[i+1]=="ban")
					{
						SanctionType = 1
                        realsanctiontype = "ban"
					}
					else{
						
						commandin.returnmessage = "Sanction type has to be ban or mute.";
                        return commandin;
					}
					break
				case "-expire":
                    if (commandin.commandargs[i+1] == "-expire" || commandin.commandargs[i+1] == "-reason" || commandin.commandargs[i+1] == "-type" || commandin.commandargs[i+1] == "-issuer")
                    {
                        
                    }
                    else{
        
					expire = commandin.commandargs[i+1]}
					break
                case "-issuer":
                    if (commandin.commandargs[i+1] == "-expire" || commandin.commandargs[i+1] == "-reason" || commandin.commandargs[i+1] == "-type" || commandin.commandargs[i+1] == "-issuer")
                    {
                        
                    }
                    else{
                    issueruid = commandin.commandargs[i+1]}
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
    table data = {}
    data["playername"] <- playername
    data["Sanctiontype"] <- realsanctiontype
    data["expire"] <- expiresat
    data["reason"] <- reason
    data["IP"] <- IP
    data["issueruid"] <- issueruid
    data["UID"] <- UID
#if SANCTIONAPI_ENABLED
    UploadToDatabase(playername, UID, SanctionType.tostring(), issueruid, expire, reason, IP)
    commandin.returnmessage = EncodeJSON(data)
#endif
    return commandin;
}
*/