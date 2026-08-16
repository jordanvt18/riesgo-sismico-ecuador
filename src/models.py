# -*- coding: utf-8 -*-
"""
Modelos estadísticos (ninguno 'predice sismos'):

1) Ley de Omori-Utsu: tasa de réplicas r(t) = K / (t + c)^p
   Pronostica la TASA esperada de réplicas, no eventos individuales.
   Ajuste por máxima verosimilitud (proceso de Poisson no estacionario)
   sobre los tiempos de ocurrencia de las réplicas.
2) Índice de peligro relativo por cantón: frecuencia histórica + energía
   (escala de Gutenberg-Richter), combinado con exposición poblacional.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize


# ---------------------------------------------------------------- Omori-Utsu
def tasa_omori(t, K, c, p):
    """Tasa diaria de réplicas según la ley de Omori-Utsu: K/(t+c)^p."""
    t = np.asarray(t, dtype=float)
    return K / np.power(t + c, p)


def _integral_omori(K, c, p, T):
    """∫₀ᵀ K/(t+c)^p dt (número esperado de réplicas hasta el día T)."""
    if abs(p - 1.0) < 1e-8:
        return K * np.log((T + c) / c)
    return K / (1 - p) * ((T + c) ** (1 - p) - c ** (1 - p))


def _neg_verosimilitud(x, tiempos, T):
    """Log-verosimilitud negativa de un proceso de Poisson no estacionario.

    Incluye cotas físicas estándar de la sismología de réplicas:
    p ∈ [0.5, 2.0] (típicamente 0.8–1.5; Utsu et al. 1995) y c ≤ 50 días.
    Sin ellas, ventanas cortas admiten óptimos degenerados con p >> 2.
    """
    K, c, p = x
    if K <= 0 or c <= 1e-6 or not (0.5 <= p <= 2.0) or c > 50:
        return 1e12
    tasas = K / (tiempos + c) ** p
    if np.any(tasas <= 0):
        return 1e12
    return _integral_omori(K, c, p, T) - np.sum(np.log(tasas))


def _hessiano_num(f, x, h=1e-4):
    """Hessiano numérico (diferencias finitas centrales) de f en x."""
    n = len(x)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            ei, ej = np.zeros(n), np.zeros(n)
            ei[i], ej[j] = h, h
            if i == j:
                H[i, i] = (f(x + ei) - 2 * f(x) + f(x - ei)) / h**2
            else:
                H[i, j] = H[j, i] = (f(x + ei + ej) - f(x + ei - ej)
                                     - f(x - ei + ej) + f(x - ei - ej)) / (4 * h**2)
    return H


def ajustar_omori_mle(tiempos, T):
    """Ajusta Omori-Utsu por máxima verosimilitud sobre tiempos de réplicas.

    tiempos: días (fraccionarios) de cada réplica desde el sismo principal.
    T: duración de la ventana de entrenamiento (días).
    Devuelve (params=[K,c,p], cov_aprox). La covarianza aproximada sale del
    inverso del Hessiano de la log-verosimilitud negativa.
    """
    tiempos = np.asarray(tiempos, dtype=float)
    mejor, mejor_nll = None, np.inf
    for semilla in [(50, 0.5, 1.0), (500, 0.1, 0.8), (10, 1.0, 1.2), (100, 0.01, 1.5)]:
        try:
            res = minimize(_neg_verosimilitud, semilla, args=(tiempos, T),
                           method="Nelder-Mead",
                           options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 5000})
        except Exception:
            continue
        if res.fun < mejor_nll:
            mejor, mejor_nll = res.x, res.fun
    if mejor is None:
        raise RuntimeError("El ajuste Omori-Utsu no convergió")
    try:
        cov = np.linalg.inv(_hessiano_num(
            lambda x: _neg_verosimilitud(x, tiempos, T), mejor))
        cov = np.abs(np.diag(cov)) * np.eye(3)  # aproximación diagonal
    except np.linalg.LinAlgError:
        cov = np.full((3, 3), np.nan)
    return mejor, cov


# ------------------------------------------------- Peligro x exposición
def indice_peligro(tabla: pd.DataFrame,
                   col_n="n_sismos_someros", col_e="energia_somera_j") -> pd.Series:
    """Índice de peligro relativo por cantón (0–100).

    Usa únicamente sismicidad SOMERA (profundidad ≤ 70 km), que es la que
    gobierna la sacudida en superficie: combina la frecuencia histórica de
    sismos M≥4 y la energía total liberada (escala Gutenberg-Richter
    E = 10^(1.5M+4.8) joules), ambas normalizadas y promediadas con igual peso.
    La sismicidad profunda del slab (>70 km, bajo la Amazonía) atenúa mucho
    antes de llegar a superficie y no pondera este índice.
    """
    freq = tabla[col_n].astype(float)
    ener = tabla[col_e].astype(float)
    # Log para energía (varía órdenes de magnitud) y raíz para conteos
    if freq.max() > 0:
        f_norm = 100 * np.sqrt(freq) / np.sqrt(freq).max()
    else:
        f_norm = freq * 0
    if ener.max() > 0:
        e_norm = 100 * np.log10(ener + 1) / np.log10(ener.max() + 1)
    else:
        e_norm = ener * 0
    return (0.5 * f_norm + 0.5 * e_norm).round(2)


def indice_riesgo(peligro: pd.Series, densidad: pd.Series) -> pd.Series:
    """Índice de riesgo relativo = peligro relativo x exposición (densidad).

    Ambos factores se normalizan 0-1 antes de multiplicarse.
    """
    p = (peligro - peligro.min()) / (peligro.max() - peligro.min() + 1e-12)
    d = np.log10(densidad + 1)                    # log: la densidad es asimétrica
    d = (d - d.min()) / (d.max() - d.min() + 1e-12)
    return (100 * p * d).round(2)
