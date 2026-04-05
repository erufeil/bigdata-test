# Plan de Desarrollo — Análisis Inmobiliario Córdoba

> Archivo de planificación. No es código ejecutable.
> El CLAUDE.md lo actualiza el usuario. El CLAUDE-Dicc.md lo actualiza Claude automáticamente.

---

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Arquitectura | Flask monolito (API + HTML estático en un proceso) |
| Backend | Python + Flask |
| Frontend | HTML / JS vanilla / CSS — sin Node.js |
| Gráficos | Chart.js desde CDN |
| Modelo estadístico | Regresión lineal múltiple (scikit-learn) |
| Variable objetivo (Y) | `precio` (USD) |
| Variables predictoras (X) | `superficie_m2` + 5 amenities binarios |
| Criterio outlier | Residuos > N desvíos estándar del modelo |
| Umbral sigma | Configurable en la UI (default 2.0) |
| Salida principal | CSV con valores originales + predichos + residuos + etiqueta |
| Salida secundaria | TXT con ecuación lineal + métricas + resumen |
| Persistencia | Archivos JSON/CSV en carpetas locales |
| Moneda | USD (dólares) |
| Identificador de fila | Número de fila automático (sin columna ID) |
| Separador CSV | Auto-detectado (`,` o `;`) |

---

## Estructura de carpetas

```
test2/
├── app.py                      ← Flask: rutas API + servir templates
├── services/
│   ├── regression.py           ← ajustar_modelo(): regresión lineal + métricas
│   └── outliers.py             ← etiquetar_outliers(): clasifica cada fila
├── templates/
│   └── index.html              ← UI principal (una sola página)
├── static/
│   ├── app.js                  ← lógica frontend: fetch, tabla, gráfico
│   └── style.css               ← estilos visuales
├── data/                       ← CSVs de entrada subidos por el usuario
├── results/                    ← CSVs resultado + TXT reportes + index.json
├── requirements.txt
├── CLAUDE.md                   ← fuente de verdad del proyecto (edita el usuario)
├── CLAUDE-Dicc.md              ← diccionario técnico (actualiza Claude)
└── Plan.md                     ← este archivo
```

---

## Formato del CSV de entrada

```
precio,superficie_m2,cocina_separada,monoambiente,a_estrenar,patio,planta_baja
85000,52,1,0,0,0,0
72000,48,0,1,0,0,1
```

| Columna | Tipo | Descripción |
|---|---|---|
| `precio` | float | Precio total en USD |
| `superficie_m2` | float | Superficie cubierta en m² |
| `cocina_separada` | 0/1 | 1 = tiene cocina separada |
| `monoambiente` | 0/1 | 1 = es monoambiente |
| `a_estrenar` | 0/1 | 1 = a estrenar (nuevo) |
| `patio` | 0/1 | 1 = tiene patio |
| `planta_baja` | 0/1 | 1 = planta baja |

---

## Modelo estadístico

```
precio = β₀ + β₁·superficie_m2 + β₂·cocina_separada + β₃·monoambiente
               + β₄·a_estrenar + β₅·patio + β₆·planta_baja
```

- **Método**: Regresión Lineal Múltiple (Ordinary Least Squares)
- **Librería**: `scikit-learn.LinearRegression`
- **Residuo**: `precio_real - precio_predicho`
- **Outlier**: `|residuo| > sigma * std(residuos)`
  - `sobrevaluado`: residuo > +umbral
  - `subvaluado`: residuo < −umbral

---

## Archivos de salida

### CSV resultado (`results/resultado_<nombre>_<timestamp>.csv`)
Columnas: todas las originales + `precio_predicho` + `residuo` + `es_outlier` + `tipo_outlier`

### TXT reporte (`results/reporte_<nombre>_<timestamp>.txt`)
```
============================================================
  REPORTE DE ANÁLISIS INMOBILIARIO
============================================================
Fecha y hora   : 2026-04-03 14:30:22
Archivo origen : nva_cordoba_1dorm.csv
Sigma utilizado: 2.0

ECUACIÓN DEL MODELO
------------------------------------------------------------
precio = +12500.00 +950.00 * superficie_m2 +3200.00 * cocina_separada ...

COEFICIENTES
------------------------------------------------------------
  superficie_m2       : +950.0000 USD
  cocina_separada     : +3200.0000 USD
  ...

MÉTRICAS DEL MODELO
------------------------------------------------------------
  R²             : 0.8342
  RMSE           : 4123.50 USD
  Std. residuos  : 4100.00 USD
  Umbral outlier : ±8200.00 USD

RESUMEN DE INMUEBLES
------------------------------------------------------------
  Total analizados : 45
  Normales         : 38
  Outliers total   : 7
    Sobrevaluados  : 4
    Subvaluados    : 3
============================================================
```

---

## Endpoints API Flask

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/` | Sirve `index.html` |
| `POST` | `/upload` | Recibe CSV → guarda en `/data/` → retorna preview |
| `POST` | `/analyze` | Recibe `{filename, sigma}` → ejecuta modelo → retorna resultados |
| `GET` | `/download/csv/<filename>` | Descarga CSV resultado |
| `GET` | `/download/report/<filename>` | Descarga TXT reporte |
| `GET` | `/results` | Lista historial de análisis |

---

## Frontend — Secciones de la UI

1. **Upload**: selector de archivo CSV (drag & drop)
2. **Configuración**: input numérico para sigma (default 2.0)
3. **Botón Analizar**
4. **Estadísticas**: R², RMSE, ecuación del modelo
5. **Gráfico**: scatter precio vs superficie con línea de regresión (Chart.js)
   - Puntos rojos = sobrevaluados
   - Puntos azules = subvaluados
   - Puntos grises = normales
6. **Tabla de resultados**: todas las filas, coloreadas por tipo_outlier
7. **Descargas**: botón CSV + botón TXT
8. **Historial**: lista de análisis anteriores con link para re-descargar

---

## Librerías Python

```
flask>=3.0.0
pandas>=2.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
```

## Cómo iniciar

```bash
pip install -r requirements.txt
flask run
# Abrir http://localhost:5000
```

---

## Plan de acción

### Etapa 1

Crea solo el backend en python y el readme de cómo se usa.

### Etapa 2

Crea un archivo de salida tipo txt con los resultados estadísticos obtenidos y tambien el archivo csv de respuesta.

### Etapa 3

Crear el módulo `services/enriquecer.py` que lee una columna de texto libre (descripción)
de un CSV en bruto y genera nuevas columnas binarias (0/1) a partir de la detección
de palabras clave configurables. El módulo debe ser adaptable a cualquier tabla de
entrada: el nombre de la columna y el diccionario de variables se definen en un
archivo externo `config_keywords.json`, sin modificar el código.

**Archivo de configuración `config_keywords.json`:**

Define la columna de origen y la lista de variables a generar. Cada variable tiene
un nombre de columna de salida y una lista de palabras/frases clave a buscar
(búsqueda case-insensitive). Ejemplo:

```json
{
  "columna_descripcion": "description",
  "variables": [
    {
      "nombre": "C_integrada",
      "palabras_clave": ["cocina integrada", "cocina americana", "cocina sectorizada", "cocina semiseparada"]
    },
    {
      "nombre": "C_independiente",
      "palabras_clave": ["cocina independiente", "cocina separada"]
    },
    {
      "nombre": "Patio",
      "palabras_clave": ["patio"]
    },
    {
      "nombre": "PB",
      "palabras_clave": ["pb", "planta baja"]
    },
    {
      "nombre": "Amenities",
      "palabras_clave": ["amenities", "terraza con", "juegos infantiles", "gimnasio", "piscina", "pileta", "quincho", "sum", "salon de usos multiples"]
    },
    {
      "nombre": "Balcon",
      "palabras_clave": ["balcon", "balcón"]
    },
    {
      "nombre": "Monoambiente",
      "palabras_clave": ["monoambiente", "mono ambiente", "mono-ambiente", "ambiente unico", "ambiente único"]
    },
    {
      "nombre": "A estrenar",
      "palabras_clave": ["a estrenar"]
    },
    {
      "nombre": "Descartar",
      "palabras_clave": ["1, 2 y 3 dormitorios", "1, 1 y 1/2", "1-2-3 dormitorios", "2 dormitorios", "3 dormitorios"] 
    }
  ],
  "columnas_derivadas": [
    {
      "nombre": "Sep_check",
      "operacion": "suma",
      "fuentes": ["C_integrada", "C_independiente"]
    }
  ],
  "columnas_extraidas": [
    {
      "nombre": "id_publicacion",
      "columna_origen": "url",
      "patron": "(\\d{8})\\.html"
    }
  ]
}
```

**Función principal `enriquecer_desde_descripcion(df, ruta_config)`:**

1. Leer el JSON de configuración.
2. Verificar que la columna de descripción exista. Si no existe, avisar y continuar sin cambios.
3. Por cada variable: buscar las palabras clave en el texto (lowcase), asignar 1 si hay
   coincidencia, 0 si no.
4. Calcular columnas derivadas (ej: `Sep_check = C_integrada + C_independiente`).
5. Eliminar columnas completamente vacías del DataFrame resultante.
6. Devolver el DataFrame enriquecido y la lista de columnas generadas.

**Punto de inserción en el pipeline** (antes de la regresión):

```
Cargar CSV → enriquecer_desde_descripcion() → ajustar_modelo() → etiquetar_outliers() → Guardar salidas
```

El paso es opcional: si no se pasa `--config`, el pipeline continúa igual que antes.

**Uso desde consola:**

```bash
python services/enriquecer.py --archivo datos.csv --config config_keywords.json --salida enriquecido.csv
```

## Etapa 4

Volver numerica la columna price_value, si no es numero poner 0.
Volver numerica square_meter_area_0

Sanitización

Borrar los registros completos si Sep_check tiene valor 0 o 2.
Borrar los registros completos si Descartar tiene valor 1.
Borrar los registros completos si el valor price_value es menor a 29000.
Borrar los registros completos si el valor square_meter_area_0 es menor a 20.

Generar un nuevo cvs datos_sani solo con las siguientes columnas el siguiente orden:
'Precio': "price_value", 'M2' : "square_meter_area_0", 'Balcon' : "Balcon", 'Amenities' : "Amenities", 'cocinaSep' : "C_independiente", 'Monoambiente' : "Monoambiente", 'A Estrenar' : "A estrenar", 'Patio PB' : "Patio", 'PB' : "PB".

Que esta informacion sea leida de un archivo json, que tambien será usado para armar las variables "y" que leerá procesar.py

