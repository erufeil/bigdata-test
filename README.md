# Análisis Inmobiliario — Córdoba

Detecta inmuebles sobrevaluados y subvaluados mediante regresión lineal múltiple.

---

## Instalación

```bash
# Crear el entorno virtual
python -m venv venv

# Activarlo
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## Iniciar el servidor

```bash
python app.py
# Servidor en http://localhost:5000
```

---

## API REST

### Subir un CSV
```
POST /upload
Content-Type: multipart/form-data
Campo: file = <archivo.csv>
```
Respuesta: preview de las primeras 5 filas + columnas detectadas.

### Analizar
```
POST /analyze
Content-Type: application/json
Body: { "filename": "datos.csv", "sigma": 2.0 }
```
Respuesta: ecuación del modelo, métricas, tabla completa con etiquetas de outlier y nombres de los archivos generados.

### Descargar CSV resultado
```
GET /download/csv/<nombre_archivo>
```

### Descargar reporte TXT
```
GET /download/report/<nombre_archivo>
```

### Historial de análisis
```
GET /results
```

---

## Usar los módulos directamente desde consola

### Solo regresión (muestra ecuación y métricas)
```bash
python services/regression.py --archivo datos.csv
python services/regression.py --archivo datos.csv --separador punto_y_coma
```

### Regresión + detección de outliers + archivos de salida
```bash
python services/outliers.py \
    --archivo datos.csv \
    --sigma 2.0 \
    --salida_csv resultado.csv \
    --salida_txt reporte.txt
```

Opciones disponibles:

| Parámetro     | Default | Descripción                              |
|---------------|---------|------------------------------------------|
| `--archivo`   | —       | Ruta al CSV de entrada (obligatorio)     |
| `--sigma`     | 2.0     | Sensibilidad outlier (mayor = menos outliers) |
| `--separador` | auto    | `coma`, `punto_y_coma` o `auto`          |
| `--salida_csv`| —       | Ruta del CSV resultado (opcional)        |
| `--salida_txt`| —       | Ruta del TXT reporte (opcional)          |

---

## Formato del CSV de entrada

```
precio,superficie_m2,cocina_separada,monoambiente,a_estrenar,patio,planta_baja
85000,52,1,0,0,0,0
72000,48,0,1,0,0,1
```

| Columna          | Tipo  | Descripción                  |
|------------------|-------|------------------------------|
| `precio`         | float | Precio total en USD          |
| `superficie_m2`  | float | Superficie cubierta en m²    |
| `cocina_separada`| 0/1   | 1 = tiene cocina separada    |
| `monoambiente`   | 0/1   | 1 = es monoambiente          |
| `a_estrenar`     | 0/1   | 1 = a estrenar               |
| `patio`          | 0/1   | 1 = tiene patio              |
| `planta_baja`    | 0/1   | 1 = planta baja              |

---

## Archivos generados

Los archivos se guardan en la carpeta `results/`:

- **`resultado_<nombre>_<timestamp>.csv`** — datos originales + `precio_predicho` + `residuo` + `es_outlier` + `tipo_outlier`
- **`reporte_<nombre>_<timestamp>.txt`** — ecuación del modelo, coeficientes, métricas y resumen de outliers
