global function discordlogthrowplayer

discordlogcommand function discordlogthrowplayer(discordlogcommand commandin) {
    if (discordlogcheck("throw", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	array<string> splitargs = commandin.commandargs
	if (splitargs[0] == "all"){
		print("throwing all players")
		array<entity> players = GetPlayerArray()
		foreach (entity player in players){
			if (player != null){
				vector velocity = player.GetVelocity()
				velocity.z = 10000
				PushEntWithVelocity(player,velocity)
			}
		}
		// check.commandcheck[validation] <- args + ": All players thrown"
        commandin.returnmessage = commandin.command+": All players thrown"
	}
	else {
		entity player = findname(splitargs[0])
		if (player != null){
			print("throwing "+player.GetPlayerName())
			vector velocity =player.GetVelocity()
			velocity.z = 10000
			PushEntWithVelocity(player,velocity)
			// check.commandcheck[validation] <-  args + ": "+player.GetPlayerName()+" thrown"
            commandin.returnmessage = commandin.command+": "+player.GetPlayerName()+" thrown"
		}
		else {
			// check.commandcheck[validation] <- args + ": Player not found"}
            commandin.returnmessage = commandin.command+": Player not found"
	}

    }
    return commandin;
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