# Traductions de la version anglaise du classeur (XL_LANG=en).
# STRINGS : texte de cellule exact (après .upper() des étiquettes) ou chaîne entre
# guillemets dans une formule → traduction. Une clé absente = texte inchangé.
# SHEETS : noms d'onglets. FORMATS : formats numériques. Vérifié par le balayage
# anti-restes-français de la chaîne de construction.

SHEETS = {
    "Accueil": "Home",
    "Tableau de bord": "Dashboard",
    "Carte provinces": "Province map",
    "Carte villes": "City map",
    "Scénarios": "Scenarios",
    "Simulateur": "Simulator",
    "Mode d'emploi": "How-to",
    "Loyers Montréal": "Rents Montreal",
    "Séries annuelles": "Annual series",
    "IPC provinces": "CPI provinces",
    "Loyers trimestriels": "Quarterly rents",
    "SCHL": "CMHC",
    "Calculs": "Calculations",      # feuille masquée : références de formules, plages nommées et graphiques suivent
}

FORMATS = {
    '#,##0 "$"': '"$"#,##0',
    '+#,##0 "$";-#,##0 "$";0 "$"': '+"$"#,##0;-"$"#,##0;"$"0',
}

STRINGS = {
    # ---------- morceaux de formules
    " % pour les locataires en place": "% for sitting tenants",
    " ans": " yrs",
    " ans (": " yrs (",
    " pour l'indicateur sur un an": " for the one-year indicator",
    " sur 10 provinces": " of 10 provinces",
    " sur 16": " of 16",
    " à ": " to ",
    ", octobre ": ", October ",
    "Après inflation. De 1992 à 2019 : ": "After inflation. From 1992 to 2019: ",
    "Au-dessus du seuil": "Above the threshold",
    "Classe 1 : à partir de ": "Class 1: from ",
    "Classe 2 : à partir de ": "Class 2: from ",
    "Classe 3 : à partir de ": "Class 3: from ",
    "Classe 4 : à partir de ": "Class 4: from ",
    "Classe 5 : à partir de ": "Class 5: from ",
    "Croissance composée sur ": "Compound growth over ",
    "Demandé": "Asking",
    "Hausse 2019 → ": "Increase 2019 → ",
    "Hausse de ": "Increase from ",
    "Hausse réelle 2019 → ": "Real increase 2019 → ",
    "Hausse sur un an (": "One-year increase (",
    "L'année de début doit précéder l'année de fin.": "The start year must come before the end year.",
    "Non calculé": "Not computed",
    "Payé": "Paid",
    "Rang ": "Rank ",
    "Sous le seuil": "Below the threshold",
    "contre ": "vs ",
    "jamais": "never",
    "← Accueil": "← Home",
    # navigation (texte affiché des hyperliens = nom d'onglet traduit via SHEETS ci-dessus,
    # mais le libellé est aussi une chaîne entre guillemets)
    "Accueil": "Home",
    "Tableau de bord": "Dashboard",
    "Carte provinces": "Province map",
    "Carte villes": "City map",
    "Scénarios": "Scenarios",
    "Simulateur": "Simulator",
    "Mode d'emploi": "How-to",
    "Studio,1 chambre,2 chambres,3 chambres": "Studio,1 bedroom,2 bedrooms,3 bedrooms",
    "Choisis une année entre 1992 et 2024.": "Pick a year between 1992 and 2024.",
    "Choisis une année entre 1993 et 2025.": "Pick a year between 1993 and 2025.",
    "Choisis une année entre 2020 et 2025.": "Pick a year between 2020 and 2025.",
    "Choisis une année entre 1992 et 2025.": "Pick a year between 1992 and 2025.",

    # ---------- types de logement (données, listes et critères de formules)
    "1 chambre": "1 bedroom",
    "2 chambres": "2 bedrooms",
    "3 chambres": "3 bedrooms",

    # ---------- provinces et villes (valeurs de données affichées)
    "Alberta": "Alberta",
    "Colombie-Britannique": "British Columbia",
    "Île-du-Prince-Édouard": "Prince Edward Island",
    "Manitoba": "Manitoba",
    "Nouveau-Brunswick": "New Brunswick",
    "Nouvelle-Écosse": "Nova Scotia",
    "Ontario": "Ontario",
    "Québec": "Quebec",
    "Saskatchewan": "Saskatchewan",
    "Terre-Neuve-et-Labrador": "Newfoundland and Labrador",
    "Canada (référence)": "Canada (reference)",
    "Montréal": "Montreal",
    "Grand Sudbury": "Greater Sudbury",
    "Gatineau (Ottawa-Gatineau, partie québécoise)": "Gatineau (Ottawa-Gatineau, Quebec part)",

    # ---------- Accueil
    "À Montréal, qui paie vraiment la hausse des loyers ?": "In Montreal, who really pays for rising rents?",
    "Classeur d'analyse · Projet « Loyers à Montréal, 1992-2026 »": "Analysis workbook · Project “Montreal rents, 1992-2026”",
    "Réponse courte : ceux qui déménagent. Les quatre chiffres ci-dessous sont recalculés par les formules du classeur.":
        "Short answer: people who move. The four figures below are recomputed by the workbook's formulas.",
    "Par mois, 2 chambres à Montréal": "Per month, two-bedroom in Montreal",
    "HAUSSE 2025 : RELOUÉS / EN PLACE": "2025 INCREASE: RE-LET / SITTING",
    "HAUSSE RÉELLE D'UN 2 CH., 2019-2025": "REAL INCREASE, 2-BED, 2019-2025",
    "LOYER AU QUÉBEC EN 2025 (IPC)": "QUEBEC RENT IN 2025 (CPI)",
    "Explorer le classeur": "Explore the workbook",
    "Choisis une période et un type de logement : indicateurs et graphiques se recalculent.":
        "Pick a period and a unit type: indicators and charts recompute.",
    "La carte du Canada : hausse des loyers par province, par année, avec classement.":
        "The map of Canada: rent increases by province and year, with rankings.",
    "Les 16 régions où l'on connaît le loyer demandé et le loyer payé. Choisis une ville.":
        "The 16 metro areas where both the asking and the paid rent are known. Pick a city.",
    "Trois hypothèses jusqu'en 2030 et le délai pour que le loyer moyen rattrape les annonces.":
        "Three assumptions to 2030 and how long the average rent needs to catch up with listings.",
    "Compare un loyer à la moyenne du marché et au prix d'un logement reloué.":
        "Compare a rent to the market average and to the price of a re-let unit.",
    "Chaque fonction du classeur, de la plus simple à la plus avancée, et trois exercices.":
        "Every function in the workbook, from simplest to most advanced, plus three exercises.",
    "Méthode": "Method",
    "MÉTHODE": "METHOD",
    "• Cases jaunes : entrées. Texte bleu : donnée source. Vert : valeur lue dans une autre feuille. Noir : calcul. Aucune macro.":
        "• Yellow cells: inputs. Blue text: source data. Green: value read from another sheet. Black: calculation. No macros.",
    "• Chaque chiffre est recalculé ici par formules et vérifié contre la base SQL du projet à chaque construction.":
        "• Every figure is recomputed here by formulas and checked against the project's SQL database at every build.",
    "• Sources : Statistique Canada (34-10-0133-01, 18-10-0005-01, 46-10-0092-01) et SCHL, Rapport sur le marché locatif 2025.":
        "• Sources: Statistics Canada (34-10-0133-01, 18-10-0005-01, 46-10-0092-01) and CMHC, Rental Market Report 2025.",

    # ---------- Tableau de bord
    "Tableau de bord : loyers à Montréal, 1992-2025": "Dashboard: Montreal rents, 1992-2025",
    "Modifie les cases jaunes : les 4 indicateurs et les 4 graphiques se recalculent":
        "Edit the yellow cells: the 4 indicators and 4 charts recompute",
    "Année de début": "Start year",
    "Année de fin": "End year",
    "Logement": "Unit type",
    "LOYER MOYEN, ANNÉE DE FIN": "AVERAGE RENT, END YEAR",
    "HAUSSE RÉELLE (APRÈS INFLATION)": "REAL INCREASE (AFTER INFLATION)",
    "Hausse nominale": "Nominal increase",
    "RYTHME ANNUEL RÉEL": "REAL ANNUAL PACE",
    "PRIME DE RELOCATION 2025 (2 CH.)": "2025 RE-LET PREMIUM (2-BED)",
    "Loyer d'un 2 ch. reloué": "Rent of a re-let 2-bed",
    "Sources : Statistique Canada 34-10-0133-01, 18-10-0005-01 ; SCHL, Rapport sur le marché locatif 2025.":
        "Sources: Statistics Canada 34-10-0133-01, 18-10-0005-01; CMHC, Rental Market Report 2025.",

    # ---------- titres de graphiques
    "Loyer réel du type choisi (en couleur : période choisie)": "Real rent of the selected type (highlighted: selected period)",
    "Hausse du 2 chambres sur la période choisie": "Two-bedroom increase over the selected period",
    "Loyer par type de logement (dollars courants)": "Rent by unit type (current dollars)",
    "2 chambres : tous les locataires et logements reloués": "Two-bedroom: all tenants and re-let units",
    "IPC du loyer, base 2019 = 100": "Rent CPI, 2019 = 100",
    "Ville choisie : loyer demandé et loyer payé": "Selected city: asking rent and rent paid",
    "Loyer moyen d'un 2 chambres : historique et scénarios jusqu'en 2030": "Average two-bedroom rent: history and scenarios to 2030",
    "Ton loyer comparé au marché (2025)": "Your rent against the market (2025)",
    "Canada · une bulle par province, couleur selon la valeur (rose : province choisie)":
        "Canada · one bubble per province, coloured by value (pink: selected province)",
    "Québec, Ontario et Maritimes": "Quebec, Ontario and the Maritimes",
    "Prairies et Colombie-Britannique": "Prairies and British Columbia",

    # ---------- Carte provinces
    "Carte du Canada : où les loyers montent-ils le plus vite ?": "Map of Canada: where are rents rising fastest?",
    "Indice des prix du loyer par province · choisis l'indicateur, l'année et la province (cases jaunes)":
        "Rent price index by province · pick the indicator, year and province (yellow cells)",
    "Indicateur": "Indicator",
    "Année": "Year",
    "Province": "Province",
    "Hausse des loyers sur un an": "One-year rent increase",
    "Hausse des loyers depuis 2019": "Rent increase since 2019",
    "Hausse réelle depuis 2019 (après inflation)": "Real increase since 2019 (after inflation)",
    "CLASSEMENT DES PROVINCES": "PROVINCE RANKING",
    "Valeur": "Value",
    "Rang": "Rank",
    "Écart au Canada": "Gap to Canada",
    "PROVINCE CHOISIE": "SELECTED PROVINCE",
    "Valeur de l'indicateur": "Indicator value",
    "Rang sur 10 provinces": "Rank of 10 provinces",
    "LÉGENDE : QUINTILES DE L'INDICATEUR (UNE COULEUR = 2 PROVINCES)": "LEGEND: INDICATOR QUINTILES (ONE COLOUR = 2 PROVINCES)",
    "Contours : Natural Earth (domaine public), projection conique conforme de Lambert (paramètres de Statistique Canada), calculée par src/geo.py. Territoires : pas d'IPC provincial publié.":
        "Outlines: Natural Earth (public domain), Lambert conformal conic projection (Statistics Canada parameters), computed by src/geo.py. Territories: no provincial CPI published.",

    # ---------- Carte villes
    "Carte des villes : combien coûte un déménagement ?": "City map: what does moving cost?",
    "Écart entre loyer demandé et loyer payé (%)": "Gap between asking rent and rent paid (%)",
    "Loyer demandé (annonces)": "Asking rent (listings)",
    "Loyer payé (locataires en place)": "Rent paid (sitting tenants)",
    "Ville": "City",
    "VILLE CHOISIE": "SELECTED CITY",
    "Région": "Metro area",
    "Écart par mois": "Gap per month",
    "Écart en %": "Gap in %",
    "Rang pour l'indicateur": "Rank for the indicator",
    "LES 10 PREMIÈRES RÉGIONS": "TOP 10 METRO AREAS",
    "LÉGENDE : QUINTILES DE L'INDICATEUR": "LEGEND: INDICATOR QUINTILES",
    "REPÈRES DU MARCHÉ (CALCULÉS SUR LE TABLEAU SOURCE)": "MARKET BENCHMARKS (COMPUTED ON THE SOURCE TABLE)",
    "Loyer demandé le plus élevé": "Highest asking rent",
    "Loyer demandé le plus bas": "Lowest asking rent",
    "Positions : projection conique conforme de Lambert (src/geo.py). Contours : Natural Earth. Estimations expérimentales de Statistique Canada (46-10-0092-01).":
        "Positions: Lambert conformal conic projection (src/geo.py). Outlines: Natural Earth. Experimental estimates from Statistics Canada (46-10-0092-01).",

    # ---------- Scénarios
    "Scénarios : quand le loyer moyen rattrapera-t-il les annonces ?": "Scenarios: when will the average rent catch up with listings?",
    "Loyer moyen d'un 2 chambres à Montréal · trois hypothèses tirées des données · des scénarios pour raisonner, pas une prévision":
        "Average two-bedroom rent in Montreal · three assumptions drawn from the data · scenarios to reason with, not a forecast",
    "POINT DE DÉPART": "STARTING POINT",
    "Loyer moyen 2025, tous les locataires": "2025 average rent, all tenants",
    "HYPOTHÈSES DE CROISSANCE ANNUELLE": "ANNUAL GROWTH ASSUMPTIONS",
    "Scénario": "Scenario",
    "Taux tiré des données": "Rate drawn from the data",
    "Ajustement (points)": "Adjustment (points)",
    "Taux retenu": "Rate used",
    "Rattrape les annonces en": "Catches listings in",
    "Source du taux": "Source of the rate",
    "A · Tendance longue": "A · Long trend",
    "B · Locataires en place": "B · Sitting tenants",
    "C · Rythme récent": "C · Recent pace",
    "A · Tendance": "A · Trend",
    "B · En place": "B · Sitting",
    "C · Récent": "C · Recent",
    "Croissance annuelle composée 1992-2019": "Compound annual growth 1992-2019",
    "Croissance annuelle composée 2019-2025": "Compound annual growth 2019-2025",
    "Hausse 2025 des loyers non reloués (SCHL)": "2025 increase for non-re-let units (CMHC)",
    "Loyer moyen": "Average rent",
    "Historique": "History",
    "« Rattrape les annonces » : années pour que le loyer moyen atteigne le loyer affiché aujourd'hui (fonction NPM).":
        "“Catches listings”: years for the average rent to reach today's advertised rent (NPER function).",

    # ---------- Simulateur
    "Simulateur : ton loyer face au marché montréalais": "Simulator: your rent against the Montreal market",
    "Modifie uniquement les cellules jaunes ; tout le reste se recalcule, y compris le graphique":
        "Edit only the yellow cells; everything else recomputes, chart included",
    "ENTRÉES": "INPUTS",
    "Loyer mensuel actuel ($)": "Current monthly rent ($)",
    "Exemple : 1 250 $. Remplace par ton loyer.": "Example: $1,250. Replace with your rent.",
    "Type de logement": "Unit type",
    "Liste déroulante.": "Drop-down list.",
    "Année de début du bail": "Lease start year",
    "Entre 1992 et 2025.": "Between 1992 and 2025.",
    "Revenu annuel brut du ménage ($)": "Gross annual household income ($)",
    "Mets 0 pour ne pas calculer le taux d'effort.": "Enter 0 to skip the effort-ratio calculation.",
    "RÉSULTATS (DONNÉES D'OCTOBRE 2025)": "RESULTS (OCTOBER 2025 DATA)",
    "Loyer moyen SCHL, ce type, 2025": "CMHC average rent, this type, 2025",
    "Écart entre ton loyer et cette moyenne": "Gap between your rent and this average",
    "Hausse du loyer moyen depuis le début du bail": "Average-rent increase since the lease began",
    "Inflation (IPC Montréal) sur la même période": "Inflation (Montreal CPI) over the same period",
    "Hausse réelle du loyer moyen (au-delà de l'inflation)": "Real increase in the average rent (beyond inflation)",
    "Taux d'effort (loyer × 12 / revenu)": "Effort ratio (rent × 12 / income)",
    "Statut d'abordabilité (seuil SCHL : 30 % du revenu)": "Affordability status (CMHC threshold: 30% of income)",
    "Loyer moyen d'un 2 chambres reloué en 2025 (SCHL)": "Average rent of a re-let two-bedroom in 2025 (CMHC)",
    "Ce que coûterait un déménagement (2 ch. reloué − ton loyer)": "What moving would cost (re-let 2-bed − your rent)",
    "COMPARAISON": "COMPARISON",
    "Ton loyer": "Your rent",
    "Moyenne, tous locataires": "Average, all tenants",
    "2 ch. reloué (SCHL)": "Re-let 2-bed (CMHC)",
    "• Moyenne de la région métropolitaine, immeubles de 3 logements et plus, tous âges et tous quartiers.":
        "• Metro-area average, buildings with 3+ units, all ages and neighbourhoods.",
    "• La moyenne inclut les locataires de longue date : un logement à louer coûte en général plus cher.":
        "• The average includes long-time tenants: a unit up for rent usually costs more.",
    "• Le logement social et les condos loués ne sont pas couverts par l'enquête.":
        "• Social housing and rented condos are not covered by the survey.",
    "SCHL, Rapport sur le marché locatif 2025, figure 1. Publié pour les 2 chambres seulement.":
        "CMHC, Rental Market Report 2025, figure 1. Published for two-bedrooms only.",

    # ---------- Mode d'emploi
    "Mode d'emploi : les fonctions du classeur, de la plus simple à la plus avancée":
        "How-to: the workbook's functions, from simplest to most advanced",
    "Chaque formule est visible : clique sur une cellule pour la lire. Aucune macro, aucun code caché.":
        "Every formula is visible: click a cell to read it. No macros, no hidden code.",
    "LES FONCTIONS, PAR NIVEAU": "THE FUNCTIONS, BY LEVEL",
    "Niveau": "Level",
    "Fonction ou outil": "Function or tool",
    "Ce qu'elle fait ici": "What it does here",
    "Où la voir": "Where to see it",
    "Débutant": "Beginner",
    "Intermédiaire": "Intermediate",
    "Avancé": "Advanced",
    "SI + ET + SIERREUR": "IF + AND + IFERROR",
    "Teste une condition ou neutralise une erreur : le message si les années sont inversées, les points qu'une série affiche ou non.":
        "Tests a condition or neutralises an error: the message when the years are reversed, the points a series shows or hides.",
    "Liste déroulante": "Drop-down list",
    "Validation des données : une case jaune n'accepte qu'une année, un type de logement ou une ville de la liste.":
        "Data validation: a yellow cell only accepts a year, a unit type or a city from the list.",
    "Tableau de bord, Calculs": "Dashboard, Calculations sheet",
    "Tableau de bord, Cartes, Simulateur": "Dashboard, Maps, Simulator",
    "SOMME.SI.ENS": "SUMIFS",
    "SI.CONDITIONS": "IFS",
    "MAX.SI.ENS / MIN.SI.ENS": "MAXIFS / MINIFS",
    "INDEX + EQUIV": "INDEX + MATCH",
    "CHOISIR + EQUIV": "CHOOSE + MATCH",
    "RANG + INDEX/EQUIV": "RANK + INDEX/MATCH",
    "CENTILE": "PERCENTILE",
    "NPM (NPER)": "NPER",
    "LIEN_HYPERTEXTE": "HYPERLINK",
    "NA() dans les séries": "NA() in chart series",
    "Graphique en nuage de points": "Scatter chart",
    "Lit un loyer dans les tableaux sources selon plusieurs critères (année, type, trimestre…). La fonction la plus utilisée du classeur.":
        "Reads a rent from the source tables by several criteria (year, type, quarter…). The most used function in the workbook.",
    "Le statut d'abordabilité en une seule formule lisible, au lieu de SI imbriqués.":
        "The affordability status in one readable formula, instead of nested IFs.",
    "Le loyer demandé le plus élevé et le plus bas parmi les 16 régions, sans trier le tableau.":
        "The highest and lowest asking rents among the 16 metro areas, without sorting the table.",
    "Retrouve une valeur par sa position : la fiche de la ville choisie, le tri des classements.":
        "Finds a value by its position: the selected city's card, the sorted rankings.",
    "Bascule les cartes d'un indicateur à l'autre à partir d'une liste déroulante.":
        "Switches the maps from one indicator to another from a drop-down list.",
    "Trie les villes par hausse sans macro : RANG classe, INDEX/EQUIV reconstruit la liste triée.":
        "Sorts cities by increase without a macro: RANK orders, INDEX/MATCH rebuilds the sorted list.",
    "Découpe les valeurs en quintiles : les 5 classes de couleur des cartes.":
        "Cuts the values into quintiles: the maps' 5 colour classes.",
    "Le nombre d'années pour que le loyer moyen rattrape le prix des annonces, pour chaque scénario.":
        "How many years the average rent needs to catch up with listing prices, for each scenario.",
    "Les boutons de navigation entre les feuilles.": "The navigation buttons between sheets.",
    "Un point NA() n'est pas tracé : les classes de couleur des cartes et les périodes des courbes.":
        "An NA() point is not plotted: the maps' colour classes and the curves' periods.",
    "Les deux cartes : les contours projetés sont une série de lignes, chaque ville ou province une série de points.":
        "Both maps: projected outlines are a line series; each city or province is a point series.",
    "Partout · ex. Tableau de bord": "Everywhere · e.g. Dashboard",
    "Cartes, Tableau de bord": "Maps, Dashboard",
    "Carte villes, repères du marché": "City map, market benchmarks",
    "Carte provinces, Carte villes": "Province map, City map",
    "Calculs, légendes des cartes": "Calculations sheet, map legends",
    "Calculs (alimente les graphiques)": "Calculations sheet (feeds the charts)",
    "Accueil, bandeaux": "Home, banners",
    "Calculs (feuille masquée)": "Calculations (hidden sheet)",
    "ET LES FONCTIONS D'EXCEL 365 ?": "WHAT ABOUT EXCEL 365 FUNCTIONS?",
    "Avec Excel 365 : RECHERCHEX remplacerait les paires INDEX + EQUIV, LET nommerait les étapes des longues formules des scénarios,":
        "With Excel 365: XLOOKUP would replace the INDEX + MATCH pairs, LET would name the steps of the long scenario formulas,",
    "et FILTRE + TRIER remplaceraient le tri par RANG. Trois réécritures faciles : bonnes candidates pour une prochaine version.":
        "and FILTER + SORT would replace the RANK-based sorting. Three easy rewrites: good candidates for a next version.",
    "Le classeur n'utilise que des fonctions disponibles dans toutes les versions d'Excel depuis 2019, pour s'ouvrir partout sans erreur.":
        "The workbook only uses functions available in every version of Excel since 2019, so it opens everywhere without errors.",
    "TROIS EXERCICES POUR PRENDRE LE CLASSEUR EN MAIN": "THREE EXERCISES TO GET STARTED",
    "1.  Tableau de bord : mets la période 1992-2019, puis 2019-2025. Compare les deux rythmes annuels réels (+0,5 % contre +4,1 %).":
        "1.  Dashboard: set the period to 1992-2019, then 2019-2025. Compare the two real annual paces (+0.5% vs +4.1%).",
    "2.  Carte provinces : année 2024. Quelle province mène ? (Réponse : l'Alberta.) Repasse à 2025 : le Québec prend la tête.":
        "2.  Province map: year 2024. Which province leads? (Answer: Alberta.) Switch back to 2025: Quebec takes the lead.",
    "3.  Simulateur : entre ton propre loyer et ton année de bail, puis lis l'écart avec le marché et ton taux d'effort.":
        "3.  Simulator: enter your own rent and lease year, then read the gap to the market and your effort ratio.",
    "CONVENTIONS": "CONVENTIONS",
    "Cases jaunes : entrées modifiables (protégées par une validation des données). Texte bleu : données sources. Vert : valeur lue ailleurs. Noir : calcul.":
        "Yellow cells: editable inputs (guarded by data validation). Blue text: source data. Green: value read elsewhere. Black: calculation.",
    "Chaque bandeau de feuille cite sa source. Les données brutes sont dans les cinq derniers onglets, en tableaux Excel nommés.":
        "Each sheet banner cites its source. The raw data sits in the last five tabs, as named Excel tables.",
    "La feuille « Calculs » (masquée : clic droit sur un onglet → Afficher) contient les séries des graphiques ; ses NA() sont volontaires.":
        "The “Calculations” sheet (hidden: right-click a tab → Unhide) holds the chart series; its NA() values are intentional.",

    # ---------- feuilles de données (en-têtes et bandeaux)
    "Loyers Montréal": "Rents Montreal",
    "Séries annuelles": "Annual series",
    "IPC provinces": "CPI provinces",
    "Loyers trimestriels": "Quarterly rents",
    "Loyer moyen ($/mois)": "Average rent ($/month)",
    "Code de l'indicateur": "Indicator code",
    "Loyer moyen d'un 2 chambres reloué à un nouveau locataire": "Average rent of a 2-bedroom re-let to a new tenant",
    "Hausse du loyer des 2 chambres reloués": "Rent increase, re-let 2-bedroom units",
    "Hausse du loyer des 2 chambres non reloués (locataires en place)": "Rent increase, 2-bedroom units not re-let (sitting tenants)",
    "Hausse du loyer des 2 chambres à échantillon constant": "Rent increase, 2-bedroom units, fixed sample",
    "Taux d'inoccupation, immeubles de 3 logements et plus": "Vacancy rate, buildings with 3 or more units",
    "Une ligne": "One row",
    "Plages nommées": "Named ranges",
    "Texte bleu : donnée saisie depuis la source, sans formule": "Blue text: value entered from the source, no formula",
    "une année et un type de logement": "one year and one unit type",
    "une année (loyer d'un 2 chambres dans six villes, IPC de Montréal)": "one year (two-bedroom rent in six cities, Montreal CPI)",
    "une année et une province (ou le Canada)": "one year and one province (or Canada)",
    "un trimestre, une région et une estimation (loyer demandé ou payé)": "one quarter, one metro area and one estimate (asking or paid rent)",
    "une année et un indicateur du rapport": "one year and one indicator of the report",
    "IPC Montréal (2002 = 100)": "Montreal CPI (2002 = 100)",
    "Statistique Canada · 34-10-0133-01 : loyer moyen d'un 2 chambres, octobre · 18-10-0005-01 : IPC d'ensemble de Montréal, moyenne annuelle":
        "Statistics Canada · 34-10-0133-01: average two-bedroom rent, October · 18-10-0005-01: Montreal all-items CPI, annual average",
    "Statistique Canada 34-10-0133-01 · loyers moyens SCHL, immeubles de 3 logements et plus, octobre":
        "Statistics Canada 34-10-0133-01 · CMHC average rents, buildings with 3+ units, October",
    "Statistique Canada 18-10-0005-01 · 2002 = 100 · le loyer suit les mêmes logements d'une année à l'autre":
        "Statistics Canada 18-10-0005-01 · 2002 = 100 · rent tracks the same units from one year to the next",
    "Code": "Code",
    "IPC du loyer": "Rent CPI",
    "IPC d'ensemble": "All-items CPI",
    "Statistique Canada 46-10-0092-01 · 2 chambres · les 16 régions où loyer demandé et payé sont publiés":
        "Statistics Canada 46-10-0092-01 · two-bedroom · the 16 metro areas where asking and paid rents are published",
    "Trimestre": "Quarter",
    "Région métropolitaine": "Metro area",
    "Estimation": "Estimate",
    "Loyer ($)": "Rent ($)",
    "Fiabilité": "Reliability",
    "Normale": "Normal",
    "À utiliser avec prudence": "Use with caution",
    "SCHL, Rapport sur le marché locatif 2025 · logements reloués, hausses à échantillon constant":
        "CMHC, Rental Market Report 2025 · re-let units, same-sample increases",
    "Unité": "Unit",

    # ---------- Calculs (bandeau seulement ; petites étiquettes techniques laissées)
    "Séries des graphiques et des cartes · les NA() masquent un point de graphique, aucune autre feuille ne les lit":
        "Chart and map series · NA() hides a chart point; no other sheet reads them",
}

# ---------- Excel 365 (portefeuille)
_X365 = {
    "Excel 365 : un portefeuille de logements lu avec les fonctions dynamiques": "Excel 365: a housing portfolio read with dynamic array functions",
    "RECHERCHEX, LET, FILTRE, TRIER, UNIQUE · cases jaunes modifiables · requiert Excel 2021 ou Microsoft 365": "XLOOKUP, LET, FILTER, SORT, UNIQUE · yellow cells editable · requires Excel 2021 or Microsoft 365",
    "Portefeuille fictif d'une agence · huit logements, données du marché 2025".upper(): "FICTIONAL AGENCY PORTFOLIO · EIGHT UNITS, 2025 MARKET DATA",
    "Logement": "Unit", "Type": "Type", "Loyer actuel ($)": "Current rent ($)", "Début du bail": "Lease start", "Marché 2025 ($)": "Market 2025 ($)",
    "Hausse du marché depuis le bail": "Market increase since lease", "Écart au marché": "Gap to market", "Position": "Position",
    "Gain de relocation ($/mois)": "Re-let gain ($/month)",
    "Sous le marché": "Below market", "Au-dessus du marché": "Above market", "Dans le marché": "At market",
    "Choisis un type dans la liste.": "Pick a type from the list.", "Type de logement": "Unit type",
    "Année entre 1992 et 2025.": "Year between 1992 and 2025.",
    "Lecture dynamique du portefeuille".upper(): "DYNAMIC READ OF THE PORTFOLIO",
    "Logements sous le marché, du plus grand écart au plus petit (TRIER + FILTRE)": "Units below market, largest gap first (SORT + FILTER)",
    "Indicateurs du portefeuille (LET + FILTRE, UNIQUE)": "Portfolio indicators (LET + FILTER, UNIQUE)",
    "Logements sous le marché (écart < −5 %)": "Units below market (gap < −5%)",
    "Revenu annuel libéré si les 2 chambres sous le marché étaient reloués au prix des annonces": "Yearly income freed if the below-market two-bedrooms were re-let at asking prices",
    "Écart moyen au marché, tout le portefeuille": "Average gap to market, whole portfolio",
    "Types présents (UNIQUE)": "Types present (UNIQUE)", "Logements": "Units", "Écart moyen": "Average gap",
    "Les fonctions de cette feuille".upper(): "THE FUNCTIONS ON THIS SHEET",
    "Fonction": "Function", "Ce qu'elle fait ici": "What it does here", "Où": "Where",
    "RECHERCHEX": "XLOOKUP", "FILTRE + TRIER": "FILTER + SORT", "SI.CONDITIONS": "IFS",
    "Lit le loyer du marché pour un type ET une année : un seul appel, deux critères, sans colonne d'aide ni INDEX/EQUIV.": "Reads the market rent for a type AND a year: one call, two criteria, no helper column and no INDEX/MATCH.",
    "Nomme les étapes d'un calcul (debut, marche_bail, sous, gains) : la formule se lit comme une phrase.": "Names the steps of a calculation (start, market_at_lease, below, gains): the formula reads like a sentence.",
    "Extrait les logements sous le marché et les classe par écart, sans RANG ni colonnes intermédiaires.": "Extracts the units below market and ranks them by gap, with no RANK and no helper columns.",
    "Liste les types présents dans le portefeuille ; NB.SI et MOYENNE.SI.ENS complètent par type.": "Lists the types present in the portfolio; COUNTIF and AVERAGEIFS complete the picture by type.",
    "Position du loyer face au marché en une formule lisible.": "Position of the rent against the market in one readable formula.",
    "Colonnes F et G": "Columns F and G", "Colonne G, indicateurs": "Column G, indicators", "Bloc de gauche": "Left block", "Bloc de droite": "Right block", "Colonne I": "Column I",
    "Dans une version d'Excel antérieure à 2021, seule cette feuille affiche #NOM? ; toutes les autres s'ouvrent normalement.": "In an Excel version older than 2021, only this sheet shows #NAME?; every other sheet opens normally.",
    "Chaque cellule des blocs à résultat multiple lit sa ligne avec INDEX : les lignes sans résultat restent vides. Dans Excel 365, =TRIER(FILTRE(…)) saisi seul dans la première cellule se propage de lui-même.": "Each cell of the multi-result blocks reads its row with INDEX: rows without a result stay empty. In Excel 365, =SORT(FILTER(…)) typed alone in the first cell spills by itself.",
    # Mode d'emploi et Accueil
    "RECHERCHEX à deux critères": "XLOOKUP with two criteria",
    "Le loyer du marché pour un type et une année, en un seul appel.": "The market rent for a type and a year, in a single call.",
    "Des étapes nommées dans la formule : lisible et plus rapide à vérifier.": "Named steps inside the formula: readable and faster to check.",
    "FILTRE + TRIER + UNIQUE": "FILTER + SORT + UNIQUE",
    "Extraire, classer et dédoublonner un portefeuille sans colonnes intermédiaires.": "Extract, rank and de-duplicate a portfolio without helper columns.",
    "Toutes les feuilles d'analyse n'utilisent que des fonctions disponibles depuis Excel 2019, pour s'ouvrir partout sans erreur.": "Every analysis sheet uses only functions available since Excel 2019, so it opens everywhere without errors.",
    "La feuille « Excel 365 » montre les fonctions dynamiques (RECHERCHEX, LET, FILTRE, TRIER, UNIQUE) sur un portefeuille de logements ;": "The \"Excel 365\" sheet shows the dynamic functions (XLOOKUP, LET, FILTER, SORT, UNIQUE) on a housing portfolio;",
    "elle demande Excel 2021 ou Microsoft 365, et c'est la seule.": "it requires Excel 2021 or Microsoft 365, and it is the only one that does.",
    "Un portefeuille de logements lu avec RECHERCHEX, LET, FILTRE, TRIER et UNIQUE (Excel 2021 ou 365).": "A housing portfolio read with XLOOKUP, LET, FILTER, SORT and UNIQUE (Excel 2021 or 365).",
}
STRINGS.update(_X365)

# ---------- feuille masquée Calculs : en-têtes de colonnes, dont ceux qui deviennent des légendes et
# des infobulles de graphiques (« Tous les locataires », « Province choisie », « Loyer demandé »…)
_CALCULS = {
    "Calculs": "Calculations", "Contours": "Outline", "Classe": "Class",
    "Loyer (type choisi)": "Rent (selected type)", "IPC": "CPI", "Loyer réel": "Real rent", "Période choisie": "Selected period",
    "Contours Canada": "Canada outline", "Contours Est": "East outline", "Contours Ouest": "West outline",
    "Loyer début": "Starting rent", "Loyer fin": "Ending rent", "Hausse": "Increase",
    "Ville (triée)": "City (sorted)", "Hausse (triée)": "Increase (sorted)",
    "Tous les locataires": "All tenants", "Logements reloués (SCHL)": "Re-let units (CMHC)",
    "Écart entre loyer demandé et loyer payé ($)": "Gap between asking rent and rent paid ($)", "Loyer demandé ($)": "Asking rent ($)",
    "Loyer (année)": "Rent (year)", "Loyer (année - 1)": "Rent (year - 1)", "Loyer 2019": "Rent 2019",
    "Ensemble (année)": "All units (year)", "Ensemble 2019": "All units 2019", "Sur un an": "One year", "Depuis 2019": "Since 2019",
    "Réelle": "Real", "Tri": "Sort key", "Étiquette": "Label", "x étiquette": "x label", "y étiquette": "y label",
    **{f"y classe {i}": f"y class {i}" for i in range(1, 6)}, "y choisie": "y selected",
    "Rang trié": "Sorted rank", "Province triée": "Sorted province", "Valeur triée": "Sorted value",
    "Hausse 2025": "Increase 2025", "Rang 2025": "Rank 2025", "Seuils (quintiles)": "Thresholds (quintiles)",
    "Code choisi": "Selected code", "Province choisie": "Selected province",
    "x est": "x east", "y est": "y east", "x ouest": "x west", "y ouest": "y west", "Écart $": "Gap $", "Écart %": "Gap %",
    **{f"y est c{i}": f"y east c{i}" for i in range(1, 6)}, **{f"y ouest c{i}": f"y west c{i}" for i in range(1, 6)},
    "Ville choisie": "Selected city", "Valeur (texte)": "Value (text)", "Loyer demandé": "Asking rent", "Loyer payé": "Rent paid",
}
for _k, _v in _CALCULS.items():
    STRINGS.setdefault(_k, _v)
