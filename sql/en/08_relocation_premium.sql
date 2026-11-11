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
