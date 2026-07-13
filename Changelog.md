# Changelog

## [1.0.0] — 2026-07-13
Versión de entrega para el Concurso Datos al Ecosistema 2026.

### Añadido
- Arquitectura híbrida de IA: XGBoost (diagnóstico) + Llama 4 Scout vía Groq (recomendaciones
  de política pública), con fallback determinista por reglas.
- Marcado explícito del contenido generado por IA en la interfaz (badge "✦ IA").
- Tres variables derivadas de gestión de destinos: `ocupacion_proxy`, `estacionalidad`,
  `residuos_per_turista` (consolidado de 20 variables).
- Documentación técnica completa: CRISP-ML, arquitectura, diccionario de datos, evaluación
  de impacto y ética, guía de validación.
- Notebooks de análisis exploratorio, correlaciones y evaluación del modelo.

### Modificado
- Modelo reentrenado con 16 features: R²=0.998 (test), R²=0.961±0.018 (CV 5-fold).
- Score Territorial agregado ahora se calcula como promedio **ponderado por intensidad
  turística**, en lugar de promedio simple.
- Tendencia territorial expresada en **puntos del índice** (antes en porcentaje, que producía
  saltos artificiales sobre bases pequeñas).

### Corregido
- Scores acotados al rango válido [0, 100] (antes podían resultar negativos).
- Visibilidad de las 31 zonas en el mapa: los corregimientos rurales, hasta 8.600 veces más
  pequeños que el casco urbano, ahora se representan con marcadores además del polígono.

## [0.1.0] — 2026-07-09
- Primera versión de la demo: dashboard con mapa interactivo e inferencia XGBoost en vivo.
