"""
Modèles de la base de données et paquet téléchargeable.

- Modèle conceptuel (MCD, notation Merise) : entités, associations, cardinalités. Défini ici, puis
  CONFRONTÉ à la base réelle : chaque association porteuse de données doit correspondre à une table
  de faits qui contient ses attributs, et chaque entité traduite en table doit exister.
- Modèle logique (MLD) : dessiné directement à partir du schéma SQLite (tables, clés primaires,
  clés étrangères lues par PRAGMA) ; il ne peut donc pas diverger de la base.
- Fichiers téléchargeables dans docs/assets : base SQLite, requêtes réunies, dictionnaire ;
  modèles MCD/MLD (SVG et PNG) dans docs/assets/sql.

Exécution : python src/modeles.py (après build_db.py)
"""
from pathlib import Path
import html
import sqlite3
import shutil

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "loyers.sqlite"
OUT = ROOT / "docs" / "assets" / "sql"
OUT.mkdir(parents=True, exist_ok=True)
BLUE, BLUE_D, BLUE_L, PINK, PINK_L, CORAL, INK, INK2, LINE = ("#2f86d6", "#1f5fa8", "#e8f2fc", "#e0457b", "#fdeaf1",
                                                              "#f2876b", "#13233a", "#5b6b82", "#c9d6e5")
FONT = "Inter, 'Helvetica Neue', Arial, sans-serif"
MONO = "'IBM Plex Mono', Menlo, Consolas, monospace"
esc = lambda s: html.escape(str(s))

# ================================================================== MCD
# entité : (titre, identifiant, attributs, x, y, table SQL ou None si l'entité n'est pas traduite en table)
ENT = {
    "LOGEMENT": ("TYPE DE LOGEMENT", "unit_id", ["libellé", "chambres"], 40, 40, "dim_logement"),
    "VILLE": ("GRANDE VILLE", "geo_id", ["libellé"], 40, 300, "dim_geo"),
    "INDIC": ("INDICATEUR SCHL", "code", ["libellé", "unité"], 40, 560, "dim_indicateur"),
    "ANNEE": ("ANNÉE", "annee", [], 560, 330, None),
    "PROV": ("PROVINCE", "code", ["nom", "niveau"], 1010, 120, "dim_province"),
    "RMR": ("RÉGION MÉTROPOLITAINE", "geo_id", ["nom", "latitude", "longitude"], 1010, 470, "dim_rmr"),
    "TRIM": ("TRIMESTRE", "periode", [], 560, 640, None),
    "EST": ("ESTIMATION", "code", ["libellé"], 1010, 700, "dim_estimation"),
}
# association : (nom, attributs, x, y, [(entité, cardinalité)], table SQL portant l'association ou None)
ASSO = [
    ("Mesurer le loyer", ["loyer"], 330, 60, [("LOGEMENT", "0,n"), ("VILLE", "0,n"), ("ANNEE", "0,n")], "fait_loyer"),
    ("Mesurer l'inoccupation", ["taux"], 330, 230, [("VILLE", "0,n"), ("ANNEE", "0,n")], "fait_inoccupation"),
    ("Indicer les prix", ["ipc"], 330, 380, [("VILLE", "0,n"), ("ANNEE", "0,n")], "ipc"),
    ("Publier (SCHL)", ["valeur"], 330, 540, [("VILLE", "0,n"), ("INDIC", "0,n"), ("ANNEE", "0,n")], "schl_roulement"),
    ("Indicer le loyer", ["ipc_loyer", "ipc_ensemble"], 790, 200, [("PROV", "0,n"), ("ANNEE", "0,n")], "ipc_provinces"),
    ("Appartenir", [], 1040, 330, [("RMR", "1,1"), ("PROV", "0,n")], None),
    ("Observer le loyer", ["loyer", "cote"], 790, 600, [("RMR", "0,n"), ("TRIM", "0,n"), ("EST", "0,n")], "fait_loyer_trimestriel"),
]
EW, AW, AH = 220, 170, 0


def ent_box(key):
    t, ident, attrs, x, y, _ = ENT[key]
    return x, y, EW, 38 + 22 * (1 + len(attrs)) + 6


def asso_box(a):
    _, attrs, x, y, _, _ = a
    return x, y, AW, 34 + 20 * max(len(attrs), 0) + 10


def clip(box, tx, ty):
    """Point du bord de la boîte sur le segment centre -> (tx, ty)."""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    dx, dy = tx - cx, ty - cy
    if dx == dy == 0:
        return cx, cy
    s = min((w / 2) / abs(dx) if dx else 1e9, (h / 2) / abs(dy) if dy else 1e9)
    return cx + dx * s, cy + dy * s


def mcd_svg():
    W, H = 1270, 830
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="40" y="{H - 22}" font-size="12" fill="{INK2}">Modèle conceptuel de données (Merise) · identifiants soulignés · '
           f'ANNÉE et TRIMESTRE sont des entités temporelles non traduites en tables</text>']
    links, labels = [], []
    for a in ASSO:
        ab = asso_box(a)
        acx, acy = ab[0] + ab[2] / 2, ab[1] + ab[3] / 2
        for ek, card in a[4]:
            eb = ent_box(ek)
            ecx, ecy = eb[0] + eb[2] / 2, eb[1] + eb[3] / 2
            x1, y1 = clip(ab, ecx, ecy)
            x2, y2 = clip(eb, acx, acy)
            links.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{INK2}" stroke-width="1.3"/>')
            lx, ly = x2 + (x1 - x2) * 0.22, y2 + (y1 - y2) * 0.22
            labels.append(f'<g><rect x="{lx - 17:.1f}" y="{ly - 10:.1f}" width="34" height="18" rx="9" fill="#ffffff" stroke="{LINE}"/>'
                          f'<text x="{lx:.1f}" y="{ly + 3.5:.1f}" font-size="11" font-weight="600" text-anchor="middle" fill="{BLUE_D}" '
                          f'font-family="{MONO}">{card}</text></g>')
    out += links
    for k in ENT:
        t, ident, attrs, *_ = ENT[k]
        x, y, w, h = ent_box(k)
        out.append(f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="{BLUE}" stroke-width="1.6"/>'
                   f'<path d="M{x} {y + 10} a10 10 0 0 1 10 -10 h{w - 20} a10 10 0 0 1 10 10 v22 h-{w} z" fill="{BLUE}"/>'
                   f'<text x="{x + 12}" y="{y + 21}" font-size="12.5" font-weight="700" fill="#ffffff" letter-spacing=".04em">{esc(t)}</text>'
                   f'<text x="{x + 12}" y="{y + 54}" font-size="12.5" fill="{INK}" text-decoration="underline" font-family="{MONO}">{esc(ident)}</text>')
        for i, at in enumerate(attrs):
            out.append(f'<text x="{x + 12}" y="{y + 76 + 22 * i}" font-size="12.5" fill="{INK2}" font-family="{MONO}">{esc(at)}</text>')
        out.append('</g>')
    for a in ASSO:
        name, attrs, *_ = a
        x, y, w, h = asso_box(a)
        out.append(f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2 if not attrs else 22}" fill="{PINK_L}" stroke="{PINK}" stroke-width="1.6"/>'
                   f'<text x="{x + w / 2}" y="{y + 22}" font-size="12.5" font-weight="700" text-anchor="middle" fill="#a21f50">{esc(name)}</text>')
        for i, at in enumerate(attrs):
            out.append(f'<text x="{x + w / 2}" y="{y + 44 + 20 * i}" font-size="12" text-anchor="middle" fill="{INK}" font-family="{MONO}">{esc(at)}</text>')
        out.append('</g>')
    out += labels
    out.append('</svg>')
    return "\n".join(out)


# ================================================================== MLD, lu dans la base
LAYOUT = {  # table : (x, y)
    "dim_logement": (30, 30), "dim_geo": (30, 250), "dim_indicateur": (30, 470),
    "fait_loyer": (380, 30), "fait_inoccupation": (380, 210), "ipc": (380, 360), "schl_roulement": (380, 510),
    "fait_loyer_trimestriel": (740, 30), "ipc_provinces": (740, 400),
    "dim_rmr": (1100, 30), "dim_estimation": (1100, 250), "dim_province": (1100, 420),
}
TW, RH, HH = 250, 22, 32


def schema():
    con = sqlite3.connect(DB)
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    info = {}
    for t in tables:
        cols = [(c[1], c[2], c[5]) for c in con.execute(f"PRAGMA table_info({t})")]
        notnull = {c[1] for c in con.execute(f"PRAGMA table_info({t})") if c[3] or c[5]}
        fks = {f[3]: (f[2], f[4], f[3] in notnull) for f in con.execute(f"PRAGMA foreign_key_list({t})")}
        info[t] = (cols, fks)
    con.close()
    return info


def card_pill(cx, cy, txt):
    return (f'<g><rect x="{cx - 19:.1f}" y="{cy - 10.5:.1f}" width="38" height="20" rx="10" fill="#ffffff" stroke="{BLUE_D}" stroke-width=".8"/>'
            f'<text x="{cx:.1f}" y="{cy + 4.2:.1f}" font-size="12.5" font-weight="700" text-anchor="middle" fill="{BLUE_D}" '
            f'font-family="{MONO}">{txt}</text></g>')


def mld_svg(info):
    assert set(info) == set(LAYOUT), f"Tables sans position dans le MLD : {set(info) ^ set(LAYOUT)}"
    W, H = 1460, 700
    rowy = {}
    boxes, arrows, cards, seen = [], [], [], set()
    for t, (cols, fks) in info.items():
        x, y = LAYOUT[t]
        h = HH + RH * len(cols) + 8
        fact = not t.startswith("dim_")
        col = BLUE if not fact else PINK
        boxes.append(f'<g><rect x="{x}" y="{y}" width="{TW}" height="{h}" rx="10" fill="#ffffff" stroke="{col}" stroke-width="1.6"/>'
                     f'<path d="M{x} {y + 10} a10 10 0 0 1 10 -10 h{TW - 20} a10 10 0 0 1 10 10 v{HH - 10} h-{TW} z" fill="{col}"/>'
                     f'<text x="{x + 12}" y="{y + 21}" font-size="13" font-weight="700" fill="#ffffff" font-family="{MONO}">{esc(t)}</text>'
                     f'<text x="{x + TW - 10}" y="{y + 21}" font-size="10" fill="#ffffff" text-anchor="end" opacity=".9">'
                     f'{"fait" if fact else "dimension"}</text>')
        for i, (name, typ, pk) in enumerate(cols):
            cy = y + HH + RH * i + 16
            rowy[(t, name)] = cy - 4
            key = ("PK" if pk else "") + (" FK" if name in fks else "")
            boxes.append(f'<text x="{x + 12}" y="{cy}" font-size="12" fill="{INK}" font-family="{MONO}"'
                         f'{" font-weight=\"700\" text-decoration=\"underline\"" if pk else ""}>{"#" if name in fks else ""}{esc(name)}</text>'
                         f'<text x="{x + TW - 52}" y="{cy}" font-size="10.5" fill="{INK2}" text-anchor="end" font-family="{MONO}">{esc(typ)}</text>'
                         f'<text x="{x + TW - 10}" y="{cy}" font-size="10" fill="{PINK if "FK" in key else BLUE_D}" text-anchor="end" font-weight="700">{key.strip()}</text>')
        boxes.append('</g>')
    for t, (cols, fks) in info.items():
        for c, (rt, rc, nn) in fks.items():
            x1, x2 = LAYOUT[t][0], LAYOUT[rt][0]
            y1, y2 = rowy[(t, c)], rowy[(rt, rc)]
            if x2 + TW < x1:            # cible à gauche
                sx, ex, k, ke = x1, x2 + TW, -1, -1
            elif x1 + TW < x2:          # cible à droite
                sx, ex, k, ke = x1 + TW, x2, 1, 1
            else:                       # même colonne : boucle par la droite
                sx, ex, k, ke = x1 + TW, x2 + TW, 1, -1
                arrows.append(f'<path d="M{sx} {y1} C{sx + 70} {y1}, {ex + 70} {y2}, {ex + 6} {y2}" fill="none" stroke="{INK2}" stroke-width="1.3" marker-end="url(#a)"/>')
            if x1 != x2:
                mid = (sx + ex) / 2
                arrows.append(f'<path d="M{sx} {y1} C{mid} {y1}, {mid} {y2}, {ex - 6 * k} {y2}" fill="none" stroke="{INK2}" stroke-width="1.3" marker-end="url(#a)"/>')
            # cardinalités (notation Merise, comme le MCD) : côté clé étrangère, chaque ligne référence
            # exactement une ligne (1,1 si la colonne est NOT NULL, sinon 0,1) ; côté clé référencée, une
            # ligne peut être référencée par zéro ou plusieurs lignes (0,n). Un seul 0,n par point d'arrivée.
            cards.append(card_pill(sx + 24 * k, y1 - 12, "1,1" if nn else "0,1"))
            if (rt, rc, ke) not in seen:
                seen.add((rt, rc, ke))
                cards.append(card_pill(ex - 27 * ke, y2 - 12, "0,n"))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
           f'<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           f'<path d="M0 0 L10 5 L0 10 z" fill="{INK2}"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>', *arrows, *boxes, *cards,
           f'<text x="30" y="{H - 18}" font-size="12" fill="{INK2}">Modèle logique (relationnel) généré depuis la base · '
           f'souligné : clé primaire · # : clé étrangère, flèche vers la clé référencée · 1,1 / 0,n : cardinalités · rose : faits, bleu : dimensions</text>', '</svg>']
    return "\n".join(out)


def check_mcd(info):
    """Le MCD doit se traduire dans la base réelle : entités -> tables, associations porteuses -> tables de faits."""
    cols = {t: {c[0] for c in info[t][0]} for t in info}
    for k, (_, ident, attrs, *_ , table) in ENT.items():
        if table:
            assert table in info and ident in cols[table], (k, table, ident)
    for name, attrs, *_, links, table in ASSO:
        if table:
            assert table in info, (name, table)
            assert set(attrs) <= cols[table], (name, attrs, cols[table])
            fk_targets = {info[table][1][c][0] for c in info[table][1]}
            expected = {ENT[e][5] for e, _ in links if ENT[e][5]}
            assert expected <= fk_targets, (name, expected, fk_targets)
        else:  # association 1,1 – 0,n : traduite par une clé étrangère côté 1,1
            one = next(e for e, c in links if c == "1,1")
            many = next(e for e, c in links if c != "1,1")
            assert ENT[many][5] in {v[0] for v in info[ENT[one][5]][1].values()}, name


def png(svg_path, png_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=2)
        svg = svg_path.read_text(encoding="utf-8")
        w = int(svg.split('width="')[1].split('"')[0]); h = int(svg.split('height="')[1].split('"')[0])
        pg.set_viewport_size({"width": w, "height": h})
        pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
        pg.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": w, "height": h})
        b.close()


if __name__ == "__main__":
    info = schema()
    check_mcd(info)
    (OUT / "mcd.svg").write_text(mcd_svg(), encoding="utf-8")
    (OUT / "mld.svg").write_text(mld_svg(info), encoding="utf-8")
    for n in ("mcd", "mld"):
        png(OUT / f"{n}.svg", OUT / f"{n}.png")
    # Fichiers téléchargeables individuellement (pas d'archive : chaque fichier est utile seul)
    assets = ROOT / "docs" / "assets"
    shutil.copy(ROOT / "data" / "loyers.sqlite", assets / "loyers.sqlite")   # lue par la console SQL de la page (sql.js), plus proposée au téléchargement
    (assets / "dictionnaire_donnees.csv").unlink(missing_ok=True)
    parts = ["-- Les requêtes analytiques du projet « Loyers à Montréal », du niveau débutant au niveau avancé.",
             "-- ÉTAPE 2 SUR 2 : à exécuter APRÈS loyers.sql, sur la même base (SQLite 3.25+). Le niveau est indiqué en tête de chacune.",
             "-- Sources : Statistique Canada et SCHL, Licence du gouvernement ouvert – Canada.", ""]
    for f in sorted((ROOT / "sql").glob("*.sql")):
        parts += [f"-- ===================================================================== {f.name}", f.read_text(encoding="utf-8").strip(), "", ""]
    (assets / "requetes_loyers_montreal.sql").write_text("\n".join(parts), encoding="utf-8")
    old_zip = assets / "base_loyers_montreal.zip"
    if old_zip.exists():
        old_zip.unlink()
    print("modèles et fichiers écrits :", ", ".join(p.name for p in sorted(OUT.iterdir())), "· loyers.sqlite (console), loyers.sql, requetes_loyers_montreal.sql")
