# TerraMap Maroc — Dashboard cartographique

Dashboard frontend interactif pour explorer les scores région × culture du fichier `score_final_explicable.csv`.

## Prérequis

- Node.js 18 ou supérieur
- npm
- Visual Studio Code

## Installation dans VS Code

1. Décompresser l'archive puis ouvrir le dossier `terramap-dashboard` dans VS Code.
2. Ouvrir le terminal intégré.
3. Installer les dépendances :

```bash
npm install
```

4. Démarrer le serveur de développement :

```bash
npm run dev
```

5. Ouvrir l'URL affichée par Vite, généralement `http://localhost:3000`.

Pour générer la version de production :

```bash
npm run build
```

Le résultat est créé dans le dossier `dist/`.

## Ajouter le fichier de scores réel

Placer le fichier à cet emplacement :

```text
public/data/score_final_explicable.csv
```

Le dashboard le chargera automatiquement au démarrage. Si le fichier n'est pas trouvé, un jeu de démonstration est utilisé et un bandeau d'avertissement est affiché. Il est également possible d'importer un CSV directement avec le bouton **Importer un CSV**.

## Comparer avec la réalité agricole

Pour activer le bloc **Recommandations TerraMap et cultures observées**, placer le second fichier à cet emplacement :

```text
public/data/agriculture_actuelle.csv
```

Le schéma utilisé est compatible avec votre fichier :

```csv
region_id,region,culture,superficie_ha,rendement_qha,source_doc,annee,note
```

Le dashboard rapproche les deux sources par `region` et `culture` (les accents sont normalisés, donc `Ble` correspond à `Blé`). Pour chaque région, il affiche la meilleure recommandation du modèle selon le scénario α actif, les cultures réellement observées, le rendement réel, la superficie, l'année et un statut :

- **Recommandation observée sur le terrain** : la culture recommandée est observée dans la région ;
- **Observée · données quantitatives manquantes** : la culture est observée, mais la superficie et/ou le rendement ne sont pas renseignés ;
- **Opportunité à vérifier** : la culture recommandée n'est pas présente dans les observations fournies.

Une cellule vide reste affichée comme **non renseignée** : elle n'est jamais convertie en `0` et ne pénalise pas le statut d'observation. La source et l'année sont conservées lorsqu'elles sont disponibles.

Le bloc affiche également un **Priorité d'étude** par région. Pour éviter de tirer une conclusion à partir de sources incomplètes, son calcul utilise uniquement les lignes de `agriculture_actuelle.csv` qui ont **à la fois** `superficie_ha` et `rendement_qha` renseignés. Il compare alors le score de la meilleure recommandation TerraMap au meilleur score TerraMap parmi ces cultures observées quantitativement :

- **Fort · à étudier** : écart d'au moins 15 points et recommandation non observée ;
- **Modéré · à étudier** : écart de 8 à 14 points ;
- **Faible · proche** : écart inférieur à 8 points ;
- **À documenter** : aucune culture observée ne peut être rapprochée d'une culture évaluée par TerraMap.

Les cultures présentes dans le fichier mais sans superficie ou rendement restent visibles comme observations documentaires, mais elles ne participent pas au calcul de l'écart ni au classement du potentiel. Il s'agit d'un signal de priorisation, pas d'une preuve qu'un changement de culture améliorerait effectivement la production. Une validation agronomique, économique et sociale reste nécessaire.

Cette comparaison ne constitue pas une preuve causale de supériorité agronomique : elle confronte une recommandation de suitability à une observation historique/documentaire, en conservant l'année et la source du fichier réel.

## Barre de navigation

La barre **Aller à** reste visible pendant le défilement. Elle permet de basculer rapidement entre :

- **Synthèse** : indicateurs KPI ;
- **Carte & explication** : carte interactive et panneau « Pourquoi ce score ? » ;
- **Comparaison des scores** : classement des couples région × culture ;
- **Réalité agricole** : confrontation avec `agriculture_actuelle.csv`.

Sur mobile, la barre peut défiler horizontalement. La section actuellement visible est automatiquement mise en évidence.

## Colonnes reconnues

Le parser accepte plusieurs variantes de noms. Il reconnaît notamment directement le schéma produit par le script d'explicabilité intrinsèque :

```csv
region_id,region,culture,score_rendement,score_eco,score_final_alpha03,score_final_alpha05,score_final_alpha07,composante_dominante_alpha03,explication_alpha03,composante_dominante_alpha05,explication_alpha05,composante_dominante_alpha07,explication_alpha07,facteur_limitant
```

Le curseur du dashboard sélectionne les trois scénarios disponibles : `α = 0.3`, `α = 0.5` et `α = 0.7`. Les colonnes `score_final_alpha03`, `score_final_alpha05` et `score_final_alpha07` alimentent le score affiché ; les colonnes `explication_alpha03`, `explication_alpha05` et `explication_alpha07` alimentent le panneau **Pourquoi ce score ?**. Les scores peuvent être exprimés entre `0` et `1`, ou entre `0` et `100`. Les séparateurs virgule, point-virgule et tabulation sont acceptés. Les fichiers UTF-8 avec BOM sont également pris en charge. Les noms de régions avec ou sans accents sont normalisés pour la carte.

## Structure du projet

| Fichier | Rôle |
|---|---|
| `index.html` | Structure HTML, métadonnées et chargement de Leaflet |
| `src/main.js` | Parsing CSV, filtres, calculs, carte et interactions |
| `src/styles.css` | Design responsive desktop, tablette et mobile |
| `public/data/score_final_explicable.csv` | Emplacement du fichier CSV réel |
| `public/data/agriculture_actuelle.csv` | Observations agricoles réelles pour la comparaison terrain |
| `public/data/morocco-regions.geojson` | Limites géographiques locales des 12 régions marocaines |

## Carte réelle du Maroc

La carte utilise `public/data/morocco-regions.geojson` pour afficher les limites administratives réelles des 12 régions du Maroc. Le fichier est local et est donc disponible même lorsque les tuiles cartographiques Internet sont bloquées par le navigateur ou le réseau. Les repères de scores restent superposés au-dessus des limites régionales.
| `package.json` | Scripts npm et dépendance Vite |
| `public/routes.json` | Manifeste de route |

## Personnaliser

- Modifier les coordonnées des régions dans `REGION_META` dans `src/main.js`.
- Modifier la palette et les points de rupture des scores dans `scoreColor()` et `src/styles.css`.
- Ajouter ou modifier les alias de colonnes dans la fonction `field()`/`transform()`.
- Le fond cartographique est local et stylisé : aucune clé API ni service de tuiles externe n'est nécessaire.
