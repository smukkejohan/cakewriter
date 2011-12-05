var show=true;
var hide=false;
var close=false;
$(document).ready(function(){

 $(window).scroll(function () {
 
     if($(window).scrollTop()>=$("#chapter").height()-200 )
     {
         if( show==true && close==false)
         {
            show=false;
            hide=true;          
            $("#message").show("slide", { direction: "right" }, 500);
         }
     }else if ($(window).scrollTop()<$("#chapter").height()-200)
     {
         if(hide==true && close==false)
         {
                show=true;
                hide=false;                         
                $("#message").hide("slide", { direction: "right" }, 500);
         }
     }
     
    });
 });

function hide_message(){
    $("#message").hide("slide", { direction: "right" }, 500);
    close=true;
}