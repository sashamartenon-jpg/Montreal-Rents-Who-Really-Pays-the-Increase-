/* Animations au défilement, communes à toutes les pages : barre de progression, apparition des blocs,
   tracé progressif des courbes, compteurs. Tout est désactivé si l'utilisateur préfère réduire les animations. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const bar = document.createElement("div");
  bar.className = "progress";
  document.body.appendChild(bar);
  const top = document.querySelector(".top");
  const onScroll = () => {
    const h = document.documentElement;
    if (top) top.classList.toggle("solid", h.scrollTop > 40);
    bar.style.transform = `scaleX(${h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight)})`;
  };
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const SEL = "section.block .wrap > h2, section.block .wrap > .intro, section.block .wrap > .panel, section.block .wrap > .figure, " +
    ".qcard, .stepc, .card, .kpi, .skill, .ctxcard, .erd > .t, .gallery > *, .two > *, .cols > *, .flow > *, .sim > *, .models, .dico, details.ddl, .mapwrap, .yearbar";
  const mark = root => root.querySelectorAll(SEL).forEach(el => {
    if (el.closest(".heroband") || el.classList.contains("rv")) return;
    el.classList.add("rv");
    const sibs = [...el.parentElement.children].filter(x => x.matches(SEL));
    const i = sibs.indexOf(el);
    if (i > 0 && !el.style.getPropertyValue("--d")) el.style.setProperty("--d", `${Math.min(i, 5) * 0.08}s`);
  });

  const fmt = (v, dec, ref) => {
    const s = v.toLocaleString("fr-CA", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    return ref.includes("\u202f") || ref.includes("\u00a0") ? s : s.replace(/\u202f|\u00a0/g, " ");
  };
  const count = el => {
    const txt = el.textContent, re = /(\d{1,3}(?:[\s\u202f\u00a0]\d{3})+|\d+)(,\d+)?/g, m = [...txt.matchAll(re)];
    if (m.length !== 1 || el.dataset.counted) return;
    el.dataset.counted = "1";
    const raw = m[0][0], dec = m[0][2] ? m[0][2].length - 1 : 0;
    const target = parseFloat(raw.replace(/[\s\u202f\u00a0]/g, "").replace(",", "."));
    const pre = txt.slice(0, m[0].index), post = txt.slice(m[0].index + raw.length), t0 = performance.now(), dur = 1100;
    const step = now => {
      if (el.textContent !== el.dataset.last && el.dataset.last !== undefined) return;   // texte remplacé (changement de langue)
      const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = el.dataset.last = pre + fmt(target * e, dec, raw) + post;
      if (k < 1) requestAnimationFrame(step); else { el.textContent = txt; delete el.dataset.last; }
    };
    requestAnimationFrame(step);
  };
  const drawChart = el => {
    if (el.classList.contains("drawn")) return;
    el.querySelectorAll("path").forEach(p => {
      if (p.closest(".axis") || p.classList.contains("domain")) return;
      const fillNone = (p.getAttribute("fill") || getComputedStyle(p).fill) === "none";
      if (!fillNone || !p.getTotalLength) return;
      const L = p.getTotalLength();
      if (L < 40) return;
      p.style.strokeDasharray = L;
      p.style.strokeDashoffset = L;
      p.classList.add("draw");
      setTimeout(() => { p.style.strokeDasharray = ""; p.style.strokeDashoffset = ""; p.classList.remove("draw"); }, 2000);
    });
    el.querySelectorAll("rect").forEach((r, i) => { if (+r.getAttribute("width") > 2 && +r.getAttribute("height") > 2) { r.classList.add("grow"); r.style.animationDelay = `${Math.min(i, 12) * 0.04}s`; } });
    el.querySelectorAll("circle").forEach((c, i) => { c.classList.add("pop"); c.style.animationDelay = `${0.2 + Math.min(i, 40) * 0.015}s`; });
    el.classList.add("drawn");
  };

  // les blocs défilants (code, tableaux) doivent être atteignables au clavier
  document.querySelectorAll("pre.code, .tablewrap, .dico").forEach(el => {
    el.tabIndex = 0;
    if (!el.hasAttribute("aria-label")) el.setAttribute("aria-label", el.matches("pre.code") ? "Code, défilement horizontal" : "Tableau, défilement");
  });
  mark(document);
  const all = () => document.querySelectorAll(".rv:not(.in)");
  if (reduce || !("IntersectionObserver" in window)) {
    document.querySelectorAll(".rv").forEach(e => e.classList.add("in"));
    return;
  }
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add("in");
    e.target.querySelectorAll(".kpi b, .num").forEach(count);
    if (e.target.matches(".kpi b, .num")) count(e.target);
    io.unobserve(e.target);
  }), { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
  const cio = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { drawChart(e.target); cio.unobserve(e.target); }
  }), { threshold: 0.25 });
  const kio = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("typed"); kio.unobserve(e.target); }
  }), { threshold: 0.15 });
  all().forEach(e => io.observe(e));
  document.querySelectorAll(".chart").forEach(c => cio.observe(c));
  document.querySelectorAll("pre.code").forEach(c => kio.observe(c));
  document.querySelectorAll(".heroband .num").forEach(n => setTimeout(() => count(n), 500));
  new MutationObserver(ms => {
    ms.forEach(m => m.addedNodes.forEach(n => {
      if (n.nodeType !== 1) return;
      mark(n.parentElement || n);
      if (n.classList && n.classList.contains("rv") && !n.classList.contains("in")) io.observe(n);
      n.querySelectorAll && n.querySelectorAll(".rv:not(.in)").forEach(x => io.observe(x));
      n.querySelectorAll && n.querySelectorAll("pre.code:not(.typed)").forEach(x => kio.observe(x));
    }));
  }).observe(document.body, { childList: true, subtree: true });
})();

/* Motifs animés des bandeaux des pages de compétences : un canevas par page, dessiné avec les vraies données.
     cells  (Excel) : une cellule par formule du classeur ; une vague de recalcul part d'une cellule « modifiée »
     schema (SQL)   : les tables de la base et leurs clés étrangères ; une impulsion parcourt chaque jointure
     cities (Carte) : les régions métropolitaines à leur position ; l'onde est d'autant plus large que l'écart est grand
   Le motif se place à droite du texte s'il reste de la place, sinon en filigrane derrière lui (téléphone).
   Avec « réduire les animations », une seule image fixe est dessinée. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2, clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const MONO = '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace', SANS = '"Inter", "Helvetica Neue", Arial, sans-serif';
  const FX = {};

  FX.cells = {
    faint: .5,
    build(a, cv) {
      const n = parseInt((cv.dataset.n || "").replace(/\D/g, ""), 10) || 0;
      if (n < 1) return null;
      const cols = Math.max(4, Math.round(Math.sqrt(n * a.w / a.h))), rows = Math.ceil(n / cols), s = Math.min(a.w / cols, a.h / rows);
      return { n, cols, s, gx: a.x + (a.w - cols * s) / 2, gy: a.y + (a.h - rows * s) / 2, waves: [], next: 0 };
    },
    draw(c, m, t, a, ptr) {
      const at = (x, y) => { const cx = Math.floor((x - m.gx) / m.s), cy = Math.floor((y - m.gy) / m.s), i = cy * m.cols + cx; return cx >= 0 && cx < m.cols && cy >= 0 && i < m.n ? i : -1; };
      if (ptr.down) { ptr.down = false; const i = at(ptr.dx, ptr.dy); if (i >= 0) m.waves.push({ i, t0: t }); }
      if (t >= m.next) { m.waves.push({ i: (Math.random() * m.n) | 0, t0: t }); m.next = t + 2600 + Math.random() * 1600; }
      m.waves = m.waves.filter(w => t - w.t0 < 3800).slice(-5);
      const B = [[], [], [], [], []];
      const px = ptr.x == null ? -99 : (ptr.x - m.gx) / m.s - .5, py = ptr.x == null ? -99 : (ptr.y - m.gy) / m.s - .5;
      for (let i = 0; i < m.n; i++) {
        const cx = i % m.cols, cy = (i / m.cols) | 0;
        let v = 0;
        for (const w of m.waves) {
          const age = (t - w.t0) / 1000, k = (Math.hypot(cx - w.i % m.cols, cy - ((w.i / m.cols) | 0)) - age * 13) / 1.7;
          v += Math.exp(-k * k) * (1 - age / 3.8);
        }
        const d = Math.hypot(cx - px, cy - py);
        if (d < 3.2) v += (1 - d / 3.2) * .9;
        B[v > .75 ? 4 : v > .45 ? 3 : v > .22 ? 2 : v > .08 ? 1 : 0].push(i);
      }
      const al = [.17, .3, .46, .66, .92], q = m.s * .84;
      B.forEach((arr, b) => {
        c.fillStyle = `rgba(255,255,255,${al[b] * a.k})`; c.beginPath();
        for (const i of arr) c.rect(m.gx + (i % m.cols) * m.s, m.gy + ((i / m.cols) | 0) * m.s, q, q);
        c.fill();
      });
      for (const w of m.waves) {                 /* cellule « modifiée » : le jaune des cellules de saisie du classeur */
        const age = (t - w.t0) / 1000;
        if (age < 1.2) { c.fillStyle = `rgba(255,232,130,${(1 - age / 1.2) * (a.faint ? .45 : 1)})`; c.fillRect(m.gx + (w.i % m.cols) * m.s, m.gy + ((w.i / m.cols) | 0) * m.s, q, q); }
      }
    }
  };

  FX.schema = {
    faint: .55,
    build(a, cv) {
      let S; try { S = JSON.parse(cv.dataset.schema); } catch (e) { return null; }
      const dims = S.t.filter(n => n.startsWith("dim_")), facts = S.t.filter(n => !n.startsWith("dim_"));
      const cx = a.x + a.w / 2, cy = a.y + a.h / 2, rx = a.w * (a.faint ? .44 : .36), ry = a.h * .4, pos = {};
      dims.forEach((n, i) => { const an = -Math.PI / 2 + TAU * (i + .5) / dims.length; pos[n] = { n, x: cx + Math.cos(an) * rx, y: cy + Math.sin(an) * ry, an, dim: true }; });
      /* chaque table de faits se place du côté de ses dimensions (moyenne circulaire), puis l'ensemble est réparti régulièrement */
      const fa = facts.map(n => { let sx = 0, sy = 0; S.l.forEach(([f, d]) => { if (f === n && pos[d]) { sx += Math.cos(pos[d].an); sy += Math.sin(pos[d].an); } }); return { n, an: Math.atan2(sy, sx) }; })
        .sort((p, q) => p.an - q.an);
      fa.forEach((f, i) => { const an = fa[0].an + TAU * i / fa.length; pos[f.n] = { n: f.n, x: cx + Math.cos(an) * rx * .4, y: cy + Math.sin(an) * ry * .4, an }; });
      const links = S.l.filter(([f, d]) => pos[f] && pos[d]).map(([f, d], i) => ({ a: pos[d], b: pos[f], per: 2600 + (i * 977) % 2400, ph: (i * .37) % 1 }));
      return { nodes: Object.values(pos), links, t0: null };
    },
    draw(c, m, t, a, ptr) {
      if (m.t0 == null) m.t0 = reduce ? t - 1e5 : t;
      const intro = (t - m.t0) / 1600;
      let hot = null;
      if (ptr.x != null) { let bd = 46; m.nodes.forEach(n => { const d = Math.hypot(n.x - ptr.x, n.y - ptr.y); if (d < bd) { bd = d; hot = n; } }); }
      c.lineWidth = 1;
      m.links.forEach((l, i) => {
        const p = clamp01(intro * 1.4 - i * .06), on = hot && (l.a === hot || l.b === hot);
        if (p <= 0) return;
        c.strokeStyle = `rgba(255,255,255,${(on ? .95 : hot ? .22 : .5) * a.k})`;
        c.beginPath(); c.moveTo(l.a.x, l.a.y); c.lineTo(l.a.x + (l.b.x - l.a.x) * p, l.a.y + (l.b.y - l.a.y) * p); c.stroke();
        if (p >= 1 && !reduce) {                  /* une impulsion va de la dimension vers la table de faits : une jointure */
          const u = (t / l.per + l.ph) % 1, x = l.a.x + (l.b.x - l.a.x) * u, y = l.a.y + (l.b.y - l.a.y) * u, f = Math.sin(Math.PI * u);
          c.fillStyle = `rgba(255,232,214,${.95 * f * a.k})`; c.beginPath(); c.arc(x, y, 2.4, 0, TAU); c.fill();
          c.fillStyle = `rgba(255,232,214,${.22 * f * a.k})`; c.beginPath(); c.arc(x, y, 6, 0, TAU); c.fill();
        }
      });
      c.font = `500 11.5px ${MONO}`; c.textBaseline = "middle";
      m.nodes.forEach((n, i) => {
        const p = clamp01(intro * 1.6 - i * .05), k = (hot && hot !== n ? .55 : 1) * a.k * p;
        if (p <= 0) return;
        if (n.dim) { c.strokeStyle = `rgba(255,255,255,${.9 * k})`; c.lineWidth = 1.5; c.beginPath(); c.arc(n.x, n.y, 5.5 * p, 0, TAU); c.stroke(); c.fillStyle = `rgba(255,255,255,${.22 * k})`; c.fill(); }
        else { c.fillStyle = `rgba(255,255,255,${.92 * k})`; c.fillRect(n.x - 5 * p, n.y - 5 * p, 10 * p, 10 * p); }
        if (!a.faint) {
          c.fillStyle = `rgba(255,255,255,${.96 * k})`;
          if (n.dim) { const r = Math.cos(n.an) >= -.01; c.textAlign = r ? "left" : "right"; c.fillText(n.n, n.x + (r ? 11 : -11), n.y); }
          else { const r = Math.cos(n.an) >= 0; c.textAlign = r ? "left" : "right"; c.fillText(n.n, n.x + (r ? 11 : -11), n.y + (Math.sin(n.an) >= 0 ? 9 : -9)); }
        }
      });
    }
  };

  let villes = null;
  FX.cities = {
    faint: .7, full: true,
    build(a) {
      const el = document.getElementById("carte");
      if (!el || typeof d3 === "undefined") return null;
      try { villes = villes || JSON.parse(el.textContent).villes.filter(v => v.lat != null && v.lon != null); } catch (e) { return null; }
      const proj = d3.geoConicConformal().parallels([49, 77]).rotate([96, 0])
        .fitExtent([[a.x + 16, a.y + 16], [a.x + a.w - 16, a.y + a.h - 16]], { type: "MultiPoint", coordinates: villes.map(v => [v.lon, v.lat]) });
      const pts = villes.map((v, i) => { const xy = proj([v.lon, v.lat]); return { x: xy[0], y: xy[1], v, mtl: v.id === 7, ph: (i * .618) % 1 }; });
      const links = [], seen = new Set();          /* chaque région reliée à ses deux plus proches voisines */
      pts.forEach((p, i) => {
        pts.map((q, j) => [j, Math.hypot(p.x - q.x, p.y - q.y)]).filter(d => d[0] !== i).sort((x, y) => x[1] - y[1]).slice(0, 2).forEach(([j]) => {
          const key = i < j ? i + "-" + j : j + "-" + i;
          if (!seen.has(key)) { seen.add(key); links.push([p, pts[j]]); }
        });
      });
      return { pts, links };
    },
    draw(c, m, t, a, ptr) {
      c.strokeStyle = `rgba(255,255,255,${.24 * a.k})`; c.lineWidth = 1; c.beginPath();
      m.links.forEach(([p, q]) => { c.moveTo(p.x, p.y); c.lineTo(q.x, q.y); }); c.stroke();
      let hot = null;
      if (ptr.x != null) { let bd = 26; m.pts.forEach(p => { const d = Math.hypot(p.x - ptr.x, p.y - ptr.y); if (d < bd) { bd = d; hot = p; } }); }
      m.pts.forEach(p => {
        const e = p.v.ecart, col = p.mtl ? "255,150,186" : "255,255,255", k = a.k * (p.x < a.textRight + 20 ? .5 : 1);
        if (e > 0) {                                /* onde : rayon proportionnel à l'écart entre loyer demandé et loyer payé */
          const u = reduce ? .55 : (t / 3400 + p.ph) % 1, R = (7 + e / 15) * (1 - Math.pow(1 - u, 2));
          c.strokeStyle = `rgba(${col},${(1 - u) * .6 * k})`; c.lineWidth = p.mtl ? 2 : 1.2; c.beginPath(); c.arc(p.x, p.y, R, 0, TAU); c.stroke();
        }
        c.fillStyle = `rgba(${col},${(p.v.paye ? .95 : .5) * k})`; c.beginPath(); c.arc(p.x, p.y, 1.6 + (p.v.demande || 1300) / 900, 0, TAU); c.fill();
      });
      if (hot && !a.faint && hot.x > a.textRight + 20) {
        const en = window.LANG === "en", e = hot.v.ecart, nf = new Intl.NumberFormat(en ? "en-CA" : "fr-CA");
        const amt = e == null ? "" : "  " + (e > 0 ? "+" : e < 0 ? "−" : "") + (en ? "$" + nf.format(Math.abs(e)) : nf.format(Math.abs(e)) + " $");
        c.font = `600 12px ${SANS}`; c.textBaseline = "middle"; c.textAlign = hot.x > a.x + a.w * .6 ? "right" : "left";
        c.fillStyle = "rgba(255,255,255,.96)"; c.fillText(hot.v.nom.split(" (")[0] + amt, hot.x + (c.textAlign === "right" ? -12 : 12), hot.y - 12);
      }
    }
  };

  document.querySelectorAll("canvas.herofx").forEach(cv => {
    const host = cv.closest(".heroband"), fx = FX[cv.dataset.fx], c = cv.getContext ? cv.getContext("2d") : null;
    if (!host || !fx || !c) return;
    let W = 0, H = 0, a = null, m = null, on = false, last = 0, rt = 0;
    const ptr = { x: null, y: null, down: false, dx: 0, dy: 0 };
    const size = () => {
      const hr = host.getBoundingClientRect();
      W = Math.round(hr.width); H = Math.round(hr.height);
      if (W < 200 || H < 160) { m = null; return; }
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); c.setTransform(dpr, 0, 0, dpr, 0, 0);
      let right = 0;                               /* bord droit réel du texte du bandeau */
      host.querySelectorAll(".phero > *").forEach(e => { const rg = document.createRange(); rg.selectNodeContents(e); right = Math.max(right, rg.getBoundingClientRect().right - hr.left); });
      const room = W - 28 - (right + 44);
      a = fx.full ? { x: 14, y: 84, w: W - 28, h: H - 84 - 22, k: W < 700 ? fx.faint : .9, faint: W < 700, textRight: W < 700 ? W : right }
        : room >= 300 ? { x: right + 44, y: 86, w: Math.min(room, 560), h: H - 86 - 30, k: 1, faint: false }
                      : { x: 14, y: 72, w: W - 28, h: H - 72 - 16, k: fx.faint || .3, faint: true, textRight: W };
      m = a.h > 80 ? fx.build(a, cv) : null;
      c.clearRect(0, 0, W, H);
      if (m) fx.draw(c, m, performance.now(), a, ptr);
    };
    const tick = t => {
      if (!on) return;
      if (m && !document.hidden && t - last > 33) { last = t; c.clearRect(0, 0, W, H); fx.draw(c, m, t, a, ptr); }
      requestAnimationFrame(tick);
    };
    size();
    const resize = () => { clearTimeout(rt); rt = setTimeout(size, 160); };
    if ("ResizeObserver" in window) new ResizeObserver(resize).observe(host); else addEventListener("resize", resize);
    document.addEventListener("langchange", resize);            /* le texte change de longueur : le motif se replace */
    if (reduce || !("IntersectionObserver" in window)) return;
    new IntersectionObserver(es => {
      const v = es[es.length - 1].isIntersecting;
      if (v && !on) { on = true; requestAnimationFrame(tick); } else if (!v) on = false;
    }).observe(host);
    host.addEventListener("pointermove", e => { const r = host.getBoundingClientRect(); ptr.x = e.clientX - r.left; ptr.y = e.clientY - r.top; }, { passive: true });
    host.addEventListener("pointerleave", () => { ptr.x = ptr.y = null; }, { passive: true });
    host.addEventListener("pointerdown", e => { const r = host.getBoundingClientRect(); ptr.dx = e.clientX - r.left; ptr.dy = e.clientY - r.top; ptr.down = true; }, { passive: true });
  });

  /* accueil : les cartes de verre s'inclinent légèrement vers le pointeur (souris seulement) */
  const glass = document.querySelector(".glass-stack");
  if (glass && !reduce && matchMedia("(hover: hover) and (pointer: fine)").matches) {
    const zone = glass.closest(".heroband") || glass.parentElement;
    zone.addEventListener("pointermove", e => {
      const r = glass.getBoundingClientRect();
      glass.style.setProperty("--ry", (clamp01((e.clientX - r.left) / r.width * .5 + .25) * 10 - 5).toFixed(2) + "deg");
      glass.style.setProperty("--rx", (5 - clamp01((e.clientY - r.top) / r.height * .5 + .25) * 10).toFixed(2) + "deg");
    }, { passive: true });
    zone.addEventListener("pointerleave", () => { glass.style.setProperty("--rx", "0deg"); glass.style.setProperty("--ry", "0deg"); }, { passive: true });
  }
})();
