/* Parent Data Force — rotating stats strip (progressive enhancement).
 * Crossfades .pdf-stats-set blocks every INTERVAL ms. No-op when the strip
 * is absent, when only one set exists, or when the user prefers reduced
 * motion (the first set simply stays visible). Dots appear only once this
 * script activates (via .pdf-stats--rotating). */
(function () {
	"use strict";
	var grids = document.querySelectorAll(".pdf-stats-grid");
	if (!grids.length) { return; }
	var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
	var INTERVAL = 7000;

	Array.prototype.forEach.call(grids, function (grid) {
		var sets = Array.prototype.slice.call(grid.querySelectorAll(".pdf-stats-set"));
		if (sets.length < 2) { return; }
		var strip = grid.closest(".pdf-stats") || grid.parentElement;
		var dots = strip ? Array.prototype.slice.call(strip.querySelectorAll(".pdf-stats-dot")) : [];
		var active = 0;
		var timer = null;
		var paused = false;

		function show(n) {
			active = n;
			sets.forEach(function (s, idx) {
				s.classList.toggle("is-hidden", idx !== n);
				if (idx !== n) { s.setAttribute("aria-hidden", "true"); } else { s.removeAttribute("aria-hidden"); }
			});
			dots.forEach(function (d, idx) { d.classList.toggle("is-active", idx === n); });
		}
		function start() {
			if (reduce || paused || timer) { return; }
			timer = setInterval(function () { show((active + 1) % sets.length); }, INTERVAL);
		}
		function stop() {
			if (timer) { clearInterval(timer); timer = null; }
		}

		strip.classList.add("pdf-stats--rotating");
		show(0);
		if (reduce) { return; }
		start();

		grid.addEventListener("mouseenter", function () { paused = true; stop(); });
		grid.addEventListener("mouseleave", function () { paused = false; start(); });
		grid.addEventListener("focusin", function () { paused = true; stop(); });
		grid.addEventListener("focusout", function () { paused = false; start(); });
		dots.forEach(function (d) {
			d.addEventListener("click", function () {
				stop();
				show(parseInt(d.getAttribute("data-set"), 10) || 0);
				start();
			});
		});
	});
})();
