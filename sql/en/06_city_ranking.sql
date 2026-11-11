-- Ranking of six large cities by two-bedroom rent increase, 2019 -> 2025
-- Level: Intermediate
WITH h AS (
  SELECT g.label_en AS city,
         MAX(CASE WHEN f.year = 2019 THEN f.rent END) AS rent_2019,
         MAX(CASE WHEN f.year = 2025 THEN f.rent END) AS rent_2025
  FROM fact_rent f JOIN dim_city g ON g.geo_id = f.geo_id
  WHERE f.unit_id = '2br'
  GROUP BY g.label_en
)
SELECT RANK() OVER (ORDER BY 1.0 * rent_2025 / rent_2019 DESC) AS ranking,
       city, rent_2019, rent_2025,
       ROUND(100.0 * (1.0 * rent_2025 / rent_2019 - 1), 1)     AS increase_pct
FROM h
ORDER BY ranking;
