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
