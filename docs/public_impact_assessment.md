# Evaluación de Impacto Público, Ética y Sesgos

---

## 1. Impacto esperado

### Ambiental
Focalización de la gestión de residuos y la vigilancia ambiental en las zonas de mayor
presión, en lugar de una distribución uniforme que subatiende los puntos críticos.

### Social
Anticipación de la presión sobre servicios públicos y salud en temporada alta, protegiendo
a las comunidades receptoras del turismo.

### Económico
Sustento con evidencia para calibrar tasas turísticas locales y para negociar
corresponsabilidad con el sector privado.

### Institucional
Cierra la brecha entre el dato abierto disponible y la decisión pública concreta. La
arquitectura es replicable en cualquier municipio turístico del país.

---

## 2. Riesgos éticos y mitigación

| Riesgo | Mitigación aplicada |
|---|---|
| **Decisiones basadas en un supuesto no validado** (`peso_turistico`) | Declarado explícitamente en la documentación y en el diccionario de datos. Se advierte que es la variable más influyente del modelo. |
| **Sobreconfianza en las métricas** (R²=0.998) | Se explica abiertamente por qué esa cifra no representa capacidad predictiva real. Se reporta la validación cruzada como métrica honesta. |
| **Confusión entre contenido humano y generado por IA** | Todo texto producido por el LLM está marcado en la interfaz con un badge "✦ IA" y una nota explicativa. |
| **Alucinación del LLM** | El modelo recibe únicamente el diagnóstico numérico calculado por el XGBoost como contexto, y se le exige salida estructurada (JSON). Existe fallback determinista. |
| **Alertas simuladas presentadas como reales** | Separadas explícitamente en `config_alertas.json` (`alertas_reales` vs. `alertas_simuladas`), con la razón de la simulación documentada. |

---

## 3. Sesgos identificados

### Sesgo de concentración urbana
Los indicadores oficiales existen a nivel municipal agregado. Al distribuirlos mediante
`peso_turistico`, **el modelo tiende a reproducir la hipótesis de que la presión sigue a la
intensidad turística**. Esto puede **subestimar problemas en zonas rurales** con baja
afluencia pero alta vulnerabilidad.

**Este es el sesgo estructural más relevante del sistema y se declara sin atenuantes.**

### Sesgo de disponibilidad de datos
Las dimensiones con mejores fuentes (turística, RNT) dominan el modelo (42.6% de
importancia solo el RNT), mientras las socioeconómicas —peor medidas a nivel zonal— aportan
menos del 1.3%. **La importancia de una variable refleja tanto su relevancia real como la
calidad de su medición.**

### Ausencia de datos personales
Todos los indicadores son **agregados territoriales**. El sistema no procesa información
personal identificable, por lo que no aplican riesgos de reidentificación ni requisitos de
anonimización.

---

## 4. Uso responsable

Este sistema es una **herramienta de priorización**, no un sustituto del juicio técnico ni
del proceso deliberativo de política pública.

Sus salidas —incluidas las recomendaciones generadas por IA— deben entenderse como
**insumos para la decisión**, sujetos a validación por parte de los equipos técnicos de la
administración distrital.

**No debe usarse** para justificar decisiones punitivas sobre territorios o comunidades sin
verificación en campo.
