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
