"""
Precomputa TODO el análisis (inferencia XGBoost en vivo al arrancar) y lo
devuelve como un dict listo para inyectar en el frontend. Reusa la lógica
de api.py (mismo modelo, mismas funciones).
"""
import json
import api


def build_bundle() -> dict:
    bundle = {"meta": api.meta(), "years": {}, "zonas": {}, "evolucion": {}}

    anio_actual = api.ANIOS[-1]  # solo el año vigente usa el LLM (coste/tiempo)

    for a in api.ANIOS:
        mp = json.loads(api.mapa(a).body)
        bundle["years"][a] = {"kpis": api.kpis(a), "mapa": mp}
        bundle["zonas"][a] = {}
        for f in mp["features"]:
            z = f["properties"]["zona"]
            if f["properties"]["score"] is not None:
                bundle["zonas"][a][z] = {
                    "detalle": api.zona(z, a),
                    # Arquitectura híbrida: el LLM redacta las recomendaciones
                    # del año vigente; los años históricos usan reglas.
                    "reco": api.recomendaciones(z, a, usar_llm=(a == anio_actual)),
                }

    zonas_all = [f["properties"]["zona"]
                 for f in json.loads(api.mapa(api.ANIOS[-1]).body)["features"]]
    for z in zonas_all:
        bundle["evolucion"][z] = api.evolucion(z)

    return bundle
