-- Real rent (2025 dollars): join with the Montreal CPI
-- Level: Beginner
WITH base AS (SELECT cpi AS cpi_2025 FROM cpi WHERE year = 2025 AND geo_id = 'Montreal')
SELECT f.year,
       l.label_en                            AS unit_type,
       f.rent                                AS nominal_rent,
       ROUND(f.rent * b.cpi_2025 / i.cpi, 0) AS real_rent_2025
FROM fact_rent f
JOIN cpi i           ON i.year = f.year AND i.geo_id = f.geo_id
JOIN dim_unit_type l  ON l.unit_id = f.unit_id
CROSS JOIN base b
WHERE f.geo_id = 'Montreal' AND f.year IN (1992, 2019, 2025)
ORDER BY l.bedrooms, f.year;
