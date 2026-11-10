-- Tendance lissée : moyenne mobile sur 3 ans de la hausse annuelle (2 chambres, Montréal)
-- Niveau : Avancé
-- EN: Smoothed trend: 3-year moving average of the annual increase (two-bedroom, Montreal) · Level: Advanced
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
