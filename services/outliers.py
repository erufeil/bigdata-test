"""
outliers.py
-----------
Etiqueta cada inmueble como normal, sobrevaluado o subvaluado
segun la distancia de su residuo al modelo.

Criterio:
    |residuo| > sigma * std(residuos)  → es outlier
    residuo >  umbral                  → sobrevaluado
    residuo < -umbral                  → subvaluado
"""

import numpy as np
import pandas as pd


def etiquetar_outliers(df, residuos, sigma, std_residuos):
    """
    Agrega columnas al DataFrame:
        - es_outlier   : bool
        - tipo_outlier : 'normal' | 'sobrevaluado' | 'subvaluado'

    Parametros:
        df           : DataFrame original
        residuos     : array numpy con los residuos (precio_real - precio_predicho)
        sigma        : float, umbral en cantidad de desvios estandar
        std_residuos : float, desvio estandar de los residuos

    Devuelve el DataFrame con las columnas nuevas.
    """
    umbral = sigma * std_residuos

    df = df.copy()
    df["es_outlier"] = np.abs(residuos) > umbral
    df["tipo_outlier"] = "normal"
    df.loc[residuos >  umbral, "tipo_outlier"] = "sobrevaluado"
    df.loc[residuos < -umbral, "tipo_outlier"] = "subvaluado"

    return df, float(umbral)
