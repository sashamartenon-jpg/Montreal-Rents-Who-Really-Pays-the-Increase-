"""
Construit la base SQLite du projet (modèle en étoile) et exécute les requêtes de sql/.
Chaque requête est contrôlée contre les chiffres calculés en Python : si un résultat diffère,
le script s'arrête.

Sorties : data/loyers.sqlite, docs/assets/loyers.sqlite (pour la console SQL du site),
          docs/data/sql_results.json (résultats affichés si la console ne peut pas se charger)
Exécution : python src/build_db.py   (après src/pipeline.py)
"""
from pathlib import Path
import json
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN, SQL = ROOT / "data" / "clean", ROOT / "sql"
DB = ROOT / "data" / "loyers.sqlite"
SITE_DB = ROOT / "docs" / "assets" / "loyers.sqlite"

SCHEMA_DIR = SQL / "schema"  # DDL : tables, contraintes, index (01) puis vues (02)
DUMP = ROOT / "docs" / "assets" / "loyers.sql"


PROVINCES = [("NL", "Terre-Neuve-et-Labrador", "province"), ("PE", "Île-du-Prince-Édouard", "province"),
             ("NS", "Nouvelle-Écosse", "province"), ("NB", "Nouveau-Brunswick", "province"), ("QC", "Québec", "province"),
             ("ON", "Ontario", "province"), ("MB", "Manitoba", "province"), ("SK", "Saskatchewan", "province"),
             ("AB", "Alberta", "province"), ("BC", "Colombie-Britannique", "province"), ("YT", "Yukon", "territoire"),
             ("NT", "Territoires du Nord-Ouest", "territoire"), ("NU", "Nunavut", "territoire"), ("CA", "Canada", "pays")]
INDICATEURS = {"loyer_moyen_reloues_2ch": "Loyer moyen d'un 2 chambres reloué à un nouveau locataire",
               "hausse_loyer_reloues_2ch": "Hausse du loyer des 2 chambres reloués",
               "hausse_loyer_non_reloues_2ch": "Hausse du loyer des 2 chambres non reloués (locataires en place)",
               "hausse_loyer_meme_echantillon_2ch": "Hausse du loyer des 2 chambres à échantillon constant",
               "taux_inoccupation_3plus": "Taux d'inoccupation, immeubles de 3 logements et plus"}


def build(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    for f in sorted(SCHEMA_DIR.glob("*.sql")):
        con.executescript(f.read_text(encoding="utf-8"))
    u = pd.read_csv(CLEAN / "dim_unit.csv")
    con.executemany("INSERT INTO dim_logement VALUES (?,?,?,?)",
                    u[["unit_id", "label_fr", "label_en", "bedrooms"]].itertuples(index=False))
    g = pd.read_csv(CLEAN / "dim_geo.csv")
    con.executemany("INSERT INTO dim_geo VALUES (?,?,?)", g.itertuples(index=False))
    m = pd.read_csv(CLEAN / "fait_loyers_montreal.csv")
    c = pd.read_csv(CLEAN / "fait_loyers_2ch_rmr.csv")
    c = c[c.geo_id != "Montreal"].assign(unit_id="2ch")  # Montréal 2 ch. déjà dans la table Montréal
    rows = pd.concat([m[["year", "geo_id", "unit_id", "loyer_nominal"]], c[["year", "geo_id", "unit_id", "loyer_nominal"]]])
    con.executemany("INSERT INTO fait_loyer VALUES (?,?,?,?)", rows.astype(object).itertuples(index=False))
    v = pd.read_csv(CLEAN / "fait_inoccupation.csv")
    con.executemany("INSERT INTO fait_inoccupation VALUES (?,?,?)",
                    v[["year", "geo_id", "taux_inoccupation_pct"]].astype(object).itertuples(index=False))
    con.executemany("INSERT INTO dim_province VALUES (?,?,?)", PROVINCES)
    con.executemany("INSERT INTO dim_estimation VALUES (?,?)", [("A", "Loyer demandé"), ("P", "Loyer payé")])
    i = pd.read_csv(CLEAN / "ipc_montreal.csv")
    con.executemany("INSERT INTO ipc VALUES (?,'Montreal',?)", i[["year", "ipc_2002_100"]].astype(object).itertuples(index=False))
    t = pd.read_csv(CLEAN / "schl_roulement.csv")
    ind = t[["indicateur", "unite"]].drop_duplicates()
    assert not ind.indicateur.duplicated().any(), "un indicateur a deux unités"
    con.executemany("INSERT INTO dim_indicateur VALUES (?,?,?)",
                    [(c, INDICATEURS[c], u) for c, u in ind.itertuples(index=False)])
    con.executemany("INSERT INTO schl_roulement VALUES (?,'Montreal',?,?)",
                    t[["year", "indicateur", "valeur"]].astype(object).itertuples(index=False))
    r = pd.read_csv(CLEAN / "dim_rmr.csv")
    con.executemany("INSERT INTO dim_rmr VALUES (?,?,?,?,?)", r.astype(object).where(r.notna(), None).itertuples(index=False))
    q = pd.read_csv(CLEAN / "fait_loyer_trimestriel.csv", dtype={"cote": str})
    q = q[["periode", "geo_id", "estimation", "loyer", "cote"]].astype(object).where(q.notna(), None)
    con.executemany("INSERT INTO fait_loyer_trimestriel VALUES (?,?,?,?,?)", q.itertuples(index=False))
    p = pd.read_csv(CLEAN / "fait_ipc_provinces.csv")
    con.executemany("INSERT INTO ipc_provinces VALUES (?,?,?,?)",
                    p[["annee", "code", "ipc_loyer", "ipc_ensemble"]].astype(object).itertuples(index=False))
    con.commit()
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    assert not bad, f"Clés étrangères orphelines : {bad[:5]}"
    check_dictionary(con)
    con.execute("VACUUM")
    return con


def check_dictionary(con):
    """Le dictionnaire de données doit décrire exactement chaque colonne de chaque table et vue, avec le bon type."""
    dico = pd.read_csv(ROOT / "data" / "ref" / "dictionnaire.csv", sep=";", dtype=str).fillna("")
    assert dico.shape[1] == 6 and not dico.duplicated(["table", "colonne"]).any(), "dictionnaire.csv mal formé"
    documented = {(r.table, r.colonne): r.type for r in dico.itertuples()}
    actual = {}
    for name, kind in con.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"):
        for _, col, typ, *_ in con.execute(f"PRAGMA table_info({name})"):
            actual[(name, col)] = (typ, kind)
    missing, extra = set(actual) - set(documented), set(documented) - set(actual)
    assert not missing and not extra, f"Dictionnaire incomplet : manque {sorted(missing)}, en trop {sorted(extra)}"
    wrong = [(k, documented[k], t) for k, (t, kind) in actual.items() if kind == "table" and documented[k] != t]
    assert not wrong, f"Types du dictionnaire différents du schéma : {wrong}"


def run_all(con):
    out = []
    for f in sorted(SQL.glob("*.sql")):
        text = f.read_text(encoding="utf-8")
        cur = con.execute(text)
        cols = [d[0] for d in cur.description]
        out.append({"file": f.name, "title": text.splitlines()[0].lstrip("- ").strip(),
                    "sql": text.strip(), "columns": cols, "rows": cur.fetchall()})
    return out


def check(results, k):
    """Chaque requête qui produit un chiffre publié est comparée au calcul Python."""
    r = {x["file"]: x for x in results}
    rows = lambda f: r[f]["rows"]
    qa = {x[0]: x for x in rows("01_controle_qualite.sql")}
    assert qa["fait_loyer"][4] == 0 and qa["ipc_provinces"][4] == 0, qa
    var = [x for x in rows("02_variation_par_type.sql") if x[1] == "2 chambres" and x[0] == 2025][0]
    assert abs(var[3] - k["hausse_annuelle_2025"]) < 0.05, var
    rythme = rows("05_rythme_par_periode.sql")
    assert abs(rythme[0][1] - k["hausse_reelle_1992_2019"]) < 0.05 and abs(rythme[1][1] - k["hausse_reelle_2019_2025"]) < 0.05, rythme
    villes = rows("06_classement_villes.sql")
    assert villes[0][1] == "Montréal" and abs(villes[0][4] - k["hausse_2019_2025_par_ville"]["Montreal"]) < 0.05, villes
    # recoupement entre deux requêtes : le rang de Montréal (07) doit découler des loyers 2025 de la requête 06
    rang = [x for x in rows("07_rang_montreal_par_annee.sql") if x[0] == 2025][0]
    mtl_2025 = [x for x in villes if x[1] == "Montréal"][0][3]
    assert rang[2] == 1 + sum(1 for x in villes if x[3] < mtl_2025), rang
    reloc = rows("08_prime_de_relocation.sql")[-1]
    assert reloc[0] == 2025 and reloc[3] == k["prime_relocation_2025"], reloc
    mtl = [x for x in rows("09_demande_vs_paye.sql") if x[1] == "Montréal"][0]
    assert mtl[6] == k["mtl_ecart_dernier"] and abs(mtl[7] - k["mtl_ecart_pct_dernier"]) < 0.05, mtl
    prov = rows("10_provinces_loyer_inflation.sql")
    qc = [x for x in prov if x[1] == "Québec"][0]
    assert qc[0] == k["qc_rang_hausse_2025"] and abs(qc[2] - k["qc_hausse_loyer_2025"]) < 0.05, qc
    vq = {x[0]: x for x in rows("12_vues_quebec.sql")}
    assert vq["Montréal"][3] == k["mtl_ecart_pct_dernier"] and vq["Montréal"][4] == k["qc_hausse_loyer_2025"], vq["Montréal"]


if __name__ == "__main__":
    con = build(DB)
    res = run_all(con)
    data = json.loads((ROOT / "docs" / "data" / "data.json").read_text(encoding="utf-8"))
    check(res, data["insights"])
    con.close()
    build(SITE_DB).close()
    with sqlite3.connect(DB) as c_:  # export complet en SQL pur : schéma + données, rejouable dans n'importe quel SQLite
        DUMP.write_text("-- Base « Loyers à Montréal » : export complet (schéma, données, vues), SQLite 3.25+\n"
                        "-- ÉTAPE 1 SUR 2 : exécuter ce fichier en premier, dans une base vide, une seule fois.\n"
                        "-- ÉTAPE 2 : exécuter requetes_loyers_montreal.sql sur la même base.\n"
                        + "\n".join(c_.iterdump()) + "\n", encoding="utf-8")
    (ROOT / "docs" / "data" / "sql_results.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    for x in res:
        print(f"\n== {x['file']} ({len(x['rows'])} lignes)")
        print(pd.DataFrame(x["rows"], columns=x["columns"]).to_string(index=False))
    print("\nToutes les requêtes concordent avec le pipeline Python.")
