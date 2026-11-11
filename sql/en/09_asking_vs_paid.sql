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
