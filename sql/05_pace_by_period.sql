-- Hausse réelle et taux de croissance annuel composé, 1992-2019 vs 2019-2025 (2 chambres)
-- Niveau : Intermédiaire
-- EN: Real increase and compound annual growth rate, 1992-2019 vs 2019-2025 (two-bedroom) · Level: Intermediate
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
