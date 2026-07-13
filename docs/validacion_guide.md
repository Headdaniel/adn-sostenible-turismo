# Guía de Validación

Instrucciones para que un evaluador reproduzca y audite los resultados.

---

## 1. Reproducir el entorno

```bash
git clone <url-del-repositorio>
cd adn-sostenible-turismo
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 2. Verificar el dataset

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/processed/dataset.csv')
print('Filas:', len(df), '| Columnas:', len(df.columns))
print('Zonas:', df.zona.nunique(), '| Periodo:', df.anio.min(), '-', df.anio.max())
print('Nulos:', df.isnull().sum().sum())
"
```

**Resultado esperado:** 3.348 filas × 27 columnas · 31 zonas · 2016–2024 · 0 nulos.

## 3. Reproducir la ingeniería de características

```bash
python src/ampliar_dataset.py
```

Regenera las 3 variables derivadas de forma determinista.

## 4. Reentrenar el modelo desde cero

```bash
python src/entrenar_modelo.py
```

**Resultado esperado** (semilla fija `random_state=42`):

| Métrica | Valor |
|---|---|
| R² (test) | ≈ 0.998 |
| MAE | ≈ 0.175 |
| R² (CV 5-fold) | ≈ 0.961 ± 0.018 |

⚠️ **Al interpretar el R²**, leer previamente la sección 2.2 de
[`conclusiones.md`](conclusiones.md): la cifra es alta por construcción del target, no por
capacidad predictiva sobre datos externos.

## 5. Verificar la inferencia en vivo

```bash
python src/app.py
```

Abrir `http://localhost:7860`. El modelo predice el score de cada zona en tiempo real al
arrancar: no hay valores precalculados en disco.

**Verificación vía API:**
```bash
curl "http://localhost:7860/api/zona/TAGANGA?anio=2024"
curl "http://localhost:7860/api/kpis?anio=2024"
```

## 6. Verificar la capa de IA generativa

```bash
export GROQ_API_KEY=<api_key>
python src/app.py
```

En el campo `fuente` de `/api/recomendaciones/{zona}`:
- `llama-4-scout-17b (Groq)` → el texto lo generó el LLM.
- `reglas` → operó el fallback determinista.

**Sin API key el sistema funciona igual**, usando el fallback. Esto es intencional: la
herramienta no debe caer por indisponibilidad de un proveedor externo.

## 7. Auditar los notebooks

| Notebook | Qué verifica |
|---|---|
| `01_EDA_exploracion_datos.ipynb` | Estructura, calidad y distribución del score |
| `02_limpieza_transformacion.ipynb` | Construcción de las variables derivadas |
| `03_analisis_descriptivo.ipynb` | Correlaciones (incluye el hallazgo sobre `peso_turistico`) |
| `04_modelo_predictivo.ipynb` | Métricas e importancia de variables |

## 8. Puntos de auditoría crítica

Un evaluador riguroso debería revisar específicamente:

1. **`peso_turistico`** — es un supuesto del equipo con 30.3% de importancia en el modelo.
   Declarado en `conclusiones.md` §2.1.
2. **El target es un PCA de las features** — explica el R² alto. Ver `conclusiones.md` §2.2.
3. **Tres alertas son simuladas** — marcadas en `models/config_alertas.json`.
4. **El sesgo de concentración urbana** — ver `public_impact_assessment.md` §3.
