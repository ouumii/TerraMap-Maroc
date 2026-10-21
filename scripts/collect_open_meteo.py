import pandas as pd
import requests
import time

# 1. Charger ton CSV de régions
try:
    df_regions = pd.read_csv("D:\\terramap_maroc\\data_raw\\regions_maroc.csv")
    print(f"✅ Fichier 'regions_maroc.csv' chargé avec succès ({len(df_regions)} régions trouvées).")
except FileNotFoundError:
    print("❌ Erreur : Le fichier 'regions_maroc.csv' est introuvable. Vérifie son nom et son emplacement.")
    exit()

# Période d'analyse : Année complète 2025 pour des statistiques annuelles stables
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

climat_results = []

print("\nDébut de la collecte des données climatiques sur Open-Meteo...")

# 2. Boucle sur chaque région de ton CSV
for index, row in df_regions.iterrows():
    region_name = row['region']
    lat = row['latitude']
    lon = row['longitude']

    print(f"-> Récupération pour : {region_name} (Lat: {lat}, Lon: {lon})...")

    # URL de l'API Archive d'Open-Meteo
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,et0_fao_evapotranspiration",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            hourly = data["hourly"]
            df_hourly = pd.DataFrame(hourly)

            # Calcul des indicateurs demandés
            temp_mean = round(df_hourly["temperature_2m"].mean(), 1)
            temp_max = round(df_hourly["temperature_2m"].max(), 1)
            temp_min = round(df_hourly["temperature_2m"].min(), 1)
            humidity = round(df_hourly["relative_humidity_2m"].mean(), 1)

            # Cumuls annuels (Somme)
            rainfall = round(df_hourly["precipitation"].sum(), 1)
            et0_fao_evapotranspiration = round(df_hourly["et0_fao_evapotranspiration"].sum(), 1)

            # Stocker avec l'ID pour pouvoir fusionner proprement
            climat_results.append({
                "region_id": row['region_id'],
                "temp_mean": temp_mean,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "rainfall": rainfall,
                "humidity": humidity,
                "et0_fao_evapotranspiration": et0_fao_evapotranspiration
            })
        else:
            print(f"⚠️ Code erreur {response.status_code} pour {region_name}")

        # Pause d'une seconde pour respecter les limites de l'API gratuite
        time.sleep(1)

    except Exception as e:
        print(f"❌ Erreur de connexion pour {region_name} : {e}")

# 3. Convertir les résultats en DataFrame
df_climat = pd.DataFrame(climat_results)

# 4. Fusionner les données climatiques avec les colonnes initiales (capital, lat, lon...)
df_final = pd.merge(df_regions, df_climat, on="region_id", how="inner")

# 5. Sauvegarder le résultat final pour l'Étape 4
df_final.to_csv("D:\\terramap_maroc\\data_processed\\donnees_climatiques.csv", index=False)

print("\n🎉 Étape 4 terminée avec succès !")
print("Le fichier enrichi a été sauvegardé sous le nom : 'donnees_climatiques.csv'")
print(df_final[['region', 'temp_mean', 'rainfall', 'humidity', 'et0_fao_evapotranspiration']].head())

# NOTE METHODOLOGIQUE (ajoutee lors de l'audit Sept. 2026) :
# La colonne "et0_fao_evapotranspiration" ci-dessus correspond au champ API
# "et0_fao_evapotranspiration" (ET0 de reference, methode FAO Penman-Monteith),
# et NON a la variable "evapotranspiration" (evapotranspiration reelle/actuelle)
# egalement disponible chez Open-Meteo. les valeurs sont correctes et utilisables directement comme ET0
# dans le calcul ETc = Kc x ET0 (methode FAO-56).