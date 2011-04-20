$(document).ready(function() {
  function filterPath(string) {
  return string
    .replace(/^\//,'')
    .replace(/(index|default).[a-zA-Z]{3,4}$/,'')
    .replace(/\/$/,'');
  }
  var locationPath = filterPath(location.pathname);
  var scrollElem = scrollableElement('html', 'body');

  $('a[href*=#]').each(function() {
    var thisPath = filterPath(this.pathname) || locationPath;
    if (  locationPath == thisPath
    && (location.hostname == this.hostname || !this.hostname)
    && this.hash.replace(/#/,'') ) {
      var $target = $(this.hash), target = this.hash;
      if (target) {
        var targetOffset = $target.offset().top;
        $(this).click(function(event) {
          event.preventDefault();
          $(scrollElem).animate({scrollTop: targetOffset}, 400, function() {
            location.hash = target;
          });
        });
      }
    }
  });

  // use the first element that is "scrollable"
  function scrollableElement(els) {
    for (var i = 0, argLength = arguments.length; i <argLength; i++) {
      var el = arguments[i],
          $scrollElement = $(el);
      if ($scrollElement.scrollTop()> 0) {
        return el;
      } else {
        $scrollElement.scrollTop(1);
        var isScrollable = $scrollElement.scrollTop()> 0;
        $scrollElement.scrollTop(0);
        if (isScrollable) {
          return el;
        }
      }
    }
    return [];
  }

});

$(function() {
     
    $(".vote-up, .vote-down").click(function() {
        var self = $(this);
        var comment = self.parents(".comment");
        var uid = comment.attr("id").substr(1);
        var action;
             
        if (self.hasClass('vote-on')) { action = 'clear'; }
        else if (self.hasClass('vote-up')) { action = 'up'; }    
        else { action = 'down'; }
        
        $.post('/book/comment/' + uid + '/vote/' + action, function(data) {
            if(data.success == true){
                comment.find(".vote-score").html(data.score.score);
                if(action == 'clear') {
                    self.removeClass("vote-on");
                } else {
                    self.siblings(".vote-on").removeClass("vote-on");
                    self.addClass("vote-on");
                }
            } else {
                if (data.error_message == "Not authenticated."){}
            }
        }, "json");               
    });
});

  


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
                    $.post($("#rating-widget").attr("action"), {score: value}, function(data){
                    
                    });
                }
            });
               $caption.appendTo("#rating-widget");

});

 

$(document).ready(function(){
	
	$(".toggle_container").hide();
 
	$(".trigger").toggle(function(){
		$(this).addClass("active"); 
		}, function () {
		$(this).removeClass("active");
	});
	
	$(".trigger").click(function(){
		$(this).next(".toggle_container").slideToggle("slow,");
	});
 
});
