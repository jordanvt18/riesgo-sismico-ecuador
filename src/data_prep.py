# -*- coding: utf-8 -*-
"""
Preparación de datos: catálogo sísmico IG/USGS + límites cantonales + censo 2022.

Pasos:
1) Limpieza del catálogo sísmico (fecha, hora, magnitud, profundidad, lat, lon).
2) Unión espacial (geopandas.sjoin) de cada sismo con su cantón.
3) Agregación por cantón (n.º de sismos, magnitud máxima, profundidad media,
   energía liberada) y cruce con la población del Censo 2022.

Uso:  python src/data_prep.py   (o importado desde los notebooks)
"""
import os
import unicodedata

import pandas as pd
import geopandas as gpd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
os.makedirs(PROC, exist_ok=True)

# Constantes del modelo de energía (Gutenberg-Richter): log10(E) = 1.5*M + 4.8 (E en joules)
A_ENERGIA, B_ENERGIA = 1.5, 4.8


# Alias entre nombres del Censo 2022 (INEC) y de geoBoundaries (IGM/OCHA)
ALIAS_CANTON = {
    "DISTRITO METROPOLITANO DE QUITO": "QUITO",
    "ALFREDO BAQUERIZO MORENO (JUJAN)": "ALFREDO BAQUERIZO MORENO",
    "GENERAL ANTONIO ELIZALDE": "GNRAL. ANTONIO ELIZALDE",
    "FRANCISCO DE ORELLANA": "ORELLANA",
    "CORONEL MARCELINO MARIDUENA": "CRNEL. MARCELINO MARIDUENA",
    "EL EMPALME": "EMPALME",
}


def normalizar_nombre(texto: str) -> str:
    """Quita acentos, colapsa espacios y normaliza mayúsculas para cruzar nombres."""
    if pd.isna(texto):
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = " ".join(texto.split()).strip().upper()
    return ALIAS_CANTON.get(texto, texto)


def cargar_catalogo() -> pd.DataFrame:
    """Limpia el catálogo sísmico crudo y devuelve un DataFrame ordenado."""
    ruta = os.path.join(RAW, "catalogo_sismico_ecuador_1983_2026.csv")
    df = pd.read_csv(ruta)
    df = df[df["type"] == "earthquake"].copy()          # solo sismos (no explosiones)
    df["fecha_hora"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["fecha_hora", "latitude", "longitude", "mag", "depth"])
    df["fecha"] = df["fecha_hora"].dt.date
    df["hora"] = df["fecha_hora"].dt.strftime("%H:%M:%S")
    df["anio"] = df["fecha_hora"].dt.year
    # Energía sísmica liberada en joules (relación de Gutenberg-Richter)
    df["energia_j"] = 10 ** (A_ENERGIA * df["mag"] + B_ENERGIA)
    columnas = ["fecha_hora", "fecha", "hora", "anio", "mag", "depth",
                "latitude", "longitude", "magType", "place", "energia_j", "id"]
    return df[columnas].sort_values("fecha_hora").reset_index(drop=True)


def cargar_cantones() -> gpd.GeoDataFrame:
    """Carga los límites cantonales y normaliza el nombre para unions."""
    ruta = os.path.join(RAW, "cantones_ecuador.geojson")
    gdf = gpd.read_file(ruta)
    gdf = gdf[["shapeName", "geometry"]].rename(columns={"shapeName": "canton"})
    gdf["canton_norm"] = gdf["canton"].apply(normalizar_nombre)
    return gdf


# Las 24 provincias del Ecuador (para separar filas de provincia vs. cantón,
# ya que ambas usan el marcador 'Total <nombre>' en el tabulado del INEC)
PROVINCIAS = {
    "AZUAY", "BOLIVAR", "CANAR", "CARCHI", "CHIMBORAZO", "COTOPAXI",
    "EL ORO", "ESMERALDAS", "GALAPAGOS", "GUAYAS", "IMBABURA", "LOJA",
    "LOS RIOS", "MANABI", "MORONA SANTIAGO", "NAPO", "ORELLANA", "PASTAZA",
    "PICHINCHA", "SANTA ELENA", "SANTO DOMINGO DE LOS TSACHILAS", "SUCUMBIOS",
    "TUNGURAHUA", "ZAMORA CHINCHIPE",
}


def cargar_poblacion() -> pd.DataFrame:
    """Parsea el tabulado 1.1 del Censo 2022: población total por cantón.

    Estructura del archivo oficial (INEC): col 1 = provincia, col 2 = cantón,
    col 3 = área ('Total <Cantón>' / 'Urbana' / 'Rural'), col 4 = total de
    personas (números con comas). Nos quedamos solo con las filas 'Total'.
    """
    ruta = os.path.join(RAW, "censo2022_poblacion_canton.csv")
    crudo = pd.read_csv(ruta, encoding="cp1252", header=None, dtype=str)
    crudo = crudo.iloc[:, :5]
    crudo.columns = ["basura", "provincia", "canton", "area", "total"]

    datos = crudo.dropna(subset=["provincia", "canton", "area", "total"])
    # Fila de cantón: el área es 'Total <Cantón>' (descarta Urbana/Rural,
    # los totales provinciales 'Total Azuay' y el 'Total Nacional')
    cantones = datos[datos.apply(
        lambda f: f["area"] == f"Total " + str(f["canton"]) and not str(f["canton"]).startswith("Total"),
        axis=1,
    )].copy()
    cantones["poblacion_2022"] = (
        cantones["total"].str.replace(",", "", regex=False).astype(float)
    )
    pob = cantones[["provincia", "canton", "poblacion_2022"]].reset_index(drop=True)
    pob["canton_norm"] = pob["canton"].apply(normalizar_nombre)
    return pob.drop_duplicates(subset="canton_norm", keep="first")


def sismos_con_canton(catalogo: pd.DataFrame, cantones: gpd.GeoDataFrame,
                      max_dist_proximidad_km: float = 150.0) -> gpd.GeoDataFrame:
    """Une espacialmente cada sismo con el cantón donde ocurrió (sjoin).

    Los sismos frente a la costa (zona de subducción, fuera de todo polígono
    cantonal) se asignan al cantón más cercano si están a menos de
    ``max_dist_proximidad_km`` km, para no subestimar el peligro de los
    cantones costeros. La distancia al cantón queda en 'dist_km'.
    """
    puntos = gpd.GeoDataFrame(
        catalogo.copy(),
        geometry=gpd.points_from_xy(catalogo["longitude"], catalogo["latitude"]),
        crs="EPSG:4326",
    )
    # 1) Sismos dentro de un polígono cantonal
    unido = gpd.sjoin(puntos, cantones, how="left", predicate="within")
    unido = unido.drop(columns=["index_right"]) if "index_right" in unido.columns else unido
    unido["dist_km"] = 0.0

    # 2) Sismos fuera (mayormente mar adentro): cantón más cercano dentro del radio
    fuera = unido["canton"].isna()
    if fuera.any():
        proyeccion = "ESRI:54009"                    # métrica, buena para distancias locales
        cercanos = gpd.sjoin_nearest(
            puntos[fuera].to_crs(proyeccion), cantones.to_crs(proyeccion),
            how="left", max_distance=max_dist_proximidad_km * 1000,
            distance_col="dist_km",
        )
        cercanos = cercanos.drop(columns=["index_right"]) if "index_right" in cercanos.columns else cercanos
        # Un punto puede empatar a la misma distancia con dos polígonos: nos
        # quedamos con la primera coincidencia (una fila por sismo)
        cercanos = cercanos[~cercanos.index.duplicated(keep="first")]
        unido.loc[fuera, ["canton", "canton_norm", "dist_km"]] = cercanos[
            ["canton", "canton_norm", "dist_km"]].values
        unido["dist_km"] = pd.to_numeric(unido["dist_km"], errors="coerce")
    return unido


def agregar_por_canton(sismos_canton: gpd.GeoDataFrame) -> pd.DataFrame:
    """Agrega la sismicidad histórica por cantón.

    Además del resumen total, agrega las métricas de eventos SOMEROS
    (profundidad ≤ 70 km): son los que gobiernan la sacudida en superficie;
    la sismicidad profunda (>70 km, slab de Nazca bajo la Amazonía) atenúa
    mucho antes de llegar a superficie y no debería ponderar el peligro.
    """
    grupo = sismos_canton.groupby("canton_norm")
    resumen = grupo.agg(
        n_sismos=("id", "count"),
        mag_max=("mag", "max"),
        prof_media_km=("depth", "mean"),
        energia_total_j=("energia_j", "sum"),
        primer_sismo=("fecha_hora", "min"),
        ultimo_sismo=("fecha_hora", "max"),
    ).reset_index()
    someros = (sismos_canton[sismos_canton["depth"] <= 70]
               .groupby("canton_norm")
               .agg(n_sismos_someros=("id", "count"),
                    energia_somera_j=("energia_j", "sum"),
                    mag_max_somera=("mag", "max"))
               .reset_index())
    return resumen.merge(someros, on="canton_norm", how="left")


def construir_dataset_cantonal() -> gpd.GeoDataFrame:
    """Pipeline completo: catálogo -> sjoin -> agregado -> censo -> densidad."""
    catalogo = cargar_catalogo()
    cantones = cargar_cantones()
    poblacion = cargar_poblacion()

    sismos = sismos_con_canton(catalogo, cantones)
    resumen = agregar_por_canton(sismos)

    # Área por cantón en km² (proyección equivalente para áreas); se calcula
    # sobre la misma geometría, sin merges, para no duplicar cantones homónimos
    # (Bolívar y Olmedo existen en dos provincias distintas)
    cantones["area_km2"] = cantones.to_crs("ESRI:54009").geometry.area.values / 1e6

    base = cantones.merge(resumen, on="canton_norm", how="left")
    base = base.merge(poblacion[["canton_norm", "provincia", "poblacion_2022"]],
                      on="canton_norm", how="left")
    # Cantones sin sismos M>=4 registrados dentro de su polígono
    for col, val in [("n_sismos", 0), ("mag_max", np.nan), ("prof_media_km", np.nan),
                     ("energia_total_j", 0.0), ("n_sismos_someros", 0),
                     ("energia_somera_j", 0.0), ("mag_max_somera", np.nan)]:
        base[col] = base[col].fillna(val)

    base["poblacion_2022"] = base["poblacion_2022"].fillna(0)
    base["densidad_hab_km2"] = np.where(base["area_km2"] > 0,
                                        base["poblacion_2022"] / base["area_km2"], 0)
    return base, catalogo, sismos


def ejecutar_pipeline() -> None:
    """Ejecuta todo el pipeline y guarda los archivos procesados."""
    base, catalogo, sismos = construir_dataset_cantonal()

    catalogo.to_csv(os.path.join(PROC, "catalogo_limpio.csv"), index=False)
    sismos.drop(columns="geometry").to_csv(
        os.path.join(PROC, "sismos_con_canton.csv"), index=False)
    tabular = base.drop(columns="geometry")
    tabular.to_csv(os.path.join(PROC, "cantones_sismicidad_poblacion.csv"), index=False)
    base.to_file(os.path.join(PROC, "cantones_riesgo.geojson"), driver="GeoJSON")

    print(f"[ok] Catálogo limpio: {len(catalogo)} sismos (1983-2026)")
    print(f"[ok] Sismos asignados a cantón: {sismos['canton'].notna().sum()}")
    print(f"[ok] Cantones con población censada: {(base['poblacion_2022']>0).sum()}/{len(base)}")
    print("[ok] Archivos generados en data/processed/")


if __name__ == "__main__":
    ejecutar_pipeline()
