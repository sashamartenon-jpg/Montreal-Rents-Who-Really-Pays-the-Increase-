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
