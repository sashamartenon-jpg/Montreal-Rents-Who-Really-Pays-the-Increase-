#!/usr/bin/env python3
"""
Évaluateur de loyer : situe automatiquement un loyer montréalais par rapport au marché.

Ce que fait le programme, pour un logement donné (loyer, type, année de début du bail) :
  1. le compare au loyer moyen SCHL de 2025 pour ce type de logement ;
  2. mesure la hausse du marché depuis le début du bail, et ce qu'il en reste après inflation ;
  3. pour un 2 chambres, calcule le potentiel de relocation : l'écart entre le loyer actuel
     et le loyer demandé dans les annonces (le revenu supplémentaire possible à chaque départ) ;
  4. si le revenu du ménage est fourni, calcule le taux d'effort (seuil SCHL : 30 %).

Deux modes :
  un logement   python3 evalue_loyer.py --loyer 1450 --type 2ch --annee-bail 2021 --revenu 60000
  un fichier    python3 evalue_loyer.py --fichier annonces_exemple.csv
                (colonnes : id,loyer,type,annee_bail ; évalue chaque ligne puis résume le portefeuille,
                 comme pour la liste de logements d'une agence immobilière)

Options : --json (sortie machine), --donnees DOSSIER (emplacement des CSV de données).
Aucune dépendance : Python 3.9+ et sa bibliothèque standard.

Données (incluses dans le téléchargement, extraites le 4 novembre 2026) :
  Statistique Canada 34-10-0133-01 et 18-10-0005-01 ; 46-10-0092-01 (estimations expérimentales) ;
  SCHL, Rapport sur le marché locatif 2025. Licence du gouvernement ouvert – Canada.
Limites : moyennes de la RMR de Montréal (immeubles de 3 logements et plus), pas de détail par
quartier ni par état du logement. Le programme situe un loyer ; il ne fixe pas un prix.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

ANNEE_REF = 2025          # dernière enquête SCHL (octobre 2025)
SEUIL_MARCHE = 0.05       # à ±5 % de la moyenne : « dans le marché »
SEUIL_EFFORT = 0.30       # norme SCHL d'abordabilité
TYPES = {"studio": "Studio", "1ch": "1 chambre", "2ch": "2 chambres", "3ch": "3 chambres"}


def _simplifie(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte.lower().strip()).encode("ascii", "ignore").decode()
    return t.replace("-", " ").replace("_", " ")


def normalise_type(texte: str) -> str:
    """Accepte « 2ch », « 2 chambres », « Studio », « 3 1/2 »… et renvoie l'identifiant interne."""
    t = _simplifie(texte)
    alias = {"studio": "studio", "1 1/2": "studio", "2 1/2": "studio",
             "1ch": "1ch", "1 chambre": "1ch", "1 chambres": "1ch", "3 1/2": "1ch",
             "2ch": "2ch", "2 chambres": "2ch", "4 1/2": "2ch",
             "3ch": "3ch", "3 chambres": "3ch", "3 chambres et plus": "3ch", "5 1/2": "3ch"}
    if t in alias:
        return alias[t]
    raise ValueError(f"type de logement inconnu : « {texte} » (attendu : studio, 1ch, 2ch ou 3ch)")


class Marche:
    """Les repères du marché montréalais, lus une fois dans les fichiers de données."""

    def __init__(self, dossier: Path):
        lire = lambda nom: list(csv.DictReader((dossier / nom).open(encoding="utf-8")))
        self.loyers = {(int(r["year"]), r["unit_id"]): float(r["loyer_nominal"]) for r in lire("fait_loyers_montreal.csv")}
        self.ipc = {int(r["year"]): float(r["ipc_2002_100"]) for r in lire("ipc_montreal.csv")}
        schl = {(int(r["year"]), r["indicateur"]): float(r["valeur"]) for r in lire("schl_roulement.csv")}
        self.loyer_reloue_2ch = schl[(ANNEE_REF, "loyer_moyen_reloues_2ch")]
        self.hausse_en_place = schl[(ANNEE_REF, "hausse_loyer_non_reloues_2ch")]
        trim = [r for r in lire("fait_loyer_trimestriel.csv") if r["geo_id"] == "7" and r["loyer"]]
        derniere = max(r["periode"] for r in trim)
        q = {"01": 1, "04": 2, "07": 3, "10": 4}[derniere[5:]]
        self.periode = f"{q}e trimestre {derniere[:4]}"
        par_est = {r["estimation"]: float(r["loyer"]) for r in trim if r["periode"] == derniere}
        self.demande_2ch, self.paye_2ch = par_est["A"], par_est["P"]
        self.annees = sorted({a for a, _ in self.loyers})

    def moyenne(self, annee: int, unit: str) -> float:
        return self.loyers[(annee, unit)]


def evalue(m: Marche, loyer: float, unit: str, annee_bail: int, revenu: float | None = None) -> dict:
    """Évalue un logement et renvoie un dictionnaire de résultats (toutes les valeurs sont dérivées)."""
    if loyer <= 0:
        raise ValueError(f"loyer invalide : {loyer}")
    if not (m.annees[0] <= annee_bail <= ANNEE_REF):
        raise ValueError(f"année de bail hors période couverte ({m.annees[0]}-{ANNEE_REF}) : {annee_bail}")
    moyenne = m.moyenne(ANNEE_REF, unit)
    ecart_pct = loyer / moyenne - 1
    position = ("dans le marché" if abs(ecart_pct) <= SEUIL_MARCHE
                else "sous le marché" if ecart_pct < 0 else "au-dessus du marché")
    hausse = moyenne / m.moyenne(annee_bail, unit) - 1
    inflation = m.ipc[ANNEE_REF] / m.ipc[annee_bail] - 1
    r = {
        "loyer": round(loyer, 2), "type": TYPES[unit], "annee_bail": annee_bail,
        "moyenne_2025": round(moyenne), "ecart_dollars": round(loyer - moyenne), "ecart_pct": round(ecart_pct * 100, 1),
        "position": position,
        "hausse_marche_depuis_bail_pct": round(hausse * 100, 1),
        "inflation_depuis_bail_pct": round(inflation * 100, 1),
        "hausse_reelle_marche_pct": round(((1 + hausse) / (1 + inflation) - 1) * 100, 1),
    }
    if unit == "2ch":
        r["loyer_demande_annonces"] = round(m.demande_2ch)
        r["potentiel_relocation_dollars"] = round(m.demande_2ch - loyer)
    if revenu and revenu > 0:
        effort = loyer * 12 / revenu
        r["taux_effort_pct"] = round(effort * 100, 1)
        r["abordable_seuil_30pct"] = effort <= SEUIL_EFFORT
    return r


def _fr(v, dec=0, signe=False) -> str:
    """1234.5 -> « 1 234,5 » (écriture française des nombres)."""
    s = f"{v:+,.{dec}f}" if signe else f"{v:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",")


def texte(r: dict, m: Marche) -> str:
    lignes = [f"Logement : {r['type']} à {_fr(r['loyer'])} $ par mois, bail commencé en {r['annee_bail']}",
              f"  Moyenne SCHL 2025 ({r['type']}) : {_fr(r['moyenne_2025'])} $  →  écart {_fr(r['ecart_dollars'], signe=True)} $ "
              f"({_fr(r['ecart_pct'], 1, True)} %) : {r['position'].upper()}",
              f"  Depuis {r['annee_bail']}, le marché a monté de {_fr(r['hausse_marche_depuis_bail_pct'], 1, True)} % "
              f"(inflation {_fr(r['inflation_depuis_bail_pct'], 1, True)} %, hausse réelle {_fr(r['hausse_reelle_marche_pct'], 1, True)} %)"]
    if "potentiel_relocation_dollars" in r:
        lignes.append(f"  Annonces ({m.periode}) : {_fr(r['loyer_demande_annonces'])} $  →  "
                      f"potentiel de relocation {_fr(r['potentiel_relocation_dollars'], signe=True)} $ par mois")
    if "taux_effort_pct" in r:
        verdict = "sous le" if r["abordable_seuil_30pct"] else "au-dessus du"
        lignes.append(f"  Taux d'effort : {_fr(r['taux_effort_pct'], 1)} % du revenu, {verdict} seuil SCHL de 30 %")
    return "\n".join(lignes)


def evalue_fichier(m: Marche, chemin: Path) -> tuple[list[dict], dict]:
    """Évalue chaque ligne d'un fichier CSV (id,loyer,type,annee_bail[,revenu]) puis résume le portefeuille."""
    lignes = [l for l in chemin.read_text(encoding="utf-8-sig").splitlines() if l.strip() and not l.startswith("#")]
    resultats = []
    for i, row in enumerate(csv.DictReader(lignes), start=2):
        try:
            r = evalue(m, float(row["loyer"]), normalise_type(row["type"]), int(row["annee_bail"]),
                       float(row["revenu"]) if row.get("revenu") else None)
            r["id"] = row.get("id") or f"ligne {i}"
            resultats.append(r)
        except (KeyError, ValueError) as e:
            sys.exit(f"Erreur à la ligne {i} de {chemin.name} : {e}")
    n = len(resultats)
    potentiel = [r["potentiel_relocation_dollars"] for r in resultats if "potentiel_relocation_dollars" in r]
    ecarts = sorted(r["ecart_pct"] for r in resultats)
    synthese = {
        "logements": n,
        "sous_le_marche": sum(r["position"] == "sous le marché" for r in resultats),
        "dans_le_marche": sum(r["position"] == "dans le marché" for r in resultats),
        "au_dessus_du_marche": sum(r["position"] == "au-dessus du marché" for r in resultats),
        "ecart_median_pct": round(ecarts[n // 2] if n % 2 else (ecarts[n // 2 - 1] + ecarts[n // 2]) / 2, 1),
        "potentiel_relocation_total_dollars_par_mois": round(sum(p for p in potentiel if p > 0)) if potentiel else None,
        "note": "potentiel de relocation calculé pour les 2 chambres seulement, seul type couvert par les annonces agrégées",
    }
    return resultats, synthese


def trouve_donnees(option: str | None) -> Path:
    ici = Path(__file__).resolve().parent
    candidats = ([Path(option)] if option else []) + [ici / "donnees", ici.parent / "data" / "clean", ici]
    for c in candidats:
        if (c / "fait_loyers_montreal.csv").exists():
            return c
    sys.exit("Fichiers de données introuvables. Place le dossier « donnees » à côté du script, ou indique --donnees CHEMIN.")


def main(argv=None):
    p = argparse.ArgumentParser(description="Situe un loyer montréalais par rapport au marché (données SCHL et Statistique Canada).")
    p.add_argument("--loyer", type=float, help="loyer mensuel actuel, en dollars")
    p.add_argument("--type", help="studio, 1ch, 2ch ou 3ch (ou « 2 chambres », « 4 1/2 »…)")
    p.add_argument("--annee-bail", type=int, help="année de début du bail")
    p.add_argument("--revenu", type=float, help="revenu annuel brut du ménage (facultatif)")
    p.add_argument("--fichier", type=Path, help="fichier CSV de logements à évaluer (id,loyer,type,annee_bail[,revenu])")
    p.add_argument("--json", action="store_true", help="sortie en JSON plutôt qu'en texte")
    p.add_argument("--donnees", help="dossier des fichiers de données")
    a = p.parse_args(argv)
    m = Marche(trouve_donnees(a.donnees))

    if a.fichier:
        resultats, synthese = evalue_fichier(m, a.fichier)
        if a.json:
            print(json.dumps({"logements": resultats, "synthese": synthese}, ensure_ascii=False, indent=2))
        else:
            for r in resultats:
                print(f"\n[{r['id']}]")
                print(texte(r, m))
            s = synthese
            print(f"\n{'=' * 72}\nSynthèse du portefeuille : {s['logements']} logements · "
                  f"{s['sous_le_marche']} sous le marché, {s['dans_le_marche']} dans le marché, {s['au_dessus_du_marche']} au-dessus")
            print(f"Écart médian à la moyenne SCHL : {_fr(s['ecart_median_pct'], 1, True)} %")
            if s["potentiel_relocation_total_dollars_par_mois"] is not None:
                print(f"Potentiel de relocation (2 ch. sous le prix des annonces) : {_fr(s['potentiel_relocation_total_dollars_par_mois'], signe=True)} $ par mois")
            print(s["note"].capitalize() + ".")
    elif a.loyer and a.type and a.annee_bail:
        try:
            r = evalue(m, a.loyer, normalise_type(a.type), a.annee_bail, a.revenu)
        except ValueError as e:
            sys.exit(f"Erreur : {e}")
        print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else texte(r, m))
    else:
        p.error("indique soit --loyer, --type et --annee-bail, soit --fichier")


if __name__ == "__main__":
    main()
