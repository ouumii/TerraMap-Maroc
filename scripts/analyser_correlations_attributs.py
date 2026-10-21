"""
TerraMap Maroc — Analyse de corrélation entre attributs régionaux (Phase M2)

Utilise la matrice NEUTRE (sans inversion) pour l'exploration statistique,
conformément à la séparation exploration / scoring décidée en M2.

Objectifs :
  - Calculer la matrice de corrélation (Pearson) entre tous les attributs
  - Repérer les paires fortement corrélées (redondance potentielle entre
    critères) : utile pour éviter le double comptage lors de la pondération
    AHP en M3/M4
  - Produire une heatmap pour le mémoire

Entrée  : matrice_normalisee_neutre.csv
Sorties : correlation_attributs.csv (matrice complète)
          heatmap_correlation.png (visualisation)
          Liste des paires fortement corrélées affichée en console
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT_FILE = Path(r"D:\terramap_maroc\data_processed\matrice_normalisee_neutre.csv")
OUTPUT_CSV = Path(r"D:\terramap_maroc\data_processed\correlation_attributs.csv")
OUTPUT_HEATMAP = Path(r"D:\terramap_maroc\data_processed\heatmap_correlation.png")

COLONNES_EXCLUES = ["region_id", "region", "capital", "latitude", "longitude", "source_doc", "annee","note", "score_irrigation"]

# Seuil au-delà duquel une corrélation est considérée comme forte
SEUIL_FORTE_CORRELATION = 0.7


def calculer_correlations(matrice: pd.DataFrame) -> pd.DataFrame:
    colonnes_numeriques = [c for c in matrice.columns if c not in COLONNES_EXCLUES]
    return matrice[colonnes_numeriques].corr(method="pearson")


def lister_paires_fortes(corr: pd.DataFrame, seuil: float) -> list:
    """Retourne les paires (var1, var2, r) avec |r| >= seuil, sans doublons."""
    paires = []
    colonnes = corr.columns
    for i, col1 in enumerate(colonnes):
        for col2 in colonnes[i + 1:]:
            r = corr.loc[col1, col2]
            if abs(r) >= seuil:
                paires.append((col1, col2, round(r, 3)))
    return sorted(paires, key=lambda x: abs(x[2]), reverse=True)


def tracer_heatmap(corr: pd.DataFrame, output_path: Path):
    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(corr.columns, fontsize=8)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            valeur = corr.iloc[i, j]
            couleur = "white" if abs(valeur) > 0.5 else "black"
            ax.text(j, i, f"{valeur:.2f}", ha="center", va="center",
                     color=couleur, fontsize=6)

    fig.colorbar(im, ax=ax, label="Coefficient de corrélation (Pearson)")
    ax.set_title("Corrélation entre attributs régionaux — matrice neutre (M2)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main():
    matrice = pd.read_csv(INPUT_FILE)
    corr = calculer_correlations(matrice)
    corr.round(3).to_csv(OUTPUT_CSV)
    tracer_heatmap(corr, OUTPUT_HEATMAP)

    print(f"✅ Matrice de corrélation sauvegardée : {OUTPUT_CSV.resolve()}")
    print(f"✅ Heatmap sauvegardée : {OUTPUT_HEATMAP.resolve()}\n")

    paires_fortes = lister_paires_fortes(corr, SEUIL_FORTE_CORRELATION)
    if paires_fortes:
        print(f"⚠️  Paires avec |r| >= {SEUIL_FORTE_CORRELATION} (redondance potentielle) :")
        for var1, var2, r in paires_fortes:
            print(f"   {var1} <-> {var2} : r = {r}")
    else:
        print(f"Aucune paire avec |r| >= {SEUIL_FORTE_CORRELATION}.")


if __name__ == "__main__":
    main()
