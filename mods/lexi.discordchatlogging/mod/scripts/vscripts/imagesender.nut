global function discordlogsendimage

discordlogcommand function discordlogsendimage(discordlogcommand commandin) {
    if (commandin.commandargs.len() < 1)
    {
        commandin.returnmessage = "Wrong number of args";
        commandin.returncode = 400
        return commandin;
    }
    thread discordlogsendmultiplemessages(commandin.commandargs)
   
    commandin.returnmessage = "Image sent"
    commandin.returncode = 200
    return commandin;
}

void function discordlogsendmultiplemessages(array<string> messages){
	foreach (string message in messages){
        Chat_ServerBroadcast(message, false)
	}
}
