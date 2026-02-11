global function Lexi_killstat_Init


struct {
    string killstatVersion
    string host
    string protocol
    string serverId
    string serverName
    string token
    bool connected

    int matchId
    string gameMode
    string map
} file

string function sanitizePlayerName(string name) {
    

    if (name.len() > 3 && name[0] == 40 && name.find(")") != null  && name[1] > 47 && name[1] < 58) {
        string outputname = "";
        array <string> parts = split(name, ")");
        for (int i = 1; i < parts.len(); i++) {
            outputname += parts[i];
        }
        // print(outputname);
         return outputname;
    }
    // print(name);
    return name;
   
}

void function Lexi_killstat_Init() {
	if (GetConVarInt("discordloggingserverid") == 0){
		print("[DiscordLogger]Server ID not set, please set it in the console PLEASE FIX THIS")
		return
	} 
    // KcommandArr.append(new_KCommandStruct(["stats"], false,  realstats, 0, "Usage: !stats (player name or UID) => show your (or someone else's) stats on the server"))
    // KcommandArr.append(new_KCommandStruct(["bettertb"], false,  threadtbreal, 1, "actually good tb!!! woa!!! no way!!!"))
    file.host = GetConVarString("discordlogginghttpServer")
    // file.token = GetConVarString("nutone_token")
    file.connected = false
    file.serverName = GetConVarString("ns_server_name")
    file.serverId = GetConVarString("discordloggingserverid")
  
    //register to NUTONEAPI if default or invalid token
    // nutone_verify()

    // callbacks
    AddCallback_GameStateEnter(eGameState.Playing, killstat_Begin)
    AddCallback_OnPlayerKilled(killstat_Record)
    AddCallback_OnNPCKilled(killstat_Record)
    AddCallback_GameStateEnter(eGameState.Postmatch, killstat_End)
    AddCallback_OnClientConnected(JoinMessage)
}

string prefix = "\x1b[38;5;81m[NUTONEAPI]\x1b[0m "
// bool function realstats (entity player, array<string> args){
//     thread CommandStats(player,args)
//     return true
// }
// bool function threadtbreal (entity player, array<string> args){
//     thread actuallygoodbalance(player,args)
//     return true
// }

void function JoinMessage(entity player) {
    //Chat_ServerPrivateMessage(player, prefix + "This server collects data using the Nutone API. Check your data here: \x1b[34mhttps://nutone.okudai.dev/frontend" + player.GetPlayerName()+ "\x1b[0m", false, false)
    // thread CommandStats(player,[])
    runcommandondiscord("stats",{ name = player.GetUID()})
}

void function killstat_Begin() {
    file.gameMode = GameRules_GetGameMode()
    file.map = StringReplace(GetMapName(), "mp_", "")

    Log("Sending kill data to " + file.host + "/data")
}
// void function waitabit(entity player){
//     wait 1
//     CommandStats(player,[])
// }


// bool function actuallygoodbalance(entity player, array<string> args){
//     table<string,string> uids
//     table<string,entity> uidentmap
//     foreach(entity player in GetPlayerArray()){
//         string teammessage = "unknown"
//         int playerteam = player.GetTeam()
//         if( playerteam == 2 ){
//             teammessage = "imc"}
//         if( playerteam == 3 ){
//             teammessage = "mil"}
//             uids[player.GetUID()] <- teammessage
//             uidentmap[player.GetUID()] <- player
//         }
//     string url = file.host + "/autobalancedata"

//     void functionref( HttpRequestResponse ) onSuccess = void function (HttpRequestResponse response) : (uidentmap)
//     {
//                 for(int i = 0; i < GetPlayerArray().len(); i++){
//             SendHudMessageBuilder(GetPlayerArray()[i], "Teams have been betterbalanced by idk something", 255, 200, 200)
//         }
//         if (NSIsSuccessHttpCode(response.statusCode)) {
//             table responseTable = DecodeJSON(response.body)
//             table stats = expect table( responseTable.stats)
//             int counter = 2

//             while (counter + "" in stats){
        
//                 table people = expect table(stats[counter+""])
//                 foreach ( person in  people){
//                     table realperson = expect table(person)
//                     SetTeam(uidentmap[expect string(realperson.uid)], counter)
//                 }
//                 counter +=1
//                 // Chat_ServerPrivateMessage
//             }


//         }
//     }
//     void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure ) 
//     {
//         Chat_ServerBroadcast("sobbing balance brokey sob sob sob",false)
//     }

//     table params = {}
//     params[ "password" ] <- GetConVarString("discordloggingserverpassword")
//     params["players"] <- EncodeJSON(uids)
    
//     HttpRequest request
// 	request.method = HttpRequestMethod.POST
// 	request.url = url
// 	request.body = EncodeJSON(params)
//     NSHttpRequest(request, onSuccess, onFailure)
//     return true
    
// }
// bool function CommandStats(entity player, array<string> args) {
//     if (GetGameState() > eGameState.Playing) {
//         Chat_ServerPrivateMessage(player,"\x1b[38;2;220;0;0mStats not available at map end, wait for next map",false,false)
//         return true
//     }
//     entity targetPlayer = player
//     string nameOrUID = player.GetUID()
//     string targetName = player.GetPlayerName()
//     if (0 < args.len()) {
//         string searchStr = args[0]
//         targetName = args[0]
//         nameOrUID = args[0]

//         // PlayerSearchResult result = RunPlayerSearch(player, searchStr, PS_NOPRINT)
//         // if (result.kind == PlayerSearchResultKind.SINGLE) {
//         //     entity foundPlayer = result.players[0]
//         //     targetName = foundPlayer.GetPlayerName()
//         //     nameOrUID = foundPlayer.GetUID()
//         // }
//     }

//     string url = file.host + "/players/" + nameOrUID

//     void functionref( HttpRequestResponse ) onSuccess = void function (HttpRequestResponse response) : (player, targetName, nameOrUID,args)
//     {
//         // needed if player DC's before request finish
//         if (!IsValid(player)) {
//             return
//         }

//         if (NSIsSuccessHttpCode(response.statusCode)) {
//             table responseTable = DecodeJSON(response.body)
//             string name = ""
//             string uid = ""
//             int kills = 0
//             int deaths = 0
//             int counter = 0
//             // float kd = 1.0
//             bool shouldreturn = false
//             while (counter + "" in responseTable){
//                 if (args.len() == 0){
//                 Chat_ServerPrivateMessage(player,expect string(responseTable[counter+""]),false,false)}
//                 else{
//                     Chat_ServerBroadcast(expect string(responseTable[counter+""]),false)
//                 }
//                 counter +=1
//                 shouldreturn = true
//                 // Chat_ServerPrivateMessage
//             }
//             if (shouldreturn){
//                 return
//             }
        
//             if ("name" in responseTable) {
//                 name = expect string(responseTable["name"])
//             }

//             if ("uid" in responseTable) {
//                 uid = expect string(responseTable["uid"])
//             }

//             if ("total" in responseTable){
//                 if ("kills" in expect table(responseTable["total"])) {
//                     kills = expect int(expect table(responseTable["total"])["kills"])
//                 }
//                 if ("deaths" in expect table(responseTable["total"])) {
//                     deaths = expect int(expect table(responseTable["total"])["deaths"])
//                 }
//             }

//             // TODO: figure out how to extract float
//             //if ("kd" in responseTable) {
//             //    kd = expect float(responseTable["kd"])
//             //    Log("[CommandStats] kd = " + kd)
//             //}


//             string prefix = "you have"
//             if (player.GetUID() != uid) {
//                 prefix = name + " has"
//             }

//             float kd = kills / max(deaths, 1)
//             // file.nutonePlayerKds[uid] <- kd // Store for !teambalance
//             string msg = format("%s %d kills and %d deaths (%.2f K/D)", prefix, kills, deaths, kd)
//             Chat_ServerPrivateMessage(player, msg,false,false)
//         } else {
//             Chat_ServerPrivateMessage(player,format("could not find stats for '%s'", targetName),false,false)
//         }
//     }
//     void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure ) : (player, targetName)
//     {
//         Chat_ServerPrivateMessage(player, "could not find stats for " + targetName,false,false)
//     }

//     table params = {}
//     params[ "server_id" ] <- file.serverId
//     // if (args.len() == 0) {
//     //     array<entity> attackerWeapons = player.GetMainWeapons()
//     //     entity aw1 = GetNthWeapon(attackerWeapons, 0)
//     //     Chat_ServerPrivateMessage(player,GetWeaponName(aw1),false,false)
//     // params[ "current_weapon"] <- GetWeaponName(aw1)}
//     HttpRequest request
// 	request.method = HttpRequestMethod.POST
// 	request.url = url
// 	request.body = EncodeJSON(params)
//     NSHttpRequest(request, onSuccess, onFailure)

//     return true
// }



void function killstat_Record(entity victim, entity attacker, var damageInfo) {
    // printt("beep boop bop")
    if ((!victim.IsPlayer() && !attacker.IsPlayer() && !attacker.GetBossPlayer() && !victim.GetBossPlayer())  || GetGameState() != eGameState.Playing ) {
        // printt("here")
        // Chat_PrivateMessage(victim,victim, "PRIVATE MESSAGE"+(attacker.GetClassName()) +(!victim.IsPlayer() && !attacker.IsPlayer()) ,false)
            return}
    // printt("HEREE")
    // Chat_PrivateMessage(victim,victim, "PRIVATE MESSAGwwwwE"+(attacker.GetClassName()) +(!victim.IsPlayer() && !attacker.IsPlayer()) ,false)
    table values = {}

    vector attackerPos = attacker.GetOrigin()
    vector victimPos = victim.GetOrigin()
    // Chat_ServerBroadcast(attacker.GetBossPlayer()+"e")
    // Chat_ServerBroadcast(victim.GetBossPlayer()+"e")
    

    if (attacker.IsPlayer()) {
        values["attacker_name"] <- sanitizePlayerName(discordloggetplayername(attacker))
        values["attacker_id"] <- attacker.GetUID()
        values["attacker_titan"] <- GetTitan(attacker)
    }
    else if (attacker.GetBossPlayer()) {
        entity boss = attacker.GetBossPlayer()
        values["attacker_name"] <- sanitizePlayerName(discordloggetplayername(boss))
        values["attacker_id"] <- boss.GetUID()
        values["attacker_titan"] <- GetTitan(attacker,true)
    }

    if (victim.IsPlayer()) {
        values["victim_name"] <- sanitizePlayerName(discordloggetplayername(victim))
        values["victim_id"] <- victim.GetUID()
        values["victim_titan"] <- GetTitan(victim)
    }
    else if (victim.GetBossPlayer()) {
        entity boss = victim.GetBossPlayer()
        values["victim_name"] <- sanitizePlayerName(discordloggetplayername(boss))
        values["victim_id"] <- boss.GetUID()
        values["victim_titan"] <- GetTitan(victim,true)
    }
    if (attacker.IsPlayer() || attacker.IsNPC()){
            array<entity> attackerWeapons = attacker.GetMainWeapons()

    array<entity> attackerOffhandWeapons = attacker.GetOffhandWeapons()
        attackerWeapons.sort(MainWeaponSort)
        
  

        entity aw1 = GetNthWeapon(attackerWeapons, 0)
        entity aw2 = GetNthWeapon(attackerWeapons, 1)
        entity aw3 = GetNthWeapon(attackerWeapons, 2)
        entity aow1 = GetNthWeapon(attackerOffhandWeapons, 0)
        entity aow2 = GetNthWeapon(attackerOffhandWeapons, 1)
        entity aow3 = GetNthWeapon(attackerOffhandWeapons, 2)
            values["attacker_weapon_1"] <- GetWeaponName(aw1)
    values["attacker_weapon_2"] <- GetWeaponName(aw2)
    values["attacker_weapon_3"] <- GetWeaponName(aw3)
    values["attacker_offhand_weapon_1"] <- GetWeaponName(aow1)
    values["attacker_offhand_weapon_2"] <- GetWeaponName(aow2)
    values["attacker_current_weapon"] <- GetWeaponName(attacker.GetLatestPrimaryWeapon())

    }
    if (victim.IsPlayer() || victim.IsNPC()){
       array<entity> victimOffhandWeapons = victim.GetOffhandWeapons()

      array<entity> victimWeapons = victim.GetMainWeapons()
victimWeapons.sort(MainWeaponSort)

          entity vw1 = GetNthWeapon(victimWeapons, 0)
        entity vw2 = GetNthWeapon(victimWeapons, 1)
        entity vw3 = GetNthWeapon(victimWeapons, 2)
            entity vow1 = GetNthWeapon(victimOffhandWeapons, 0)
    entity vow2 = GetNthWeapon(victimOffhandWeapons, 1)
    entity vow3 = GetNthWeapon(victimOffhandWeapons, 2)
            values["victim_weapon_1"] <- GetWeaponName(vw1)
    values["victim_weapon_2"] <- GetWeaponName(vw2)
    values["victim_weapon_3"] <- GetWeaponName(vw3)
    values["victim_offhand_weapon_1"] <- GetWeaponName(vow1)
    values["victim_offhand_weapon_2"] <- GetWeaponName(vow2)
    values["victim_current_weapon"] <- GetWeaponName(victim.GetLatestPrimaryWeapon())

    }
    // values["victim_name"] <- sanitizePlayerName(victim.GetPlayerName())
    // values["victim_id"] <- victim.GetUID()
    // values["victim_titan"] <- GetTitan(victim)
    // Chat_PrivateMessage(attacker,attacker, "PRIVATE MESSAGE"+attacker.GetClassName,false)
    values["match_id"] <- GetConVarString("discordloggingmatchid")
    values["server_id"] <- file.serverId
    // values["server_name"] <- file.serverName
    values["game_mode"] <- file.gameMode
    values["game_time"] <- Time()
    values["map"] <- file.map
    
    
    

    
    values["attacker_x"] <- attackerPos.x
    values["attacker_y"] <- attackerPos.y
    values["attacker_z"] <- attackerPos.z
    values["timeofkill"] <- GetUnixTimestamp()

    // values["victim_current_weapon"] <- GetWeaponName(victim.GetLatestPrimaryWeapon())
    // values["victim_weapon_1"] <-  GetWeaponName(vw1)
    // values["victim_weapon_2"] <- GetWeaponName(vw2)
    // values["victim_weapon_3"] <- GetWeaponName(vw3)
    // values["victim_offhand_weapon_1"] <- GetWeaponName(vow1)
    // values["victim_offhand_weapon_2"] <- GetWeaponName(vow2)

    values["victim_x"] <- victimPos.x
    values["victim_y"] <- victimPos.y
    values["victim_z"] <- victimPos.z
    values["password"] <- GetConVarString("discordloggingserverpassword")
    values["victim_type"] <- victim.GetClassName()
    values["attacker_type"] <-attacker.GetClassName()
    // values["attacker_title"] <- attacker.Title()

    int damageSourceId = DamageInfo_GetDamageSourceIdentifier(damageInfo)
    string damageName = DamageSourceIDToString(damageSourceId)
    values["cause_of_death"] <- damageName
   
    array<string> typedMods
    if (IsValid(DamageInfo_GetWeapon(damageInfo))){
        typedMods = DamageInfo_GetWeapon(damageInfo).GetMods()

    }
    else if (IsValid(attacker) &&  attacker.IsPlayer()){
        foreach (entity weapon  in attacker.GetMainWeapons()){
  
            if (weapon.GetWeaponClassName() == damageName){
                typedMods = weapon.GetMods()
            }
        }
        foreach (entity  weapon in attacker.GetOffhandWeapons() ){
    
            if (weapon.GetWeaponClassName() == damageName){
                typedMods = weapon.GetMods()
            }
        }
    }
    array untypedMods = []
    foreach (mod in typedMods){
        untypedMods.append(mod)}
        values["modsused"] <- untypedMods
    
    float dist = Distance(attacker.GetOrigin(), victim.GetOrigin())
    values["distance"] <- dist
    // printt("MODSSSS"+GetWeaponMods(DamageInfo_GetWeapon( damageInfo )))
    // PrintTable(untypedMods)
    HttpRequest request
    request.method = HttpRequestMethod.POST
    request.url = file.host + "/data"
    request.headers = {Token = [file.token]}
    request.body = EncodeJSON(values)

    void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse response )
    {
        if(response.statusCode == 200 || response.statusCode == 201){
            print("[NUTONEAPI] Kill data sent!")
        }else{
            print("[NUTONEAPI][WARN] Couldn't send kill data, status " + response.statusCode)
            print("[NUTONEAPI][WARN] " + response.body )
        }
    }

    void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
    {
        print("[NUTONEAPI][WARN]  Couldn't send kill data")
        print("[NUTONEAPI][WARN] " + failure.errorMessage )
    }
    // Chat_PrivateMessage(victim,victim, "PRIVATE MESSAGE"+(attacker.GetClassName()) +(!victim.IsPlayer() && !attacker.IsPlayer()) ,false)
    // printt("HEREEww")
    NSHttpRequest(request, onSuccess, onFailure)
}

void function killstat_End() {
    Log("-----END KILLSTAT-----")
}




array<int> MAIN_DAMAGE_SOURCES = [
    // primaries
	eDamageSourceId.mp_weapon_car,
	eDamageSourceId.mp_weapon_r97,
	eDamageSourceId.mp_weapon_alternator_smg,
	eDamageSourceId.mp_weapon_hemlok_smg,
	eDamageSourceId.mp_weapon_hemlok,
	eDamageSourceId.mp_weapon_vinson,
	eDamageSourceId.mp_weapon_g2,
	eDamageSourceId.mp_weapon_rspn101,
	eDamageSourceId.mp_weapon_rspn101_og,
	eDamageSourceId.mp_weapon_esaw,
	eDamageSourceId.mp_weapon_lstar,
	eDamageSourceId.mp_weapon_lmg,
	eDamageSourceId.mp_weapon_shotgun,
	eDamageSourceId.mp_weapon_mastiff,
	eDamageSourceId.mp_weapon_dmr,
	eDamageSourceId.mp_weapon_sniper,
	eDamageSourceId.mp_weapon_doubletake,
	eDamageSourceId.mp_weapon_pulse_lmg,
	eDamageSourceId.mp_weapon_smr,
	eDamageSourceId.mp_weapon_softball,
	eDamageSourceId.mp_weapon_epg,
	eDamageSourceId.mp_weapon_shotgun_pistol,
	eDamageSourceId.mp_weapon_wingman_n,

    // secondaries
	eDamageSourceId.mp_weapon_smart_pistol,
	eDamageSourceId.mp_weapon_wingman,
	eDamageSourceId.mp_weapon_semipistol,
	eDamageSourceId.mp_weapon_autopistol,

    // anti-titan
	eDamageSourceId.mp_weapon_mgl,
	eDamageSourceId.mp_weapon_rocket_launcher,
	eDamageSourceId.mp_weapon_arc_launcher,
	eDamageSourceId.mp_weapon_defender
]
// Should sort main weapons in following order:
// 1. primary
// 2. secondary
// 3. anti-titan
int function MainWeaponSort(entity a, entity b) {
    int aID = a.GetDamageSourceID()
    int bID = b.GetDamageSourceID()

    int aIdx = MAIN_DAMAGE_SOURCES.find(aID)
    int bIdx = MAIN_DAMAGE_SOURCES.find(bID)

    if (aIdx == bIdx) {
        return 0
    } else if (aIdx != -1 && bIdx == -1) {
        return -1
    } else if (aIdx == -1 && bIdx != -1) {
        return 1
    }

    return aIdx < bIdx ? -1 : 1
}

int function WeaponNameSort(entity a, entity b) {
    return SortStringAlphabetize(a.GetWeaponClassName(), b.GetWeaponClassName())
}

entity function GetNthWeapon(array<entity> weapons, int index) {
    return index < weapons.len() ? weapons[index] : null
}

string function GetWeaponName(entity weapon) {
    string s = "null"
    if (weapon != null) {
        s = weapon.GetWeaponClassName()
    }
    return s
}

string function GetTitan(entity player, bool getboss = false) {
    if(!player.IsTitan()) return "null"
    if (getboss){
    if (discordlogpullplayerstat(player.GetBossPlayer().GetUID(),"togglebrute") == "True" && (player.GetModelName() == $"models/titans/light/titan_light_northstar_prime.mdl" || player.GetModelName() == $"models/titans/light/titan_light_raptor.mdl")){
        return "brute"
    }}
    else{
    if (discordlogpullplayerstat(player.GetUID(),"togglebrute") == "True" && (player.GetModelName() == $"models/titans/light/titan_light_northstar_prime.mdl" || player.GetModelName() == $"models/titans/light/titan_light_raptor.mdl")){
        return "brute"
    }   
    }
    if (getboss){
    if (discordlogpullplayerstat(player.GetBossPlayer().GetUID(),"toggleexpi") == "True" && (player.GetModelName() == $"models/titans/medium/titan_medium_vanguard.mdl" )){
        return "expedition"
    }}
    else{
    if (discordlogpullplayerstat(player.GetUID(),"toggleexpi") == "True" && (player.GetModelName() == $"models/titans/medium/titan_medium_vanguard.mdl")){
        return "expedition"
    }   
    }
    if (getboss){
    if (discordlogpullplayerstat(player.GetBossPlayer().GetUID(),"tgrap") == "True" && (player.GetModelName() == $"models/titans/light/titan_light_locust.mdl" || player.GetModelName() == $"models/titans/light/titan_light_ronin_prime.mdl")){
        return "tgrap"
    }}
    else{
    if (discordlogpullplayerstat(player.GetUID(),"tgrap") == "True" && (player.GetModelName() == $"models/titans/light/titan_light_locust.mdl" || player.GetModelName() == $"models/titans/light/titan_light_ronin_prime.mdl")){
        return "tgrap"
    }   
    }
    return GetTitanCharacterName(player)
}
//  ( (discordlogpullplayerstat(player.GetUID(),"tgrap") == "True") &&(titan.GetModelName() == $"models/titans/light/titan_light_locust.mdl" || titan.GetModelName() == $"models/titans/light/titan_light_ronin_prime.mdl"))
// string function Anonymize(entity player) {
//     return "null" // unused
// }

void function Log(string s) {
    print("[NUTONEAPI] " + s)
}

// void function nutone_verify(){
//     HttpRequest request
//     request.method = HttpRequestMethod.POST
//     request.url = file.host + "/auth"
//     request.headers = {Token = [file.token]}
//     void functionref( HttpRequestResponse ) onSuccess = void function ( HttpRequestResponse response )
//     {
//         if(response.statusCode == 200){
//             print("[NUTONEAPI] NUTONEAPI Online !")
//             file.connected = true
//         }else{
//             print("[NUTONEAPI] NUTONEAPI login failed")
//             print("[NUTONEAPI] " + response.body )

//         }
//     }

//     void functionref( HttpRequestFailure ) onFailure = void function ( HttpRequestFailure failure )
//     {
//         print("[NUTONEAPI] NUTONEAPI login failed")
//         print("[NUTONEAPI] " + failure.errorMessage )
//     }

//     NSHttpRequest(request, onSuccess, onFailure)
// }
