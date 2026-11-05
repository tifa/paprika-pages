(function () {
    "use strict";

    const $ = (sel, root = document) => root.querySelector(sel);
    const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
    const store = {
        get(key) { try { return localStorage.getItem(key); } catch (e) { return null; } },
        set(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* ignore */ } },
    };

    // ------------------------------------------------------------------
    // Search: "/" focuses it from anywhere, Esc clears.

    const search = $("#search");

    document.addEventListener("keydown", (event) => {
        const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
        if (event.key === "/" && !typing && search) {
            event.preventDefault();
            search.focus();
            search.select();
        }
    });

    // ------------------------------------------------------------------
    // Gallery: live filter, A–Z / Photos views, letter rail.

    const viewButtons = $$(".views [data-view]");
    if (viewButtons.length) {
        const panels = $$("[data-view-panel]");
        const count = $("#count");
        const empty = $("#empty");
        const total = count ? count.textContent : "";

        const setView = (view) => {
            viewButtons.forEach((b) => b.setAttribute("aria-selected", String(b.dataset.view === view)));
            panels.forEach((p) => { p.hidden = p.dataset.viewPanel !== view; });
            store.set("view", view);
        };
        viewButtons.forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));
        setView(store.get("view") === "index" ? "index" : "photos");

        const normalize = (s) => s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").trim();

        const filter = () => {
            const terms = normalize(search.value).split(/\s+/).filter(Boolean);
            const match = (el) => terms.every((t) => normalize(el.dataset.search).includes(t));
            let shown = 0;

            $$(".view-index .entry").forEach((el) => {
                el.hidden = !match(el);
                if (!el.hidden) shown++;
            });
            $$(".view-photos .tile").forEach((el) => { el.hidden = !match(el); });

            $$(".letter-group").forEach((group) => {
                const visible = $$(".entry", group).some((el) => !el.hidden);
                group.hidden = !visible;
                const link = $(`.rail a[data-letter="${group.dataset.letter}"]`);
                if (link) link.style.opacity = visible ? "" : "0.25";
            });

            count.textContent = terms.length ? `${shown} / ${total}` : total;
            empty.hidden = shown > 0;
            $("#empty-q").textContent = search.value;
        };

        search.addEventListener("input", filter);

        // On the gallery the search box filters in place instead of submitting.
        // Enter jumps straight to the first visible match.
        search.form.addEventListener("submit", (event) => {
            event.preventDefault();
            const view = store.get("view") === "index" ? ".view-index .entry" : ".view-photos .tile";
            const first = $$(view).find((el) => !el.hidden && $("a", el));
            if (first) window.location.href = $("a", first).href;
        });

        search.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                search.value = "";
                filter();
                search.blur();
            }
        });

        $("#clear-search").addEventListener("click", () => {
            search.value = "";
            filter();
            search.focus();
        });

        if (search.value) filter();

        // highlight the letter currently at the top of the list
        const railLinks = $$(".rail a");
        if ("IntersectionObserver" in window && railLinks.length) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    const letter = entry.target.dataset.letter;
                    railLinks.forEach((a) => a.classList.toggle("current", a.dataset.letter === letter));
                });
            }, { rootMargin: "-30% 0px -65% 0px" });
            $$(".letter-group").forEach((g) => observer.observe(g));
        }
    }

    // ------------------------------------------------------------------
    // Recipe: check off ingredients, keep your place in the steps.

    const recipe = $("#recipe");
    if (recipe) {
        const key = "checked:" + location.pathname;
        const items = $$(".ingredients li", recipe);
        const reset = $("#reset-ingredients");
        let checked = new Set();
        try { checked = new Set(JSON.parse(sessionStorage.getItem(key) || "[]")); } catch (e) { /* ignore */ }

        const save = () => {
            try { sessionStorage.setItem(key, JSON.stringify([...checked])); } catch (e) { /* ignore */ }
            if (reset) reset.hidden = checked.size === 0;
        };

        items.forEach((li, i) => {
            li.tabIndex = 0;
            li.setAttribute("role", "checkbox");
            const sync = () => {
                li.classList.toggle("done", checked.has(i));
                li.setAttribute("aria-checked", String(checked.has(i)));
            };
            const toggle = () => {
                checked.has(i) ? checked.delete(i) : checked.add(i);
                sync();
                save();
            };
            li.addEventListener("click", toggle);
            li.addEventListener("keydown", (e) => {
                if (e.key === " " || e.key === "Enter") { e.preventDefault(); toggle(); }
            });
            sync();
        });
        save();

        if (reset) {
            reset.addEventListener("click", () => {
                checked.clear();
                items.forEach((li) => { li.classList.remove("done"); li.setAttribute("aria-checked", "false"); });
                save();
            });
        }

        // Directions are often typed one step per line; split each line into its own paragraph.
        $$(".steps > p", recipe).forEach((p) => {
            if (!$("br", p)) return;
            const chunks = [[]];
            Array.from(p.childNodes).forEach((node) => {
                if (node.nodeName === "BR") chunks.push([]);
                else chunks[chunks.length - 1].push(node);
            });
            chunks.forEach((nodes) => {
                if (!nodes.some((n) => n.textContent.trim() || n.nodeName === "IMG")) return;
                const para = document.createElement("p");
                nodes.forEach((n) => para.appendChild(n));
                p.before(para);
            });
            p.remove();
        });

        // number only paragraphs that have words in them (not photo-only rows)
        $$(".steps > p", recipe).forEach((p) => {
            if (!p.textContent.trim()) return;
            p.classList.add("step");
            p.addEventListener("click", (event) => {
                if (event.target.tagName === "IMG") return;
                const wasCurrent = p.classList.contains("current");
                $$(".steps > p.current", recipe).forEach((el) => el.classList.remove("current"));
                if (!wasCurrent) p.classList.add("current");
            });
        });
    }

    // ------------------------------------------------------------------
    // Lightbox for every photo on a recipe page.

    const lightbox = $("#lightbox");
    const lightboxImg = $("#lightbox-img");
    const prev = $(".lightbox-prev");
    const next = $(".lightbox-next");
    let images = [];
    let index = 0;

    const show = (i) => {
        if (i < 0 || i >= images.length) return;
        index = i;
        lightboxImg.src = images[i].src;
        prev.hidden = i === 0;
        next.hidden = i === images.length - 1;
    };
    const close = () => lightbox.classList.remove("active");

    if (recipe) {
        recipe.addEventListener("click", (event) => {
            if (event.target.tagName !== "IMG") return;
            event.stopPropagation();
            images = $$("img", recipe);
            lightbox.classList.add("active");
            show(images.indexOf(event.target));
        });
    }

    prev.addEventListener("click", (e) => { e.stopPropagation(); show(index - 1); });
    next.addEventListener("click", (e) => { e.stopPropagation(); show(index + 1); });
    $(".lightbox-close").addEventListener("click", close);
    lightbox.addEventListener("click", (e) => { if (e.target === lightbox) close(); });

    document.addEventListener("keydown", (event) => {
        if (!lightbox.classList.contains("active")) return;
        if (event.key === "Escape") close();
        else if (event.key === "ArrowLeft") show(index - 1);
        else if (event.key === "ArrowRight") show(index + 1);
    });
})();
