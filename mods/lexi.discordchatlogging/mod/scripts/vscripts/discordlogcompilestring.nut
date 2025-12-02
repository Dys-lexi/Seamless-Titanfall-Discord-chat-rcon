untyped
global function discordlogcompilestring_init
global function discordlogcompilestring

void function discordlogcompilestring_init()
{
	AddDiscordRconCommand( discordlogcompilestring )
}

discordlogcommand function discordlogcompilestring( discordlogcommand commandin )
{
	if ( discordlogcheck( "compilestring", true, commandin ) )
		return commandin

	commandin.commandmatch = true

	string commandtostring
	foreach ( string command in commandin.commandargs )
		if ( commandtostring == "" )
			commandtostring = command
		else
			commandtostring += " " + command

	try
	{
		compilestring( commandtostring )()
	}
	catch( error )
	{
		commandin.returnmessage = "Command failed. Error message: " + error
		commandin.returncode = -3

		return commandin
	}

	commandin.returnmessage = "Command successful."
	commandin.returncode = 200

	return commandin
}