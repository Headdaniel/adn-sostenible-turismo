"""
Reentrenamiento del modelo XGBoost — Score Territorial de Turismo Sostenible.

Entrena un XGBRegressor para predecir el Score Territorial (score_pca) a partir
de las variables del dataset ampliado (20 variables en total, 16 features de
entrada al modelo).

Salidas:
  - modelo_xgboost_score.pkl     (modelo entrenado)
  - modelo_xgboost_config.json   (features, hiperparámetros, métricas)
"""

import json
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

SEED = 42

# --- Datos ------------------------------------------------------------------
df = pd.read_csv("dataset.csv")

FEATURES = [
    # Turísticas
    "pasajeros_mun", "extranjeros_mun",
    "rnt_prestadores", "rnt_camas", "rnt_habitaciones",
    # Ambientales
    "residuos_ton",
    # Socioeconómicas
    "gini", "pobreza", "ingreso",
    # Contexto (salud / clima)
    "dengue_ctx", "oni_ctx",
    # Moduladores espacio-temporales
    "peso_turistico", "mes",
    # Derivadas (indicadores de gestión de destinos)
    "ocupacion_proxy", "estacionalidad", "residuos_per_turista",
]
TARGET = "score_pca"

X = df[FEATURES]
y = df[TARGET]

print(f"Dataset: {len(df)} filas | {len(FEATURES)} features")

# --- Split ------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED
)
X_tr, X_val, y_tr, y_val = train_test_split(
    X_train, y_train, test_size=0.2, random_state=SEED
)

# --- Modelo -----------------------------------------------------------------
params = {
    "n_estimators": 1000,
    "learning_rate": 0.05,
    "max_depth": 4,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.5,
    "reg_lambda": 2.0,
    "eval_metric": "rmse",
    "early_stopping_rounds": 50,
    "random_state": SEED,
}

model = XGBRegressor(**params)
model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)

# --- Evaluación -------------------------------------------------------------
pred = model.predict(X_test)
r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
rmse = float(np.sqrt(mean_squared_error(y_test, pred)))

cv = cross_val_score(
    XGBRegressor(**{k: v for k, v in params.items() if k != "early_stopping_rounds"}),
    X, y, cv=5, scoring="r2",
)

print(f"\nMétricas (test):  R²={r2:.4f}  MAE={mae:.3f}  RMSE={rmse:.3f}")
print(f"Validación cruzada (5-fold): R²={cv.mean():.4f} ± {cv.std():.4f}")

# --- Importancia de variables ----------------------------------------------
imp = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
print("\nImportancia de variables:")
for f, v in imp:
    print(f"  {v:6.3f}  {f}")

# --- Persistencia -----------------------------------------------------------
with open("modelo_xgboost_score.pkl", "wb") as f:
    pickle.dump(model, f)

config = {
    "modelo": "XGBRegressor",
    "objetivo": "predecir score_pca (Score Territorial) desde variables crudas",
    "features": FEATURES,
    "n_features": len(FEATURES),
    "target": TARGET,
    "hiperparametros": params,
    "metricas_test": {
        "R2": round(r2, 4),
        "MAE": round(mae, 3),
        "RMSE": round(rmse, 3),
        "CV_R2": f"{cv.mean():.4f} ± {cv.std():.4f}",
    },
    "importancia_variables": {f: round(float(v), 4) for f, v in imp},
    "split": "80% train / 20% test, validación 20% interna para early stopping",
}
with open("modelo_xgboost_config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("\n✓ modelo_xgboost_score.pkl y modelo_xgboost_config.json actualizados")
