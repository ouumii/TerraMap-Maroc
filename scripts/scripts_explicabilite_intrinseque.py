#!/usr/bin/env python3
"""Explicabilité intrinsèque des recommandations TerraMap.

Le script enrichit le fichier des scores sans réentraîner de modèle ML.
Il calcule :
- les contributions rendement/écologie selon alpha ;
- la composante dominante ;
- le rang et l'écart avec la culture suivante ;
- la stabilité de la recommandation entre alpha=0.3, 0.5 et 0.7 ;
- une explication textuelle lisible.

Si le fichier de rendement contient les trois colonnes détaillées
(score_temp, score_rainfall, score_ph), le facteur limitant est calculé
automatiquement par la loi du minimum de Liebig.
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd

DEFAULT_INPUT = Path("D:\\terramap_maroc\\data_processed\\score_final_r_c.csv")
DEFAULT_OUTPUT = Path("D:\\terramap_maroc\\data_processed\\score_final_explicable.csv")

KEY = ["region_id", "region", "culture"]
ALPHAS = ["03", "05", "07"]

# Noms acceptés pour faciliter l'intégration avec de futurs fichiers détaillés.
COMPONENT_ALIASES = {
    "score_temperature": ["score_temperature", "score_temp", "score_température"],
    "score_pluie": ["score_pluie", "score_rainfall", "score_precipitation", "score_precipitations"],
    "score_ph": ["score_ph", "score_pH", "score_pH_sol"],
}
CORE_COMPONENTS = ["score_temperature", "score_pluie", "score_ph"]


def find_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def first_existing(df, candidates):
    col = find_column(df, candidates)
    if col is None:
        return pd.Series(np.nan, index=df.index, dtype="float64"), None
    return pd.to_numeric(df[col], errors="coerce"), col


def check_input(df):
    missing = [c for c in KEY + ["score_rendement", "score_eco"] if c not in df.columns]
    if missing:
        raise ValueError("Colonnes obligatoires absentes: " + ", ".join(missing))
    if df.duplicated(KEY).any():
        raise ValueError("Le fichier contient des doublons région-culture.")
    for c in ["score_rendement", "score_eco"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        if df[c].isna().any():
            raise ValueError(f"La colonne {c} contient des valeurs manquantes.")
        if not df[c].between(0, 1).all():
            raise ValueError(f"La colonne {c} contient des valeurs hors de [0,1].")


def rank_and_gap(group, score_col):
    order = group.sort_values(score_col, ascending=False)
    ranks = order[score_col].rank(method="min", ascending=False).astype(int)
    out = pd.Series(index=group.index, data=ranks)
    next_score = order[score_col].shift(-1)
    gaps = (order[score_col] - next_score).fillna(np.nan)
    gap_out = pd.Series(index=group.index, data=gaps.values)
    return out, gap_out


def explain_row(row, alpha):
    r = row["score_rendement"]
    e = row["score_eco"]
    cr = row[f"contribution_rendement_alpha{alpha}"]
    ce = row[f"contribution_ecologie_alpha{alpha}"]
    total = row[f"score_final_alpha{alpha}"]
    factor = row.get("facteur_limitant", "non calculable avec les colonnes disponibles")

    if cr > ce:
        dominant = "rendement"
    elif ce > cr:
        dominant = "écologie"
    else:
        dominant = "équilibre rendement-écologie"

    text = (
        f"{row['culture']} obtient un score final de {total:.3f} pour alpha={float(alpha)/10:.1f}. "
        f"Le score de rendement est {r:.3f} et le score écologique est {e:.3f}. "
        f"La composante dominante est {dominant} "
        f"(contributions: rendement={cr:.3f}, écologie={ce:.3f})."
    )
    if factor == "aucun facteur limitant unique (scores égaux)":
        text += " Les trois critères de rendement sont au même niveau ; aucun facteur limitant unique n'est identifié."
    elif factor and factor != "non calculable avec les colonnes disponibles":
        text += f" Le facteur limitant : {factor}."
    else:
        text += " Le facteur limitant détaillé n'est pas calculable car les scores température, pluviométrie et pH ne figurent pas encore dans le fichier d'entrée."
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument(
        "--rendement-file",
        default=Path("D:\\terramap_maroc\\data_processed\\score_rendement_r_c.csv"),
        help="Fichier contenant les composantes détaillées du score rendement. "
             "La fusion utilise region_id, region et culture.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    # Les composantes détaillées peuvent être stockées dans un fichier séparé.
    # Le fichier est optionnel afin de conserver la possibilité d'exécuter le
    # script sur le score final seul.
    rendement_path = Path(args.rendement_file)
    if rendement_path.exists():
        rendement = pd.read_csv(rendement_path)
        missing_keys = [c for c in KEY if c not in rendement.columns]
        if missing_keys:
            raise ValueError(
                f"Clés absentes de {rendement_path}: {', '.join(missing_keys)}"
            )
        if rendement.duplicated(KEY).any():
            raise ValueError(
                f"Le fichier {rendement_path} contient des doublons région-culture."
            )

        # Ne fusionner que les composantes détaillées, jamais score_rendement
        # ou une autre sortie déjà présente dans le score final.
        detailed_cols = []
        for aliases in COMPONENT_ALIASES.values():
            col = find_column(rendement, aliases)
            if col is not None and col not in detailed_cols:
                detailed_cols.append(col)
        if not detailed_cols:
            raise ValueError(
                f"Aucune colonne de composante reconnue dans {rendement_path}. "
                f"Colonnes attendues: score_temp, score_rainfall, score_ph."
            )
        df = df.merge(rendement[KEY + detailed_cols], on=KEY, how="left", validate="one_to_one")
        print(f"Composantes rendement fusionnées depuis : {rendement_path}")
        print(f"Colonnes fusionnées : {', '.join(detailed_cols)}")
    else:
        print(f"Fichier rendement détaillé absent ({rendement_path}); poursuite sans fusion.")

    check_input(df)

    # Si les trois colonnes détaillées sont présentes, calculer le facteur limitant.
    component_series = {}
    component_source = {}
    for name, aliases in COMPONENT_ALIASES.items():
        component_series[name], component_source[name] = first_existing(df, aliases)
        df[name] = component_series[name]

    available_components = [k for k in CORE_COMPONENTS if component_series[k].notna().all()]
    if len(available_components) == len(CORE_COMPONENTS):
        component_frame = df[CORE_COMPONENTS]
        labels = {
            "score_temperature": "température",
            "score_pluie": "pluviométrie",
            "score_ph": "pH",
        }
        def limiting_factor(row):
            minimum = row.min()
            limiting = [labels[col] for col in CORE_COMPONENTS if abs(row[col] - minimum) <= 1e-12]
            if len(limiting) == len(CORE_COMPONENTS):
                return "aucun facteur limitant unique (scores égaux)"
            return " + ".join(limiting)
        df["facteur_limitant"] = component_frame.apply(limiting_factor, axis=1)
        df["facteur_limitant_score"] = component_frame.min(axis=1)
        df["explicabilite_liebig_disponible"] = True
    else:
        df["facteur_limitant"] = "non calculable avec les colonnes disponibles"
        df["facteur_limitant_score"] = np.nan
        df["explicabilite_liebig_disponible"] = False

    # Calcul des contributions pour chaque scénario alpha.
    for alpha in ALPHAS:
        a = float(f"0.{alpha[-1]}")
        final_col = f"score_final_alpha{alpha}"
        if final_col not in df.columns:
            df[final_col] = a * df["score_rendement"] + (1 - a) * df["score_eco"]
        df[f"contribution_rendement_alpha{alpha}"] = a * df["score_rendement"]
        df[f"contribution_ecologie_alpha{alpha}"] = (1 - a) * df["score_eco"]
        df[f"composante_dominante_alpha{alpha}"] = np.select(
            [df[f"contribution_rendement_alpha{alpha}"] > df[f"contribution_ecologie_alpha{alpha}"],
             df[f"contribution_ecologie_alpha{alpha}"] > df[f"contribution_rendement_alpha{alpha}"]],
            ["rendement", "écologie"],
            default="équilibre rendement-écologie",
        )
        ranks, gaps = [], []
        for _, group in df.groupby("region_id", sort=False):
            r, g = rank_and_gap(group, final_col)
            ranks.append(r); gaps.append(g)
        df[f"rang_alpha{alpha}"] = pd.concat(ranks).sort_index().astype(int)
        df[f"ecart_score_suivant_alpha{alpha}"] = pd.concat(gaps).sort_index()
        df[f"explication_alpha{alpha}"] = df.apply(lambda row: explain_row(row, alpha), axis=1)

    # Stabilité de chaque recommandation entre les trois scénarios.
    winners = {}
    for alpha in ALPHAS:
        winners[alpha] = df.loc[df[f"rang_alpha{alpha}"].eq(1)].set_index("region_id")["culture"]
    df["culture_recommandee_alpha03"] = df["region_id"].map(winners["03"])
    df["culture_recommandee_alpha05"] = df["region_id"].map(winners["05"])
    df["culture_recommandee_alpha07"] = df["region_id"].map(winners["07"])
    df["recommandation_stable_sur_3_scenarios"] = (
        (df["culture_recommandee_alpha03"] == df["culture_recommandee_alpha05"]) &
        (df["culture_recommandee_alpha05"] == df["culture_recommandee_alpha07"]) &
        (df["culture"] == df["culture_recommandee_alpha05"])
    )

    # Contrôle numérique et sauvegarde.
    for alpha in ALPHAS:
        expected = df[f"contribution_rendement_alpha{alpha}"] + df[f"contribution_ecologie_alpha{alpha}"]
        if not np.allclose(expected, df[f"score_final_alpha{alpha}"], atol=1e-10):
            raise ValueError(f"Incohérence dans le score final alpha={alpha}")

    df.to_csv(args.output, index=False)

    # Résumé lisible pour la rédaction et le futur dashboard.
    summary = []
    for alpha in ALPHAS:
        top = df[df[f"rang_alpha{alpha}"].eq(1)]
        summary.append({
            "scenario": f"alpha=0.{alpha[-1]}",
            "regions": int(df["region_id"].nunique()),
            "recommandations": len(top),
            "cultures_recommandees_distinctes": int(top["culture"].nunique()),
            "score_min_recommandations": top[f"score_final_alpha{alpha}"].min(),
            "score_max_recommandations": top[f"score_final_alpha{alpha}"].max(),
            "facteur_limitant_detaille_disponible": bool(df["explicabilite_liebig_disponible"].all()),
        })
    pd.DataFrame(summary).to_csv(Path(args.output).with_name("synthese_explicabilite.csv"), index=False)

    print(f"Fichier produit : {args.output}")
    print(f"Lignes : {len(df)} | Régions : {df['region_id'].nunique()}")
    print("Facteur limitant détaillé disponible :", bool(df["explicabilite_liebig_disponible"].all()))
    print("Colonnes d'explication ajoutées : contributions, composante dominante, rang, écart, stabilité et texte explicatif.")


if __name__ == "__main__":
    main()
