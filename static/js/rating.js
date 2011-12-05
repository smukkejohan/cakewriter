$(function() {	
            $("#avg").children().not(":input").hide();
            $("#rating-widget").children().not("select").hide();	
           
            $caption = $("<span/>");

            $("#avg").stars({captionEl: $caption});
            $("#rating-widget").stars({
                inputType: "select",
            	cancelShow: false,
                captionEl: $caption,
                callback: function(ui, type, value){
                    $.post($("#rating-widget").attr("action"), {score: value}, 
                    function(data){
                        $('#rating-after').show('slow');
                        if (!(data=="Vote changed.")){
                            var oldHTML = document.getElementById('score_int').innerHTML;
                            var oldNumber = parseInt(oldHTML);
                            var newHTML = oldNumber+1;
                            document.getElementById('score_int').innerHTML = newHTML;
                            $( "#animation" )
                            .animate({color: "#A80002",fontSize: "30px",textShadow: "#df0003 0px 0px 5px;"}, 500, 
                            function(){$( "#animation" )
                            .animate({color:"#df0003", fontSize: "14px",textShadow: "#df0003 0px 0px 0px;"},500);});
                        }
                    }
                    );
                }
                
            });
               $caption.appendTo("#rating-widget");

});