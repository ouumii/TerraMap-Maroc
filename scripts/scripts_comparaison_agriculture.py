from pathlib import Path
import pandas as pd
import numpy as np

#BASE = Path(__file__).resolve().parent
score_path = Path("D:\\terramap_maroc\\data_processed\\score_final_r_c.csv")
agri_path = Path("D:\\terramap_maroc\\data_processed\\agriculture_actuelle.csv")

score = pd.read_csv(score_path)
agri = pd.read_csv(agri_path)

# Les valeurs vides sont conservées comme inconnues : elles ne signifient pas zéro.
key = ["region_id", "region", "culture"]

# Contrôle des doublons dans les clés de jointure.
dup_score = score[score.duplicated(key, keep=False)]
dup_agri = agri[agri.duplicated(key, keep=False)]
if not dup_score.empty:
    raise ValueError(f"Doublons dans le score final: {dup_score[key].to_dict('records')}")

# Harmonisation légère des colonnes numériques.
for col in ["superficie_ha", "rendement_qha"]:
    agri[col] = pd.to_numeric(agri[col], errors="coerce")

# Marrakech-Safi comporte deux blocs issus de tableaux HCP différents.
# Lorsque les mesures sont concordantes, on conserve une seule observation
# et on concatène les éléments de traçabilité. Toute divergence numérique
# reste bloquante et doit être arbitrée manuellement.
if not dup_agri.empty:
    value_cols = ["superficie_ha", "rendement_qha", "annee"]
    for k, group in agri[agri.duplicated(key, keep=False)].groupby(key, dropna=False):
        for col in value_cols:
            vals = group[col].dropna().astype(str).unique()
            if len(vals) > 1:
                raise ValueError(f"Valeurs contradictoires pour {k}, colonne {col}: {vals}")
    agri["source_doc"] = agri["source_doc"].fillna("")
    agri["note"] = agri["note"].fillna("")
    agri = (
        agri.groupby(key, as_index=False, dropna=False)
        .agg({
            "superficie_ha": "first",
            "rendement_qha": "first",
            "source_doc": lambda s: " | ".join(dict.fromkeys(x for x in s if x)),
            "annee": "first",
            "note": lambda s: " | ".join(dict.fromkeys(x for x in s if x)),
        })
    )

merged = score.merge(agri, on=key, how="left", validate="one_to_one", indicator=True)
merged["superficie_documentee"] = merged["superficie_ha"].notna()
merged["rendement_documente"] = merged["rendement_qha"].notna()
merged["agriculture_actuelle_documentee"] = (
    merged["superficie_documentee"] & merged["rendement_documente"]
)
merged["donnee_agricole_absente_du_fichier"] = merged["_merge"].eq("left_only")

# Statut descriptif : ne pas transformer une absence en absence de culture.
def status(row):
    if row["agriculture_actuelle_documentee"]:
        return "documentée (superficie et rendement disponibles)"
    if row["donnee_agricole_absente_du_fichier"]:
        return "non couverte par le fichier agricole"
    note = str(row.get("note", ""))
    low = note.lower()
    if "non pratique" in low or "non pratiqu" in low:
        return "non documentée — note: non pratiquée/non significative"
    if "non isole" in low or "non isol" in low or "agrég" in low or "agrege" in low or "mélange" in low or "melange" in low:
        return "non documentée — culture agrégée/non isolée"
    if "non disponible" in low or "valeur non disponible" in low:
        return "non documentée — valeur non disponible dans la source"
    return "non documentée — motif à vérifier dans la note/source"

merged["statut_comparaison"] = merged.apply(status, axis=1)

# Pour une comparaison quantitative, on ne retient que les couples avec les deux mesures.
for alpha in ["03", "05", "07"]:
    score_col = f"score_final_alpha{alpha}"
    merged[f"rang_score_alpha{alpha}"] = merged[f"rang_alpha{alpha}"]
    merged[f"score_disponible_comparaison_alpha{alpha}"] = merged[score_col].where(
        merged["agriculture_actuelle_documentee"]
    )

# Classement des cultures réellement documentées, par rendement agricole.
# Il est donné à titre de contexte descriptif et n'est pas assimilé au classement TerraMap.
merged["rang_rendement_agricole_region"] = np.nan
for region, idx in merged[merged["rendement_documente"]].groupby("region").groups.items():
    vals = merged.loc[idx, "rendement_qha"]
    merged.loc[idx, "rang_rendement_agricole_region"] = vals.rank(method="min", ascending=False)

# Colonnes pratiques pour l'exploitation.
ordered = key + [
    "score_rendement", "score_eco",
    "score_final_alpha03", "rang_alpha03",
    "score_final_alpha05", "rang_alpha05",
    "score_final_alpha07", "rang_alpha07",
    "superficie_ha", "rendement_qha", "source_doc", "annee", "note",
    "agriculture_actuelle_documentee", "statut_comparaison",
    "rang_rendement_agricole_region",
]
comparison = merged[ordered].sort_values(["region_id", "rang_alpha05", "culture"])
comparison.to_csv(Path("D:\\terramap_maroc\\data_processed\\comparaison_score_agriculture.csv"), index=False)

# Recommandation top 1 et état documentaire de la culture recommandée.
rows = []
for alpha in ["03", "05", "07"]:
    rank_col = f"rang_alpha{alpha}"
    score_col = f"score_final_alpha{alpha}"
    tops = merged[merged[rank_col].eq(1)].copy()
    for _, row in tops.iterrows():
        rows.append({
            "region_id": row["region_id"],
            "region": row["region"],
            "scenario": f"alpha=0.{alpha[-1]}",
            "culture_recommandee": row["culture"],
            "score_final": row[score_col],
            "score_rendement": row["score_rendement"],
            "score_eco": row["score_eco"],
            "agriculture_actuelle_documentee": row["agriculture_actuelle_documentee"],
            "statut_comparaison": row["statut_comparaison"],
            "superficie_actuelle_ha": row["superficie_ha"],
            "rendement_actuel_qha": row["rendement_qha"],
            "annee_agricole": row["annee"],
            "source_agricole": row["source_doc"],
            "note_agricole": row["note"],
        })
recommendations = pd.DataFrame(rows).sort_values(["region_id", "scenario"])
recommendations.to_csv(Path("D:\\terramap_maroc\\data_processed\\recommandations_et_situation_actuelle.csv"), index=False)

# Synthèse statistique des couvertures et des recommandations.
regions = score["region"].nunique()
cultures = score["culture"].nunique()
pairs = len(score)
documented = int(merged["agriculture_actuelle_documentee"].sum())
partial = int((merged["_merge"].eq("both") & ~merged["agriculture_actuelle_documentee"]).sum())
not_covered = int(merged["donnee_agricole_absente_du_fichier"].sum())

summary_rows = []
for alpha in ["03", "05", "07"]:
    rec = recommendations[recommendations["scenario"].eq(f"alpha=0.{alpha[-1]}")]
    summary_rows.append({
        "scenario": f"alpha=0.{alpha[-1]}",
        "regions": regions,
        "cultures": cultures,
        "couples_scores": pairs,
        "couples_agriculture_documentes": documented,
        "taux_couverture_quantitative_pct": round(100 * documented / pairs, 2),
        "recommandations_avec_donnees_actuelles": int(rec["agriculture_actuelle_documentee"].sum()),
        "recommandations_sans_donnees_completes": int((~rec["agriculture_actuelle_documentee"]).sum()),
    })
summary = pd.DataFrame(summary_rows)
summary.to_csv(Path("D:\\terramap_maroc\\data_processed\\synthese_comparaison_agriculture.csv"), index=False)

# Rapport Markdown directement exploitable dans le mémoire.
from collections import Counter
status_counts = merged["statut_comparaison"].value_counts()
lines = []
lines.append("# Comparaison TerraMap avec la situation agricole actuelle\n")
lines.append("## 1. Périmètre et règle de traitement des données manquantes\n")
lines.append(
    "La comparaison est réalisée entre les 228 couples région–culture du score final et le fichier `agriculture_actuelle.csv`. "
    "Les valeurs absentes ne sont pas remplacées par zéro : une cellule vide peut correspondre à une culture non isolée, "
    "à une donnée non disponible dans la monographie, à une culture non pratiquée ou à une absence de couverture dans le fichier. "
    "La comparaison quantitative est donc limitée aux couples disposant simultanément d’une superficie et d’un rendement documentés.\n"
)
lines.append("## 2. Couverture des données\n")
lines.append(f"- Régions couvertes par les scores : **{regions}**.")
lines.append(f"- Cultures couvertes par les scores : **{cultures}**.")
lines.append(f"- Couples région–culture évalués : **{pairs}**.")
lines.append(f"- Couples avec superficie et rendement disponibles : **{documented}** ({100*documented/pairs:.1f} %).")
lines.append(f"- Couples présents dans le fichier agricole mais incomplets : **{partial}**.")
lines.append(f"- Couples non couverts par le fichier agricole : **{not_covered}**.\n")
lines.append("### Répartition des statuts\n")
lines.append("| Statut | Nombre de couples |")
lines.append("|---|---:|")
for label, count in status_counts.items():
    lines.append(f"| {label} | {count} |")
lines.append("")
lines.append("## 3. État des recommandations selon α\n")
lines.append("| Scénario | Recommandations avec données agricoles complètes | Recommandations sans données complètes |")
lines.append("|---|---:|---:|")
for _, row in summary.iterrows():
    lines.append(f"| {row['scenario']} | {int(row['recommandations_avec_donnees_actuelles'])}/12 | {int(row['recommandations_sans_donnees_completes'])}/12 |")
lines.append("")
lines.append("## 4. Tableau des recommandations et de leur situation documentée\n")
lines.append("| Région | Scénario | Culture recommandée | Score final | Situation actuelle documentée | Rendement actuel (qx/ha) |")
lines.append("|---|---|---|---:|---|---:|")
for _, row in recommendations.iterrows():
    rend = "—" if pd.isna(row["rendement_actuel_qha"]) else f"{row['rendement_actuel_qha']:.2f}"
    doc = "Oui" if row["agriculture_actuelle_documentee"] else "Non"
    lines.append(f"| {row['region']} | {row['scenario']} | {row['culture_recommandee']} | {row['score_final']:.3f} | {doc} — {row['statut_comparaison']} | {rend} |")
lines.append("")
lines.append("## 5. Interprétation méthodologique\n")
lines.append(
    "Une recommandation TerraMap qui ne possède pas de rendement agricole actuel documenté ne doit pas être interprétée comme une preuve "
    "que la culture est absente de la région, ni comme une preuve d’amélioration potentielle. Elle signifie uniquement que la comparaison "
    "quantitative n’est pas possible avec les sources actuellement compilées. De même, une culture présente dans les données agricoles "
    "n’est pas automatiquement considérée comme optimale : l’objectif du système est précisément d’examiner l’écart entre la situation "
    "observée et l’adéquation calculée selon les critères climatiques, pédologiques et hydriques.\n"
)
lines.append("## 6. Fichiers de sortie\n")
lines.append("- `comparaison_score_agriculture.csv` : jointure complète des scores et données agricoles.")
lines.append("- `recommandations_et_situation_actuelle.csv` : une ligne par région et scénario α.")
lines.append("- `synthese_comparaison_agriculture.csv` : indicateurs de couverture et de comparaison.")

(Path("D:\\terramap_maroc\\data_processed\\Rapport_comparaison_agriculture.md")).write_text("\n".join(lines), encoding="utf-8")

print(f"Scores: {pairs} couples, {regions} régions, {cultures} cultures")
print(f"Agriculture documentée quantitativement: {documented}/{pairs} ({100*documented/pairs:.1f}%)")
print("Sorties créées: comparaison_score_agriculture.csv, recommandations_et_situation_actuelle.csv, synthese_comparaison_agriculture.csv, Rapport_comparaison_agriculture.md")
