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
