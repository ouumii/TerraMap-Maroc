import pandas as pd
d = pd.read_csv("robustesse_climat_2015_2024/comparaison_scores_2025_vs_2015_2024.csv")
for k in ["03", "05", "07"]:
    s = d.groupby("region").apply(
        lambda g: g[f"score_final_alpha{k}_2025"].rank()
                   .corr(g[f"score_final_alpha{k}_2015_2024"].rank()))
    print("alpha", k)
    print(s.round(2).sort_values().to_string())