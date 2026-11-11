-- Year-over-year rent change in Montreal, for each unit type (LAG with PARTITION BY)
-- Level: Intermediate
WITH v AS (
  SELECT f.year, l.label_en AS unit_type, l.bedrooms, f.rent,
         ROUND(100.0 * (f.rent - LAG(f.rent) OVER (PARTITION BY f.unit_id ORDER BY f.year))
               / LAG(f.rent) OVER (PARTITION BY f.unit_id ORDER BY f.year), 1) AS change_pct
  FROM fact_rent f
  JOIN dim_unit_type l ON l.unit_id = f.unit_id
  WHERE f.geo_id = 'Montreal'
)
SELECT year, unit_type, rent, change_pct
FROM v
WHERE year >= 2023
ORDER BY bedrooms, year;
