"""
Assemble le site multipage dans docs/ (GitHub Pages).

Pages : index.html (analyse), carte.html, excel.html, sql.html.
Le style vient du gabarit de l'accueil ; les données, les formules Excel et les extraits de code
Python sont lus dans les fichiers du projet au moment de la construction :
ce que montre le site est toujours ce que contient le dépôt.

Exécution : python src/build_site.py [SITE_URL] [DOSSIER_APERCU]
  SITE_URL        adresse publique (rend l'image d'aperçu LinkedIn absolue)
  DOSSIER_APERCU  facultatif : copie des pages pour un aperçu hébergé
"""
import ast
import html
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from openpyxl import load_workbook
sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).resolve().parents[1]
SRC, DOCS = ROOT / "src", ROOT / "docs"
SITE_URL = (sys.argv[1] if len(sys.argv) > 1 else "").rstrip("/")
PREVIEW = Path(sys.argv[2]) if len(sys.argv) > 2 else None

PAGES = [("index.html", "Analyse"), ("carte.html", "Carte"), ("excel.html", "Excel"), ("sql.html", "SQL")]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=Inter+Tight:wght@300;400;500;600&family=Inter:wght@400;500;600&display=swap">\n')
SKELETON = ('<!doctype html>\n<html lang="fr">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n<meta name="theme-color" content="#1f5fa8">\n')


LANG_BOOT = ('<script>window.LANG=(function(){try{var q=new URLSearchParams(location.search).get("lang");'
             'if(q==="en"||q==="fr"){localStorage.setItem("loyers.lang",q);return q}'
             'return localStorage.getItem("loyers.lang")==="en"?"en":"fr"}catch(e){return"fr"}})();</script>\n')
LANG_SEG = ('<div class="seg" role="group" aria-label="Langue / Language"><button type="button" id="lang-fr" aria-pressed="true">FR</button>'
            '<button type="button" id="lang-en" aria-pressed="false">EN</button></div>')


def header(current, actions=""):
    links = "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == current else ""}>{label}</a>' for f, label in PAGES)
    return (LANG_BOOT + '<a class="skip" href="#main">Aller au contenu</a>\n'
            f'<header class="top">\n  <div class="wrap topbar">\n'
            f'    <a class="brand" href="index.html">Loyers Montréal <span>· 1992–2026</span></a>\n'
            f'    <nav class="nav" aria-label="Pages du projet">{links}</nav>\n'
            f'    <div class="top-actions">{actions}{LANG_SEG}</div>\n  </div>\n</header>')


INDEX_ACTIONS = '<button class="btn" id="share" type="button" data-i18n="share">Copier le lien</button>'
FOOTER = ('<footer><div class="wrap">Données : Statistique Canada et SCHL, Licence du gouvernement ouvert – Canada. '
          'Extraction le 4 novembre 2026. '
          'Site accessible : navigation au clavier, contrastes AA, animations coupées si votre système le demande.</div></footer>')


# ------------------------------------------------------------------ contenus lus dans le projet
def py_function(path, name):
    src = path.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    raise KeyError(name)


def py_between(path, start, end):
    src = path.read_text(encoding="utf-8")
    i = src.index(start)
    j = src.index(end, i)
    lines = src[i:j].rstrip().splitlines()
    indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    return "\n".join(l[indent:] for l in lines)


def excel_facts():
    wb = load_workbook(DOCS / "assets" / "modele_loyers_montreal.xlsx")
    n = sum(1 for ws in wb.worksheets for row in ws.iter_rows() for c in row
            if (isinstance(c.value, str) and c.value.startswith("=")) or hasattr(c.value, "text"))
    x = wb["Excel 365"]
    xl365 = lambda cell: x[cell].value.text.replace("_xlfn._xlws.", "").replace("_xlfn.", "")
    assert "XLOOKUP" in xl365("G7") and "SORT" in xl365("B20"), "feuille Excel 365 déplacée"
    d, k = wb["Tableau de bord"], wb["Calculs"]
    cells = [c for row in k.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    find = lambda col, start: next(c for c in cells if c.column_letter == col and c.value.startswith(start))
    rank = find("E", "=RANK(D")
    assert d["E9"].value.startswith("=(SUMIFS") and d["H9"].value.startswith("=IFERROR"), "cellules du tableau de bord déplacées"
    visible = [ws.title for ws in wb.worksheets if ws.sheet_state == "visible"]
    return n, {
        "__XLF_DASH_E9__": d["E9"].value, "__XLF_DASH_H9__": d["H9"].value,
        "__XLF_CALC_RANK__": rank.value, "__XLF_CALC_SORT__": k.cell(row=rank.row, column=6).value,
        "__XLF_CALC_E5__": k["E5"].value, "__XLF_SC_NPER__": wb["Scénarios"]["H11"].value,
        "__XLF_PROV_V__": find("M", "=CHOOSE").value, "__XLF_PROV_CLASS__": find("T", "=IF(AND(P").value,
        "__XLF_PROV_LABEL__": find("Q", "=A").value, "__XLF_SEUIL__": next(c for c in cells if c.value.startswith("=PERCENTILE(ProvValeurs")).value,
        "__XLF_VILLE_CLASS__": find("O", "=IF(AND(L").value,
        "__XLF_365_LET__": xl365("G7"), "__XLF_365_SORT__": xl365("B20"), "__XLF_365_GAINS__": xl365("J21"),
    }, len(visible), len(wb.worksheets)


def sql_volumes():
    con = sqlite3.connect(ROOT / "data" / "loyers.sqlite")
    q = lambda t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    txt = (f"Volumes : {q('fait_loyer')} loyers annuels, {q('fait_loyer_trimestriel')} loyers trimestriels "
           f"({q('dim_rmr')} régions), {q('fait_inoccupation')} taux d'inoccupation, {q('ipc') + q('ipc_provinces')} valeurs d'IPC, "
           f"{q('schl_roulement')} indicateurs SCHL.")
    txt_en = (f"Volumes: {q('fait_loyer')} annual rents, {q('fait_loyer_trimestriel')} quarterly rents "
              f"({q('dim_rmr')} metro areas), {q('fait_inoccupation')} vacancy rates, {q('ipc') + q('ipc_provinces')} CPI values, "
              f"{q('schl_roulement')} CMHC indicators.")
    con.close()
    return txt, txt_en


def index_demo():
    """Plan d'exécution et temps mesurés avec puis sans l'index ix_trim_geo_est, sur une copie de la base."""
    import shutil, tempfile, time
    tmp = Path(tempfile.mkdtemp()) / "loyers.sqlite"
    shutil.copy(ROOT / "data" / "loyers.sqlite", tmp)
    q = "SELECT periode, loyer\nFROM fait_loyer_trimestriel\nWHERE geo_id = 7 AND estimation = 'A'\nORDER BY periode DESC;"
    flat = q.replace("\n", " ")

    def run():
        con = sqlite3.connect(tmp)
        plan = "\n".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN " + flat))
        best = 1e9
        for _ in range(5):
            t0 = time.perf_counter()
            for _ in range(3000):
                con.execute(flat).fetchall()
            best = min(best, (time.perf_counter() - t0) / 3000 * 1e6)
        n = con.execute("SELECT COUNT(*) FROM fait_loyer_trimestriel").fetchone()[0]
        con.close()
        return plan, best, n

    plan_on, us_on, n = run()
    con = sqlite3.connect(tmp)
    con.execute("DROP INDEX ix_trim_geo_est")
    con.commit()
    con.close()
    plan_off, us_off, _ = run()
    shutil.rmtree(tmp.parent, ignore_errors=True)
    assert "USING INDEX ix_trim_geo_est" in plan_on and "SCAN" in plan_off, (plan_on, plan_off)
    return {"__IX_QUERY__": q, "__IX_PLAN_ON__": plan_on, "__IX_PLAN_OFF__": plan_off,
            "__IX_US_ON__": f"{us_on:.0f}", "__IX_US_OFF__": f"{us_off:.0f}", "__IX_ROWS__": str(n),
            "__IX_RATIO__": fr_num(us_off / us_on, 1), "__IX_RATIO_EN__": f"{us_off / us_on:.1f}",
            "__IX_DDL__": "CREATE INDEX ix_trim_geo_est ON fait_loyer_trimestriel (geo_id, estimation, periode);"}


def fr_num(x, d=2):
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


# ------------------------------------------------------------------ assemblage
index_tpl = (SRC / "index.template.html").read_text(encoding="utf-8")
CSS = index_tpl[index_tpl.index("<style>"):index_tpl.index("</style>") + len("</style>")]
COMMON_JS = (SRC / "pages" / "common.js").read_text(encoding="utf-8")
MOTION_JS = (SRC / "pages" / "motion.js").read_text(encoding="utf-8")
I18N_JS = (SRC / "pages" / "i18n.js").read_text(encoding="utf-8")
data = (DOCS / "data" / "data.json").read_text(encoding="utf-8").replace("</", "<\\/")
sqlres = (DOCS / "data" / "sql_results.json").read_text(encoding="utf-8").replace("</", "<\\/")
carte_json = (DOCS / "data" / "carte.json").read_text(encoding="utf-8").replace("</", "<\\/")
geo_json = (DOCS / "data" / "canada_provinces.geojson").read_text(encoding="utf-8")
N_PAYE = sum(1 for v in json.loads(carte_json.replace("<\\/", "</"))["villes"] if v["paye"])


def scene_json():
    """Données de la scène de défilement de l'accueil : contours projetés du Canada
    (geo.py, projection de Statistique Canada) et régions où le loyer payé est publié."""
    import geo
    rings, (bx0, by0, bx1, by1) = geo.outlines((-141.0, 41.7, -52.6, 70.0), 0.004)
    W = 1000.0
    sx = W / (bx1 - bx0)
    H = (by1 - by0) * sx
    def px(x, y):
        return round((x - bx0) * sx, 1), round(H - (y - by0) * sx, 1)
    out_rings = []
    for _, r in rings:
        out_rings.append([c for xy in r for c in px(xy[0], xy[1])])
    C = json.loads(carte_json.replace("<\\/", "</"))
    villes = []
    for v in C["villes"]:
        if not v.get("paye") or v.get("lat") is None:
            continue
        x, y = geo.proj(v["lon"], v["lat"])
        x, y = px(float(x), float(y))
        villes.append({"n": v["nom"].split(" (")[0], "x": x, "y": y, "g": v["ecart_pct"], "mtl": v["id"] == 7})
    return json.dumps({"w": 1000, "h": round(H, 1), "rings": out_rings, "villes": villes},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

def package_program():
    """Paquet public de l'évaluateur : script, données, exemple, mode d'emploi."""
    import io
    import subprocess
    import zipfile
    demo = subprocess.run([sys.executable, str(SRC / "evalue_loyer.py"), "--fichier", str(ROOT / "data" / "exemples" / "annonces_exemple.csv")],
                          capture_output=True, text=True, check=True).stdout
    lisezmoi = (
        "Évaluateur de loyer (Montréal) — programme public du projet « Loyers à Montréal »\n\n"
        "Situe un loyer par rapport au marché montréalais : moyenne SCHL 2025, hausse depuis le début\n"
        "du bail (avec et sans inflation), potentiel de relocation (2 chambres), taux d'effort.\n\n"
        "Prérequis : Python 3.9 ou plus. Aucune bibliothèque à installer.\n\n"
        "Essais :\n"
        "  python3 evalue_loyer.py --loyer 1450 --type 2ch --annee-bail 2021 --revenu 60000\n"
        "  python3 evalue_loyer.py --fichier annonces_exemple.csv\n"
        "  python3 evalue_loyer.py --fichier annonces_exemple.csv --json\n\n"
        "Pour évaluer vos propres logements : un fichier CSV avec les colonnes\n"
        "  id,loyer,type,annee_bail,revenu   (revenu facultatif ; types : studio, 1ch, 2ch, 3ch ou « 4 1/2 »...)\n"
        "annonces_exemple.csv est un exemple FICTIF de liste d'agence.\n\n"
        "Données incluses (dossier donnees/), extraites le 4 novembre 2026 : Statistique Canada\n"
        "34-10-0133-01, 18-10-0005-01, 46-10-0092-01 (estimations expérimentales) et SCHL,\n"
        "Rapport sur le marché locatif 2025. Licence du gouvernement ouvert – Canada. Code : MIT.\n\n"
        "Limites : moyennes de la RMR de Montréal (immeubles de 3 logements et plus), sans détail par\n"
        "quartier ni par état du logement. Le programme situe un loyer ; il ne fixe pas un prix.\n"
        "Exemple de sortie complète dans demo_sortie.txt\n")
    dest = DOCS / "assets" / "programme_evaluateur.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(SRC / "evalue_loyer.py", "evalue_loyer.py")
        z.write(ROOT / "data" / "exemples" / "annonces_exemple.csv", "annonces_exemple.csv")
        for f in ("fait_loyers_montreal.csv", "ipc_montreal.csv", "schl_roulement.csv", "fait_loyer_trimestriel.csv"):
            z.write(ROOT / "data" / "clean" / f, f"donnees/{f}")
        z.writestr("LISEZMOI.txt", lisezmoi)
        z.writestr("demo_sortie.txt", demo)
    return demo


DEMO_EVAL = ""  # évaluateur retiré du site (réservé à un prochain projet) ; package_program() conservé pour le réactiver
n_formulas, xlf, n_visible, n_sheets = excel_facts()
SQL_FILES = sorted((ROOT / "sql").glob("*.sql"))
DDL_T = (ROOT / "sql" / "schema" / "01_tables.sql").read_text(encoding="utf-8").strip()
DDL_V = (ROOT / "sql" / "schema" / "02_vues.sql").read_text(encoding="utf-8").strip()
N_TABLES, N_VUES = len(re.findall(r"^CREATE TABLE", DDL_T, re.M)), len(re.findall(r"^CREATE VIEW", DDL_V, re.M))
import csv
DICO = list(csv.DictReader((ROOT / "data" / "ref" / "dictionnaire.csv").open(encoding="utf-8"), delimiter=";"))
assert all(len(r) == 6 and None not in r for r in DICO), "dictionnaire.csv mal formé"

stats = json.loads((DOCS / "assets" / "python" / "stats.json").read_text(encoding="utf-8"))
INS = json.loads((DOCS / "data" / "data.json").read_text(encoding="utf-8"))["insights"]
# délai de rattrapage du scénario B (locataires en place), même calcul que la fonction NPM du classeur
import math
_b = INS["hausse_non_reloues_2025"] / 100
_n = math.ceil(math.log(INS["mtl_demande_dernier"] / INS["loyer_2ch_2025"]) / math.log(1 + _b))
RATTRAPAGE = f"{2025 + _n}, soit dans {_n} ans"
code = {
    "__PY_VALIDATE__": py_function(SRC / "pipeline.py", "validate"),
    "__PY_REAL__": py_between(SRC / "pipeline.py", "# --- Faits : loyers Montréal par taille", "# --- Faits : loyers 2 chambres"),
    "__PY_CHECK__": py_function(SRC / "build_db.py", "check"),
    "__PY_FETCH__": py_function(SRC / "fetch_statcan.py", "download"),
    "__PY_GEO__": py_function(SRC / "geo.py", "proj"),
    "__PY_CHOW__": py_function(SRC / "rupture.py", "chow_f") + "\n\n\n" + py_between(SRC / "rupture.py", "    # Hypothèse nulle", "    return {"),
    "__DDL_TABLES__": DDL_T, "__DDL_VUES__": DDL_V,
}
SQL_VOL_FR, SQL_VOL_EN = sql_volumes()


def en_num(x, d=2):
    return f"{x:.{d}f}".replace("-", "\u2212")


IX = index_demo()
shutil.copy(ROOT / "tableau" / "loyers_long.csv", DOCS / "data" / "loyers_long.csv")

# Règles d'hébergement, au format lu par Netlify ET par Cloudflare Pages (fichiers _headers / _redirects
# placés dans le dossier publié). Elles forcent le téléchargement des fichiers de données et renvoient
# les pages retirées du projet vers l'accueil.
(DOCS / "_headers").write_text("""/assets/*.sqlite
  Content-Type: application/vnd.sqlite3
  Content-Disposition: attachment
/assets/*.sql
  Content-Type: application/sql
  Content-Disposition: attachment
/assets/*.csv
  Content-Type: text/csv; charset=utf-8
  Content-Disposition: attachment
/data/loyers_long.csv
  Content-Type: text/csv; charset=utf-8
  Content-Disposition: attachment
""", encoding="utf-8")
(DOCS / "_redirects").write_text("/python.html  /  301\n/notebooks/*  /  301\n", encoding="utf-8")
def ko(rel):
    """Taille d'un fichier de docs/ en Ko, pour l'afficher à côté du lien de téléchargement."""
    return f"{(DOCS / rel).stat().st_size / 1024:.0f} Ko"
SIZES = {"__SZ_SQLITE__": ko("assets/loyers.sqlite"), "__SZ_SQL__": ko("assets/loyers.sql"),
         "__SZ_REQ__": ko("assets/requetes_loyers_montreal.sql"), "__SZ_PG__": ko("assets/loyers_postgres.sql"),
         "__SZ_DICO__": ko("assets/dictionnaire_donnees.csv"), "__SZ_CSV__": ko("data/loyers_long.csv"),
         "__SZ_XL__": ko("assets/modele_loyers_montreal.xlsx"), "__SZ_XL_EN__": ko("assets/modele_loyers_montreal_en.xlsx")}
common = {
    **IX, **SIZES,
    "__XL_FORMULAS__": f"{n_formulas:,}".replace(",", " "),
    "__SQL_VOLUMES__": SQL_VOL_FR, "__SQL_VOLUMES_EN__": SQL_VOL_EN,
    "__N_PAYE__": str(N_PAYE),
    "__N_SQL__": str(len(SQL_FILES)), "__N_TABLES__": str(N_TABLES), "__N_VUES__": str(N_VUES),
    "__XL_SHEETS__": str(n_sheets - 1), "__XL_VISIBLE__": str(n_visible),
    "__PERIODE__": INS["periode_derniere"],
    "__CHOW_RUPT__": str(stats["chow_rupture"]), "__CHOW_F__": fr_num(stats["chow_f_2019"], 1),
    "__CHOW_P__": fr_num(stats["chow_p_simulee"], 3), "__CHOW_PN__": f"{stats['chow_p_naive']:.0e}".replace("e-", " × 10⁻").replace("10⁻10", "10⁻¹⁰").replace("10⁻0", "10⁻"),
    "__CHOW_RHO__": fr_num(stats["chow_rho"], 2), "__CHOW_SEUIL__": fr_num(stats["chow_seuil"], 1), "__CHOW_NSIM__": f"{stats['chow_n_sim']:,}".replace(",", " "),
    "__DICO_JSON__": json.dumps(DICO, ensure_ascii=False).replace("</", "<\\/"),
    "__PY_PENTE_AVANT__": fr_num(stats["pente_avant"], 1), "__PY_PENTE_APRES__": fr_num(stats["pente_apres"], 1),
    "__PY_RATIO__": fr_num(stats["ratio_pentes"], 1), "__PY_R2_AVANT__": fr_num(stats["r2_avant"]), "__PY_R2_APRES__": fr_num(stats["r2_apres"]),
    "__PY_BRUTE__": fr_num(stats["hausse_brute_2025"], 1), "__PY_MEME__": fr_num(stats["hausse_meme_echantillon_2025"], 1),
    "__PY_COMPO__": fr_num(stats["effet_composition_2025"], 1), "__PY_PART__": str(stats["part_composition"]),
    "__PY_NABOVE__": str(stats["n_demande_superieur"]), "__PY_NPAYE__": str(stats["n_rmr_paye"]),
    "__K_LOYER_2025__": f"{INS['loyer_2ch_2025']:,} $".replace(",", " "), "__K_DEMANDE__": f"{int(INS['mtl_demande_dernier']):,} $".replace(",", " "),
    "__K_RATTRAPAGE__": RATTRAPAGE,
    "__PY_R__": fr_num(stats["correlation"]), "__PY_R_WO__": fr_num(stats["correlation_sans_2025"]), "__PY_N__": str(stats["n"]),
    # jumeaux anglais (mêmes valeurs, format en-CA) pour les traductions des pages
    "__XL_FORMULAS_EN__": f"{n_formulas:,}",
    "__PERIODE_EN__": "Q" + INS["periode_derniere"][-1] + " " + INS["periode_derniere"][:4],
    "__CHOW_F_EN__": en_num(stats["chow_f_2019"], 1), "__CHOW_P_EN__": en_num(stats["chow_p_simulee"], 3),
    "__CHOW_RHO_EN__": en_num(stats["chow_rho"], 2), "__CHOW_NSIM_EN__": f"{stats['chow_n_sim']:,}",
    "__CHOW_SEUIL_EN__": en_num(stats["chow_seuil"], 1),
    "__PY_PENTE_AVANT_EN__": en_num(stats["pente_avant"], 1), "__PY_PENTE_APRES_EN__": en_num(stats["pente_apres"], 1),
    "__PY_RATIO_EN__": en_num(stats["ratio_pentes"], 1), "__PY_R2_AVANT_EN__": en_num(stats["r2_avant"]), "__PY_R2_APRES_EN__": en_num(stats["r2_apres"]),
    "__PY_BRUTE_EN__": en_num(stats["hausse_brute_2025"], 1), "__PY_MEME_EN__": en_num(stats["hausse_meme_echantillon_2025"], 1),
    "__PY_COMPO_EN__": en_num(stats["effet_composition_2025"], 1),
    "__PY_R_EN__": en_num(stats["correlation"]), "__PY_R_WO_EN__": en_num(stats["correlation_sans_2025"]),
    "__K_LOYER_2025_EN__": f"${INS['loyer_2ch_2025']:,}", "__K_DEMANDE_EN__": f"${int(INS['mtl_demande_dernier']):,}",
    "__K_RATTRAPAGE_EN__": f"{2025 + _n}, {_n} years from now",
}


from PIL import Image as _Img
_DIMS = {}


def img_dims(html_):
    """Ajoute width/height/decoding aux <img> : pas de saut de mise en page pendant le chargement."""
    import re as _re

    def one(m):
        tag, src = m.group(0), m.group(1)
        if "width=" in tag:
            return tag
        f = DOCS / src
        if src not in _DIMS:
            _DIMS[src] = _Img.open(f).size if f.exists() else None
        if not _DIMS[src]:
            return tag
        w, h = _DIMS[src]
        return tag[:-1].rstrip() + f' width="{w}" height="{h}" decoding="async">'
    return _re.sub(r'<img src="(assets/[^"]+\.(?:png|jpg|webp))"[^>]*>', one, html_)


def fill(text):
    for k, v in common.items():
        text = text.replace(k, v)
    for k, v in {**code, **xlf}.items():
        text = text.replace(k, html.escape(str(v), quote=False))
    text = text.replace("__COMMON_JS__", COMMON_JS)
    left = re.findall(r"__[A-Z][A-Z0-9_]+__", text)
    assert not left, f"Marqueurs non remplacés : {set(left)}"
    return text


written = {}
# accueil
body = index_tpl.replace("__HEADER__", header("index.html", INDEX_ACTIONS)).replace("__DATA_JSON__", data)
body = body.replace("__SCENE_JSON__", scene_json())
body = fill(body)
if SITE_URL:
    body = body.replace('content="assets/og-image-v2.png"', f'content="{SITE_URL}/assets/og-image-v2.png"')
    body = body.replace('<meta property="og:type" content="website">',
                        f'<meta property="og:type" content="website">\n<meta property="og:url" content="{SITE_URL}/">'
                        f'\n<link rel="canonical" href="{SITE_URL}/">')
body = body + f"\n<script>{MOTION_JS}</script>\n<script>{I18N_JS}</script>"
written["index.html"] = (SKELETON + body + "\n</html>\n", body)

# pages de compétences
for fname, _ in PAGES[1:]:
    tpl = (SRC / "pages" / fname).read_text(encoding="utf-8")
    head_part, rest = tpl.split("__HEADER__", 1)
    rest = rest.replace("__FOOTER__", FOOTER).replace("__SQL_JSON__", sqlres)
    rest = rest.replace("__CARTE_JSON__", carte_json).replace("__GEO_JSON__", geo_json)
    page = SKELETON + head_part + FONTS + CSS + "\n" + header(fname) + rest
    page = fill(page) + f"\n<script>{MOTION_JS}</script>\n<script>{I18N_JS}</script>\n</html>\n"
    written[fname] = (page, page)

for fname, (full, _) in written.items():
    (DOCS / fname).write_text(img_dims(full), encoding="utf-8")
if PREVIEW:
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for fname, (_, prev) in written.items():
        (PREVIEW / fname).write_text(img_dims(prev), encoding="utf-8")
print("pages écrites :", ", ".join(written), f"· {common['__XL_FORMULAS__']} formules Excel")
