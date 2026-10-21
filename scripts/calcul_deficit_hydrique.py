"""
Calcul du Deficit hydrique climatique potentiel et de Score_deficit(r, c)
----------------------------------------------------------------------------
Methode FAO-56 (Allen et al. 1998) :
    ETc(r, c) = Kc_mid(c) x ET0(r)
    Deficit(r, c) = max(0, ETc(r, c) - rainfall(r))
    Score_deficit(r, c) = 1 - MinMax(Deficit(r, c))

Sources :
- ET0(r) et rainfall(r) : donnees_climatiques.csv (Open-Meteo, methode FAO
  Penman-Monteith). La colonne "evapotranspiration" correspond a
  et0_fao_evapotranspiration (verifie dans le script de collecte).
- Kc_mid(c) : kc_values.csv (FAO-56 Table 12 ; Paredes et al. 2024 pour
  le figuier, absent de FAO-56).

Limite assumee et documentee : Kc_mid seul est utilise (pas de courbe
Kc_ini -> Kc_mid -> Kc_end), faute de calendriers culturaux pour les 19
cultures. Le "Deficit" est donc un indicateur climatique comparatif
annuel simplifie, pas une estimation exacte du besoin d'irrigation.
Un score de 0 ou 1 est relatif a l'echantillon des 228 couples observes,
pas un seuil agronomique absolu.
"""

import pandas as pd
from pathlib import Path

CLIMAT_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_climatiques.csv")
KC_FILE = Path("D:\\terramap_maroc\\data_raw\\eau\\kc_values.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\deficit_hydrique_r_c.csv")

clim = pd.read_csv(CLIMAT_FILE)
kc = pd.read_csv(KC_FILE)

# Produit cartesien region x culture (12 x 19 = 228 couples)
clim["key"] = 1
kc["key"] = 1
df = clim.merge(kc, on="key").drop(columns="key")

# ETc et Deficit
df["ETc_mm"] = df["kc_mid"] * df["et0_fao_evapotranspiration"]
df["deficit_mm"] = (df["ETc_mm"] - df["rainfall"]).clip(lower=0)

# Normalisation min-max du deficit sur les 228 couples (score inverse : 1 = favorable)
dmin, dmax = df["deficit_mm"].min(), df["deficit_mm"].max()
df["score_deficit"] = 1 - (df["deficit_mm"] - dmin) / (dmax - dmin)

out = df[[
    "region_id", "region", "culture", "kc_mid",
    "et0_fao_evapotranspiration", "rainfall", "ETc_mm", "deficit_mm", "score_deficit"
]].rename(columns={"et0_fao_evapotranspiration": "et0_mm", "rainfall": "rainfall_mm"})

out.to_csv(OUTPUT_FILE, index=False)

print(f"Fichier cree : {len(out)} lignes (12 regions x 19 cultures)")
print("\nCouple avec le deficit minimal (score le plus favorable) :")
print(out.loc[out["deficit_mm"].idxmin()])
print("\nCouple avec le deficit maximal (score le moins favorable) :")
print(out.loc[out["deficit_mm"].idxmax()])

# ============================================================
# Verification de non-redondance avec Score_irrigation (region seule)
# Suit la meme exigence methodologique que la verification de
# correlation clay/sand/silt et water_stress_pct/resource_pressure_score
# effectuee en M2, avant integration conjointe dans l'AHP.
# ============================================================
try:
    eco = pd.read_csv(Path("D:\\PFE\\TerraMap\\data_processed\\donnees_ecologie.csv"))
    deficit_moyen = out.groupby("region")["deficit_mm"].mean().reset_index()
    deficit_moyen.columns = ["region", "deficit_moyen_mm"]
    merged = eco.merge(deficit_moyen, on="region")
    corr = merged["irrigation_rate_pct"].corr(merged["deficit_moyen_mm"])
    print(f"\nCorrelation (Pearson) irrigation_rate_pct(r) vs deficit hydrique moyen(r) : r = {corr:.3f}")
    print("(seuil de redondance forte : r > 0.90, cf. M2 ; ici correlation moderee -> variables conservees separement)")
except FileNotFoundError:
    print("\n(donnees_ecologie.csv non trouve - verification de correlation ignoree)")
