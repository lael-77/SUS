/* SUS Kigali Haircut — public site progressive enhancements.
   Nothing here is required for the site to work: navigation, links, forms and
   the booking flow all function with JavaScript disabled. This file only adds
   polish (sticky-header shadow, scroll reveals) and always respects the
   visitor's "reduce motion" preference. */

(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- 1. Sticky header gains a shadow once the page has scrolled ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- 2. Close the mobile menu after tapping a link ---------------------- */
  var nav = document.getElementById("nav");
  if (nav) {
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) { nav.classList.remove("open"); }
    });
  }

  /* ---- 3. Scroll reveals -------------------------------------------------- */
  var targets = document.querySelectorAll("[data-reveal]");
  if (!targets.length) { return; }

  if (reduced || !("IntersectionObserver" in window)) {
    targets.forEach(function (el) { el.classList.add("is-visible"); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });

  targets.forEach(function (el) { observer.observe(el); });
})();
