"""
Version anglaise de la base, dérivée de la version française (qui reste la source).

Les noms de tables, de colonnes, de vues, d'alias et les libellés sont traduits par des tables de correspondance ;
les requêtes anglaises sont exécutées sur la base anglaise et leurs résultats comparés, cellule par cellule, à ceux
des requêtes françaises. Les versions SQL Server et PostgreSQL sont produites par les mêmes générateurs
(src/sqlserver.py, src/postgres.py), lancés sur les sources anglaises.

Sorties : sql/en/ (schéma et requêtes), docs/assets/rents_*_en.sql (6 fichiers), docs/assets/rents_en.sqlite
(console de la page), docs/data/sql_results_en.json.
Exécution : python src/english.py   (après build_db.py, sqlserver.py, postgres.py, modeles.py)
"""
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIR = ROOT / "build" / "en"                 # arborescence miroir où tournent les générateurs
ASSETS = ROOT / "docs" / "assets"

# ------------------------------------------------------------------ identifiants
IDENT = {
    # tables, vues, index
    "dim_logement": "dim_unit_type", "dim_geo": "dim_city", "dim_estimation": "dim_estimate", "dim_indicateur": "dim_indicator",
    "dim_rmr": "dim_metro_area", "fait_loyer": "fact_rent", "fait_inoccupation": "fact_vacancy",
    "fait_loyer_trimestriel": "fact_rent_quarterly", "ipc": "cpi", "ipc_provinces": "cpi_provinces", "schl_roulement": "cmhc_turnover",
    "v_loyer_reel": "v_real_rent", "v_variation_annuelle": "v_annual_change", "v_dernier_trimestre": "v_latest_quarter",
    "v_ecart_demande_paye": "v_asking_paid_gap", "v_ipc_provinces_variation": "v_cpi_provinces_change",
    "ix_ipcp_code": "ix_cpip_code", "ix_loyer_geo_unit": "ix_rent_geo_unit", "ix_rmr_province": "ix_metro_province",
    "ix_trim_geo_est": "ix_quarter_geo_est",
    # colonnes
    "annee": "year", "chambres": "bedrooms", "cote": "grade", "estimation": "estimate", "indicateur": "indicator",
    "ipc_ensemble": "all_items_cpi", "ipc_loyer": "rent_cpi", "libelle": "label", "libelle_en": "label_en", "libelle_fr": "label_fr",
    "loyer": "rent", "niveau": "level", "nom": "name", "periode": "period", "taux": "rate", "unite": "unit", "valeur": "value",
    # colonnes calculées, alias, CTE
    "annee_ref": "ref_year", "cote_E": "grade_e", "debut": "start_year", "fin": "end_year", "demande": "asking", "dernier": "latest",
    "ecart": "gap", "ecart_annuel": "annual_gap", "ecart_mensuel": "monthly_gap", "ecart_pct": "gap_pct",
    "ens_2019": "all_items_2019", "ens_2025": "all_items_2025", "hausse_2019_2025_pct": "increase_2019_2025_pct",
    "hausse_2025_pct": "increase_2025_pct", "hausse_ipc_loyer_qc_2025": "qc_rent_cpi_increase_2025",
    "hausse_loyer_pct": "rent_increase_pct", "hausse_pct": "increase_pct", "hausse_reelle_pct": "real_increase_pct",
    "inoccupation_pct": "vacancy_pct", "ipc_2025": "cpi_2025", "ipc_ref": "ref_cpi", "lignes": "row_count", "logement": "unit_type",
    "loyer_2019": "rent_2019", "loyer_2024": "rent_2024", "loyer_2025": "rent_2025", "loyer_moyen_reloues": "avg_rent_relet",
    "loyer_moyen_tous": "avg_rent_all", "loyer_nominal": "nominal_rent", "loyer_prec": "prev_rent", "loyer_reel": "real_rent",
    "loyer_reel_2025": "real_rent_2025", "manquantes": "missing", "mm3": "ma3", "moyenne_mobile_3_ans": "moving_avg_3yr",
    "par_region": "by_area", "paye": "paid", "pct_du_plus_cher": "pct_of_most_expensive", "periodes": "periods",
    "rang": "ranking", "rang_2025": "ranking_2025", "rang_moins_cher": "cheapest_rank", "reel": "real_series",
    "rythme_annuel_pct": "annual_pace_pct", "taux_prec": "prev_rate", "variation_pct": "change_pct", "ville": "city",
}
# noms identiques dans les deux langues
SAME = set("""a b d e f g h i l m p r s t v w base code dim_province geo_id unit_id province lat lon inflation_pct ref rn series
source LEN""".split())
KEYWORDS = set("""select from where and or not null as on join left cross inner group by order having limit desc asc with case when
then else end over partition rows between preceding current row union all distinct count sum min max avg round cast integer real text
create table view primary key references check unique in is like glob insert into values pragma foreign_keys window lag rank
row_number power length index nulls last""".split())

# ------------------------------------------------------------------ valeurs
UNIT = {"1ch": "1br", "2ch": "2br", "3ch": "3br"}
INDIC = {
    "loyer_moyen_reloues_2ch": ("avg_rent_relet_2br", "Average rent of a two-bedroom re-let to a new tenant"),
    "hausse_loyer_reloues_2ch": ("rent_increase_relet_2br", "Rent increase of re-let two-bedrooms"),
    "hausse_loyer_non_reloues_2ch": ("rent_increase_not_relet_2br", "Rent increase of two-bedrooms not re-let (sitting tenants)"),
    "hausse_loyer_meme_echantillon_2ch": ("rent_increase_same_sample_2br", "Rent increase of two-bedrooms, fixed sample"),
    "taux_inoccupation_3plus": ("vacancy_rate_3plus", "Vacancy rate, buildings with 3 units or more"),
}
LEVEL = {"territoire": "territory", "pays": "country"}
ESTIMATE = {"Loyer demandé": "Asking rent", "Loyer payé": "Rent paid"}
PROVINCE = {"Québec": "Quebec", "Colombie-Britannique": "British Columbia", "Île-du-Prince-Édouard": "Prince Edward Island",
            "Nouveau-Brunswick": "New Brunswick", "Nouvelle-Écosse": "Nova Scotia", "Terre-Neuve-et-Labrador": "Newfoundland and Labrador",
            "Territoires du Nord-Ouest": "Northwest Territories"}
METRO = {"Montréal": "Montreal", "Québec": "Quebec City", "Grand Sudbury": "Greater Sudbury",
         "Gatineau (Ottawa-Gatineau, partie québécoise)": "Gatineau (Ottawa-Gatineau, Quebec part)",
         "Ottawa (Ottawa-Gatineau, partie ontarienne)": "Ottawa (Ottawa-Gatineau, Ontario part)", "Ensemble des RMR": "All metro areas"}
# littéraux des scripts (schéma et requêtes) : codes sans ambiguïté
LIT = {**UNIT, **{k: v[0] for k, v in INDIC.items()}, **LEVEL}
LIT_SAME = {"Montreal", "A", "P", "E", "F", "..", "QC", "province", "dollars", "pct", "-", " / ", " -> ", "studio",
            "[0-9][0-9][0-9][0-9]-[0-1][0-9]"}
# traduction des valeurs par (table française, colonne française) pour la copie des données
VALUES = {
    ("dim_logement", "unit_id"): UNIT, ("fait_loyer", "unit_id"): UNIT,
    ("dim_province", "nom"): PROVINCE, ("dim_province", "niveau"): LEVEL, ("dim_estimation", "libelle"): ESTIMATE,
    ("dim_indicateur", "code"): {k: v[0] for k, v in INDIC.items()}, ("dim_indicateur", "libelle"): None,   # voir copie()
    ("schl_roulement", "indicateur"): {k: v[0] for k, v in INDIC.items()}, ("dim_rmr", "nom"): METRO,
}

# ------------------------------------------------------------------ commentaires
COM = {
    "Base de données « Loyers à Montréal » : modèle en étoile": '"Montreal Rents" database: star schema',
    "Moteur : SQLite (compatible PostgreSQL / DuckDB avec ajustements mineurs)": "Engine: SQLite (PostgreSQL / DuckDB compatible with minor changes)",
    "Moteur : PostgreSQL 12+ (version dérivée du script SQLite par src/postgres.py)": "Engine: PostgreSQL 12+ (derived from the SQLite script)",
    "Moteur : SQL Server 2016+ (version dérivée du script SQLite par src/sqlserver.py)": "Engine: SQL Server 2016+ (derived from the SQLite script)",
    "Grain de chaque table de faits indiqué en commentaire.": "The grain of each fact table is given in a comment.",
    "studio, 1ch, 2ch, 3ch": "studio, 1br, 2br, 3br",
    "six grandes RMR (séries annuelles SCHL)": "six large metro areas (CMHC annual series)",
    "10 provinces, 3 territoires et le Canada (agrégat)": "10 provinces, 3 territories and Canada (aggregate)",
    "type d'estimation du tableau 46-10-0092": "type of estimate in table 46-10-0092",
    "A = loyer demandé, P = loyer payé": "A = asking rent, P = rent paid",
    "indicateurs du rapport SCHL ; l'unité dépend de l'indicateur seul (3FN)": "indicators from the CMHC report; the unit depends on the indicator alone (3NF)",
    "42 RMR du tableau 46-10-0092 (+ ensemble)": "42 metro areas of table 46-10-0092 (+ all areas)",
    "Grain : une année × une RMR × un type de logement (loyer moyen d'octobre, $ courants)": "Grain: one year × one metro area × one unit type (October average rent, current dollars)",
    "Grain : une année × une RMR (taux d'inoccupation, immeubles de 6 logements et plus, %)": "Grain: one year × one metro area (vacancy rate, buildings with 6 units or more, %)",
    "Grain : un trimestre × une RMR × une estimation (A = loyer demandé, P = loyer payé), 2 chambres": "Grain: one quarter × one metro area × one estimate (A = asking rent, P = rent paid), two-bedroom",
    "NULL = non publié par Statistique Canada": "NULL = not published by Statistics Canada",
    "Grain : une année × une grande ville (IPC d'ensemble, moyenne annuelle, 2002 = 100 ; Montréal)": "Grain: one year × one large city (all-items CPI, annual average, 2002 = 100; Montreal)",
    "Grain : une année × une province (IPC du loyer et IPC d'ensemble, 2002 = 100)": "Grain: one year × one province (rent CPI and all-items CPI, 2002 = 100)",
    "Grain : une année × une grande ville × un indicateur publié dans le rapport SCHL 2025": "Grain: one year × one large city × one indicator published in the 2025 CMHC report",
    "Vues analytiques : la logique métier vit dans la base, pas dans chaque requête": "Analytical views: the business logic lives in the database, not in each query",
    "Loyers de Montréal en dollars constants de la dernière année disponible": "Montreal rents in constant dollars of the latest available year",
    "Variation annuelle de chaque série (ville × type de logement)": "Year-over-year change of each series (city × unit type)",
    "Dernier trimestre publié de chaque série (région × estimation)": "Latest published quarter of each series (metro area × estimate)",
    "Écart entre loyer demandé et loyer payé, par région": "Gap between asking rent and rent paid, by metro area",
    "Hausse des loyers (IPC du loyer) par province et par année": "Rent increase (rent CPI) by province and year",
    "Les vues sont dans des lots séparés (GO), comme SQL Server l'exige.": "Views are in separate batches (GO), as SQL Server requires.",
    "Each query starts with its title in French and in English (EN:) and its level.": "Each query starts with its title and its level.",
}
SECTIONS = {"faits": "facts", "données": "data"}
FRENCH = re.compile(r"[éèêàâçùûîôÉÈÀ«»]|\b(les|des|une|du|pour|sur|dans|chaque|est|sont|loyer|depuis)\b")


def comment(text):
    """Commentaire français -> anglais ; None : ligne à retirer (bloc d'en-tête français, lexique)."""
    t = text.strip()
    if t in COM:
        return COM[t]
    if not t or set(t) <= set("=- "):
        return t
    m = re.match(r"^(-{10,}) (\w+)$", t)
    if m:
        return f"{m.group(1)} {SECTIONS.get(m.group(2), m.group(2))}"
    m = re.match(r"^(\w+) : (\d+) lignes$", t)
    if m:
        return f"{m.group(1)}: {m.group(2)} rows"
    if re.match(r"^(Names are in French|periode = quarter|inoccupation = vacancy)", t):
        return None
    if FRENCH.search(t):
        return None                       # en-têtes français des générateurs : le bloc anglais qui suit les remplace
    return t


def scan(sql):
    """Découpe un script en segments ('code' | 'lit' | 'com', texte)."""
    out, i, n, buf = [], 0, len(sql), []
    flush = lambda: (out.append(("code", "".join(buf))), buf.clear()) if buf else None
    while i < n:
        c = sql[i]
        if c == "-" and sql[i:i + 2] == "--":
            flush(); j = sql.find("\n", i); j = n if j < 0 else j
            out.append(("com", sql[i + 2:j])); i = j
        elif c == "'":
            flush(); j = i + 1
            while j < n:
                if sql[j] == "'":
                    if sql[j:j + 2] == "''":
                        j += 2; continue
                    break
                j += 1
            out.append(("lit", sql[i + 1:j])); i = j + 1
        else:
            buf.append(c); i += 1
    flush()
    return out


WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def code(text):
    def sub(m):
        w = m.group(0)
        if w in IDENT:
            return IDENT[w]
        assert w in SAME or w.lower() in KEYWORDS or w.upper() == w, f"identifiant sans traduction : {w}"
        return w
    return re.sub(r"\b([a-z])\.label_fr\b", r"\1.label_en", WORD.sub(sub, text))    # les requêtes anglaises lisent le libellé anglais


def literal(text):
    raw = text.replace("''", "'")
    if raw in LIT:
        return LIT[raw]
    if raw in IDENT:                      # noms de tables cités comme valeurs (contrôle qualité)
        return IDENT[raw]
    assert raw in LIT_SAME, f"littéral sans traduction : {raw!r}"
    return text


def translate(sql, comments=True):
    """Script français -> anglais (identifiants, littéraux, commentaires)."""
    lines_out, cur = [], []
    for kind, text in scan(sql):
        if kind == "code":
            cur.append(code(text))
        elif kind == "lit":
            cur.append("'" + literal(text) + "'")
        else:
            c = comment(text) if comments else text
            if c is None:
                cur.append("\x00")        # marque : retirer la ligne si elle ne contient que ce commentaire
            else:
                cur.append("--" + (text if c == text.strip() else " " + c))
    for line in "".join(cur).split("\n"):
        if "\x00" in line:
            if line.replace("\x00", "").strip():
                lines_out.append(line.replace("\x00", "").rstrip())
            continue
        lines_out.append(line)
    return align("\n".join(lines_out))


def align(sql):
    """Réaligne les colonnes après traduction : types dans les CREATE TABLE, alias « AS » en fin de ligne."""
    lines = sql.split("\n")
    def groups(pat, gaps=False):
        run = []
        for i, l in enumerate(lines + [""]):
            m = pat.match(l)
            if m:
                run.append((i, m))
            elif not gaps or not l.strip() or re.match(r"\s*(FROM|WHERE|GROUP|ORDER|JOIN|UNION|\)|CREATE|WINDOW)\b", l):
                if len(run) > 1:
                    yield run
                run = []
    for run in groups(re.compile(r"^(  \w+)( +)((?:TEXT|INTEGER|REAL)\b.*)$")):
        w = max(len(m.group(1)) for _, m in run) + 2
        for i, m in run:
            lines[i] = m.group(1).ljust(w) + m.group(3)
    for run in groups(re.compile(r"^(.*\S)( +)(AS \w+,?)$"), gaps=True):
        if any(len(m.group(2)) > 1 for _, m in run):
            w = max(len(m.group(1)) for _, m in run) + 1
            for i, m in run:
                lines[i] = m.group(1).ljust(w) + m.group(3)
    return "\n".join(lines)


def query_en(src):
    """Requête : titre anglais et niveau en tête, puis le SQL traduit."""
    lines = src.strip().splitlines()
    m = re.match(r"^-- EN: (.+) · Level: (\w+)$", lines[2])
    assert lines[1].startswith("-- Niveau") and m, lines[:3]
    return f"-- {m.group(1)}\n-- Level: {m.group(2)}\n" + translate("\n".join(lines[3:]), comments=False) + "\n"


def tidy(text, engine):
    """Commentaires d'un fichier produit par un générateur : anglais seulement, noms de fichiers et de base anglais."""
    out, held, in_fr = [], None, False
    for line in text.split("\n"):
        m = re.match(r"^(\s*)--(.*)$", line)
        if not m:
            in_fr = False
        if m:
            raw = re.sub(r"\bloyers\b(?!\.)", "rents", m.group(2)) if not FRENCH.search(m.group(2).replace("loyers", "")) else m.group(2)
            c = comment(raw)
            if c is None:
                in_fr = True                 # bloc d'en-tête français : retiré jusqu'à la ligne de séparation
                continue
            if not c or set(c) <= set("=- "):
                in_fr = False
            elif in_fr and raw.strip() not in COM:
                continue
            c = re.sub(r"(rents_(?:database|queries)_(?:sqlserver|postgres|sqlite))\.sql", r"\1_en.sql", c)
            if c.startswith("Engine: SQLite"):
                c = {"sqlserver": "Engine: SQL Server 2016+ (derived from the SQLite script)",
                     "postgres": "Engine: PostgreSQL 12+ (derived from the SQLite script)"}[engine]
            line = m.group(1) + "--" + raw[:len(raw) - len(raw.lstrip())] + c
            if c.startswith("Views are in separate batches"):
                held = line; continue
            if held and c.startswith("Run it once only"):
                out += [line, held]; held = None; continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"(--\n){2,}", "--\n", text)
    return re.sub(r"(-- =+\n)--\n", r"\1", text)


def french_left(text, name):
    """Aucun identifiant ni commentaire français ne doit rester dans un fichier anglais."""
    bad = set()
    for kind, t in scan(text):
        if kind == "code":
            bad |= {w for w in WORD.findall(t) if w in IDENT and IDENT[w] != w and w not in IDENT.values()}
        elif kind == "com" and FRENCH.search(t):
            bad.add("commentaire : " + t.strip()[:60])
    assert not bad, f"{name} : restes français {sorted(bad)[:8]}"


def copie(fr, en):
    """Copie les données de la base française vers la base anglaise, valeurs traduites."""
    for (t,) in fr.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY rowid"):
        cols = [c[1] for c in fr.execute(f"PRAGMA table_info({t})")]
        rows = []
        for row in fr.execute(f"SELECT * FROM {t}"):
            new = []
            for c, v in zip(cols, row):
                if (t, c) == ("dim_indicateur", "libelle"):
                    v = INDIC[row[0]][1]
                elif VALUES.get((t, c)):
                    v = VALUES[(t, c)].get(v, v)
                new.append(v)
            rows.append(new)
        en.executemany(f"INSERT INTO {IDENT.get(t, t)} ({', '.join(IDENT.get(c, c) for c in cols)}) "
                       f"VALUES ({', '.join('?' * len(cols))})", rows)
    en.commit()


if __name__ == "__main__":
    # 1. sources anglaises (schéma, vues, requêtes) dans l'arborescence miroir et dans sql/en/
    shutil.rmtree(MIR, ignore_errors=True)
    for d in ("sql/schema", "data", "docs/assets", "src"):
        (MIR / d).mkdir(parents=True)
    EN_SQL = ROOT / "sql" / "en"
    shutil.rmtree(EN_SQL, ignore_errors=True)
    (EN_SQL / "schema").mkdir(parents=True)
    for f in sorted((ROOT / "sql" / "schema").glob("*.sql")):
        t = translate(f.read_text(encoding="utf-8"))
        (MIR / "sql" / "schema" / f.name).write_text(t, encoding="utf-8"); (EN_SQL / "schema" / f.name).write_text(t, encoding="utf-8")
    queries = {}
    for f in sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql")):
        queries[f.name] = query_en(f.read_text(encoding="utf-8"))
        (MIR / "sql" / f.name).write_text(queries[f.name], encoding="utf-8"); (EN_SQL / f.name).write_text(queries[f.name], encoding="utf-8")

    # 2. base anglaise : schéma traduit, données copiées de la base française
    fr = sqlite3.connect(ROOT / "data" / "loyers.sqlite")
    en_path = MIR / "data" / "loyers.sqlite"
    en = sqlite3.connect(en_path)
    en.execute("PRAGMA foreign_keys = ON")
    en.executescript((MIR / "sql" / "schema" / "01_tables.sql").read_text(encoding="utf-8"))
    copie(fr, en)
    en.executescript((MIR / "sql" / "schema" / "02_views.sql").read_text(encoding="utf-8"))
    assert not en.execute("PRAGMA foreign_key_check").fetchall()
    for (t,) in fr.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall():
        a, b = fr.execute(f"SELECT COUNT(*) FROM {t}").fetchone(), en.execute(f"SELECT COUNT(*) FROM {IDENT.get(t, t)}").fetchone()
        assert a == b, (t, a, b)

    # 3. mêmes résultats que les requêtes françaises, cellule par cellule
    labels = {}
    for tab in ("dim_logement", "dim_geo"):
        labels.update(dict(fr.execute(f"SELECT libelle_fr, libelle_en FROM {tab}")))
    value_map = {**labels, **METRO, **UNIT, **{k: v[0] for k, v in INDIC.items()},
                 **{k: v for k, v in IDENT.items() if k.startswith(("fait_", "ipc", "schl_"))}}
    res_fr = json.loads((ROOT / "docs" / "data" / "sql_results.json").read_text(encoding="utf-8"))
    res_en = []
    for q in res_fr:
        cur = en.execute(queries[q["file"]])
        cols, rows = [d[0] for d in cur.description], [list(r) for r in cur.fetchall()]
        assert cols == [IDENT.get(c, c) for c in q["columns"]], (q["file"], cols, q["columns"])
        # « Québec » est une province (colonne province) ou une ville : la colonne décide
        tr_ = lambda c, v: v if not isinstance(v, str) else (PROVINCE.get(v, v) if c == "province" else value_map.get(v, v))
        want = [[tr_(c, v) for c, v in zip(q["columns"], r)] for r in q["rows"]]
        assert rows == want, (q["file"], rows[:3], want[:3])
        res_en.append({"file": q["file"], "title": queries[q["file"]].splitlines()[0][3:], "sql": queries[q["file"]].strip(),
                       "columns": cols, "rows": rows})
    (ROOT / "docs" / "data" / "sql_results_en.json").write_text(json.dumps(res_en, ensure_ascii=False), encoding="utf-8")
    en.close(); fr.close()

    # 4. SQL Server et PostgreSQL : les générateurs du projet, lancés sur les sources anglaises
    for g in ("sqlserver.py", "postgres.py"):
        shutil.copy(ROOT / "src" / g, MIR / "src" / g)
        r = subprocess.run([sys.executable, str(MIR / "src" / g)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
        print("  [en]", r.stdout.strip().splitlines()[-1])

    # 5. fichiers anglais : commentaires anglais, noms de fichiers anglais, contrôle des restes français
    c_ = sqlite3.connect(en_path)
    dump = ("-- \"Montreal Rents\" database: full export (schema, data, views), SQLite 3.25+\n"
            "-- STEP 1 OF 2: run this file first, in an empty database, once only.\n"
            "-- STEP 2: run rents_queries_sqlite_en.sql on the same database.\n"
            "-- Sources: Statistics Canada and CMHC, Open Government Licence – Canada.\n"
            + "\n".join(c_.iterdump()) + "\n")
    c_.close()
    reqs = ("-- The analytical queries of the \"Montreal Rents\" project, from beginner to advanced level.\n"
            "-- STEP 2 OF 2: run AFTER rents_database_sqlite_en.sql, on the same database (SQLite 3.25+).\n"
            "-- Each query starts with its title and its level.\n"
            "-- Sources: Statistics Canada and CMHC, Open Government Licence – Canada.\n\n"
            + "".join(f"-- ===================================================================== {n}\n{q.strip()}\n\n\n" for n, q in queries.items()))
    files = {"rents_database_sqlite_en.sql": dump, "rents_queries_sqlite_en.sql": reqs}
    for name in ("rents_database_sqlserver.sql", "rents_queries_sqlserver.sql", "rents_database_postgres.sql", "rents_queries_postgres.sql"):
        files[name.replace(".sql", "_en.sql")] = tidy((MIR / "docs" / "assets" / name).read_text(encoding="utf-8-sig"),
                                                      "sqlserver" if "sqlserver" in name else "postgres")
    for name, text in files.items():
        french_left(text, name)
        (ASSETS / name).write_text(text, encoding="utf-8-sig" if "sqlserver" in name else "utf-8")
    shutil.copy(en_path, ASSETS / "rents_en.sqlite")
    print(f"version anglaise : {len(queries)} requêtes aux résultats identiques à la version française · "
          f"{len(files)} fichiers · rents_en.sqlite")
