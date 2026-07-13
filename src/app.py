"""
Entrypoint para Hugging Face — Gradio SDK (compatible con ZeroGPU gratis).

El dashboard completo (HTML + CSS + Leaflet + Chart.js) se sirve dentro de un
gr.HTML a pantalla completa. Los datos se precomputan al arrancar con el modelo
XGBoost (inferencia real) y se inyectan como window.DATA, de modo que el mapa
interactivo y el selector de años funcionan sin backend por request.
"""

import json
from pathlib import Path

import gradio as gr

from precompute import build_bundle

BASE = Path(__file__).parent
STATIC = BASE / "static"

# ZeroGPU exige al menos una función @spaces.GPU registrada.
try:
    import spaces

    @spaces.GPU
    def _warmup():
        return "ok"
except Exception:
    pass

# --- Precomputar datos (inferencia XGBoost en vivo, una vez al arrancar) ---
BUNDLE = build_bundle()

# --- Ensamblar el dashboard como un único documento HTML ---
html = (STATIC / "index.html").read_text(encoding="utf-8")
css = (STATIC / "styles.css").read_text(encoding="utf-8")
js = (STATIC / "app.js").read_text(encoding="utf-8")

# Quitamos los <link>/<script src> locales y embebemos CSS+JS+datos inline.
# Inyectamos el bundle antes del JS del dashboard.
inline = f"""
<style>{css}</style>
<script>window.DATA = {json.dumps(BUNDLE, ensure_ascii=False)};</script>
"""

# Reemplazos: el <link styles.css> por el <style>, y el <script app.js> por inline.
html = html.replace('<link rel="stylesheet" href="styles.css"/>', inline)
html = html.replace('<script src="app.js"></script>', f"<script>{js}</script>")

# Gradio sanitiza HTML complejo dentro de gr.HTML. Para renderizar el documento
# completo (con Leaflet, Chart.js y scripts) sin recortes, lo incrustamos en un
# iframe aislado via srcdoc.
iframe = (
    '<iframe srcdoc="'
    + html.replace("&", "&amp;").replace('"', "&quot;")
    + '" style="width:100vw;height:100vh;border:none;display:block;"></iframe>'
)

FULL_CSS = """
footer{display:none!important}
gradio-app{margin:0!important;padding:0!important;width:100vw!important}
.gradio-container{max-width:100vw!important;width:100vw!important;padding:0!important;margin:0!important}
.gradio-container>*{padding:0!important;margin:0!important;gap:0!important;width:100%!important}
.app,.main,.wrap,.contain,.block,.form,.html-container{padding:0!important;margin:0!important;border:none!important;gap:0!important;box-shadow:none!important;background:transparent!important;width:100%!important;max-width:100vw!important}
body,html{margin:0!important;padding:0!important;overflow:hidden!important;background:#eef1f6!important}
"""

with gr.Blocks(css=FULL_CSS) as demo:
    gr.HTML(iframe)

if __name__ == "__main__":
    demo.launch()
