"""
Vérifie (et met à jour) les données du projet à partir de l'API officielle de Statistique Canada.

Le script télécharge les tableaux complets par le service web WDS
(https://www.statcan.gc.ca/fr/developpeurs/wds), extrait exactement les séries utilisées par le projet
et les compare valeur par valeur aux fichiers de data/raw.

  python src/fetch_statcan.py                 # vérification : affiche les écarts, code de sortie 1 s'il y en a
  python src/fetch_statcan.py --mettre-a-jour # réécrit data/raw avec les dernières données publiées

Dépendance : pandas. À exécuter sur un poste avec accès à Internet (ou dans Google Colab).
"""
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
WDS = "https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/{pid}/en"
UA = {"User-Agent": "loyers-montreal/1.0 (projet etudiant)"}

CITIES = {  # nom du projet -> libellé GEO exact dans les tableaux 34-10-0133 et 34-10-0127
    "Montreal": "Montréal, Quebec", "Quebec": "Québec, Quebec", "Ottawa-Gatineau": "Ottawa-Gatineau, Ontario/Quebec",
    "Toronto": "Toronto, Ontario", "Calgary": "Calgary, Alberta", "Vancouver": "Vancouver, British Columbia",
}
UNITS = ["Bachelor units", "One bedroom units", "Two bedroom units", "Three bedroom units"]
STRUCTURE = "Apartment structures of three units and over"


def download(pid: str) -> pd.DataFrame:
    """Télécharge un tableau complet (CSV dans un ZIP) et le renvoie sous forme de DataFrame."""
    with urllib.request.urlopen(urllib.request.Request(WDS.format(pid=pid), headers=UA), timeout=60) as r:
        meta = json.load(r)
    if meta.get("status") != "SUCCESS":
        raise RuntimeError(f"Tableau {pid} : réponse inattendue de l'API : {meta}")
    with urllib.request.urlopen(urllib.request.Request(meta["object"], headers=UA), timeout=300) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    name = next(n for n in z.namelist() if n.endswith(".csv") and "MetaData" not in n)
    df = pd.read_csv(z.open(name), low_memory=False)
    df["REF_DATE"] = df["REF_DATE"].astype(str)
    return df


def official_rents(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """34-10-0133 : loyers de Montréal par type, et 2 chambres pour les six villes."""
    t = t[t["Type of structure"] == STRUCTURE]
    mtl = t[(t.GEO == CITIES["Montreal"]) & t["Type of unit"].isin(UNITS)]
    mtl = mtl[mtl.REF_DATE.astype(int) >= 1992].rename(columns={"REF_DATE": "year", "Type of unit": "unit_type", "VALUE": "value"})
    villes = t[t.GEO.isin(CITIES.values()) & (t["Type of unit"] == "Two bedroom units")]
    villes = villes[villes.REF_DATE.astype(int) >= 1992].assign(geo=lambda d: d.GEO.map({v: k for k, v in CITIES.items()}))
    villes = villes.rename(columns={"REF_DATE": "year", "VALUE": "value"})
    return (mtl[["year", "unit_type", "value"]].dropna(), villes[["year", "geo", "value"]].dropna())


def official_vacancy(t: pd.DataFrame) -> pd.DataFrame:
    """34-10-0127 : taux d'inoccupation des six villes."""
    v = t[t.GEO.isin(CITIES.values())].assign(geo=lambda d: d.GEO.map({v: k for k, v in CITIES.items()}))
    v = v[v.REF_DATE.astype(int) >= 1992].rename(columns={"REF_DATE": "year", "VALUE": "value"})
    return v[["year", "geo", "value"]].dropna()


def official_cpi(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """18-10-0005 : IPC d'ensemble de Montréal ; IPC loyer et ensemble par province depuis 2019."""
    prod = "Products and product groups"
    mtl = t[(t.GEO == "Montréal, Quebec") & (t[prod] == "All-items") & (t.REF_DATE.astype(int) >= 1992)]
    mtl = mtl.rename(columns={"REF_DATE": "year", "VALUE": "value"}).assign(geo="Montreal", product="All-items", uom="2002=100")
    provs = ["Canada", "Newfoundland and Labrador", "Prince Edward Island", "Nova Scotia", "New Brunswick", "Quebec",
             "Ontario", "Manitoba", "Saskatchewan", "Alberta", "British Columbia"]
    p = t[t.GEO.isin(provs) & t[prod].isin(["All-items", "Rent"]) & (t.REF_DATE.astype(int) >= 2019)]
    p = p.rename(columns={"REF_DATE": "year", "GEO": "geo", prod: "product", "VALUE": "value"})
    return mtl[["year", "geo", "product", "value", "uom"]], p[["year", "geo", "product", "value"]]


def official_asking(t: pd.DataFrame, ref: pd.DataFrame, n_quarters: int = 5) -> pd.DataFrame:
    """46-10-0092 : loyers demandés et payés, appartements de 2 chambres, derniers trimestres."""
    t = t[t["Rental unit type"] == "Apartment - 2 bedrooms"].copy()
    t["est"] = t["Estimates"].map({"Average asking rent": "A", "Average paid rent": "P"})
    t["geo_id"] = t["COORDINATE"].astype(str).str.split(".").str[0].astype(int)
    keep = sorted(t.REF_DATE.unique())[-n_quarters:]
    t = t[t.REF_DATE.isin(keep) & t.geo_id.isin(ref.geo_id)]
    t = t.rename(columns={"REF_DATE": "ref", "VALUE": "value", "STATUS": "status"})
    return t[["ref", "geo_id", "est", "value", "status"]]


def compare(name: str, official: pd.DataFrame, local: pd.DataFrame, keys: list[str], tol: float = 0.05) -> int:
    official = official.copy()
    local = local.copy()
    for k in keys:
        official[k] = official[k].astype(str)
        local[k] = local[k].astype(str)
    m = local.merge(official, on=keys, how="left", suffixes=("_projet", "_statcan"))
    absent = m["value_statcan"].isna() & m["value_projet"].notna()
    diff = (m["value_projet"] - m["value_statcan"]).abs() > tol
    bad = m[absent | diff]
    print(f"{name:<52} {len(local):>4} valeurs vérifiées · {len(bad)} écart(s)")
    if len(bad):
        print(bad.head(20).to_string(index=False))
    return len(bad)


def main(update: bool) -> int:
    ref = pd.read_csv(RAW / "ref_rmr_46100092.csv", sep=";")
    print("Téléchargement des tableaux officiels…")
    t133, t127, t005, t092 = (download(p) for p in ("34100133", "34100127", "18100005", "46100092"))
    mtl, villes = official_rents(t133)
    vac = official_vacancy(t127)
    cpi_mtl, cpi_prov = official_cpi(t005)
    asking = official_asking(t092, ref)

    if update:
        mtl.to_csv(RAW / "statcan_34100133_montreal_loyers_par_chambres.csv", index=False)
        villes.to_csv(RAW / "statcan_34100133_loyers_2ch_6_rmr.csv", index=False)
        vac.to_csv(RAW / "statcan_34100127_taux_inoccupation_6_rmr.csv", index=False)
        cpi_mtl.to_csv(RAW / "statcan_18100005_ipc_montreal.csv", index=False)
        cpi_prov.to_csv(RAW / "statcan_18100005_ipc_provinces.csv", index=False)
        asking.to_csv(RAW / "statcan_46100092_loyers_demandes_payes_2ch.csv", index=False)
        print("data/raw mis à jour. Relance ensuite les scripts de construction.")
        return 0

    n = 0
    n += compare("34-10-0133 · Montréal, loyers par type", mtl,
                 pd.read_csv(RAW / "statcan_34100133_montreal_loyers_par_chambres.csv"), ["year", "unit_type"])
    n += compare("34-10-0133 · 2 chambres, six villes", villes,
                 pd.read_csv(RAW / "statcan_34100133_loyers_2ch_6_rmr.csv"), ["year", "geo"])
    n += compare("34-10-0127 · taux d'inoccupation", vac,
                 pd.read_csv(RAW / "statcan_34100127_taux_inoccupation_6_rmr.csv"), ["year", "geo"])
    n += compare("18-10-0005 · IPC Montréal", cpi_mtl,
                 pd.read_csv(RAW / "statcan_18100005_ipc_montreal.csv"), ["year", "geo", "product"])
    n += compare("18-10-0005 · IPC par province", cpi_prov,
                 pd.read_csv(RAW / "statcan_18100005_ipc_provinces.csv"), ["year", "geo", "product"])
    n += compare("46-10-0092 · loyers demandés et payés", asking,
                 pd.read_csv(RAW / "statcan_46100092_loyers_demandes_payes_2ch.csv"), ["ref", "geo_id", "est"])
    print("\nAucun écart : les données du projet correspondent aux tableaux officiels." if n == 0
          else f"\n{n} écart(s) à examiner avant de publier.")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main("--mettre-a-jour" in sys.argv))
