# Diccionario de Datos

Dataset consolidado: **3348 filas × 27 columnas**
Cobertura: 31 zonas × 9 años (2016–2024) × 12 meses

**Variables de entrada al modelo:** 16 (marcadas con ✅)
**Target:** `score_pca`

---

## Variables

| Variable | Dimensión | Descripción | Rango | Fuente | En modelo | Importancia |
|---|---|---|---|---|---|---|
| `zona` | Identificador | Nombre oficial de la zona (DANE-MGN) | — | — |  |  |
| `anio` | Temporal | Año de referencia | 2016–2024 | — |  |  |
| `mes` | Temporal | Mes de referencia | 1–12 | Aeronáutica/Migración | ✅ | 0.0% |
| `pasajeros_mun` | Turística | Pasajeros aéreos movilizados (mes) | — | [Aeronáutica Civil](https://www.datos.gov.co/Transporte/Transporte-A-reo-Comercial-Tr-fico-Origen-Destino-/gb6w-ynu4/about_data) | ✅ | 11.0% |
| `extranjeros_mun` | Turística | Visitantes extranjeros no residentes (mes) | — | [Migración Colombia](https://www.datos.gov.co/Estad-sticas-Nacionales/Entradas-de-extranjeros-a-Colombia/96sh-4v8d/about_data) | ✅ | 2.1% |
| `dengue_ctx` | Salud | Casos de dengue notificados | — | SIVIGILA — INS | ✅ | 1.4% |
| `residuos_ton` | Ambiental | Residuos sólidos generados (toneladas) | — | SUI — Superservicios | ✅ | 3.2% |
| `gini` | Socioeconómica | Coeficiente de Gini (desigualdad) | 0–1 | Terridata — DNP | ✅ | 0.7% |
| `pobreza` | Socioeconómica | Índice de pobreza multidimensional | % | Terridata — DNP | ✅ | 0.1% |
| `ingreso` | Socioeconómica | Ingreso per cápita | — | Terridata — DNP | ✅ | 0.6% |
| `oni_ctx` | Climática | Índice Oceánico Niño (ENSO) | — | NOAA | ✅ | 0.1% |
| `rnt_prestadores` | Turística | Prestadores turísticos registrados (año) | — | [RNT — MinCIT](https://www.datos.gov.co/Comercio-Industria-y-Turismo/Registro-Nacional-de-Turismo-RNT/thwd-ivmp/about_data) | ✅ | 18.5% |
| `rnt_camas` | Turística | Camas de alojamiento registradas (año) | — | [RNT — MinCIT](https://www.datos.gov.co/Comercio-Industria-y-Turismo/Registro-Nacional-de-Turismo-RNT/thwd-ivmp/about_data) | ✅ | 17.6% |
| `rnt_habitaciones` | Turística | Habitaciones de alojamiento registradas (año) | — | [RNT — MinCIT](https://www.datos.gov.co/Comercio-Industria-y-Turismo/Registro-Nacional-de-Turismo-RNT/thwd-ivmp/about_data) | ✅ | 6.5% |
| `peso_turistico` | Modulador | ⚠️ Intensidad turística relativa de la zona — SUPUESTO DE DISEÑO | 0.08–1.0 | Estimación propia | ✅ | 30.3% |
| `nivel_turistico` | Categórica | Clasificación de intensidad turística | — | Derivada |  |  |
| `score_pca` | 🎯 TARGET | Score Territorial de presión (mayor = peor) | 0–100 | PCA |  |  |
| `residuos_zona` | Ambiental | Residuos atribuidos a la zona | — | Derivada |  |  |
| `ocupacion_proxy` | Derivada | Presión de la demanda sobre la planta hotelera | ≥0 | Calculada | ✅ | 7.7% |
| `estacionalidad` | Derivada | Índice del mes vs. promedio anual (>1 = temporada alta) | ≥0 | Calculada | ✅ | 0.2% |
| `residuos_per_turista` | Derivada | Huella de residuos por unidad de flujo (log1p) | ≥0 | Calculada | ✅ | 0.1% |

---

## Variables de alerta

Umbrales parametrizados en [`../models/config_alertas.json`](../models/config_alertas.json).

| Alerta | Estado | Base |
|---|---|---|
| `alerta_residuos` | ✅ Real | Percentiles sobre `residuos_ton × peso_turistico` |
| `alerta_presion` | ✅ Real | Percentiles sobre `score_pca` |
| `alerta_sanitaria` | ✅ Real | `dengue_ctx` + `oni_ctx` |
| `alerta_hidrica` | ⚠️ Simulada | Sin estación IDEAM de agua en Santa Marta |
| `alerta_servicios` | ⚠️ Simulada | Sin dato de saturación de servicios públicos |
| `alerta_gentrificacion` | ⚠️ Simulada | Sin dato de arriendos / presión habitacional |

---

## Notas de interpretación

### El Score Territorial se lee al revés de lo intuitivo
Un score **mayor** indica **mayor presión** sobre el territorio, es decir, **peor situación**.
Umbrales: `<40` Estable · `40–70` Riesgo Alto · `≥70` Crítico.

### ⚠️ `peso_turistico` es la variable crítica del modelo
Con **30.3%** de importancia, es la más influyente — y es un
**supuesto de diseño del equipo**, no un dato oficial. Ver
[`conclusiones.md`](conclusiones.md), sección 2.1.

### Granularidad heterogénea
Las variables del RNT y las socioeconómicas son **anuales** y se replican en los 12 meses del
año. Las turísticas y de salud son **mensuales**.

### Calidad
Sin valores nulos ni infinitos (0 nulos verificados).
