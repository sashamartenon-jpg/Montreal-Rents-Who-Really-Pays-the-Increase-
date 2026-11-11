-- Provinces: rent increase (rent CPI) in 2025 and since 2019, compared with inflation
-- Level: Intermediate
WITH b AS (
  SELECT i.code, p.name                                        AS province,
         MAX(CASE WHEN i.year = 2019 THEN i.rent_cpi END)      AS rent_2019,
         MAX(CASE WHEN i.year = 2024 THEN i.rent_cpi END)      AS rent_2024,
         MAX(CASE WHEN i.year = 2025 THEN i.rent_cpi END)      AS rent_2025,
         MAX(CASE WHEN i.year = 2019 THEN i.all_items_cpi END) AS all_items_2019,
         MAX(CASE WHEN i.year = 2025 THEN i.all_items_cpi END) AS all_items_2025
  FROM cpi_provinces i
  JOIN dim_province p ON p.code = i.code
  WHERE p.level = 'province'
  GROUP BY i.code, p.name
)
SELECT RANK() OVER (ORDER BY rent_2025 / rent_2024 DESC)                                   AS ranking_2025,
       province,
       ROUND(100.0 * (rent_2025 / rent_2024 - 1), 1)                                       AS increase_2025_pct,
       ROUND(100.0 * (rent_2025 / rent_2019 - 1), 1)                                       AS increase_2019_2025_pct,
       ROUND(100.0 * ((rent_2025 / rent_2019) / (all_items_2025 / all_items_2019) - 1), 1) AS real_increase_pct
FROM b
ORDER BY ranking_2025;
