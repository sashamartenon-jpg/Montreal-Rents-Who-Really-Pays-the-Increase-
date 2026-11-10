-- =====================================================================
-- Vues analytiques : la logique métier vit dans la base, pas dans chaque requête
-- =====================================================================

-- Loyers de Montréal en dollars constants de la dernière année disponible
CREATE VIEW v_loyer_reel AS
WITH ref AS (SELECT annee AS annee_ref, ipc AS ipc_ref FROM ipc WHERE geo_id = 'Montreal' ORDER BY annee DESC LIMIT 1)
SELECT f.annee, f.unit_id, l.libelle_fr AS logement, f.loyer AS loyer_nominal,
       ROUND(f.loyer * r.ipc_ref / i.ipc, 0) AS loyer_reel, r.annee_ref
FROM fait_loyer f
JOIN dim_logement l ON l.unit_id = f.unit_id
JOIN ipc i          ON i.annee = f.annee AND i.geo_id = f.geo_id
CROSS JOIN ref r
WHERE f.geo_id = 'Montreal';

-- Variation annuelle de chaque série (ville × type de logement)
CREATE VIEW v_variation_annuelle AS
SELECT annee, geo_id, unit_id, loyer,
       LAG(loyer) OVER w                                      AS loyer_prec,
       ROUND(100.0 * (loyer - LAG(loyer) OVER w) / LAG(loyer) OVER w, 1) AS variation_pct
FROM fait_loyer
WINDOW w AS (PARTITION BY geo_id, unit_id ORDER BY annee);

-- Dernier trimestre publié de chaque série (région × estimation)
CREATE VIEW v_dernier_trimestre AS
SELECT geo_id, estimation, periode, loyer, cote
FROM (
  SELECT t.*, ROW_NUMBER() OVER (PARTITION BY geo_id, estimation ORDER BY periode DESC) AS rn
  FROM fait_loyer_trimestriel t
  WHERE loyer IS NOT NULL
)
WHERE rn = 1;

-- Écart entre loyer demandé et loyer payé, par région
CREATE VIEW v_ecart_demande_paye AS
SELECT r.geo_id, r.nom, r.province,
       MAX(CASE WHEN d.estimation = 'A' THEN d.loyer END) AS demande,
       MAX(CASE WHEN d.estimation = 'P' THEN d.loyer END) AS paye,
       MAX(CASE WHEN d.estimation = 'A' THEN d.periode END) AS periode
FROM v_dernier_trimestre d
JOIN dim_rmr r ON r.geo_id = d.geo_id
GROUP BY r.geo_id, r.nom, r.province;

-- Hausse des loyers (IPC du loyer) par province et par année
CREATE VIEW v_ipc_provinces_variation AS
SELECT i.annee, i.code, p.nom AS province, i.ipc_loyer, i.ipc_ensemble,
       ROUND(100.0 * (i.ipc_loyer / LAG(i.ipc_loyer) OVER w - 1), 1)       AS hausse_loyer_pct,
       ROUND(100.0 * (i.ipc_ensemble / LAG(i.ipc_ensemble) OVER w - 1), 1) AS inflation_pct
FROM ipc_provinces i
JOIN dim_province p ON p.code = i.code
WINDOW w AS (PARTITION BY i.code ORDER BY i.annee);
