global function discordlogtb
global function discordlogplayerfinder

discordlogcommand function discordlogplayerfinder(discordlogcommand commandin) {
    if (discordlogcheck("playerfinder", commandin) && discordlogcheck("teambalance", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	array<entity> players = GetPlayerArray()
	table playerlist
	foreach (entity player in players){
		if (player != null){

            array<string> recenthurts
            if (IsAlive(player) &&  GetPlayerArray().len() > 1){
                array<entity> otherPlayers = GetPlayerArray()
                for(int i = 0; i < otherPlayers.len(); i++){
                    if(otherPlayers[i] == player){
                        otherPlayers.remove(i)
                        break
                    }
                }
                recenthurts.append(GetClosest(otherPlayers,player.GetOrigin()).GetUID())
            float recent = Time() - 12
            foreach ( history in player.e.recentDamageHistory )
            {
                if ( history.time < recent )
                    break

                if ( history.attacker.IsPlayer() && IsAlive(history.attacker) )
                    recenthurts.append(history.attacker.GetUID())
            }
            }

			playerlist[player.GetUID()] <- {scary = recenthurts,team = player.GetTeam()}

		}
	}
    commandin.returnmessage = EncodeJSON(playerlist)
	commandin.returncode = 200
    return commandin;
}

// discordlogcommand function getconvar(discordlogcommand commandin) {
//     if (discordlogcheck("getconvar", commandin)){
//             return commandin;
//     }
//     commandin.commandmatch = true
//     if (commandin.commandargs.len() != 1)
//     {
//         commandin.returnmessage = "Wrong number of args";
//         commandin.returncode = 400
//         return commandin;
//     }
//     string convar = GetConVarString(commandin.commandargs[0]);
//     if (convar == "")
//     {
//         commandin.returnmessage = "Convar not found, or is empty";
//         commandin.returncode = 404
//         return commandin;
//     }
//     commandin.returnmessage = "Convar: " + commandin.commandargs[0] + " = " + convar;
//     commandin.returncode = 200

//     return commandin;
// }

discordlogcommand function discordlogtb(discordlogcommand commandin) {
    if (discordlogcheck("bettertb", commandin) ){
            return commandin;
    }
    commandin.commandmatch = true

    table<string,entity> uidentmap
    foreach(entity player in GetPlayerArray()){

            uidentmap[player.GetUID()] <- player
        }
	int prevarg = 0
	for(int i = 0; i < commandin.commandargs.len(); i++) {
		if ((i+1) % 2) {
			prevarg = commandin.commandargs[i].tointeger()
		}
		else if ( GetPlayerArray().contains(uidentmap[ commandin.commandargs[i]]) ){
			SetTeam(uidentmap[ commandin.commandargs[i]], prevarg)
		}
		
	}


        
  
                // Chat_ServerPrivateMessage
            

    commandin.returnmessage = "Balance ran!"
	commandin.returncode = 200
    return commandin;

    
}