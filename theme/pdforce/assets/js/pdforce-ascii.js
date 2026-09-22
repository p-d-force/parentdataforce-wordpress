/**
 * pdforce-ascii.js — animated ASCII hero for Parent Data Force.
 *
 * The brand fault line (the exact crack traced from the logo, embedded as
 * window.PDFORCE_CRACK_PATH) splits a rippling dark data field, glowing with
 * the signal orange ramp and a travelling shine. Public records — little
 * document glyphs — well up out of the fissure, drip downward under gravity,
 * and dissolve into the field. Embers and a sparse starfield drift above.
 *
 * Vanilla <canvas>, zero dependencies. The crack outline is rasterized once
 * per resize from the same SVG path used for the vector logo, so the hero and
 * the mark are pixel-identical in shape.
 *
 * Accessibility & performance:
 *   - prefers-reduced-motion / saveData -> a single static frame
 *   - IntersectionObserver -> pauses offscreen
 *   - capped devicePixelRatio, pre-rendered glyph sprites, ~30fps ceiling
 *
 * Usage:
 *   <canvas class="pdf-ascii" data-scene="hero" data-cell="15"></canvas>
 *   window.PDFORCE_ASCII.mount(canvas, { scene: 'hero' });
 */
(function () {
	'use strict';

	var REDUCED = typeof window.matchMedia === 'function' &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	var SAVE_DATA = !!(navigator.connection && navigator.connection.saveData);
	var MOTION_OK = !REDUCED && !SAVE_DATA;

	// Brand ramp: light tip -> signal -> deep. [r,g,b]
	var ORANGE = [
		[255, 176, 120], // #ffb078
		[255, 106, 43],  // #ff6a2b
		[230, 68, 10],   // #e6440a
	];
	var SIGNAL = [255, 90, 31];   // #ff5a1f
	var GREY = [150, 150, 150];
	var DIM = [74, 74, 78];

	// Density ramp, light -> heavy.
	var RAMP = [' ', '░', '▒', '▓', '█'];
	// Record glyphs — little documents spilling out of the fault.
	var RECORDS = ['▤', '▥', '▦', '▧'];

	function lerp(a, b, f) { return a + (b - a) * f; }
	function rampRGB(stops, t) {
		var seg = t * (stops.length - 1);
		var i = Math.min(stops.length - 2, Math.floor(seg));
		var f = seg - i;
		var a = stops[i], b = stops[i + 1];
		return [lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f)];
	}

	// Deterministic hash -> [0,1)
	function hash01(x, y, s) {
		var h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 974634211)) | 0;
		h = Math.imul(h ^ (h >>> 13), 1274126177);
		h ^= h >>> 16;
		return (h >>> 0) / 4294967296;
	}

	function starGlyph(x, y, frame) {
		var b = Math.floor(hash01(x, y, frame) * 150);
		if (b === 0) return '✦';
		if (b === 1) return '✧';
		if (b === 2) return '·';
		return null;
	}

	// Rippling field amplitude in [0,1]: three interfering travelling waves.
	function fieldAmp(x, y, cx, top, hh, w, t) {
		var dx = (x - cx) / 2, dy = y - top;
		var dist = Math.sqrt(dx * dx + dy * dy);
		var wave =
			0.5 * Math.sin(dist * 0.5 - t) +
			0.3 * Math.sin(x * 0.2 + y * 0.42 - t * 0.7) +
			0.2 * Math.sin(Math.abs(dx) * 0.75 + dy * 0.5 - t * 1.3);
		var level = 0.5 + 0.5 * wave;
		var edge = Math.max(0, 1 - Math.abs(x - cx) / (w * 0.5));
		var fade = Math.max(0, 1 - (dy / Math.max(1, hh)) * 0.5);
		return level * Math.pow(edge, 0.7) * fade;
	}

	function mount(canvas, opts) {
		opts = opts || {};
		var ctx = canvas.getContext('2d');
		var dpr = Math.min(2, window.devicePixelRatio || 1);
		var fontPx = 0, cellW = 0, cellH = 0, cols = 0, rows = 0;
		var spriteCache = Object.create(null);

		// crack raster: intensity per cell + position along the fault (0..1)
		var crackI = null, crackT = null, crackCells = [];

		function css(rgb) { return 'rgb(' + (rgb[0] | 0) + ',' + (rgb[1] | 0) + ',' + (rgb[2] | 0) + ')'; }

		function sprite(glyph, rgb) {
			var key = glyph + '|' + (rgb[0] >> 4) + '|' + (rgb[1] >> 4) + '|' + (rgb[2] >> 4);
			var s = spriteCache[key];
			if (s) return s;
			s = document.createElement('canvas');
			s.width = Math.max(1, Math.ceil(cellW * dpr));
			s.height = Math.max(1, Math.ceil(cellH * dpr));
			var c = s.getContext('2d');
			c.font = fontPx + 'px "JetBrains Mono","Fira Code",monospace';
			c.textAlign = 'center'; c.textBaseline = 'middle';
			c.fillStyle = css(rgb);
			c.fillText(glyph, s.width / 2, s.height / 2 + fontPx * 0.04);
			spriteCache[key] = s;
			return s;
		}

		// Rasterize the real crack path onto the cell grid, scaled to the hero.
		function buildCrack() {
			crackI = new Float32Array(cols * rows);
			crackT = new Float32Array(cols * rows);
			crackCells = [];
			var d = window.PDFORCE_CRACK_PATH;
			if (!d || typeof Path2D === 'undefined') return;
			var vb = (window.PDFORCE_CRACK_VIEWBOX || '0 0 586 731').split(/\s+/).map(Number);
			var vw = vb[2], vh = vb[3];

			// Fit the crack to ~92% of hero height, centered at 66% width.
			var targetH = rows * 0.92;
			var scale = targetH / vh;
			var offCol = Math.round(cols * 0.66 - (vw * scale) / 2);
			var offRow = Math.round((rows - targetH) / 2);

			var off = document.createElement('canvas');
			off.width = cols; off.height = rows;
			var oc = off.getContext('2d');
			oc.translate(offCol, offRow);
			oc.scale(scale, scale);
			oc.fillStyle = '#fff';
			oc.fill(new Path2D(d));
			var img = oc.getImageData(0, 0, cols, rows).data;

			var minX = cols, maxX = 0;
			for (var y = 0; y < rows; y++) {
				for (var x = 0; x < cols; x++) {
					var a = img[(y * cols + x) * 4 + 3] / 255;
					if (a > 0.12) {
						crackI[y * cols + x] = a;
						if (x < minX) minX = x;
						if (x > maxX) maxX = x;
					}
				}
			}
			// position along the fault (top-right=0 -> bottom-left=1) for the shine
			for (var y2 = 0; y2 < rows; y2++) {
				for (var x2 = 0; x2 < cols; x2++) {
					var idx = y2 * cols + x2;
					if (crackI[idx] > 0) {
						var t = Math.min(1, Math.max(0, ((maxX - x2) + y2) / Math.max(1, (maxX - minX) + rows)));
						crackT[idx] = t;
						crackCells.push(idx);
					}
				}
			}
		}

		// Records welling out of the fault and dripping down. When the hero shows
		// the real logo (data-emit-from), records spill from its crack instead of
		// an ASCII crack, so the mark stays the centerpiece.
		var particles = [];
		var nextSpawn = 1400 + Math.random() * 1200;
		var MAXP = 7;
		var emitEl = null;
		var emitSel = opts.emitFrom || canvas.getAttribute('data-emit-from');
		if (emitSel && typeof document !== 'undefined') emitEl = document.querySelector(emitSel);

		// crack-line emitter: rasterize the real crack inside the logo element
		// and spawn documents from points along the visible fissure.
		var logoCells = [];
		function buildLogoCrack() {
			var d = window.PDFORCE_CRACK_PATH;
			if (!d || typeof Path2D === 'undefined' || !emitEl) return;
			var cr = canvas.getBoundingClientRect();
			var lr = emitEl.getBoundingClientRect();
			var wCols = Math.max(2, Math.round(lr.width / cellW));
			var hRows = Math.max(2, Math.round(lr.height / cellH));
			var vb = (window.PDFORCE_CRACK_VIEWBOX || '0 0 586 731').split(/\s+/).map(Number);
			var vw = vb[2], vh = vb[3];
			var off = document.createElement('canvas');
			off.width = wCols; off.height = hRows;
			var oc = off.getContext('2d');
			oc.scale(wCols / vw, hRows / vh);
			oc.fillStyle = '#fff';
			oc.fill(new Path2D(d));
			var img = oc.getImageData(0, 0, wCols, hRows).data;
			logoCells = [];
			for (var y = 0; y < hRows; y++) {
				for (var x = 0; x < wCols; x++) {
					if (img[(y * wCols + x) * 4 + 3] / 255 > 0.25) {
						logoCells.push({ x: (lr.left - cr.left) / cellW + x, y: (lr.top - cr.top) / cellH + y });
					}
				}
			}
		}

		function spawnParticles(count) {
			if (emitEl && !logoCells.length) buildLogoCrack();
			var origin = null;
			if (logoCells.length) {
				var oc = logoCells[(Math.random() * logoCells.length) | 0];
				origin = { col: oc.x, row: oc.y };
			}
			for (var i = 0; i < count; i++) {
				var cx, cy;
				if (origin) {
					cx = origin.col + (Math.random() - 0.5) * 1.6;
					cy = origin.row + (Math.random() - 0.5) * 0.8;
				} else if (crackCells.length) {
					var idx = crackCells[(Math.random() * crackCells.length) | 0];
					cx = idx % cols; cy = (idx / cols) | 0;
				} else { break; }
				particles.push({
					x: cx, y: cy,
					rot: (Math.random() - 0.5) * 0.5,
					va: (Math.random() - 0.5) * 0.0022,
					sway: Math.random() * Math.PI * 2,
					sprite: (Math.random() * 3) | 0,
					scl: 0.85 + Math.random() * 0.35,
					vy: 0.005 + Math.random() * 0.009,
					vx: (Math.random() - 0.5) * 0.05,
					life: 1,
					decay: 0.0008 + Math.random() * 0.0012,
					ch: RECORDS[(Math.random() * RECORDS.length) | 0],
				});
			}
		}

		function stepParticles(timeMs) {
			for (var i = particles.length - 1; i >= 0; i--) {
				var p = particles[i];
				p.vy = Math.min(0.09, p.vy + 0.002);   // gentle gravity (slowed)
				p.sway += 0.012;
				p.x += p.vx + Math.sin(p.sway) * 0.014;
				p.y += p.vy;
				p.rot += p.va;
				p.life -= p.decay;
				if (p.y >= rows || p.life <= 0) particles.splice(i, 1);
			}
			// occasional drip along the visible crack line
			if (particles.length < MAXP && timeMs > nextSpawn) {
				spawnParticles(1 + (Math.random() < 0.5 ? 1 : 0));
				nextSpawn = timeMs + 1400 + Math.random() * 1200;
			}
		}

		// SVG-drawn document sprites — wide sheets like real paperwork.
		var docSprites = null;
		function buildDocSprites() {
			var scaleF = 1.15;
			var DW = 3.4, DH = 2.3;
			docSprites = [
				{ kind: 'lined' },
				{ kind: 'memo' },
				{ kind: 'signed' },
			].map(function (sp) {
				var W = DW * cellW * scaleF, H = DH * cellH * scaleF;
				var c = document.createElement('canvas');
				c.width = Math.ceil(W * dpr);
				c.height = Math.ceil(H * dpr);
				var g = c.getContext('2d');
				g.scale(dpr, dpr);
				var m = W * 0.08, fold = W * 0.16;
				g.strokeStyle = 'rgba(255,90,31,0.95)';
				g.lineWidth = Math.max(1, W * 0.035);
				g.lineJoin = 'round';
				g.beginPath();
				g.moveTo(m, m);
				g.lineTo(W - m - fold, m);
				g.lineTo(W - m, m + fold);
				g.lineTo(W - m, H - m);
				g.lineTo(m, H - m);
				g.closePath();
				g.stroke();
				g.beginPath();
				g.moveTo(W - m - fold, m);
				g.lineTo(W - m, m + fold);
				g.lineTo(W - m - fold, m + fold);
				g.closePath();
				g.stroke();
				function rule(x1, y1, x2, y2, w) {
					g.lineWidth = Math.max(1, (w || W * 0.028));
					g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
				}
				var x0 = m + W * 0.10, x2 = W - m - W * 0.08;
				if (sp.kind === 'lined') {
					rule(x0, H * 0.34, x2, H * 0.34);
					rule(x0, H * 0.48, x2, H * 0.48);
					rule(x0, H * 0.62, x2, H * 0.48 + H * 0.16);
					rule(x0, H * 0.74, x2 - W * 0.14, H * 0.74);
				} else if (sp.kind === 'memo') {
					g.fillStyle = 'rgba(255,90,31,0.55)';
					g.fillRect(x0, H * 0.12, W * 0.38, H * 0.09);
					rule(x0, H * 0.38, x2, H * 0.38);
					rule(x0, H * 0.54, x2 - W * 0.10, H * 0.54);
					rule(x0, H * 0.70, x2, H * 0.70);
				} else {
					rule(x0, H * 0.30, x2, H * 0.30);
					rule(x0, H * 0.46, x2 - W * 0.08, H * 0.46);
					g.lineWidth = Math.max(1.4, W * 0.04);
					g.beginPath();
					g.moveTo(x0 + W * 0.04, H * 0.76);
					g.bezierCurveTo(x0 + W * 0.14, H * 0.64, x0 + W * 0.26, H * 0.88, x0 + W * 0.38, H * 0.74);
					g.bezierCurveTo(x0 + W * 0.45, H * 0.66, x0 + W * 0.55, H * 0.80, x0 + W * 0.62, H * 0.74);
					g.stroke();
				}
				return { c: c, w: W, h: H };
			});
		}

		function drawFrame(timeMs) {
			var t = timeMs * 0.001;
			var frame = Math.floor(timeMs / 33);
			var W = canvas.clientWidth, H = canvas.clientHeight;
			ctx.clearRect(0, 0, W, H);

			var fieldTop = Math.floor(rows * 0.30);
			var fieldH = Math.max(1, rows - fieldTop);
			var prog = (timeMs % 6000) / 6000;
			var shinePos = (prog * 2.2) % 1;
			var shineStr = MOTION_OK ? 0.7 : 0.0;
			var pulse = MOTION_OK ? 0.82 + 0.18 * Math.sin(t * 2.0) : 1.0;

			for (var y = 0; y < rows; y++) {
				for (var x = 0; x < cols; x++) {
					var idx = y * cols + x;
					var glyph = null, rgb = null;

					// 1. the fault line (only when no logo element carries it)
					var ci = emitEl ? 0 : crackI[idx];
					if (ci > 0) {
						var ct = crackT[idx];
						var base = rampRGB(ORANGE, ct);
						var dshine = Math.abs(ct - shinePos);
						var inten = Math.max(0, 1 - dshine / 0.16) * shineStr;
						var r = base[0] + (255 - base[0]) * inten;
						var g = base[1] + (255 - base[1]) * inten;
						var b = base[2] + (255 - base[2]) * inten;
						var glowF = (0.55 + 0.45 * ci) * pulse;
						glyph = ci > 0.6 ? '█' : (ci > 0.35 ? '▓' : '▒');
						rgb = [r * glowF, g * glowF, b * glowF];
					}
					// 2. rippling data field — a quiet backdrop, not the focus
					else if (y >= fieldTop) {
						var amp = fieldAmp(x, y, cols * 0.6, fieldTop, fieldH, cols, MOTION_OK ? t * 0.85 : 0);
						amp += (hash01(x, y, 0) - 0.5) * 0.1;
						if (amp > 0.52) {  // high threshold -> sparse, calm field
							var ri = Math.min(RAMP.length - 1, Math.max(1, Math.floor(amp * RAMP.length)));
							glyph = RAMP[ri];
							var dim = 0.16 + 0.14 * amp;  // kept dim so the mark leads
							rgb = [SIGNAL[0] * dim * 0.6 + GREY[0] * dim * 0.4,
							       SIGNAL[1] * dim * 0.6 + GREY[1] * dim * 0.4,
							       SIGNAL[2] * dim * 0.6 + GREY[2] * dim * 0.4];
						}
					}
					// 3. starfield in the sky
					if (!glyph && y < fieldTop) {
						var sg = starGlyph(x, y, MOTION_OK ? (frame >> 3) : 0);
						if (sg) { glyph = sg; rgb = sg === '✦' ? SIGNAL : DIM; }
					}

					if (glyph && rgb) ctx.drawImage(sprite(glyph, rgb), x * cellW, y * cellH, cellW, cellH);
				}
			}

			// 4. documents drifting out of the logo crack
			if (!docSprites) buildDocSprites();
			for (var i = 0; i < particles.length; i++) {
				var p = particles[i];
				var fade = Math.max(0, Math.min(1, p.life * 1.4));
				var ds = docSprites[p.sprite];
				ctx.save();
				ctx.globalAlpha = Math.max(0, Math.min(1, fade * 1.15));
				ctx.translate((p.x + 0.5) * cellW, (p.y + 0.5) * cellH);
				ctx.rotate(p.rot);
				ctx.drawImage(ds.c, -ds.w * p.scl / 2, -ds.h * p.scl / 2, ds.w * p.scl, ds.h * p.scl);
				ctx.restore();
			}
		}

		function resize() {
			var w = canvas.clientWidth || (canvas.parentNode && canvas.parentNode.clientWidth) || 900;
			var h = canvas.clientHeight || 480;
			canvas.width = Math.round(w * dpr);
			canvas.height = Math.round(h * dpr);
			ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
			fontPx = parseInt(opts.cell || canvas.getAttribute('data-cell') || '15', 10);
			ctx.font = fontPx + 'px "JetBrains Mono","Fira Code",monospace';
			var m = ctx.measureText('█');
			cellW = Math.max(6, m.width || fontPx * 0.6);
			cellH = Math.round(fontPx * 1.12);
			cols = Math.max(1, Math.ceil(w / cellW));
			rows = Math.max(1, Math.ceil(h / cellH));
			spriteCache = Object.create(null);
			buildCrack();
		}

		resize();
		if (MOTION_OK) spawnParticles(4);

		var raf = null, running = false, start = 0;
		function loop(now) {
			if (!running) return;
			if (!start) start = now;
			stepParticles(now - start);
			drawFrame(now - start);
			raf = requestAnimationFrame(loop);
		}
		function play() { if (running || !MOTION_OK) return; running = true; start = 0; raf = requestAnimationFrame(loop); }
		function stop() { running = false; if (raf) cancelAnimationFrame(raf); raf = null; }

		if (MOTION_OK) {
			if ('IntersectionObserver' in window) {
				new IntersectionObserver(function (es) {
					es.forEach(function (e) { e.isIntersecting ? play() : stop(); });
				}, { threshold: 0.05 }).observe(canvas);
			} else { play(); }
		} else {
			drawFrame(0);
		}

		var rt;
		window.addEventListener('resize', function () {
			clearTimeout(rt);
			rt = setTimeout(function () { resize(); if (!MOTION_OK) drawFrame(0); }, 150);
		});

		return { play: play, stop: stop, redraw: function () { drawFrame(0); } };
	}

	function boot() {
		var nodes = document.querySelectorAll('canvas.pdf-ascii');
		for (var i = 0; i < nodes.length; i++) mount(nodes[i], {});
	}
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
	else boot();

	window.PDFORCE_ASCII = { mount: mount };
})();
