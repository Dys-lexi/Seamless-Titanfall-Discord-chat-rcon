global function discordlogsimplesay

discordlogcommand function discordlogsimplesay(discordlogcommand commandin) {
    if (discordlogcheck("simplesay", commandin)){
            return commandin;
    }
    commandin.commandmatch = true
    string message = ""
    for(int i = 0; i < commandin.commandargs.len(); i++)
    {
        message += commandin.commandargs[i] + " "
    }
    Chat_ServerBroadcast(message,false)
    commandin.returnmessage = "Message sent"
    commandin.returncode = 200
    return commandin;
}