global function discordloghighlightplayerforplayerinit
global function discordlogaddnewhighlight
global function discordlogaddnewhighlightforwallhacks

struct highlightinfo {
    string whoishighlighted
    entity whoishighlightedent
    string typeofhighlight
    table otherinfo = {}
}
struct {
    table <string,array<highlightinfo> > uidshighlights //this is the oopsie, what if one player is dueling more than one?
} highlights

struct {
    table <entity,vector> entitycolours
} prettycolours

void function addnewuidpairtotablething(string uid1,string uid2, string typeofhighlight){
    array<highlightinfo> adder = []
    if ((uid1 in highlights.uidshighlights)){
        adder = highlights.uidshighlights[uid1]
    }
    bool found = false
    for (int i = 0; i < adder.len(); i++){
        if (adder[i].whoishighlighted == uid2){
            found = true
            adder[i].typeofhighlight = typeofhighlight
        }
    }
    if (!found) {
    highlightinfo addedpersonhighlight
    addedpersonhighlight.typeofhighlight = typeofhighlight
    addedpersonhighlight.whoishighlighted = uid2
    adder.append(addedpersonhighlight)}
    highlights.uidshighlights[uid1] <- adder
    table<string,array<highlightinfo> > newhighlight
    highlightinfo highlightinfostuff
    highlightinfostuff.whoishighlighted = uid2
    highlightinfostuff.typeofhighlight = typeofhighlight
    newhighlight[uid1] <- [highlightinfostuff]
    thread highlightplayertoplayer(newhighlight)
}



void function discordloghighlightplayerforplayerinit(){
    RegisterSignal( "discordlogsignalstop" )
    AddCallback_OnClientConnected( readdhighlightjustincase )
    AddCallback_OnPlayerRespawned( readdhighlightjustincase )
    AddCallback_OnPilotBecomesTitan(readdhighlightjustincasetitan)
    AddCallback_OnTitanBecomesPilot( readdhighlightjustincasetitan )
    // addnewuidpairtotablething("1012640166434" , "1012744612530","tempwallhacks")
    // addnewuidpairtotablething("1012744612530" , "1012640166434","tempwallhacks")

    // addnewuidpairtotablething("1012640166434","2509670718","actualwallhacks")
    // addnewuidpairtotablething("2509670718","1012640166434","actualwallhacks")
}
void function readdhighlightjustincasetitan(entity player,entity titan){
    table<string,array<highlightinfo> > highlightsthings
    foreach(key,value in highlights.uidshighlights){
        if ( key == player.GetUID()){
            highlightsthings[key] <- value
        }
        foreach (person in value){
            if (person.whoishighlighted == player.GetUID()){
                highlightsthings[key] <- [person]
            }
        }

    }
    thread highlightplayertoplayer(highlightsthings)
}

void function readdhighlightjustincase(entity player){
    // discordlogsendmessage("w"+" e "+player.GetUID())
    if (!(player in prettycolours.entitycolours)){
        prettycolours.entitycolours[player] <- RandomVecc(1)
    }
    table<string,array<highlightinfo> > highlightsthings
    foreach(key,value in highlights.uidshighlights){
        // discordlogsendmessage("s"+key)
        if ( key == player.GetUID()){
            // discordlogsendmessage("w"+key+" e "+player.GetUID())
            highlightsthings[key] <- value

        }
        foreach (person in value){
            if (person.whoishighlighted == player.GetUID()){
                // discordlogsendmessage(key+"w"+person.whoishighlighted)
                highlightsthings[key] <- [person]

            }
        }

    }
    thread highlightplayertoplayer(highlightsthings)
}

void function highlightplayertoplayer(table<string,array<highlightinfo> >  highlightsthings = {},table<entity,array<highlightinfo> >  highlightsthingsentitys = {}){
    // wait 10
    // // discordlogsendmessage("eee "+ uid + "wqdq "+ uid2)
    // discordlogsendmessage("b")
    WaitFrame()
    table<entity,array<highlightinfo> > entityhighlights
    foreach (key,value in highlightsthings){
        // discordlogsendmessage("yyzzzzyy"+key)
        foreach (player in GetPlayerArray()){
            
        if (key == (player.GetUID())){
                // discordlogsendmessage("yyyy")
            entity realplayer = player
            entityhighlights[player] <- []
            // break
                foreach (thing in value){
                    // discordlogsendmessage("dwqdwq")
                    foreach (player in GetPlayerArray()){
                        if (thing.whoishighlighted == (player.GetUID())){
                                        // discordlogsendmessage("xxxx")
                            highlightinfo addedplayer = thing
                            addedplayer.whoishighlightedent = player
                            // PrintTable(addedplayer)
                            entityhighlights[realplayer].append(addedplayer)
                    }}
        }
        }}

    }

    // PrintTable(entityhighlights)
    
    // if (!IsValid(player1) || !IsValid(player2)){
    //     return
    // }
    table<string,table<entity,array<highlightinfo> > > entityhighlightsfilteredbytype

    foreach (key,value in entityhighlights){
        // discordlogsendmessage("eeee"+key)
        foreach (thing in value) {
            // discordlogsendmessage("dwqdwqd")
            if (!(thing.typeofhighlight in entityhighlightsfilteredbytype)){
                entityhighlightsfilteredbytype[thing.typeofhighlight] <- {}
            }
            if (!(key in entityhighlightsfilteredbytype[thing.typeofhighlight])){
                entityhighlightsfilteredbytype[thing.typeofhighlight][key] <- []
            }
            entityhighlightsfilteredbytype[thing.typeofhighlight][key].append(thing)
        }
    }
    // WaitFrame()
    
    // player1.Signal("discordlogsignalstop")
    foreach (typeofhighlight,realhighlights in entityhighlightsfilteredbytype){
        // discordlogsendmessage("wwww")
        table<entity,array<entity> > shouldhighlight
        foreach (key,value in entityhighlightsfilteredbytype[typeofhighlight]){
            // discordlogsendmessage("wqdqd"+key.GetPlayerName())
            shouldhighlight[key] <- []
            foreach (person in value){
                // printt(person.whoishighlightedent+"")
                // discordlogsendmessage("wqdqd"+person.whoishighlightedent.GetPlayerName())
                shouldhighlight[key].append((person.whoishighlightedent))
            }
        }
        // discordlogsendmessage("ee"+typeofhighlight)
        if (typeofhighlight == "tempwallhacks"){
            actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,106,7.0)
            wait 5
            actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,112,1.0)
                foreach (player in findallplayers(shouldhighlight)){
                    // discordlogsendmessage("dqwdwq"+player.GetPlayerName())
                    // // discordlogsendmessage("dqwdwq"+player.GetPlayerName())
                    thread keephighlighted(player,shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,112,1.0)
                }
        }
        if (typeofhighlight == "actualwallhacks"){
            // thread actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,106,7.0)
            // wait 5
            // 126, 114
            // while (true){
            actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,126,7.0)
            // wait 0.5
            // }
            
            foreach (player in findallplayers(shouldhighlight)){
            
            
            thread keephighlighted(player,shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,126,7.0)
           }
        }

        if (typeofhighlight == "titanhighlight"){
            // thread actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,106,7.0)
            // wait 5
            actuallyhighlight(shouldhighlight,"enemy_boss_bounty",<1.0,0.2,0.7>,112,1.0)}
     }
    
    // foreach (npc in GetNPCArray()){
    // thread actuallyhighlight(player1,npc,shouldhighlight)}
}
    
    array<entity> function findallplayers(table<entity,array<entity> > entityhighlights){
        array<entity> found = []
        foreach (key,value in entityhighlights){
            foreach (thing in value){
                if (!(found.contains(thing))){
                    found.append(thing)
                }
            }
        }
        return found
    }

    void function keephighlighted(entity player,table<entity,array<entity> > entityhighlights,string highlightname, vector colour, int insideslot, float radius){
        player.EndSignal(  "OnDestroy" )
        player.EndSignal(  "OnDeath" )
        table<entity,array<entity> > realhighlights
        while (true){
            // discordlogsendmessage("eeestart"+player.GetPlayerName())
            waitthread waitforstuff(player)
            // discordlogsendmessage("eeestopped"+player.GetPlayerName())
            foreach (key, value in entityhighlights){
                
                // discordlogsendmessage("bleh"+key.GetPlayerName()+" e "+ value.len())
                if (value.contains(player)){
                    // discordlogsendmessage("blewdqqwdqw")
                    foreach (thing in value){
                        // discordlogsendmessage("blewdqqwdqwdqwh"+thing.GetPlayerName())
                    }
                    realhighlights[key] <- [player]
                     
                }

                // else{
                //     realhighlights[key] <- []
                // }

            }
            actuallyhighlight(realhighlights,highlightname,colour,insideslot,radius)
            wait RODEO_BATTERY_THIEF_ICON_DURATION
            foreach (key, value in entityhighlights){
                
                // discordlogsendmessage("bleh"+key.GetPlayerName()+" e "+ value.len())
                if (value.contains(player)){
                    // discordlogsendmessage("blewdqqwdqw")
                    foreach (thing in value){
                        // discordlogsendmessage("blewdqqwdqwdqwh"+thing.GetPlayerName())
                    }
                    realhighlights[key] <- [player]
                     
                }

                // else{
                //     realhighlights[key] <- []
                // }

            }
            actuallyhighlight(realhighlights,highlightname,colour,insideslot,radius)
        }
    }

    void function waitforstuff(entity player){
        player.EndSignal( "StopPhaseShift" )
        player.EndSignal( "ForceStopPhaseShift" )
        player.EndSignal( "RodeoOver" )
        WaitForever()
    }

    void function actuallyhighlight(table<entity,array<entity> > entityhighlights, string highlightname, vector colour, int insideslot, float radius){
    
	// player1.EndSignal(  "OnDestroy" )
	// player1.EndSignal(  "OnDeath" )
    // player1.EndSignal( "discordlogsignalstop" )
    HighlightContext highlight = GetHighlight( highlightname )

    foreach (player1real, value in entityhighlights){
        // // discordlogsendmessage("eeestopped")

        foreach (entity player2real in value){
            
        
        if (!IsValid(player2real)){continue}
        
        if (!IsValid(player1real)){continue}
        colour = prettycolours.entitycolours[player2real]
         Highlight_ClearOwnedHighlight(player2real)
         WaitFrame()
        if (player1real == player2real){
            continue
        }
        // discordlogsendmessage("highlighting "+ player1real.GetPlayerName() +" and "+ player2real.GetPlayerName())
        // highlight.drawFuncId  = 3
        
        player2real.SetBossPlayer(player1real)
        highlight.insideSlot = insideslot
        // __SetEntityContextHighlight( ent, HIGHLIGHT_CONTEXT_OWNED, highlight )
        // Highlight_SetOwnedHighlight(player2real,"interact_object_los") //interact_object_always
        // /compilestring function:foreach(entity cPlayer in GetPlayerArray()){cPlayer.SetBossPlayer( discordlogmatchplayers("allu")[0]) ; Highlight_SetOwnedHighlight(cPlayer,"interact_object_los")}  servername:Aegisattritionihh
        highlight.paramVecs[0] = colour //<0.8,0.4,0.2>
        highlight.paramVecs[1] = <0,0,0>

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
    // // discordlogsendmessage("eeestopped")
    }


vector function RandomVecc( float range )
{
	// could rewrite so it doesnt make a box of random.
	vector vec = Vector( 0, 0, 0 )
	vec.x = RandomFloatRange( 0, range )
	vec.y = RandomFloatRange( 0, range )
	vec.z = RandomFloatRange( 0, range )

	return vec
}




discordlogcommand function discordlogaddnewhighlight(discordlogcommand commandin) {
	if (commandin.commandargs.len() != 2){
		commandin.returncode = 404
		commandin.returnmessage = "Wrong number of args"
		return commandin
	}
    addnewuidpairtotablething(commandin.commandargs[0],commandin.commandargs[1],"tempwallhacks")

		commandin.returncode = 200
		commandin.returnmessage = "Highlighted " + commandin.commandargs[1]+ " to " + commandin.commandargs[0]
    return commandin
}




discordlogcommand function discordlogaddnewhighlightforwallhacks(discordlogcommand commandin) {
    // if (commandin.commandargs.len() != 2 && commandin.commandargs.len() != 3)
    // {
    //     commandin.returnmessage = "Wrong number of args";
    //     commandin.returncode = 400
    //     return commandin;
    // }
    array<entity> players = discordlogmatchplayers(commandin.commandargs[1])
    if (players.len() == 0 && commandin.commandargs[1] != "all"){
        commandin.returnmessage = "No players found"
        commandin.returncode = 401
    }
    else if (players.len() > 1 && commandin.commandargs[1] != "all"){
        commandin.returnmessage = "Multiple players found"
        commandin.returncode = 402
    }
    else {
        if (commandin.commandargs[1] == "all"){
            players = GetPlayerArray()
            commandin.returnmessage = "Highlighting "+ players.len() + " players"  
        }else{
            commandin.returnmessage = "Highlighting " + discordloggetplayername(players[0])       
        }
        string typeofhighlight = "actualwallhacks"
        if (commandin.commandargs.len() == 3) {
            typeofhighlight = commandin.commandargs[2]
        }
        foreach (player in players){
            addnewuidpairtotablething(commandin.commandargs[0],player.GetUID(),typeofhighlight)
        }
        commandin.returncode = 200
    }
    return commandin;
}

