# Marco Metodológico — CRISP-ML(Q)

El proyecto sigue **CRISP-ML(Q)** (*Cross-Industry Standard Process for Machine Learning
with Quality assurance*), la adaptación de CRISP-DM a proyectos de machine learning que
incorpora aseguramiento de calidad en cada fase.

---

## 1. Business & Data Understanding

### Objetivo de negocio
Dotar a la administración distrital de Santa Marta de un instrumento que permita
**anticipar y localizar la presión que el turismo ejerce sobre el territorio**, para
priorizar inversión pública y activar medidas de mitigación antes de que el daño sea
irreversible.

### Criterio de éxito
El sistema debe responder tres preguntas operativas:
1. ¿Qué zonas del distrito están bajo mayor presión turística?
2. ¿La situación está mejorando o empeorando respecto al año anterior?
3. ¿Qué acciones concretas debe tomar la administración en cada zona?

### Traducción a problema de ML
Construir un **indicador compuesto** (Score Territorial) que integre las dimensiones
turística, ambiental, socioeconómica y de salud pública, y un **modelo de regresión** capaz
de inferirlo a partir de las variables observables de cada zona.

### Comprensión de los datos
- 9 fuentes oficiales integradas (ver [`fuentes_datos.md`](fuentes_datos.md)).
- Granularidad final: **zona × año × mes** → 31 × 9 × 12 = 3.348 registros.
- Sin valores nulos tras la consolidación.
- Exploración documentada en [`../notebooks/01_EDA_exploracion_datos.ipynb`](../notebooks/01_EDA_exploracion_datos.ipynb).

**Hallazgo determinante del EDA:** la mayoría de indicadores oficiales existen solo a nivel
**municipal agregado**, no por zona. Esto obligó a introducir un modulador espacial
(`peso_turistico`) para distribuirlos territorialmente — decisión metodológica que se
declara abiertamente como limitación (ver [`conclusiones.md`](conclusiones.md)).

---

## 2. Data Preparation

### Consolidación
Integración de las 9 fuentes en una tabla única, homologando la clave territorial con los
nombres oficiales del Marco Geoestadístico Nacional (DANE-MGN), lo que garantiza un
*join* exacto 31/31 con las geometrías del mapa.

### Ingeniería de características
Se derivaron tres indicadores estándar de gestión de destinos turísticos
([`../src/ampliar_dataset.py`](../src/ampliar_dataset.py)):

| Variable | Construcción | Justificación |
|---|---|---|
| `ocupacion_proxy` | (pasajeros × peso) / camas | Presión de la demanda sobre la planta hotelera instalada |
| `estacionalidad` | flujo_mes / flujo_promedio_anual | Los picos de temporada alta son el momento de mayor riesgo |
| `residuos_per_turista` | log1p((residuos × peso) / flujo) | Huella ambiental por unidad de actividad turística |

La transformación logarítmica en la tercera corrige una cola extrema que aparece cuando el
flujo turístico tiende a cero (zonas rurales), donde el cociente crudo se dispara sin
significado interpretable.

### Construcción del target
El **Score Territorial** (`score_pca`) se obtiene por **Análisis de Componentes Principales**
sobre las variables de presión, reescalado a 0–100. Un score mayor indica **mayor presión**
sobre el territorio (peor situación).

---

## 3. Modeling

**Algoritmo:** XGBRegressor (gradient boosting sobre árboles).

**Justificación de la elección:**
- Maneja relaciones no lineales entre variables heterogéneas (turísticas, ambientales,
  socioeconómicas) sin requerir normalización previa.
- Robusto ante la fuerte asimetría de la distribución territorial.
- Proporciona **importancia de variables**, requisito para la interpretabilidad exigida en
  contextos de política pública.

**Hiperparámetros** (ver [`../models/modelo_xgboost_config.json`](../models/modelo_xgboost_config.json)):
`n_estimators=1000`, `learning_rate=0.05`, `max_depth=4`, `subsample=0.8`,
`colsample_bytree=0.8`, regularización L1=0.5 / L2=2.0, `early_stopping_rounds=50`.

La regularización y la profundidad limitada (4) se eligieron deliberadamente para
**contener el sobreajuste**, dado el tamaño moderado del dataset.

**Entrenamiento reproducible:** [`../src/entrenar_modelo.py`](../src/entrenar_modelo.py)
(`random_state=42` en todos los pasos).

---

## 4. Evaluation

| Métrica | Valor |
|---|---|
| R² (test) | 0.9979 |
| MAE (test) | 0.175 |
| RMSE (test) | 0.643 |
| **R² validación cruzada (5-fold)** | **0.9606 ± 0.0182** |

**Protocolo:** split 80/20 train-test, con un 20% interno adicional para *early stopping*.
Validación cruzada de 5 pliegues sobre el conjunto completo.

### Lectura crítica de las métricas ⚠️

El R² de test **no debe interpretarse como capacidad predictiva sobre el mundo real**.

El target (`score_pca`) es una combinación lineal (PCA) de las mismas variables que
alimentan el modelo. El XGBoost, por tanto, **aprende a reproducir una fórmula conocida**,
no a predecir un fenómeno externo no observado. Un R² cercano a 1 es el resultado esperado
en esta configuración, y sería sospechoso lo contrario.

**El valor real del modelo** no está en la precisión del ajuste, sino en su función como
**motor de inferencia en producción**: permite recalcular el score ante nuevas
combinaciones de variables (simulación de escenarios, proyecciones, zonas sin score
previo), sirviéndose vía API en tiempo real.

La **validación cruzada (0.9606 ± 0.018)** es la métrica conservadora y es la que se debe
usar para juzgar la estabilidad del modelo.

---

## 5. Deployment

**Arquitectura híbrida en producción** (ver [`architecture/`](architecture/)):

```
Datos abiertos → XGBoost (inferencia) → Llama 4 Scout (IA generativa) → Dashboard
```

- **Backend:** FastAPI. Carga el modelo serializado y expone endpoints REST
  ([`api_spec.md`](api_spec.md)).
- **Capa generativa:** Llama 4 Scout vía Groq. Recibe el diagnóstico cuantitativo de cada
  zona y lo traduce en recomendaciones de política pública ejecutables. Incluye
  **fallback determinista** por reglas si la API no está disponible: el sistema nunca falla.
- **Frontend:** dashboard interactivo (Leaflet + Chart.js) con mapa de las 31 zonas.
- **Despliegue:** Hugging Face Spaces, con inferencia en vivo del modelo al arrancar.

**Marcado de contenido generado por IA:** todo texto producido por el LLM está
explícitamente señalizado en la interfaz (badge "✦ IA" y nota al pie), como práctica de
IA responsable y transparencia hacia el usuario final.

---

## 6. Monitoring & Maintenance

**Estado actual (alcance de la demo):**
- Reentrenamiento reproducible mediante script versionado.
- Configuración del modelo (features, hiperparámetros, métricas, importancia) persistida en
  JSON para trazabilidad entre versiones.
- Umbrales de alerta parametrizados y auditables en `config_alertas.json`.

**Fuera del alcance de esta entrega** (ver [`conclusiones.md`](conclusiones.md)):
pipeline ETL automatizado, detección de *data drift*, y reentrenamiento programado.

---

## Aseguramiento de calidad (la "Q" de CRISP-ML)

| Fase | Control aplicado |
|---|---|
| Data Understanding | Verificación de nulos e infinitos; *join* 31/31 validado contra geometrías DANE |
| Data Preparation | Transformaciones documentadas y reproducibles vía script |
| Modeling | Semilla fija; regularización explícita; *early stopping* |
| Evaluation | Validación cruzada además del split simple; lectura crítica de métricas |
| Deployment | Fallback determinista ante fallo del LLM; scores acotados al rango válido [0,100] |
| Ética | Limitaciones y supuestos declarados; contenido de IA marcado en la interfaz |
