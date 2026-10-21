"""
TerraMap Maroc - Test de robustesse au climat de référence.

Question : les recommandations changent-elles si l'on remplace le climat de l'année 2025 par le
climat moyen 2015-2024 ?

Le script
  1. collecte via Open-Meteo (API d'archive, valeurs journalières, 2015-2025) les séries de chaque capitale
     régionale, puis calcule le climat moyen 2015-2024 (température moyenne, pluie et ET0 annuelles moyennes) ;
  2. VÉRIFIE d'abord qu'il reproduit exactement score_final_explicable.csv avec le climat 2025 ;
  3. recalcule toute la chaîne (Liebig, déficit FAO-56, score écologique AHP 0,75/0,25, score final) avec
     le climat 2015-2024 et compare aux résultats de 2025.

Les fichiers d'origine ne sont JAMAIS modifiés : toutes les sorties vont dans le dossier OUT_DIR, et chaque colonne
porte le suffixe _2025 ou _2015_2024.

Utilisation :  python robustesse_climat_2015_2024.py            (mode strict : s'arrête si la reproduction échoue)
               python robustesse_climat_2015_2024.py --no-strict (continue malgré un écart de reproduction)
               python robustesse_climat_2015_2024.py --refresh   (retélécharge les données Open-Meteo)
"""
import argparse
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ----------------------------- CONFIG -----------------------------
DIR_IN = Path(__file__).resolve().parent             # dossier contenant les fichiers d'entrée
PATH_REGIONS = DIR_IN / "regions_maroc.csv"          # region_id, region, capital, latitude, longitude
PATH_EXIG = DIR_IN / "exigences_cultures.csv"        # ECOCROP
PATH_SOLS = DIR_IN / "donnees_sols.csv"              # region_id, ph, ...
PATH_ECO = DIR_IN / "donnees_ecologie.csv"           # region_id, irrigation_rate_pct (version reconstruite)
PATH_KC = DIR_IN / "kc_values.csv"                   # culture, kc_mid, source, note
PATH_CLIM_2025 = DIR_IN / "donnees_climatiques.csv"  # climat 2025 déjà collecté
PATH_BASE = DIR_IN / "score_final_explicable.csv"    # résultats de référence (2025)

OUT_DIR = Path("robustesse_climat_2015_2024")
RAW_DIR = OUT_DIR / "openmeteo_brut"                 # cache des téléchargements

YEAR_START, YEAR_END, YEAR_CHECK = 2015, 2024, 2025
WD, WI = 0.75, 0.25
ALPHAS = {"03": 0.3, "05": 0.5, "07": 0.7}
TOL = 1e-12
TOL_REPRO = 1e-6

CROP_NAME_MAPPING = {
    "Allium cepa": "Oignon", "Citrus sp.": "Agrumes", "Ficus carica": "Figuier",
    "Helianthus annuus": "Tournesol", "Hordeum vulgare": "Orge", "Lycopersicon esculentum": "Tomate",
    "Malus domestica": "Pommier", "Medicago sativa": "Luzerne", "Olea europaea": "Olivier",
    "Oryza sativa": "Riz", "Phaseolus vulgaris": "Haricot", "Phoenix dactylifera": "Palmier dattier",
    "Solanum tuberosum": "Pomme de terre", "Triticum aestivum": "Ble", "Vitis vinifera": "Vigne",
    "Zea mays": "Mais", "Prunus amygdalus": "Amandier", "Cicer arietinum": "Pois chiche",
    "Lens culinaris": "Lentille",
}
# ------------------------------------------------------------------


def norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().replace("-", " ").split())


def fetch_region(rid, lat, lon, refresh=False):
    """Séries journalières 2015-2025 d'une capitale, avec cache disque."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"region_{int(rid)}_{YEAR_START}_{YEAR_CHECK}.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, parse_dates=["time"])
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": f"{YEAR_START}-01-01", "end_date": f"{YEAR_CHECK}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "auto",
    }
    for attempt in range(1, 6):
        try:
            r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=180)
            if r.status_code == 200:
                df = pd.DataFrame(r.json()["daily"])
                df["time"] = pd.to_datetime(df["time"])
                df.to_csv(cache, index=False)
                time.sleep(1)
                return df
            wait = 65 * attempt if r.status_code == 429 else 5 * attempt
            print(f"   code {r.status_code} (essai {attempt}/5), nouvel essai dans {wait} s")
            time.sleep(wait)
        except requests.RequestException as e:
            print(f"   erreur réseau ({e}), nouvel essai")
            time.sleep(5 * attempt)
    raise RuntimeError(f"Échec de collecte pour la région {rid}")


def build_climatology(regions, refresh=False):
    rows = []
    for _, r in regions.iterrows():
        print(f"-> {r['region']} ...")
        d = fetch_region(r["region_id"], r["latitude"], r["longitude"], refresh)
        d["year"] = d["time"].dt.year
        ref = d[(d["year"] >= YEAR_START) & (d["year"] <= YEAR_END)]
        annual = ref.groupby("year").agg(rain=("precipitation_sum", "sum"), et0=("et0_fao_evapotranspiration", "sum"))
        chk = d[d["year"] == YEAR_CHECK]
        rows.append({
            "region_id": r["region_id"], "region": r["region"],
            "temp_mean_2015_2024": round(ref["temperature_2m_mean"].mean(), 2),
            "rainfall_2015_2024": round(annual["rain"].mean(), 1),
            "et0_2015_2024": round(annual["et0"].mean(), 1),
            "rainfall_min_annuelle": round(annual["rain"].min(), 1),
            "rainfall_max_annuelle": round(annual["rain"].max(), 1),
            "rainfall_cv_annuel": round(annual["rain"].std(ddof=0) / annual["rain"].mean(), 3) if annual["rain"].mean() > 0 else np.nan,
            "temp_mean_2025_journalier": round(chk["temperature_2m_mean"].mean(), 2),
            "rainfall_2025_journalier": round(chk["precipitation_sum"].sum(), 1),
            "et0_2025_journalier": round(chk["et0_fao_evapotranspiration"].sum(), 1),
        })
    return pd.DataFrame(rows)


def trapezoid(x, a, b, c, d):
    if any(pd.isna(v) for v in (x, a, b, c, d)):
        return np.nan
    if x < a or x > d:
        return 0.0
    if x < b:
        return 1.0 if b == a else (x - a) / (b - a)
    if x <= c:
        return 1.0
    return 1.0 if d == c else (d - x) / (d - c)


def compute_scores(clim, regions, sols, eco, exig, kc):
    """Chaîne complète. clim : region_id, temp_mean, rainfall, et0."""
    reg = (regions[["region_id", "region"]]
           .merge(clim[["region_id", "temp_mean", "rainfall", "et0"]], on="region_id", validate="1:1")
           .merge(sols[["region_id", "ph"]], on="region_id", validate="1:1")
           .merge(eco[["region_id", "irrigation_rate_pct"]], on="region_id", validate="1:1"))
    reg["score_irrigation"] = 1 - (reg["irrigation_rate_pct"] - reg["irrigation_rate_pct"].min()) / (
        reg["irrigation_rate_pct"].max() - reg["irrigation_rate_pct"].min())
    reg["_k"], exig = 1, exig.assign(_k=1)
    df = reg.merge(exig, on="_k").drop(columns="_k")
    df["score_temp"] = [trapezoid(r.temp_mean, r.TMIN, r.TOPMN, r.TOPMX, r.TMAX) for r in df.itertuples()]
    df["score_rainfall"] = [trapezoid(r.rainfall, r.RMIN, r.ROPMN, r.ROPMX, r.RMAX) for r in df.itertuples()]
    df["score_ph"] = [trapezoid(r.ph, r.PHMIN, r.PHOPMN, r.PHOPMX, r.PHMAX) for r in df.itertuples()]
    df["score_rendement"] = df[["score_temp", "score_rainfall", "score_ph"]].min(axis=1, skipna=False)
    df = df.merge(kc, on="key", how="left", validate="m:1")
    assert df["kc_mid"].notna().all(), "Kc manquant pour au moins une culture (vérifier les noms)"
    df["etc"] = df["kc_mid"] * df["et0"]
    df["deficit"] = (df["etc"] - df["rainfall"]).clip(lower=0)
    df["score_deficit"] = 1 - (df["deficit"] - df["deficit"].min()) / (df["deficit"].max() - df["deficit"].min())
    df["score_eco"] = WD * df["score_deficit"] + WI * df["score_irrigation"]
    for k, a in ALPHAS.items():
        df[f"score_final_alpha{k}"] = a * df["score_rendement"] + (1 - a) * df["score_eco"]
    return df


def top_sets(df, col):
    out = {}
    for rid, g in df.groupby("region_id", sort=False):
        m = g[col].max()
        out[rid] = sorted(g.loc[g[col] >= m - TOL, "culture"])
    return out


def spearman(x, y):
    return x.rank().corr(y.rank())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-strict", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regions = pd.read_csv(PATH_REGIONS)
    sols = pd.read_csv(PATH_SOLS)
    eco = pd.read_csv(PATH_ECO)
    exig = pd.read_csv(PATH_EXIG)
    exig["culture"] = exig["ScientificName"].map(CROP_NAME_MAPPING)
    assert exig["culture"].notna().all(), "ScientificName absent du dictionnaire CROP_NAME_MAPPING"
    exig["key"] = exig["culture"].map(norm)
    kc = pd.read_csv(PATH_KC)[["culture", "kc_mid"]].rename(columns={"culture": "culture_kc"})
    kc["key"] = kc["culture_kc"].map(norm)
    kc = kc[["key", "kc_mid"]]
    base = pd.read_csv(PATH_BASE)
    base["key"] = base["culture"].map(norm)

    # ---- 1. Climat 2025 (existant) et reproduction de la référence -------------------------------------
    c25 = pd.read_csv(PATH_CLIM_2025)
    et_col = "et0_fao_evapotranspiration" if "et0_fao_evapotranspiration" in c25.columns else "evapotranspiration"
    c25 = c25.rename(columns={et_col: "et0"})[["region_id", "temp_mean", "rainfall", "et0"]]
    s25 = compute_scores(c25, regions, sols, eco, exig, kc)
    cmp = s25.merge(base, on=["region_id", "key"], suffixes=("", "_base"), validate="1:1")
    ok = True
    for col in ["score_rendement", "score_eco"] + [f"score_final_alpha{k}" for k in ALPHAS]:
        diff = (cmp[col] - cmp[f"{col}_base"]).abs().max()
        print(f"[REPRODUCTION] {col}: écart max = {diff:.2e}")
        ok &= bool(diff < TOL_REPRO)
    print("[REPRODUCTION]", "RÉUSSIE" if ok else "ÉCHOUÉE")
    if not ok and not args.no_strict:
        print("Arrêt : la chaîne recalculée ne reproduit pas score_final_explicable.csv. "
              "Vérifier les fichiers d'entrée (ou relancer avec --no-strict pour diagnostiquer).")
        sys.exit(1)

    # ---- 2. Climat moyen 2015-2024 ---------------------------------------------------------------------
    print("\nCollecte Open-Meteo (une requête par région, cache dans", RAW_DIR, ") ...")
    clim = build_climatology(regions, refresh=args.refresh)
    clim.to_csv(OUT_DIR / "donnees_climatiques_2015_2024.csv", index=False, encoding="utf-8-sig")

    cc = clim.merge(c25, on="region_id", validate="1:1")
    cc["ratio_pluie_2025_sur_moy"] = (cc["rainfall"] / cc["rainfall_2015_2024"]).round(2)
    cc["ratio_et0_2025_sur_moy"] = (cc["et0"] / cc["et0_2015_2024"]).round(2)
    cc["ecart_pluie_methode_journalier_vs_horaire_mm"] = (cc["rainfall_2025_journalier"] - cc["rainfall"]).round(1)
    cc = cc.rename(columns={"temp_mean": "temp_mean_2025", "rainfall": "rainfall_2025", "et0": "et0_2025"})
    cc.to_csv(OUT_DIR / "comparaison_climat_2025_vs_2015_2024.csv", index=False, encoding="utf-8-sig")
    print("\n=== Climat : 2025 contre moyenne 2015-2024 ===")
    print(cc[["region", "rainfall_2025", "rainfall_2015_2024", "ratio_pluie_2025_sur_moy", "rainfall_cv_annuel",
              "et0_2025", "et0_2015_2024"]].to_string(index=False))

    # ---- 3. Scores avec le climat 2015-2024 ------------------------------------------------------------
    cm = clim.rename(columns={"temp_mean_2015_2024": "temp_mean", "rainfall_2015_2024": "rainfall",
                              "et0_2015_2024": "et0"})[["region_id", "temp_mean", "rainfall", "et0"]]
    sm = compute_scores(cm, regions, sols, eco, exig, kc)

    keep = ["region_id", "region", "culture", "key", "score_rendement", "score_eco"] + [f"score_final_alpha{k}" for k in ALPHAS]
    a = s25[keep].rename(columns={c: f"{c}_2025" for c in keep[4:]})
    b = sm[keep].rename(columns={c: f"{c}_2015_2024" for c in keep[4:]})
    both = a.merge(b.drop(columns=["region", "culture"]), on=["region_id", "key"], validate="1:1").drop(columns="key")
    both.to_csv(OUT_DIR / "comparaison_scores_2025_vs_2015_2024.csv", index=False, encoding="utf-8-sig")
    sm.drop(columns=["key"]).to_csv(OUT_DIR / "scores_complets_clim_2015_2024.csv", index=False, encoding="utf-8-sig")

    # ---- 4. Recommandations et indicateurs de robustesse -----------------------------------------------
    rec_rows, synth = [], []
    for k, alpha in ALPHAS.items():
        t25 = top_sets(s25, f"score_final_alpha{k}")
        tm = top_sets(sm, f"score_final_alpha{k}")
        same, rhos = 0, []
        for rid in t25:
            ident = bool(set(t25[rid]) & set(tm[rid]))
            same += ident
            name = regions.loc[regions.region_id == rid, "region"].iloc[0]
            rec_rows.append({"region_id": rid, "region": name, "alpha": alpha,
                             "recommandation_2025": " | ".join(t25[rid]),
                             "recommandation_2015_2024": " | ".join(tm[rid]), "identique": ident})
            g = both[both.region_id == rid]
            rhos.append(spearman(g[f"score_final_alpha{k}_2025"], g[f"score_final_alpha{k}_2015_2024"]))
        synth.append({
            "alpha": alpha,
            "regions_recommandation_identique": f"{same}/12",
            "spearman_moyen_classements": round(float(np.nanmean(rhos)), 3),
            "spearman_min_classements": round(float(np.nanmin(rhos)), 3),
            "ecart_moyen_abs_score_final": round(float((both[f"score_final_alpha{k}_2025"] -
                                                         both[f"score_final_alpha{k}_2015_2024"]).abs().mean()), 3),
        })
    rec = pd.DataFrame(rec_rows)
    rec.to_csv(OUT_DIR / "recommandations_2025_vs_2015_2024.csv", index=False, encoding="utf-8-sig")
    sy = pd.DataFrame(synth)
    z25, zm = int((s25["score_rendement"] == 0).sum()), int((sm["score_rendement"] == 0).sum())
    sy["couples_rendement_nul_2025"] = z25
    sy["couples_rendement_nul_2015_2024"] = zm
    sy.to_csv(OUT_DIR / "synthese_robustesse_climat.csv", index=False, encoding="utf-8-sig")

    print("\n=== Synthèse de robustesse ===")
    print(sy.to_string(index=False))
    print("\n=== Régions dont la recommandation change ===")
    ch = rec[~rec["identique"]]
    print(ch.to_string(index=False) if len(ch) else "aucune")
    print(f"\nFichiers écrits dans : {OUT_DIR}/ (aucun fichier d'entrée n'a été modifié)")


if __name__ == "__main__":
    main()
