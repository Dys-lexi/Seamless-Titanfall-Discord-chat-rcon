global function discordlogplaying

struct playerinfo {
	string playername = "Not found"
	int score = 0
	string team = "No team"
	int kills = 0
	int deaths = 0
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
