# CLAUDE-Dicc.md — Diccionario del Proyecto

> Archivo mantenido automáticamente por Claude. Contiene definiciones, variables, convenciones y opciones del proyecto.

---

## Variables del modelo

| Variable | Rol | Tipo | Descripción |
|---|---|---|---|
| `precio` | Y (target) | float | Precio total del inmueble en USD |
| `superficie_m2` | X | float | Superficie cubierta en metros cuadrados |
| `cocina_separada` | X | 0/1 | 1 si tiene cocina separada del living |
| `monoambiente` | X | 0/1 | 1 si es monoambiente (sin dormitorio separado) |
| `a_estrenar` | X | 0/1 | 1 si el inmueble es a estrenar (nuevo) |
| `patio` | X | 0/1 | 1 si tiene patio propio |
| `planta_baja` | X | 0/1 | 1 si está en planta baja |

---

## Variables calculadas (generadas por el sistema)

| Variable | Tipo | Descripción |
|---|---|---|
| `precio_predicho` | float | Precio estimado por la regresión lineal múltiple |
| `residuo` | float | Diferencia: `precio - precio_predicho` (positivo = sobrevaluado) |
| `es_outlier` | bool | True si `|residuo| > sigma * std(residuos)` |
| `tipo_outlier` | string | `sobrevaluado` / `subvaluado` / `normal` |

---

## Parámetros del modelo

| Parámetro | Valor por defecto | Rango | Descripción |
|---|---|---|---|
| `sigma` | 2.0 | 1.0 – 3.0 | Número de desvíos estándar del residuo para clasificar outlier |

---

## Algoritmo

| Término | Definición |
|---|---|
| **Regresión lineal múltiple** | Modelo estadístico que predice `precio` como combinación lineal de las variables X |
| **Residuo** | Error de estimación: `precio_real - precio_predicho` |
| **Outlier** | Inmueble cuyo residuo supera ±N desvíos estándar del conjunto de residuos |
| **R²** | Coeficiente de determinación: proporción de varianza explicada por el modelo (0 a 1) |
| **RMSE** | Raíz del error cuadrático medio. En USD, indica el error típico de estimación |
| **Intercepto (β₀)** | Valor base del precio cuando todas las variables X son 0 |
| **Coeficiente (βᵢ)** | Impacto marginal de cada variable X sobre el precio predicho |

---

## Formato CSV de entrada

| Propiedad | Valor |
|---|---|
| Separador | `,` (auto-detecta también `;`) |
| Encoding | UTF-8 |
| Moneda | USD (dólares) |
| Amenities | Codificados como `1` (tiene) / `0` (no tiene) |
| Identificador | No existe — se usa número de fila (índice) |
| Cabecera | Requerida en la primera fila |

### Ejemplo de fila válida

```
precio,superficie_m2,cocina_separada,monoambiente,a_estrenar,patio,planta_baja
85000,52,1,0,0,0,0
```

---

## Archivos del proyecto

| Archivo | Rol |
|---|---|
| `app.py` | Aplicación Flask principal — define todas las rutas API |
| `services/regression.py` | Encapsula el modelo de regresión lineal (scikit-learn) |
| `services/outliers.py` | Detecta y etiqueta outliers a partir de los residuos |
| `templates/index.html` | Interfaz de usuario principal |
| `static/app.js` | Lógica del frontend (fetch, render tabla, gráfico) |
| `static/style.css` | Estilos visuales |
| `data/` | Carpeta donde se guardan los CSVs subidos |
| `results/` | Carpeta donde se guardan CSVs resultado y TXT reportes |
| `results/index.json` | Índice JSON con el historial de análisis realizados |

---

## Endpoints API

| Método | Ruta | Parámetros | Retorna |
|---|---|---|---|
| `GET` | `/` | — | index.html |
| `POST` | `/upload` | `file` (multipart) | `{filename, preview[], columnas[]}` |
| `POST` | `/analyze` | `{filename, sigma}` | `{stats, rows[], resultado_csv, reporte_txt}` |
| `GET` | `/download/csv/<filename>` | — | Archivo CSV |
| `GET` | `/download/report/<filename>` | — | Archivo TXT |
| `GET` | `/results` | — | `[{filename, fecha, n_total, n_outliers, r2}]` |

---

## Convenciones de nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| CSV resultado | `resultado_YYYYMMDD_HHMMSS.csv` | `resultado_20260403_143022.csv` |
| TXT reporte | `reporte_YYYYMMDD_HHMMSS.txt` | `reporte_20260403_143022.txt` |
| CSV entrada | Nombre original del archivo subido | `nva_cordoba_1dorm.csv` |

---

## Librerías

### Python (backend)
| Librería | Versión mínima | Uso |
|---|---|---|
| `flask` | 3.x | Framework web |
| `pandas` | 2.x | Lectura y manipulación de CSV |
| `scikit-learn` | 1.x | `LinearRegression` |
| `numpy` | 1.x | Cálculos estadísticos |

### JavaScript (frontend)
| Librería | Fuente | Uso |
|---|---|---|
| `Chart.js` | CDN | Gráfico scatter con línea de regresión |

---

## Tipos de outlier

| Tipo | Condición | Interpretación | Color en UI |
|---|---|---|---|
| `sobrevaluado` | `residuo > +sigma * σ` | El inmueble pide más de lo que el mercado justifica | Rojo |
| `subvaluado` | `residuo < -sigma * σ` | El inmueble pide menos de lo esperado — oportunidad | Azul |
| `normal` | Dentro del rango | Precio alineado con el mercado | Blanco |
