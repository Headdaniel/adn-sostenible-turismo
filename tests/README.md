# Pruebas

## Estado actual

Las verificaciones del sistema se realizan mediante los procedimientos documentados en
[`../docs/validacion_guide.md`](../docs/validacion_guide.md), que permiten a un evaluador
externo reproducir y auditar los resultados.

**Validaciones implementadas en el propio código:**

| Verificación | Dónde |
|---|---|
| Integridad del *join* territorial (31/31 zonas) | Verificado contra geometrías DANE-MGN |
| Ausencia de nulos e infinitos | `src/ampliar_dataset.py` |
| Validación cruzada del modelo (5-fold) | `src/entrenar_modelo.py` |
| Acotación del score al rango [0,100] | `src/api.py` (`predecir_score`) |
| Fallback ante fallo del LLM | `src/api.py` (`recomendaciones`) |
| Reintento ante rate limit (HTTP 429) | `src/api.py` (`_groq_recomendar`) |

## Fuera del alcance de esta entrega

Una suite formal de pruebas unitarias, de integración y de sesgo algorítmico automatizado
está contemplada como próximo paso (ver [`../docs/conclusiones.md`](../docs/conclusiones.md)).
