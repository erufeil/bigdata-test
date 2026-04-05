"""
app.py
------
Servidor Flask principal.
Expone la API REST y sirve el frontend estático.

Endpoints:
    GET  /                          → index.html
    POST /upload                    → recibe CSV, guarda en data/, devuelve preview
    POST /analyze                   → ejecuta modelo, guarda resultados, devuelve datos
    GET  /download/csv/<filename>   → descarga CSV resultado
    GET  /download/report/<filename>→ descarga TXT reporte
    GET  /results                   → historial de analisis previos
"""

import os
import json
from datetime import datetime

import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, render_template

from services.regression import ajustar_modelo
from services.outliers import etiquetar_outliers

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(BASE_DIR, "data")
RESULTS_DIR  = os.path.join(BASE_DIR, "results")
INDEX_FILE   = os.path.join(RESULTS_DIR, "index.json")

os.makedirs(DATA_DIR,    exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _cargar_csv(ruta):
    """Carga un CSV detectando automaticamente el separador y eliminando BOM."""
    return pd.read_csv(ruta, sep=None, engine="python", encoding="utf-8-sig")


def _leer_index():
    """Lee el historial de analisis guardados."""
    if not os.path.exists(INDEX_FILE):
        return []
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_index(entrada):
    """Agrega una entrada nueva al historial."""
    historial = _leer_index()
    historial.insert(0, entrada)          # mas reciente primero
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def _construir_reporte(resultado, umbral, sigma, nombre_archivo, df_final):
    """Devuelve el string del reporte TXT."""
    total    = len(df_final)
    n_normal = (df_final["tipo_outlier"] == "normal").sum()
    n_sobre  = (df_final["tipo_outlier"] == "sobrevaluado").sum()
    n_sub    = (df_final["tipo_outlier"] == "subvaluado").sum()

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

    sobre = df_final[df_final["tipo_outlier"] == "sobrevaluado"]
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

    sub = df_final[df_final["tipo_outlier"] == "subvaluado"]
    if sub.empty:
        lineas.append("  (ninguno)")
    else:
        for i, fila in sub.iterrows():
            lineas.append(fila_str(i, fila))

    lineas.append("=" * 60)
    return "\n".join(lineas) + "\n"


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Recibe un archivo CSV mediante multipart/form-data (campo 'file').
    Guarda el archivo en data/ y devuelve un preview de las primeras 5 filas.
    """
    if "file" not in request.files:
        return jsonify({"error": "No se envio ningun archivo (campo 'file')"}), 400

    archivo = request.files["file"]
    if archivo.filename == "":
        return jsonify({"error": "El nombre del archivo esta vacio"}), 400

    nombre = archivo.filename
    ruta   = os.path.join(DATA_DIR, nombre)
    archivo.save(ruta)

    try:
        df = _cargar_csv(ruta)
    except Exception as e:
        return jsonify({"error": f"No se pudo leer el CSV: {str(e)}"}), 422

    preview = df.head(5).replace({float("nan"): None}).to_dict(orient="records")
    columnas = list(df.columns)

    return jsonify({
        "filename" : nombre,
        "filas"    : len(df),
        "columnas" : columnas,
        "preview"  : preview,
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Body JSON esperado: { "filename": "datos.csv", "sigma": 2.0 }
    Ejecuta regresion + deteccion de outliers.
    Guarda CSV resultado y TXT reporte en results/.
    Devuelve JSON con metricas, ecuacion, filas con etiqueta y nombres de archivos.
    """
    body = request.get_json(force=True)
    if not body or "filename" not in body:
        return jsonify({"error": "Falta el campo 'filename' en el body"}), 400

    nombre = body["filename"]
    sigma  = float(body.get("sigma", 2.0))
    ruta   = os.path.join(DATA_DIR, nombre)

    if not os.path.exists(ruta):
        return jsonify({"error": f"Archivo '{nombre}' no encontrado en data/"}), 404

    try:
        df = _cargar_csv(ruta)
    except Exception as e:
        return jsonify({"error": f"No se pudo leer el CSV: {str(e)}"}), 422

    # --- Modelo ---
    resultado = ajustar_modelo(df)

    # --- Outliers ---
    df["Precio_predicho"] = resultado["precio_predicho"].round(2)
    df["residuo"]         = resultado["residuos"].round(2)
    df, umbral = etiquetar_outliers(
        df,
        resultado["residuos"],
        sigma,
        resultado["std_residuos"],
    )

    # --- Guardar archivos resultado ---
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_nombre = os.path.splitext(nombre)[0]
    nombre_csv  = f"resultado_{base_nombre}_{timestamp}.csv"
    nombre_txt  = f"reporte_{base_nombre}_{timestamp}.txt"

    df.to_csv(os.path.join(RESULTS_DIR, nombre_csv), index=False)

    reporte_str = _construir_reporte(resultado, umbral, sigma, nombre, df)
    with open(os.path.join(RESULTS_DIR, nombre_txt), "w", encoding="utf-8") as f:
        f.write(reporte_str)

    # --- Historial ---
    _guardar_index({
        "timestamp"  : timestamp,
        "origen"     : nombre,
        "sigma"      : sigma,
        "archivo_csv": nombre_csv,
        "archivo_txt": nombre_txt,
        "r2"         : round(resultado["r2"], 4),
        "rmse"       : round(resultado["rmse"], 2),
    })

    # --- Preparar filas para la respuesta (NaN → None para JSON) ---
    filas = (
        df.replace({float("nan"): None, True: True, False: False})
        .to_dict(orient="records")
    )

    # Convertir numpy types a python natives
    filas_serializables = json.loads(
        json.dumps(filas, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    )

    return jsonify({
        "ecuacion"        : resultado["ecuacion_str"],
        "coeficientes"    : {k: round(v, 4) for k, v in resultado["coeficientes"].items()},
        "intercepto"      : round(resultado["intercepto"], 2),
        "r2"              : round(resultado["r2"], 4),
        "rmse"            : round(resultado["rmse"], 2),
        "std_residuos"    : round(resultado["std_residuos"], 2),
        "umbral"          : round(umbral, 2),
        "sigma"           : sigma,
        "total"           : len(df),
        "normales"        : int((df["tipo_outlier"] == "normal").sum()),
        "sobrevaluados"   : int((df["tipo_outlier"] == "sobrevaluado").sum()),
        "subvaluados"     : int((df["tipo_outlier"] == "subvaluado").sum()),
        "filas"           : filas_serializables,
        "archivo_csv"     : nombre_csv,
        "archivo_txt"     : nombre_txt,
    })


@app.route("/download/csv/<nombre_archivo>")
def download_csv(nombre_archivo):
    return send_from_directory(RESULTS_DIR, nombre_archivo, as_attachment=True)


@app.route("/download/report/<nombre_archivo>")
def download_report(nombre_archivo):
    return send_from_directory(RESULTS_DIR, nombre_archivo, as_attachment=True)


@app.route("/results")
def list_results():
    """Devuelve el historial de analisis previos."""
    return jsonify(_leer_index())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
