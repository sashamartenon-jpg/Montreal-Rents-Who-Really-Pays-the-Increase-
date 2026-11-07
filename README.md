# Loyers à Montréal, 1992-2026

**La question : à Montréal, qui paie vraiment la hausse des loyers ?**
Réponse courte : ceux qui déménagent. Au 2ᵉ trimestre 2026, un 2 chambres affiché coûte 460 $ de plus par mois que le loyer payé par les locataires déjà en place.

**Site :** `https://sashamartenon-jpg.github.io/Montreal-Rents-Who-Really-Pays-the-Increase-/` · Projet d'intelligence d'affaires

## Constats

1. **Depuis 2019, la hausse a changé de régime.** Après inflation, le loyer moyen d'un 2 chambres a monté de 27 % de 2019 à 2025, contre 14 % de 1992 à 2019. Un test de Chow, calculé pour chaque année de 1997 à 2021, place la rupture en 2019. La p-value classique vaut 6 × 10⁻¹⁰. Corrigée par 20 000 simulations, qui tiennent compte de l'autocorrélation et de la recherche de l'année, elle vaut 0,037.
2. **Montréal a connu la plus forte hausse des six grandes villes depuis 2019** (+57 %). Elle n'est plus la moins chère : Québec l'est depuis 2020.
3. **Déménager coûte cher.** En 2025, la SCHL mesure une hausse de 17,2 % pour un logement reloué, contre 6,0 % pour un locataire en place. Au 2ᵉ trimestre 2026, l'écart entre le loyer affiché et le loyer payé atteint 460 $ par mois à Montréal (+34 %). C'est le 4ᵉ plus fort des 16 régions où les deux loyers sont publiés.
4. **La moitié de la hausse brute de 2025 (14,5 %) vient de la composition du parc.** Sur les mêmes logements, la hausse est de 7,2 %.
5. **Le Québec est la province où l'IPC du loyer a le plus monté en 2025** (+7,8 %). Sur 2019-2025, il n'est que 4ᵉ.

## Outils et ce qu'ils démontrent

| Couche | Outil | Fichiers |
|---|---|---|
| Acquisition et préparation | Chaîne de construction automatisée : extraction des tableaux officiels (API WDS), contrôles qualité, tables propres | `src/fetch_statcan.py`, `src/pipeline.py` |
| Modélisation | MCD (Merise) confronté à la base, MLD généré depuis la base | `src/modeles.py`, `docs/assets/sql/` |
| Base de données | SQL : 12 tables (6 faits, 6 dimensions, 3ᵉ forme normale), clés primaires composées, clés étrangères, contraintes CHECK, 5 vues, dictionnaire contrôlé | `sql/schema/`, `data/ref/dictionnaire.csv` |
| Requêtes analytiques | SQL (SQLite) : 12 requêtes classées par niveau (débutant → avancé) : contrôle qualité, LAG, ROW_NUMBER, RANK, PARTITION BY, moyennes mobiles, CTE, requêtes sur des vues | `sql/*.sql`, `src/build_db.py` |
| Statistique | Test de Chow avec recherche de la rupture et p-value corrigée par 20 000 simulations (résidus AR(1)) ; calculé par la chaîne de construction | `src/rupture.py` |
| Classeur | Excel sans macro : carte du Canada et carte des villes en graphiques Excel, tableau de bord, scénarios (NPM), simulateur, feuille « Mode d'emploi » (chaque fonction, du simple SOMME.SI.ENS aux séries à NA(), et les équivalents 365). Aucune cellule vide ni erreur visible | `docs/assets/modele_loyers_montreal.xlsx`, `src/build_excel.py`, `src/geo.py` |
| Visualisation et diffusion | Site de 4 pages (HTML, CSS, JavaScript, D3.js, sql.js) : carte animée, console SQL, animations au défilement. Accessibilité vérifiée (axe-core : 0 violation WCAG 2.1 AA sur les 4 pages, clair et sombre), navigation clavier, animations coupées avec `prefers-reduced-motion` | `src/index.template.html`, `src/pages/` → `docs/` |

## Contrôles automatiques

La construction s'arrête dans chacun des cas suivants :
- une table contient des doublons, des valeurs hors bornes ou une province inattendue ;
- une clé étrangère est orpheline ;
- le dictionnaire ne décrit pas exactement chaque colonne de la base (nom et type) ;
- le MCD ne correspond plus aux tables ;
- une des 12 requêtes SQL ne redonne pas le chiffre de référence du projet, ou deux requêtes se contredisent ;
- un tableau source du classeur Excel contient une cellule vide.

## Structure

```
data/raw/        extractions officielles (Statistique Canada, SCHL) et coordonnées des villes
data/ref/        contours des provinces (Natural Earth, via sane-topojson, MIT), dictionnaire de données
data/clean/      tables propres
sql/schema/      création des tables et des vues
sql/             12 requêtes commentées
src/             fetch_statcan · pipeline · build_db · postgres · modeles · build_excel (+ geo) · render_excel · build_site (+ rupture)
src/pages/       pages Carte, Excel, SQL ; code commun et animations
docs/            site publié par GitHub Pages, dont assets/base_loyers_montreal.zip (base, modèles, requêtes)
guides/          publication, post LinkedIn
```

## Reproduire

```bash
pip install pandas numpy scipy openpyxl matplotlib playwright pglast
python src/fetch_statcan.py   # vérifie data/raw contre les tableaux officiels (--mettre-a-jour pour les remplacer)
python src/pipeline.py
python src/build_db.py
python src/postgres.py        # version PostgreSQL du schéma, des vues et des données (validée par pglast)
python src/modeles.py         # MCD, MLD et paquet de la base
python src/build_excel.py
python src/render_excel.py    # captures des feuilles (LibreOffice requis)
python src/build_site.py https://sashamartenon-jpg.github.io/Montreal-Rents-Who-Really-Pays-the-Increase-
```

## Sources

- Statistique Canada, [34-10-0133-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3410013301) : loyers moyens de la SCHL (immeubles de 3 logements et plus). Montréal 2 chambres : vecteur v3824161.
- Statistique Canada, [34-10-0127-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3410012701) : taux d'inoccupation.
- Statistique Canada, [18-10-0005-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1810000501) : IPC (Montréal ; loyer et ensemble par province).
- Statistique Canada, [46-10-0092-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=4610009201) : loyers demandés et payés (estimations expérimentales).
- SCHL, [Rapport sur le marché locatif 2025](https://www.cmhc-schl.gc.ca/fr/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres) : logements reloués, hausse à échantillon constant.
- Contexte réglementaire : [Gouvernement du Québec, calcul de l'ajustement des loyers en 2026](https://www.quebec.ca/nouvelles/actualites/details/le-calcul-de-lajustement-des-loyers-en-2026-68053) ; [Éducaloi, section G du bail](https://educaloi.qc.ca/actualites-juridiques/loyer-paye-par-lancien-locataire-vous-avez-le-droit-de-savoir).

Données sous Licence du gouvernement ouvert – Canada. Extraction : 4 novembre 2026.

## Limites

- Champ de la SCHL : immeubles locatifs privés de 3 logements et plus. Le logement social et les condos loués sont exclus.
- L'effet de composition est déduit, il n'est pas mesuré directement.
- Les loyers demandés et payés sont des estimations expérimentales. Le loyer payé n'est publié que pour 16 régions sur 42.
- Le test de Chow confirme une cassure, pas sa cause. Son seuil simulé dépend du modèle AR(1).
- « Grande ville » et « Région métropolitaine » viennent de deux référentiels aux identifiants différents. Une table de correspondance reste à faire.
- Les scénarios servent à raisonner ; ce ne sont pas des prévisions.

## Méthode de travail

Le code a été écrit avec l'aide de Claude (assistant d'IA). Les choix d'analyse, la vérification des sources et l'interprétation sont les miens.

## Licence

Code : MIT. Données : Licence du gouvernement ouvert – Canada.
