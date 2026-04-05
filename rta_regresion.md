# Cómo funciona `regression.py`

---

## La idea central

Imaginá que tenés una planilla con 620 departamentos. Cada uno tiene un precio y varias características (metros cuadrados, si tiene balcón, etc.). El programa mira todos esos datos y encuentra **la fórmula matemática que mejor explica el precio**.

Esa fórmula es una suma:

```
Precio = número_base
       + (valor de cada m²)    × metros cuadrados
       + (valor del balcón)    × tiene_balcon
       + ...
```

Eso se llama **regresión lineal**. La librería `scikit-learn` hace el cálculo pesado por nosotros.

---

## Parte 1 — Las variables

```python
COLUMNAS_X = ["M2", "Balcon2", "Amenities", ...]
COLUMNA_Y  = "Precio"
```

- **X** son las columnas que usamos para *predecir* (las causas).
- **Y** es lo que queremos *predecir* (el efecto: el precio).

---

## Parte 2 — La función principal

```python
def ajustar_modelo(df):
```

Recibe un DataFrame (básicamente una tabla de datos) y sigue estos pasos:

**Paso 1 — Separar los datos**
```python
X = df[COLUMNAS_X].values   # tabla de características
y = df[COLUMNA_Y].values    # columna de precios reales
```

**Paso 2 — Entrenar el modelo**
```python
modelo = LinearRegression()
modelo.fit(X, y)
```
`fit()` es el momento donde la librería "aprende" de los datos. Busca los mejores valores para cada coeficiente de la fórmula.

**Paso 3 — Predecir y calcular errores**
```python
y_pred   = modelo.predict(X)   # precio que el modelo calcula para cada depto
residuos = y - y_pred          # diferencia entre precio real y predicho
```
El **residuo** es el error. Si es positivo, el depto sale más caro que lo esperado (sobrevaluado). Si es negativo, sale más barato (subvaluado).

**Paso 4 — Medir qué tan bueno es el modelo**
```python
r2   = r2_score(y, y_pred)
rmse = sqrt(mean_squared_error(y, y_pred))
```
- **R²** va de 0 a 1. Cuanto más cerca de 1, mejor explica el modelo el precio. Un R²=0.25 (el que obtuvimos) significa que el modelo explica el 25% de la variación de precios — hay mucho que los m² y amenities no explican.
- **RMSE** es el error promedio en dólares. Obtuvimos ~21.000 USD de error promedio.

**Paso 5 — Armar la ecuación legible**
```python
partes = [f"{modelo.intercept_:+.2f}"]
for col, coef in coeficientes.items():
    partes.append(f"{coef:+.2f} * {col}")
```
Convierte los números en un texto como `precio = +75047 +16.07 * M2 +9586 * Balcon2 ...` para que una persona lo pueda leer.

---

## Lo que devuelve

La función devuelve un diccionario con todo junto:

| Clave | Qué es |
|---|---|
| `coeficientes` | cuánto aporta cada variable al precio |
| `r2` | qué tan bueno es el modelo (0-1) |
| `rmse` | error promedio en USD |
| `precio_predicho` | array con el precio calculado para cada depto |
| `residuos` | array con la diferencia real vs predicho |
| `ecuacion_str` | la fórmula en texto legible |

Ese diccionario lo usan tanto `procesar.py` (para guardar los archivos) como `app.py` (para responder al frontend).
