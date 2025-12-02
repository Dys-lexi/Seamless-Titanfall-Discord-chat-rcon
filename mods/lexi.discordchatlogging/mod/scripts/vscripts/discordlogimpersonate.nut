global function discordlogimpersonate_init
global function discordlogimpersonate

void function discordlogimpersonate_init()
{
	AddDiscordRconCommand( discordlogimpersonate )
}

discordlogcommand function discordlogimpersonate(discordlogcommand commandin) {
    if (discordlogcheck("impersonate", true, commandin)){
            return commandin;
    }
	serverdetails.showchatprefix = GetConVarBool("discordlogshowteamchatprefix")
    commandin.commandmatch = true
    string message = ""
    for(int i = 1; i < commandin.commandargs.len(); i++)
    {
        message += commandin.commandargs[i] + " "
    }
        array<entity> players = discordlogmatchplayers(commandin.commandargs[0])
    if (players.len() == 0){
        commandin.returnmessage = "No players found"
        commandin.returncode = 401
        return commandin;
    }
    else if (players.len() > 1){
        commandin.returnmessage = "Multiple players found"
        commandin.returncode = 402
        return commandin;
    }


    commandin.returnmessage = "Impersonated " + players[0].GetPlayerName() +" with " + message
    calcmessage (players[0],message)
    commandin.returncode = 200
    return commandin;
}


void function calcmessage ( entity player, string message, bool isTeam = false){
	// log typical messages
    // string playername = message.player.GetPlayerName()
	// string messagecontent = message.message
	// print(serverdetails.Servername)
	bool showchatprefix = GetConVarBool( "discordlogshowteamchatprefix" ) && !IsFFAGame() && GetCurrentPlaylistVarInt( "max_teams", 2 ) == 2
	string teamnewmessage = player.GetPlayerName()
	string teammessage = "not team"
    if( isTeam && showchatprefix )
    {
		int playerteam = player.GetTeam()
		if ( playerteam == TEAM_IMC )
			teammessage = "IMC"
		else if ( playerteam == TEAM_MILITIA )
			teammessage = "Militia"

		teammessage = "[Team-" + teammessage + "]"
	}
	// print(teammessage)
	outgoingmessage newmessage
	newmessage.playername = teamnewmessage
	newmessage.message = message
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 1
	table meta
	if (IsAlive(player)){

			if ( discordlogpullplayerstat(player.GetUID(),"togglebrute") == "True" && (player.GetModelName() == $"models/titans/light/titan_light_northstar_prime.mdl" || player.GetModelName() == $"models/titans/light/titan_light_raptor.mdl"))
		{
			meta["pfp"] <- "brute"}
		else if ( discordlogpullplayerstat(player.GetUID(),"toggleexpi") == "True" && player.GetModelName() == $"models/titans/medium/titan_medium_vanguard.mdl" )
		{
			meta["pfp"] <-  "expedition"
		}
		else{
			meta["pfp"] <- player.GetModelName() + ""}
	}
	else{
		// array<string> knownuids = expect array<string>(TableKeysToArray(lastmodels.playermodels))
		// if (knownuids.contains(message.player.GetUID())){
		// print("PFP PFP FPF"+lastmodels.playermodels[message.player.GetUID()] + "")
		 if ( player.GetUID() in discordloggetlastmodels ){
		meta["pfp"] <- discordloggetlastmodels[player.GetUID()]}
		// // }
		// else{
		// 	meta["pfp"] <- "I don't know"
		// }
	}
	if ( showchatprefix )
		meta["teamtype"] <- teammessage

	meta["teamint"] <- player.GetTeam()
	meta["type"] <- "impersonate"
	meta["isalive"] <- IsAlive(player)
		meta["uid"] <- player.GetUID()
		meta["blockedmessage"] <- true
		if ( newmessage.message[0] == 47 || newmessage.message[0] == 33 )
		{
			
			// meta["type"] <- "command"
			
			
			// newmessage.overridechannel = "commandlogchannel"
			// newmessage.typeofmsg = 3
		}
	
	

	newmessage.metadata = EncodeJSON(meta)
	
	discordlogpostmessages(newmessage)

}