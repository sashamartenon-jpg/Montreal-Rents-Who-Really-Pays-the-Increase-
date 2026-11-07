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
