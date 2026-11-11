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
