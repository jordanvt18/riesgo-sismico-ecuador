# -*- coding: utf-8 -*-
"""
Genera el sitio estático de GitHub Pages (docs/index.html).

Incluye:
- Mapa coroplético INTERACTIVO por cantón (índice de riesgo / peligro / exposición)
- Gráfico interactivo del ajuste Omori-Utsu de las réplicas de Pedernales 2016
- Tabla top-10 de riesgo, tarjetas de cifras clave y figuras del proyecto
- Advertencia destacada: este proyecto NO predice sismos

Uso:  python src/build_pages.py
"""
import json
import os
import shutil

import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

DOCS = os.path.join(BASE, "docs")
FIGS = os.path.join(DOCS, "figures")
os.makedirs(FIGS, exist_ok=True)

COLOR_BASE = "#0F2743"        # azul petróleo (identidad del sitio)
COLOR_ACENTO = "#C8102E"      # rojo bandera


# ------------------------------------------------------------------ datos
def cargar_datos():
    base = gpd.read_file("data/processed/cantones_riesgo.geojson")
    tabla = pd.read_csv("data/processed/cantones_indice_riesgo.csv")
    return base, tabla


def ajustar_omori_sitio():
    """Repite el ajuste del notebook 05 para alimentar el gráfico interactivo."""
    import sys
    sys.path.insert(0, BASE)
    from src.models import tasa_omori, ajustar_omori_mle

    cat = pd.read_csv("data/raw/catalogo_sismico_ecuador_M3_1983_2026.csv")
    cat["fecha_hora"] = pd.to_datetime(cat["time"], utc=True)
    cat = cat[cat["type"] == "earthquake"]
    abril = cat[(cat["fecha_hora"] >= "2016-04-16") & (cat["fecha_hora"] <= "2016-04-17")]
    principal = abril.loc[abril["mag"].idxmax()]
    dist = np.hypot(cat["latitude"] - principal["latitude"],
                    cat["longitude"] - principal["longitude"])
    seq = cat[(dist * 111 <= 150) & (cat["fecha_hora"] > principal["fecha_hora"]) &
              (cat["fecha_hora"] <= principal["fecha_hora"] + pd.Timedelta(days=120)) &
              (cat["mag"] >= 4.5)].copy()
    seq["dias"] = (seq["fecha_hora"] - principal["fecha_hora"]).dt.total_seconds() / 86400

    dias = np.arange(1, 121)
    tasas = np.array([((seq["dias"] >= d - 0.5) & (seq["dias"] < d + 0.5)).sum()
                      for d in dias], dtype=float)
    params, cov = ajustar_omori_mle(seq.loc[seq["dias"] <= 60, "dias"].values, T=60)
    pred = tasa_omori(dias.astype(float), *params)
    return dias, tasas, pred, params, cov


# --------------------------------------------------------------- mapa plotly
def construir_mapa(base: gpd.GeoDataFrame):
    """Mapa coroplético interactivo con selector de indicador (dropdown)."""
    mapa = base[base["provincia"] != "Galápagos"].copy()  # vista continental
    mapa["densidad_hab_km2"] = mapa["densidad_hab_km2"].round(1)
    # Las columnas de fecha (Timestamp) no son serializables a GeoJSON
    mapa = mapa.drop(columns=["primer_sismo", "ultimo_sismo"], errors="ignore")
    # Reducimos la precisión de vértices: el mapa es nacional, no catastral
    mapa["geometry"] = mapa.geometry.set_precision(0.002)
    geojson = json.loads(mapa.to_json())

    variables = [
        ("indice_riesgo", "Índice de riesgo (peligro × exposición)", "YlOrRd", "Riesgo (0–100)"),
        ("indice_peligro", "Índice de peligro sísmico somero (1983–2026)", "Sunset", "Peligro (0–100)"),
        ("densidad_hab_km2", "Exposición: densidad (hab/km², Censo 2022)", "PuBu", "hab/km²"),
        ("mag_max", "Magnitud máxima histórica registrada", "Viridis", "Magnitud"),
    ]

    fig = go.Figure()
    botones = []
    for i, (col, titulo, escala, etiqueta_cb) in enumerate(variables):
        mapa[col] = pd.to_numeric(mapa[col], errors="coerce")
        traza = go.Choroplethmapbox(
            geojson=geojson, locations=mapa["canton_norm"],
            featureidkey="properties.canton_norm", z=mapa[col].fillna(0),
            colorscale=escala,
            marker=dict(opacity=0.85, line=dict(width=0.4, color="#37474F")),
            customdata=np.stack([mapa["canton"], mapa["provincia"].fillna("—"),
                                 mapa["poblacion_2022"].fillna(0).astype(int),
                                 mapa["n_sismos_someros"].fillna(0).astype(int),
                                 mapa["mag_max_somera"].fillna(0)], axis=-1),
            hovertemplate=("<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                           "Población 2022: %{customdata[2]:,}<br>"
                           "Sismos someros M≥4: %{customdata[3]}<br>"
                           "Magnitud máx. somera: %{customdata[4]}<br>"
                           f"{titulo.split(':')[0] if ':' in titulo else titulo}: %{{z:.1f}}"
                           "<extra></extra>"),
            visible=(i == 0),
            colorbar=dict(title=dict(text=etiqueta_cb, side="right"),
                          thickness=14, outlinewidth=0),
        )
        fig.add_trace(traza)
        botones.append(dict(label=titulo[:38], method="update",
                            args=[{"visible": [j == i for j in range(len(variables))]},
                                  {"coloraxis.colorscale": escala}]))
    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=-1.5, lon=-78.5), zoom=5.6),
        margin=dict(l=0, r=0, t=46, b=0), height=560,
        # Sin título interno: el encabezado HTML de la sección ya lo enuncia
        updatemenus=[dict(buttons=botones, direction="down",
                          x=0.0, xanchor="left", y=1.015, yanchor="top",
                          bgcolor="white", bordercolor="#B0BEC5")],
    )
    return fig


# ------------------------------------------------------- gráfico Omori
def construir_omori(dias, tasas, pred, params, cov):
    K, c, p = params
    dos_sigma = 2 * np.sqrt(np.abs(np.diag(cov)))
    fig = go.Figure()
    fig.add_bar(x=dias, y=tasas, name="Réplicas observadas/día",
                marker_color="#7896B5", opacity=0.75)
    fig.add_scatter(x=dias, y=pred, mode="lines", name="Omori-Utsu ajustada",
                    line=dict(color=COLOR_ACENTO, width=2.5))
    fig.add_vrect(x0=60.5, x1=120, fillcolor="#F4C430", opacity=0.15,
                  line_width=0, annotation_text="validación (61–120)",
                  annotation_position="top left", annotation_font_size=10)
    fig.update_layout(
        title=f"Réplicas Pedernales 2016 (M≥4.5, radio 150 km) — "
              f"K={K:.1f}±{dos_sigma[0]:.1f}, c={c:.2f}±{dos_sigma[1]:.2f} d, p={p:.2f}±{dos_sigma[2]:.2f}",
        title_font_size=13, xaxis_title="Días desde el sismo principal (16-abr-2016)",
        yaxis_title="Réplicas por día", height=430,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(orientation="h", x=1, y=1, xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="#B0BEC5", borderwidth=1),
        hovermode="x unified",
    )
    return fig


# ----------------------------------------------------- consultor accionable
# Zonificación NEC aproximada a nivel provincial (igual que el notebook 06)
ZONA_NEC_APROX = {
    "Esmeraldas": 4, "Manabí": 4, "Galápagos": 4,
    "Guayas": 3, "Santa Elena": 3, "Los Ríos": 3, "Santo Domingo de los Tsáchilas": 3,
    "Pichincha": 3, "Carchi": 3, "Imbabura": 3, "Cotopaxi": 3, "Tungurahua": 3,
    "Bolívar": 2, "Chimborazo": 2, "Cañar": 2, "Azuay": 2, "Loja": 2, "El Oro": 2,
    "Morona Santiago": 1, "Napo": 1, "Orellana": 1, "Pastaza": 1,
    "Sucumbíos": 1, "Zamora Chinchipe": 1,
}
PROVINCIAS_COSTERAS = {"ESMERALDAS", "MANABI", "GUAYAS", "SANTA ELENA", "EL ORO", "GALAPAGOS"}

# Acciones recomendadas por nivel de prioridad (clasificación relativa nacional)
ACCIONES_NIVEL = {
    3: [  # percentil ≥75 del índice de riesgo: prioridad alta
        "Solicitar una evaluación técnica de la vivienda, en particular si es autoconstruida o de adobe; es la medida de mayor impacto individual.",
        "Asegurar a la estructura muebles altos, estanterías, calentadores y tanques; identificar espacios seguros (junto a muros portantes, lejos de ventanas).",
        "Preparar el kit familiar de emergencia (agua, alimentos no perecederos, linterna, radio a pilas, botiquín, copias de documentos) y un plan con puntos de encuentro.",
        "Participar en los simulacros y conocer las rutas de evacuación del barrio y del centro de trabajo o de estudios.",
    ],
    2: [  # percentil 50–75: prioridad moderada
        "Preparar el kit familiar de emergencia y acordar un plan familiar con puntos de encuentro y un contacto fuera de la zona.",
        "Fijar muebles altos y objetos pesados; revisar instalaciones de gas y electricidad con apoyo técnico.",
        "Conocer la zona NEC de su cantón y verificar que remodelaciones y ampliaciones cumplan la norma.",
    ],
    1: [  # línea base nacional
        "Tener el kit básico de emergencia y un plan familiar acordado, como práctica general de resiliencia.",
        "Familiarizarse con las recomendaciones oficiales del SNGRE y del IG-EPN antes de que ocurra una emergencia.",
    ],
}
ACCION_COSTA = ("Al estar en una provincia costera, identificar desde ya las rutas y puntos de "
                "evacuación ante tsunami: ante un sismo fuerte que dificulte ponerse de pie o que "
                "duración prolongada, diríjase de inmediato a terreno alto, sin esperar la orden oficial.")
ACCION_POSTSISMO = ("Tras un sismo principal, la tasa de réplicas decae de forma hiperbólica "
                    "(p ≈ 0.9 en la secuencia de Pedernales): la mayor parte se concentra en horas y días. "
                    "No reingrese a edificaciones dañadas mientras la tasa sea alta, permanezca atento a los "
                    "canales oficiales (IG-EPN, SNGRE) y anticipe la evacuación en la costa.")


def _sin_acentos(texto: str) -> str:
    import unicodedata
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


def construir_datos_accion(tabla: pd.DataFrame):
    """Compacta por cantón lo necesario para el consultor del sitio (JS puro)."""
    import unicodedata
    normas = lambda s: "".join(c for c in unicodedata.normalize("NFKD", str(s))
                               if not unicodedata.combining(c)).upper().strip()
    registros, opciones = {}, []
    for fila in tabla.itertuples():
        clave = normas(fila.canton)
        registros[clave] = {
            "c": fila.canton, "p": fila.provincia if isinstance(fila.provincia, str) else "—",
            "pob": int(fila.poblacion_2022 or 0),
            "ip": round(float(fila.indice_peligro or 0), 1),
            "ir": round(float(fila.indice_riesgo or 0), 1),
            "ns": int(fila.n_sismos_someros or 0),
            "mm": round(float(fila.mag_max_somera or 0), 1),
            "den": round(float(fila.densidad_hab_km2 or 0), 1),
            "z": ZONA_NEC_APROX.get(fila.provincia if isinstance(fila.provincia, str) else "", None),
            "co": normas(fila.provincia) in PROVINCIAS_COSTERAS if isinstance(fila.provincia, str) else False,
        }
        opciones.append(f'<option value="{fila.canton}">')
    umbrales = {
        "ir75": round(float(tabla["indice_riesgo"].quantile(0.75)), 1),
        "ir50": round(float(tabla["indice_riesgo"].quantile(0.50)), 1),
        "ip75": round(float(tabla["indice_peligro"].quantile(0.75)), 1),
        "ip50": round(float(tabla["indice_peligro"].quantile(0.50)), 1),
    }
    return registros, umbrales, "\n".join(opciones)


JS_CONSULTOR = """
<script>
const DATOS = __DATOS_JSON__;
const UMBRALES = __UMBRALES_JSON__;
const ACCIONES = __ACCIONES_JSON__;
const ACCION_COSTA = __ACCION_COSTA_JSON__;
const ZONA_TXT = {1:"I (menor)", 2:"II", 3:"III", 4:"IV (mayor)"};
function sinAcentos(s){return s.normalize("NFKD").replace(/[\\u0300-\\u036f]/g,"").toUpperCase().trim();}
function nivel(v, u75, u50){ return v>=u75 ? 3 : (v>=u50 ? 2 : 1); }
const ETIQ_NIVEL = {3:"prioridad alta", 2:"prioridad moderada", 1:"línea base"};
function li(txt){ const e=document.createElement("li"); e.textContent=txt; return e; }
function consultar(){
  const entrada = document.getElementById("entrada-canton");
  const caja = document.getElementById("resultado-canton");
  const clave = sinAcentos(entrada.value);
  caja.innerHTML = "";
  const d = DATOS[clave];
  if(!d){
    const av = document.createElement("p");
    av.textContent = "No se encontró el cantón. Verifique la escritura o selecciónelo de la lista.";
    caja.appendChild(av); return;
  }
  const nR = nivel(d.ir, UMBRALES.ir75, UMBRALES.ir50);
  const nP = nivel(d.ip, UMBRALES.ip75, UMBRALES.ip50);
  const h3 = document.createElement("h3");
  h3.textContent = d.c + " (" + d.p + ")";
  caja.appendChild(h3);
  const dl = document.createElement("dl");
  dl.style.cssText = "display:grid;grid-template-columns:auto 1fr;gap:.25rem .9rem;font-size:.92rem;";
  const filas = [
    ["Índice de riesgo relativo", d.ir.toFixed(1) + " / 100 — " + ETIQ_NIVEL[nR]],
    ["Índice de peligro somero", d.ip.toFixed(1) + " / 100 — " + ETIQ_NIVEL[nP]],
    ["Zona NEC aprox. (provincial)", d.z ? ZONA_TXT[d.z] : "no asignada"],
    ["Población (Censo 2022)", d.pob.toLocaleString("es-EC") + " hab."],
    ["Densidad", d.den.toLocaleString("es-EC") + " hab/km²"],
    ["Sismos someros M≥4 (1983–2026)", String(d.ns)],
    ["Magnitud máx. somera registrada", d.mm > 0 ? "M" + d.mm.toFixed(1) : "sin registro"],
  ];
  for (const [k, v] of filas){
    const dt=document.createElement("dt"); dt.textContent=k; dt.style.cssText="color:#5B7083;";
    const dd=document.createElement("dd"); dd.textContent=v; dd.style.margin="0";
    dl.appendChild(dt); dl.appendChild(dd);
  }
  caja.appendChild(dl);
  const h4 = document.createElement("h4");
  h4.textContent = "Acciones recomendadas para su cantón";
  caja.appendChild(h4);
  const ul = document.createElement("ul");
  for (const a of ACCIONES[nR]) ul.appendChild(li(a));
  if (d.co) ul.appendChild(li(ACCION_COSTA));
  caja.appendChild(ul);
  const nota = document.createElement("p");
  nota.style.cssText = "font-size:.8rem;color:#5B7083;";
  nota.textContent = "Clasificación relativa a escala nacional y de carácter orientativo: no sustituye la microzonificación sísmica local, la evaluación estructural profesional ni la norma NEC.";
  caja.appendChild(nota);
}
document.getElementById("btn-consultar").addEventListener("click", consultar);
document.getElementById("entrada-canton").addEventListener("keydown", function(e){ if(e.key==="Enter") consultar(); });
</script>
"""


# ------------------------------------------------------------- plantilla HTML
PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Riesgo Sísmico en Ecuador — peligro, exposición y réplicas</title>
<meta name="description" content="Análisis CRISP-DM de riesgo sísmico en Ecuador con fuentes oficiales: índice de peligro × exposición por cantón (1983–2026) y pronóstico estadístico de tasa de réplicas (Omori-Utsu, Pedernales 2016). No predice sismos.">
<style>
:root {{ --base:{COLOR_BASE}; --acento:{COLOR_ACENTO}; --papel:#F7F9FB; --tinta:#22303C; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
       background:var(--papel); color:var(--tinta); line-height:1.55; }}
header {{ background:linear-gradient(135deg,var(--base) 0%,#1B3F63 100%); color:#fff;
         padding:2.2rem 1.2rem 1.6rem; }}
header h1 {{ margin:0 0 .3rem; font-size:clamp(1.4rem,3.5vw,2.1rem); }}
header p.sub {{ margin:0; opacity:.85; max-width:60rem; }}
nav {{ background:#0B1D31; position:sticky; top:0; z-index:50; }}
nav a {{ color:#E3ECF5; text-decoration:none; padding:.7rem .9rem; display:inline-block;
        font-size:.92rem; }}
nav a:hover {{ background:#16324F; }}
main {{ max-width:72rem; margin:0 auto; padding:1.2rem; }}
section {{ background:#fff; border:1px solid #E1E8EE; border-radius:12px;
          padding:1.4rem; margin:1.2rem 0; box-shadow:0 1px 3px rgba(16,42,67,.06); }}
h2 {{ margin:.2rem 0 1rem; color:var(--base); font-size:1.25rem;
     border-bottom:3px solid #E7EDF3; padding-bottom:.45rem; }}
.aviso {{ border-left:6px solid var(--acento); }}
.aviso .no {{ color:var(--acento); }}
.tarjetas {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
            gap:.8rem; margin:1rem 0; }}
.tarjeta {{ background:#F2F6FA; border-radius:10px; padding:.9rem; text-align:center; }}
.tarjeta .valor {{ font-size:1.6rem; font-weight:700; color:var(--base); }}
.tarjeta .etiqueta {{ font-size:.8rem; color:#5B7083; }}
table {{ border-collapse:collapse; width:100%; font-size:.92rem; }}
th,td {{ padding:.5rem .6rem; text-align:left; border-bottom:1px solid #E7EDF3; }}
th {{ background:#F2F6FA; color:var(--base); }}
tr:hover td {{ background:#FAFCFE; }}
.galeria {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
           gap:1rem; }}
.galeria figure {{ margin:0; }}
.galeria img {{ width:100%; border-radius:8px; border:1px solid #E1E8EE; }}
figcaption {{ font-size:.8rem; color:#5B7083; margin-top:.35rem; }}
footer {{ text-align:center; padding:1.6rem 1rem 2.4rem; color:#5B7083; font-size:.85rem; }}
a.boton {{ display:inline-block; background:var(--base); color:#fff; padding:.55rem .95rem;
          border-radius:8px; text-decoration:none; font-size:.9rem; margin:.2rem .35rem .2rem 0; }}
.nota {{ font-size:.8rem; color:#5B7083; }}
</style>
</head>
<body>
<header>
  <h1>Riesgo sísmico en Ecuador</h1>
  <p class="sub">Índice de peligro y exposición poblacional por cantón (1983–2026) y
  pronóstico estadístico de la tasa de réplicas de la secuencia de Pedernales 2016
  (Omori-Utsu) — marco CRISP-DM, fuentes oficiales, código abierto.</p>
</header>
<nav>
  <a href="#aviso">Alcance</a><a href="#mapa">Cartograma</a>
  <a href="#riesgo">Clasificación</a><a href="#replicas">Réplicas</a>
  <a href="#accion">Uso práctico</a>
  <a href="#figuras">Figuras</a><a href="#metodologia">Metodología</a>
  <a href="https://github.com/jordanvt18/riesgo-sismico-ecuador" target="_blank" rel="noopener">GitHub ↗</a>
</nav>
<main>

<section class="aviso" id="aviso">
  <h2>Alcance del estudio y premisa científica</h2>
  <p>La <b class="no">predicción determinista</b> de terremotos —fecha, hora, lugar y
  magnitud de un evento concreto— no resulta alcanzable con el estado actual del
  conocimiento sismológico (USGS y literatura especializada), y este estudio no la
  persigue. Su aporte comprende: (1) un índice de <b>peligro sísmico relativo</b>
  por cantón, derivado de 43 años de catálogo oficial; (2) la <b>exposición
  poblacional</b> del Censo 2022 y su integración con el peligro en un índice de
  <b>riesgo relativo</b> orientado a priorizar la inversión en construcción
  sismorresistente; y (3) un pronóstico estadístico de la <b>tasa esperada de
  réplicas</b> tras un sismo principal —una tasa, como estadístico de un proceso
  estocástico, no la ocurrencia de eventos individuales.</p>
</section>

<section id="mapa">
  <h2>Cartograma interactivo por cantón</h2>
  {MAPA_HTML}
  <p class="nota">Pase el cursor sobre cada cantón. Los sismos frente a la costa
  (subducción) se asignan al cantón más cercano (≤150 km). El peligro usa solo
  sismicidad somera (≤70 km). Galápagos se excluye de la vista.</p>
</section>

<section id="riesgo">
  <h2>Clasificación cantonal por índice de riesgo relativo</h2>
  <div class="tarjetas">
    <div class="tarjeta"><div class="valor">2.589</div><div class="etiqueta">sismos M≥4 (1983–2026)</div></div>
    <div class="tarjeta"><div class="valor">224</div><div class="etiqueta">cantones analizados</div></div>
    <div class="tarjeta"><div class="valor">221</div><div class="etiqueta">cantones con censo 2022</div></div>
    <div class="tarjeta"><div class="valor">0.86</div><div class="etiqueta">exponente p de Omori (rango típico 0.8–1.5)</div></div>
  </div>
  {TABLA_HTML}
  <p class="nota">Escala relativa 0–100 dentro del Ecuador. La clasificación
  responde a la pregunta de priorización territorial de la inversión
  sismorresistente y no a la ocurrencia temporal de futuros eventos.</p>
</section>

<section id="replicas">
  <h2>Pronóstico de la tasa de réplicas — Pedernales 2016 (M7.8)</h2>
  {OMORI_HTML}
  <p class="nota">Entrenamiento con los días 1–60 (máxima verosimilitud bajo un proceso
  de Poisson no estacionario) y <b>validación fuera de muestra</b> contra los días
  61–120 observados. El modelo estima la <b>tasa diaria esperada</b> de la secuencia
  (M≥4.5, radio de 150 km), no la ocurrencia de eventos individuales.</p>
</section>

<section id="figuras">
  <h2>Figuras del análisis</h2>
  <div class="galeria">
    <figure><img src="figures/05_mapa_secuencia.png" alt="Secuencia de réplicas de Pedernales 2016" loading="lazy">
      <figcaption>Epicentros de las réplicas de Pedernales 2016 (color: días desde el sismo principal).</figcaption></figure>
    <figure><img src="figures/06_contraste_nec.png" alt="Contraste con zonificación NEC" loading="lazy">
      <figcaption>¿Coincide el peligro histórico con la zonificación NEC? (Zona IV claramente arriba).</figcaption></figure>
    <figure><img src="figures/06_embalses_exploracion.png" alt="Exploración de sismicidad cerca de embalses" loading="lazy">
      <figcaption>Exploración (sin hipótesis causal) cerca de Mazar, Paute y Coca Codo Sinclair.</figcaption></figure>
    <figure><img src="figures/demo_alerta_temprana.png" alt="Demo educativa de alerta temprana P/S" loading="lazy">
      <figcaption>DEMO EDUCATIVA del principio de alerta temprana por diferencia de velocidad P/S — no es un sistema real.</figcaption></figure>
  </div>
</section>

<section id="accion">
  <h2>¿Cómo usar esta información? De los índices a la acción</h2>
  <p>Los índices de este estudio no son un fin descriptivo: son un instrumento de
  <b>priorización</b>. La pregunta práctica que responden es «con recursos limitados para
  la reducción del riesgo, ¿dónde empiezo?». Esta sección traduce los resultados en
  acciones concretas por audiencia y pone a disposición un consultor cantonal.</p>

  <h3 style="margin:1.2rem 0 .4rem;font-size:1.05rem;">Consulte el perfil y las acciones para su cantón</h3>
  <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;">
    <input id="entrada-canton" list="lista-cantones" placeholder="Escriba su cantón (p. ej., Manta)"
           style="flex:1;min-width:230px;padding:.55rem .7rem;border:1px solid #B0BEC5;border-radius:8px;font-size:.95rem;">
    <datalist id="lista-cantones">__OPCIONES_CANTONES__</datalist>
    <button id="btn-consultar" type="button"
            style="padding:.55rem 1.1rem;background:#0F2743;color:#fff;border:none;border-radius:8px;font-size:.95rem;cursor:pointer;">
      Consultar</button>
  </div>
  <div id="resultado-canton" style="margin-top:1rem;background:#F2F6FA;border-radius:10px;padding:1rem;"></div>

  <h3 style="margin:1.6rem 0 .4rem;font-size:1.05rem;">Acciones por audiencia</h3>
  <details style="border:1px solid #E1E8EE;border-radius:8px;padding:.7rem .9rem;margin:.5rem 0;">
    <summary style="cursor:pointer;font-weight:600;">Ciudadanía y hogares</summary>
    <ul style="margin:.6rem 0 0;">
      <li>Consulte el perfil de su cantón (arriba) y la zona NEC provincial; use ambos como referencia para decidir inversiones en su vivienda.</li>
      <li>Kit familiar de emergencia: agua (≈4 L por persona al día, para tres días), alimentos no perecederos, linterna, radio a pilas, botiquín y copias de documentos.</li>
      <li>Plan familiar de emergencia: puntos de encuentro, rutas de evacuación y un contacto fuera de la zona afectable.</li>
      <li>Reducción de vulnerabilidad en casa: fijar muebles altos y calentadores, revisar gas y electricidad; en viviendas autoconstruidas o de adobe, solicitar evaluación técnica municipal.</li>
    </ul>
  </details>
  <details style="border:1px solid #E1E8EE;border-radius:8px;padding:.7rem .9rem;margin:.5rem 0;">
    <summary style="cursor:pointer;font-weight:600;">Gobiernos autónomos descentralizados (GAD) y gestores de riesgo</summary>
    <ul style="margin:.6rem 0 0;">
      <li>Priorizar el reforzamiento de edificaciones esenciales (hospitales, escuelas, cuarteles de bomberos) con el criterio peligro × exposición del estudio.</li>
      <li>Incorporar la clasificación cantonal en los planes de ordenamiento territorial y de contingencia; exigir el cumplimiento de la NEC en permisos de construcción.</li>
      <li>Construir catastros de edificaciones vulnerables (autoconstrucción, adobe) y programar simulacros anuales con la comunidad.</li>
    </ul>
  </details>
  <details style="border:1px solid #E1E8EE;border-radius:8px;padding:.7rem .9rem;margin:.5rem 0;">
    <summary style="cursor:pointer;font-weight:600;">Educación y medios de comunicación</summary>
    <ul style="margin:.6rem 0 0;">
      <li>Incorporar simulacros y contenidos de preparación en el calendario escolar, con énfasis en los cantones de prioridad alta.</li>
      <li>Comunicar las réplicas con el lenguaje correcto del modelo: tasas esperadas que decaen en el tiempo, nunca anuncios de eventos individuales.</li>
      <li>Citar las fuentes oficiales (IG-EPN, SNGRE) y evitar la difusión de «predicciones» sin sustento.</li>
    </ul>
  </details>

  <h3 style="margin:1.6rem 0 .4rem;font-size:1.05rem;">Tras un sismo fuerte: lectura práctica del modelo de réplicas</h3>
  <p style="background:#FDF3F3;border-left:4px solid #C8102E;padding:.8rem .9rem;border-radius:0 8px 8px 0;font-size:.93rem;">
  La mayor tasa de réplicas se concentra en las primeras horas y días y luego decae de
  forma hiperbólica (en Pedernales 2016, p ≈ 0.9: la tasa cayó de ≈5 réplicas/día al
  inicio a menos de 1/día hacia la tercera semana). En la práctica: <b>no reingrese a
  edificaciones dañadas mientras la tasa sea alta</b>, espere las inspecciones oficiales,
  y en la costa anticipe la evacuación a terreno alto. Las réplicas esperadas por día son
  un estadístico: cada una puede sentirse con intensidad.</p>
</section>

<section id="metodologia">
  <h2>Metodología y reproducibilidad</h2>
  <p><b>Peligro (0–100):</b> ½ frecuencia de sismos M≥4 someros (≤70 km) + ½ energía
  liberada (escala Gutenberg-Richter E = 10^(1.5M+4.8) J), normalizadas.
  <b>Exposición:</b> densidad poblacional del Censo 2022 (INEC), log-normalizada.
  <b>Riesgo = peligro × exposición.</b> <b>Réplicas:</b> ley de Omori-Utsu
  r(t) = K/(t+c)^p ajustada por máxima verosimilitud.</p>
  <p>Fuentes oficiales: catálogo sísmico IG-EPN/USGS-FDSN, Censo 2022 (INEC),
  límites cantonales IGM/CONALI (geoBoundaries), zonificación NEC-SE-DS.</p>
  <a class="boton" href="https://github.com/jordanvt18/riesgo-sismico-ecuador" target="_blank" rel="noopener">Repositorio GitHub</a>
  <a class="boton" href="https://github.com/jordanvt18/riesgo-sismico-ecuador/blob/main/README.md" target="_blank" rel="noopener">README completo</a>
  <a class="boton" href="https://github.com/jordanvt18/riesgo-sismico-ecuador/tree/main/notebooks" target="_blank" rel="noopener">Notebooks CRISP-DM</a>
</section>

</main>
<footer>
  Sitio generado automáticamente por <code>src/build_pages.py</code> ·
  Código bajo licencia MIT · Datos: IG-EPN, USGS, INEC, IGM/CONALI ·
  El estudio no persigue la predicción determinista de terremotos ·
  <a href="https://github.com/jordanvt18" target="_blank" rel="noopener">@jordanvt18</a>
</footer>
</body>
</html>
"""


def main() -> None:
    base, tabla = cargar_datos()

    # Mapa interactivo
    mapa_fig = construir_mapa(base)
    mapa_html = mapa_fig.to_html(full_html=False, include_plotlyjs="cdn",
                                 config={"displayModeBar": False, "responsive": True})

    # Omori interactivo
    dias, tasas, pred, params, cov = ajustar_omori_sitio()
    omori_html = construir_omori(dias, tasas, pred, params, cov).to_html(
        full_html=False, include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True})

    # Tabla top 10
    top = tabla.nlargest(10, "indice_riesgo")
    filas = "".join(
        f"<tr><td>{i+1}</td><td><b>{r.canton}</b></td><td>{r.provincia}</td>"
        f"<td>{r.indice_peligro:.1f}</td><td>{r.densidad_hab_km2:,.0f}</td>"
        f"<td><b>{r.indice_riesgo:.1f}</b></td></tr>"
        for i, r in enumerate(top.itertuples()))
    tabla_html = (
        "<table><tr><th>#</th><th>Cantón</th><th>Provincia</th><th>Peligro</th>"
        f"<th>Densidad (hab/km²)</th><th>Riesgo</th></tr>{filas}</table>")

    # Figuras estáticas
    for nombre in ["05_mapa_secuencia.png", "06_contraste_nec.png",
                   "06_embalses_exploracion.png", "demo_alerta_temprana.png"]:
        origen = os.path.join("reports", "figures", nombre)
        if os.path.exists(origen):
            shutil.copy(origen, os.path.join(FIGS, nombre))

    html = PLANTILLA.format(COLOR_BASE=COLOR_BASE, COLOR_ACENTO=COLOR_ACENTO,
                            MAPA_HTML=mapa_html, OMORI_HTML=omori_html,
                            TABLA_HTML=tabla_html)

    # Inyección del consultor cantonal (JS puro, sin backend): los tokens se
    # sustituyen después de .format() para no escapar las llaves del código JS
    registros, umbrales, opciones = construir_datos_accion(tabla)
    html = html.replace("__OPCIONES_CANTONES__", opciones)
    html = (html
            .replace("</body>", JS_CONSULTOR + "</body>")
            .replace("__DATOS_JSON__", json.dumps(registros, ensure_ascii=False, separators=(",", ":")))
            .replace("__UMBRALES_JSON__", json.dumps(umbrales))
            .replace("__ACCIONES_JSON__", json.dumps(ACCIONES_NIVEL, ensure_ascii=False, separators=(",", ":")))
            .replace("__ACCION_COSTA_JSON__", json.dumps(ACCION_COSTA, ensure_ascii=False)))

    salida = os.path.join(DOCS, "index.html")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    peso = os.path.getsize(salida) / 1e6
    print(f"[ok] Sitio generado: docs/index.html ({peso:.1f} MB)")


if __name__ == "__main__":
    main()
