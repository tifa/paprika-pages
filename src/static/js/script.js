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

    // ----------------------------------------------
    // lightbox functionality
    const lightbox = document.getElementById("lightbox");
    const lightboxImg = document.getElementById("lightbox-img");
    const lightboxClose = document.querySelector(".lightbox-close");
    const lightboxPrev = document.querySelector(".lightbox-prev");
    const lightboxNext = document.querySelector(".lightbox-next");
    let currentImageIndex = 0;
    let lightboxImages = [];

    // make all images in recipe page clickable for lightbox
    $("#recipe img").each(function() {
        $(this).addClass("lightbox-trigger").css("cursor", "pointer");
    });

    function updateLightboxImages() {
        lightboxImages = $("#recipe img").toArray();
    }

    function showLightboxImage(index) {
        if (lightboxImages.length === 0) return;

        // don't loop - clamp to valid range
        if (index < 0 || index >= lightboxImages.length) return;

        currentImageIndex = index;
        lightboxImg.src = lightboxImages[currentImageIndex].src;

        // show/hide navigation arrows based on position
        if (lightboxPrev) {
            lightboxPrev.style.display = (currentImageIndex === 0) ? 'none' : 'block';
        }
        if (lightboxNext) {
            lightboxNext.style.display = (currentImageIndex === lightboxImages.length - 1) ? 'none' : 'block';
        }
    }

    // add click handler to all images with lightbox-trigger class
    $(document).on("click", ".lightbox-trigger", function() {
        updateLightboxImages();
        currentImageIndex = lightboxImages.indexOf(this);
        lightbox.classList.add("active");
        showLightboxImage(currentImageIndex);
    });

    // navigate to previous image
    if (lightboxPrev) {
        lightboxPrev.onclick = function(event) {
            event.stopPropagation();
            showLightboxImage(currentImageIndex - 1);
        };
    }

    // navigate to next image
    if (lightboxNext) {
        lightboxNext.onclick = function(event) {
            event.stopPropagation();
            showLightboxImage(currentImageIndex + 1);
        };
    }

    // close lightbox when clicking the X
    if (lightboxClose) {
        lightboxClose.onclick = function() {
            lightbox.classList.remove("active");
        };
    }

    // close lightbox when clicking outside the image
    if (lightbox) {
        lightbox.onclick = function(event) {
            if (event.target === lightbox) {
                lightbox.classList.remove("active");
            }
        };
    }

    // keyboard navigation
    document.addEventListener("keydown", function(event) {
        if (lightbox.classList.contains("active")) {
            if (event.key === "Escape") {
                lightbox.classList.remove("active");
            } else if (event.key === "ArrowLeft") {
                showLightboxImage(currentImageIndex - 1);
            } else if (event.key === "ArrowRight") {
                showLightboxImage(currentImageIndex + 1);
            }
        }
    });
});
