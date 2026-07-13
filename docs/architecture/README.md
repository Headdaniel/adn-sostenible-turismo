# Arquitectura y Diagramas de Flujo

---

## 1. Arquitectura general del sistema

```mermaid
flowchart TB
    subgraph FUENTES["📊 Fuentes de datos abiertos"]
        A1["datos.gov.co<br/>RNT · Aeronáutica · Migración"]
        A2["SUI · Terridata<br/>SIVIGILA · NOAA"]
        A3["DANE-MGN<br/>Geometrías 31 zonas"]
    end

    subgraph PREP["⚙️ Preparación de datos"]
        B1["Consolidación<br/>clave territorial DANE"]
        B2["Modulación espacial<br/>peso_turistico"]
        B3["Ingeniería de características<br/>3 variables derivadas"]
        B4["PCA → score_pca<br/>(target)"]
    end

    subgraph IA["🧠 Capa de inteligencia"]
        C1["XGBoost<br/>Diagnóstico cuantitativo"]
        C2["Llama 4 Scout (Groq)<br/>IA generativa"]
        C3["Fallback por reglas<br/>determinista"]
    end

    subgraph APP["🖥️ Aplicación"]
        D1["FastAPI<br/>endpoints REST"]
        D2["Dashboard<br/>Leaflet + Chart.js"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> D2
    B1 --> B2 --> B3 --> B4
    B4 --> C1
    C1 -->|"score, drivers,<br/>tendencia"| C2
    C2 -->|"si falla"| C3
    C1 --> D1
    C2 --> D1
    C3 --> D1
    D1 --> D2

    style C1 fill:#2563eb,color:#fff
    style C2 fill:#8b5cf6,color:#fff
    style D2 fill:#22a06b,color:#fff
```

**Arquitectura híbrida:** el XGBoost produce el **diagnóstico cuantitativo** (qué tan
presionada está cada zona y por qué); el LLM lo traduce en **acciones de política pública**.
Son dos capas de IA con funciones distintas y complementarias.

---

## 2. Flujo de trabajo — CRISP-ML

```mermaid
flowchart LR
    F1["1️⃣ Business &<br/>Data Understanding"] --> F2["2️⃣ Data<br/>Preparation"]
    F2 --> F3["3️⃣ Modeling"]
    F3 --> F4["4️⃣ Evaluation"]
    F4 -->|"métricas OK"| F5["5️⃣ Deployment"]
    F4 -->|"ajustar"| F3
    F5 --> F6["6️⃣ Monitoring"]
    F6 -.->|"drift / nuevos datos"| F2

    style F3 fill:#2563eb,color:#fff
    style F5 fill:#22a06b,color:#fff
```

---

## 3. Flujo de inferencia (en ejecución)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant D as Dashboard
    participant A as FastAPI
    participant X as XGBoost
    participant L as Llama 4 (Groq)

    U->>D: Selecciona zona en el mapa
    D->>A: GET /api/zona/{nombre}
    A->>X: predict(16 features)
    X-->>A: score, nivel, drivers
    A-->>D: diagnóstico cuantitativo

    D->>A: GET /api/recomendaciones/{nombre}
    A->>L: prompt(diagnóstico + contexto)
    alt LLM disponible
        L-->>A: recomendaciones JSON
        A-->>D: acciones (fuente: llama-4-scout)
    else LLM no disponible
        A->>A: fallback por reglas
        A-->>D: acciones (fuente: reglas)
    end
    D-->>U: Centro de Decisión + acciones IA
```

**Nota de diseño:** el fallback determinista garantiza que el sistema **nunca falle** ante
una caída del proveedor de LLM — un requisito no negociable en una herramienta destinada al
sector público.

---

## 4. Pipeline de datos

```mermaid
flowchart LR
    R1["9 fuentes<br/>heterogéneas"] --> R2["Homologación<br/>nomenclatura DANE"]
    R2 --> R3["Join 31/31<br/>con geometrías"]
    R3 --> R4["ampliar_dataset.py<br/>+3 variables"]
    R4 --> R5["dataset.csv<br/>3.348 × 27"]
    R5 --> R6["entrenar_modelo.py"]
    R6 --> R7["modelo.pkl<br/>+ config.json"]

    style R5 fill:#f5a623,color:#fff
    style R7 fill:#2563eb,color:#fff
```

---

## 5. Componentes y responsabilidades

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Ingeniería de datos | `src/ampliar_dataset.py` | Deriva las 3 variables adicionales |
| Entrenamiento | `src/entrenar_modelo.py` | Entrena, valida y persiste el modelo |
| Inferencia + API | `src/api.py` | Carga el modelo, expone endpoints, integra Groq |
| Precómputo | `src/precompute.py` | Calcula el bundle completo al arrancar |
| Entrypoint | `src/app.py` | Sirve la aplicación (Gradio/HF Spaces) |
| Frontend | `src/static/` | Dashboard interactivo |

---

## 6. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Modelo predictivo | XGBoost 2.1 · scikit-learn |
| IA generativa | Llama 4 Scout 17B (Groq API) |
| Backend | FastAPI · Python 3.11 |
| Frontend | Leaflet · Chart.js · HTML/CSS/JS |
| Datos geoespaciales | GeoJSON (EPSG:4326) · DANE-MGN |
| Despliegue | Hugging Face Spaces (Gradio SDK) |
