-- The analytical queries of the "Montreal Rents" project, from beginner to advanced level.
-- STEP 2 OF 2: run AFTER rents_database_sqlite_en.sql, on the same database (SQLite 3.25+).
-- Each query starts with its title and its level.
-- Sources: Statistics Canada and CMHC, Open Government Licence – Canada.

-- ===================================================================== 01_quality_check.sql
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


-- ===================================================================== 02_change_by_unit_type.sql
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


-- ===================================================================== 03_moving_average.sql
-- Smoothed trend: 3-year moving average of the annual increase (two-bedroom, Montreal)
-- Level: Advanced
WITH v AS (
  SELECT year, rent,
         100.0 * rent / LAG(rent) OVER (ORDER BY year) - 100 AS change_pct
  FROM fact_rent
  WHERE geo_id = 'Montreal' AND unit_id = '2br'
),
m AS (
  SELECT year, rent, change_pct,
         AVG(change_pct) OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3
  FROM v
)
SELECT year, rent, ROUND(change_pct, 1) AS change_pct, ROUND(ma3, 1) AS moving_avg_3yr
FROM m
WHERE year >= 2015
ORDER BY year;


-- ===================================================================== 04_real_rent.sql
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


-- ===================================================================== 05_pace_by_period.sql
-- Real increase and compound annual growth rate, 1992-2019 vs 2019-2025 (two-bedroom)
-- Level: Intermediate
WITH real_series AS (
  SELECT f.year, f.rent * (SELECT cpi FROM cpi WHERE year = 2025 AND geo_id = 'Montreal') / i.cpi AS real_rent
  FROM fact_rent f JOIN cpi i ON i.year = f.year AND i.geo_id = f.geo_id
  WHERE f.geo_id = 'Montreal' AND f.unit_id = '2br'
),
periods(start_year, end_year) AS (VALUES (1992, 2019), (2019, 2025))
SELECT p.start_year || '-' || p.end_year                                AS period,
       ROUND(100.0 * (b.real_rent / a.real_rent - 1), 1)                AS real_increase_pct,
       ROUND(100.0 * (POWER(b.real_rent / a.real_rent,
                            1.0 / (p.end_year - p.start_year)) - 1), 2) AS annual_pace_pct
FROM periods p
JOIN real_series a ON a.year = p.start_year
JOIN real_series b ON b.year = p.end_year;


-- ===================================================================== 06_city_ranking.sql
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


-- ===================================================================== 07_montreal_rank_by_year.sql
-- Is Montreal still the cheapest? Rank and relative level each year (RANK and MAX ... PARTITION BY)
-- Level: Advanced
WITH r AS (
  SELECT year, geo_id, rent,
         RANK() OVER (PARTITION BY year ORDER BY rent)               AS cheapest_rank,
         ROUND(100.0 * rent / MAX(rent) OVER (PARTITION BY year), 1) AS pct_of_most_expensive
  FROM fact_rent
  WHERE unit_id = '2br'
)
SELECT year, rent, cheapest_rank, pct_of_most_expensive
FROM r
WHERE geo_id = 'Montreal' AND year IN (1995, 2005, 2015, 2019, 2023, 2024, 2025)
ORDER BY year;


-- ===================================================================== 08_relocation_premium.sql
-- Gap between the rent of a re-let two-bedroom (CMHC) and the average rent of all tenants
-- Level: Beginner
SELECT r.year,
       f.rent                                   AS avg_rent_all,
       CAST(r.value AS INTEGER)                 AS avg_rent_relet,
       CAST(r.value - f.rent AS INTEGER)        AS monthly_gap,
       ROUND(100.0 * (r.value / f.rent - 1), 1) AS gap_pct,
       CAST((r.value - f.rent) * 12 AS INTEGER) AS annual_gap
FROM cmhc_turnover r
JOIN fact_rent f ON f.year = r.year AND f.geo_id = r.geo_id AND f.unit_id = '2br'
WHERE r.indicator = 'avg_rent_relet_2br' AND r.geo_id = 'Montreal'
ORDER BY r.year;


-- ===================================================================== 09_asking_vs_paid.sql
-- Asking rent vs rent paid: latest available quarter for each metro area (ROW_NUMBER per group)
-- Level: Advanced
WITH latest AS (
  SELECT geo_id, estimate, period, rent,
         ROW_NUMBER() OVER (PARTITION BY geo_id, estimate ORDER BY period DESC) AS rn
  FROM fact_rent_quarterly
  WHERE rent IS NOT NULL
),
by_area AS (
  SELECT geo_id,
         MAX(period)                                 AS period,
         MAX(CASE WHEN estimate = 'A' THEN rent END) AS asking,
         MAX(CASE WHEN estimate = 'P' THEN rent END) AS paid
  FROM latest
  WHERE rn = 1
  GROUP BY geo_id
)
SELECT RANK() OVER (ORDER BY asking / paid DESC) AS ranking,
       r.name, r.province, p.period,
       CAST(p.asking AS INTEGER)                 AS asking,
       CAST(p.paid AS INTEGER)                   AS paid,
       CAST(p.asking - p.paid AS INTEGER)        AS gap,
       ROUND(100.0 * (p.asking / p.paid - 1), 1) AS gap_pct
FROM by_area p
JOIN dim_metro_area r ON r.geo_id = p.geo_id
WHERE p.asking IS NOT NULL AND p.paid IS NOT NULL
ORDER BY ranking;


-- ===================================================================== 10_provinces_rent_vs_inflation.sql
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


-- ===================================================================== 11_vacancy_vs_rent.sql
-- Years when vacancy rose AND rent went up by more than 5% (Montreal, two-bedroom)
-- Level: Intermediate
WITH s AS (
  SELECT f.year, f.rent, v.rate,
         LAG(f.rent) OVER (ORDER BY f.year) AS prev_rent,
         LAG(v.rate)  OVER (ORDER BY f.year) AS prev_rate
  FROM fact_rent f
  JOIN fact_vacancy v ON v.year = f.year AND v.geo_id = f.geo_id
  WHERE f.geo_id = 'Montreal' AND f.unit_id = '2br'
)
SELECT year,
       prev_rate || ' -> ' || rate                    AS vacancy_pct,
       ROUND(100.0 * (1.0 * rent / prev_rent - 1), 1) AS rent_increase_pct
FROM s
WHERE rate > prev_rate AND 1.0 * rent / prev_rent - 1 > 0.05
ORDER BY year;


-- ===================================================================== 12_quebec_views.sql
-- Query on the views: Quebec metro areas, asking / paid gap and provincial rent increase in 2025
-- Level: Intermediate
SELECT e.name,
       CAST(e.asking AS INTEGER)                 AS asking,
       CAST(e.paid AS INTEGER)                   AS paid,
       ROUND(100.0 * (e.asking / e.paid - 1), 1) AS gap_pct,
       p.rent_increase_pct                       AS qc_rent_cpi_increase_2025
FROM v_asking_paid_gap e
JOIN v_cpi_provinces_change p ON p.code = e.province AND p.year = 2025
WHERE e.province = 'QC'
ORDER BY gap_pct DESC NULLS LAST;


