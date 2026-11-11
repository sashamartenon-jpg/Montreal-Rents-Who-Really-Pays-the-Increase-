-- =====================================================================
-- Analytical views: the business logic lives in the database, not in each query
-- =====================================================================

-- Montreal rents in constant dollars of the latest available year
CREATE VIEW v_real_rent AS
WITH ref AS (SELECT year AS ref_year, cpi AS ref_cpi FROM cpi WHERE geo_id = 'Montreal' ORDER BY year DESC LIMIT 1)
SELECT f.year, f.unit_id, l.label_en AS unit_type, f.rent AS nominal_rent,
       ROUND(f.rent * r.ref_cpi / i.cpi, 0) AS real_rent, r.ref_year
FROM fact_rent f
JOIN dim_unit_type l ON l.unit_id = f.unit_id
JOIN cpi i          ON i.year = f.year AND i.geo_id = f.geo_id
CROSS JOIN ref r
WHERE f.geo_id = 'Montreal';

-- Year-over-year change of each series (city × unit type)
CREATE VIEW v_annual_change AS
SELECT year, geo_id, unit_id, rent,
       LAG(rent) OVER w                                               AS prev_rent,
       ROUND(100.0 * (rent - LAG(rent) OVER w) / LAG(rent) OVER w, 1) AS change_pct
FROM fact_rent
WINDOW w AS (PARTITION BY geo_id, unit_id ORDER BY year);

-- Latest published quarter of each series (metro area × estimate)
CREATE VIEW v_latest_quarter AS
SELECT geo_id, estimate, period, rent, grade
FROM (
  SELECT t.*, ROW_NUMBER() OVER (PARTITION BY geo_id, estimate ORDER BY period DESC) AS rn
  FROM fact_rent_quarterly t
  WHERE rent IS NOT NULL
)
WHERE rn = 1;

-- Gap between asking rent and rent paid, by metro area
CREATE VIEW v_asking_paid_gap AS
SELECT r.geo_id, r.name, r.province,
       MAX(CASE WHEN d.estimate = 'A' THEN d.rent END) AS asking,
       MAX(CASE WHEN d.estimate = 'P' THEN d.rent END) AS paid,
       MAX(CASE WHEN d.estimate = 'A' THEN d.period END) AS period
FROM v_latest_quarter d
JOIN dim_metro_area r ON r.geo_id = d.geo_id
GROUP BY r.geo_id, r.name, r.province;

-- Rent increase (rent CPI) by province and year
CREATE VIEW v_cpi_provinces_change AS
SELECT i.year, i.code, p.name AS province, i.rent_cpi, i.all_items_cpi,
       ROUND(100.0 * (i.rent_cpi / LAG(i.rent_cpi) OVER w - 1), 1)           AS rent_increase_pct,
       ROUND(100.0 * (i.all_items_cpi / LAG(i.all_items_cpi) OVER w - 1), 1) AS inflation_pct
FROM cpi_provinces i
JOIN dim_province p ON p.code = i.code
WINDOW w AS (PARTITION BY i.code ORDER BY i.year);
