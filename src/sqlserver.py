"""Version SQL Server (T-SQL) de la base et des requêtes :
  sql/sqlserver/loyers_sqlserver.sql    schéma, vues, données (lots séparés par GO)
  sql/sqlserver/requetes_sqlserver.sql  les 12 requêtes analytiques

Dérivée des scripts SQLite du projet (sql/schema/*.sql, sql/*.sql) et de data/loyers.sqlite, pour que
les versions ne divergent jamais. Les requêtes et les vues sont traduites par sqlglot (sqlite → tsql),
puis chaque instruction est relue par deux parseurs T-SQL (sqlglot et sqlfluff) : une erreur arrête
la construction. Écarts SQLite → SQL Server appliqués ici, et seulement ceux-là :
  PRAGMA foreign_keys           retiré (toujours actif)
  TEXT / INTEGER / REAL         → NVARCHAR(100) / INT / FLOAT   (TEXT existe dans SQL Server mais ne se compare pas)
  length(x)                     → LEN(x)
  GLOB 'motif'                  → LIKE '[0-9][0-9][0-9][0-9]-[0-1][0-9]'  (même classe de caractères)
  a || b                        → CONCAT(a, b)   (+ convertit les nombres en erreur ; CONCAT les convertit en texte)
  LIMIT n                       → TOP n
  x / y                         inchangé (sqlglot proposerait NULLIF(y, 0) ; les diviseurs sont contraints > 0 par CHECK)
  WINDOW w AS (...)             → fenêtre écrite dans chaque OVER (clause WINDOW réservée au niveau de compatibilité 160)
  sous-requête FROM sans alias  → alias obligatoire
  CREATE VIEW                   → un lot par vue (GO), exigence de SQL Server
  INSERT                        → 500 lignes par instruction (limite : 1000), chaînes préfixées N''
Un alias de CTE nommé « pivot » (mot réservé en T-SQL) a été renommé à la source.
"""
import re
import sqlite3
from pathlib import Path

import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "sql" / "sqlserver"
TABLES = (ROOT / "sql" / "schema" / "01_tables.sql").read_text(encoding="utf-8")
VUES = (ROOT / "sql" / "schema" / "02_vues.sql").read_text(encoding="utf-8")
REQUETES = sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql"))


# ---------------------------------------------------------------- schéma : traduction textuelle (commentaires conservés)
def schema_tsql(sql):
    sql = re.sub(r"^PRAGMA[^\n]*\n", "", sql, flags=re.M)
    sql = sql.replace("Moteur : SQLite (compatible PostgreSQL / DuckDB avec ajustements mineurs)",
                      "Moteur : SQL Server 2016+ (version dérivée du script SQLite par src/sqlserver.py)")
    sql = re.sub(r"\bTEXT\b", "NVARCHAR(100)", sql)
    sql = re.sub(r"\bINTEGER\b", "INT", sql)
    sql = re.sub(r"\bREAL\b", "FLOAT", sql)
    sql = sql.replace("length(code)", "LEN(code)")
    sql = sql.replace("GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'", "LIKE '[0-9][0-9][0-9][0-9]-[0-1][0-9]'")
    # les colonnes NVARCHAR(100) cassent l'alignement des types sur une seule colonne : on laisse, c'est lisible
    return sql


# ---------------------------------------------------------------- requêtes et vues : sqlglot + retouches
def concat_dpipe(node):
    """a || b || c  →  CONCAT(a, b, c) : en T-SQL, + sur un entier et un texte est une erreur de conversion.
    Division : SQLite renvoie NULL pour x / 0, SQL Server une erreur ; sqlglot entoure donc chaque diviseur
    d'un NULLIF(…, 0). Ici tous les diviseurs sont des loyers ou des indices contraints par CHECK (> 0) :
    on garde la division telle qu'écrite, lisible."""
    if isinstance(node, exp.Div):
        node.set("safe", None)
        return node
    if isinstance(node, exp.DPipe):
        parts = []

        def flat(n):
            if isinstance(n, exp.DPipe):
                flat(n.this)
                flat(n.expression)
            else:
                parts.append(n)
        flat(node)
        return exp.Anonymous(this="CONCAT", expressions=parts)
    return node


def inline_window(sql):
    """WINDOW w AS (...) en fin de requête → la définition recopiée dans chaque OVER w."""
    m = re.search(r"\nWINDOW (\w+) AS \((.*?)\)\s*$", sql, flags=re.S)
    if not m:
        return sql
    name, spec = m.group(1), m.group(2)
    sql = sql[:m.start()] + sql[m.end():]
    return re.sub(rf"\bOVER {name}\b", f"OVER ({spec})", sql)


def polish(sql):
    sql = re.sub(r"^/\* (.*?) \*/$", r"-- \1", sql, flags=re.M)        # commentaires d'en-tête en -- comme à la source
    sql = sql.replace("COUNT_BIG(", "COUNT(")
    sql = re.sub(r"\bNOT (\w+(?:\.\w+)?) IS NULL\b", r"\1 IS NOT NULL", sql)
    sql = re.sub(r"^(\s+)(\w+) AS \2(,?)$", r"\1\2\3", sql, flags=re.M)  # « annee AS annee » → « annee »
    sql = re.sub(r"^(\s+)(\w+\.)(\w+) AS \3(,?)$", r"\1\2\3\4", sql, flags=re.M)
    # CTE sur un constructeur VALUES : SQL Server exige les noms de colonnes de la table dérivée
    sql = re.sub(r"(\w+)\(([^)]+)\) AS \(\s*SELECT\s*\*\s*FROM \(VALUES(.*?)\) AS _values\s*\)",
                 lambda m: f"{m.group(1)}({m.group(2)}) AS (\n  SELECT * FROM (VALUES{m.group(3)}) AS v({m.group(2)})\n)",
                 sql, flags=re.S)
    sql = inline_window(sql)
    return sql.strip()


def to_tsql(sqlite_sql):
    out = []
    for stmt in sqlglot.parse(sqlite_sql, read="sqlite"):
        if stmt is None:
            continue
        stmt = stmt.transform(concat_dpipe)
        out.append(polish(stmt.sql(dialect="tsql", pretty=True)))
    return out


vues = to_tsql(VUES)
# sous-requête FROM sans alias (v_dernier_trimestre)
vues = [re.sub(r"\n\)\nWHERE\n  rn = 1$", "\n) AS s\nWHERE\n  rn = 1", v) for v in vues]
assert len(vues) == VUES.count("CREATE VIEW"), len(vues)
assert any("TOP 1" in v for v in vues) and not any("WINDOW" in v for v in vues)

requetes = []
for f in REQUETES:
    src = f.read_text(encoding="utf-8")
    heads = [l for l in src.splitlines() if l.startswith("--")]       # titre + niveau, tels quels
    body = to_tsql(src)
    assert len(body) == 1, f.name
    q = body[0]
    q = "\n".join(l for l in q.splitlines() if not l.startswith("-- "))  # sqlglot a déjà recopié les commentaires
    requetes.append("\n".join(heads) + "\n" + q.strip() + ";")

# ---------------------------------------------------------------- données depuis la base SQLite
con = sqlite3.connect(ROOT / "data" / "loyers.sqlite")
order = re.findall(r"CREATE TABLE (\w+)", TABLES)


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return repr(v)
    return "N'" + str(v).replace("'", "''") + "'"


data = []
for t in order:
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
    rows = con.execute(f"SELECT {', '.join(cols)} FROM {t}").fetchall()
    data.append(f"\n-- {t} : {len(rows)} lignes")
    for i in range(0, len(rows), 500):
        vals = ",\n".join("  (" + ", ".join(lit(v) for v in r) + ")" for r in rows[i:i + 500])
        data.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES\n{vals};")
con.close()

# ---------------------------------------------------------------- assemblage
BASE = """-- =====================================================================
-- Base « Loyers à Montréal » pour SQL Server : schéma, vues, données
-- Générée par src/sqlserver.py depuis les scripts SQLite du projet et data/loyers.sqlite.
-- Chargement : ouvrir ce fichier dans Azure Data Studio ou SSMS, choisir la base cible, exécuter (F5).
--              Les vues sont dans des lots séparés (GO), comme SQL Server l'exige.
-- Requêtes : requetes_sqlserver.sql (les 12 requêtes analytiques, même dialecte).
-- =====================================================================
SET NOCOUNT ON;
GO

""" + schema_tsql(TABLES).strip() + "\nGO\n\n" + \
    "-- =====================================================================\n" \
    "-- Vues analytiques : la logique métier vit dans la base, pas dans chaque requête\n" \
    "-- =====================================================================\n" + \
    "\nGO\n\n".join(vues) + "\nGO\n\n" + \
    "-- ---------------------------------------------------------------- données\n" + "\n".join(data) + "\nGO\n"

REQ = """-- =====================================================================
-- Loyers à Montréal : les 12 requêtes analytiques, version SQL Server (T-SQL)
-- Traduites des requêtes SQLite du projet par src/sqlserver.py. Chaque requête s'exécute
-- telle quelle sur une base chargée avec loyers_sqlserver.sql. Le niveau est indiqué en tête de chacune.
-- =====================================================================

""" + "\n\n".join(requetes) + "\n"

# ---------------------------------------------------------------- validation : deux parseurs T-SQL
for name, script in (("loyers_sqlserver.sql", BASE), ("requetes_sqlserver.sql", REQ)):
    for batch in re.split(r"^GO$", script, flags=re.M):
        for stmt in sqlglot.parse(batch, read="tsql", error_level=sqlglot.ErrorLevel.RAISE):
            pass
n_stmt = sum(len([s for s in sqlglot.parse(b, read="tsql") if s is not None]) for b in re.split(r"^GO$", BASE, flags=re.M))

OUT_DIR.mkdir(parents=True, exist_ok=True)
from sqlfluff.core import FluffConfig, Linter
linter = Linter(config=FluffConfig(overrides={"dialect": "tsql", "large_file_skip_byte_limit": 0}))
for name, script in (("loyers_sqlserver.sql", BASE), ("requetes_sqlserver.sql", REQ)):
    parsed = linter.parse_string(script, fname=name)
    errors = [str(v) for v in parsed.violations]
    unparsable = [seg.raw[:120] for seg in parsed.tree.recursive_crawl("unparsable")] if parsed.tree else ["(arbre vide)"]
    if errors or unparsable:
        raise SystemExit(f"{name} : T-SQL non reconnu par sqlfluff\n" + "\n".join(errors[:5] + unparsable[:5]))
    p = OUT_DIR / name
    p.write_text(script, encoding="utf-8-sig")             # BOM : SSMS et Azure Data Studio lisent l'UTF-8 sans ambiguïté
    (ROOT / "docs" / "assets" / name).write_bytes(p.read_bytes())

print(f"SQL Server : {len(order)} tables, {len(vues)} vues, {len(requetes)} requêtes · "
      f"{n_stmt} instructions validées par sqlglot et sqlfluff (dialecte tsql)")
