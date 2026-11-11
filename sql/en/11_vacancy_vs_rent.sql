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
