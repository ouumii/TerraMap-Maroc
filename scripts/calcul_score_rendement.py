"""
Calcul du Score de rendement : Score_rendement(r, c)
-------------------------------------------------------
Methode : fonction d'appartenance trapezoidale ECOCROP, appliquee a 3 criteres
continus (temperature, pluviometrie, pH), puis agregation par MINIMUM (loi du
minimum de Liebig - un facteur limitant ne peut pas etre compense par un autre
facteur favorable).

Decision validee : le critere texture (categoriel, TEXT) est exclu du
calcul quantitatif et signale comme limite assumee dans le rapport - seuls les
3 criteres non categoriels (temperature, pluviometrie, pH) sont retenus.

    S(x) = 0                                   si x < Vmin
         = (x - Vmin) / (Vopmin - Vmin)         si Vmin <= x < Vopmin
         = 1                                    si Vopmin <= x <= Vopmax
         = (Vmax - x) / (Vmax - Vopmax)         si Vopmax < x <= Vmax
         = 0                                    si x > Vmax

    Score_rendement(r, c) = min(Score_temp(r, c), Score_rainfall(r, c), Score_pH(r, c))

Entrees :
    - exigences_cultures.csv   (FAO ECOCROP : TMIN/TOPMN/TOPMX/TMAX, RMIN/ROPMN/ROPMX/RMAX, PHMIN/PHOPMN/PHOPMX/PHMAX)
    - donnees_climatiques.csv  (Open-Meteo : temp_mean, rainfall par region)
    - donnees_sols.csv         (SoilGrids : ph par region)

Sortie :
    - score_rendement_r_c.csv (228 lignes : region x culture, Score_temp, Score_rainfall, Score_pH, Score_rendement)
"""

import pandas as pd
from pathlib import Path

ECOCROP_FILE = Path("D:\\terramap_maroc\\data_processed\\exigences_cultures.csv")
CLIMAT_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_climatiques.csv")
SOLS_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_sols.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\score_rendement_r_c.csv")

# ============================================================
# Correspondance ScientificName (ECOCROP) -> nom francais utilise
# dans le reste du data lake (agriculture_actuelle.csv, kc_values.csv...).
# Verifie directement sur le contenu d'exigences_cultures.csv.
# ============================================================
CROP_NAME_MAPPING = {
    "Allium cepa": "Oignon",
    "Citrus sp.": "Agrumes",
    "Ficus carica": "Figuier",
    "Helianthus annuus": "Tournesol",
    "Hordeum vulgare": "Orge",
    "Lycopersicon esculentum": "Tomate",
    "Malus domestica": "Pommier",
    "Medicago sativa": "Luzerne",
    "Olea europaea": "Olivier",
    "Oryza sativa": "Riz",
    "Phaseolus vulgaris": "Haricot",
    "Phoenix dactylifera": "Palmier dattier",
    "Solanum tuberosum": "Pomme de terre",
    "Triticum aestivum": "Ble",
    "Vitis vinifera": "Vigne",
    "Zea mays": "Mais",
    "Prunus amygdalus": "Amandier",
    "Cicer arietinum": "Pois chiche",
    "Lens culinaris": "Lentille",
}


def trapezoidal_score(x, vmin, vopmin, vopmax, vmax):
    """Fonction d'appartenance trapezoidale ECOCROP. Retourne un score [0, 1].
    Gere les cas limites ou les bornes optimales et absolues sont confondues
    (evite une division par zero)."""
    if pd.isna(x) or pd.isna(vmin) or pd.isna(vopmin) or pd.isna(vopmax) or pd.isna(vmax):
        return None

    if x < vmin or x > vmax:
        return 0.0
    elif x < vopmin:
        if vopmin == vmin:
            return 1.0
        return (x - vmin) / (vopmin - vmin)
    elif x <= vopmax:
        return 1.0
    else:
        if vmax == vopmax:
            return 1.0
        return (vmax - x) / (vmax - vopmax)


# 1. Chargement des donnees
ecocrop = pd.read_csv(ECOCROP_FILE)
climat = pd.read_csv(CLIMAT_FILE)
sols = pd.read_csv(SOLS_FILE)

ecocrop["culture"] = ecocrop["ScientificName"].map(CROP_NAME_MAPPING)

missing_mapping = ecocrop[ecocrop["culture"].isna()]["ScientificName"].tolist()
if missing_mapping:
    print(f"⚠️ ATTENTION : {len(missing_mapping)} ScientificName non trouve(s) dans CROP_NAME_MAPPING : {missing_mapping}")
    print("   -> Verifier l'orthographe exacte dans exigences_cultures.csv et completer le mapping.")

# 2. Produit cartesien region x culture (12 x 19 = 228 couples)
climat_sols = climat.merge(sols[["region_id", "ph"]], on="region_id", how="left")
climat_sols["key"] = 1
ecocrop["key"] = 1
df = climat_sols.merge(ecocrop, on="key").drop(columns="key")

# 3. Calcul des 3 scores trapezoidaux
df["score_temp"] = df.apply(
    lambda r: trapezoidal_score(r["temp_mean"], r["TMIN"], r["TOPMN"], r["TOPMX"], r["TMAX"]),
    axis=1
)
df["score_rainfall"] = df.apply(
    lambda r: trapezoidal_score(r["rainfall"], r["RMIN"], r["ROPMN"], r["ROPMX"], r["RMAX"]),
    axis=1
)
df["score_ph"] = df.apply(
    lambda r: trapezoidal_score(r["ph"], r["PHMIN"], r["PHOPMN"], r["PHOPMX"], r["PHMAX"]),
    axis=1
)

# 4. Agregation par Minimum (loi de Liebig) - texture (categorielle) exclue,
#    decision validee avec MO, a signaler comme limite assumee dans le rapport.
df["score_rendement"] = df[["score_temp", "score_rainfall", "score_ph"]].min(axis=1, skipna=False)

out = df[[
    "region_id", "region", "culture",
    "score_temp", "score_rainfall", "score_ph", "score_rendement"
]]
out.to_csv(OUTPUT_FILE, index=False)

print(f"\nFichier cree : {len(out)} lignes (12 regions x 19 cultures attendues)")
print(f"Lignes avec score_rendement manquant (donnee ECOCROP ou region incomplete) : {out['score_rendement'].isna().sum()}")

print("\nTop 5 meilleurs Score_rendement :")
print(out.nlargest(5, "score_rendement")[["region", "culture", "score_rendement"]].to_string(index=False))

print("\nTop 5 Score_rendement les plus faibles (hors valeurs manquantes) :")
print(out.dropna(subset=["score_rendement"]).nsmallest(5, "score_rendement")[["region", "culture", "score_rendement"]].to_string(index=False))
