"""
procesar.py
-----------
Pipeline completo: carga CSV → regresion lineal → deteccion de outliers
→ guarda CSV resultado + TXT reporte.

Uso:
    python procesar.py --archivo datos.csv
    python procesar.py --archivo datos.csv --sigma 1.5
    python procesar.py --archivo datos.csv --sigma 2.0 --separador punto_y_coma
    python procesar.py --archivo datos.csv --salida_dir mi_carpeta/

Archivos generados en --salida_dir (default: results/):
    resultado_<nombre>_<timestamp>.csv
    reporte_<nombre>_<timestamp>.txt
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

# Permite ejecutar desde cualquier ubicacion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.regression import ajustar_modelo
from services.outliers import etiquetar_outliers


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def cargar_csv(ruta, separador):
    sep_map = {"coma": ",", "punto_y_coma": ";", "auto": None}
    sep = sep_map.get(separador, None)
    # encoding='utf-8-sig' elimina el BOM que generan Excel y otros editores
    if sep is None:
        return pd.read_csv(ruta, sep=None, engine="python", encoding="utf-8-sig")
    return pd.read_csv(ruta, sep=sep, encoding="utf-8-sig")


def construir_reporte(resultado, umbral, sigma, nombre_archivo, df):
    total    = len(df)
    n_normal = (df["tipo_outlier"] == "normal").sum()
    n_sobre  = (df["tipo_outlier"] == "sobrevaluado").sum()
    n_sub    = (df["tipo_outlier"] == "subvaluado").sum()

    lineas = [
        "=" * 60,
        "  REPORTE DE ANALISIS INMOBILIARIO",
        "=" * 60,
        f"Fecha y hora   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Archivo origen : {nombre_archivo}",
        f"Sigma utilizado: {sigma}",
        "",
        "ECUACION DEL MODELO",
        "-" * 60,
        resultado["ecuacion_str"],
        "",
        "COEFICIENTES",
        "-" * 60,
    ]
    for col, coef in resultado["coeficientes"].items():
        lineas.append(f"  {col:<20}: {coef:+.4f} USD")

    lineas += [
        "",
        "METRICAS DEL MODELO",
        "-" * 60,
        f"  R²             : {resultado['r2']:.4f}",
        f"  RMSE           : {resultado['rmse']:.2f} USD",
        f"  Std. residuos  : {resultado['std_residuos']:.2f} USD",
        f"  Umbral outlier : ±{umbral:.2f} USD",
        "",
        "RESUMEN DE INMUEBLES",
        "-" * 60,
        f"  Total analizados : {total}",
        f"  Normales         : {n_normal}",
        f"  Outliers total   : {n_sobre + n_sub}",
        f"    Sobrevaluados  : {n_sobre}",
        f"    Subvaluados    : {n_sub}",
        "",
        "SOBREVALUADOS",
        "-" * 60,
    ]

    def fila_str(i, fila):
        return (
            f"  Fila {i+1:>3} | "
            f"Precio: {fila['Precio']:>9.0f}  "
            f"Predicho: {fila['Precio_predicho']:>9.0f}  "
            f"Residuo: {fila['residuo']:>+9.0f} USD"
        )

    sobre = df[df["tipo_outlier"] == "sobrevaluado"]
    if sobre.empty:
        lineas.append("  (ninguno)")
    else:
        for i, fila in sobre.iterrows():
            lineas.append(fila_str(i, fila))

    lineas += [
        "",
        "SUBVALUADOS",
        "-" * 60,
    ]

    sub = df[df["tipo_outlier"] == "subvaluado"]
    if sub.empty:
        lineas.append("  (ninguno)")
    else:
        for i, fila in sub.iterrows():
            lineas.append(fila_str(i, fila))

    lineas.append("=" * 60)
    return "\n".join(lineas) + "\n"


def procesar(archivo, sigma, separador, salida_dir):
    # --- Cargar ---
    df = cargar_csv(archivo, separador)
    nombre_archivo = os.path.basename(archivo)
    print(f"Archivo cargado : {nombre_archivo}  ({len(df)} filas)")

    # --- Modelo ---
    resultado = ajustar_modelo(df)
    print(f"Modelo ajustado : R²={resultado['r2']:.4f}  RMSE={resultado['rmse']:.2f} USD")

    # --- Agregar columnas calculadas ---
    df["Precio_predicho"] = resultado["precio_predicho"].round(2)
    df["residuo"]         = resultado["residuos"].round(2)

    # --- Outliers ---
    df, umbral = etiquetar_outliers(
        df,
        resultado["residuos"],
        sigma,
        resultado["std_residuos"],
    )
    n_sobre = (df["tipo_outlier"] == "sobrevaluado").sum()
    n_sub   = (df["tipo_outlier"] == "subvaluado").sum()
    print(f"Umbral outlier  : ±{umbral:.2f} USD  (sigma={sigma})")
    print(f"Sobrevaluados   : {n_sobre}   Subvaluados: {n_sub}")

    # --- Nombres de archivos de salida ---
    os.makedirs(salida_dir, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_nombre = os.path.splitext(nombre_archivo)[0]
    ruta_csv    = os.path.join(salida_dir, f"resultado_{base_nombre}_{timestamp}.csv")
    ruta_txt    = os.path.join(salida_dir, f"reporte_{base_nombre}_{timestamp}.txt")

    # --- Guardar CSV ---
    df.to_csv(ruta_csv, index=False)
    print(f"\nCSV guardado    : {ruta_csv}")

    # --- Guardar TXT ---
    reporte = construir_reporte(resultado, umbral, sigma, nombre_archivo, df)
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(reporte)
    print(f"Reporte guardado: {ruta_txt}")

    return ruta_csv, ruta_txt


# ---------------------------------------------------------------------------
# Ejecucion directa
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analisis inmobiliario: regresion + outliers → CSV + TXT."
    )
    parser.add_argument("--archivo",    required=True,         help="Ruta al CSV de entrada")
    parser.add_argument("--sigma",      type=float, default=2.0, help="Sensibilidad outlier (default 2.0)")
    parser.add_argument("--separador",  default="auto",        help="coma | punto_y_coma | auto")
    parser.add_argument("--salida_dir", default="results",     help="Carpeta de salida (default: results/)")
    args = parser.parse_args()

    procesar(args.archivo, args.sigma, args.separador, args.salida_dir)
