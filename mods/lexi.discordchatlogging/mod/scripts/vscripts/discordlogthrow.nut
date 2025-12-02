global function discordlogthrowplayer_init
global function discordlogthrowplayer

void function discordlogthrowplayer_init()
{
	AddDiscordRconCommand( discordlogthrowplayer )
}

discordlogcommand function discordlogthrowplayer(discordlogcommand commandin) {
    if (discordlogcheck("throw", true, commandin)){
            return commandin;
    }
    commandin.commandmatch = true
	if (commandin.commandargs.len() != 1)
	{
		commandin.returnmessage = "Wrong number of args";
		commandin.returncode = 400
		return commandin;
	}

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
		commandin.returncode = 200
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
			commandin.returncode = 200
		}
		else {
			// check.commandcheck[validation] <- args + ": Player not found"}
            commandin.returnmessage = commandin.command+": Player not found"
			commandin.returncode = 401
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