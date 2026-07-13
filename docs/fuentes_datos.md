# Fuentes de Datos

El sistema integra **9 fuentes de datos oficiales**, de las cuales varias provienen
directamente del **Portal de Datos Abiertos del Estado colombiano** (datos.gov.co).

---

## Conjuntos provenientes de datos.gov.co

| Variable(s) | Conjunto de datos | Entidad |
|---|---|---|
| `rnt_prestadores`, `rnt_camas`, `rnt_habitaciones` | [Registro Nacional de Turismo (RNT)](https://www.datos.gov.co/Comercio-Industria-y-Turismo/Registro-Nacional-de-Turismo-RNT/thwd-ivmp/about_data) | MinCIT |
| `pasajeros_mun` | [Transporte Aéreo Comercial — Tráfico Origen-Destino](https://www.datos.gov.co/Transporte/Transporte-A-reo-Comercial-Tr-fico-Origen-Destino-/gb6w-ynu4/about_data) | Aeronáutica Civil |
| `extranjeros_mun` | [Entradas de extranjeros a Colombia](https://www.datos.gov.co/Estad-sticas-Nacionales/Entradas-de-extranjeros-a-Colombia/96sh-4v8d/about_data) | Migración Colombia |

Estas tres fuentes constituyen el **núcleo turístico del modelo**: las variables del RNT por
sí solas concentran el 42.6% de la importancia del XGBoost.

## Otras fuentes oficiales integradas

| Variable(s) | Fuente | Entidad | Naturaleza |
|---|---|---|---|
| `residuos_ton` | Sistema Único de Información (SUI) | Superservicios | Oficial |
| `gini`, `pobreza`, `ingreso` | Terridata | DNP | Oficial |
| `dengue_ctx` | SIVIGILA — vigilancia epidemiológica | INS | Oficial |
| `oni_ctx` | Índice Oceánico Niño (ONI) | NOAA (EE.UU.) | Oficial internacional |
| Geometrías de las 31 zonas | Marco Geoestadístico Nacional (MGN) | DANE | Oficial |

## Variable derivada de estimación propia

| Variable | Naturaleza | Estado |
|---|---|---|
| `peso_turistico` | **Supuesto de diseño del equipo** | ⚠️ Sin fuente estadística oficial |

Ver la declaración completa de esta limitación en [`conclusiones.md`](conclusiones.md).

---

## Cobertura geográfica: las 31 zonas

Las geometrías provienen del **Marco Geoestadístico Nacional (MGN) del DANE**, filtrando el
municipio con código **47001** (Santa Marta, Distrito Turístico, Cultural e Histórico).

El *join* entre el dataset y las geometrías es **exacto: 31/31 zonas**, sin discrepancias de
nomenclatura. Esto se verificó programáticamente y permite que cada indicador se represente
espacialmente sin ambigüedad.

**Sistema de referencia:** EPSG:4326 (WGS 84).

Las 31 zonas incluyen el casco urbano del Distrito y 30 corregimientos y centros poblados
rurales (Taganga, Minca, Bonda, Guachaca, Buritaca, Palomino, entre otros).

---

## Trazabilidad de la transformación

El paso de los datos crudos al dataset consolidado está documentado y es reproducible:

1. **Consolidación** — integración de las 9 fuentes con clave territorial homologada a la
   nomenclatura oficial DANE-MGN.
2. **Modulación espacial** — los indicadores disponibles solo a nivel municipal agregado se
   distribuyen entre las 31 zonas mediante `peso_turistico`.
3. **Ingeniería de características** — [`../src/ampliar_dataset.py`](../src/ampliar_dataset.py)
   genera las 3 variables derivadas.
4. **Construcción del target** — PCA sobre las variables de presión → `score_pca`.

Dataset resultante: [`../data/processed/dataset.csv`](../data/processed/dataset.csv)
(3.348 filas × 27 columnas).

---

## Enlaces directos a datos.gov.co

Conjuntos verificables y descargables desde el Portal de Datos Abiertos del Estado
colombiano:

| Variables | Conjunto de datos | Entidad | URL |
|---|---|---|---|
| `rnt_prestadores`<br/>`rnt_camas`<br/>`rnt_habitaciones` | Registro Nacional de Turismo (RNT) | MinCIT | https://www.datos.gov.co/Comercio-Industria-y-Turismo/Registro-Nacional-de-Turismo-RNT/thwd-ivmp/about_data |
| `extranjeros_mun` | Entradas de extranjeros a Colombia | Migración Colombia | https://www.datos.gov.co/Estad-sticas-Nacionales/Entradas-de-extranjeros-a-Colombia/96sh-4v8d/about_data |
| `pasajeros_mun` | Transporte Aéreo Comercial — Tráfico Origen-Destino | Aeronáutica Civil | https://www.datos.gov.co/Transporte/Transporte-A-reo-Comercial-Tr-fico-Origen-Destino-/gb6w-ynu4/about_data |

**Cumplimiento del requisito:** los términos de referencia exigen al menos un (1) conjunto
proveniente de datos.gov.co. Este proyecto integra **tres**, y son el núcleo turístico del
modelo: las variables del RNT concentran el **42.6% de la importancia** total del
XGBoost.

---

## Licencias y uso

Todos los conjuntos utilizados son de **acceso público y libre reutilización**, conforme a
la Ley 1712 de 2014 de Transparencia y Acceso a la Información Pública.

Los datos no contienen información personal identificable: todos los indicadores son
**agregados territoriales**, por lo que no se requirieron procesos de anonimización.
