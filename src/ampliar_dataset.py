"""
Amplía el dataset con 3 variables derivadas de indicadores estándar de
gestión de destinos turísticos. NO son sintéticas ni aleatorias: se calculan
a partir de las variables reales ya existentes.

  1. ocupacion_proxy      — presión de la demanda sobre la planta hotelera
  2. estacionalidad       — índice del mes frente al promedio anual de la zona
  3. residuos_per_turista — huella de residuos por unidad de flujo turístico

Salida: dataset.csv ampliado (mismas filas, 3 columnas nuevas).
"""

import numpy as np
import pandas as pd

df = pd.read_csv("dataset.csv")
print(f"Entrada: {len(df)} filas × {len(df.columns)} columnas")

# --- 1. Ocupación proxy -----------------------------------------------------
# Flujo de pasajeros ponderado por la intensidad turística de la zona, sobre
# la capacidad instalada (camas). Aproxima la presión sobre el alojamiento.
flujo_zona = df["pasajeros_mun"] * df["peso_turistico"]
df["ocupacion_proxy"] = (flujo_zona / df["rnt_camas"].replace(0, np.nan)).fillna(0).round(4)

# --- 2. Estacionalidad ------------------------------------------------------
# Índice mensual: flujo del mes / flujo promedio de la zona ese año.
# >1 = temporada alta, <1 = temporada baja.
prom = df.groupby(["zona", "anio"])["pasajeros_mun"].transform("mean")
df["estacionalidad"] = (df["pasajeros_mun"] / prom.replace(0, np.nan)).fillna(1).round(4)

# --- 3. Residuos por turista (escala log) -----------------------------------
# Toneladas de residuos atribuibles a la zona por unidad de flujo turístico.
# Mide la huella ambiental del modelo turístico local.
# El cociente crudo tiene una cola extrema en zonas rurales (flujo→0), por lo
# que se aplica log1p: es la transformación estándar para ratios sesgados y
# preserva el orden y la interpretabilidad (mayor valor = mayor huella).
rpt = ((df["residuos_ton"] * df["peso_turistico"]) / flujo_zona.replace(0, np.nan)).fillna(0)
df["residuos_per_turista"] = np.log1p(rpt).round(4)

print(f"Salida:  {len(df)} filas × {len(df.columns)} columnas")
print("\nNuevas variables (Santa Marta 2024):")
sm = df[(df.zona.str.startswith("SANTA MARTA")) & (df.anio == 2024)]
print(sm[["mes", "ocupacion_proxy", "estacionalidad", "residuos_per_turista"]].head(4).to_string(index=False))
print("\nEstadísticos:")
print(df[["ocupacion_proxy", "estacionalidad", "residuos_per_turista"]].describe().round(3).to_string())

df.to_csv("dataset.csv", index=False)
print("\n✓ dataset.csv actualizado")
