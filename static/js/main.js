google.load("jquery", "1.2");
google.load("jqueryui", "1.5");

google.setOnLoadCallback(function() {
    $(".vote-up, .vote-down").click(function() {
        //.hasClass()     
        alert('vote up');   
    });
    
   /* $(".vote-down").click(function() {      
        alert('vote down');   
    });*/
 
});