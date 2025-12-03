global function discordloghighlightplayerforplayerinit
global function discordlogaddnewhighlight

void function discordloghighlightplayerforplayerinit(){
    AddCallback_OnPlayerRespawned( readdhighlightjustincase )
}

struct {
    table <string,string> uidshighlights
} highlights

void function highlightplayertoplayer(string uid, string uid2){
    // discordlogsendmessage("eee "+ uid + "wqdq "+ uid2)
    entity player1
    entity player2
    foreach (player in GetPlayerArray()){
        if (player.GetUID() == uid){
            player1 = player
        }}
    foreach (player in GetPlayerArray()){
        if (player.GetUID() == uid2){
            player2 = player
        }}
    player2.SetBossPlayer(player1)
    HighlightContext highlight = GetHighlight( "interact_object_los" )
    // highlight.drawFuncId  = 3
    highlight.insideSlot = 101
    // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
    // Highlight_SetOwnedHighlight(player2,"interact_object_los") //interact_object_always
    // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
    highlight.paramVecs[0] = <1.0,0.2,0.7> //<0.8,0.4,0.2>
    highlight.adsFade = false
    // highlight.outlineRadius = 20.0
    player2.Highlight_SetCurrentContext( 3 )
	player2.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
	player2.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
	player2.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )

}

void function readdhighlightjustincase(entity player){
    foreach(key,value in highlights.uidshighlights){
        if (player.GetUID() == key || player.GetUID() == value){
        highlightplayertoplayer(key,value)}
    }
}

discordlogcommand function discordlogaddnewhighlight(discordlogcommand commandin) {
	if (commandin.commandargs.len() != 2){
		commandin.returncode = 404
		commandin.returnmessage = "Wrong number of args"
		return commandin
	}
    highlights.uidshighlights[commandin.commandargs[0]] <- commandin.commandargs[1]
    highlightplayertoplayer(commandin.commandargs[0],commandin.commandargs[1])
		commandin.returncode = 200
		commandin.returnmessage = "Highlighted " + commandin.commandargs[1]+ " to " + commandin.commandargs[0]
    return commandin
}