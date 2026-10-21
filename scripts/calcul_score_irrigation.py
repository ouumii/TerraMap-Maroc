"""
Calcul de irrigation_rate_pct et Score_irrigation par region
---------------------------------------------------------------
Source des donnees brutes (SAU, SAU irriguee) : transcription manuelle
du tableau de l'Atlas de l'Agriculture Marocaine, 3e edition (2020),
base sur le Recensement General de l'Agriculture (RGA) 2016. Cette
source a ete retenue car elle fournit, dans un meme tableau et pour
une meme annee de reference, la SAU et la SAU irriguee des 12 regions
administratives actuelles - garantissant l'homogeneite necessaire
(contrairement aux monographies HCP/DRA individuelles, dont l'annee
et le perimetre administratif different selon les regions).

Ce script ne "collecte" pas les donnees (transcription manuelle depuis
l'Atlas, non automatisable) mais calcule le taux et le score a partir
des valeurs SAU / SAU irriguee une fois saisies.
"""

import pandas as pd
from pathlib import Path

INPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv")

# Donnees brutes transcrites de l'Atlas RGA 2016 (SAU et SAU irriguee en ha)
data = {
    "region_id": list(range(1, 13)),
    "region": [
        "Tanger-Tetouan-Al Hoceima", "Oriental", "Fes-Meknes", "Rabat-Sale-Kenitra",
        "Beni Mellal-Khenifra", "Casablanca-Settat", "Marrakech-Safi", "Draa-Tafilalet",
        "Souss-Massa", "Guelmim-Oued Noun", "Laayoune-Sakia El Hamra", "Dakhla-Oued Ed Dahab"
    ],
    "sau_2016_ha": [
        729149, 889450, 1235521, 942981, 994463, 1263042,
        2055977, 270910, 453445, 164100, 19732, 1908
    ],
    "sau_irriguee_2016_ha": [
        56712, 150094, 158968, 185704, 208374, 141469,
        306264, 176539, 163759, 30107, 4311, 990
    ],
    "source_doc": ["Atlas de l'Agriculture Marocaine 3e edition (2020) - RGA 2016"] * 12,
    "annee": [2016] * 12,
}

df = pd.DataFrame(data)

# Calcul du taux d'irrigation
df["irrigation_rate_pct"] = (df["sau_irriguee_2016_ha"] / df["sau_2016_ha"] * 100).round(2)

# Normalisation min-max inversee : taux eleve -> score bas (pression plus forte)
r_min, r_max = df["irrigation_rate_pct"].min(), df["irrigation_rate_pct"].max()
df["score_irrigation"] = 1 - (df["irrigation_rate_pct"] - r_min) / (r_max - r_min)

# Notes ponctuelles (coherence externe / prudence agronomique)
notes = {
    8: "Coherent avec source independante DRA (63.9% via agrimaroc.ma) - confiance elevee",
    12: "SAU tres faible (region desertique/cotiere) - a interpreter avec prudence agronomique",
}
df["note"] = df["region_id"].map(notes).fillna("")

# Reordonner les colonnes
df = df[[
    "region_id", "region", "sau_2016_ha", "sau_irriguee_2016_ha",
    "irrigation_rate_pct", "source_doc", "annee", "note", "score_irrigation"
]]

df.to_csv(OUTPUT_FILE, index=False)

print("Score_irrigation calcule pour les 12 regions :")
print(df[["region", "irrigation_rate_pct", "score_irrigation"]].sort_values("irrigation_rate_pct").to_string(index=False))
