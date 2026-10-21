# TerraMap Maroc — Rapport complet du travail réalisé

## 1. Présentation du projet

TerraMap Maroc est un dashboard cartographique interactif destiné à explorer et expliquer des scores d'adéquation entre des régions marocaines et des cultures agricoles.

Le dashboard met en relation :

- le **rendement attendu** ;
- la **composante écologique** ;
- le **score final** selon plusieurs scénarios alpha ;
- les **facteurs limitants** ;
- les **explications textuelles** générées par le script d'explicabilité intrinsèque ;
- les observations provenant de sources agricoles réelles.

L'objectif est de ne pas afficher uniquement un classement, mais de permettre de comprendre pourquoi une culture obtient un score donné et de comparer les recommandations avec les cultures documentées dans les données agricoles.

---

## 2. Architecture générale

Le projet est une application frontend basée sur :

- **Vite** ;
- **JavaScript** ;
- **HTML** ;
- **CSS** ;
- **Leaflet** pour la carte interactive ;
- des fichiers CSV locaux placés dans `public/data/`.

### Structure principale

```text
terramap/
├── index.html
├── package.json
├── package-lock.json
├── app.config.ts
├── plan.md
├── TODO.md
├── README_VSCODE.md
├── rapport_travail_dashboard.md
├── public/
│   ├── routes.json
│   └── data/
│       ├── .gitkeep
│       ├── score_final_explicable.csv
│       └── agriculture_actuelle.csv
└── src/
    ├── main.js
    └── styles.css
```

Les deux fichiers CSV sont des entrées de données. Ils ne sont pas obligatoirement inclus dans l'archive distribuée, car ils doivent être remplacés par les fichiers réels du projet.

---

## 3. Fonctionnalités réalisées

### 3.1 Carte interactive

La carte permet de :

- visualiser les régions marocaines ;
- afficher un repère par région ;
- représenter le score par la taille et la couleur du repère ;
- distinguer visuellement la dominante **rendement** et la dominante **écologie** ;
- survoler un repère pour obtenir un résumé ;
- cliquer sur un repère pour sélectionner une région et une culture ;
- utiliser le zoom et le déplacement de la carte.

La carte utilise désormais une géométrie locale réelle des **12 régions administratives du Maroc** dans `public/data/morocco-regions.geojson`. Les limites sont affichées sous les repères de scores, avec survol des régions et nom de la région. Cette approche évite de dépendre du chargement de tuiles Internet, qui peut être bloqué par certains navigateurs, réseaux ou environnements de prévisualisation.

La source de la géométrie est le jeu de données ouvert **geoBoundaries**, dérivé de sources OpenStreetMap/Wambacher. Une attribution est affichée dans la carte.

### 3.2 Filtres

L'interface propose :

- un filtre par culture ;
- un filtre par région ;
- un curseur alpha ;
- un bouton de réinitialisation ;
- un bouton d'import d'un CSV de scores.

Le curseur alpha permet de choisir entre trois scénarios présents dans le fichier réel :

```text
alpha = 0.3
alpha = 0.5
alpha = 0.7
```

Le poids alpha représente la contribution du rendement dans le score final. Plus alpha est élevé, plus la composante rendement est importante.

### 3.3 Indicateurs de synthèse

Le dashboard affiche notamment :

- le score final moyen ;
- le Meilleur score final ;
- la dominante du périmètre filtré ;
- le nombre de couples région × culture analysés.

### 3.4 Panneau d'explicabilité

Lorsqu'un couple région-culture est sélectionné, le panneau d'explicabilité affiche :

- le score final ;
- le score rendement ;
- le score écologique ;
- les barres de contribution des composantes ;
- la composante dominante ;
- l'explication textuelle du score ;
- les facteurs limitants ;
- la région et la culture sélectionnées.

Les colonnes alpha du fichier réel sont reconnues, notamment :

```text
score_final_alpha03
score_final_alpha05
score_final_alpha07
composante_dominante_alpha03
composante_dominante_alpha05
composante_dominante_alpha07
explication_alpha03
explication_alpha05
explication_alpha07
```

Le panneau utilise le scénario alpha sélectionné dans le curseur.

### 3.5 Comparaison des scores

La section « Comparaison des scores » présente les couples région-culture triés par score actif.

Elle affiche :

- le nom de la région ;
- la culture ;
- une barre proportionnelle au score ;
- le score final ;
- la composante dominante.

Les noms de régions sont construits à partir de la colonne `region`, qui est prioritaire sur `region_id` lorsque les deux colonnes existent.

### 3.6 Comparaison avec la réalité agricole

Une seconde source CSV peut être chargée automatiquement :

```text
public/data/agriculture_actuelle.csv
```

Cette source permet de comparer les recommandations TerraMap avec les cultures observées dans les documents agricoles.

Pour chaque région, le dashboard affiche :

- la meilleure recommandation TerraMap ;
- son score TerraMap ;
- les cultures observées dans le fichier agricole ;
- la culture recommandée si elle est observée ;
- le rendement réel lorsqu'il est disponible ;
- la superficie lorsqu'elle est disponible ;
- l'année ;
- la source documentaire ;
- le potentiel d'amélioration.

---

## 4. Schémas CSV utilisés

### 4.1 Fichier des scores TerraMap

Nom attendu :

```text
score_final_explicable.csv
```

Exemple d'en-tête utilisé :

```csv
region_id,region,culture,score_rendement,score_eco,score_final_alpha03,rang_alpha03,score_final_alpha05,rang_alpha05,score_final_alpha07,rang_alpha07,score_temp,score_rainfall,score_ph,score_temperature,score_pluie,facteur_limitant,facteur_limitant_score,explicabilite_liebig_disponible,contribution_rendement_alpha03,contribution_ecologie_alpha03,composante_dominante_alpha03,ecart_score_suivant_alpha03,explication_alpha03,contribution_rendement_alpha05,contribution_ecologie_alpha05,composante_dominante_alpha05,ecart_score_suivant_alpha05,explication_alpha05,contribution_rendement_alpha07,contribution_ecologie_alpha07,composante_dominante_alpha07,ecart_score_suivant_alpha07,explication_alpha07,culture_recommandee_alpha03,culture_recommandee_alpha05,culture_recommandee_alpha07,recommandation_stable_sur_3_scenarios
```

Colonnes importantes :

| Colonne | Utilisation |
|---|---|
| `region` | Nom de la région affiché dans l'interface |
| `culture` | Culture analysée |
| `score_rendement` | Score de rendement |
| `score_eco` | Score écologique |
| `score_final_alpha03` | Score final pour alpha 0,3 |
| `score_final_alpha05` | Score final pour alpha 0,5 |
| `score_final_alpha07` | Score final pour alpha 0,7 |
| `composante_dominante_alpha03` | Dominante du scénario alpha 0,3 |
| `composante_dominante_alpha05` | Dominante du scénario alpha 0,5 |
| `composante_dominante_alpha07` | Dominante du scénario alpha 0,7 |
| `explication_alpha03` | Explication pour alpha 0,3 |
| `explication_alpha05` | Explication pour alpha 0,5 |
| `explication_alpha07` | Explication pour alpha 0,7 |
| `facteur_limitant` | Facteur limitant général |

### 4.2 Fichier des observations agricoles

Nom attendu :

```text
agriculture_actuelle.csv
```

Schéma communiqué :

```csv
region_id,region,culture,superficie_ha,rendement_qha,source_doc,annee,note
```

Exemple :

```csv
region_id,region,culture,superficie_ha,rendement_qha,source_doc,annee,note
1,Tanger-Tetouan-Al Hoceima,Ble,253100.0,13.3,Monographie HCP Tanger-Tetouan-Al Hoceima Decembre 2020 (Tableau 47),2018-2019,Ble dur + ble tendre combines
1,Tanger-Tetouan-Al Hoceima,Orge,95300.0,10.6,Monographie HCP Tanger-Tetouan-Al Hoceima Decembre 2020 (Tableau 47),2018-2019,
1,Tanger-Tetouan-Al Hoceima,Mais,1500.0,12.7,Monographie HCP Tanger-Tetouan-Al Hoceima Decembre 2020 (Tableau 47),2018-2019,
```

Les valeurs absentes restent absentes. Elles ne sont jamais automatiquement converties en zéro.

---

## 5. Normalisation des données

### 5.1 Normalisation des régions

Le parser :

- retire les espaces inutiles ;
- normalise les accents ;
- accepte plusieurs variantes de nom ;
- rapproche les régions du CSV avec les régions cartographiques connues.

### 5.2 Normalisation des cultures

Les accents sont également normalisés pour rapprocher les cultures.

Par exemple :

```text
Ble = Blé
Mais = Maïs
```

Cette normalisation sert uniquement à faire correspondre les lignes entre les deux fichiers. Elle ne modifie pas le texte affiché à l'utilisateur.

### 5.3 Valeurs manquantes

Une cellule vide dans `superficie_ha` ou `rendement_qha` est traitée comme une donnée manquante :

```text
superficie non renseignée
rendement non renseigné
```

Elle n'est pas traitée comme :

```text
superficie = 0
rendement = 0
```

Une culture peut donc être affichée comme observée dans une source documentaire, même si ses données quantitatives sont incomplètes.

---

## 6. Calcul du potentiel d'amélioration

Le potentiel d'amélioration utilise uniquement les lignes agricoles qui possèdent simultanément :

```text
superficie_ha renseignée
ET
rendement_qha renseigné
```

Les lignes incomplètes restent visibles, mais elles ne sont pas utilisées dans le calcul du potentiel.

### 6.1 Étape 1 : meilleure recommandation TerraMap

Pour chaque région, le dashboard sélectionne la culture ayant le meilleur score TerraMap dans le périmètre courant et pour le scénario alpha actif.

Exemple :

```text
Olivier : 0,84
Blé : 0,72
Orge : 0,68
```

La recommandation TerraMap est alors :

```text
Olivier : 0,84
```

### 6.2 Étape 2 : cultures agricoles quantitativement exploitables

Le dashboard conserve uniquement les lignes agricoles dont les deux valeurs suivantes sont disponibles :

```text
superficie_ha
rendement_qha
```

Une ligne comme celle-ci est utilisée :

```text
Blé, superficie = 253100 ha, rendement = 13,3 q/ha
```

Une ligne comme celle-ci n'est pas utilisée dans le calcul :

```text
Orge, superficie vide, rendement vide
```

### 6.3 Étape 3 : meilleure culture observée comparable

Parmi les cultures observées avec des données complètes et qui existent aussi dans les scores TerraMap, le dashboard sélectionne la culture ayant le meilleur score TerraMap.

### 6.4 Formule

```text
Écart =
Score TerraMap de la meilleure recommandation
−
Score TerraMap de la meilleure culture observée quantitativement
```

Exemple :

```text
Recommandation TerraMap : Olivier = 0,84
Meilleure culture observée complète : Blé = 0,69

Écart = 0,84 − 0,69
Écart = 0,15
Écart = 15 points
```

Important : l'écart n'est pas une différence directe de rendement en q/ha.

Il ne calcule pas :

```text
rendement recommandé − rendement actuel
```

Il mesure l'écart entre deux scores TerraMap.

### 6.5 Seuils d'interprétation

| Écart | Niveau affiché |
|---:|---|
| 15 points ou plus | Fort · à étudier |
| 8 à 14 points | Modéré · à étudier |
| Moins de 8 points | Faible · proche |
| Aucun rapprochement possible | À documenter |
| Recommandation déjà observée avec données complètes | Alignée |

### 6.6 Limites

Le potentiel d'amélioration est un indicateur de priorisation. Il ne signifie pas automatiquement que :

- la culture recommandée doit remplacer la culture actuelle ;
- le rendement augmentera réellement ;
- la culture est économiquement rentable ;
- la culture est socialement acceptable ;
- les données documentaires sont récentes ;
- les contraintes d'irrigation, de marché ou de main-d'œuvre sont satisfaites.

Une validation agronomique, économique, environnementale et sociale est nécessaire avant toute décision.

---

## 7. Barre de navigation

Une barre « Aller à » a été ajoutée pour faciliter la bascule entre les parties du dashboard.

Elle contient les sections suivantes :

- **Synthèse** ;
- **Carte & explication** ;
- **Comparaison des scores** ;
- **Réalité agricole**.

Fonctionnement :

- clic sur un onglet pour atteindre directement la section ;
- défilement doux ;
- section active automatiquement mise en évidence ;
- barre sticky visible pendant le défilement ;
- défilement horizontal sur petits écrans mobiles.

---

## 8. Expérience utilisateur et design

Le design utilise une esthétique éditoriale et analytique :

- fond clair et sobre ;
- bleu profond pour la structure et les textes ;
- vert pour l'écologie et les états favorables ;
- ocre pour le rendement ;
- rouge doux pour les alertes ou écarts élevés ;
- typographie sans-serif pour la lecture ;
- police monospace pour les indicateurs, labels et scénarios alpha.

Les éléments importants sont présentés dans des panneaux séparés afin de conserver une hiérarchie claire :

1. filtres ;
2. synthèse ;
3. carte et explicabilité ;
4. classement ;
5. Confrontation avec la réalité agricole.

L'interface a été adaptée aux écrans desktop et mobiles.

---

## 9. Installation dans VS Code

### 9.1 Pré-requis

Installer :

- Node.js ;
- npm ;
- Visual Studio Code.

### 9.2 Installation

Décompresser l'archive puis ouvrir le dossier `terramap-dashboard` dans VS Code.

Dans le terminal VS Code :

```bash
npm install
```

Placer ensuite les deux fichiers CSV :

```text
public/data/score_final_explicable.csv
public/data/agriculture_actuelle.csv
```

### 9.3 Démarrage

```bash
npm run dev
```

Vite affiche normalement une adresse similaire à :

```text
http://localhost:3000
```

### 9.4 Build de production

```bash
npm run build
```

Le résultat compilé est placé dans :

```text
dist/
```

### 9.5 Import manuel

Si le fichier de score n'est pas présent dans `public/data/`, le dashboard affiche un jeu de démonstration.

Il est alors possible d'utiliser le bouton :

```text
Importer un CSV
```

Cette fonction permet de charger temporairement un fichier de score depuis l'ordinateur.

Le fichier `agriculture_actuelle.csv`, lui, est chargé automatiquement depuis :

```text
public/data/agriculture_actuelle.csv
```

---

## 10. Vérifications réalisées

Les vérifications suivantes ont été effectuées :

- vérification de syntaxe JavaScript avec `node --check src/main.js` ;
- compilation avec `npm run build` ;
- test du schéma réel du fichier de scores ;
- test des colonnes `alpha03`, `alpha05` et `alpha07` ;
- test des noms de régions avec et sans accents ;
- test des cultures `Ble`, `Blé`, `Mais` et `Maïs` ;
- test du fichier agricole contenant des valeurs en hectares et en q/ha ;
- test de lignes agricoles incomplètes ;
- test du calcul avec uniquement les lignes quantitativement complètes ;
- vérification desktop ;
- vérification mobile ;
- vérification de la barre de navigation ;
- création et mise à jour de l'archive VS Code.

Le dernier build a été validé avec succès.

---

## 11. Fichiers livrés

Archive complète prête pour VS Code :

```text
/home/ubuntu/terramap-dashboard-vscode.zip
```

Guide d'installation :

```text
/home/ubuntu/terramap/README_VSCODE.md
```

Rapport complet du travail :

```text
/home/ubuntu/terramap/rapport_travail_dashboard.md
```

---

## 12. Évolutions possibles

Les évolutions suivantes peuvent être ajoutées ultérieurement :

- afficher le classement des régions par potentiel d'amélioration ;
- ajouter un filtre « Fort potentiel uniquement » ;
- afficher un graphique comparant rendement réel et score TerraMap ;
- intégrer plusieurs années et une évolution temporelle ;
- distinguer les données HCP, DRA, monographies et autres sources ;
- ajouter un indice de fraîcheur des données ;
- ajouter un export CSV des régions prioritaires ;
- afficher des intervalles d'incertitude ;
- intégrer les contraintes économiques, hydriques et sociales ;
- ajouter une validation experte par région.

---

## Conclusion

Le dashboard TerraMap Maroc est désormais un outil d'exploration cartographique, d'explicabilité des scores et de confrontation prudente avec la réalité agricole.

La logique actuelle respecte les principes suivants :

- ne pas confondre absence de données et valeur nulle ;
- conserver la traçabilité des sources et des années ;
- distinguer observation documentaire et observation quantitative ;
- calculer le potentiel uniquement avec des lignes agricoles complètes ;
- présenter le potentiel comme une piste d'étude et non comme une décision automatique.
