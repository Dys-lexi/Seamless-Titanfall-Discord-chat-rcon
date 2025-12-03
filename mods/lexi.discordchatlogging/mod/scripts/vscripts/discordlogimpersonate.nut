global function discordlogimpersonate

struct {
	string Requestpath
	string Servername
	string serverid
	int rconenabled
	string password
	string currentlyplaying = ""
	string matchid
	bool showchatprefix
} serverdetails


discordlogcommand function discordlogimpersonate(discordlogcommand commandin) {
	serverdetails.showchatprefix = true//GetConVarBool("discordlogshowteamchatprefix")
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
	string teamnewmessage = player.GetPlayerName()
	string teammessage = "not team"
    if( isTeam && serverdetails.showchatprefix )
    {
	int playerteam = player.GetTeam()
	if( playerteam <= 0 )
	teammessage = "Spec"
    if( playerteam == 1 )
    teammessage = "None"
    if( playerteam == 2 )
    teammessage = "IMC"
    if( playerteam == 3 )
    teammessage = "Militia"
    if( playerteam >= 4 )
    teammessage = "Both"
	teammessage = "[TEAM (" + teammessage + ")]"
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
	meta["teamtype"] <- teammessage
	meta["teamint"] <- player.GetTeam()
	meta["type"] <- "impersonate"
	if (serverdetails.showchatprefix){
	meta["isalive"] <- IsAlive(player)}
	meta["uid"] <- player.GetUID()
	meta["blockedmessage"] <- true
	if (newmessage.message[0] == 47 || newmessage.message[0] == 33){
		
		// meta["type"] <- "command"
		
		
		// newmessage.overridechannel = "commandlogchannel"
		// newmessage.typeofmsg = 3
	}
	
	

	newmessage.metadata = EncodeJSON(meta)
	
	discordlogpostmessages(newmessage)

}