# -*- coding: utf-8 -*-
"""
DEMOSTRACIÓN DIDÁCTICA — Principio físico de la alerta temprana sísmica (ondas P y S)
======================================================================================

El presente script ilustra el principio físico en que se fundan los sistemas
de alerta temprana (como el SASMEX mexicano o el de Japón). La demostración
tiene carácter estrictamente didáctico: no constituye un sistema de alerta,
no está conectada a instrumentación alguna y no debe emplearse para
decisiones de seguridad. Al año 2026, el Ecuador no dispone de un sistema
público nacional de alerta temprana sísmica en operación.

Principio físico:
- Las ondas P (primarias) viajan a ~7 km/s: llegan primero pero casi no dañan.
- Las ondas S (secundarias) viajan a ~3.9 km/s: llegan después y son las que
  sacuden y dañan las estructuras.
- Un sismo fuerte frente a la costa tarda decenas de segundos en que sus ondas
  S alcancen las ciudades. Detectar la onda P cerca del epicentro permite
  "ganar" esos segundos de aviso (apagar industrias, detener trenes, que la
  gente se proteja).

Salida: reports/figures/demo_alerta_temprana.png
"""
import os
import numpy as np
import matplotlib.pyplot as plt

# Velocidades típicas de la corteza ecuatoriana (aproximadas, fines didácticos)
V_P = 7.0   # km/s — onda primaria (compresiva)
V_S = 3.9   # km/s — onda secundaria (cizalla, la dañina)

# Distancias aproximadas de un hipotético M7.8 frente a Pedernales (2016)
# a ciudades del perfil costero-interandino
CIUDADES = {
    "Muisne": 45,
    "Manta": 105,
    "Portoviejo": 150,
    "Santo Domingo": 215,
    "Quito": 265,
    "Guayaquil": 300,
    "Cuenca": 430,
}

distancias = np.linspace(0, 600, 400)
t_p = distancias / V_P
t_s = distancias / V_S
adelanto = t_s - t_p

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))

# Panel 1: tiempo de arribo de cada onda vs distancia
ax1.plot(distancias, t_s, c="#C8102E", lw=2.2, label=f"Onda S (dañina) · {V_S} km/s")
ax1.plot(distancias, t_p, c="#1F77B4", lw=2.2, label=f"Onda P (aviso) · {V_P} km/s")
ax1.fill_between(distancias, t_p, t_s, color="#C8102E", alpha=0.12, label="Ventana de alerta posible")
for ciudad, d in CIUDADES.items():
    ax1.vlines(d, 0, d / V_S, ls=":", color="grey", lw=0.8)
    ax1.annotate(ciudad, (d, d / V_S), xytext=(3, -10), textcoords="offset points", fontsize=8, rotation=90)
ax1.set_xlabel("Distancia al epicentro (km)")
ax1.set_ylabel("Tiempo de arribo (s)")
ax1.set_title("Arrivo de ondas P y S desde un hipotético M7.8 frente a Pedernales")
ax1.legend(loc="lower right", fontsize=8)
ax1.set_xlim(0, 600); ax1.set_ylim(0, 155)

# Panel 2: segundos de adelanto que daría la alerta
ax2.plot(distancias, adelanto, c="#2E7D32", lw=2.2)
ax2.set_xlabel("Distancia al epicentro (km)")
ax2.set_ylabel("Adelanto de la alerta (s)")
ax2.set_title("Tiempo de adelanto = t(S) − t(P)\n(zona de mayor beneficio: 60–300 km del epicentro)")
for ciudad, d in CIUDADES.items():
    ax2.plot(d, d / V_S - d / V_P, "o", ms=4, color="#C8102E")
    ax2.annotate(f"{ciudad}\n{d/V_S - d/V_P:.0f} s", (d, d / V_S - d / V_P),
                 xytext=(4, 4), textcoords="offset points", fontsize=8)
ax2.set_xlim(0, 600)

fig.suptitle("Demostración didáctica del principio de alerta temprana por diferencia "
             "de velocidad entre ondas P y S (sin valor operativo)", fontsize=11, y=1.02)
plt.tight_layout()

salida = os.path.join("..", "reports", "figures", "demo_alerta_temprana.png")
if not os.path.isdir(os.path.join("..", "reports", "figures")):
    salida = os.path.join("reports", "figures", "demo_alerta_temprana.png")
os.makedirs(os.path.dirname(salida), exist_ok=True)
plt.savefig(salida, bbox_inches="tight", dpi=130)
print(f"[ok] Figura guardada: {salida}")
print("Nota: demostración didáctica del principio físico; no constituye un sistema de alerta real.")
