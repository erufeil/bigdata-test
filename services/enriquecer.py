"""
enriquecer.py
-------------
Lee una columna de texto libre de un DataFrame y genera nuevas columnas
binarias (0/1) a partir de la deteccion de palabras clave configurables.

El nombre de la columna de origen y el diccionario de variables se definen
en un archivo JSON externo, sin modificar este codigo.

Uso desde consola:
    python services/enriquecer.py --archivo datos.csv --config config_keywords.json
    python services/enriquecer.py --archivo datos.csv --config config_keywords.json --salida enriquecido.csv
"""

import argparse
import json
import os
import sys

import pandas as pd

# Permite importar desde la raiz del proyecto cuando se ejecuta directamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def enriquecer_desde_descripcion(df, ruta_config):
    """
    Lee la columna de descripcion y genera nuevas columnas binarias segun
    el archivo de configuracion JSON.

    Parametros:
        df          : DataFrame con los datos de entrada
        ruta_config : ruta al archivo JSON de configuracion

    Devuelve:
        df_enriquecido    : DataFrame con las columnas nuevas agregadas
        columnas_generadas: lista de nombres de columnas creadas
    """
    with open(ruta_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    col_desc = config["columna_descripcion"]

    if col_desc not in df.columns:
        print(f"  [enriquecer] Advertencia: columna '{col_desc}' no encontrada. Se omite el enriquecimiento.")
        return df, []

    df = df.copy()
    columnas_generadas = []

    # Texto en minusculas para todas las comparaciones
    texto = df[col_desc].fillna("").str.lower()

    # --- Columnas binarias por palabras clave ---
    for variable in config.get("variables", []):
        nombre       = variable["nombre"]
        palabras     = variable["palabras_clave"]

        # Construir patron regex con todas las palabras clave unidas por OR
        patron = "|".join(palabras)
        df[nombre] = texto.str.contains(patron, case=False, regex=True).astype(int)
        columnas_generadas.append(nombre)

    # --- Columnas extraidas por regex desde otra columna ---
    for extraccion in config.get("columnas_extraidas", []):
        nombre         = extraccion["nombre"]
        col_origen     = extraccion["columna_origen"]
        patron         = extraccion["patron"]

        if col_origen not in df.columns:
            print(f"  [enriquecer] Advertencia: columna origen '{col_origen}' no encontrada para extraer '{nombre}'.")
            continue

        df[nombre] = df[col_origen].str.extract(patron, expand=False)
        columnas_generadas.append(nombre)

    # --- Columnas derivadas (ej: sumas) ---
    for derivada in config.get("columnas_derivadas", []):
        nombre    = derivada["nombre"]
        operacion = derivada.get("operacion", "suma")
        fuentes   = derivada["fuentes"]

        if operacion == "suma":
            df[nombre] = df[fuentes].sum(axis=1)
            columnas_generadas.append(nombre)

    # --- Eliminar columnas completamente vacias ---
    columnas_antes = set(df.columns)
    df = df.dropna(axis=1, how="all")
    columnas_eliminadas = columnas_antes - set(df.columns)
    if columnas_eliminadas:
        print(f"  [enriquecer] Columnas vacias eliminadas: {sorted(columnas_eliminadas)}")

    return df, columnas_generadas


# ---------------------------------------------------------------------------
# Ejecucion directa desde consola
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera columnas binarias a partir de palabras clave en una columna de texto."
    )
    parser.add_argument("--archivo",    required=True,  help="Ruta al CSV de entrada")
    parser.add_argument("--config",     required=True,  help="Ruta al JSON de configuracion de palabras clave")
    parser.add_argument("--separador",  default="auto", help="coma | punto_y_coma | auto")
    parser.add_argument("--salida",     default=None,   help="Ruta del CSV de salida (opcional)")
    args = parser.parse_args()

    sep_map = {"coma": ",", "punto_y_coma": ";", "auto": None}
    sep = sep_map.get(args.separador, None)
    if sep is None:
        df = pd.read_csv(args.archivo, sep=None, engine="python", encoding="utf-8-sig")
    else:
        df = pd.read_csv(args.archivo, sep=sep, encoding="utf-8-sig")

    print(f"Archivo cargado : {args.archivo}  ({len(df)} filas, {len(df.columns)} columnas)")

    df_resultado, columnas = enriquecer_desde_descripcion(df, args.config)

    print(f"Columnas nuevas : {columnas}")
    print(f"Total columnas  : {len(df_resultado.columns)}")

    if args.salida:
        df_resultado.to_csv(args.salida, index=False)
        print(f"CSV guardado    : {args.salida}")
    else:
        print("\nPrimeras 3 filas con columnas generadas:")
        print(df_resultado[columnas].head(3).to_string())
