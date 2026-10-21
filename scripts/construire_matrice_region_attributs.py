"""
TerraMap Maroc — Construction de la matrice région x attributs (Phase M2)

Fusionne les 3 fichiers sources (sols, climat, écologie) sur `region_id`
pour obtenir une matrice unique : 12 régions x attributs environnementaux.

Entrées attendues (dans le même dossier que ce script, ou adapter INPUT_DIR) :
  - donnees_sols.csv
  - donnees_climatiques.csv
  - donnees_ecologie.csv

Sortie :
  - matrice_region_attributs.csv
"""

import pandas as pd
from pathlib import Path

INPUT_DIR = Path(r"D:\\terramap_maroc\\data_processed")   # dossier contenant les CSV sources
OUTPUT_FILE = Path(r"D:\\terramap_maroc\\data_processed\\matrice_region_attributs.csv")

# Colonnes redondantes présentes dans chaque fichier source (à ne garder qu'une fois)
COMMON_COLS = ["region", "capital", "latitude", "longitude"]


def charger_csv(nom_fichier: str) -> pd.DataFrame:
    """Charge un CSV source et vérifie la présence de la clé region_id."""
    chemin = INPUT_DIR / nom_fichier
    df = pd.read_csv(chemin)
    if "region_id" not in df.columns:
        raise ValueError(f"'region_id' absent de {nom_fichier}")
    return df


def construire_matrice() -> pd.DataFrame:
    """Fusionne sols + climat + écologie sur region_id."""
    sols = charger_csv("donnees_sols.csv")
    climat = charger_csv("donnees_climatiques.csv")
    ecologie = charger_csv("donnees_ecologie.csv")

    matrice = (
        sols
        .merge(climat.drop(columns=COMMON_COLS), on="region_id", how="inner")
        .merge(ecologie.drop(columns=COMMON_COLS), on="region_id", how="inner")
    )

    # Vérifications de cohérence
    n_regions_attendu = 12
    if len(matrice) != n_regions_attendu:
        print(
            f"⚠️  Attention : {len(matrice)} régions dans la matrice finale "
            f"(attendu : {n_regions_attendu}). Vérifier les jointures."
        )

    if matrice.isnull().values.any():
        cols_manquantes = matrice.columns[matrice.isnull().any()].tolist()
        print(f"⚠️  Valeurs manquantes détectées dans : {cols_manquantes}")

    return matrice


def main():
    matrice = construire_matrice()
    matrice.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Matrice construite : {matrice.shape[0]} régions x {matrice.shape[1]} colonnes")
    print(f"   Colonnes : {matrice.columns.tolist()}")
    print(f"   Fichier sauvegardé : {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
