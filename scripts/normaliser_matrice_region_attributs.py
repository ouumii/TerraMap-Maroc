"""
TerraMap Maroc — Normalisation min-max de la matrice région x attributs (Phase M2)

Produit DEUX matrices distinctes, pour ne pas mélanger exploration et scoring :

  1. matrice_normalisee_neutre.csv
     -> Toutes les variables normalisées 0-1, SANS aucune inversion.
     -> Usage : analyse exploratoire, corrélations entre attributs.
     -> Aucune variable n'a de sens "bon/mauvais" universel ici : même
        water_stress_pct ou resource_pressure_score restent bruts (juste
        remis à l'échelle), on ne fait qu'observer les régions telles quelles.

  2. matrice_orientee_ecologique.csv
     -> Mêmes variables normalisées 0-1, mais avec les indicateurs à
        direction universelle inversés (1 = toujours favorable).
     -> Usage : brique de départ pour le futur score écologique (M3/M4).
     -> Les attributs dépendants de la culture (pH, texture, climat) ne
        sont PAS inversés ici non plus : leur favorabilité dépend d'ECOCROP,
        pas d'un sens universel (traité en M3).

Règle de classification des variables :
  - Descriptives, dépendantes de la culture (jamais inversées, ni ici ni
    dans la version orientée) :
      ph, clay, sand, silt, temp_mean, temp_max, temp_min, rainfall, humidity
  - organic_carbon : descriptive à ce stade (non inversée), mais deviendra
    favorable (haut = mieux) lors du calcul du score écologique en M3/M4 —
    non inversée ici, car cette étape ne concerne que les indicateurs à
    direction UNIVERSELLE indépendante de la culture ; organic_carbon est
    laissée à la logique de pondération du score écologique, pas à
    l'inversion binaire.
  - À direction universelle, inversées dans la version "orientée écologique" :
      water_stress_pct        (haut = stress hydrique sévère -> défavorable)
      resource_pressure_score (haut = pression sur les ressources -> défavorable)
      evapotranspiration      (haut = perte en eau -> défavorable)
      irrigation_surface_pct  (haut = dépendance à l'irrigation -> défavorable)
  - À direction universelle, jamais inversées (déjà favorables si hautes) :
      water_availability (haut = mieux)

⚠️ Ces choix reflètent des décisions prises au fil du projet — à confirmer
   formellement avec l'encadrant, comme la liste finale des critères du score
   écologique.

Entrée  : matrice_region_attributs.csv (sortie du script précédent)
Sorties : matrice_normalisee_neutre.csv
          matrice_orientee_ecologique.csv
"""

import pandas as pd
from pathlib import Path

INPUT_FILE = Path(r"D:\terramap_maroc\data_processed\matrice_region_attributs.csv")
OUTPUT_NEUTRE = Path(r"D:\terramap_maroc\data_processed\matrice_normalisee_neutre.csv")
OUTPUT_ECOLOGIQUE = Path(r"D:\terramap_maroc\data_processed\matrice_orientee_ecologique.csv")

# Colonnes identifiantes / non pertinentes à ne pas normaliser
COLONNES_EXCLUES = ["region_id", "region", "capital", "latitude", "longitude", "source_doc", "annee","note", "score_irrigation"]

# Colonnes à direction universelle où une valeur plus haute est défavorable
# -> inversées UNIQUEMENT dans la version orientée écologique
COLONNES_INVERSEES = [
    "et0_fao_evapotranspiration",
    "irrigation_rate_pct",
]


def normaliser_min_max(serie: pd.Series) -> pd.Series:
    """Normalise une série sur [0, 1]. Retourne 0.5 partout si la série est constante."""
    min_val, max_val = serie.min(), serie.max()
    if max_val == min_val:
        return pd.Series(0.5, index=serie.index)
    return (serie - min_val) / (max_val - min_val)


def construire_matrice_neutre(matrice: pd.DataFrame) -> pd.DataFrame:
    """Normalisation pure 0-1, sans aucune inversion. Pour l'exploration."""
    resultat = matrice.copy()
    colonnes_a_normaliser = [c for c in matrice.columns if c not in COLONNES_EXCLUES]
    for col in colonnes_a_normaliser:
        resultat[col] = normaliser_min_max(matrice[col]).round(4)
    return resultat


def construire_matrice_ecologique(matrice_neutre: pd.DataFrame) -> pd.DataFrame:
    """Reprend la matrice neutre déjà normalisée et inverse les colonnes à
    direction universelle défavorable, pour préparer le score écologique."""
    resultat = matrice_neutre.copy()
    for col in COLONNES_INVERSEES:
        resultat[col] = (1 - resultat[col]).round(4)
    return resultat


def main():
    matrice = pd.read_csv(INPUT_FILE)

    matrice_neutre = construire_matrice_neutre(matrice)
    matrice_neutre.to_csv(OUTPUT_NEUTRE, index=False)

    matrice_ecologique = construire_matrice_ecologique(matrice_neutre)
    matrice_ecologique.to_csv(OUTPUT_ECOLOGIQUE, index=False)

    print(f"✅ Matrice neutre (exploration)          : {OUTPUT_NEUTRE.resolve()}")
    print(f"✅ Matrice orientée écologique (scoring) : {OUTPUT_ECOLOGIQUE.resolve()}")
    print(f"   Colonnes inversées dans la version écologique : {COLONNES_INVERSEES}")


if __name__ == "__main__":
    main()