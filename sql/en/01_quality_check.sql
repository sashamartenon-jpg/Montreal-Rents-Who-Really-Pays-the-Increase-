-- Quality check: coverage, missing values and reliability grades of each fact table
-- Level: Beginner
SELECT 'fact_rent' AS source, COUNT(*) AS row_count, MIN(year) || '-' || MAX(year) AS period,
       COUNT(DISTINCT geo_id || unit_id) AS series,
       SUM(CASE WHEN rent IS NULL THEN 1 ELSE 0 END) AS missing, 0 AS grade_e
FROM fact_rent
UNION ALL
SELECT 'fact_vacancy', COUNT(*), MIN(year) || '-' || MAX(year), COUNT(DISTINCT geo_id),
       SUM(CASE WHEN rate IS NULL THEN 1 ELSE 0 END), 0
FROM fact_vacancy
UNION ALL
SELECT 'fact_rent_quarterly', COUNT(*), MIN(period) || ' / ' || MAX(period), COUNT(DISTINCT geo_id || estimate),
       SUM(CASE WHEN rent IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN grade = 'E' THEN 1 ELSE 0 END)
FROM fact_rent_quarterly
UNION ALL
SELECT 'cpi_provinces', COUNT(*), MIN(year) || '-' || MAX(year), COUNT(DISTINCT code),
       SUM(CASE WHEN rent_cpi IS NULL THEN 1 ELSE 0 END), 0
FROM cpi_provinces;
