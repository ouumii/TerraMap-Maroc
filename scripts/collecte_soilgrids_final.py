"""
Collecte des données de sols SoilGrids v2.0 via WebDAV (mosaïques VRT globales)
--------------------------------------------------------------------------------
Méthodologie unifiée (v2) :
- Pour éviter de mélanger deux méthodes de mesure différentes (moyenne de zone
  vs. pixel unique, ce qui s'est produit lors des itérations précédentes et a
  donné des valeurs différentes selon les régions), CE SCRIPT applique
  SYSTÉMATIQUEMENT une moyenne sur une fenêtre fixe de 3x3 pixels (~750m)
  autour du point, pour les 12 régions sans exception.
- Si la fenêtre 3x3 est entièrement en nodata (bord de côte/estuaire), la
  fenêtre s'élargit automatiquement (9x9 -> 15x15 pixels).
- En fin de script, une PASSE DE SECOURS automatique retente, avec une fenêtre
  encore plus large (25x25 pixels, ~6.25km), toute région qui resterait
  incomplète après la boucle principale (ex. Dakhla-Oued Ed Dahab, zone
  côtière/péninsulaire à risque de nodata comme Rabat-Salé-Kénitra) - pas
  besoin de relancer le script séparément.

Corrections critiques intégrées :
1. Conversion organic_carbon : /100 au total (dg/kg -> g/kg -> %), pas /10.
2. Projection Homolosine : sphère ISRIC/MODIS (R=6371007.181), pas l'ellipsoïde
   WGS84 - source d'un décalage dépendant de la latitude sinon.

Référence : https://docs.isric.org/globaldata/soilgrids/webdav_from_R_terra.html

Installation requise (une seule fois) :
    pip install rasterio pyproj pandas numpy
"""

import pandas as pd
import numpy as np
import rasterio
import pyproj
import time
from pathlib import Path

# ============================================================
# CONFIGURATION DES CHEMINS
# ============================================================
INPUT_FILE = Path("D:\\terramap_maroc\\data_raw\\regions_maroc.csv")
OUTPUT_FILE = Path("D:\\terramap_maroc\\data_processed\\donnees_sols.csv")
LOG_FILE = Path("D:\\terramap_maroc\\data_processed\\log_collecte_soilgrids.csv")

# ============================================================
# FACTEURS DE CONVERSION OFFICIELS SoilGrids v2.0 (documentation ISRIC)
# phh2o : pH*10                  -> /10  = pH
# clay/sand/silt : g/kg          -> /10  = %
# soc   : dg/kg                  -> /100 au total = %  (dg/kg -> g/kg -> %)
# ============================================================

PROPERTIES = ["phh2o", "clay", "sand", "silt", "soc"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]

# Fenêtre de moyenne de base, appliquée uniformément aux 12 régions.
BASE_WINDOW = 3          # ~750m - moyenne standard pour toutes les régions
ESCALATION_WINDOWS = (9, 15)   # utilisées seulement si BASE_WINDOW est en nodata
RESCUE_WINDOW = 25       # ~6.25km - passe de secours finale automatique

# Projection native des mosaïques SoilGrids : Interrupted Goode Homolosine.
# IMPORTANT : ISRIC utilise une sphère de rayon 6371007.181 m (même convention
# que MODIS), PAS l'ellipsoïde WGS84.
IGH_PROJ4 = "+proj=igh +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +R=6371007.181 +units=m +no_defs"
_transformer = pyproj.Transformer.from_crs("EPSG:4326", IGH_PROJ4, always_xy=True)

VRT_URL_TEMPLATE = "/vsicurl/https://files.isric.org/soilgrids/latest/data/{prop}/{prop}_{depth}_mean.vrt"

MAX_ATTEMPTS = 3


def _read_window_mean(src, x, y, window_size, nodata):
    """Lit la moyenne d'une fenêtre carrée de window_size pixels centrée sur (x, y).
    Retourne None si la fenêtre est entièrement en nodata."""
    row, col = src.index(x, y)
    half = window_size // 2
    window = rasterio.windows.Window(
        col_off=col - half, row_off=row - half,
        width=window_size, height=window_size
    )
    arr = src.read(1, window=window).astype("float64")
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return None
    with np.errstate(invalid="ignore"):
        return float(np.nanmean(arr))


def fetch_value(prop, depth, lat, lon, region_name, window_size=BASE_WINDOW):
    """Échantillonne la valeur brute (unité mappée SoilGrids, non convertie)
    en moyennant une fenêtre de `window_size` pixels autour de (lat, lon).
    Si cette fenêtre est en nodata, élargit progressivement
    (9x9 -> 15x15 pixels) avant d'abandonner pour cette tentative."""

    vrt_url = VRT_URL_TEMPLATE.format(prop=prop, depth=depth)
    x, y = _transformer.transform(lon, lat)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with rasterio.open(vrt_url) as src:
                nodata = src.nodata

                mean_val = _read_window_mean(src, x, y, window_size, nodata)
                if mean_val is not None:
                    return mean_val

                # Élargissement progressif si la fenêtre de base est en nodata
                for w in ESCALATION_WINDOWS:
                    if w <= window_size:
                        continue
                    mean_val = _read_window_mean(src, x, y, w, nodata)
                    if mean_val is not None:
                        print(f"      ℹ️ {prop}_{depth} pour {region_name} : fenêtre {window_size}x{window_size} "
                              f"en nodata, valeur récupérée via fenêtre {w}x{w} ({mean_val:.2f}).")
                        return mean_val

                print(f"      ⚠️ {prop}_{depth} pour {region_name} : nodata même sur fenêtre "
                      f"{max(window_size, *ESCALATION_WINDOWS)}x{max(window_size, *ESCALATION_WINDOWS)}.")
                return None

        except Exception as e:
            print(f"      ❌ Échec {prop}_{depth} pour {region_name} (tentative {attempt}/{MAX_ATTEMPTS}) : {e}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(3 * attempt)

    return None


def collect_region(region_id, region_name, lat, lon, window_size=BASE_WINDOW):
    """Collecte les 5 propriétés de sol pour une région, moyennées sur les
    3 profondeurs, avec conversion d'unité appliquée. Retourne un dict avec
    les colonnes finales (ph, clay, sand, silt, organic_carbon)."""

    region_soil = {"region_id": region_id, "region": region_name}

    for prop in PROPERTIES:
        depth_values = []
        for depth in DEPTHS:
            val = fetch_value(prop, depth, lat, lon, region_name, window_size=window_size)
            if val is not None:
                depth_values.append(val)

        if depth_values:
            mean_val = sum(depth_values) / len(depth_values)

            if prop == "phh2o":
                region_soil["ph"] = round(mean_val / 10, 1)
            elif prop == "clay":
                region_soil["clay"] = round(mean_val / 10, 1)
            elif prop == "sand":
                region_soil["sand"] = round(mean_val / 10, 1)
            elif prop == "silt":
                region_soil["silt"] = round(mean_val / 10, 1)
            elif prop == "soc":
                region_soil["organic_carbon"] = round(mean_val / 100, 3)

            print(f"   ✅ {prop} : {mean_val:.2f} (brut, moyenne sur {len(depth_values)} profondeurs, "
                  f"fenêtre {window_size}x{window_size})")
        else:
            print(f"   ⚠️ {prop} : aucune valeur récupérée pour {region_name}")

    return region_soil


# 1. Charger le CSV des 12 régions
try:
    df_regions = pd.read_csv(INPUT_FILE)
    print(f"✅ Fichier 'regions_maroc.csv' chargé avec succès ({len(df_regions)} régions trouvées).")
except FileNotFoundError:
    print(f"❌ Erreur : Le fichier '{INPUT_FILE}' est introuvable.")
    exit()

soil_results = []

print(f"\nDébut de la collecte des données de sols via WebDAV/VRT "
      f"(fenêtre de base {BASE_WINDOW}x{BASE_WINDOW}, Couche 0-30cm)...")

# 2. Boucle principale sur les 12 régions - fenêtre de base identique pour toutes
for index, row in df_regions.iterrows():
    region_id = row['region_id']
    region_name = row['region']
    lat = row['latitude']
    lon = row['longitude']

    print(f"\n-> Extraction des sols pour : {region_name} (Lat: {lat}, Lon: {lon})...")
    soil_results.append(collect_region(region_id, region_name, lat, lon, window_size=BASE_WINDOW))

df_soil = pd.DataFrame(soil_results)

# 3. PASSE DE SECOURS AUTOMATIQUE : toute région avec au moins une propriété
# manquante est retentée avec une fenêtre beaucoup plus large (25x25 pixels),
# directement dans ce même script - pas besoin de le relancer séparément.
expected_cols = ["ph", "clay", "sand", "silt", "organic_carbon"]
for col in expected_cols:
    if col not in df_soil.columns:
        df_soil[col] = np.nan

incomplete_mask = df_soil[expected_cols].isna().any(axis=1)
incomplete_regions = df_soil.loc[incomplete_mask, "region_id"].tolist()

if incomplete_regions:
    print(f"\n🔄 Passe de secours automatique (fenêtre {RESCUE_WINDOW}x{RESCUE_WINDOW}) "
          f"pour {len(incomplete_regions)} région(s) incomplète(s)...")
    for region_id in incomplete_regions:
        row = df_regions.loc[df_regions["region_id"] == region_id].iloc[0]
        region_name = row['region']
        lat, lon = row['latitude'], row['longitude']
        print(f"\n-> Nouvelle tentative pour : {region_name} (fenêtre {RESCUE_WINDOW}x{RESCUE_WINDOW})...")
        rescued = collect_region(region_id, region_name, lat, lon, window_size=RESCUE_WINDOW)

        idx = df_soil.index[df_soil["region_id"] == region_id][0]
        for col in expected_cols:
            if col in rescued:
                df_soil.loc[idx, col] = rescued[col]
else:
    print("\n✅ Toutes les régions sont complètes dès la passe principale - pas besoin de passe de secours.")

# 4. Structuration et fusion avec les colonnes initiales (capital, lat, lon...)
df_final_soil = pd.merge(df_regions, df_soil.drop(columns=["region"], errors="ignore"), on="region_id", how="inner")

# 5. Sauvegarde
df_final_soil.to_csv(OUTPUT_FILE, index=False)

print("\n🎉 Collecte terminée (via WebDAV/VRT) pour les 12 régions, méthodologie unifiée.")
print(f"Fichier de données sauvegardé : {OUTPUT_FILE}")

print("\nAperçu des données collectées :")
print(df_final_soil[['region', 'ph', 'clay', 'sand', 'silt', 'organic_carbon']])

missing_oc = df_final_soil[df_final_soil['organic_carbon'].isna()]['region'].tolist()
if missing_oc:
    print(f"\n⚠️ ATTENTION : 'organic_carbon' toujours manquant pour {len(missing_oc)} région(s) "
          f"même après la passe de secours : {missing_oc}")
    print("   -> Vérifier manuellement ces régions (coordonnées très proches de l'eau, ou panne réseau).")
else:
    print("\n✅ 'organic_carbon' est renseigné pour toutes les régions.")