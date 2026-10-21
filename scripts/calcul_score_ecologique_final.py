"""
Calcul du Score ecologique final : Score_eco(r, c)
----------------------------------------------------
Formule :
    Score_eco(r, c) = w1 x Score_deficit(r, c) + w2 x Score_irrigation(r)

Ponderation AHP (matrice 2x2, echelle de Saaty) :
    a = 3  ->  Score_deficit jugé modérément plus important que Score_irrigation
    w1 = a / (a+1) = 0.75
    w2 = 1 / (a+1) = 0.25

Justification du jugement (a=3) :
    Le cadre FAO de land evaluation (Sys et al. ; methodologie ECOCROP) place
    l'adequation directe entre exigences de la culture et conditions du milieu
    - ici, le deficit hydrique climatique propre a chaque couple region-culture -
    au coeur de l'evaluation de suitabilite. La pression d'irrigation regionale
    est un facteur contextuel/de gestion, pertinent mais secondaire dans ce cadre.
    Note methodologique : pour une matrice 2x2, le Consistency Ratio vaut
    systematiquement 0 (un jugement unique ne peut pas se contredire lui-meme) -
    ceci est une propriete mathematique du cas n=2, pas une preuve de qualite
    du jugement lui-meme.

Entrees :
    - deficit_hydrique_r_c.csv  (228 lignes : region x culture, Score_deficit)
    - donnees_ecologie.csv      (12 lignes  : region, Score_irrigation)

Sortie :
    - score_ecologique_final.csv (228 lignes : region x culture, Score_eco)
"""

import pandas as pd
from pathlib import Path

DEFICIT_FILE = Path("D:\\terramap_maroc\\data_processed\\deficit_hydrique_r_c.csv")
ECOLOGIE_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\score_ecologique_final.csv")

# Ponderation AHP (cf. justification ci-dessus)
A_SAATY = 3
W1 = A_SAATY / (A_SAATY + 1)   # poids Score_deficit  = 0.75
W2 = 1 / (A_SAATY + 1)          # poids Score_irrigation = 0.25

deficit = pd.read_csv(DEFICIT_FILE)
eco = pd.read_csv(ECOLOGIE_FILE)

df = deficit.merge(eco[["region_id", "score_irrigation"]], on="region_id", how="left")
df["score_eco"] = W1 * df["score_deficit"] + W2 * df["score_irrigation"]

out = df[["region_id", "region", "culture", "score_deficit", "score_irrigation", "score_eco"]]
out.to_csv(OUTPUT_FILE, index=False)

print(f"Ponderation AHP : w1={W1} (Score_deficit), w2={W2} (Score_irrigation) - a={A_SAATY} (echelle de Saaty)")
print(f"Fichier cree : {len(out)} lignes (12 regions x 19 cultures)\n")

print("Top 5 meilleurs Score_eco :")
print(out.nlargest(5, "score_eco")[["region", "culture", "score_eco"]].to_string(index=False))

print("\nTop 5 Score_eco les plus faibles :")
print(out.nsmallest(5, "score_eco")[["region", "culture", "score_eco"]].to_string(index=False))
