global function discordloghighlightplayerforplayerinit
global function discordlogaddnewhighlight

struct {
    table <string,string> uidshighlights
} highlights

void function discordloghighlightplayerforplayerinit(){
    AddCallback_OnPlayerRespawned( readdhighlightjustincase )
    // highlights.uidshighlights["1012640166434"] <- "2509670718"
    // highlights.uidshighlights["2509670718"] <- "1012640166434"

    // thread highlightplayertoplayer("1012640166434","2509670718")
    // thread highlightplayertoplayer("2509670718","1012640166434")
}



void function highlightplayertoplayer(string uid, string uid2){
    // wait 10
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

    thread actuallyhighlight(player1,player2)


    
}

    void function actuallyhighlight(entity player1,entity player2){
    
	player1.EndSignal(  "OnDestroy" )
	player1.EndSignal(  "OnDeath" )
    player2.SetBossPlayer(player1)
    HighlightContext highlight = GetHighlight( "enemy_boss_bounty" )
    // highlight.drawFuncId  = 3
    highlight.insideSlot = 106
    // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
    // Highlight_SetOwnedHighlight(player2,"interact_object_los") //interact_object_always
    // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
    highlight.paramVecs[0] = <1.0,0.2,0.7> //<0.8,0.4,0.2>

    highlight.adsFade = false
    highlight.outlineRadius = 7.0
    player2.Highlight_SetCurrentContext( 3 )
	player2.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
	player2.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
	player2.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
    WaitFrame()
    player2.ClearBossPlayer()
    // for (int i = 0; i < 10; i++){   
    //     wait 1
    //     Highlight_ClearOwnedHighlight(player2)
    //     HighlightContext highlight = GetHighlight( "enemy_boss_bounty" )
    //     highlight.paramVecs[0] = <RandomFloatRange( 0.0, 1.0 ),RandomFloatRange( 0.0, 1.0 ),RandomFloatRange( 0.0, 1.0 )>
    //     player2.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
    //     player2.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
    //     player2.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
    // }
    wait 7
    Highlight_ClearOwnedHighlight(player2)
    player2.SetBossPlayer(player1)

    // highlight.drawFuncId  = 3
    highlight.insideSlot = 112
    // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
    // Highlight_SetOwnedHighlight(player2,"interact_object_los") //interact_object_always
    // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
    highlight.paramVecs[0] = <1.0,0.2,0.7> //<0.8,0.4,0.2>
    highlight.adsFade = false
    highlight.outlineRadius = 1.0
    player2.Highlight_SetCurrentContext( 3 )
	player2.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
	player2.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
	player2.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
    WaitFrame()
    player2.ClearBossPlayer()
    }

void function readdhighlightjustincase(entity player){
    foreach(key,value in highlights.uidshighlights){
        if (player.GetUID() == key || player.GetUID() == value){
        thread highlightplayertoplayer(key,value)
        
        }

    }
}

discordlogcommand function discordlogaddnewhighlight(discordlogcommand commandin) {
	if (commandin.commandargs.len() != 2){
		commandin.returncode = 404
		commandin.returnmessage = "Wrong number of args"
		return commandin
	}
    highlights.uidshighlights[commandin.commandargs[0]] <- commandin.commandargs[1]
    thread highlightplayertoplayer(commandin.commandargs[0],commandin.commandargs[1])
		commandin.returncode = 200
		commandin.returnmessage = "Highlighted " + commandin.commandargs[1]+ " to " + commandin.commandargs[0]
    return commandin
}