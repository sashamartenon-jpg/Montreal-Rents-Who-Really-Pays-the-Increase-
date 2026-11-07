-- Écart entre le loyer d'un 2 chambres reloué (SCHL) et le loyer moyen de tous les locataires
-- Niveau : Débutant
SELECT r.annee,
       f.loyer                                         AS loyer_moyen_tous,
       CAST(r.valeur AS INTEGER)                       AS loyer_moyen_reloues,
       CAST(r.valeur - f.loyer AS INTEGER)             AS ecart_mensuel,
       ROUND(100.0 * (r.valeur / f.loyer - 1), 1)      AS ecart_pct,
       CAST((r.valeur - f.loyer) * 12 AS INTEGER)      AS ecart_annuel
FROM schl_roulement r
JOIN fait_loyer f ON f.annee = r.annee AND f.geo_id = r.geo_id AND f.unit_id = '2ch'
WHERE r.indicateur = 'loyer_moyen_reloues_2ch' AND r.geo_id = 'Montreal'
ORDER BY r.annee;
