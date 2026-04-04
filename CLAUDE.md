# Big Data — Análisis Inmobiliario Córdoba

Programa de análisis de datos inmobiliarios de la ciudad de Córdoba, Argentina.

**Rol**: Eres un experto en Data Science. Debes crear un programa que procese
valores inmobiliarios de departamentos para toma de decisiones de inmobiliarias.

**Objetivo**: Detectar qué inmuebles están muy por debajo o muy por encima del
precio esperado según un modelo estadístico, para recibir tratamiento diferencial.

## Contexto de IA

CLAUDE.md: úsalo como fuente de verdad.
CLAUDE-Dicc.md: úsalo para revisar los nombres de variables, funciones, endpoints y convenciones de este proyecto.
CLAUDE-Plan.md: úsalo para avanzar en el desarrollo del proyecto de a una etapa a la vez.

## Forma de programar

Programa en forma simple y clara para que un humano lo pueda entender facilmente.
Programa de forma modular.
Quiero que cada modulo se pueda usar independientemente desde consola y reciva todas las condiciones para procesar el archivo.csv


## Stack de programación

- Backend: Python (Flask monolito — API + templates en un proceso)
- Frontend: JavaScript vanilla, HTML y CSS sin Node.js
- Gráficos: Chart.js desde CDN (sin npm)
- Modelo estadístico: scikit-learn (LinearRegression)


## Caso de uso

1. El usuario sube un archivo CSV con un lote de datos de un sector inmobiliario
   (ej: departamentos de 1 dormitorio en Nueva Córdoba).

2. El sistema ajusta una regresión lineal múltiple con las variables del CSV
   y calcula los residuos de estimación para cada inmueble.

3. El usuario configura el umbral de sigma (desvíos estándar) desde la interfaz.

4. El sistema clasifica cada inmueble como: normal / sobrevaluado / subvaluado.

5. Se generan dos archivos descargables:
   - CSV con los valores originales + precio predicho + residuo + clasificación
   - TXT con la ecuación lineal obtenida, coeficientes y métricas del modelo

6. Los resultados quedan guardados en carpetas locales para consulta futura.


## Formato del CSV de entrada

Columnas requeridas:

| Columna          | Tipo  | Descripción                        |
|------------------|-------|------------------------------------|
| precio           | float | Precio total en USD                |
| superficie_m2    | float | Superficie cubierta en m²          |
| cocina_separada  | 0/1   | Tiene cocina separada              |
| monoambiente     | 0/1   | Es monoambiente                    |
| a_estrenar       | 0/1   | Es a estrenar (nuevo)              |
| patio            | 0/1   | Tiene patio                        |
| planta_baja      | 0/1   | Es planta baja                     |

- Separador: coma (`,`) o punto y coma (`;`) — auto-detectado
- Encoding: UTF-8
- Sin columna de ID — se usa número de fila automático


## Modelo estadístico

- Variable Y (objetivo): `precio` (USD)
- Variables X (predictoras): `superficie_m2` + los 5 amenities binarios
- Algoritmo: Regresión Lineal Múltiple (OLS)
- Criterio outlier: residuo > N × σ(residuos), donde N es configurable en la UI
  - sobrevaluado: residuo > +N×σ
  - subvaluado:   residuo < −N×σ


## Estructura del proyecto

test2/
├── app.py                  ← Flask (API + templates)
├── services/
│   ├── regression.py       ← ajuste del modelo lineal
│   └── outliers.py         ← clasificación de outliers
├── templates/index.html    ← UI principal
├── static/app.js           ← lógica frontend
├── static/style.css        ← estilos
├── data/                   ← CSVs de entrada
├── results/                ← CSVs resultado + TXT reportes
├── requirements.txt
├── CLAUDE.md               ← fuente de verdad (edita el usuario)
├── CLAUDE-Dicc.md          ← diccionario técnico (actualiza Claude)
└── Plan.md                 ← planificación