-- Requête sur les vues : régions du Québec, écart demandé / payé et hausse provinciale des loyers en 2025
-- Niveau : Intermédiaire
-- EN: Query on the views: Quebec metro areas, asking / paid gap and provincial rent increase in 2025 · Level: Intermediate
SELECT e.nom,
       CAST(e.demande AS INTEGER)                  AS demande,
       CAST(e.paye AS INTEGER)                     AS paye,
       ROUND(100.0 * (e.demande / e.paye - 1), 1)  AS ecart_pct,
       p.hausse_loyer_pct                          AS hausse_ipc_loyer_qc_2025
FROM v_ecart_demande_paye e
JOIN v_ipc_provinces_variation p ON p.code = e.province AND p.annee = 2025
WHERE e.province = 'QC'
ORDER BY ecart_pct DESC NULLS LAST;
