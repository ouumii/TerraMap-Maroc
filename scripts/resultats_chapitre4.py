"""
TerraMap Maroc - Production des tableaux et figures du chapitre 4 (Résultats).

Entrée principale (obligatoire) : score_final_explicable.csv
Entrées optionnelles (les sections correspondantes sont ignorées si absentes) :
  - sensibilite_wd_synthese.csv, sensibilite_alpha_synthese.csv   (4.6)
  - donnees_climatiques.csv, donnees_sols.csv, donnees_ecologie.csv (4.2)

Sorties dans OUT_DIR : tableaux CSV (T4.x) et figures PNG 300 dpi (F4.x).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------- CONFIG -----------------------------
PATH_SCORES = "D:\\terramap_maroc\\data_processed\\score_final_explicable.csv"
PATH_WD = "D:\\terramap_maroc\\sorties_sensibilite\\sensibilite_wd_synthese.csv"
PATH_ALPHA = "D:\\terramap_maroc\\sorties_sensibilite\\sensibilite_alpha_synthese.csv"
PATH_CLIMAT = "D:\\terramap_maroc\\data_processed\\donnees_climatiques.csv"
PATH_SOLS = "D:\\terramap_maroc\\data_processed\\donnees_sols.csv"
PATH_ECO = "D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv"
OUT_DIR = "D:\\terramap_maroc\\sorties_resultats_ch4"
DPI = 300
ALPHAS = {"03": 0.3, "05": 0.5, "07": 0.7}
TOL = 1e-9
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
# ------------------------------------------------------------------


def save_table(df, name):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  -> {name} ({len(df)} lignes)")


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, name), dpi=DPI)
    plt.close(fig)
    print(f"  -> {name}")


def t41_qualite(s):
    print("\n[4.1] Qualité des données et contrôles de cohérence")
    checks = []
    checks.append(("Régions", s["region"].nunique()))
    checks.append(("Cultures", s["culture"].nunique()))
    checks.append(("Couples région-culture", len(s)))
    checks.append(("Doublons (région, culture)", int(s.duplicated(["region", "culture"]).sum())))
    cols = ["score_rendement", "score_eco"] + [f"score_final_alpha{k}" for k in ALPHAS]
    checks.append(("Valeurs manquantes dans les scores", int(s[cols].isna().sum().sum())))
    checks.append(("Scores hors [0,1]", int(((s[cols] < -TOL) | (s[cols] > 1 + TOL)).sum().sum())))
    mn = s[["score_temp", "score_rainfall", "score_ph"]].min(axis=1)
    checks.append(("Écart max S_rend vs min des 3 scores", float((mn - s["score_rendement"]).abs().max())))
    for k, a in ALPHAS.items():
        recomp = a * s["score_rendement"] + (1 - a) * s["score_eco"]
        checks.append((f"Écart max score final alpha={a}", float((recomp - s[f"score_final_alpha{k}"]).abs().max())))
        ok = s.groupby("region").apply(
            lambda g: g.sort_values(f"rang_alpha{k}")[f"score_final_alpha{k}"].is_monotonic_decreasing).all()
        checks.append((f"Rangs cohérents alpha={a}", bool(ok)))
    t = pd.DataFrame(checks, columns=["controle", "resultat"])
    print(t.to_string(index=False))
    save_table(t, "T4.1_controles_coherence.csv")


def t42_regions():
    if not all(os.path.exists(p) for p in (PATH_CLIMAT, PATH_SOLS, PATH_ECO)):
        print("\n[4.2] Fichiers régionaux absents : section ignorée.")
        return
    print("\n[4.2] Caractérisation des régions")
    c, so, e = pd.read_csv(PATH_CLIMAT), pd.read_csv(PATH_SOLS), pd.read_csv(PATH_ECO)
    t = c[["region_id", "region", "temp_mean", "rainfall", "et0_fao_evapotranspiration"]].merge(
        so[["region_id", "ph", "clay", "organic_carbon"]], on="region_id")
    if "irrigation_rate_pct" in e.columns:
        t = t.merge(e[["region_id", "irrigation_rate_pct"]], on="region_id")
    else:
        print("  (colonne irrigation_rate_pct absente : fichier écologie ancien ?)")
    print(t.round(2).to_string(index=False))
    save_table(t.round(3), "T4.2_caracterisation_regions.csv")


def t43_rendement(s):
    print("\n[4.3] Score de rendement")
    fl = s["facteur_limitant"].value_counts().rename_axis("facteur_limitant").reset_index(name="nb_couples")
    fl["part_%"] = (100 * fl["nb_couples"] / len(s)).round(1)
    print(fl.to_string(index=False))
    save_table(fl, "T4.3a_facteurs_limitants.csv")

    par_reg = s.groupby("region").agg(
        nb_rend_nul=("score_rendement", lambda x: int((x == 0).sum())),
        nb_rend_max=("score_rendement", lambda x: int((x >= 1 - TOL).sum())),
        rend_moyen=("score_rendement", "mean")).round(3).reset_index()
    print(par_reg.to_string(index=False))
    print(f"Couples à score de rendement nul : {int((s.score_rendement == 0).sum())}/{len(s)}")
    save_table(par_reg, "T4.3b_rendement_par_region.csv")

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].hist(s["score_rendement"], bins=20, color="#c08a2e", edgecolor="white")
    ax[0].set(xlabel="Score de rendement", ylabel="Nombre de couples", title="Distribution du score de rendement")
    ax[1].barh(fl["facteur_limitant"][::-1], fl["nb_couples"][::-1], color="#2f4b7c")
    ax[1].set(xlabel="Nombre de couples", title="Facteur limitant")
    save_fig(fig, "F4.1_rendement_distribution_facteurs.png")


def t44_eco(s):
    print("\n[4.4] Score écologique (w_d = 0,75 ; w_i = 0,25)")
    par_reg = s.groupby("region")["score_eco"].agg(["min", "mean", "max"]).round(3).reset_index()
    print(par_reg.to_string(index=False))
    save_table(par_reg, "T4.4a_eco_par_region.csv")
    top = s.nlargest(5, "score_eco")[["region", "culture", "score_eco"]]
    bot = s.nsmallest(5, "score_eco")[["region", "culture", "score_eco"]]
    print("\nTop 5 écologique :\n", top.round(3).to_string(index=False))
    print("\nBas 5 écologique :\n", bot.round(3).to_string(index=False))
    save_table(pd.concat([top.assign(rang="meilleurs"), bot.assign(rang="moins favorables")]).round(3),
               "T4.4b_eco_extremes.csv")
    moy_cult = s.groupby("culture")["score_eco"].mean().sort_values().round(3)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    ax[0].hist(s["score_eco"], bins=20, color="#4c8c5a", edgecolor="white")
    ax[0].set(xlabel="Score écologique", ylabel="Nombre de couples", title="Distribution du score écologique")
    ax[1].barh(moy_cult.index, moy_cult.values, color="#4c8c5a")
    ax[1].set(xlabel="Score écologique moyen (12 régions)", title="Par culture")
    save_fig(fig, "F4.2_eco_distribution_cultures.png")


def t45_final(s):
    print("\n[4.5] Score final et recommandations")
    blocs = []
    for k, a in ALPHAS.items():
        b = s[s[f"rang_alpha{k}"] == 1][["region", "culture", "score_rendement", "score_eco",
                                          f"score_final_alpha{k}", f"ecart_score_suivant_alpha{k}",
                                          f"composante_dominante_alpha{k}"]].copy()
        b.columns = ["region", "culture_recommandee", "score_rendement", "score_eco", "score_final",
                     "ecart_au_second", "composante_dominante"]
        b.insert(1, "alpha", a)
        blocs.append(b)
    rec = pd.concat(blocs).round(3)
    save_table(rec, "T4.5a_recommandations_long.csv")
    wide = rec.pivot(index="region", columns="alpha", values="culture_recommandee")
    wide.columns = [f"alpha_{c}" for c in wide.columns]
    wide["stable_3_scenarios"] = wide.nunique(axis=1) == 1
    wide = wide.reset_index()
    print(wide.to_string(index=False))
    save_table(wide, "T4.5b_recommandations_par_region.csv")
    print("\nFréquence des cultures recommandées (36 recommandations) :")
    print(rec["culture_recommandee"].value_counts().to_string())
    print("\nRecommandations à écart < 0,02 avec la 2e culture :")
    fragile = rec[rec["ecart_au_second"] < 0.02][["region", "alpha", "culture_recommandee", "ecart_au_second"]]
    print(fragile.to_string(index=False))
    save_table(fragile, "T4.5c_recommandations_fragiles.csv")

    # Heatmap région x culture (alpha = 0,5)
    piv = s.pivot(index="region", columns="culture", values="score_final_alpha05")
    order = piv.mean(axis=0).sort_values(ascending=False).index
    piv = piv[order]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    im = ax.imshow(piv.values, cmap="YlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns, rotation=60, ha="right")
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels(piv.index)
    for i, reg in enumerate(piv.index):
        j = list(piv.columns).index(s[(s.region == reg) & (s.rang_alpha05 == 1)].culture.iloc[0])
        ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec="#b03030", lw=1.8))
    fig.colorbar(im, ax=ax, label="Score final (alpha = 0,5)", fraction=0.03)
    ax.set_title("Score final par région et culture (cadre rouge : culture recommandée)")
    save_fig(fig, "F4.3_heatmap_score_final_alpha05.png")


def t46_sensibilite():
    print("\n[4.6] Sensibilité")
    if os.path.exists(PATH_WD):
        w = pd.read_csv(PATH_WD).dropna(subset=["region"])
        piv = w.pivot(index="region", columns="alpha", values="tau_w")
        print(piv.round(2).to_string())
        print(w.groupby("alpha")["classe"].value_counts().unstack(fill_value=0).to_string())
        fig, ax = plt.subplots(figsize=(4.6, 4.2))
        im = ax.imshow(piv.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels([f"{c:g}" for c in piv.columns])
        ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index)
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                ax.text(j, i, f"{piv.values[i, j]:.2f}", ha="center", va="center", fontsize=7)
        ax.set(xlabel="alpha", title="Stabilité τ_w (w_d de 0,50 à 0,90)")
        fig.colorbar(im, ax=ax, fraction=0.05)
        save_fig(fig, "F4.4_stabilite_tau_w.png")
    else:
        print("  sensibilite_wd_synthese.csv absent : τ_w ignoré.")
    if os.path.exists(PATH_ALPHA):
        a = pd.read_csv(PATH_ALPHA).dropna(subset=["region"]).sort_values("tau_alpha")
        print(a.round(2).to_string(index=False))
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.barh(a["region"], a["tau_alpha"], color="#2f4b7c")
        ax.axvline(0.8, ls="--", c="#4c8c5a", lw=1); ax.axvline(0.5, ls="--", c="#b03030", lw=1)
        ax.set(xlabel="Taux de stabilité τ_α (α de 0 à 1, référence α = 0,5)", xlim=(0, 1.05),
               title="Stabilité de la recommandation selon α")
        save_fig(fig, "F4.5_stabilite_tau_alpha.png")
    else:
        print("  sensibilite_alpha_synthese.csv absent : τ_α ignoré.")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    s = pd.read_csv(PATH_SCORES)
    t41_qualite(s)
    t42_regions()
    t43_rendement(s)
    t44_eco(s)
    t45_final(s)
    t46_sensibilite()
    print(f"\nTerminé. Fichiers dans {OUT_DIR}/")


if __name__ == "__main__":
    main()
