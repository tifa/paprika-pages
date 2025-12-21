$(document).ready(function () {
    // ----------------------------------------------
    // header shrink effect

    const header = document.querySelector("#bar");
    let resizeTimer;

    function resize() {
        var distanceY = window.pageYOffset || document.documentElement.scrollTop,
            shrinkOn = 75;
        if (distanceY > shrinkOn) {
            header.classList.add("smaller");
        } else if (header.classList.contains("smaller")) {
            header.classList.remove("smaller");
        }
    }

    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
    });

    window.addEventListener("scroll", resize);
    resize();

    // ----------------------------------------------
    // ingredient click to strike-through
    $("#recipe .ingredients li").css("cursor", "pointer");
    $("#recipe .ingredients li").click(function () {
        if ($(this).css("text-decoration") === "line-through") {
            $(this).css({
                "text-decoration": "none",
                "opacity": "1",
            });
        } else {
            $(this).css({
                "text-decoration": "line-through",
                "opacity": "0.5",
            });
        }
    });
});
