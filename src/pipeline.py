"""
Pipeline de données : Loyers à Montréal, 1992-2025.

Entrées (data/raw/, extraites de Statistique Canada) :
  - Tableau 34-10-0133-01 : loyers moyens SCHL (immeubles d'appartements de 3 logements et plus)
  - Tableau 34-10-0127-01 : taux d'inoccupation SCHL (immeubles de 6 logements et plus)
  - Tableau 18-10-0005-01 : IPC, moyenne annuelle, Montréal, Ensemble (2002=100)

Sorties :
  - data/clean/*.csv        tables propres, format long (modèle en étoile)
  - docs/data/data.json     agrégats légers chargés par le site
  - tableau/loyers_long.csv une table unique pour Tableau Public

Exécution : python src/pipeline.py   (dépendance : pandas)
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
SITE_DATA, TABLEAU = ROOT / "docs" / "data", ROOT / "tableau"
for d in (CLEAN, SITE_DATA, TABLEAU):
    d.mkdir(parents=True, exist_ok=True)

BASE_YEAR = 2025  # les loyers réels sont exprimés en dollars de 2025

UNIT_MAP = {
    "Bachelor units": ("studio", "Studio", "Studio", 0),
    "One bedroom units": ("1ch", "1 chambre", "1 bedroom", 1),
    "Two bedroom units": ("2ch", "2 chambres", "2 bedrooms", 2),
    "Three bedroom units": ("3ch", "3 chambres", "3 bedrooms", 3),
}
GEO_MAP = {
    "Montreal": ("Montréal", "Montreal"),
    "Quebec": ("Québec", "Quebec City"),
    "Ottawa-Gatineau": ("Ottawa-Gatineau", "Ottawa-Gatineau"),
    "Toronto": ("Toronto", "Toronto"),
    "Calgary": ("Calgary", "Calgary"),
    "Vancouver": ("Vancouver", "Vancouver"),
}


def load():
    rents = pd.read_csv(RAW / "statcan_34100133_montreal_loyers_par_chambres.csv")
    cities = pd.read_csv(RAW / "statcan_34100133_loyers_2ch_6_rmr.csv")
    vac = pd.read_csv(RAW / "statcan_34100127_taux_inoccupation_6_rmr.csv")
    cpi = pd.read_csv(RAW / "statcan_18100005_ipc_montreal.csv")
    return rents, cities, vac, cpi


def validate(rents, cities, vac, cpi):
    # Contrôles de qualité : pas de doublons, pas de valeurs manquantes, bornes plausibles
    assert not rents.duplicated(["year", "unit_type"]).any()
    assert not cities.duplicated(["year", "geo"]).any()
    assert not vac.duplicated(["year", "geo"]).any()
    assert rents["value"].between(200, 5000).all()
    assert cities["value"].between(200, 5000).all()
    assert vac["value"].between(0, 15).all()
    # Montréal 2 chambres doit être identique dans les deux extractions du tableau 34-10-0133
    a = rents[rents.unit_type == "Two bedroom units"].set_index("year")["value"]
    b = cities[cities.geo == "Montreal"].set_index("year")["value"]
    assert a.equals(b.loc[a.index]), "Incohérence entre les deux extractions"
    assert cpi["year"].is_unique


def transform(rents, cities, vac, cpi):
    cpi_idx = cpi.set_index("year")["value"]
    deflator = cpi_idx[BASE_YEAR] / cpi_idx  # multiplicateur vers dollars de BASE_YEAR

    # --- Dimension type de logement
    dim_unit = pd.DataFrame(
        [(k, *v) for k, v in UNIT_MAP.items()],
        columns=["source_label", "unit_id", "label_fr", "label_en", "bedrooms"],
    )
    # --- Dimension géographie
    dim_geo = pd.DataFrame(
        [(k, *v) for k, v in GEO_MAP.items()], columns=["geo_id", "label_fr", "label_en"]
    )
    # --- Dimension calendrier
    dim_year = pd.DataFrame({"year": range(1992, 2026)})
    dim_year["periode"] = pd.cut(
        dim_year.year, [1991, 2000, 2010, 2019, 2025],
        labels=["1992-2000", "2001-2010", "2011-2019", "2020-2025"],
    ).astype(str)

    # --- Faits : loyers Montréal par taille
    f_rent = rents.merge(dim_unit[["source_label", "unit_id"]], left_on="unit_type", right_on="source_label")
    f_rent = f_rent[["year", "unit_id", "value"]].rename(columns={"value": "loyer_nominal"})
    f_rent["geo_id"] = "Montreal"
    f_rent["loyer_reel_2025"] = (f_rent.loyer_nominal * f_rent.year.map(deflator)).round(0)
    f_rent = f_rent.sort_values(["unit_id", "year"])
    f_rent["var_annuelle_pct"] = (f_rent.groupby("unit_id").loyer_nominal.pct_change() * 100).round(1)

    # --- Faits : loyers 2 chambres, 6 RMR
    f_city = cities.rename(columns={"geo": "geo_id", "value": "loyer_nominal"}).sort_values(["geo_id", "year"])
    f_city["var_annuelle_pct"] = (f_city.groupby("geo_id").loyer_nominal.pct_change() * 100).round(1)

    # --- Faits : inoccupation
    f_vac = vac.rename(columns={"geo": "geo_id", "value": "taux_inoccupation_pct"})

    # --- IPC
    f_cpi = cpi[["year", "value"]].rename(columns={"value": "ipc_2002_100"})
    f_cpi["inflation_pct"] = (f_cpi.ipc_2002_100.pct_change() * 100).round(1)

    return dict(dim_unit=dim_unit, dim_geo=dim_geo, dim_year=dim_year,
                fait_loyers_montreal=f_rent, fait_loyers_2ch_rmr=f_city,
                fait_inoccupation=f_vac, ipc_montreal=f_cpi), deflator


def insights(t, deflator):
    r = t["fait_loyers_montreal"]
    two = r[r.unit_id == "2ch"].set_index("year")
    real = two.loyer_reel_2025
    cpi = t["ipc_montreal"].set_index("year").ipc_2002_100
    city = t["fait_loyers_2ch_rmr"].pivot(index="year", columns="geo_id", values="loyer_nominal")
    vac = t["fait_inoccupation"].pivot(index="year", columns="geo_id", values="taux_inoccupation_pct")

    def pct(a, b):
        return round((b / a - 1) * 100, 1)

    k = {
        "loyer_2ch_2025": int(two.loyer_nominal[2025]),
        "loyer_2ch_2019": int(two.loyer_nominal[2019]),
        "hausse_nominale_2019_2025": pct(two.loyer_nominal[2019], two.loyer_nominal[2025]),
        "inflation_2019_2025": pct(cpi[2019], cpi[2025]),
        "hausse_reelle_1992_2019": pct(real[1992], real[2019]),
        "hausse_reelle_2019_2025": pct(real[2019], real[2025]),
        "hausse_annuelle_2025": float(two.var_annuelle_pct[2025]),
        "ratio_mtl_tor_2015": round(city.Montreal[2015] / city.Toronto[2015] * 100, 1),
        "ratio_mtl_tor_2025": round(city.Montreal[2025] / city.Toronto[2025] * 100, 1),
        "inoccupation_mtl_2024": float(vac.Montreal[2024]),
        "inoccupation_mtl_2025": float(vac.Montreal[2025]),
        "hausse_2025_par_ville": {g: pct(city[g][2024], city[g][2025]) for g in city.columns},
        "hausse_2019_2025_par_ville": {g: pct(city[g][2019], city[g][2025]) for g in city.columns},
    }
    return k


def export(t, k):
    for name, df in t.items():
        df.to_csv(CLEAN / f"{name}.csv", index=False)

    r = t["fait_loyers_montreal"]
    site = {
        "meta": {
            "base_year": BASE_YEAR,
            "sources": [
                {"id": "34-10-0133-01", "title": "SCHL, loyers moyens pour les régions de 10 000 habitants et plus",
                 "url": "https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3410013301"},
                {"id": "34-10-0127-01", "title": "SCHL, taux d'inoccupation, immeubles d'appartements de six logements et plus",
                 "url": "https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3410012701"},
                {"id": "18-10-0005-01", "title": "Indice des prix à la consommation, moyenne annuelle",
                 "url": "https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1810000501"},
            ],
        },
        "units": t["dim_unit"][["unit_id", "label_fr", "label_en"]].to_dict("records"),
        "geos": t["dim_geo"].to_dict("records"),
        "rents": r[["year", "unit_id", "loyer_nominal", "loyer_reel_2025", "var_annuelle_pct"]]
                 .rename(columns={"loyer_nominal": "nom", "loyer_reel_2025": "real", "var_annuelle_pct": "yoy"})
                 .to_dict("records"),
        "cities": t["fait_loyers_2ch_rmr"].rename(columns={"loyer_nominal": "nom", "var_annuelle_pct": "yoy", "geo_id": "geo"})
                 .to_dict("records"),
        "vacancy": t["fait_inoccupation"].rename(columns={"taux_inoccupation_pct": "v", "geo_id": "geo"}).to_dict("records"),
        "cpi": t["ipc_montreal"].rename(columns={"ipc_2002_100": "cpi", "inflation_pct": "infl"}).to_dict("records"),
        "insights": k,
        "turnover": TURNOVER.to_dict("records"),
    }
    site["meta"]["sources"].append({
        "id": "SCHL RML 2025", "title": "SCHL, Rapport sur le marché locatif 2025 (figures 1 et 9, fiche Montréal)",
        "url": "https://www.cmhc-schl.gc.ca/fr/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres"})
    site["meta"]["sources"] += [
        {"id": "46-10-0092-01", "title": "Prix des loyers demandés et des loyers payés (estimations expérimentales)",
         "url": "https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=4610009201"},
        {"id": "18-10-0005-01 (provinces)", "title": "Indice des prix à la consommation, loyer et ensemble, par province",
         "url": "https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1810000501"}]
    # NaN -> null pour un JSON valide
    txt = json.dumps(site, ensure_ascii=False, separators=(",", ":")).replace("NaN", "null")
    (SITE_DATA / "data.json").write_text(txt, encoding="utf-8")

    # Table unique pour Tableau (format long)
    a = r.merge(t["dim_unit"][["unit_id", "label_fr"]], on="unit_id").rename(columns={"label_fr": "type_logement"})
    a["ville"] = "Montréal"
    b = t["fait_loyers_2ch_rmr"].merge(t["dim_geo"], on="geo_id").rename(columns={"label_fr": "ville"})
    b["type_logement"] = "2 chambres"
    cpi = t["ipc_montreal"].set_index("year").ipc_2002_100
    b["loyer_reel_2025"] = None  # l'IPC disponible est celui de Montréal seulement
    vac = t["fait_inoccupation"].merge(t["dim_geo"], on="geo_id").rename(columns={"label_fr": "ville"})
    long = pd.concat([
        a[["year", "ville", "type_logement", "loyer_nominal", "loyer_reel_2025", "var_annuelle_pct"]].assign(serie="Montréal par taille"),
        b[["year", "ville", "type_logement", "loyer_nominal", "loyer_reel_2025", "var_annuelle_pct"]].assign(serie="Comparaison RMR"),
    ])
    long = long.merge(vac[["year", "ville", "taux_inoccupation_pct"]], on=["year", "ville"], how="left")
    long = long.rename(columns={"year": "annee"})
    long.to_csv(TABLEAU / "loyers_long.csv", index=False)


def load_turnover():
    """Indicateurs publiés par la SCHL dans son rapport 2025 (non disponibles dans les tableaux de StatCan)."""
    d = pd.read_csv(RAW / "schl_rml2025_montreal_roulement.csv")
    assert not d.duplicated(["year", "indicateur"]).any()
    d[["year", "indicateur", "valeur", "unite"]].to_csv(CLEAN / "schl_roulement.csv", index=False)
    return d[["year", "indicateur", "valeur"]]


PROV_CODES = {"Newfoundland and Labrador": "NL", "Prince Edward Island": "PE", "Nova Scotia": "NS",
              "New Brunswick": "NB", "Quebec": "QC", "Ontario": "ON", "Manitoba": "MB", "Saskatchewan": "SK",
              "Alberta": "AB", "British Columbia": "BC", "Canada": "CA"}
PROV_FR = {"NL": "Terre-Neuve-et-Labrador", "PE": "Île-du-Prince-Édouard", "NS": "Nouvelle-Écosse",
           "NB": "Nouveau-Brunswick", "QC": "Québec", "ON": "Ontario", "MB": "Manitoba", "SK": "Saskatchewan",
           "AB": "Alberta", "BC": "Colombie-Britannique", "CA": "Canada"}


def build_map():
    """Données de la carte : IPC du loyer par province (annuel) et loyers demandés / payés par RMR (trimestriel)."""
    # --- IPC par province
    c = pd.read_csv(RAW / "statcan_18100005_ipc_provinces.csv")
    assert not c.duplicated(["year", "geo", "product"]).any()
    assert set(c.geo) == set(PROV_CODES), "Province inattendue"
    c["code"] = c.geo.map(PROV_CODES)
    pv = c.pivot_table(index=["code", "year"], columns="product", values="value").reset_index()
    pv.columns = ["code", "annee", "ipc_ensemble", "ipc_loyer"]
    pv["province"] = pv.code.map(PROV_FR)
    pv[["annee", "code", "province", "ipc_loyer", "ipc_ensemble"]].to_csv(CLEAN / "fait_ipc_provinces.csv", index=False)

    # --- loyers demandés et payés (2 chambres, appartements)
    q = pd.read_csv(RAW / "statcan_46100092_loyers_demandes_payes_2ch.csv", dtype={"status": str})
    q["status"] = q["status"].fillna("")
    assert not q.duplicated(["ref", "geo_id", "est"]).any()
    # cote F ou .. = estimation non publiable : on la retire ; E = à utiliser avec prudence, conservée et signalée
    q.loc[q.status.isin(["F", ".."]), "value"] = None
    assert q.value.dropna().between(500, 5000).all()
    ref = pd.read_csv(RAW / "ref_rmr_46100092.csv", sep=";")
    assert set(q.geo_id) <= set(ref.geo_id)
    ref.to_csv(CLEAN / "dim_rmr.csv", index=False)
    q.rename(columns={"ref": "periode", "est": "estimation", "value": "loyer", "status": "cote"}) \
        .to_csv(CLEAN / "fait_loyer_trimestriel.csv", index=False)

    latest, year_ago = q.ref.max(), sorted(q.ref.unique())[0]
    w = q.pivot_table(index="geo_id", columns=["est", "ref"], values="value")
    cities = []
    for _, r in ref.iterrows():
        g = r.geo_id
        get = lambda e, p: (float(w.loc[g, (e, p)]) if g in w.index and (e, p) in w.columns and pd.notna(w.loc[g, (e, p)]) else None)
        flag = lambda e, p: (q[(q.geo_id == g) & (q.est == e) & (q.ref == p)].status.tolist() or [""])[0]
        a, a0, p_, p0 = get("A", latest), get("A", year_ago), get("P", latest), get("P", year_ago)
        cities.append({
            "id": int(g), "nom": r.nom, "prov": r.province,
            "lat": None if pd.isna(r.lat) else float(r.lat), "lon": None if pd.isna(r.lon) else float(r.lon),
            "demande": a, "paye": p_,
            "ecart": round(a - p_) if a and p_ else None,
            "ecart_pct": round((a / p_ - 1) * 100, 1) if a and p_ else None,
            "var_demande": round((a / a0 - 1) * 100, 1) if a and a0 else None,
            "var_paye": round((p_ / p0 - 1) * 100, 1) if p_ and p0 else None,
            "cote": flag("A", latest),
            "serie_demande": [get("A", p) for p in sorted(q.ref.unique())],
            "serie_paye": [get("P", p) for p in sorted(q.ref.unique())],
        })

    provinces = []
    for code, d in pv.groupby("code"):
        d = d.set_index("annee")
        provinces.append({
            "code": code, "nom": PROV_FR[code],
            "hausse_loyer": round((d.ipc_loyer[2025] / d.ipc_loyer[2019] - 1) * 100, 1),
            "hausse_inflation": round((d.ipc_ensemble[2025] / d.ipc_ensemble[2019] - 1) * 100, 1),
            "hausse_reelle": round(((d.ipc_loyer[2025] / d.ipc_loyer[2019]) / (d.ipc_ensemble[2025] / d.ipc_ensemble[2019]) - 1) * 100, 1),
            "hausse_loyer_2025": round((d.ipc_loyer[2025] / d.ipc_loyer[2024] - 1) * 100, 1),
            "serie_loyer": [round(float(v), 1) for v in d.ipc_loyer.values],
        })
    periods = sorted(q.ref.unique())
    labels = {"01": "T1", "04": "T2", "07": "T3", "10": "T4"}
    out = {"periodes": [f"{p[:4]} {labels[p[5:]]}" for p in periods], "dernier": latest, "il_y_a_un_an": year_ago,
           "villes": cities, "provinces": provinces}
    (SITE_DATA / "carte.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    geo = ROOT / "data" / "ref" / "canada_provinces.geojson"
    (SITE_DATA / "canada_provinces.geojson").write_bytes(geo.read_bytes())

    mtl = next(x for x in cities if x["id"] == 7)
    qc = next(x for x in provinces if x["code"] == "QC")
    ranked = sorted([p for p in provinces if p["code"] != "CA"], key=lambda p: -p["hausse_loyer_2025"])
    return {
        "mtl_demande_dernier": mtl["demande"], "mtl_paye_dernier": mtl["paye"], "mtl_ecart_dernier": mtl["ecart"],
        "mtl_ecart_pct_dernier": mtl["ecart_pct"], "mtl_var_demande": mtl["var_demande"], "mtl_var_paye": mtl["var_paye"],
        "periode_derniere": out["periodes"][-1], "periode_il_y_a_un_an": out["periodes"][0],
        "qc_hausse_loyer_ipc": qc["hausse_loyer"], "qc_hausse_reelle_ipc": qc["hausse_reelle"],
        "qc_hausse_loyer_2025": qc["hausse_loyer_2025"],
        "qc_rang_hausse_2025": [p["code"] for p in ranked].index("QC") + 1,
    }


if __name__ == "__main__":
    raw = load()
    validate(*raw)
    TURNOVER = load_turnover()
    tables, deflator = transform(*raw)
    k = insights(tables, deflator)
    tv = TURNOVER.set_index(["indicateur", "year"]).valeur
    avg25 = int(tables["fait_loyers_montreal"].query("unit_id == '2ch' and year == 2025").loyer_nominal.iloc[0])
    k.update({
        "loyer_reloues_2ch_2025": int(tv["loyer_moyen_reloues_2ch", 2025]),
        "prime_relocation_2025": int(tv["loyer_moyen_reloues_2ch", 2025]) - avg25,
        "prime_relocation_pct_2025": round((tv["loyer_moyen_reloues_2ch", 2025] / avg25 - 1) * 100, 1),
        "hausse_reloues_2025": float(tv["hausse_loyer_reloues_2ch", 2025]),
        "hausse_non_reloues_2025": float(tv["hausse_loyer_non_reloues_2ch", 2025]),
        "hausse_meme_echantillon_2025": float(tv["hausse_loyer_meme_echantillon_2ch", 2025]),
        "inoccupation_3plus_2025": float(tv["taux_inoccupation_3plus", 2025]),
    })
    k.update(build_map())
    export(tables, k)
    print(json.dumps(k, ensure_ascii=False, indent=2))
