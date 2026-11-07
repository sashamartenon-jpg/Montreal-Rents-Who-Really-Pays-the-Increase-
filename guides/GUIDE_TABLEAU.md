# Guide : construire la version Tableau Public

Fichier de données : `tableau/loyers_long.csv` (une ligne par année × ville × type de logement).

| Colonne | Contenu |
|---|---|
| `annee` | 1992 à 2025 |
| `ville` | Montréal, Québec, Ottawa-Gatineau, Toronto, Calgary, Vancouver |
| `type_logement` | Studio, 1 chambre, 2 chambres, 3 chambres (les autres villes : 2 chambres seulement) |
| `loyer_nominal` | loyer moyen d'octobre, $ par mois |
| `loyer_reel_2025` | loyer en dollars de 2025 (Montréal seulement) |
| `var_annuelle_pct` | variation sur un an, en % |
| `taux_inoccupation_pct` | taux d'inoccupation de la ville cette année-là |
| `serie` | « Montréal par taille » ou « Comparaison RMR » |

## Étapes (environ 3 heures)

1. **Connexion.** Tableau Public > Fichier texte > `loyers_long.csv`. Vérifie que `annee` est en nombre entier (dimension discrète) et les loyers en mesures.
2. **Feuille 1, « Loyer réel ».** Filtre `serie` = Montréal par taille. Colonnes : `annee` (continue). Lignes : `loyer_reel_2025`. Couleur : `type_logement`. Ajoute une bande de référence de 2019 à 2025.
3. **Feuille 2, « Six villes ».** Filtre `serie` = Comparaison RMR. Crée le champ calculé `Indice 2019` avec une expression LOD (niveau de détail) :
   ```
   SUM([loyer_nominal]) / SUM({ FIXED [ville] : SUM(IF [annee] = 2019 THEN [loyer_nominal] END) }) * 100
   ```
   Lignes : `Indice 2019`. Couleur : `ville` (Montréal en bleu, le reste en gris).
4. **Feuille 3, « Inoccupation vs hausse ».** Nuage de points : colonnes `taux_inoccupation_pct`, lignes `var_annuelle_pct`, filtre ville = Montréal, étiquette `annee`. Ajoute une courbe de tendance et lis son R² : c'est un bon sujet d'entrevue (la relation est faible, et 2025 sort du nuage).
5. **Paramètre « Année de début »** (entier 1992–2024) et champ calculé de hausse depuis cette année, pour reproduire la logique du simulateur.
6. **Tableau de bord.** Taille « Automatique », les trois feuilles, un titre qui énonce le constat (pas « Dashboard »), la source en bas : « Statistique Canada, tableaux 34-10-0133-01, 34-10-0127-01, 18-10-0005-01 ».
7. **Publication.** Enregistre sur Tableau Public, copie l'URL de la vue (format `https://public.tableau.com/views/...`).
8. **Diffusion.** Le site n'intègre pas de vue Tableau : ajoute l'URL de la vue dans ton post LinkedIn ou dans le README, à côté du lien du site.

Test de réussite : la vue s'ouvre en navigation privée, et le chiffre +57 % (Montréal, 2019 à 2025) apparaît identique dans Tableau, Excel et sur le site.
