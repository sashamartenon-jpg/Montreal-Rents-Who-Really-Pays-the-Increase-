"""Version PostgreSQL de la base : sql/postgres/loyers_postgres.sql (schéma, vues, données).

Dérivée des scripts SQLite du projet (sql/schema/*.sql) et des données de data/loyers.sqlite,
pour que les deux versions ne divergent jamais. Chaque instruction est validée par le parseur
PostgreSQL (pglast, la grammaire de PostgreSQL elle-même) : une erreur de syntaxe arrête la construction.
Écarts SQLite → PostgreSQL appliqués ici, et seulement ceux-là :
  PRAGMA foreign_keys           retiré (toujours actif dans PostgreSQL)
  GLOB 'motif'                  → expression régulière  ~ '^...$'
  REAL                          → DOUBLE PRECISION
  ROUND(expr, n) sur un double  → ROUND(expr::numeric, n)   (PostgreSQL n'arrondit que les numeric)
  sous-requête FROM sans alias  → alias obligatoire (… ) AS s
"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sql" / "postgres" / "loyers_postgres.sql"
TABLES = (ROOT / "sql" / "schema" / "01_tables.sql").read_text(encoding="utf-8")
VUES = (ROOT / "sql" / "schema" / "02_vues.sql").read_text(encoding="utf-8")


def to_pg(sql):
    sql = re.sub(r"^PRAGMA[^\n]*\n", "", sql, flags=re.M)
    sql = sql.replace("GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'", r"~ '^\d{4}-[01]\d$'")
    sql = re.sub(r"\bREAL\b", "DOUBLE PRECISION", sql)
    sql = sql.replace("Moteur : SQLite (compatible PostgreSQL / DuckDB avec ajustements mineurs)",
                      "Moteur : PostgreSQL 12+ (version dérivée du script SQLite par src/postgres.py)")
    return sql


def round_numeric(sql):
    """ROUND(x, n) → ROUND((x)::numeric, n) en respectant les parenthèses imbriquées."""
    out, i = [], 0
    while True:
        j = sql.find("ROUND(", i)
        if j < 0:
            out.append(sql[i:])
            return "".join(out)
        out.append(sql[i:j])
        k, depth, comma = j + 6, 1, None
        while depth:
            ch = sql[k]
            depth += (ch == "(") - (ch == ")")
            if depth == 1 and ch == "," and comma is None:
                comma = k
            k += 1
        inner = sql[j + 6:k - 1]
        if comma is None:
            out.append(f"ROUND(({inner})::numeric)")
        else:
            a, b = sql[j + 6:comma], sql[comma + 1:k - 1]
            out.append(f"ROUND(({a.strip()})::numeric,{b})")
        i = k


tables_pg = to_pg(TABLES)
vues_pg = round_numeric(to_pg(VUES)).replace(")\nWHERE rn = 1;", ") AS s\nWHERE rn = 1;")

# ---------------------------------------------------------------- données depuis la base SQLite
con = sqlite3.connect(ROOT / "data" / "loyers.sqlite")
order = re.findall(r"CREATE TABLE (\w+)", TABLES)          # ordre de création = ordre de chargement (clés étrangères)
lit = lambda v: "NULL" if v is None else (str(v) if isinstance(v, (int, float)) else "'" + str(v).replace("'", "''") + "'")
data = []
for t in order:
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
    rows = con.execute(f"SELECT {', '.join(cols)} FROM {t}").fetchall()
    data.append(f"\n-- {t} : {len(rows)} lignes")
    for i in range(0, len(rows), 200):
        vals = ",\n".join("  (" + ", ".join(lit(v) for v in r) + ")" for r in rows[i:i + 200])
        data.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES\n{vals};")
con.close()

header = """-- =====================================================================
-- Base « Loyers à Montréal » pour PostgreSQL : schéma, vues, données
-- Générée par src/postgres.py depuis les scripts SQLite du projet et data/loyers.sqlite.
-- Chargement :  createdb loyers && psql -d loyers -f loyers_postgres.sql
-- Les 12 requêtes de sql/requetes/ sont en SQL standard ; deux ajustements PostgreSQL :
--   ROUND(x, n) demande un numeric → ROUND((x)::numeric, n) ; POWER et || sont identiques.
-- =====================================================================
BEGIN;
"""
script = header + tables_pg.strip() + "\n\n" + vues_pg.strip() + "\n\n-- ---------------------------------------------------------------- données\n" + "\n".join(data) + "\n\nCOMMIT;\n"

# ---------------------------------------------------------------- validation par la grammaire PostgreSQL
from pglast import parse_sql
from pglast.parser import ParseError
try:
    stmts = parse_sql(script)
except ParseError as e:
    raise SystemExit(f"loyers_postgres.sql : syntaxe PostgreSQL invalide : {e}")
n_tables = sum(1 for s in stmts if s.stmt.__class__.__name__ == "CreateStmt")
n_views = sum(1 for s in stmts if s.stmt.__class__.__name__ == "ViewStmt")
n_idx = sum(1 for s in stmts if s.stmt.__class__.__name__ == "IndexStmt")
n_ins = sum(1 for s in stmts if s.stmt.__class__.__name__ == "InsertStmt")
assert n_tables == len(order) and n_views == VUES.count("CREATE VIEW"), (n_tables, n_views)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(script, encoding="utf-8")
(ROOT / "docs" / "assets" / "loyers_postgres.sql").write_text(script, encoding="utf-8")
print(f"PostgreSQL : {OUT.relative_to(ROOT)} · {n_tables} tables, {n_views} vues, {n_idx} index, {n_ins} INSERT · {len(stmts)} instructions validées par pglast")
