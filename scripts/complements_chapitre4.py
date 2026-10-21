"""
TerraMap Maroc - Compléments du chapitre 4.

  4.4.4 : contributions moyennes du déficit hydrique (w_d x S_deficit) et de la pression
          d'irrigation (w_i x S_irrig) au score écologique, par région.
  4.6.3 : valeurs de alpha auxquelles la culture recommandée change (zone de compromis).

Entrées :
  - score_final_explicable.csv : region, culture, score_rendement, score_eco
  - donnees_ecologie.csv       : region, irrigation_rate_pct  (version reconstruite, Atlas RGA 2016)

Remarque : S_deficit n'est pas relu depuis un autre fichier : il est reconstitué par
S_deficit = (S_eco - w_i x S_irrig) / w_d, ce qui évite toute dépendance aux noms de colonnes
de deficit_hydrique_r_c.csv. Le script vérifie que les valeurs restent dans [0, 1].
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------- CONFIG -----------------------------
PATH_SCORES = "D:\\terramap_maroc\\data_processed\\score_final_explicable.csv"
PATH_ECO = "D:\\terramap_maroc\\data_processed\\donnees_ecologie.csv"
OUT_DIR = "D:\\terramap_maroc\\sorties_complements_ch4"
COL_IRR = "irrigation_rate_pct"
WD, WI = 0.75, 0.25
DPI = 300
STEP = 0.001          # pas de la grille fine sur alpha (intervalle ouvert ]0, 1[)
TOL = 1e-12
# ------------------------------------------------------------------
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def save_table(df, name):
    df.to_csv(os.path.join(OUT_DIR, name), index=False, encoding="utf-8-sig")
    print(f"  -> {name} ({len(df)} lignes)")


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, name), dpi=DPI)
    plt.close(fig)
    print(f"  -> {name}")


def contributions(s):
    print("\n[4.4.4] Contributions au score écologique (w_d = 0,75 ; w_i = 0,25)")
    if not os.path.exists(PATH_ECO):
        print("  donnees_ecologie.csv absent : section ignorée.")
        return
    e = pd.read_csv(PATH_ECO)[["region", COL_IRR]].drop_duplicates("region")
    e["region"] = e["region"].astype(str).str.strip()
    e["score_irrig"] = 1 - (e[COL_IRR] - e[COL_IRR].min()) / (e[COL_IRR].max() - e[COL_IRR].min())
    d = s.merge(e[["region", "score_irrig"]], on="region", how="left", validate="m:1")
    assert d["score_irrig"].notna().all(), "région sans taux d'irrigation (vérifier les noms)"
    d["score_deficit"] = (d["score_eco"] - WI * d["score_irrig"]) / WD
    hors = int(((d["score_deficit"] < -1e-9) | (d["score_deficit"] > 1 + 1e-9)).sum())
    print(f"  Contrôle : S_deficit reconstitué hors de [0,1] pour {hors} couple(s) (0 attendu)")
    g = d.groupby("region").agg(score_irrig=("score_irrig", "first"),
                                score_deficit_moyen=("score_deficit", "mean"),
                                score_eco_moyen=("score_eco", "mean")).reset_index()
    g["contrib_deficit"] = WD * g["score_deficit_moyen"]
    g["contrib_irrigation"] = WI * g["score_irrig"]
    g["part_deficit_%"] = 100 * g["contrib_deficit"] / g["score_eco_moyen"]
    g = g.sort_values("score_eco_moyen", ascending=False)
    print(g.round(3).to_string(index=False))
    print(f"\n  Score écologique moyen (228 couples) : {s['score_eco'].mean():.3f}")
    print(f"  Contribution moyenne du déficit      : {g['contrib_deficit'].mean():.3f}")
    print(f"  Contribution moyenne de l'irrigation : {g['contrib_irrigation'].mean():.3f}")
    save_table(g.round(4), "T4.4c_contributions_eco.csv")

    fig, ax = plt.subplots(figsize=(7, 4))
    y = np.arange(len(g))[::-1]
    ax.barh(y, g["contrib_deficit"], color="#2f4b7c", label="Déficit hydrique (w_d × S_déficit)")
    ax.barh(y, g["contrib_irrigation"], left=g["contrib_deficit"], color="#4c8c5a",
            label="Pression d'irrigation (w_i × S_irrig)")
    ax.set_yticks(y)
    ax.set_yticklabels(g["region"])
    ax.set(xlabel="Contribution moyenne au score écologique", xlim=(0, 1),
           title="Décomposition du score écologique par région")
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    save_fig(fig, "F4.6_contributions_score_eco.png")


def top_set(R, E, a, cultures):
    sc = a * R + (1 - a) * E
    return sc.argmax()


def bascules(s):
    print("\n[4.6.3] Valeurs de alpha où la recommandation change")
    grid = np.round(np.arange(STEP, 1 - STEP / 2, STEP), 6)
    rows_int, rows_sw = [], []
    for reg, g in s.groupby("region", sort=False):
        cultures = g["culture"].values
        R, E = g["score_rendement"].values, g["score_eco"].values
        winners = [cultures[(a * R + (1 - a) * E).argmax()] for a in grid]
        start = 0
        for i in range(1, len(grid) + 1):
            if i == len(grid) or winners[i] != winners[start]:
                rows_int.append({"region": reg, "culture": winners[start],
                                 "alpha_debut": 0.0 if start == 0 else None,
                                 "alpha_fin": 1.0 if i == len(grid) else None})
                if i < len(grid):
                    a_c, b_c = winners[start], winners[i]
                    ia, ib = list(cultures).index(a_c), list(cultures).index(b_c)
                    den = (R[ia] - E[ia]) - (R[ib] - E[ib])
                    a_star = (E[ib] - E[ia]) / den if abs(den) > TOL else np.nan
                    rows_sw.append({"region": reg, "de": a_c, "vers": b_c, "alpha_bascule": round(a_star, 4)})
                start = i
    sw = pd.DataFrame(rows_sw)
    # intervalles : bornes = points de bascule
    ints = []
    for reg, g in pd.DataFrame(rows_int).groupby("region", sort=False):
        bounds = [0.0] + list(sw.loc[sw.region == reg, "alpha_bascule"]) + [1.0]
        for k, (_, r) in enumerate(g.iterrows()):
            ints.append({"region": reg, "culture": r["culture"],
                         "alpha_debut": bounds[k], "alpha_fin": bounds[k + 1]})
    ints = pd.DataFrame(ints)
    nb = ints.groupby("region").size().rename("nb_cultures_recommandees").reset_index()
    print("Points de bascule (alpha) :")
    print(sw.to_string(index=False) if len(sw) else "  aucun")
    print("\nNombre de cultures successivement recommandées sur ]0, 1[ :")
    print(nb.to_string(index=False))
    save_table(ints, "T4.6c_intervalles_recommandation.csv")
    save_table(sw, "T4.6d_bascules_alpha.csv")

    cult = sorted(ints["culture"].unique())
    cmap = plt.get_cmap("tab20")
    col = {c: cmap(i % 20) for i, c in enumerate(cult)}
    regs = list(s["region"].drop_duplicates())
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for yi, reg in enumerate(regs[::-1]):
        for _, r in ints[ints.region == reg].iterrows():
            ax.barh(yi, r["alpha_fin"] - r["alpha_debut"], left=r["alpha_debut"], color=col[r["culture"]],
                    edgecolor="white", height=0.7)
            if r["alpha_fin"] - r["alpha_debut"] > 0.12:
                ax.text((r["alpha_debut"] + r["alpha_fin"]) / 2, yi, r["culture"], ha="center", va="center",
                        fontsize=7)
    for a in (0.3, 0.5, 0.7):
        ax.axvline(a, ls="--", c="black", lw=0.8)
    ax.set_yticks(range(len(regs)))
    ax.set_yticklabels(regs[::-1])
    ax.set(xlim=(0, 1), xlabel="α (poids du rendement)",
           title="Culture recommandée selon α (traits : scénarios 0,3 ; 0,5 ; 0,7)")
    save_fig(fig, "F4.7_recommandation_selon_alpha.png")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    s = pd.read_csv(PATH_SCORES)
    s["region"] = s["region"].astype(str).str.strip()
    contributions(s)
    bascules(s)
    print(f"\nTerminé. Fichiers dans {OUT_DIR}/")


if __name__ == "__main__":
    main()
