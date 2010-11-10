google.load("jquery", "1.4");

google.setOnLoadCallback(function() {
    
    
    $(".vote-up, .vote-down").click(function() {
        var self = $(this);
        var uid = self.parents(".comment").attr("id").substr(1);
        var action;
             
        if (self.hasClass('vote-on')) { action = 'clear'; }
        else if (self.hasClass('vote-up')) { action = 'up'; }    
        else { action = 'down'; }
        
        $.post('/book/comment/' + uid + '/' + action, function(data) {
            if(data.success == true){
                self.siblings(".vote-score").html(data.score.score);
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