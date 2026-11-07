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
  all().forEach(e => io.observe(e));
  document.querySelectorAll(".chart").forEach(c => cio.observe(c));
  document.querySelectorAll(".heroband .num").forEach(n => setTimeout(() => count(n), 500));
  new MutationObserver(ms => {
    ms.forEach(m => m.addedNodes.forEach(n => {
      if (n.nodeType !== 1) return;
      mark(n.parentElement || n);
      if (n.classList && n.classList.contains("rv") && !n.classList.contains("in")) io.observe(n);
      n.querySelectorAll && n.querySelectorAll(".rv:not(.in)").forEach(x => io.observe(x));
    }));
  }).observe(document.body, { childList: true, subtree: true });
})();
