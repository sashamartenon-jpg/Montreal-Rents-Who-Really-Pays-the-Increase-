-- Les requêtes analytiques du projet « Loyers à Montréal », du niveau débutant au niveau avancé.
-- ÉTAPE 2 SUR 2 : à exécuter APRÈS rents_database_sqlite.sql, sur la même base (SQLite 3.25+). Le niveau est indiqué en tête de chacune.
-- Sources : Statistique Canada et SCHL, Licence du gouvernement ouvert – Canada.

-- ===================================================================== 01_quality_check.sql
-- Contrôle qualité : couverture, valeurs manquantes et cotes de fiabilité de chaque table de faits
-- Niveau : Débutant
SELECT 'fait_loyer' AS source, COUNT(*) AS lignes, MIN(annee) || '-' || MAX(annee) AS periode,
       COUNT(DISTINCT geo_id || unit_id) AS series,
       SUM(CASE WHEN loyer IS NULL THEN 1 ELSE 0 END) AS manquantes, 0 AS cote_E
FROM fait_loyer
UNION ALL
SELECT 'fait_inoccupation', COUNT(*), MIN(annee) || '-' || MAX(annee), COUNT(DISTINCT geo_id),
       SUM(CASE WHEN taux IS NULL THEN 1 ELSE 0 END), 0
FROM fait_inoccupation
UNION ALL
SELECT 'fait_loyer_trimestriel', COUNT(*), MIN(periode) || ' à ' || MAX(periode), COUNT(DISTINCT geo_id || estimation),
       SUM(CASE WHEN loyer IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN cote = 'E' THEN 1 ELSE 0 END)
FROM fait_loyer_trimestriel
UNION ALL
SELECT 'ipc_provinces', COUNT(*), MIN(annee) || '-' || MAX(annee), COUNT(DISTINCT code),
       SUM(CASE WHEN ipc_loyer IS NULL THEN 1 ELSE 0 END), 0
FROM ipc_provinces;


-- ===================================================================== 02_change_by_unit_type.sql
-- Variation annuelle du loyer à Montréal, pour chaque type de logement (LAG avec PARTITION BY)
-- Niveau : Intermédiaire
WITH v AS (
  SELECT f.annee, l.libelle_fr AS logement, l.chambres, f.loyer,
         ROUND(100.0 * (f.loyer - LAG(f.loyer) OVER (PARTITION BY f.unit_id ORDER BY f.annee))
               / LAG(f.loyer) OVER (PARTITION BY f.unit_id ORDER BY f.annee), 1) AS variation_pct
  FROM fait_loyer f
  JOIN dim_logement l ON l.unit_id = f.unit_id
  WHERE f.geo_id = 'Montreal'
)
SELECT annee, logement, loyer, variation_pct
FROM v
WHERE annee >= 2023
ORDER BY chambres, annee;


-- ===================================================================== 03_moving_average.sql
-- Tendance lissée : moyenne mobile sur 3 ans de la hausse annuelle (2 chambres, Montréal)
-- Niveau : Avancé
WITH v AS (
  SELECT annee, loyer,
         100.0 * loyer / LAG(loyer) OVER (ORDER BY annee) - 100 AS variation_pct
  FROM fait_loyer
  WHERE geo_id = 'Montreal' AND unit_id = '2ch'
),
m AS (
  SELECT annee, loyer, variation_pct,
         AVG(variation_pct) OVER (ORDER BY annee ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS mm3
  FROM v
)
SELECT annee, loyer, ROUND(variation_pct, 1) AS variation_pct, ROUND(mm3, 1) AS moyenne_mobile_3_ans
FROM m
WHERE annee >= 2015
ORDER BY annee;


-- ===================================================================== 04_real_rent.sql
-- Loyer réel (dollars de 2025) : jointure avec l'IPC de Montréal
-- Niveau : Débutant
WITH base AS (SELECT ipc AS ipc_2025 FROM ipc WHERE annee = 2025 AND geo_id = 'Montreal')
SELECT f.annee,
       l.libelle_fr                                AS logement,
       f.loyer                                     AS loyer_nominal,
       ROUND(f.loyer * b.ipc_2025 / i.ipc, 0)      AS loyer_reel_2025
FROM fait_loyer f
JOIN ipc i           ON i.annee = f.annee AND i.geo_id = f.geo_id
JOIN dim_logement l  ON l.unit_id = f.unit_id
CROSS JOIN base b
WHERE f.geo_id = 'Montreal' AND f.annee IN (1992, 2019, 2025)
ORDER BY l.chambres, f.annee;


-- ===================================================================== 05_pace_by_period.sql
-- Hausse réelle et taux de croissance annuel composé, 1992-2019 vs 2019-2025 (2 chambres)
-- Niveau : Intermédiaire
WITH reel AS (
  SELECT f.annee, f.loyer * (SELECT ipc FROM ipc WHERE annee = 2025 AND geo_id = 'Montreal') / i.ipc AS loyer_reel
  FROM fait_loyer f JOIN ipc i ON i.annee = f.annee AND i.geo_id = f.geo_id
  WHERE f.geo_id = 'Montreal' AND f.unit_id = '2ch'
),
periodes(debut, fin) AS (VALUES (1992, 2019), (2019, 2025))
SELECT p.debut || '-' || p.fin                                        AS periode,
       ROUND(100.0 * (b.loyer_reel / a.loyer_reel - 1), 1)            AS hausse_reelle_pct,
       ROUND(100.0 * (POWER(b.loyer_reel / a.loyer_reel,
                            1.0 / (p.fin - p.debut)) - 1), 2)         AS rythme_annuel_pct
FROM periodes p
JOIN reel a ON a.annee = p.debut
JOIN reel b ON b.annee = p.fin;


-- ===================================================================== 06_city_ranking.sql
-- Classement des six grandes villes selon la hausse du 2 chambres, 2019 -> 2025
-- Niveau : Intermédiaire
WITH h AS (
  SELECT g.libelle_fr AS ville,
         MAX(CASE WHEN f.annee = 2019 THEN f.loyer END) AS loyer_2019,
         MAX(CASE WHEN f.annee = 2025 THEN f.loyer END) AS loyer_2025
  FROM fait_loyer f JOIN dim_geo g ON g.geo_id = f.geo_id
  WHERE f.unit_id = '2ch'
  GROUP BY g.libelle_fr
)
SELECT RANK() OVER (ORDER BY 1.0 * loyer_2025 / loyer_2019 DESC)  AS rang,
       ville, loyer_2019, loyer_2025,
       ROUND(100.0 * (1.0 * loyer_2025 / loyer_2019 - 1), 1)       AS hausse_pct
FROM h
ORDER BY rang;


-- ===================================================================== 07_montreal_rank_by_year.sql
-- Montréal reste-t-elle la moins chère ? Rang et niveau relatif chaque année (RANK et MAX ... PARTITION BY)
-- Niveau : Avancé
WITH r AS (
  SELECT annee, geo_id, loyer,
         RANK() OVER (PARTITION BY annee ORDER BY loyer)                 AS rang_moins_cher,
         ROUND(100.0 * loyer / MAX(loyer) OVER (PARTITION BY annee), 1) AS pct_du_plus_cher
  FROM fait_loyer
  WHERE unit_id = '2ch'
)
SELECT annee, loyer, rang_moins_cher, pct_du_plus_cher
FROM r
WHERE geo_id = 'Montreal' AND annee IN (1995, 2005, 2015, 2019, 2023, 2024, 2025)
ORDER BY annee;


-- ===================================================================== 08_relocation_premium.sql
-- Écart entre le loyer d'un 2 chambres reloué (SCHL) et le loyer moyen de tous les locataires
-- Niveau : Débutant
SELECT r.annee,
       f.loyer                                         AS loyer_moyen_tous,
       CAST(r.valeur AS INTEGER)                       AS loyer_moyen_reloues,
       CAST(r.valeur - f.loyer AS INTEGER)             AS ecart_mensuel,
       ROUND(100.0 * (r.valeur / f.loyer - 1), 1)      AS ecart_pct,
       CAST((r.valeur - f.loyer) * 12 AS INTEGER)      AS ecart_annuel
FROM schl_roulement r
JOIN fait_loyer f ON f.annee = r.annee AND f.geo_id = r.geo_id AND f.unit_id = '2ch'
WHERE r.indicateur = 'loyer_moyen_reloues_2ch' AND r.geo_id = 'Montreal'
ORDER BY r.annee;


-- ===================================================================== 09_asking_vs_paid.sql
-- Loyer demandé vs loyer payé : dernier trimestre disponible de chaque région (ROW_NUMBER par groupe)
-- Niveau : Avancé
WITH dernier AS (
  SELECT geo_id, estimation, periode, loyer,
         ROW_NUMBER() OVER (PARTITION BY geo_id, estimation ORDER BY periode DESC) AS rn
  FROM fait_loyer_trimestriel
  WHERE loyer IS NOT NULL
),
par_region AS (
  SELECT geo_id,
         MAX(periode)                                      AS periode,
         MAX(CASE WHEN estimation = 'A' THEN loyer END)    AS demande,
         MAX(CASE WHEN estimation = 'P' THEN loyer END)    AS paye
  FROM dernier
  WHERE rn = 1
  GROUP BY geo_id
)
SELECT RANK() OVER (ORDER BY demande / paye DESC)          AS rang,
       r.nom, r.province, p.periode,
       CAST(p.demande AS INTEGER)                          AS demande,
       CAST(p.paye AS INTEGER)                             AS paye,
       CAST(p.demande - p.paye AS INTEGER)                 AS ecart,
       ROUND(100.0 * (p.demande / p.paye - 1), 1)          AS ecart_pct
FROM par_region p
JOIN dim_rmr r ON r.geo_id = p.geo_id
WHERE p.demande IS NOT NULL AND p.paye IS NOT NULL
ORDER BY rang;


-- ===================================================================== 10_provinces_rent_vs_inflation.sql
-- Provinces : hausse des loyers (IPC du loyer) en 2025 et depuis 2019, comparée à l'inflation
-- Niveau : Intermédiaire
WITH b AS (
  SELECT i.code, p.nom AS province,
         MAX(CASE WHEN i.annee = 2019 THEN i.ipc_loyer END)    AS loyer_2019,
         MAX(CASE WHEN i.annee = 2024 THEN i.ipc_loyer END)    AS loyer_2024,
         MAX(CASE WHEN i.annee = 2025 THEN i.ipc_loyer END)    AS loyer_2025,
         MAX(CASE WHEN i.annee = 2019 THEN i.ipc_ensemble END) AS ens_2019,
         MAX(CASE WHEN i.annee = 2025 THEN i.ipc_ensemble END) AS ens_2025
  FROM ipc_provinces i
  JOIN dim_province p ON p.code = i.code
  WHERE p.niveau = 'province'
  GROUP BY i.code, p.nom
)
SELECT RANK() OVER (ORDER BY loyer_2025 / loyer_2024 DESC)                     AS rang_2025,
       province,
       ROUND(100.0 * (loyer_2025 / loyer_2024 - 1), 1)                         AS hausse_2025_pct,
       ROUND(100.0 * (loyer_2025 / loyer_2019 - 1), 1)                         AS hausse_2019_2025_pct,
       ROUND(100.0 * ((loyer_2025 / loyer_2019) / (ens_2025 / ens_2019) - 1), 1) AS hausse_reelle_pct
FROM b
ORDER BY rang_2025;


-- ===================================================================== 11_vacancy_vs_rent.sql
-- Années où l'inoccupation a augmenté ET le loyer a monté de plus de 5 % (Montréal, 2 chambres)
-- Niveau : Avancé
WITH s AS (
  SELECT f.annee, f.loyer, v.taux,
         LAG(f.loyer) OVER (ORDER BY f.annee) AS loyer_prec,
         LAG(v.taux)  OVER (ORDER BY f.annee) AS taux_prec
  FROM fait_loyer f
  JOIN fait_inoccupation v ON v.annee = f.annee AND v.geo_id = f.geo_id
  WHERE f.geo_id = 'Montreal' AND f.unit_id = '2ch'
)
SELECT annee,
       taux_prec || ' -> ' || taux                          AS inoccupation_pct,
       ROUND(100.0 * (1.0 * loyer / loyer_prec - 1), 1)     AS hausse_loyer_pct
FROM s
WHERE taux > taux_prec AND 1.0 * loyer / loyer_prec - 1 > 0.05
ORDER BY annee;


-- ===================================================================== 12_quebec_views.sql
-- Requête sur les vues : régions du Québec, écart demandé / payé et hausse provinciale des loyers en 2025
-- Niveau : Intermédiaire
SELECT e.nom,
       CAST(e.demande AS INTEGER)                  AS demande,
       CAST(e.paye AS INTEGER)                     AS paye,
       ROUND(100.0 * (e.demande / e.paye - 1), 1)  AS ecart_pct,
       p.hausse_loyer_pct                          AS hausse_ipc_loyer_qc_2025
FROM v_ecart_demande_paye e
JOIN v_ipc_provinces_variation p ON p.code = e.province AND p.annee = 2025
WHERE e.province = 'QC'
ORDER BY ecart_pct DESC NULLS LAST;

