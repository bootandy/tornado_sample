
$(document).ready(function() {
    $("#notification").fadeIn("slow");
    $("#notification a.close-notify").click(close_it);
    //$("#notification").delay(10000).call(close_it);
    setTimeout(close_it, 5000)

    function close_it() {
        $("#notification").fadeOut("slow");
        return false;
    }
});