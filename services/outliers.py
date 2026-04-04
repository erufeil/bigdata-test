"""
outliers.py
-----------
Etiqueta cada inmueble como normal, sobrevaluado o subvaluado
segun la distancia de su residuo al promedio del modelo.

Criterio:
    |residuo| > sigma * std(residuos)  → es outlier
    residuo >  umbral                  → sobrevaluado
    residuo < -umbral                  → subvaluado

Uso desde consola:
    python services/outliers.py --archivo datos.csv --sigma 2.0
"""

import argparse
import sys
import os
import pandas as pd
import numpy as np

# Para poder importar regression cuando se ejecuta directamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.regression import ajustar_modelo


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


# ---------------------------------------------------------------------------
# Ejecucion directa desde consola
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detecta outliers inmobiliarios en un CSV."
    )
    parser.add_argument("--archivo",    required=True,  help="Ruta al archivo CSV de entrada")
    parser.add_argument("--sigma",      type=float, default=2.0, help="Sensibilidad outlier (default 2.0)")
    parser.add_argument("--separador",  default="auto", help="coma | punto_y_coma | auto")
    parser.add_argument("--salida_csv", default=None,   help="Ruta del CSV resultado (opcional)")
    parser.add_argument("--salida_txt", default=None,   help="Ruta del TXT reporte (opcional)")
    args = parser.parse_args()

    # --- Cargar CSV ---
    sep_map = {"coma": ",", "punto_y_coma": ";", "auto": None}
    sep = sep_map.get(args.separador, None)
    if sep is None:
        df = pd.read_csv(args.archivo, sep=None, engine="python")
    else:
        df = pd.read_csv(args.archivo, sep=sep)

    # --- Modelo ---
    resultado = ajustar_modelo(df)
    df["precio_predicho"] = resultado["precio_predicho"].round(2)
    df["residuo"]         = resultado["residuos"].round(2)

    # --- Outliers ---
    df, umbral = etiquetar_outliers(
        df,
        resultado["residuos"],
        args.sigma,
        resultado["std_residuos"],
    )

    # --- Mostrar resumen en consola ---
    total       = len(df)
    n_normal    = (df["tipo_outlier"] == "normal").sum()
    n_sobre     = (df["tipo_outlier"] == "sobrevaluado").sum()
    n_sub       = (df["tipo_outlier"] == "subvaluado").sum()

    print("\n=== RESUMEN DE OUTLIERS ===")
    print(f"Sigma utilizado : {args.sigma}")
    print(f"Umbral          : ±{umbral:.2f} USD")
    print(f"Total           : {total}")
    print(f"  Normales      : {n_normal}")
    print(f"  Sobrevaluados : {n_sobre}")
    print(f"  Subvaluados   : {n_sub}")

    # --- Guardar CSV resultado ---
    if args.salida_csv:
        df.to_csv(args.salida_csv, index=False)
        print(f"\nCSV guardado en: {args.salida_csv}")

    # --- Guardar TXT reporte ---
    if args.salida_txt:
        from datetime import datetime
        nombre_archivo = os.path.basename(args.archivo)
        with open(args.salida_txt, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  REPORTE DE ANALISIS INMOBILIARIO\n")
            f.write("=" * 60 + "\n")
            f.write(f"Fecha y hora   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Archivo origen : {nombre_archivo}\n")
            f.write(f"Sigma utilizado: {args.sigma}\n\n")
            f.write("ECUACION DEL MODELO\n")
            f.write("-" * 60 + "\n")
            f.write(f"{resultado['ecuacion_str']}\n\n")
            f.write("COEFICIENTES\n")
            f.write("-" * 60 + "\n")
            for col, coef in resultado["coeficientes"].items():
                f.write(f"  {col:<20}: {coef:+.4f} USD\n")
            f.write("\nMETRICAS DEL MODELO\n")
            f.write("-" * 60 + "\n")
            f.write(f"  R²             : {resultado['r2']:.4f}\n")
            f.write(f"  RMSE           : {resultado['rmse']:.2f} USD\n")
            f.write(f"  Std. residuos  : {resultado['std_residuos']:.2f} USD\n")
            f.write(f"  Umbral outlier : ±{umbral:.2f} USD\n\n")
            f.write("RESUMEN DE INMUEBLES\n")
            f.write("-" * 60 + "\n")
            f.write(f"  Total analizados : {total}\n")
            f.write(f"  Normales         : {n_normal}\n")
            f.write(f"  Outliers total   : {n_sobre + n_sub}\n")
            f.write(f"    Sobrevaluados  : {n_sobre}\n")
            f.write(f"    Subvaluados    : {n_sub}\n")
            f.write("=" * 60 + "\n")
        print(f"Reporte guardado en: {args.salida_txt}")
