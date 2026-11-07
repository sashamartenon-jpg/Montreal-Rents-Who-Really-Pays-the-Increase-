# Guide : mettre le site en ligne et le publier sur LinkedIn

Durée totale : environ 1 h 30. Aucun terminal nécessaire : tout se fait dans le navigateur.

## 1. Relire avant de publier (20 min)

- [ ] Lance `python src/fetch_statcan.py` sur ton ordinateur (ou dans Colab). Il doit afficher « Aucun écart ». C'est la vérification finale des données.
- [ ] Ouvre `docs/index.html` dans ton navigateur (double-clic) et lis toutes les pages.
- [ ] Ouvre `docs/assets/modele_loyers_montreal.xlsx` dans Excel. Sur « Carte provinces », mets l'année à 2024 : l'Alberta doit passer en tête et les bulles changer de couleur. Choisis l'Ontario : sa bulle passe en rose. Sur « Carte villes », choisis Toronto : le point rose se déplace. Aucune cellule ne doit afficher #N/A ou #VALEUR.
- [ ] Ouvre `docs/assets/base_loyers_montreal.zip` : la base s'ouvre dans DB Browser for SQLite, les images mcd.png et mld.png sont lisibles.
- [ ] Dézippe `docs/assets/programme_evaluateur.zip` et lance `python3 evalue_loyer.py --fichier annonces_exemple.csv` : la synthèse des 8 logements fictifs doit s'afficher.
- [ ] Accessibilité : parcours la page d'accueil uniquement au clavier (Tab) ; le lien « Aller au contenu » doit apparaître en premier, et chaque bouton montrer un contour rose.
- [ ] Recoupe trois chiffres avec la source : va sur le [tableau 34-10-0133-01](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=3410013301), choisis Montréal, deux chambres, et compare 2019 (855 $), 2024 (1 176 $) et 2025 (1 346 $).
- [ ] Prépare une réponse d'une minute à : « Pourquoi 14,5 % sur ton site et 7,2 % dans le rapport de la SCHL ? »
- [ ] Le site ne porte aucune identité (ni nom, ni école, ni bio) : ton profil LinkedIn et le post portent ce rôle. Vérifie que la mention d'aide d'une IA figure dans le post et dans le README (section « Transparence »).

## 2. Créer le dépôt GitHub (15 min)

1. Crée un compte sur github.com si besoin. Choisis un nom de compte professionnel (ex. `sashamartenon`).
2. Bouton **New repository** : nom `loyers-montreal`, visibilité **Public**, sans README (tu as le tien).
3. Sur la page du dépôt vide : **uploading an existing file**. Glisse le contenu du dossier `loyers-montreal` (les dossiers `data`, `docs`, `guides`, `notebooks`, `sql`, `src` et `README.md`). Ne mets pas le fichier de préparation d'entretien dans le dépôt. Clique **Commit changes**.

## 3. Activer GitHub Pages (5 min)

1. **Settings** > **Pages**.
2. Source : **Deploy from a branch**. Branche : `main`, dossier : `/docs`. **Save**.
3. Attends 1 à 2 minutes. L'adresse apparaît : `https://TON-COMPTE.github.io/loyers-montreal/`.

Test : l'adresse s'ouvre sur ton téléphone, les 5 pages (Analyse, Carte, Excel, SQL, Python) s'affichent, les blocs apparaissent au défilement, les boutons de téléchargement (classeur, base) fonctionnent, et la console de la page SQL indique « SQLite prêt ».

## 4. Reconstruire avec l'adresse publique (5 min)

Le site ne contient pas de boutons LinkedIn ou GitHub : ces liens vivent sur ton profil et dans ton post, et le dépôt GitHub est lui-même l'adresse du code. Reconstruis la page avec l'adresse publique (elle rend l'image d'aperçu LinkedIn absolue) :

```bash
python src/build_site.py https://TON-COMPTE.github.io/loyers-montreal
```

Sans Python local : ouvre un Colab, téléverse `src/build_site.py`, `src/index.template.html` et `docs/data/data.json` en respectant les dossiers, exécute `!python src/build_site.py https://...`, puis téléverse le nouveau `docs/index.html` sur GitHub. Si tu préfères, demande-moi de le faire : envoie-moi tes deux liens.

## 5. Vérifier l'aperçu LinkedIn (5 min)

1. Va sur le [Post Inspector de LinkedIn](https://www.linkedin.com/post-inspector/).
2. Colle l'adresse du site. L'aperçu doit montrer l'image sombre « Les loyers ont monté plus en 6 ans qu'en 27 ».
3. Si l'image manque : vérifie que `og:image` contient l'adresse complète (`https://...`), puis relance l'inspection.

## 6. Ajouter le suivi des visites (10 min, facultatif)

GoatCounter (gratuit pour un usage personnel) : crée un compte, puis ajoute avant `</html>` dans `docs/index.html` la ligne de script qu'il te donne. Partage le lien avec `?utm_source=linkedin` pour distinguer les visites venues du post.

## 7. Publier le post (15 min)

Voir `guides/POST_LINKEDIN.md`. Ensuite, le même jour :

- Profil > **Sélection** (Featured) > Ajouter un lien > adresse du site.
- Profil > **Projets** > « Loyers à Montréal, 1992-2025 », avec Python, Excel, D3.js, Tableau comme compétences.
- Réponds à chaque commentaire dans les 24 heures.

## 8. Mise à jour annuelle

Quand la SCHL publie l'enquête d'octobre 2026 (probablement en décembre 2026, à confirmer) :
1. Ajoute l'année 2026 dans les fichiers de `data/raw/` (et l'IPC 2026 en janvier).
2. Relance les trois scripts.
3. Republie et fais un post « Les chiffres 2026 sont sortis : voici ce qui a changé ».
