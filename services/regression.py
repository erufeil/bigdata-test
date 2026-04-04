"""
regression.py
-------------
Ajusta una regresion lineal multiple sobre el DataFrame recibido.

Uso desde consola:
    python services/regression.py --archivo datos.csv --sigma 2.0

Variables esperadas en el CSV:
    precio, superficie_m2, cocina_separada, monoambiente,
    a_estrenar, patio, planta_baja
"""

import argparse
import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error


COLUMNAS_X = [
    "M2",
    "Balcon2",
    "Amenities",
    "cocinaSep",
    "Monoambiente",
    "A Estrenar",
    "Patio PB",
    "PB",
]

COLUMNA_Y = "Precio"


def ajustar_modelo(df):
    """
    Recibe un DataFrame con las columnas del proyecto.
    Devuelve un diccionario con:
        - modelo      : objeto LinearRegression entrenado
        - coeficientes: dict {variable: coef}
        - intercepto  : float
        - r2          : float
        - rmse        : float
        - precio_predicho : array numpy
        - residuos        : array numpy
        - std_residuos    : float
        - ecuacion_str    : string legible de la ecuacion
    """
    X = df[COLUMNAS_X].values
    y = df[COLUMNA_Y].values

    modelo = LinearRegression()
    modelo.fit(X, y)

    y_pred = modelo.predict(X)
    residuos = y - y_pred

    r2   = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    std_residuos = float(np.std(residuos))

    coeficientes = dict(zip(COLUMNAS_X, modelo.coef_))

    # Construir string legible de la ecuacion
    partes = [f"{modelo.intercept_:+.2f}"]
    for col, coef in coeficientes.items():
        partes.append(f"{coef:+.2f} * {col}")
    ecuacion_str = "precio = " + " ".join(partes)

    return {
        "modelo"          : modelo,
        "coeficientes"    : coeficientes,
        "intercepto"      : float(modelo.intercept_),
        "r2"              : float(r2),
        "rmse"            : float(rmse),
        "precio_predicho" : y_pred,
        "residuos"        : residuos,
        "std_residuos"    : std_residuos,
        "ecuacion_str"    : ecuacion_str,
    }


# ---------------------------------------------------------------------------
# Ejecucion directa desde consola
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ajusta regresion lineal sobre un CSV inmobiliario."
    )
    parser.add_argument("--archivo", required=True, help="Ruta al archivo CSV")
    parser.add_argument(
        "--separador", default="auto", help="Separador del CSV: coma, punto_y_coma o auto"
    )
    args = parser.parse_args()

    sep_map = {"coma": ",", "punto_y_coma": ";", "auto": None}
    sep = sep_map.get(args.separador, None)

    if sep is None:
        df = pd.read_csv(args.archivo, sep=None, engine="python")
    else:
        df = pd.read_csv(args.archivo, sep=sep)

    resultado = ajustar_modelo(df)

    print("\n=== RESULTADO DE REGRESION ===")
    print(f"Ecuacion : {resultado['ecuacion_str']}")
    print(f"R²       : {resultado['r2']:.4f}")
    print(f"RMSE     : {resultado['rmse']:.2f} USD")
    print(f"Std res. : {resultado['std_residuos']:.2f} USD")
    print("\nCoeficientes:")
    for col, coef in resultado["coeficientes"].items():
        print(f"  {col:<20}: {coef:+.4f} USD")
