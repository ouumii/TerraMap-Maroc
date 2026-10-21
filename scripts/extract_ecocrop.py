import pandas as pd

# Chargement Ecocrop
ecocrop = pd.read_csv(
    r"D:\terramap_maroc\data_raw\cultures\EcoCrop_DB.csv",
    encoding="latin1"
)

# Chargement cultures retenues
selected = pd.read_csv(
    r"D:\terramap_maroc\data_raw\cultures\selected_crops.csv"
)

# Filtrage
filtered = ecocrop[
    ecocrop["ScientificName"].isin(
        selected["scientific_name"]
    )
]

# Colonnes utiles
columns = [
    "ScientificName",
    "COMNAME",
    "TOPMN",
    "TOPMX",
    "TMIN",
    "TMAX",
    "ROPMN",
    "ROPMX",
    "RMIN",
    "RMAX",
    "PHOPMN",
    "PHOPMX",
    "PHMIN",
    "PHMAX",
    "TEXT",
    "FER",
    "SAL",
    "DRA",
    "GMIN",
    "GMAX"
]

crop_requirements = filtered[columns]

# Sauvegarde
crop_requirements.to_csv(
    r"D:\terramap_maroc\data_processed\exigences_cultures.csv",
    index=False
)

print("Dataset créé avec succès !")
print(crop_requirements.shape)
print(crop_requirements.head())