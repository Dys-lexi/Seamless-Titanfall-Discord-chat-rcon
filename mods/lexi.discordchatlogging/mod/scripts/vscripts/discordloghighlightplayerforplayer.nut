global function discordloghighlightplayerforplayerinit
global function discordlogaddnewhighlight

struct {
    table <string,array<string> > uidshighlights //this is the oopsie, what if one player is dueling more than one?
} highlights

void function addnewuidpairtotablething(string uid1,string uid2){
    array<string> adder = []
    if ((uid1 in highlights.uidshighlights)){
        adder = highlights.uidshighlights[uid1]
    }
    adder.append(uid2)
    highlights.uidshighlights[uid1] <- adder
}



void function discordloghighlightplayerforplayerinit(){
    RegisterSignal( "discordlogsignalstop" )
    AddCallback_OnClientConnected( readdhighlightjustincase )
    AddCallback_OnPlayerRespawned( readdhighlightjustincase )
    AddCallback_OnPilotBecomesTitan(readdhighlightjustincasetitan)
    AddCallback_OnTitanBecomesPilot( readdhighlightjustincasetitan )
    // addnewuidpairtotablething("1012640166434" , "2509670718")
    // addnewuidpairtotablething("2509670718" , "1012640166434")

    // thread highlightplayertoplayer("1012640166434","2509670718")
    // thread highlightplayertoplayer("2509670718","1012640166434")
}
void function readdhighlightjustincasetitan(entity player,entity titan){
    table<string,array<string> > highlightsthings
    foreach(key,value in highlights.uidshighlights){
        if ( key == player.GetUID()){
            highlightsthings[key] <- value
        }
        if (value.contains(player.GetUID())){
            highlightsthings[key] <- [player.GetUID()]
        }
    }
    thread highlightplayertoplayer("titanhighlight",highlightsthings)
}

void function readdhighlightjustincase(entity player){
    table<string,array<string> > highlightsthings
    foreach(key,value in highlights.uidshighlights){
        if ( key == player.GetUID()){
            highlightsthings[key] <- value
        }
        if (value.contains(player.GetUID())){
            highlightsthings[key] <- [player.GetUID()]
        }
    }
    thread highlightplayertoplayer("tempwallhacks",highlightsthings)
}

void function highlightplayertoplayer(string typeofhighlight,table<string,array<string> >  highlightsthings = {},table<entity,array<entity> >  highlightsthingsentitys = {}){
    // wait 10
    // discordlogsendmessage("eee "+ uid + "wqdq "+ uid2)
    table<entity,array<entity> > entityhighlights
    foreach (key,value in highlightsthings){
        foreach (player in GetPlayerArray()){
        if (key == (player.GetUID())){
            entity realplayer = player
            entityhighlights[player] <- []
            // break
                foreach (thing in value){
                    foreach (player in GetPlayerArray()){
                        if (thing == (player.GetUID())){
                            entityhighlights[realplayer].append(player)
                    }}
        }
        }}

    }
    foreach (key, value in highlightsthingsentitys){
        entityhighlights[key] <- value
    }
    
    WaitFrame()
    // if (!IsValid(player1) || !IsValid(player2)){
    //     return
    // }


    
    // player1.Signal("discordlogsignalstop")
    if (typeofhighlight == "tempwallhacks"){
     actuallyhighlight(entityhighlights,"enemy_boss_bounty",<1.0,0.2,0.7>,106,7.0)
    wait 5
     actuallyhighlight(entityhighlights,"enemy_boss_bounty",<1.0,0.2,0.7>,112,1.0)}

    if (typeofhighlight == "titanhighlight"){
    // thread actuallyhighlight(entityhighlights,"enemy_boss_bounty",<1.0,0.2,0.7>,106,7.0)
    // wait 5
     actuallyhighlight(entityhighlights,"enemy_boss_bounty",<1.0,0.2,0.7>,112,1.0)}
    
    // foreach (npc in GetNPCArray()){
    // thread actuallyhighlight(player1,npc,shouldhighlight)}
}
    
    void function actuallyhighlight(table<entity,array<entity> > entityhighlights, string highlightname, vector colour, int insideslot, float radius){
    
	// player1.EndSignal(  "OnDestroy" )
	// player1.EndSignal(  "OnDeath" )
    // player1.EndSignal( "discordlogsignalstop" )
    HighlightContext highlight = GetHighlight( highlightname )

    foreach (player1real, value in entityhighlights){
        // discordlogsendmessage("eeestopped")

        foreach (entity player2real in value){
            
        
        if (!IsValid(player2real)){continue}
        
        if (!IsValid(player1real)){continue}
         Highlight_ClearOwnedHighlight(player2real)
        if (player1real == player2real){
            continue
        }
        // discordlogsendmessage("highlighting "+ player1real.GetPlayerName() + " and "+ player2real.GetPlayerName())
        // highlight.drawFuncId  = 3
        
        player2real.SetBossPlayer(player1real)
        highlight.insideSlot = insideslot
        // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
        // Highlight_SetOwnedHighlight(player2real,"interact_object_los") //interact_object_always
        // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
        highlight.paramVecs[0] = colour //<0.8,0.4,0.2>

        highlight.adsFade = false
        highlight.outlineRadius = radius
        player2real.Highlight_SetCurrentContext( 3 )
        player2real.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
        player2real.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
        player2real.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
        WaitFrame()
        if (!IsValid(player2real)){continue}
        player2real.ClearBossPlayer()

    }}
    // for (int int i = 0; i < 10; i++){   
    //     wait 1
    //     Highlight_ClearOwnedHighlight(player2)
    //     HighlightContext highlight = GetHighlight( "enemy_boss_bounty" )
    //     highlight.paramVecs[0] = <RandomFloatRange( 0.0, 1.0 ),RandomFloatRange( 0.0, 1.0 ),RandomFloatRange( 0.0, 1.0 )>
    //     player2.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
    //     player2.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
    //     player2.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
    // }
    // wait 5
    // // int offset = 0
    // // for (int i = 0; i < player1.len()-1; i++){
    // //     if (!IsValid(player1)){
    // //     player1.remove(i-offset)
    // //     offset +=1}
    // // }
    // // offset = 0
    // // for (int i = 0; i < player2.len()-1; i++){
    // //     if (!IsValid(player2)){
    // //     player2.remove(i-offset)
    // //     offset +=1}
    // // }
    // foreach (entity player2real in player2){
    // if (!IsValid(player2real)){continue}
    // Highlight_ClearOwnedHighlight(player2real)
    // foreach (entity player1real in player1){
    // if (!IsValid(player2real)){continue}
    // if (!IsValid(player1real)){continue}
    // if (player1real == player2real){
    //     continue
    // }
    // player2real.SetBossPlayer(player1real)

    // // highlight.drawFuncId  = 3
    // highlight.insideSlot = 112
    // // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
    // // Highlight_SetOwnedHighlight(player2real,"interact_object_los") //interact_object_always
    // // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
    // highlight.paramVecs[0] = <1.0,0.2,0.7> //<0.8,0.4,0.2>
    // highlight.adsFade = false
    // highlight.outlineRadius = 1.0
    // player2real.Highlight_SetCurrentContext( 3 )
	// player2real.Highlight_SetFunctions( 3, highlight.insideSlot, highlight.entityVisible, highlight.outsideSlot, highlight.outlineRadius, highlight.highlightId, highlight.afterPostProcess )
	// player2real.Highlight_SetParam( 3, 0, highlight.paramVecs[0] )
	// player2real.Highlight_SetParam( 3, 1, highlight.paramVecs[1] )
    // WaitFrame()
    //  if (!IsValid(player2real)){continue}
    // player2real.ClearBossPlayer()}}
    // discordlogsendmessage("eeestopped")
    }



discordlogcommand function discordlogaddnewhighlight(discordlogcommand commandin) {
	if (commandin.commandargs.len() != 2){
		commandin.returncode = 404
		commandin.returnmessage = "Wrong number of args"
		return commandin
	}
    addnewuidpairtotablething(commandin.commandargs[0],commandin.commandargs[1])
    table <string,array<string> > newhighlight
    newhighlight[commandin.commandargs[0]] <- [commandin.commandargs[1]]
    thread highlightplayertoplayer("tempwallhacks",newhighlight)
		commandin.returncode = 200
		commandin.returnmessage = "Highlighted " + commandin.commandargs[1]+ " to " + commandin.commandargs[0]
    return commandin
}

