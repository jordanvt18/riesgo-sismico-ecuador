# Riesgo sísmico en Ecuador: peligro, exposición y pronóstico estadístico de réplicas

Estudio de ciencia de datos sobre el riesgo sísmico del Ecuador, desarrollado
con el marco metodológico **CRISP-DM** a partir exclusivamente de fuentes
oficiales. El estudio comprende: (i) un índice de peligro sísmico relativo y su
interacción con la exposición poblacional, calculados por cantón para el
período 1983–2026, y (ii) un modelo estadístico de pronóstico de la tasa de
réplicas, calibrado y validado sobre la secuencia del terremoto de Pedernales
del 16 de abril de 2016 (M7.8).

**Sitio interactivo (GitHub Pages):** <https://jordanvt18.github.io/riesgo-sismico-ecuador/>
— cartograma por cantón, curva de decaimiento de réplicas y clasificación de
riesgo. El sitio se regenera con `python src/build_pages.py` (salida en `docs/`).

---

## 1. Alcance del estudio y premisa científica

La predicción determinista de terremotos —la especificación anticipada de
fecha, hora, lugar y magnitud de un evento concreto— no es alcanzable con el
estado actual del conocimiento sismológico, conforme lo sostiene el [USGS](https://www.usgs.gov/programs/earthquake-hazards/earthquake-prediction)
y la literatura especializada. Este estudio no persigue ese objetivo ni
podría lograrlo; se inscribe, en cambio, en el paradigma del **peligro sísmico
probabilístico**, cuyo propósito es cuantificar la distribución espacio-temporal
de la sismicidad y su interacción con la exposición de la población, y en la
estadística de secuencias de réplicas, cuyo fundamento es la ley de Omori-Utsu.

Los productos analíticos que este estudio entrega son los siguientes:

| Producto | Pregunta que responde | Cuaderno |
|---|---|---|
| Índice de peligro sísmico relativo por cantón | ¿Dónde se han concentrado la sismicidad somera y la energía liberada en el período 1983–2026? | [04](notebooks/04_modeling_peligro_exposicion.ipynb) |
| Índice de riesgo relativo (peligro × exposición) | ¿En qué territorios la confluencia de peligro y densidad poblacional prioriza la inversión en construcción sismorresistente? | [04](notebooks/04_modeling_peligro_exposicion.ipynb) |
| Pronóstico de la tasa de réplicas (Omori-Utsu) | Tras un sismo principal: ¿cuál es la tasa diaria esperada de réplicas y cuál su ley de decaimiento? | [05](notebooks/05_modeling_replicas.ipynb) |
| Validación fuera de muestra | ¿Extrapoló correctamente el modelo a los días 61–120 de la secuencia de Pedernales? | [05](notebooks/05_modeling_replicas.ipynb) y [06](notebooks/06_evaluation.ipynb) |
| Contraste con la norma NEC | ¿En qué medida coincide el peligro histórico observado con la zonificación sísmica normativa? | [06](notebooks/06_evaluation.ipynb) |
| Exploración de sismicidad en torno a grandes embalses | ¿Existen patrones espacio-temporales distinguibles cerca de Mazar, Paute y Coca Codo Sinclair? (ejercicio exploratorio, sin hipótesis causal) | [06](notebooks/06_evaluation.ipynb) |

Corresponde precisar que el modelo de réplicas estima la **tasa esperada** de
la secuencia —un estadístico con incertidumbre cuantificada, derivado de un
proceso de Poisson no estacionario— y no la ocurrencia de eventos
individuales. Esta distinción constituye una propiedad definitoria del enfoque
y delimita la validez de sus conclusiones.

## 2. Resultados principales

**Clasificación cantonal por índice de riesgo relativo** (peligro sísmico
somero histórico × densidad poblacional del Censo 2022; escala relativa 0–100):

| N.º | Cantón | Provincia | Peligro | Riesgo |
|---|---|---|---|---|
| 1 | Manta | Manabí | 62.9 | 53.9 |
| 2 | Guayaquil | Guayas | 62.4 | 51.0 |
| 3 | Salinas | Santa Elena | 52.5 | 46.9 |
| 4 | Quito | Pichincha | 55.7 | 45.2 |
| 5 | Montecristi | Manabí | 72.2 | 44.4 |
| 6 | Esmeraldas | Esmeraldas | 67.9 | 43.2 |
| 7 | Machala | El Oro | 46.5 | 40.0 |
| 8 | Santa Rosa | El Oro | 67.3 | 38.9 |
| 9 | Portoviejo | Manabí | 50.9 | 37.2 |
| 10 | Durán | Guayas | 41.2 | 35.8 |

![Mapa de riesgo](reports/figures/04_mapa_riesgo.png)

La lectura geográfica es consistente con la tectónica del margen: la franja
costera Manabí–Esmeraldas —epicentro de la secuencia de Pedernales de 2016,
sobre la interfaz de subducción Nazca–Sudamericana— coincide con las
principales aglomeraciones urbanas del litoral, de modo que peligro y
exposición se superponen exactamente allí donde el índice alcanza sus valores
máximos.

**Pronóstico de réplicas de Pedernales 2016** (M≥4.5, radio de 150 km, 120
días; entrenamiento: días 1–60, validación: días 61–120). Ley de Omori-Utsu
ajustada por máxima verosimilitud (proceso de Poisson no estacionario):

| Parámetro | Valor (±2σ) | Interpretación |
|---|---|---|
| K | 5.4 ± 2.9 | Productividad de la secuencia |
| c | 0.04 ± 0.11 días | Retardo inicial, compatible con detección inmediata |
| p | 0.86 ± 0.23 | Exponente de decaimiento hiperbólico (rango típico: 0.8–1.5) |

![Ajuste Omori](reports/figures/05_omori_ajuste_validacion.png)

**Contraste con la zonificación NEC.** La media del peligro histórico somero
crece con la zona normativa (Zona II: 18.5 < Zona III: 24.3 < Zona IV: 46.0),
con la Amazonía (Zona I: 32.1) como excepción, explicable por la sismicidad
cortical de retro-arco que la norma pondera mediante atenuación (ρ de
Spearman = 0.15, p = 0.03). El análisis pormenorizado se encuentra en el
[notebook 06](notebooks/06_evaluation.ipynb).

## 3. Datos y fuentes oficiales

| Dato | Fuente oficial | Acceso empleado |
|---|---|---|
| Catálogo sísmico 1983–agosto 2026 | IG-EPN (descarga mediante solicitud), complementado con el servicio FDSN del USGS (oficial, programático) | [IG-EPN, descarga de datos](https://www.igepn.edu.ec/descarga-de-datos/) · [informes de sismos](https://www.igepn.edu.ec/portal/eventos/informes-ultimos-sismosC.html) · [USGS FDSN](https://earthquake.usgs.gov/fdsnws/event/1/) |
| Eventos peligrosos por territorio, 2010–2022 | SNGRE | [datosabiertos.gob.ec (seguridad y defensa)](https://datosabiertos.gob.ec/dataset/?groups=seguridad-y-defensa) |
| Población por cantón (2022) | INEC — Censo de Población y Vivienda 2022, tabulado 1.1 | Espejo público de los CSV oficiales (el INEC no expone descarga directa) |
| Límites cantonales | IGM/CONALI, vía geoBoundaries gbOpen (INEC/OCHA), CC BY 3.0 IGO | [geoBoundaries ECU-ADM2](https://www.geoboundaries.org) |
| Zonificación normativa | NEC-SE-DS (Norma Ecuatoriana de la Construcción, 2015) | Consulta del mapa oficial; aquí se emplea una aproximación provincial |

El catálogo del IG-EPN constituye la referencia nacional; su descarga masiva
requiere solicitud institucional. Por reproducibilidad programática, este
estudio emplea el servicio FDSN del USGS —igualmente oficial—, que incorpora
los eventos reportados por la red regional. La integración del catálogo del
IG-EPN se contempla como línea de trabajo futuro (véase la sección 8).

## 4. Estructura del repositorio

```
riesgo-sismico-ecuador/
├── data/
│   ├── raw/                  # Datos oficiales descargados (véase la sección 3)
│   └── processed/            # Catálogo depurado, sismos×cantón, índices
├── notebooks/                # CRISP-DM, ejecutables de extremo a extremo
│   ├── 01_business_understanding.ipynb
│   ├── 02_data_understanding.ipynb
│   ├── 03_data_preparation.ipynb
│   ├── 04_modeling_peligro_exposicion.ipynb
│   ├── 05_modeling_replicas.ipynb
│   └── 06_evaluation.ipynb
├── src/
│   ├── fetch_data.py         # Descarga de fuentes oficiales
│   ├── data_prep.py          # Depuración, unión espacial, agregación, censo
│   ├── models.py             # Omori-Utsu (MLE) e índices de peligro/riesgo
│   └── build_pages.py        # Generación del sitio estático de GitHub Pages
├── demo/
│   └── demo_alerta_temprana.py   # Demostración didáctica del principio P/S
├── docs/                     # Sitio estático publicado (GitHub Pages)
├── reports/figures/          # Figuras generadas
├── .github/                  # CI y configuración de Dependabot
├── README.md · SECURITY.md · CODE_OF_CONDUCT.md · requirements.txt · LICENSE
```

## 5. Metodología

### 5.1 Peligro y exposición (notebook 04)

1. Depuración del catálogo M≥4 (1983–2026) y unión espacial con los 224
   cantones mediante `geopandas.sjoin`. Los eventos localizados frente al
   litoral (interfaz de subducción) se asignan al cantón más cercano dentro de
   un radio de 150 km, a fin de no subestimar el peligro de los cantones
   costeros.
2. Por cantón: frecuencia de sismos **someros** (profundidad ≤ 70 km —los que
   gobiernan la sacudida superficial—) y energía liberada según la escala de
   Gutenberg-Richter (E = 10^(1.5·M+4.8) J); ambos términos normalizados
   componen el índice de peligro (0–100).
3. Exposición: densidad poblacional del Censo 2022, normalizada
   logarítmicamente.
4. Índice de riesgo relativo = peligro × exposición. Visualización en
   cartogramas y clasificación cantonal.

### 5.2 Pronóstico de réplicas (notebook 05)

- Secuencia de Pedernales 2016 (M≥4.5, radio de 150 km, 120 días).
- Ley de Omori-Utsu r(t) = K/(t+c)^p, ajustada por **máxima verosimilitud**
  bajo un proceso de Poisson no estacionario, con cotas físicas estándar
  (p ∈ [0.5, 2.0]; Utsu et al., 1995) e incertidumbre paramétrica por
  Hessiano numérico.
- Entrenamiento: días 1–60. **Validación fuera de muestra**: días 61–120.
- El modelo estima la tasa diaria esperada de la secuencia, en tanto proceso
  estocástico; no reproduce eventos individuales.

### 5.3 Evaluación (notebook 06)

- Métricas RMSE, MAE y correlación observación-predicción, con análisis de
  residuos y detección de sub-secuencias.
- Contraste cualitativo con la zonificación NEC (aproximación provincial,
  documentada como tal).
- Exploración —sin hipótesis causal— de la sismicidad M≥3 en torno a Mazar,
  Paute y Coca Codo Sinclair, antes y después de su entrada en operación.

## 6. Reproducibilidad

Requisitos: Python ≥ 3.10.

```bash
pip install -r requirements.txt

# 1) Descarga de datos oficiales (catálogo USGS-FDSN, cantones, censo)
python src/fetch_data.py

# 2) Pipeline de preparación (unión espacial, censo, agregación e índices)
python src/data_prep.py

# 3) Cuadernos (ejecutables en orden 01 → 06)
jupyter lab notebooks/

# 4) Regeneración del sitio estático
python src/build_pages.py

# 5) Demostración didáctica del principio de alerta temprana
python demo/demo_alerta_temprana.py
```

La integración continua (`.github/workflows/ci.yml`) verifica en cada push y
pull request la sintaxis del código y la reproducibilidad integral del
pipeline sobre los datos versionados.

## 7. Demostración didáctica: principio físico de la alerta temprana

`demo/demo_alerta_temprana.py` ilustra el principio físico de los sistemas de
alerta temprana: la onda P se propaga aproximadamente 1.8 veces más rápido que
la onda S, y esa diferencia de tiempos de arribo puede convertirse en aviso.
La demostración tiene carácter **estrictamente didáctico**: no constituye un
sistema de alerta, no está conectada a instrumentación alguna y no debe
emplearse para decisiones de seguridad. Al año 2026, el Ecuador no dispone de
un sistema público nacional de alerta temprana sísmica.

![Demostración P/S](reports/figures/demo_alerta_temprana.png)

## 8. Limitaciones

1. El índice de riesgo no constituye un análisis PSHA: no calcula
   probabilidades de excedencia de aceleración y no sustituye la zonificación
   normativa NEC; es una clasificación relativa para priorización territorial.
2. El modelo no incorpora atenuación por distancia ni tipología de fuente
   (motivo por el cual se restringe a sismicidad somera, ≤ 70 km).
3. La exposición se aproxima mediante densidad de población residente (Censo
   2022); no incluye edificaciones, tipologías estructurales ni ocupación
   horaria.
4. El estudio emplea un único catálogo (USGS-FDSN). La integración del
   catálogo oficial del IG-EPN (M≥1–2, mediante solicitud) constituiría una
   mejora sustantiva para las secuencias de réplicas y la exploración de
   embalses.
5. Omori-Utsu asume un único sismo principal; secuencias con sub-choques
   (p. ej., el M6.9 del 18 de mayo de 2016) requieren una formulación ETAS.
6. Los cantones homónimos (Bolívar y Olmedo, presentes en dos provincias cada
   uno) comparten clave de nombre en el cruce, lo que afecta a 4 de 224 filas.

## 9. Seguridad y gobernanza

- **Política de divulgación responsable:** [SECURITY.md](SECURITY.md) (reportes
  privados habilitados en la pestaña *Security* del repositorio).
- **Cadena de suministro:** Dependabot activo para `pip` y para las acciones de
  GitHub; integración continua que verifica la reproducibilidad del pipeline en
  cada push ([.github/workflows/ci.yml](.github/workflows/ci.yml)).
- **Escaneo de secretos** con **protección en el push** habilitados; historial
  auditado sin credenciales. El sitio de Pages es estático: sin cookies ni
  telemetría.
- **Convivencia:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 10. Correspondencia con el marco CRISP-DM

| Fase CRISP-DM | Implementación |
|---|---|
| 1. Comprensión del negocio | `01_business_understanding.ipynb` |
| 2. Comprensión de los datos | `02_data_understanding.ipynb` |
| 3. Preparación de los datos | `03_data_preparation.ipynb` + `src/data_prep.py` |
| 4a. Modelado: peligro × exposición | `04_modeling_peligro_exposicion.ipynb` + `src/models.py` |
| 4b. Modelado: réplicas | `05_modeling_replicas.ipynb` + `src/models.py` |
| 5/6. Evaluación y conclusiones | `06_evaluation.ipynb` |

## 11. Licencia y reconocimientos

- Código bajo [licencia MIT](LICENSE). Datos conforme a cada fuente oficial:
  catálogos IG-EPN/USGS de acceso público; Censo 2022 del INEC de uso libre
  citando la fuente; geoBoundaries bajo CC BY 3.0 IGO.
- Autor: **[@jordanvt18](https://github.com/jordanvt18)**. Estudio educativo de
  ciencia de datos abierta, elaborado como contribución a la gestión del
  riesgo sísmico del Ecuador.
- Reconocimientos: IG-EPN, INEC, IGM, SNGRE y USGS por el mantenimiento de
  datos públicos, y a la comunidad sismológica por la ciencia abierta que
  sustenta este trabajo.

---

*Nota final: la ocurrencia de los terremotos no admite, con el conocimiento
actual, predicción determinista; sus consecuencias, en cambio, sí admiten
cuantificación y reducción mediante métodos estadísticos y de ingeniería. A
esa segunda tarea se consagra este estudio.*
