# Fuentes de Datos

El sistema integra **9 fuentes de datos oficiales**, de las cuales varias provienen
directamente del **Portal de Datos Abiertos del Estado colombiano** (datos.gov.co).

---

## Conjuntos provenientes de datos.gov.co

| Variable(s) | Conjunto de datos | Entidad |
|---|---|---|
| `rnt_prestadores` | Registro Nacional de Turismo — prestadores turísticos registrados | MinCIT |
| `rnt_camas` | Registro Nacional de Turismo — capacidad de alojamiento (camas) | MinCIT |
| `rnt_habitaciones` | Registro Nacional de Turismo — capacidad de alojamiento (habitaciones) | MinCIT |
| `pasajeros_mun` | Estadísticas operacionales de transporte aéreo — pasajeros movilizados | Aeronáutica Civil |
| `extranjeros_mun` | Flujo de visitantes extranjeros no residentes | Migración Colombia |

> **Nota para el evaluador:** las URLs específicas de cada conjunto en datos.gov.co se
> listan en la sección *Enlaces directos* al final de este documento.

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

## Enlaces directos

> ⚠️ **Pendiente de completar antes de la sustentación.**
> Insertar aquí las URLs exactas de cada conjunto en datos.gov.co, de modo que el jurado
> pueda verificar y descargar las fuentes originales.

| Conjunto | URL |
|---|---|
| RNT — prestadores turísticos | `https://www.datos.gov.co/...` |
| RNT — capacidad de alojamiento | `https://www.datos.gov.co/...` |
| Aeronáutica Civil — pasajeros | `https://www.datos.gov.co/...` |
| Migración Colombia — visitantes extranjeros | `https://www.datos.gov.co/...` |

---

## Licencias y uso

Todos los conjuntos utilizados son de **acceso público y libre reutilización**, conforme a
la Ley 1712 de 2014 de Transparencia y Acceso a la Información Pública.

Los datos no contienen información personal identificable: todos los indicadores son
**agregados territoriales**, por lo que no se requirieron procesos de anonimización.
