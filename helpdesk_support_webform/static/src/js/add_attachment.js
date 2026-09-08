$(document).ready(function () {
    $("#add_attachment").click(function () {
        var newel = $("#dummy").prev().clone()
        newel.val(null)
        $(newel).insertBefore("#dummy").css({
            block: "display",
            width: "100%",
            left: "10px",
        })
    })
})
