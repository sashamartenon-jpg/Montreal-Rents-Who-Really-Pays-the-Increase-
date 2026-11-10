-- Loyer réel (dollars de 2025) : jointure avec l'IPC de Montréal
-- Niveau : Débutant
-- EN: Real rent (2025 dollars): join with the Montreal CPI · Level: Beginner
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
