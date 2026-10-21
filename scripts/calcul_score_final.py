"""
Calcul du Score final : Score_final(r, c)
---------------------------------------------
Formule :
    Score_final(r, c) = alpha x Score_rendement(r, c) + (1 - alpha) x Score_eco(r, c)

alpha est un curseur configurable par l'utilisateur (compromis rendement /
ecologie). Conformement a la decision actee (section 9 du document de suivi
de projet), 3 valeurs canoniques sont presentees systematiquement plutot
qu'une valeur unique :
    alpha = 0.3  -> ecologie prioritaire
    alpha = 0.5  -> neutre
    alpha = 0.7  -> productivite prioritaire

Entrees :
    - score_rendement_r_c.csv   (228 lignes : region x culture, score_rendement)
    - score_ecologique_final.csv (228 lignes : region x culture, score_eco)

Sortie :
    - score_final_r_c.csv (228 lignes x 3 colonnes de score, une par alpha,
      + le rang de chaque culture au sein de sa region pour chaque alpha)
"""

import pandas as pd
from pathlib import Path

RENDEMENT_FILE = Path("D:\\terramap_maroc\\data_processed\\score_rendement_r_c.csv")
ECO_FILE = Path("D:\\terramap_maroc\\data_processed\\score_ecologique_final.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\score_final_r_c.csv")

ALPHAS = {
    "score_final_alpha03": 0.3,  # ecologie prioritaire
    "score_final_alpha05": 0.5,  # neutre
    "score_final_alpha07": 0.7,  # productivite prioritaire
}

# 1. Chargement et fusion des deux scores
rendement = pd.read_csv(RENDEMENT_FILE)
eco = pd.read_csv(ECO_FILE)

df = rendement.merge(
    eco[["region_id", "culture", "score_eco"]],
    on=["region_id", "culture"],
    how="outer",
    indicator=True
)

# 2. Controle de coherence : verifier que la fusion couvre bien les 228 couples
#    des deux cotes (aucun couple present dans un fichier mais absent de l'autre)
only_left = df[df["_merge"] == "left_only"]
only_right = df[df["_merge"] == "right_only"]
if len(only_left) > 0:
    print(f"⚠️ ATTENTION : {len(only_left)} couple(s) present(s) dans score_rendement mais absent(s) de score_eco :")
    print(only_left[["region", "culture"]].to_string(index=False))
if len(only_right) > 0:
    print(f"⚠️ ATTENTION : {len(only_right)} couple(s) present(s) dans score_eco mais absent(s) de score_rendement :")
    print(only_right[["region", "culture"]].to_string(index=False))
df = df.drop(columns="_merge")

n_missing = df[["score_rendement", "score_eco"]].isna().any(axis=1).sum()
if n_missing > 0:
    print(f"⚠️ ATTENTION : {n_missing} couple(s) avec score_rendement OU score_eco manquant "
          f"-> Score_final sera NaN pour ces couples (non compense arbitrairement).")

# 3. Calcul du Score_final pour les 3 alphas canoniques
for col_name, alpha in ALPHAS.items():
    df[col_name] = alpha * df["score_rendement"] + (1 - alpha) * df["score_eco"]

# 4. Rang de chaque culture au sein de sa region, pour chaque alpha
#    (1 = meilleure recommandation pour cette region, selon cet alpha)
for col_name in ALPHAS:
    rank_col = col_name.replace("score_final", "rang")
    df[rank_col] = df.groupby("region_id")[col_name].rank(ascending=False, method="min").astype("Int64")

cols = ["region_id", "region", "culture", "score_rendement", "score_eco"]
for col_name in ALPHAS:
    rank_col = col_name.replace("score_final", "rang")
    cols += [col_name, rank_col]

out = df[cols].sort_values(["region_id", "rang_alpha05"])
out.to_csv(OUTPUT_FILE, index=False)

print(f"\nFichier cree : {len(out)} lignes (12 regions x 19 cultures)")

# 5. Apercu : meilleure culture recommandee par region, pour chaque alpha
print("\nMeilleure culture recommandee par region (alpha=0.5, neutre) :")
best_neutral = out[out["rang_alpha05"] == 1][["region", "culture", "score_final_alpha05"]]
print(best_neutral.to_string(index=False))

print("\nComparaison alpha=0.3 (ecologie) vs alpha=0.7 (productivite) - meilleure culture par region :")
best_eco = out[out["rang_alpha03"] == 1][["region", "culture"]].rename(columns={"culture": "meilleure_culture_eco_prioritaire"})
best_prod = out[out["rang_alpha07"] == 1][["region", "culture"]].rename(columns={"culture": "meilleure_culture_productivite_prioritaire"})
comparaison = best_eco.merge(best_prod, on="region")
print(comparaison.to_string(index=False))
