/* Code commun aux pages de compétences : coloration syntaxique légère (SQL, Excel). */
const KW = {
  sql: "SELECT FROM WHERE JOIN LEFT INNER CROSS ON AND OR NOT AS WITH ORDER BY GROUP HAVING LIMIT CASE WHEN THEN ELSE END IN IS NULL DESC ASC OVER PARTITION VALUES DISTINCT USING UNION ALL CAST INTEGER CREATE TABLE VIEW INDEX PRIMARY KEY FOREIGN REFERENCES CHECK UNIQUE TEXT REAL PRAGMA WINDOW ROWS BETWEEN PRECEDING CURRENT ROW GLOB DEFAULT NULLS LAST",
  py: "def return if elif else for in import from as with assert not and or is None True False lambda class try except raise while",
  dax: "VAR RETURN IF NOT TRUE FALSE",
  xl: ""
};
function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function highlight(code, lang) {
  const kws = new Set((KW[lang] || "").split(" ").filter(Boolean));
  const ci = lang === "sql" || lang === "dax";
  const com = lang === "py" ? "#" : (lang === "sql" ? "--" : "//");
  const re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(--[^\n]*|#[^\n]*|\/\/[^\n]*)|(\b\d+(?:\.\d+)?\b)|([A-Za-zÀ-ÿ_][\w.À-ÿ]*)(\s*\()?/g;
  let out = "", last = 0, m;
  while ((m = re.exec(code))) {
    out += esc(code.slice(last, m.index));
    last = re.lastIndex;
    if (m[1]) out += `<span class="s">${esc(m[1])}</span>`;
    else if (m[2]) {
      if (m[2].startsWith(com)) out += `<span class="c">${esc(m[2])}</span>`;
      else { out += esc(m[2][0]); re.lastIndex = m.index + 1; last = re.lastIndex; }
    }
    else if (m[3]) out += `<span class="n">${m[3]}</span>`;
    else if (m[4]) {
      const w = m[4], paren = m[5] || "";
      if (kws.has(ci ? w.toUpperCase() : w)) out += `<span class="k">${esc(w)}</span>${esc(paren)}`;
      else if (paren) out += `<span class="f">${esc(w)}</span>${esc(paren)}`;
      else out += esc(w);
    }
  }
  return out + esc(code.slice(last));
}
document.querySelectorAll("pre.code[data-lang]").forEach(el => { el.innerHTML = highlight(el.textContent, el.dataset.lang); });
const fmtFR = v => v == null ? "NULL" : (typeof v === "number" ? new Intl.NumberFormat(window.LANG === "en" ? "en-CA" : "fr-CA", { maximumFractionDigits: Number.isInteger(v) ? 0 : 2 }).format(v) : String(v));
function resultTable(cols, rows) {
  const isYear = cols.map(c => /annee|year/i.test(c));
  // une colonne de texte (nom, type, période) se lit à gauche ; une colonne de nombres s'aligne à droite
  const isText = cols.map((c, i) => rows.some(r => typeof r[i] === "string"));
  const cl = i => (isText[i] ? ' class="t"' : "");
  return `<table class="data"><tr>${cols.map((c, i) => `<th${cl(i)}>${esc(c)}</th>`).join("")}</tr>${rows.map(r => `<tr>${r.map((v, i) => `<td${cl(i)}>${esc(isYear[i] ? String(v) : fmtFR(v))}</td>`).join("")}</tr>`).join("")}</table>`;
}
