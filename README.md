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

## Procesar desde consola (sin servidor)

```bash
python procesar.py --archivo csvmuestra1.csv
python procesar.py --archivo csvmuestra1.csv --sigma 1.5
python procesar.py --archivo csvmuestra1.csv --separador punto_y_coma --salida_dir mis_resultados/
```

Los archivos se guardan automáticamente en `results/` (o la carpeta indicada):
- `resultado_<nombre>_<timestamp>.csv`
- `reporte_<nombre>_<timestamp>.txt`

Opciones disponibles:

| Parámetro      | Default   | Descripción                                   |
|----------------|-----------|-----------------------------------------------|
| `--archivo`    | —         | Ruta al CSV de entrada (obligatorio)          |
| `--sigma`      | 2.0       | Sensibilidad outlier (mayor = menos outliers) |
| `--separador`  | auto      | `coma`, `punto_y_coma` o `auto`               |
| `--salida_dir` | results/  | Carpeta donde se guardan los archivos         |

### Solo ver el modelo (sin guardar archivos)
```bash
python services/regression.py --archivo csvmuestra1.csv
```

---

## Formato del CSV de entrada

```
Precio;M2;Balcon2;Amenities;cocinaSep;Monoambiente;A Estrenar;Patio PB;PB
85000;52;1;0;1;0;0;0;0
72000;48;0;0;0;1;0;0;1
```

| Columna        | Tipo  | Descripción                    |
|----------------|-------|--------------------------------|
| `Precio`       | float | Precio total en USD            |
| `M2`           | float | Superficie cubierta en m²      |
| `Balcon2`      | 0/1   | 1 = tiene balcón               |
| `Amenities`    | 0/1   | 1 = tiene amenities            |
| `cocinaSep`    | 0/1   | 1 = cocina separada            |
| `Monoambiente` | 0/1   | 1 = es monoambiente            |
| `A Estrenar`   | 0/1   | 1 = a estrenar                 |
| `Patio PB`     | 0/1   | 1 = tiene patio en planta baja |
| `PB`           | 0/1   | 1 = unidad en planta baja      |

---

## Archivos generados

Los archivos se guardan en la carpeta `results/`:

- **`resultado_<nombre>_<timestamp>.csv`** — datos originales + `precio_predicho` + `residuo` + `es_outlier` + `tipo_outlier`
- **`reporte_<nombre>_<timestamp>.txt`** — ecuación del modelo, coeficientes, métricas y resumen de outliers
