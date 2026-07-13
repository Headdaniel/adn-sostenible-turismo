# Especificación de la API

Backend FastAPI. Documentación interactiva autogenerada disponible en `/docs` (Swagger).

**Base URL (producción):** `https://theodoreart-inteligencia-turistica.hf.space`

---

## Endpoints

### `GET /api/meta`
Metadatos del sistema: años disponibles, número de variables y fuentes, puntos de referencia.

### `GET /api/kpis?anio={año}`
Indicadores ejecutivos del distrito.

```json
{
  "score_territorial": 29.8,
  "nivel": "Estable",
  "zonas_prioritarias": 2,
  "alertas_activas": 50,
  "tendencia": 0.7
}
```

El `score_territorial` es un **promedio ponderado por `peso_turistico`**: las zonas de mayor
intensidad turística pesan más que los corregimientos rurales. La `tendencia` se expresa en
**puntos del índice** frente al año anterior (positivo = empeora).

### `GET /api/mapa?anio={año}`
GeoJSON de las 31 zonas con el score predicho inyectado en cada *feature*.

### `GET /api/zona/{nombre}?anio={año}`
Diagnóstico completo de una zona: score local, nivel, tendencia, factores de riesgo y
alertas activas.

### `GET /api/evolucion/{nombre}`
Serie temporal 2016–2024: zona seleccionada vs. promedio territorial.

### `GET /api/recomendaciones/{nombre}?anio={año}&usar_llm={bool}`
Recomendaciones de política pública.

```json
{
  "zona": "TAGANGA",
  "nivel": "Riesgo Alto",
  "general": "...",
  "acciones": ["...", "...", "..."],
  "fuente": "llama-4-scout-17b (Groq)"
}
```

El campo **`fuente`** indica el origen del texto: `llama-4-scout-17b (Groq)` si lo generó el
LLM, o `reglas` si operó el fallback determinista.

---

## Configuración

| Variable de entorno | Requerida | Función |
|---|---|---|
| `GROQ_API_KEY` | No | Habilita la IA generativa. Sin ella, el sistema usa el fallback por reglas. |

---

## Notas de implementación

- **Inferencia en vivo:** cada petición de score ejecuta `MODEL.predict()` sobre el XGBoost
  cargado en memoria. No hay valores precalculados en disco.
- **Rate limiting:** el tier gratuito de Groq limita a 30 peticiones/minuto. El sistema
  aplica una pausa entre llamadas y reintenta automáticamente ante un HTTP 429.
- **Scores acotados:** las predicciones se restringen al rango válido [0, 100].
