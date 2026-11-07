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
