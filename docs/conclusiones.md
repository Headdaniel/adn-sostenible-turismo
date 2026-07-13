# Conclusiones, Limitaciones y Próximos Pasos

---

## 1. Hallazgos

### 1.1 La presión turística está extremadamente concentrada

El casco urbano de Santa Marta alcanza un **Score Territorial de 82.7/100 (crítico)**,
mientras que **27 de las 31 zonas** se mantienen por debajo de 40. Solo cuatro zonas
superan el umbral de riesgo.

**Implicación de política pública:** las medidas de mitigación no deben diseñarse a escala
municipal, sino **focalizarse territorialmente**. Un promedio distrital diluye el problema
y llevaría a subestimar la urgencia en las zonas críticas.

### 1.2 Taganga es la zona de riesgo emergente

| Año | Score |
|---|---|
| 2016 | 13.0 |
| 2024 | 49.2 |

Un **incremento del 279% en ocho años** — la trayectoria más acelerada del distrito.
Taganga aún no es crítica, pero su velocidad de deterioro la convierte en la prioridad de
intervención preventiva: es más barato actuar ahora que remediar después.

### 1.3 La intensidad turística domina sobre las variables socioeconómicas

`peso_turistico` concentra el **30.3% de la importancia** del modelo y correlaciona 0.856
con el score. En contraste, `gini`, `pobreza` e `ingreso` aportan **menos del 1% cada una**.

**Lectura:** en este territorio, la presión sobre el destino se explica principalmente por
la **actividad turística misma**, no por las condiciones socioeconómicas preexistentes. El
turismo no está sobre un territorio vulnerable: lo está volviendo vulnerable.

### 1.4 La capacidad instalada predice presión

Las variables del RNT (prestadores, camas, habitaciones) suman el **42.6%** de la
importancia del modelo. La oferta de alojamiento registrada es, por sí sola, un predictor
robusto de la presión territorial futura — un insumo directo para las decisiones de
licenciamiento y ordenamiento turístico.

---

## 2. Limitaciones ⚠️

Esta sección se declara con transparencia deliberada. Consideramos que una herramienta
para lo público debe ser auditable, y eso exige exponer sus debilidades.

### 2.1 `peso_turistico`: supuesto de diseño, no dato oficial

**Es la limitación más importante de este trabajo.**

La mayoría de indicadores oficiales (residuos, pobreza, gini, dengue) existen únicamente a
nivel **municipal agregado**. Para distribuirlos entre las 31 zonas fue necesario introducir
un modulador espacial: `peso_turistico`, que asigna a cada zona un coeficiente de intensidad
turística relativa (de 0.08 en corregimientos rurales a 1.0 en el casco urbano).

**Este coeficiente es una estimación del equipo, no proviene de una fuente estadística
oficial verificable.**

Su impacto es considerable: es la variable **más influyente del modelo (30.3%)**. Por tanto,
una parte sustancial de la variabilidad del Score Territorial descansa sobre un supuesto de
diseño, no sobre una medición.

**Mitigación propuesta:** sustituirlo por una medida observada de intensidad turística por
zona (datos de telefonía móvil, ocupación hotelera georreferenciada, o conteos de visitantes
en puntos de acceso).

### 2.2 El R² de 0.998 no es lo que parece

El target (`score_pca`) es una combinación lineal (PCA) de las mismas variables que
alimentan el modelo. El XGBoost **aprende a reproducir una fórmula conocida**, no a predecir
un fenómeno externo.

Un R² cercano a 1 es el resultado **esperado** en esta configuración; presentarlo como
"99.8% de precisión predictiva" sería engañoso.

**Lo que el modelo sí aporta:** un motor de inferencia que permite recalcular el score ante
nuevas combinaciones de variables (simulación de escenarios, zonas sin score previo,
proyecciones), servido en producción vía API.

**Métrica honesta:** validación cruzada R² = 0.9606 ± 0.018.

### 2.3 Tres alertas están simuladas

Declaradas explícitamente en [`../models/config_alertas.json`](../models/config_alertas.json):

| Alerta | Estado | Razón |
|---|---|---|
| `alerta_residuos` | ✅ Real | Umbrales sobre datos SUI |
| `alerta_presion` | ✅ Real | Umbrales sobre `score_pca` |
| `alerta_sanitaria` | ✅ Real | Umbrales sobre SIVIGILA + ONI |
| `alerta_hidrica` | ⚠️ Simulada | Sin estación IDEAM de agua en Santa Marta |
| `alerta_servicios` | ⚠️ Simulada | Sin dato de saturación de servicios públicos |
| `alerta_gentrificacion` | ⚠️ Simulada | Sin dato de arriendos / presión habitacional |

### 2.4 Granularidad temporal heterogénea

Algunas variables son mensuales (pasajeros, extranjeros, dengue), otras anuales (RNT,
gini, pobreza) y se replican dentro del año. Esto **subestima la variabilidad
intra-anual** de las variables anualizadas.

### 2.5 Volumen de datos

3.348 registros. Suficiente para un modelo estable (validado por CV), pero lejos de un
escenario Big Data. La cobertura es de un solo municipio.

### 2.6 Sin validación externa del indicador

El Score Territorial no ha sido contrastado contra una medida independiente de daño real
(quejas ciudadanas, indicadores de calidad ambiental medidos in situ). **Es un índice de
presión construido, no una medida validada de impacto.**

---

## 3. Próximos pasos

### Corto plazo — robustecer lo existente
1. **Sustituir `peso_turistico`** por una medida observada de intensidad turística zonal.
2. **Validación externa** del Score contra indicadores independientes (PQRS ambientales,
   mediciones de calidad de agua/aire).
3. **Completar las alertas simuladas** gestionando acceso a datos de IDEAM y de arriendos.

### Mediano plazo — escalar
4. **Pipeline ETL automatizado** con conexión directa a las APIs de datos.gov.co, para
   actualización continua sin intervención manual.
5. **Replicar en otros destinos** (Cartagena, San Andrés, Salento). La arquitectura es
   agnóstica al municipio: solo requiere el MGN correspondiente y las series locales.
6. **Detección de *data drift*** y reentrenamiento programado.

### Largo plazo — profundizar el modelo
7. **Inferencia causal.** El modelo actual es correlacional: identifica dónde hay presión,
   no qué intervención la reduciría. Un modelo causal (DAGs, diferencias en diferencias)
   permitiría evaluar el efecto esperado de cada medida antes de ejecutarla.
8. **Simulación de escenarios** de capacidad de carga bajo distintas políticas turísticas.
9. **Agente conversacional** sobre los datos territoriales, para consulta directa por parte
   de funcionarios sin formación técnica.

---

## 4. Reflexión final

Este sistema **no predice el futuro del turismo en Santa Marta**. Lo que hace es convertir
nueve fuentes dispersas de datos públicos en una **respuesta localizada a una pregunta que
hoy la administración no puede responder**: dónde está el turismo presionando más el
territorio, y hacia dónde va esa presión.

Su valor no está en la sofisticación del modelo, sino en que **cierra la distancia entre el
dato abierto y la decisión pública** — y en que declara con precisión hasta dónde llega su
propia evidencia.
