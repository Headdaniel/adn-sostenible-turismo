"""
Sistema de Inteligencia Predictiva de Turismo Sostenible — Santa Marta
Backend FastAPI. Sirve API + frontend estatico en un solo Hugging Face Space.

Inferencia en vivo: carga el modelo XGBoost (.pkl) y predice score_pca
por zona a partir de las 13 features del dataset.
"""

import json
import os
import pickle
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Carga de activos (una sola vez, al arrancar)
# ---------------------------------------------------------------------------
DF = pd.read_csv(BASE / "dataset.csv")

with open(BASE / "modelo_xgboost_config.json", encoding="utf-8") as f:
    MODEL_CFG = json.load(f)

with open(BASE / "config_alertas.json", encoding="utf-8") as f:
    ALERT_CFG = json.load(f)

with open(BASE / "modelo_xgboost_score.pkl", "rb") as f:
    MODEL = pickle.load(f)

FEATURES = MODEL_CFG["features"]  # 13 features en el orden exacto de entrenamiento
DISTRITO = "SANTA MARTA, DISTRITO TURÍSTICO, CULTURAL E HISTÓRICO"

with open(BASE / "santa_marta.geojson", encoding="utf-8") as f:
    GEOJSON = json.load(f)

ANIOS = sorted(DF["anio"].unique().tolist())

# Puntos de referencia (coordenadas aproximadas, solo visuales)
PUNTOS_REFERENCIA = [
    {"nombre": "El Rodadero", "lat": 11.2019, "lng": -74.2278},
    {"nombre": "Centro Histórico", "lat": 11.2408, "lng": -74.2110},
    {"nombre": "Taganga", "lat": 11.2664, "lng": -74.1922},
    {"nombre": "PNN Tayrona", "lat": 11.3122, "lng": -74.0300},
]


# ---------------------------------------------------------------------------
# Inferencia
# ---------------------------------------------------------------------------
def predecir_score(row: pd.Series) -> float:
    """Predice score_pca en vivo con el modelo XGBoost, acotado a [0, 100]."""
    X = pd.DataFrame([[row[f] for f in FEATURES]], columns=FEATURES)
    pred = float(MODEL.predict(X)[0])
    return max(0.0, min(100.0, pred))  # el score es un índice 0–100


def df_anio(anio: int) -> pd.DataFrame:
    """Promedio anual por zona, con score predicho en vivo."""
    sub = DF[DF["anio"] == anio].copy()
    if sub.empty:
        raise HTTPException(404, f"Sin datos para el año {anio}")
    # promedio de las features por zona (colapsa los 12 meses)
    agg = sub.groupby("zona")[FEATURES].mean().reset_index()
    agg["mes"] = 6  # mes medio de referencia para la feature 'mes'
    agg["score_pred"] = agg.apply(predecir_score, axis=1)
    return agg


def nivel_por_score(score: float) -> str:
    if score >= 70:
        return "Crítico"
    if score >= 40:
        return "Riesgo Alto"
    return "Estable"


def score_territorial_ponderado(agg: pd.DataFrame) -> float:
    """
    Score Territorial = promedio de los scores por zona ponderado por peso_turistico.
    Refleja el destino como conjunto turístico: las zonas de mayor intensidad
    turística pesan más que los corregimientos rurales de baja afluencia.
    """
    pesos = agg["peso_turistico"].clip(lower=0)
    if pesos.sum() == 0:
        return float(agg["score_pred"].mean())
    return float((agg["score_pred"] * pesos).sum() / pesos.sum())


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="ADN Sostenible — Inteligencia Turística")


@app.get("/api/meta")
def meta():
    """Metadatos para poblar selectores y contexto del concurso."""
    return {
        "anios": ANIOS,
        "n_zonas": DF["zona"].nunique(),
        "n_variables": len(FEATURES),
        "n_fuentes": 6,
        "rango_anios": f"{min(ANIOS)}–{max(ANIOS)}",
        "modelo": MODEL_CFG["modelo"],
        "r2": MODEL_CFG["metricas_test"]["R2"],
        "puntos_referencia": PUNTOS_REFERENCIA,
    }


@app.get("/api/kpis")
def kpis(anio: int = 2024):
    """4 tarjetas ejecutivas superiores, calculadas en backend."""
    agg = df_anio(anio)
    score_terr = score_territorial_ponderado(agg)

    zonas_prioritarias = int((agg["score_pred"] >= 40).sum())

    # alertas activas: cuenta zonas en estado crítico/alerta en su mes más reciente
    sub = DF[DF["anio"] == anio].sort_values("mes")
    ult = sub.groupby("zona").tail(1)  # último mes registrado por zona
    alertas_activas = int(
        (ult["alerta_residuos"] == "Crítico").sum()
        + (ult["alerta_presion"] == "Crítico").sum()
        + (ult["alerta_sanitaria"].isin(["Riesgo brote", "Vigilancia"])).sum()
    )

    # tendencia: variación del score territorial vs año anterior, en PUNTOS
    # (el score es un índice 0–100; usar % sobre bases pequeñas da saltos absurdos)
    tendencia = None
    if anio - 1 in ANIOS:
        prev = score_territorial_ponderado(df_anio(anio - 1))
        tendencia = round(score_terr - prev, 1)

    return {
        "score_territorial": round(score_terr, 1),
        "nivel": nivel_por_score(score_terr),
        "zonas_prioritarias": zonas_prioritarias,
        "alertas_activas": alertas_activas,
        "tendencia": tendencia,
    }


@app.get("/api/mapa")
def mapa(anio: int = 2024):
    """GeoJSON con score predicho inyectado en cada zona."""
    agg = df_anio(anio).set_index("zona")
    gj = json.loads(json.dumps(GEOJSON))  # copia
    for feat in gj["features"]:
        zona = feat["properties"]["zona"]
        if zona in agg.index:
            s = float(agg.loc[zona, "score_pred"])
            feat["properties"]["score"] = round(s, 1)
            feat["properties"]["nivel"] = nivel_por_score(s)
        else:
            feat["properties"]["score"] = None
            feat["properties"]["nivel"] = "Sin dato"
    return JSONResponse(gj)


@app.get("/api/zona/{nombre}")
def zona(nombre: str, anio: int = 2024):
    """Detalle de una zona: centro de decisión, drivers, alertas."""
    agg = df_anio(anio).set_index("zona")
    if nombre not in agg.index:
        raise HTTPException(404, f"Zona '{nombre}' no encontrada en {anio}")

    row = agg.loc[nombre]
    score = float(row["score_pred"])

    # tendencia local vs año anterior, en PUNTOS del índice
    tendencia_local = None
    if anio - 1 in ANIOS:
        prev = df_anio(anio - 1).set_index("zona")
        if nombre in prev.index:
            p = float(prev.loc[nombre, "score_pred"])
            tendencia_local = round(score - p, 1)

    score_terr = score_territorial_ponderado(agg)

    # drivers (factores de riesgo) — normalizados a 0-100 para barras
    drivers = [
        {"nombre": "Presión Turística", "valor": round(float(row["peso_turistico"]) * 100, 0)},
        {"nombre": "Gestión de Residuos", "valor": round(min(float(row["residuos_ton"]) / 1500, 100), 0)},
        {"nombre": "Vulnerabilidad Social", "valor": round(float(row["pobreza"]), 0)},
        {"nombre": "Desigualdad (Gini)", "valor": round(float(row["gini"]) * 100, 0)},
    ]

    # alertas reales de la zona (del dataset, mes más reciente del año)
    sub = DF[(DF["zona"] == nombre) & (DF["anio"] == anio)].sort_values("mes")
    ult = sub.iloc[-1] if not sub.empty else None
    alertas = {}
    if ult is not None:
        alertas = {
            "residuos": ult["alerta_residuos"],
            "presion": ult["alerta_presion"],
            "sanitaria": ult["alerta_sanitaria"],
        }

    return {
        "zona": nombre,
        "anio": anio,
        "score_local": round(score, 1),
        "nivel": nivel_por_score(score),
        "tendencia_local": tendencia_local,
        "score_territorial": round(score_terr, 1),
        "drivers": drivers,
        "alertas": alertas,
    }


@app.get("/api/evolucion/{nombre}")
def evolucion(nombre: str):
    """Serie temporal: zona seleccionada vs promedio territorial (por año)."""
    serie_zona, serie_terr, labels = [], [], []
    for a in ANIOS:
        agg = df_anio(a)
        labels.append(a)
        serie_terr.append(round(float(agg["score_pred"].mean()), 1))
        z = agg[agg["zona"] == nombre]
        serie_zona.append(round(float(z["score_pred"].iloc[0]), 1) if not z.empty else None)
    return {"labels": labels, "zona": serie_zona, "territorial": serie_terr, "nombre": nombre}


@app.get("/api/recomendaciones/{nombre}")
def _reglas_fallback(nombre: str, score: float, nivel: str):
    """Recomendaciones por reglas. Fallback si el LLM no está disponible."""
    if score >= 70:
        general = (
            f"La presión territorial en {nombre.title()} es crítica, impulsada por alta "
            "intensidad turística y acumulación de residuos. Se recomienda intervención inmediata."
        )
        acciones = [
            "Incrementar frecuencia de recolección durante fines de semana.",
            "Priorizar inspecciones ambientales en el corredor costero.",
            "Mantener vigilancia epidemiológica activa.",
        ]
    elif score >= 40:
        general = (
            f"{nombre.title()} presenta riesgo moderado con tendencia a vigilar. "
            "Se recomienda monitoreo preventivo y refuerzo de capacidad de carga."
        )
        acciones = [
            "Reforzar señalización de aforo en zonas de mayor visita.",
            "Programar limpieza preventiva antes de temporada alta.",
            "Actualizar registro de prestadores turísticos (RNT).",
        ]
    else:
        general = (
            f"{nombre.title()} se mantiene en condición estable. "
            "Se recomienda sostener las buenas prácticas actuales."
        )
        acciones = [
            "Documentar prácticas exitosas para replicar en otras zonas.",
            "Mantener monitoreo rutinario de indicadores.",
        ]
    return general, acciones


def _groq_recomendar(nombre: str, d: dict):
    """
    Genera recomendaciones de política pública con Llama (Groq).
    Arquitectura híbrida: XGBoost calcula el diagnóstico, el LLM lo traduce
    en acciones de gestión territorial.
    Devuelve None si no hay API key o la llamada falla.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    drivers = ", ".join(f"{x['nombre']}: {x['valor']}%" for x in d["drivers"])
    alertas = ", ".join(f"{k}: {v}" for k, v in d.get("alertas", {}).items())

    prompt = f"""Eres un analista de política pública en turismo sostenible, asesorando a la Alcaldía de Santa Marta (Colombia).

Diagnóstico de la zona {nombre.title()} (año {d['anio']}), calculado por un modelo XGBoost:
- Score Territorial de presión: {d['score_local']}/100 (nivel: {d['nivel']})
- Promedio del distrito: {d['score_territorial']}/100
- Tendencia vs. año anterior: {d['tendencia_local']} puntos
- Factores de riesgo: {drivers}
- Alertas activas: {alertas or 'ninguna'}

Nota: un score MAYOR indica MAYOR presión sobre el territorio (peor).

Responde ÚNICAMENTE con un JSON válido, sin texto adicional ni markdown:
{{"general": "diagnóstico estratégico en 2 frases, específico para esta zona",
  "acciones": ["acción operativa concreta 1", "acción 2", "acción 3"]}}

Las acciones deben ser medidas ejecutables por la administración municipal, no generalidades."""

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 500,
                "response_format": {"type": "json_object"},
            }).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # urllib manda un User-Agent genérico que Groq rechaza con 403.
                "User-Agent": "adn-sostenible/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        out = json.loads(data["choices"][0]["message"]["content"])
        # Groq (tier gratuito) limita a 30 peticiones/minuto. Pausamos para
        # no exceder el límite al precomputar las 31 zonas al arrancar.
        time.sleep(2.1)
        if "general" in out and "acciones" in out:
            return out["general"], list(out["acciones"])[:4]
    except urllib.error.HTTPError as e:
        # 429 = rate limit. Esperamos y reintentamos una vez.
        if e.code == 429:
            time.sleep(5)
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = json.loads(r.read())
                out = json.loads(data["choices"][0]["message"]["content"])
                time.sleep(2.1)
                if "general" in out and "acciones" in out:
                    return out["general"], list(out["acciones"])[:4]
            except Exception as e2:
                print(f"[groq] reintento falló en {nombre}: {e2}")
            return None
        # Mostrar el motivo real que devuelve la API, no solo el código.
        try:
            detalle = e.read().decode()[:300]
        except Exception:
            detalle = ""
        print(f"[groq] HTTP {e.code} en {nombre}: {detalle}")
    except Exception as e:
        print(f"[groq] fallo en {nombre}: {e}")
    return None


@app.get("/api/recomendaciones/{nombre}")
def recomendaciones(nombre: str, anio: int = 2024, usar_llm: bool = False):
    """
    Recomendaciones estratégicas de gestión territorial.

    Arquitectura híbrida:
      - XGBoost → diagnóstico cuantitativo (score, drivers, tendencia)
      - Llama 4 Scout (Groq) → traducción a acciones de política pública

    Si no hay GROQ_API_KEY o la llamada falla, cae a un sistema de reglas.
    """
    d = zona(nombre, anio)
    score, nivel = d["score_local"], d["nivel"]

    if usar_llm:
        res = _groq_recomendar(nombre, d)
        if res:
            general, acciones = res
            return {"zona": nombre, "nivel": nivel, "general": general,
                    "acciones": acciones, "fuente": "llama-4-scout-17b (Groq)"}

    general, acciones = _reglas_fallback(nombre, score, nivel)
    return {"zona": nombre, "nivel": nivel, "general": general,
            "acciones": acciones, "fuente": "reglas"}

