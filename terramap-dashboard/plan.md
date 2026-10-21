# Plan — TerraMap Maroc

## Produit
Dashboard cartographique interactif pour explorer les scores finaux région × culture issus de `score_final_explicable.csv`.

## Design
- **Mouvement :** cartographie éditoriale / observatoire de terrain, sobre et analytique.
- **Principes :** lisibilité d'abord, contraste sémantique, densité maîtrisée, transparence méthodologique.
- **Palette :** bleu nuit pour l'interface et la confiance analytique, ambre pour le rendement, vert menthe pour l'écologie, fond sable pour rappeler le territoire marocain.
- **Layout :** cockpit asymétrique : bandeau KPI, carte dominante à gauche, panneau d'explication et comparaison à droite.
- **Signature :** repères cartographiques cerclés, pastilles de composante dominante, mini-barres de comparaison.
- **Interaction :** les filtres mettent à jour carte, KPI, tableau et explication sans navigation.
- **Animation :** transitions courtes et discrètes sur les cartes et barres, aucun mouvement décoratif.
- **Typographie :** Plus Jakarta Sans pour l'interface et les chiffres, avec une hiérarchie compacte.
- **Essence :** rendre les compromis agronomiques visibles en un regard — précis, pédagogique, actionnable.
- **Voix :** « Lire le territoire, culture par culture. » / « Un score n'est utile que s'il s'explique. »
- **Marque :** monogramme TM dans un cercle topographique.
- **Couleur signature :** bleu atlas #123047.

## Implémentation
- Vite + JavaScript vanilla pour rester léger et autonome.
- Leaflet via CDN pour la carte interactive et les repères des 12 régions.
- Parser CSV tolérant aux séparateurs et aux variantes de noms de colonnes.
- Chargement automatique de `/data/score_final_explicable.csv`, puis import local par input ou glisser-déposer.
- Fallback de démonstration signalé si le fichier réel est absent.
- Route manifest `/routes.json`.

## Structure
- `index.html` : shell et dépendances CDN.
- `src/main.js` : parsing, état, filtres, carte, comparaison et explications.
- `src/styles.css` : système visuel responsive.
- `public/data/score_final_explicable.csv` : fichier de démonstration remplaçable par le CSV réel.
