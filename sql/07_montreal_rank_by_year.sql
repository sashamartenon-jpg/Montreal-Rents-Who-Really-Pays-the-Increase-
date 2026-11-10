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
