$( "#animation" ).animate({color: "#A80002",fontSize: "30px",textShadow: "#df0003 0px 0px 5px;"}, 500, 
function(){$( "#animation" ).animate({color:"#df0003", fontSize: "14px",textShadow: "#df0003 0px 0px 0px;"},500);});

$.post('/update_point_session/', 
           {session_del:true},
           function(data){}
    );