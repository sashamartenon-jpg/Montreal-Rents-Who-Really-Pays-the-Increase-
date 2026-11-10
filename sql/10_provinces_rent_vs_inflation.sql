-- Provinces : hausse des loyers (IPC du loyer) en 2025 et depuis 2019, comparée à l'inflation
-- Niveau : Intermédiaire
WITH b AS (
  SELECT i.code, p.nom AS province,
         MAX(CASE WHEN i.annee = 2019 THEN i.ipc_loyer END)    AS loyer_2019,
         MAX(CASE WHEN i.annee = 2024 THEN i.ipc_loyer END)    AS loyer_2024,
         MAX(CASE WHEN i.annee = 2025 THEN i.ipc_loyer END)    AS loyer_2025,
         MAX(CASE WHEN i.annee = 2019 THEN i.ipc_ensemble END) AS ens_2019,
         MAX(CASE WHEN i.annee = 2025 THEN i.ipc_ensemble END) AS ens_2025
  FROM ipc_provinces i
  JOIN dim_province p ON p.code = i.code
  WHERE p.niveau = 'province'
  GROUP BY i.code, p.nom
)
SELECT RANK() OVER (ORDER BY loyer_2025 / loyer_2024 DESC)                     AS rang_2025,
       province,
       ROUND(100.0 * (loyer_2025 / loyer_2024 - 1), 1)                         AS hausse_2025_pct,
       ROUND(100.0 * (loyer_2025 / loyer_2019 - 1), 1)                         AS hausse_2019_2025_pct,
       ROUND(100.0 * ((loyer_2025 / loyer_2019) / (ens_2025 / ens_2019) - 1), 1) AS hausse_reelle_pct
FROM b
ORDER BY rang_2025;
