/* Langue du site : FR par défaut, EN au choix. Le choix est mémorisé (localStorage)
   et suivi sur toutes les pages. Chaque page fournit ses traductions dans PAGE_EN
   (clés data-i18n) ; la page d'accueil garde son propre moteur (table T) et n'expose
   pas de PAGE_EN. Les éléments communs (navigation, lien d'évitement, pied de page)
   sont traduits ici. */
(() => {
  const NAV = {
    "index.html": { fr: "Analyse", en: "Analysis" },
    "carte.html": { fr: "Carte", en: "Map" },
    "excel.html": { fr: "Excel", en: "Excel" },
    "sql.html": { fr: "SQL", en: "SQL" }
  };
  const SKIP = { fr: "Aller au contenu", en: "Skip to content" };
  const SCROLL = {
    code: { fr: "Code, défilement horizontal", en: "Code, scrolls horizontally" },
    table: { fr: "Tableau, défilement", en: "Table, scrollable" }
  };
  const saved = new Map();
  let frTitle = document.title;

  const BRAND = { fr: "Loyers Montréal", en: "Montreal Rents" };
  function apply() {
    const L = window.LANG, en = L === "en";
    document.documentElement.lang = L;
    const br = document.querySelector("a.brand");
    if (br && br.firstChild && br.firstChild.nodeType === 3) br.firstChild.textContent = BRAND[L] + " ";
    document.querySelectorAll(".nav a").forEach(a => {
      const d = NAV[a.getAttribute("href")];
      if (d) a.textContent = d[L];
    });
    const skip = document.querySelector("a.skip");
    if (skip) skip.textContent = SKIP[L];
    // images et liens qui ont une variante anglaise (figures, captures, classeur)
    document.querySelectorAll("[data-en-src]").forEach(img => {
      if (!img.dataset.frSrc) img.dataset.frSrc = img.getAttribute("src");
      img.setAttribute("src", en ? img.dataset.enSrc : img.dataset.frSrc);
    });
    // textes non affichés : description des images et libellés lus par les lecteurs d'écran
    document.querySelectorAll("[data-en-alt],[data-en-aria]").forEach(el => {
      for (const [attr, k] of [["alt", "enAlt"], ["aria-label", "enAria"]]) {
        if (el.dataset[k] == null) continue;
        const f = "fr" + k.slice(2);
        if (el.dataset[f] == null) el.dataset[f] = el.getAttribute(attr) || "";
        el.setAttribute(attr, en ? el.dataset[k] : el.dataset[f]);
      }
    });
    document.querySelectorAll("[data-en-href]").forEach(a => {
      if (!a.dataset.frHref) a.dataset.frHref = a.getAttribute("href");
      a.setAttribute("href", en ? a.dataset.enHref : a.dataset.frHref);
    });
    const P = window.PAGE_EN;
    if (P) {
      document.querySelectorAll("[data-i18n]").forEach(el => {
        const v = P[el.dataset.i18n];
        if (v == null) return;
        if (!saved.has(el)) saved.set(el, el.innerHTML);
        el.innerHTML = en ? v : saved.get(el);
      });
      if (P["@title"]) document.title = en ? P["@title"] : frTitle;
    }
    const bf = document.getElementById("lang-fr"), be = document.getElementById("lang-en");
    if (bf) bf.setAttribute("aria-pressed", String(!en));
    if (be) be.setAttribute("aria-pressed", String(en));
    document.dispatchEvent(new CustomEvent("langchange", { detail: { lang: L } }));
    // après les re-rendus déclenchés par langchange : les zones défilantes restent
    // atteignables au clavier et annoncées dans la bonne langue
    document.querySelectorAll("pre.code, .tablewrap, .dico").forEach(el => {
      el.tabIndex = 0;
      el.setAttribute("aria-label", el.matches("pre.code") ? SCROLL.code[L] : SCROLL.table[L]);
    });
  }

  function set(L) {
    window.LANG = L;
    try { localStorage.setItem("loyers.lang", L); } catch (e) {}
    apply();
  }
  const bf = document.getElementById("lang-fr"), be = document.getElementById("lang-en");
  if (bf) bf.addEventListener("click", () => set("fr"));
  if (be) be.addEventListener("click", () => set("en"));
  apply();
})();
