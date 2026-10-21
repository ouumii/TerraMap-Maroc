# Comparaison TerraMap avec la situation agricole actuelle

## 1. Périmètre et règle de traitement des données manquantes

La comparaison est réalisée entre les 228 couples région–culture du score final et le fichier `agriculture_actuelle.csv`. Les valeurs absentes ne sont pas remplacées par zéro : une cellule vide peut correspondre à une culture non isolée, à une donnée non disponible dans la monographie, à une culture non pratiquée ou à une absence de couverture dans le fichier. La comparaison quantitative est donc limitée aux couples disposant simultanément d’une superficie et d’un rendement documentés.

## 2. Couverture des données

- Régions couvertes par les scores : **12**.
- Cultures couvertes par les scores : **19**.
- Couples région–culture évalués : **228**.
- Couples avec superficie et rendement disponibles : **57** (25.0 %).
- Couples présents dans le fichier agricole mais incomplets : **171**.
- Couples non couverts par le fichier agricole : **0**.

### Répartition des statuts

| Statut | Nombre de couples |
|---|---:|
| non documentée — valeur non disponible dans la source | 125 |
| documentée (superficie et rendement disponibles) | 57 |
| non documentée — motif à vérifier dans la note/source | 22 |
| non documentée — culture agrégée/non isolée | 15 |
| non documentée — note: non pratiquée/non significative | 9 |

## 3. État des recommandations selon α

| Scénario | Recommandations avec données agricoles complètes | Recommandations sans données complètes |
|---|---:|---:|
| alpha=0.3 | 3/12 | 9/12 |
| alpha=0.5 | 3/12 | 9/12 |
| alpha=0.7 | 3/12 | 9/12 |

## 4. Tableau des recommandations et de leur situation documentée

| Région | Scénario | Culture recommandée | Score final | Situation actuelle documentée | Rendement actuel (qx/ha) |
|---|---|---|---:|---|---:|
| Tanger-Tetouan-Al Hoceima | alpha=0.3 | Figuier | 0.963 | Oui — documentée (superficie et rendement disponibles) | 24.80 |
| Tanger-Tetouan-Al Hoceima | alpha=0.5 | Figuier | 0.938 | Oui — documentée (superficie et rendement disponibles) | 24.80 |
| Tanger-Tetouan-Al Hoceima | alpha=0.7 | Pois chiche | 0.952 | Oui — documentée (superficie et rendement disponibles) | 7.70 |
| Oriental | alpha=0.3 | Olivier | 0.586 | Oui — documentée (superficie et rendement disponibles) | 16.99 |
| Oriental | alpha=0.5 | Palmier dattier | 0.550 | Oui — documentée (superficie et rendement disponibles) | 12.94 |
| Oriental | alpha=0.7 | Palmier dattier | 0.560 | Oui — documentée (superficie et rendement disponibles) | 12.94 |
| Fes-Meknes | alpha=0.3 | Pois chiche | 0.764 | Oui — documentée (superficie et rendement disponibles) | 1.70 |
| Fes-Meknes | alpha=0.5 | Pois chiche | 0.831 | Oui — documentée (superficie et rendement disponibles) | 1.70 |
| Fes-Meknes | alpha=0.7 | Pois chiche | 0.899 | Oui — documentée (superficie et rendement disponibles) | 1.70 |
| Rabat-Sale-Kenitra | alpha=0.3 | Figuier | 0.954 | Non — non documentée — valeur non disponible dans la source | — |
| Rabat-Sale-Kenitra | alpha=0.5 | Figuier | 0.967 | Non — non documentée — valeur non disponible dans la source | — |
| Rabat-Sale-Kenitra | alpha=0.7 | Figuier | 0.980 | Non — non documentée — valeur non disponible dans la source | — |
| Beni Mellal-Khenifra | alpha=0.3 | Figuier | 0.843 | Non — non documentée — culture agrégée/non isolée | — |
| Beni Mellal-Khenifra | alpha=0.5 | Vigne | 0.856 | Non — non documentée — valeur non disponible dans la source | — |
| Beni Mellal-Khenifra | alpha=0.7 | Vigne | 0.914 | Non — non documentée — valeur non disponible dans la source | — |
| Casablanca-Settat | alpha=0.3 | Olivier | 0.877 | Non — non documentée — motif à vérifier dans la note/source | — |
| Casablanca-Settat | alpha=0.5 | Olivier | 0.891 | Non — non documentée — motif à vérifier dans la note/source | — |
| Casablanca-Settat | alpha=0.7 | Oignon | 0.909 | Non — non documentée — motif à vérifier dans la note/source | — |
| Marrakech-Safi | alpha=0.3 | Olivier | 0.578 | Non — non documentée — valeur non disponible dans la source | — |
| Marrakech-Safi | alpha=0.5 | Olivier | 0.508 | Non — non documentée — valeur non disponible dans la source | — |
| Marrakech-Safi | alpha=0.7 | Olivier | 0.438 | Non — non documentée — valeur non disponible dans la source | — |
| Draa-Tafilalet | alpha=0.3 | Palmier dattier | 0.332 | Non — non documentée — valeur non disponible dans la source | — |
| Draa-Tafilalet | alpha=0.5 | Palmier dattier | 0.409 | Non — non documentée — valeur non disponible dans la source | — |
| Draa-Tafilalet | alpha=0.7 | Palmier dattier | 0.485 | Non — non documentée — valeur non disponible dans la source | — |
| Souss-Massa | alpha=0.3 | Palmier dattier | 0.504 | Non — non documentée — valeur non disponible dans la source | — |
| Souss-Massa | alpha=0.5 | Palmier dattier | 0.549 | Non — non documentée — valeur non disponible dans la source | — |
| Souss-Massa | alpha=0.7 | Palmier dattier | 0.594 | Non — non documentée — valeur non disponible dans la source | — |
| Guelmim-Oued Noun | alpha=0.3 | Figuier | 0.428 | Non — non documentée — valeur non disponible dans la source | — |
| Guelmim-Oued Noun | alpha=0.5 | Figuier | 0.306 | Non — non documentée — valeur non disponible dans la source | — |
| Guelmim-Oued Noun | alpha=0.7 | Figuier | 0.183 | Non — non documentée — valeur non disponible dans la source | — |
| Laayoune-Sakia El Hamra | alpha=0.3 | Figuier | 0.401 | Non — non documentée — valeur non disponible dans la source | — |
| Laayoune-Sakia El Hamra | alpha=0.5 | Figuier | 0.287 | Non — non documentée — valeur non disponible dans la source | — |
| Laayoune-Sakia El Hamra | alpha=0.7 | Figuier | 0.172 | Non — non documentée — valeur non disponible dans la source | — |
| Dakhla-Oued Ed Dahab | alpha=0.3 | Figuier | 0.307 | Non — non documentée — valeur non disponible dans la source | — |
| Dakhla-Oued Ed Dahab | alpha=0.5 | Figuier | 0.219 | Non — non documentée — valeur non disponible dans la source | — |
| Dakhla-Oued Ed Dahab | alpha=0.7 | Figuier | 0.132 | Non — non documentée — valeur non disponible dans la source | — |

## 5. Interprétation méthodologique

Une recommandation TerraMap qui ne possède pas de rendement agricole actuel documenté ne doit pas être interprétée comme une preuve que la culture est absente de la région, ni comme une preuve d’amélioration potentielle. Elle signifie uniquement que la comparaison quantitative n’est pas possible avec les sources actuellement compilées. De même, une culture présente dans les données agricoles n’est pas automatiquement considérée comme optimale : l’objectif du système est précisément d’examiner l’écart entre la situation observée et l’adéquation calculée selon les critères climatiques, pédologiques et hydriques.

## 6. Fichiers de sortie

- `comparaison_score_agriculture.csv` : jointure complète des scores et données agricoles.
- `recommandations_et_situation_actuelle.csv` : une ligne par région et scénario α.
- `synthese_comparaison_agriculture.csv` : indicateurs de couverture et de comparaison.