$(document).ready(function () {
    const HEADER_PADDING = 20;
    const header = document.querySelector("#bar");
    const content = document.querySelector("#content");
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

    function updateContentPosition() {
        content.style.top = (header.offsetHeight + HEADER_PADDING) + "px";
    }

    header.addEventListener("transitionend", updateContentPosition);

    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            updateContentPosition();
        }, 100);
    });

    window.addEventListener("scroll", resize);
    resize();
    updateContentPosition();
});
