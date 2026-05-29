global function discordlognoreg

void function discordlognoreg(){
    AddDamageCallback( "player", noreg )
}

array<int> DISALLOWED_COLOURS = [
    0,
    52,
    16,
    18,
    17,
    20,
    23,
    25,
    24,
    59,
    60,
    62,
    61,
    58,
    65,
    95,
    61,
    54,
    92,
    102,
    101,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    57,
    56,
    19,
    91,
    89,
    90,
    88,
    96,
    53
]
void function noreg ( entity titan, var damageInfo )

{

	entity player = DamageInfo_GetAttacker( damageInfo )
    // discordlogsendmessage("" + player.IsPlayer() + titan.IsPlayer() + IsValid( titan ) + IsValid( player ) + (player.GetUID() in noregs) + (RandomInt( 100 ) < noregs[player.GetUID()])  + GetConVarInt("systematicnoregsenabled"))
    if (   player.IsPlayer() && titan.IsPlayer() && IsValid( titan ) && IsValid( player ) && (discordlogpullplayerstat(player.GetUID(),"noreg") != "" ) && (RandomInt( 100 ) < discordlogpullplayerstat(player.GetUID(),"noreg").tointeger())  && GetConVarInt("discordlogsystematicnoregsenabled"))

	{
		vector velocity = titan.GetVelocity()
		float squared = velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z
		// if ( squared > 50000  == 0 )
		// {
        	string reallycounter = ""
			for (int i = 0; i < RandomInt(15)+1; i++){
                int colour = 0
                while (!colour || DISALLOWED_COLOURS.contains(colour)){
					colour = RandomIntRange ( 1, 254 )

                }
				reallycounter += "[38;5;"+colour+"m!"
			}
            if (DamageInfo_GetDamage(damageInfo) > 0 && GetConVarInt("discordlogshouldnotifyofnoregs")){
        Chat_ServerPrivateMessage(player,"[110myou noregged"+reallycounter+ "[38;5;249m and missed on [38;5;189m"+ DamageInfo_GetDamage(damageInfo).tointeger() + "[38;5;249m damage!",false,false)
            }
			DamageInfo_SetDamage( damageInfo, 0 )
		// }
		// else if ( squared > 150000 )
		// {

		// 	DamageInfo_SetDamage( damageInfo, 0 )
		// }
	}
    // else{
    //     discordlogsendmessage("you did not noreg")
    // }
}