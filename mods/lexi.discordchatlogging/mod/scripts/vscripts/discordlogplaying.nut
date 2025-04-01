global function discordlogplaying
global function discordlogplayingpoll

struct playerinfo {
	string playername = "Not found"
	int score = 0
	string team = "No team"
	int kills = 0
	int deaths = 0
}

struct playerinfopoll {
	string playername = "Not found"
	int score = 0
	string team = "No team"
	int kills = 0
	int deaths = 0
	int titankills = 0
	int npckills = 0
	string uid = "0"
}

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

discordlogcommand function discordlogplayingpoll(discordlogcommand commandin) {
    if (discordlogcheck("playingpoll", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	array<entity> players = GetPlayerArray()
	table playerlist
	foreach (entity player in players){
		playerinfopoll playerinfoe
		if (player != null){
			playerinfoe.playername = player.GetPlayerName()
			playerinfoe.uid = player.GetUID()
			// print(PGS_SCORE)
			playerinfoe.score = player.GetPlayerGameStat(8)
			playerinfoe.kills = player.GetPlayerGameStat(1)
			playerinfoe.deaths = player.GetPlayerGameStat(2)
			// print(player.GetPlayerGameStat(PGS_PING)/100000)
			// playerinfoe.ping = string(player.GetPlayerGameStat(12))+ " " + string(player.GetPlayerGameStat(0)) + " " + string(player.GetPlayerGameStat(1)) + " " + string(player.GetPlayerGameStat(2)) + " " + string(player.GetPlayerGameStat(3)) + " " + string(player.GetPlayerGameStat(4)) + " " + string(player.GetPlayerGameStat(5)) + " " + string(player.GetPlayerGameStat(6)) + " " + string(player.GetPlayerGameStat(7)) + " " + string(player.GetPlayerGameStat(8)) + " " + string(player.GetPlayerGameStat(9)) + " " + string(player.GetPlayerGameStat(10)) + " " + string(player.GetPlayerGameStat(11)) + " " + string(player.GetPlayerGameStat(12)) + " " + string(player.GetPlayerGameStat(13)) + " " + string(player.GetPlayerGameStat(14)) + " " + string(player.GetPlayerGameStat(15)) + " " + string(player.GetPlayerGameStat(16)) + " " + string(player.GetPlayerGameStat(17)) + " " + string(player.GetPlayerGameStat(18)) + " " + string(player.GetPlayerGameStat(PGS_PING))
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
			// print(playerinfoe.playername)
			// string playerinforeal = EncodeJSON(playerinfoe)
			// I really hate this fake json list thing, but I don't want to throw out the table design here, so it's staying for now :(
			playerlist[playerinfoe.uid] <- [playerinfoe.score,playerinfoe.team,playerinfoe.kills,playerinfoe.deaths,playerinfoe.playername,playerinfoe.titankills,playerinfoe.npckills]

		}
	}
		int mtimeleft = 0
			try{
				mtimeleft = GameTime_TimeLeftSeconds()
			}
            catch (e){
                mtimeleft = 0
            }
	playerlist["meta"] <- [GetMapName(),mtimeleft]

    commandin.returnmessage = EncodeJSON(playerlist)
	commandin.returncode = 200
    return commandin;
}


discordlogcommand function discordlogplaying(discordlogcommand commandin) {
    if (discordlogcheck("playing", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	array<entity> players = GetPlayerArray()
	table playerlist
	foreach (entity player in players){
		playerinfo playerinfoe
		if (player != null){
			playerinfoe.playername = player.GetPlayerName()
			// print(PGS_SCORE)
			playerinfoe.score = player.GetPlayerGameStat(8)
			playerinfoe.kills = player.GetPlayerGameStat(1)
			playerinfoe.deaths = player.GetPlayerGameStat(2)
			// print(player.GetPlayerGameStat(PGS_PING)/100000)
			// playerinfoe.ping = string(player.GetPlayerGameStat(12))+ " " + string(player.GetPlayerGameStat(0)) + " " + string(player.GetPlayerGameStat(1)) + " " + string(player.GetPlayerGameStat(2)) + " " + string(player.GetPlayerGameStat(3)) + " " + string(player.GetPlayerGameStat(4)) + " " + string(player.GetPlayerGameStat(5)) + " " + string(player.GetPlayerGameStat(6)) + " " + string(player.GetPlayerGameStat(7)) + " " + string(player.GetPlayerGameStat(8)) + " " + string(player.GetPlayerGameStat(9)) + " " + string(player.GetPlayerGameStat(10)) + " " + string(player.GetPlayerGameStat(11)) + " " + string(player.GetPlayerGameStat(12)) + " " + string(player.GetPlayerGameStat(13)) + " " + string(player.GetPlayerGameStat(14)) + " " + string(player.GetPlayerGameStat(15)) + " " + string(player.GetPlayerGameStat(16)) + " " + string(player.GetPlayerGameStat(17)) + " " + string(player.GetPlayerGameStat(18)) + " " + string(player.GetPlayerGameStat(PGS_PING))
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
			// print(playerinfoe.playername)
			playerlist[playerinfoe.playername] <- [playerinfoe.score,playerinfoe.team,playerinfoe.kills,playerinfoe.deaths]

		}
	}
		int mtimeleft = 0
			try{
				mtimeleft = GameTime_TimeLeftSeconds()
			}
            catch (e){
                mtimeleft = 0
            }
	playerlist["meta"] <- [MAP_NAME_TABLE[GetMapName()],mtimeleft]

    commandin.returnmessage = EncodeJSON(playerlist)
	commandin.returncode = 200
    return commandin;
}
