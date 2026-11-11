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
