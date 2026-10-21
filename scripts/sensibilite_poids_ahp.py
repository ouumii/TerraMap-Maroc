"""
TerraMap Maroc - Analyse de sensibilité aux poids AHP (w_d) et à alpha.

Entrées (adapter les chemins et noms de colonnes dans la section CONFIG) :
  - score_rendement_r_c.csv      : region, culture, score_rendement
  - deficit_hydrique_r_c.csv     : region, culture, score_deficit
  - donnees_ecologie.csv         : region, irrigation_rate_pct  (version reconstruite, Atlas RGA 2016)
  - score_final_explicable.csv   : (optionnel) sert au test de reproduction à w_d = 0,75

Sorties (dossier OUT_DIR) :
  - sensibilite_wd_detail.csv    : culture recommandée par région, alpha et w_d
  - sensibilite_wd_synthese.csv  : taux de stabilité tau_w et classe par région et alpha
  - sensibilite_alpha_detail.csv : culture recommandée par région et alpha (0 à 1, pas 0,05)
  - sensibilite_alpha_synthese.csv : taux de stabilité tau_alpha par région
"""
import os
import numpy as np
import pandas as pd

# ----------------------------- CONFIG -----------------------------
PATH_REND = "D:\\terramap_maroc\\data_processed\\score_rendement_r_c.csv"
PATH_DEF = "D:\\terramap_maroc\\data_processed\\deficit_hydrique_r_c.csv"
PATH_ECO = "D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv"
PATH_REF = "D:\\terramap_maroc\\data_processed\\score_final_explicable.csv"   # mettre None si indisponible
OUT_DIR = "D:\\terramap_maroc\\sorties_sensibilite"

COL_REGION, COL_CULTURE = "region", "culture"
COL_REND = "score_rendement"
COL_DEF = "score_deficit"                 # à vérifier dans deficit_hydrique_r_c.csv
COL_IRR = "irrigation_rate_pct"

WD_REF = 0.75
WD_GRID = np.round(np.arange(0.50, 0.9001, 0.05), 2)      # 9 valeurs
ALPHAS = [0.3, 0.5, 0.7]
ALPHA_GRID = np.round(np.arange(0.0, 1.0001, 0.05), 2)    # 21 valeurs
ALPHA_REF_SWEEP = 0.5
SEUIL_ROBUSTE, SEUIL_INTERMEDIAIRE = 0.80, 0.50           # à valider avec l'encadrant
TOL = 1e-12
# ------------------------------------------------------------------


def alpha_tag(a):
    return f"alpha{int(round(a * 100)):02d}"


def minmax(s):
    return (s - s.min()) / (s.max() - s.min())


def charger():
    rend = pd.read_csv(PATH_REND)[[COL_REGION, COL_CULTURE, COL_REND]]
    dfc = pd.read_csv(PATH_DEF)[[COL_REGION, COL_CULTURE, COL_DEF]]
    eco = pd.read_csv(PATH_ECO)[[COL_REGION, COL_IRR]]
    for d in (rend, dfc, eco):
        d[COL_REGION] = d[COL_REGION].astype(str).str.strip()
    for d in (rend, dfc):
        d[COL_CULTURE] = d[COL_CULTURE].astype(str).str.strip()

    df = RENDEMENTmerge(dfc, on=[COL_REGION, COL_CULTURE], how="inner", validate="1:1")
    df = df.merge(eco, on=COL_REGION, how="left", validate="m:1")
    assert len(df) == 228, f"228 couples attendus, {len(df)} trouvés (vérifier noms régions/cultures)"
    assert df[COL_IRR].notna().all(), "taux d'irrigation manquant pour au moins une région"
    # Score_irrigation : Min-Max inversé calculé sur les 12 régions
    eco_u = eco.drop_duplicates(COL_REGION).copy()
    eco_u["score_irrigation"] = 1 - minmax(eco_u[COL_IRR])
    df = df.merge(eco_u[[COL_REGION, "score_irrigation"]], on=COL_REGION)
    return df


def score_final(df, alpha, wd):
    eco = wd * df[COL_DEF] + (1 - wd) * df["score_irrigation"]
    return alpha * df[COL_REND] + (1 - alpha) * eco


def recommander(df, score):
    """Culture au score maximal par région ; avertit en cas d'égalité au premier rang."""
    tmp = df[[COL_REGION, COL_CULTURE]].assign(s=score.values)
    reco, ties = {}, []
    for reg, g in tmp.groupby(COL_REGION, sort=False):
        m = g["s"].max()
        top = g[g["s"] >= m - TOL]
        reco[reg] = top.iloc[0][COL_CULTURE]
        if len(top) > 1:
            ties.append(reg)
    return pd.Series(reco), ties


def ensembles_premiers(df, score):
    """Ensemble des cultures à égalité au premier rang, par région (règle 3.5 : pas de départage arbitraire)."""
    tmp = df[[COL_REGION, COL_CULTURE]].assign(s=score.values)
    out = {}
    for reg, g in tmp.groupby(COL_REGION, sort=False):
        m = g["s"].max()
        out[reg] = list(g[g["s"] >= m - TOL][COL_CULTURE])
    return out


def test_reproduction(df):
    """À w_d = 0,75, retrouver les recommandations et scores du fichier de référence."""
    if not PATH_REF or not os.path.exists(PATH_REF):
        print("[TEST] fichier de référence absent : test de reproduction ignoré.")
        return
    ref = pd.read_csv(PATH_REF)
    ref[COL_REGION] = ref[COL_REGION].astype(str).str.strip()
    ref[COL_CULTURE] = ref[COL_CULTURE].astype(str).str.strip()
    ok = True
    for a in ALPHAS:
        tag = alpha_tag(a).replace("alpha", "alpha")
        col_score = f"score_final_{tag}"
        col_reco = f"culture_recommandee_{tag}"
        if col_score in ref.columns:
            m = df.merge(ref[[COL_REGION, COL_CULTURE, col_score]], on=[COL_REGION, COL_CULTURE])
            ecart = (score_final(m, a, WD_REF) - m[col_score]).abs().max()
            print(f"[TEST] alpha={a}: écart max sur les scores finaux = {ecart:.2e}")
            ok &= ecart < 1e-6
        if col_reco in ref.columns:
            mine, _ = recommander(df, score_final(df, a, WD_REF))
            theirs = ref.drop_duplicates(COL_REGION).set_index(COL_REGION)[col_reco]
            diff = [r for r in mine.index if mine[r] != theirs.get(r)]
            print(f"[TEST] alpha={a}: régions dont la recommandation diffère = {diff or 'aucune'}")
            ok &= not diff
    print("[TEST] reproduction", "RÉUSSIE" if ok else "ÉCHOUÉE : corriger avant d'interpréter la sensibilité")


def test_equivalence_alpha_prime(df):
    """Vérifie que le classement intra-région ne dépend que de alpha' = a/(a+(1-a)*w_d)."""
    bad = 0
    for a in ALPHAS:
        for wd in WD_GRID:
            r1, _ = recommander(df, score_final(df, a, wd))
            ap = a / (a + (1 - a) * wd)
            r2, _ = recommander(df, ap * df[COL_REND] + (1 - ap) * df[COL_DEF])
            bad += int((r1 != r2).sum())
    print(f"[TEST] équivalence alpha' : {bad} écart(s) (0 attendu)")


def classe(tau):
    if tau >= SEUIL_ROBUSTE:
        return "robuste"
    return "intermédiaire" if tau >= SEUIL_INTERMEDIAIRE else "sensible"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = charger()
    test_reproduction(df)
    test_equivalence_alpha_prime(df)

    # ---- Sensibilité à w_d (pour chaque alpha de présentation) ----
    rows = []
    for a in ALPHAS:
        ref_reco, _ = recommander(df, score_final(df, a, WD_REF))
        for wd in WD_GRID:
            tops = ensembles_premiers(df, score_final(df, a, wd))
            for reg, cults in tops.items():
                rows.append({"region": reg, "alpha": a, "w_d": wd, "culture_recommandee": " | ".join(cults),
                             "culture_reference": ref_reco[reg],
                             "n_ex_aequo": len(cults),
                             # conservée si la culture de référence figure parmi les cultures à égalité au premier rang
                             "identique_reference": ref_reco[reg] in cults})
    det = pd.DataFrame(rows)
    det.to_csv(os.path.join(OUT_DIR, "sensibilite_wd_detail.csv"), index=False, encoding="utf-8-sig")
    syn = (det.groupby(["region", "alpha"])["identique_reference"].mean()
              .rename("tau_w").reset_index())
    syn["classe"] = syn["tau_w"].apply(classe)
    syn.to_csv(os.path.join(OUT_DIR, "sensibilite_wd_synthese.csv"), index=False, encoding="utf-8-sig")
    print("\n=== tau_w par région et alpha (w_d de 0,50 à 0,90) ===")
    print(syn.pivot(index="region", columns="alpha", values="tau_w").round(2).to_string())
    print("\nRépartition des classes :")
    print(syn.groupby("alpha")["classe"].value_counts().unstack(fill_value=0).to_string())

    # ---- Sensibilité à alpha (w_d = 0,75) ----
    ref_reco, _ = recommander(df, score_final(df, ALPHA_REF_SWEEP, WD_REF))
    rows = []
    for a in ALPHA_GRID:
        tops = ensembles_premiers(df, score_final(df, a, WD_REF))
        for reg, cults in tops.items():
            rows.append({"region": reg, "alpha": a, "culture_recommandee": " | ".join(cults),
                         "n_ex_aequo": len(cults),
                         "identique_reference": ref_reco[reg] in cults})
    da = pd.DataFrame(rows)
    da.to_csv(os.path.join(OUT_DIR, "sensibilite_alpha_detail.csv"), index=False, encoding="utf-8-sig")
    sa = da.groupby("region").agg(tau_alpha=("identique_reference", "mean"),
                                  nb_alpha_avec_ex_aequo=("n_ex_aequo", lambda x: int((x > 1).sum()))).reset_index()
    sa["classe"] = sa["tau_alpha"].apply(classe)
    sa.to_csv(os.path.join(OUT_DIR, "sensibilite_alpha_synthese.csv"), index=False, encoding="utf-8-sig")
    print("\n=== tau_alpha par région (alpha de 0 à 1, référence alpha = 0,5) ===")
    print(sa.round(2).to_string(index=False))
    print(f"\nFichiers écrits dans : {OUT_DIR}/")


if __name__ == "__main__":
    main()