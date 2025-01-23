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
	newmessage.message = "Map changed too " + MAP_NAME_TABLE[GetMapName()]
	// print(newmessage.message)
	newmessage.timestamp = GetUnixTimestamp()
	newmessage.typeofmsg = 2
	Postmessages(newmessage)
}

struct {
	array<string> textcheck
	int postmatch
	int allowlogging = 0
} check

void function begintodiscord(){
  check.allowlogging = 1
}


void function DiscordClientMessageinloop()
{
	check.textcheck = []
	check.postmatch = 999999
	
	while (true) {
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
	foreach (text in check.textcheck) {
		// print(text)
    	params[text] <- text
	}

	
    HttpRequest request
    request.method = HttpRequestMethod.POST
    request.url = serverdetails.Requestpath + "/askformessage"
	request.body = EncodeJSON(params)
	
	int timeout = 60
	if (check.allowlogging == 1 && GameTime_TimeLeftSeconds() < 60){
		if (GameTime_TimeLeftSeconds()> check.postmatch){
			wait 1
			continue
		}
		// print(GameTime_TimeLeftSeconds())
		timeout = GameTime_TimeLeftSeconds()
		check.postmatch = GameTime_TimeLeftSeconds()
	}
	
	request.timeout = timeout
	
	// print("[DiscordLogger] Sending req:")
    void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse messages )
    {
		eCount = 0;
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
		table messagess = DecodeJSON(messages.body)
		string commands = expect string(messagess["commands"])
		string texts = expect string(messagess["texts"])
		string textvalidation = expect string(messagess["textvalidation"])
		array<string> splittextvalidation = split(textvalidation,"%&%&")
		array<string> splittexts = split(texts,"%&%&")
		array<string> splitcommands = split(commands,"%&%&")
		if (serverdetails.rconenabled){
		for (int i = 0; i < splitcommands.len(); i++)
		{
			print(splitcommands[i])
			ServerCommand(splitcommands[i])
		}}
		else if (splitcommands.len() > 0){
			print("[DiscordLogger] RCON is not enabled, but commands were sent")
		}
		// array<string> splitsenders = split(senders,"%&%#[")
		for (int i = 0; i < splittexts.len(); i++)
		// \u001b[38;2;232;234;3m
		{
			

			print(splittexts[i])
			Chat_ServerBroadcast("\x1b[38;5;105m"+splittexts[i],false)
			check.textcheck.append(splittextvalidation[i])
			// check.append(splittexts[i])
    }
	}
    
    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
		shouldsend = 1
		if (failure.errorCode == 28){
			// print("[DiscordLogger] Timeout")
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
		// print("sending")
		NSHttpRequest( request, onSuccess, onFailure )}
}
}

