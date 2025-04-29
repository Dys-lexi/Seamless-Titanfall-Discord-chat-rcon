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
    thread discordlogsendmessage(message)
    commandin.returnmessage = "Message sent"
    commandin.returncode = 200
    return commandin;
}