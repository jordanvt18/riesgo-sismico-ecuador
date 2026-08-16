# -*- coding: utf-8 -*-
"""
Descarga de datos oficiales para el proyecto de riesgo sísmico en Ecuador.

Fuentes:
1) Catálogo sísmico regional (1983 - 2026): servicio FDSN del USGS
   (fuente oficial; complementario al catálogo del IG-EPN, cuya descarga
   masiva requiere solicitud en https://www.igepn.edu.ec/descarga-de-datos/).
2) Límites cantonales: geoBoundaries gbOpen ECU ADM2 (basado en INEC/OCHA,
   licencia CC BY 3.0 IGO).
3) Población por cantón: tabulados del Censo de Población y Vivienda 2022
   del INEC (espejo público de los CSV oficiales).

Uso:  python src/fetch_data.py
"""
import os
import sys
import zipfile
import io
import requests

# Rutas base del proyecto (funciona desde la raíz del repo)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

# Período histórico solicitado: desde 1983 hasta hoy (2026-08-15)
INICIO = "1983-01-01"
FIN = "2026-08-15"

# Buzón geográfico de Ecuador y mar adyacente (aprox.)
BBOX = {"minlatitude": -6.0, "maxlatitude": 3.0,
        "minlongitude": -82.0, "maxlongitude": -74.0}

URL_CATALOGO = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    f"?format=csv&starttime={INICIO}&endtime={FIN}"
    "&minmagnitude=4.0&orderby=time-asc"
    f"&minlatitude={BBOX['minlatitude']}&maxlatitude={BBOX['maxlatitude']}"
    f"&minlongitude={BBOX['minlongitude']}&maxlongitude={BBOX['maxlongitude']}"
)

URL_CANTONES = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/"
                "main/releaseData/gbOpen/ECU/ADM2/"
                "geoBoundaries-ECU-ADM2_simplified.geojson")

URL_CENSO = ("https://raw.githubusercontent.com/Yachssiton/Econometria_CensoEcu2022/"
             "main/01_2022_CPV_Estructura_poblacional_CSV.zip")

HEADERS = {"User-Agent": "Mozilla/5.0 (riesgo-sismico-ecuador; investigación educativa)"}


def descargar(url: str, destino: str) -> str:
    """Descarga un archivo con reintentos básicos y lo guarda en destino."""
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        print(f"[ok] Ya existe: {destino}")
        return destino
    print(f"[..] Descargando {url}")
    r = requests.get(url, headers=HEADERS, timeout=300)
    r.raise_for_status()
    with open(destino, "wb") as f:
        f.write(r.content)
    print(f"[ok] Guardado: {destino} ({len(r.content)/1e6:.1f} MB)")
    return destino


def main() -> None:
    # 1a) Catálogo sísmico M>=4 (CSV de eventos: tiempo, magnitud, profundidad, lat/lon)
    descargar(URL_CATALOGO, os.path.join(RAW, "catalogo_sismico_ecuador_1983_2026.csv"))

    # 1b) Catálogo M>=3 para las secuencias de réplicas y exploración de embalses
    url_m3 = URL_CATALOGO.replace("minmagnitude=4.0", "minmagnitude=3.0")
    descargar(url_m3, os.path.join(RAW, "catalogo_sismico_ecuador_M3_1983_2026.csv"))

    # 2) Límites cantonales (GeoJSON simplificado)
    descargar(URL_CANTONES, os.path.join(RAW, "cantones_ecuador.geojson"))

    # 3) Censo 2022 (ZIP con tabulados INEC) -> extraemos solo 1.1.csv
    zip_path = os.path.join(RAW, "censo2022_inec.zip")
    descargar(URL_CENSO, zip_path)
    destino_csv = os.path.join(RAW, "censo2022_poblacion_canton.csv")
    if not os.path.exists(destino_csv):
        with zipfile.ZipFile(zip_path) as z:
            with z.open("1.1.csv") as origen, open(destino_csv, "wb") as destino:
                destino.write(origen.read())
        print(f"[ok] Extraído tabulado 1.1 (población por cantón): {destino_csv}")

    print("\nListo. Datos crudos en data/raw/")


if __name__ == "__main__":
    sys.exit(main())
