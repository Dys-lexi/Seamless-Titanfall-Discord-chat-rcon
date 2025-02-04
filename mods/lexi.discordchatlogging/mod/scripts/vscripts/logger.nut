global function discordloggerinit
global function discordlogextmessage

//local loggingflush = array(100) 

array<string> loggingflush
// create a string var
string logging_url

struct outgoingmessage{
	string playername
	string message
	int timestamp
	int typeofmsg
}
struct {
	string Requestpath
	string Servername
	string serverid
	int rconenabled
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

	if(!GetConVarBool("discordloggingenabled"))
	{
		print("[DiscordLogger]discord logging disabled")
		return
	}
	
	print("[DiscordLogger]Discord logging enabled")
	//AddNewFunctForEnd(SaveLog)
	// get epoch time
	// mp\_gamestate_mp.nut:
	table currentTime = GetUnixTimeParts()
	print(currentTime)
	serverdetails.Requestpath = GetConVarString("discordlogginghttpServer")
	if (GetConVarString("discordloggingservername") == "useactualservername"){
	serverdetails.Servername = GetConVarString("NS_SERVER_NAME")}
	else {
		serverdetails.Servername = GetConVarString("discordloggingservername")
	}
	serverdetails.serverid = GetConVarString("discordloggingserverid")
	if (GetConVarInt("discordloggingserverid") == 0){
		print("[DiscordLogger]Server ID not set, please set it in the console")
	} else {
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
void function discordlogextmessage(string message, bool formatascodeblock = false){
	outgoingmessage newmessage 
	newmessage.playername = ""
	newmessage.message = message
	newmessage.timestamp = GetUnixTimestamp()
	if (formatascodeblock){
		newmessage.typeofmsg = 2
	} else {
		newmessage.typeofmsg = 3
	}
	Postmessages(newmessage)
}


void function Postmessages(outgoingmessage message){
	// print(serverdetails.Servername)
	table params = {}
	params["servername"] <- serverdetails.Servername
	params["messagecontent"] <- message.message
	params["player"] <- message.playername
	params["timestamp"] <- message.timestamp
	params["type"] <- message.typeofmsg
	params["serverid"] <- serverdetails.serverid
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

	print(EncodeJSON(params))

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

struct {
	array<string> textcheck = []
	table commandcheck = {}
	int postmatch
	int allowlogging = 0
	int denylogging = 0
	string timeof = "0"
} check

void function begintodiscord(){
  check.allowlogging = 1
}
void function stoprequests(){
	check.denylogging = 1
	table params = {}
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
	// if(GetScoreLimit_FromPlaylist()-50 <GameRules_GetTeamScore(TEAM_MILITIA) || GetScoreLimit_FromPlaylist()*0.95 <GameRules_GetTeamScore(TEAM_IMC) || GameTime_TimeLeftSeconds() < 60)
	
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

			print(command)
			if (command[0] == 47 || command[0] == 33){
				runcommand(command, validation)
	}
	else{

			ServerCommand(command)
			// table output = {commandid="validation",returntext=command+": command not found"}
			check.commandcheck[validation] <- command+": successfully ran console command"}
			

		}}
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
			print(text)
			check.textcheck.append(validation)
			Chat_ServerBroadcast("\x1b[38;5;105m"+text,false)
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
	check.commandcheck[validation] <- command+": special command not found"
	throwplayer(command,validation)
	listplayers(command,validation)
}

// void function PushEntWithVelocity( entity ent, vector velocity )

struct playerinfo {
	string playername = "Not found"
	int score = 0
	string team = "No team"
	int kills = 0
	int deaths = 0
}
// struct playerlist {
// 	array<table> playerlist = []
// } 

void function listplayers(string args, string validation){
	// print(split(args," ")[0])
	if (split(args," ")[0].find("playing") == null){
		return
	}
	array<entity> players = GetPlayerArray()
	table playerlist
	foreach (entity player in players){
		playerinfo playerinfoe
		if (player != null){
			playerinfoe.playername = player.GetPlayerName()
			print(PGS_SCORE)
			playerinfoe.score = player.GetPlayerGameStat(8)
			playerinfoe.kills = player.GetPlayerGameStat(1)
			playerinfoe.deaths = player.GetPlayerGameStat(2)
			if (player.GetTeam() == TEAM_MILITIA){
				playerinfoe.team = "Militia"
			}
			else if (player.GetTeam() == TEAM_IMC){
				playerinfoe.team = "IMC"
			}
			else {
				playerinfoe.team = string(player.GetTeam())
			}
			// playerlist.append(playerinfoe)
			print(playerinfoe.playername)
			playerlist[playerinfoe.playername] <- [playerinfoe.score,playerinfoe.team,playerinfoe.kills,playerinfoe.deaths]
			int mtimeleft = 0
			if (check.allowlogging == 1){
				mtimeleft = GameTime_TimeLeftSeconds()
			}
			playerlist["meta"] <- [MAP_NAME_TABLE[GetMapName()],mtimeleft]
		}
	}


	check.commandcheck[validation] <- EncodeJSON(playerlist)

}

void function throwplayer(string args, string validation){
	if (split(args," ")[0].find("throw") == null){
		return
	}
	array<string> splitargs = split(args," ")
	if (splitargs[1] == "all"){
		print("throwing all players")
		array<entity> players = GetPlayerArray()
		foreach (entity player in players){
			if (player != null){
				vector velocity = player.GetVelocity()
				velocity.z = 10000
				PushEntWithVelocity(player,velocity)
			}
		}
		check.commandcheck[validation] <- args + ": All players thrown"
	}
	else {
		entity player = findname(splitargs[1])
		if (player != null){
			print("throwing "+player.GetPlayerName())
			vector velocity =player.GetVelocity()
			velocity.z = 10000
			PushEntWithVelocity(player,velocity)
			check.commandcheck[validation] <-  args + ": "+player.GetPlayerName()+" thrown"
		}
		else {
			check.commandcheck[validation] <- args + ": Player not found"}
	}


}


entity function findname(string name)
{
    array<entity> players = GetPlayerArray()
	array<entity> successfulnames = []
    foreach (entity player in players)
    {
        if (player != null)
        {
            string playername = player.GetPlayerName()
            if (playername.tolower().find(name.tolower()) != null)
            {
              
                successfulnames.append(player)
                
                           
            }
        }
    }
	if (successfulnames.len() == 1){
		return successfulnames[0]
	}
	else {
		return null
	}
    return;
}