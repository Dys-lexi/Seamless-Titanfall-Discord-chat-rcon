global function discordloggerinit //init mod
global function discordlogextmessage //allows other mods to send messages
global function discordlogmatchplayers //given a string, returns all players whose name includes said string
global function discordlogcheck //check if a command should be run
global function discordlogsendmessage //send a message to all players, accounting for them being dead (messages sent here have a chance of not being in order, if sent fast) DISABLED
global function stoprequests // stop sending requests till map change
global function discordlogpostmessages // external call to main message sending function
global function discordloggetlastmodels // used for /impersonate to pull peoples player models when they are dead
global function runcommandondiscord // run a command on the discord bot like stats - runs as server, so is not validated like user commands are (rcon,asactuallyavailableintf2)
global function discordlogpullplayerstat // returns a persistentvar for a player, for commands that have persistent effects.

// to add your own function create a file called xyz.nut in the same place as this one
// then make it's file load in the mod.json AFTER logger.nut
// after that, make the line "global function discordlogYOURFUNCTIONNAME"
// then create the function, in the same format as the one in discordlogkick.nut -> it must immedtiatly call discordlogcheck, and return the commandin struct if it doesn't match. if it does,
// set commandin.commandmatch to true, and set commandin.returnmessage to the message you want to return, and commandin.returncode to the code you want to return
// (codes do not mean too much, they work in a similar way to http codes)
// Then add the function's name to the array in getregisteredfunctions (the first function defined below)

// you'll be able to call the function with /rcon cmd:!YOURCOMMAND param1 param2 param3 on discord, or you can make a custom command in discord/data/commands.json



global struct discordlogcommand {
	bool commandmatch = false
	int returncode = -1
	string returnmessage
	string command
	array<string> commandargs
	string matchid
}

global struct outgoingmessage{
	string playername
	string message
	int timestamp
	int typeofmsg
	bool globalmessage = false
	string overridechannel = "None"
	string metadata = "None"
}


struct {
	array<discordlogcommand functionref(discordlogcommand)> funcs
} registeredfunctions


array <discordlogcommand functionref(discordlogcommand)> function getregisteredfunctions(){
	return [
		discordloggetdiscordcommands
		discordlogplaying,
		discordlogthrowplayer,
		discordlogsimplesay,
		discordloggetuid,
		discordlogkickplayer,
		discordlogsendimage,
		discordlogplayingpoll,
		discordlogtoggleadmin,
		getconvar,
		extmessagesendtester,
		discordlogimpersonate,
		reloadpersistentsettings
		]
		 //add functions here, and they'll work with / commands (if they fill criteria above)
}

array <entity> function discordlogmatchplayers(string playername){ //returns all players that have a partial playername match
	array<entity> matchedplayers = [];
    array<entity> players = GetPlayerArray()
    foreach (entity player in players)
        {
            if (player != null)
            {
                string playernamec = player.GetPlayerName()
                if (playernamec.tolower().find(playername.tolower()) != null)
                {
                    matchedplayers.append(player)

                }
            }
        }
	return matchedplayers
}

bool function discordlogcheck(string command, discordlogcommand inputcommand){
	// print(split(inputcommand.command," ")[0].find(command) == null)
	return ( (inputcommand.command[0] != 47 && inputcommand.command[0] != 33) || split(split(inputcommand.command," ")[0],"!/")[0] != command)
}

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


struct {
	table playermodels
} discordloglastmodels

table function discordloggetlastmodels(){
	return discordloglastmodels.playermodels
}

table<string,float> playerrespawn = {
	
}
table<string,bool> tf2todiscordcommands = {
	
}
struct {
	table<string,table> players
	bool hasfailedandneedstorequestagain = false
	array<string> messagespassed = []
} blockedplayers

// maps shamelessly stolen fvnk

table<string, string> MAP_NAME_TABLE = {
    mp_angel_city = "Angel City",
    mp_black_water_canal = "Black Water Canal",
    mp_coliseum = "Coliseum",
    mp_coliseum_column = "Pillars",
    mp_colony02 = "Colony",
    mp_complex3 = "Complex",
    mp_crashsite3 = "Crash Site",
    mp_drydock = "Drydock",
    mp_eden = "Eden",
    mp_forwardbase_kodai = "Forwardbase Kodai",
    mp_glitch = "Glitch",
    mp_grave = "Boomtown",
    mp_homestead = "Homestead",
    mp_lf_deck = "Deck",
    mp_lf_meadow = "Meadow",
    mp_lf_stacks = "Stacks",
    mp_lf_township = "Township",
    mp_lf_traffic = "Traffic",
    mp_lf_uma = "UMA",
    mp_relic02 = "Relic",
    mp_rise = "Rise",
    mp_thaw = "Exoplanet",
    mp_wargames = "Wargames",
    mp_mirror_city = "Mirror City",
	mp_brick = "BRICK"
}


void function discordloggerinit() {
	AddCallback_OnPlayerRespawned( OnPlayerRespawned )

	serverdetails.matchid = GetUnixTimestamp()+"_" + GetConVarString("discordloggingserverid")
	SetConVarString("discordloggingmatchid",serverdetails.matchid)
	registeredfunctions.funcs = getregisteredfunctions()

	#if SANCTIONAPI_ENABLED
		print("[DiscordLogger]Sanction API enabled")
		registeredfunctions.funcs.append(discordlogsanction)
		registeredfunctions.funcs.append(discordlogsanctionremove)
	#endif

	if(!GetConVarBool("discordloggingenabled"))
	{
		print("[DiscordLogger]discord logging disabled")
		return
	}

	//AddNewFunctForEnd(SaveLog)
	// get epoch time
	// mp\_gamestate_mp.nut:
	// table currentTime = GetUnixTimeParts()
	// print(currentTime)
	// serverdetails.currentlyplaying = GetConVarString("discordlogpreviousroundplayers")
	serverdetails.Requestpath = GetConVarString("discordlogginghttpServer")
	serverdetails.showchatprefix = GetConVarBool("discordlogshowteamchatprefix")
	serverdetails.password = GetConVarString("discordloggingserverpassword")
	print("[DiscordLogger]Servername: "+GetConVarString("discordloggingservername"))
	print("[DiscordLogger]Requestpath: "+serverdetails.Requestpath)
	if (GetConVarString("discordloggingservername") == "useactualservername"){
	serverdetails.Servername = GetConVarString("NS_SERVER_NAME")}
	else {
		serverdetails.Servername = GetConVarString("discordloggingservername")
	}
	serverdetails.serverid = GetConVarString("discordloggingserverid")
	
	if (GetConVarInt("discordloggingserverid") == 0){
		print("[DiscordLogger]Server ID not set, please set it in the console")
	} else {
		print("[DiscordLogger]Discord logging enabled")
		AddCallback_OnReceivedSayTextMessage( LogMSG )
	AddCallback_OnClientConnected( LogConnect )
	AddCallback_OnClientDisconnected( LogDC)
	AddCallback_GameStateEnter(eGameState.Playing, begintodiscord);
	// AddCallback_GameStateEnter(eGameState.PickLoadout, Onmapchange);
    AddCallback_GameStateEnter(eGameState.Prematch, Onmapchange);
	AddCallback_GameStateEnter(9,stoprequests);
	AddCallback_OnPlayerKilled(playerstabbedmodelsaver)

	if (GetConVarInt("discordloggingallowreturnmessages")) {
		thread DiscordClientMessageinloop()
	}
	serverdetails.rconenabled = GetConVarInt("discordloggingrconenabled")
	if (serverdetails.rconenabled){
		runcommandondiscord("getdiscordcommands")
	}
	}
	// print(serverdetails.Servername)
}


void function LogConnect( entity player )
{
	thread checkshouldblockmessages(player)
	if(!IsValid(player))
	{
		return
	}
	
	else if (Time() < 30){ // && serverdetails.currentlyplaying.find(player.GetUID().tostring()) != null){
		print("[DiscordLogger] Player "+player.GetPlayerName()+" is already in the server, not logging")
		return
	}
	// print(Time())
	outgoingmessage newmessage
	newmessage.playername = player.GetPlayerName()
	newmessage.message = "has joined the server ("+GetPlayerArray().len().tostring()+" Connected)"
	newmessage.timestamp = GetUnixTimestamp()
	table meta
	meta["uid"] <- player.GetUID()
	meta["type"] <- "connect"
	newmessage.metadata = EncodeJSON(meta)
	newmessage.typeofmsg = 2
	thread Postmessages(newmessage)
	discordloglastmodels.playermodels[player.GetUID()] <- player.GetModelName() + ""

}
void function LogDC( entity player )
{
	if(!IsValid(player))
	{
		return
	}
	outgoingmessage newmessage
	newmessage.playername = player.GetPlayerName()
	newmessage.message = "has left the server ("+(GetPlayerArray().len()-1).tostring()+" Connected)"
	newmessage.timestamp = GetUnixTimestamp()
	table meta
	meta["uid"] <- player.GetUID()
	meta["type"] <- "disconnect"
	newmessage.metadata = EncodeJSON(meta)
	newmessage.typeofmsg = 2
	thread Postmessages(newmessage)

}

void function playerstabbedmodelsaver( entity player, entity attacker, var damageInfo) {
	// table newmodel
	// newmodel["pfp"] <- player.GetModelName() + ""
	discordloglastmodels.playermodels[player.GetUID()] <- player.GetModelName() + ""
	float respawntime = Time()
	int methodOfDeath = DamageInfo_GetDamageSourceIdentifier( damageInfo )
	float replayLength = CalculateLengthOfKillReplay( player, methodOfDeath )
	bool shouldDoReplay = Replay_IsEnabled() && KillcamsEnabled() && IsValid( attacker ) && ShouldDoReplay( player, attacker, replayLength, methodOfDeath )
	if (shouldDoReplay){
		respawntime += replayLength
	}
	playerrespawn[player.GetUID()+""] <- respawntime+1
}

ClServer_MessageStruct function LogMSG ( ClServer_MessageStruct message ){
	// log typical messages
    // string playername = message.player.GetPlayerName()
	// string messagecontent = message.message
	// print(serverdetails.Servername)
	string teamnewmessage = message.player.GetPlayerName()
	string teammessage = "not team"
    if( message.isTeam && serverdetails.showchatprefix )
    {
	int playerteam = message.player.GetTeam()
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
	teammessage = "[Team-" + teammessage + "]"
	}
	// print(teammessage)
	outgoingmessage newmessage
	newmessage.playername = teamnewmessage
	newmessage.message = message.message
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 1
	table meta
	if (IsAlive(message.player)){
	meta["pfp"] <- message.player.GetModelName() + ""}
	else{
		// array<string> knownuids = expect array<string>(TableKeysToArray(discordloglastmodels.playermodels))
		// if (knownuids.contains(message.player.GetUID())){
		// print("PFP PFP FPF"+discordloglastmodels.playermodels[message.player.GetUID()] + "")
		 if ( message.player.GetUID() in discordloglastmodels["playermodels"] ){
		meta["pfp"] <- discordloglastmodels["playermodels"][message.player.GetUID()]}
		// // }
		// else{
		// 	meta["pfp"] <- "I don't know"
		// }
	}
	meta["teamtype"] <- teammessage
	meta["teamint"] <- message.player.GetTeam()
	meta["type"] <- "usermessagepfp"
	if (serverdetails.showchatprefix){
	meta["isalive"] <- IsAlive(message.player)}
	meta["uid"] <- message.player.GetUID()
	if (newmessage.message[0] == 47 || newmessage.message[0] == 33){
		
		meta["type"] <- "command"
		
		
		newmessage.overridechannel = "commandlogchannel"
		newmessage.typeofmsg = 3
	}
	else{
	
	

	bool found = false
	foreach (string key,table value in blockedplayers.players){
		if (message.player.GetUID() == key && blockedplayers.players[key].shouldblockmessages){
			found = true
			break
		}
	}
	meta["blockedmessage"] <- (found && blockedplayers.players[message.player.GetUID()].shouldblockmessages && !blockedplayers.hasfailedandneedstorequestagain)
	if (found && blockedplayers.players[message.player.GetUID()].shouldblockmessages && !blockedplayers.hasfailedandneedstorequestagain) {
		message.shouldBlock = true;
	}}
	// Chat_ServerBroadcast("BLOCKING"+split(message.message.tolower().slice(1)," ")[0] + " " + (split(message.message.tolower().slice(1)," ")[0] in tf2todiscordcommands ) )
	if (format("%c", message.message.tolower()[0]) == "!" && (split(message.message.tolower().slice(1)," ")[0] in tf2todiscordcommands && tf2todiscordcommands[split(message.message.tolower().slice(1)," ")[0]]  )){
		// Chat_ServerBroadcast("BLOCKING")
		message.shouldBlock = true
		meta["blockedcommand"] <- true
	}
	newmessage.metadata = EncodeJSON(meta)
	thread Postmessages(newmessage)


    return message
}
void function discordlogextmessage(string message, bool formatascodeblock = false, bool globalmessage = false, string channel = "None"){
	outgoingmessage newmessage
	newmessage.message = message
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.overridechannel = channel
	newmessage.globalmessage = globalmessage
	if (!formatascodeblock){
		newmessage.typeofmsg = 3
	}
	else{
		newmessage.typeofmsg = 4
	}
	thread Postmessages(newmessage)
}

struct {
	array<string> textcheck = []
	table commandcheck = {}
	int postmatch
	int allowlogging = 0
	int denylogging = 0
	string timeof = "0"
} check

string function discordlogpullplayerstat(string uid, string stat){
	if (!(uid in blockedplayers.players)){
		return ""
	}
	else if (!(stat in blockedplayers.players[uid])) {
		return ""
	}
	return expect string (blockedplayers.players[uid][stat])

}

void function checkshouldblockmessages(entity player){
	table params = {}
	params["password"] <- serverdetails.password
	params["uid"] <- player.GetUID()
	HttpRequest request
	request.method = HttpRequestMethod.POST
	request.url = serverdetails.Requestpath + "/playerdetails"
	request.body = EncodeJSON(params)
	
	void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse response )
    {
		// print("[DiscordLogger] MSG SENT")
				if (response.statusCode
		!= 200)
		{
			print("[DiscordLogger] Error: "+response.statusCode)
			return
			
		}


		// print(response.body)
		table responses = DecodeJSON(response.body)
		if ("notfound" in responses) {return}
		table output = expect table(responses["output"])
		table otheroutputs = expect table(responses["otherdata"])
		// blockedplayers.players[expect string(responses["uid"])]
		// string uid = expect string(responses["uid"])
		table actualoutput
		foreach (key,value in otheroutputs){
			actualoutput[ expect string(key)] <- expect string(value)
		}
		actualoutput.shouldblockmessages <- expect bool(output["shouldblockmessages"])
		blockedplayers.players[expect string(responses["uid"])] <- actualoutput
		// string texts = expect string(responses["texts"])
		// check.timeof = expect string(responses["time"])
		// table texts = expect table(responses["texts"])
		// table textsv2 = expect table(responses["textsv2"])
		// string textvalidation = expect string(messagess["textvalid
    }

    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
		// table errortable
		// errortable.blockmessages <- true
		blockedplayers.hasfailedandneedstorequestagain = true
    }

	// print(EncodeJSON(params))

    NSHttpRequest(request, onSuccess, onFailure)
}
void function discordlogpostmessages(outgoingmessage message){
	thread Postmessages(message)
}

void function Postmessages(outgoingmessage message){
	// print(serverdetails.Servername)
	table params = {}
	params["password"] <- serverdetails.password
	params["servername"] <- serverdetails.Servername
	params["messagecontent"] <- message.message
	params["timestamp"] <- message.timestamp
	params["type"] <- message.typeofmsg //yr
	params["serverid"] <- serverdetails.serverid
	params["metadata"] <- message.metadata
	params["overridechannel"] <- message.overridechannel
	if (message.playername != ""){
	params["player"] <- message.playername}
	params["globalmessage"] <- message.globalmessage
	HttpRequest request
	request.method = HttpRequestMethod.POST
	request.url = serverdetails.Requestpath + "/servermessagein"
	request.body = EncodeJSON(params)
	// print(request.body)
	// print(serverdetails.Requestpath + "/servermessagein")

	void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse response )
    {
		// print("[DiscordLogger] MSG SENT")
						if (response.statusCode
		!= 200)
		{
			print("[DiscordLogger] Error: "+response.statusCode)
			// print("[DiscordLogger] "+serverdetails.Requestpath + "/askformessage")
			return
		}
		blockedplayers.hasfailedandneedstorequestagain = false
		table responses = DecodeJSON(response.body)
		if ("messageteam" in responses) {
			int teamtype = expect int(responses["messageteam"])
		
			if ("forceblock" in responses) {
				if (expect string(responses["uid"])  in blockedplayers.players)
				{
						blockedplayers.players[expect string(responses["uid"])].shouldblockmessages <- expect bool(responses["forceblock"])
				
				}else{
							table actualoutput
						actualoutput.shouldblockmessages <- false
						blockedplayers.players[expect string(responses["uid"])] <- actualoutput
				}
				
			}
		if ("friendly" in responses) {
				discordlogsendmessage(expect string(responses["friendly"]),teamtype)	
         }
		 if ("enemy" in responses) {
				discordlogsendmessage(expect string(responses["enemy"]),(teamtype - 3)*-1+2)	
		 }
		 if ("both" in responses){
			discordlogsendmessage(expect string(responses["both"]),4)
		 }
    }}

    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
        print("[DiscordLogger]Failed to log chat message"  + failure.errorMessage)
		blockedplayers.hasfailedandneedstorequestagain = true
    }

	// print(EncodeJSON(params))

    NSHttpRequest(request, onSuccess, onFailure)


}
// Chat_ServerBroadcast

// wait <number> = wait seconds
int eCount = 0
int shouldsend = 1
int breakercounter = 0

void function Onmapchange(){
	wait 1
	outgoingmessage newmessage
	// string LocalizedMapName = Localize( "#STATS_NOT_APPLICABLE" )
	newmessage.playername = ""
	if( GetMapName() in MAP_NAME_TABLE )
	newmessage.message = "Map changed to " + MAP_NAME_TABLE[GetMapName()]
        else
	newmessage.message = "Map changed to " + GetMapName()
	// print(newmessage.message)
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 2
	thread Postmessages(newmessage)
}

// struct commandchecker {
// 	string commandid
// 	string returntext
// }


void function begintodiscord(){
  check.allowlogging = 1
}
void function stoprequests(){
	check.denylogging = 1
	table params = {}
	string uids = ""
	foreach (entity player in GetPlayerArray()){
		if (uids == ""){
			uids = player.GetUID().tostring()
		}
		else {
			uids = uids + "," + player.GetUID().tostring()
		}
	}
	SetConVarString("discordlogpreviousroundplayers",uids)
	params["password"] <- serverdetails.password
	params["serverid"] <- serverdetails.serverid
	HttpRequest request
	request.method = HttpRequestMethod.POST
	request.url = serverdetails.Requestpath + "/stoprequests"
	request.body = EncodeJSON(params)
	void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse response )
	{
		print("[DiscordLogger]Requests stopped")
	}

	void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
	{
		print("[DiscordLogger]Failed to stop requests"  + failure.errorMessage)
	}

	NSHttpRequest(request, onSuccess, onFailure)
}

void function discordlogsendmessage(string message, int team = 4,array<string> ovverideuids = []){
	thread discordlogsendmessagemakesureissent(message,team,ovverideuids)
	// int trys = 0
	// array <entity> players = GetPlayerArray()
	// array <entity> playersdone
	// // array <entity> playersnotdone = GetPlayerArray()
	// while (trys < 120 && players.len() > playersdone.len()){
	// 	foreach (entity player in players){
	// 		if (player.IsEntAlive()){
	// 			Chat_ServerPrivateMessage(player,message,false,false)
	// 			playersdone.append(player)
	// 			// playersnotdone.remove(playersnotdone.find(player))
	// 		}

	// 	}
	// 	wait 0.5
	// 	trys++
	// }
	// for (int i = 0; i < playersnotdone.len(); i++){
	// 	Chat_ServerPrivateMessage(playersnotdone[i],message,false,false)
	// }

}
void function discordlogsendmessagemakesureissent(string message, int team = 4, array<string> ovverideuids = []){
	array <entity> players = GetPlayerArray()
	if (ovverideuids.len() > 0){
		players = []
		foreach (entity player in GetPlayerArray() ){
		if (ovverideuids.contains(player.GetUID())) {
		players.append(player)
		}
		
		}
	}
	array <entity> shouldsend = []
	foreach (entity player in players){
		if (player.GetTeam() == team || team == 4){
			shouldsend.append(player)
		}
	}
	while (shouldsend.len() > 0){
		array <int> removeindexes = []
		for (int i = 0; i < shouldsend.len() ; i++){
			// Chat_ServerPrivateMessage(shouldsend[i],"e "+message,false,false)
			if (!IsValid(shouldsend[i]) ){
				removeindexes.append(i)
			}
			else if ( !(shouldsend[i].GetUID() +"" in playerrespawn) ||  Time() > playerrespawn[shouldsend[i].GetUID() +""] ) {
				
				removeindexes.append(i)
				
				Chat_ServerPrivateMessage(shouldsend[i],message,false,false)
				// Chat_PrivateMessage(shouldsend[i],shouldsend[i], "PRIVATE MESSAGE"+message,false)
				// discordlogextmessage("TRYING TO SEND "+message+" TO "+shouldsend[i].GetPlayerName() + Time() + " "+  playerrespawn[shouldsend[i].GetUID() +""] + IsAlive(shouldsend[i]) +  (Time() > playerrespawn[shouldsend[i].GetUID() +""]) )
			}
				

			
			// Chat_ServerBroadcast("alive" + IsAlive(shouldsend[i]) + "time" + Time() + "desiredtime" +shouldsend[i].GetPlayerName())
		}
		int offset = 0
		foreach (int removeindex in removeindexes){
			shouldsend.remove(removeindex-offset)
			offset +=1
		}
		WaitFrame()
	}

}
void function OnPlayerRespawned(entity player) {
	thread waitisalive(player)
}

void function waitisalive(entity player) {
	playerrespawn[player.GetUID()+""] <- Time() + 1
}
void function DiscordClientMessageinloop()
{
	// check.textcheck = []
	// check.commandcheck = []
	check.postmatch = 999999

	while (true) {
		// print("gamestate "+GetGameState())
		if (shouldsend == 0){
			wait 1
			breakercounter++
			if (breakercounter > 50){
				shouldsend = 1
				breakercounter = 0
				// print("breaking")
			}
			else {
				continue
			}
		}
	if (check.postmatch == 1){
		wait 1
		continue
	}
	// wait 1
	breakercounter = 0
	// print(GetPlayerArray().len())
	if(eCount==3 || GetPlayerArray().len() == 12313) //set to 0 to not relay if no people are on
	{
		wait 15
		eCount = 0

	}

	table params = {}
	params["password"] <- serverdetails.password
	// params["blockerror"] <- blockedplayers.hasfailedandneedstorequestagain

	params["serverid"] <- serverdetails.serverid
	// array<string>params["texts"] <- check.textcheck
	if (check.commandcheck.len() > 0){
	params["commands"] <- check.commandcheck}
	foreach (text in check.textcheck) {
		// print(text)
    	params[text] <- text
	}
	if (check.timeof != "0"){
		params["time"] <- check.timeof
	}
	// foreach (key,value in check.commandcheck){
	// 	string commandid = expect string(key)
	// 	string returntext = expect string(value)
	// 	params[commandid] <- returntext
	// }

    HttpRequest request
    request.method = HttpRequestMethod.POST
    request.url = serverdetails.Requestpath + "/askformessage"
	request.body = EncodeJSON(params)

	int timeout = 60
	if (check.denylogging == 1){
		break
	}
	if (check.allowlogging == 0) {
		wait 1
		continue
	}

	else if (check.allowlogging == 1 && GameTime_TimeLeftSeconds() < 60){
		// if (GameTime_TimeLeftSeconds()> check.postmatch || GameTime_TimeLeftSeconds() == 0){
		// 	wait 1
		// 	continue
		// }
		// print(GameTime_TimeLeftSeconds())
		// timeout = GameTime_TimeLeftSeconds()
		check.postmatch = GameTime_TimeLeftSeconds()
	}
	else {
		check.postmatch = 999999
	}
	// if(GetScoreLimit_FromPlaylist()-50 <GameRules_GetTeamScore(TEAM_MILITIA) || GetScoreLimit_FromPlaylist()*0.95 <GameRulfes_GetTeamScore(TEAM_IMC) || GameTime_TimeLeftSeconds() < 60)

	request.timeout = timeout

	// print("[DiscordLogger] Sending req:")
    void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse messages )
    {

		eCount = 0;
		// print("recieved")
		shouldsend = 1
		// print("[DiscordLogger] MSG RECIEVED")
		if (messages.statusCode
		!= 200)
		{
			print("[DiscordLogger] Error: "+messages.statusCode)
			// print("[DiscordLogger] "+serverdetails.Requestpath + "/askformessage")
			eCount++;
			return
		}

		check.textcheck = []
		check.commandcheck = {}
		// print(messages.body)
		table messagess = DecodeJSON(messages.body)
		table commands = expect table(messagess["commands"])
		// string texts = expect string(messagess["texts"])
		check.timeof = expect string(messagess["time"])
		// table texts = expect table(messagess["texts"])
		table textsv2 = expect table(messagess["textsv2"])
		// string textvalidation = expect string(messagess["textvalidation"])
		// array<string> splittextvalidation = split(textvalidation,"%&%&")
		// array<string> splittexts = split(texts,"%&%&")
		// array<string> splitcommands = split(commands,"⌨")
		// print(texts.len())
		if (serverdetails.rconenabled){
		foreach (value,key in commands){

			string command = expect string(key)
			string validation = expect string(value)

			print("[DiscordLogger] COMMAND "+command)
			if (command[0] == 47 || command[0] == 33){
				runcommand(command, validation)
	}
	else{

			ServerCommand(command)
			// table output = {commandid="validation",returntext=command+": command not found"}
			check.commandcheck[validation] <- EncodeJSON({statuscode=-2,output=command+": successfully ran console command"})


		}}}
		else if (commands.len() > 0){
			print("[DiscordLogger] RCON is not enabled, but commands were sent")
		}
		// array<string> splitsenders = split(senders,"%&%#[")
		// if(splittexts.len()!=splittextvalidation.len())
		// {
		// 	return
		// }
		// foreach (value, key in texts){
		// 	string validation = expect string(value)
		// 	string text = expect string(key)
		// 	print("[DiscordLogger] MESSAGE "+text)
		// 	check.textcheck.append(validation)
		// 	thread discordlogsendmessage(text)
		// 	// foreach (entity player in GetPlayerArray()) {
		// 	// 	Chat_PrivateMessage(player,player,"\x1b[38;5;105m"+text,false)
		// 	// }

		// }
				foreach (key, value in textsv2){
			table textw = expect table(value)
			string text = expect string(textw["content"])
			int teamoverride = expect int(textw["teamoverride"])
			string validation = expect string(textw["validation"])
			string ovverrideuids = expect string(textw["uidoverride"])
			array<string> uidoverride =  split(ovverrideuids,",")
			print("[DiscordLogger] MESSAGE "+text)
			check.textcheck.append(validation)
			thread discordlogsendmessage(text,teamoverride,uidoverride)
			// foreach (entity player in GetPlayerArray()) {
			// 	Chat_PrivateMessage(player,player,"\x1b[38;5;105m"+text,false)
			// }

		}
		

	}

    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
		shouldsend = 1
		if (failure.errorCode == 28){
			print("[DiscordLogger] Timeout")
			return
		}
		print("[DiscordLogger] ECode: "+failure.errorCode)
		print("[DiscordLogger] EMSG: "+failure.errorMessage)

		eCount++;

    }
	if (shouldsend == 1){

		// print("sending")
		shouldsend = 0
		// print(timeleft())

		// if (check.allowlogging == 1) {
		// 	print("sending"+timeout+" "+GameTime_TimeLeftSeconds())
		// }else{
		// print("sending"+timeout)}
		// wait 15
		NSHttpRequest( request, onSuccess, onFailure )}
}
}
void function runcommandondiscord(string commandname, table paramaters = {}){
	thread runcommandondiscordreal(commandname,paramaters)
}

void function runcommandondiscordreal(string commandname, table paramaters){
	table params = {}
		params["password"] <- serverdetails.password
		params["serverid"] <- serverdetails.serverid
		params["command"] <- commandname
		params["paramaters"] <- EncodeJSON(paramaters)
	
    HttpRequest request
    request.method = HttpRequestMethod.POST
    request.url = serverdetails.Requestpath + "/runcommand"
	request.body = EncodeJSON(params)
	    void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse messages )
{}
    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
	{}
	NSHttpRequest( request, onSuccess, onFailure )
}
void function runcommand(string command,string validation) {
	check.commandcheck[validation] <- EncodeJSON({statuscode=-3,output=command+": Special command not found"})
	discordlogcommand commandstruct
	commandstruct.matchid = serverdetails.matchid
	commandstruct.returnmessage = "Nothing returned by command"
	commandstruct.command = split(command," ")[0]
	array <string> commandargs = split(command," ")
	commandargs.remove(0)
	commandstruct.commandargs = commandargs
	for (int i = 0; i < registeredfunctions.funcs.len(); i++) {
		commandstruct = registeredfunctions.funcs[i](commandstruct)
		if (commandstruct.commandmatch) {
			check.commandcheck[validation] <- EncodeJSON({statuscode=commandstruct.returncode,output=commandstruct.returnmessage})
			return
		}
	}

	// throwplayer(command,validation)
	// listplayers(command,validation)
}

discordlogcommand function reloadpersistentsettings(discordlogcommand commandin) {
    if (discordlogcheck("reloadpersistentvars", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	int i = 0
	if (commandin.commandargs.len() < 1){
		commandin.returncode = 404
		commandin.returnmessage = "Wrong number of args"
		return commandin
	}
	string username = ""
	for( i = 0; i < commandin.commandargs.len()-1; i++) {
		username = username + commandin.commandargs[i] + " "
	}
	username = username + commandin.commandargs[commandin.commandargs.len() -1 ]
	array<entity> players = discordlogmatchplayers(username)
	if (players.len() != 1){
		commandin.returncode = 500
		commandin.returnmessage = "PLAYER NOT FOUND"
		return commandin
	}
	thread checkshouldblockmessages(players[0])
	commandin.returnmessage = "Trying to set persistentvars for "+players[0];
	commandin.returncode = 200
	return commandin
	
	
	}

discordlogcommand function discordloggetdiscordcommands(discordlogcommand commandin) {
    if (discordlogcheck("senddiscordcommands", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	int i = 0
	string prevarg = ""
	for( i = 0; i < commandin.commandargs.len(); i++) {
		if ((i+1) % 2) {
			prevarg = commandin.commandargs[i]
		}
		else{
			bool shouldblock = false
			if (commandin.commandargs[i] == "1") {
				shouldblock = true
			}
			tf2todiscordcommands[prevarg] <- shouldblock
		}
		
	}
	commandin.returnmessage = "Set commands - " + i / 2 + " commands found";
	commandin.returncode = 200
	return commandin
	
	
	}

// void function PushEntWithVelocity( entity ent, vector velocity )

// struct playerinfo {
// 	string playername = "Not found"
// 	int score = 0
// 	string team = "No team"
// 	int kills = 0
// 	int deaths = 0
// }
// struct playerlist {
// 	array<table> playerlist = []
// }

// void function listplayers(string args, string validation){
// 	// print(split(args," ")[0])
// 	if (split(args," ")[0].find("playing") == null){
// 		return
// 	}
// 	array<entity> players = GetPlayerArray()
// 	table playerlist
// 	foreach (entity player in players){
// 		playerinfo playerinfoe
// 		if (player != null){
// 			playerinfoe.playername = player.GetPlayerName()
// 			// print(PGS_SCORE)
// 			playerinfoe.score = player.GetPlayerGameStat(8)
// 			playerinfoe.kills = player.GetPlayerGameStat(1)
// 			playerinfoe.deaths = player.GetPlayerGameStat(2)
// 			// print(player.GetPlayerGameStat(PGS_PING)/100000)
// 			// playerinfoe.ping = string(player.GetPlayerGameStat(12))+ " " + string(player.GetPlayerGameStat(0)) + " " + string(player.GetPlayerGameStat(1)) + " " + string(player.GetPlayerGameStat(2)) + " " + string(player.GetPlayerGameStat(3)) + " " + string(player.GetPlayerGameStat(4)) + " " + string(player.GetPlayerGameStat(5)) + " " + string(player.GetPlayerGameStat(6)) + " " + string(player.GetPlayerGameStat(7)) + " " + string(player.GetPlayerGameStat(8)) + " " + string(player.GetPlayerGameStat(9)) + " " + string(player.GetPlayerGameStat(10)) + " " + string(player.GetPlayerGameStat(11)) + " " + string(player.GetPlayerGameStat(12)) + " " + string(player.GetPlayerGameStat(13)) + " " + string(player.GetPlayerGameStat(14)) + " " + string(player.GetPlayerGameStat(15)) + " " + string(player.GetPlayerGameStat(16)) + " " + string(player.GetPlayerGameStat(17)) + " " + string(player.GetPlayerGameStat(18)) + " " + string(player.GetPlayerGameStat(PGS_PING))
// 			if (player.GetTeam() == TEAM_MILITIA){
// 				playerinfoe.team = "Militia"
// 			}
// 			else if (player.GetTeam() == TEAM_IMC){
// 				playerinfoe.team = "IMC"
// 			}
// 			else {
// 				playerinfoe.team = string(player.GetTeam())
// 			}
// 			// playerlist.append(playerinfoe)
// 			// print(playerinfoe.playername)
// 			playerlist[playerinfoe.playername] <- [playerinfoe.score,playerinfoe.team,playerinfoe.kills,playerinfoe.deaths]
// 			int mtimeleft = 0
// 			if (check.allowlogging == 1){
// 				mtimeleft = GameTime_TimeLeftSeconds()
// 			}
// 			playerlist["meta"] <- [MAP_NAME_TABLE[GetMapName()],mtimeleft]
// 		}
// 	}


// 	check.commandcheck[validation] <- EncodeJSON(playerlist)

// }
