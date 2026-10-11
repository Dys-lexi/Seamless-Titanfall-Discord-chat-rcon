global function cheatsinit
global function setstufflatercommand
void function cheatsinit()
{
    AddCallback_OnPlayerGetsNewPilotLoadout( checkifbadlouadout )
    AddCallback_OnPilotBecomesTitan( OnClassChangeBecomeTitan )
}

void function OnClassChangeBecomeTitan( entity player, entity titan )
{
	 
   if (( discordlogpullplayerstat(player.GetUID(),"badperson")!= "True")){
    return
   }
//    atp is a bad egg!
    if (discordlogpullplayerstat(player.GetUID(),"badperson")!= "True"){
        runcommandondiscord("toggle",{ uid = player.GetUID(),originalmessage="!toggle badperson"})
    }
    delaythread( 0.5 ) setstufflater(player) 
}

void function checkifbadlouadout( entity player, PilotLoadoutDef loadout )
{
   array<string> mods = [loadout.primaryMod3,loadout.secondaryMod3 ,loadout.weapon3Mod3 ]
    bool isbad = false
   foreach (string mod in mods) {
    if (mod != "" && mod != "pro_screen" ){
        isbad = true
    }
   }
   if ((!isbad && discordlogpullplayerstat(player.GetUID(),"badperson")!= "True") || player.IsTitan() ){
    return
   }
//    atp is a bad egg!
    if (discordlogpullplayerstat(player.GetUID(),"badperson")!= "True"){
        runcommandondiscord("toggle",{ uid = player.GetUID(),originalmessage="!toggle badperson"})
    }
    delaythread( 0.5 ) setstufflater(player) 
}

discordlogcommand function setstufflatercommand(discordlogcommand commandin){
    if (commandin.commandargs.len() < 1)
    {
        commandin.returnmessage = "Wrong number of args";
        commandin.returncode = 400
        return commandin;
    }

    array<entity> players = discordlogmatchplayers(commandin.commandargs[0])
    if (commandin.commandargs[0] == "all"){
        players = GetPlayerArray()
    }
    if (players.len() == 0){
        commandin.returnmessage = "No players found"
        commandin.returncode = 401
        return commandin
    }
    float duration = 99999
    if (commandin.commandargs.len() == 2){
        duration = commandin.commandargs[1].tofloat()
    }
    foreach (entity player in players){
        thread setstufflater(player,duration)
    }
    commandin.returncode = 200
    commandin.returnmessage = "Ran emp on "+ players.len()+ " people"
     return commandin;
}

void function setstufflater(entity player,float duration = 99999){
    player.EndSignal( "OnDeath" )
    player.EndSignal( "OnDestroy" )
    player.kv.airAcceleration = 0.00001
    player.kv.gravity = 2000
    player.kv.airSpeed = 0.1
    if (!player.IsTitan()){
    player.SetPlayerSettingsWithMods( player.GetPlayerSettings(), ["disable_wallrun","disable_doublejump"   ] )}
    int health = player.GetMaxHealth()
    player.SetMaxHealth(1)
    player.SetHealth(1)
    // loadout.setFileMods.append("disable_wallrun")
    // loadout.setFileMods.append("disable_doublejump")
	print("MEOWWWGOTHER")
        StatusEffect_AddEndless( player, eStatusEffect.emp, 10)
	StatusEffect_AddEndless( player, eStatusEffect.turn_slow, 0.4 )
	StatusEffect_AddEndless( player, eStatusEffect.move_slow, 0.5 )
    
    //    for (int i; i < i; i++){
 
        Remote_CallFunction_Replay( player, "ServerCallback_TitanEMP", 9999,duration,0.0 )
    	Remote_CallFunction_Replay( player, "ServerCallback_ScreenShake", 999999, 10, duration )
        // }
        
                                                                
	// shake.SetParent( player, "CHESTFOCUS" )

    	OnThreadEnd(
		function() : ( player,health )
		{
            printt("got here weoag")
            StatusEffect_StopAll(player,eStatusEffect.emp)
            StatusEffect_StopAll(player,eStatusEffect.turn_slow)
              player.SetPlayerSettingsWithMods( player.GetPlayerSettings(),[])
            StatusEffect_StopAll(player,eStatusEffect.move_slow)
            player.SetMaxHealth(health)
            player.kv.gravity = player.GetPlayerSettingsField( "gravityScale" )
            player.kv.airAcceleration = GetCurrentPlaylistVarInt( "custom_air_accel_pilot", int( player.GetPlayerSettingsField( "airAcceleration" ) ) )
            	player.kv.airSpeed = player.GetPlayerSettingsField( "airSpeed" )
		}
	)
        wait duration

}

// CreateShake( player.GetOrigin(), 16, 150, 1.00, 400 )
// /compilestring function: StatusEffect_AddEndless( discordlogmatchplayers("lexi")[0], eStatusEffect.emp, 10)

