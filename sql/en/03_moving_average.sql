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
