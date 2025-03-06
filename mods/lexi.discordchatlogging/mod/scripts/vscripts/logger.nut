global function discordloggerinit //init mod
global function discordlogextmessage //allows other mods to send messages
global function discordlogmatchplayers //given a string, returns all players whose name includes said string
global function discordlogcheck //check if a command should be run
global function discordlogsendmessage //send a message to all players, accounting for them being dead (messages sent here have a chance of not being in order, if sent fast)

// to add your own function create a file called xyz.nut in the same place as this one
// then make it's file load in the mod.json AFTER logger.nut
// after that, make the line "global function discordlogYOURFUNCTIONNAME"
// then create the function, in the same format as the one in sanctionapiban.nut -> it must immedtiatly call discordlogcheck, and return the commandin struct if it doesn't match. if it does,
// set commandin.commandmatch to true, and set commandin.returnmessage to the message you want to return.
// Then add the function's name to the array in getregisteredfunctions (below)





global struct discordlogcommand {
	bool commandmatch = false
	int returncode = -1
	string returnmessage
	string command 
	array<string> commandargs
}
struct {
	array<discordlogcommand functionref(discordlogcommand)> funcs
} registeredfunctions


array <discordlogcommand functionref(discordlogcommand)> function getregisteredfunctions(){
	return [
		discordlogplaying,
		discordlogthrowplayer,
		discordlogsimplesay,
		discordloggetuid,
		discordlogkickplayer,
		discordlogsendimage
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
	return (split(inputcommand.command," ")[0].find(command) == null || (inputcommand.command[0] != 47 && inputcommand.command[0] != 33))
}
struct outgoingmessage{
	string playername
	string message
	int timestamp
	int typeofmsg // 1 = chat message, needs a playername. 2 = codeblock chat message, needs a playername. 3 and 4 are the same pattern, but do not need a playername.
	bool globalmessage = false
}
struct {
	string Requestpath
	string Servername
	string serverid
	int rconenabled
	string password
} serverdetails


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
	table currentTime = GetUnixTimeParts()
	print(currentTime)
	serverdetails.Requestpath = GetConVarString("discordlogginghttpServer")
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


	if (GetConVarInt("discordloggingallowreturnmessages")) {
		thread DiscordClientMessageinloop()
	}
	serverdetails.rconenabled = GetConVarInt("discordloggingrconenabled")
	}
	// print(serverdetails.Servername)
}   
void function LogConnect( entity player )
{
	if(!IsValid(player) || Time() < 30)
	{
		return
	}
	// print(Time())
	outgoingmessage newmessage 
	newmessage.playername = player.GetPlayerName()
	newmessage.message = "has joined the server ("+GetPlayerArray().len().tostring()+" Connected)"
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 2
	Postmessages(newmessage)
	
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
	newmessage.typeofmsg = 2
	Postmessages(newmessage)
	
}

ClServer_MessageStruct function LogMSG ( ClServer_MessageStruct message ){
	// log typical messages
    // string playername = message.player.GetPlayerName()
	// string messagecontent = message.message
	// print(serverdetails.Servername)
	outgoingmessage newmessage 
	newmessage.playername = message.player.GetPlayerName()
	newmessage.message = message.message
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 1
	if (newmessage.message[0] == 47 || newmessage.message[0] == 33){
		return message
	}
	Postmessages(newmessage)



	
    return message
}
void function discordlogextmessage(string message, bool formatascodeblock = false, bool globalmessage = false){
	outgoingmessage newmessage 
	newmessage.message = message
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.globalmessage = globalmessage
	if (!formatascodeblock){
		newmessage.typeofmsg = 3
	}
	else{
		newmessage.typeofmsg = 4
	}
	Postmessages(newmessage)
}

struct {
	array<string> textcheck = []
	table commandcheck = {}
	int postmatch
	int allowlogging = 0
	int denylogging = 0
	string timeof = "0"
} check

void function Postmessages(outgoingmessage message){
	// print(serverdetails.Servername)
	table params = {}
	params["password"] <- serverdetails.password
	params["servername"] <- serverdetails.Servername
	params["messagecontent"] <- message.message
	params["timestamp"] <- message.timestamp
	params["type"] <- message.typeofmsg //yr
	params["serverid"] <- serverdetails.serverid
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

    }

    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
        print("[DiscordLogger]Failed to log chat message"  + failure.errorMessage)
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
	newmessage.message = "Map changed to " + MAP_NAME_TABLE[GetMapName()]
	// print(newmessage.message)
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 2
	Postmessages(newmessage)
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

void function discordlogsendmessage(string message){
	Chat_ServerBroadcast(message,false)
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
		table texts = expect table(messagess["texts"])
		// string textvalidation = expect string(messagess["textvalidation"])
		// array<string> splittextvalidation = split(textvalidation,"%&%&")
		// array<string> splittexts = split(texts,"%&%&")
		// array<string> splitcommands = split(commands,"⌨")
		// print(texts.len())
		if (serverdetails.rconenabled){
		foreach (value,key in commands){
		
			string command = expect string(key)
			string validation = expect string(value)

			print("[DiscordLogger] COMMAND"+command)
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
		foreach (value, key in texts){
			string validation = expect string(value)
			string text = expect string(key)
			print("[DiscordLogger] MESSAGE"+text)
			check.textcheck.append(validation)
			thread discordlogsendmessage("\x1b[38;5;105m"+text)
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

void function runcommand(string command,string validation) {
	check.commandcheck[validation] <- EncodeJSON({statuscode=-3,output=command+": Special command not found"})
	discordlogcommand commandstruct
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

