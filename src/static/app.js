// ---------------------------------------------------------------------------
// ADN Sostenible — frontend. Lee datos precomputados de window.DATA
// (inferencia XGBoost calculada al arrancar el Space).
// ---------------------------------------------------------------------------
const DATA = window.DATA;        // bundle inyectado por Gradio
let map, geoLayer, evoChart, zoneMarkers, mapFitted = false;
let currentYear = null;
let selectedZona = null;

const COLORS = { "Crítico":"#ff4d4d", "Riesgo Alto":"#f5a623", "Estable":"#22a06b", "Sin dato":"#c8cfda" };

const $ = id => document.getElementById(id);

// ---- login gate -----------------------------------------------------------
let dashboardStarted = false;
const loginEl = document.getElementById("login");

document.getElementById("loginBtn").addEventListener("click", () => {
  // fade suave: primero difumina, luego oculta y arranca el dashboard
  loginEl.classList.add("fading");
  setTimeout(() => {
    loginEl.classList.add("hidden");
    if (!dashboardStarted) { dashboardStarted = true; init(); }
  }, 500);  // coincide con la transición CSS
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  loginEl.classList.remove("hidden");
  // pequeño respiro para que el display:none se revierta antes de animar opacidad
  requestAnimationFrame(() => loginEl.classList.remove("fading"));
});

// ---- init -----------------------------------------------------------------
function init(){
  const meta = DATA.meta;

  // ops meta
  $("opsMeta").innerHTML = `
    <li><b>${meta.n_variables}</b> Variables</li>
    <li><b>${meta.n_fuentes}</b> Fuentes oficiales</li>
    <li><b>${meta.n_zonas}</b> Territorios</li>
    <li>${meta.rango_anios}</li>`;
  $("modelBadge").textContent = `${meta.modelo} · R² ${meta.r2}`;

  // year selector
  const sel = $("yearSelect");
  meta.anios.forEach(a => {
    const o = document.createElement("option"); o.value = a; o.textContent = a; sel.appendChild(o);
  });
  currentYear = meta.anios[meta.anios.length - 1];
  sel.value = currentYear;
  sel.addEventListener("change", e => { currentYear = +e.target.value; refresh(); });

  // map base — el encuadre se ajusta luego a todas las zonas (ver refresh)
  map = L.map("map", { zoomControl:true, scrollWheelZoom:true }).setView([11.207, -74.188], 11);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    { attribution:"© OpenStreetMap · © CARTO", maxZoom:18 }).addTo(map);

  // reference points
  meta.puntos_referencia.forEach(p => {
    L.circleMarker([p.lat, p.lng], { radius:4, color:"#1a2233", fillColor:"#1a2233", fillOpacity:1, weight:0 })
      .addTo(map).bindTooltip(p.nombre, { permanent:false, direction:"top" });
  });

  refresh();
}

// ---- refresh on year change -----------------------------------------------
function refresh(){
  loadKpis();
  loadMap();
  if (selectedZona) selectZona(selectedZona);  // re-cargar detalle con nuevo año
}

function loadKpis(){
  const k = DATA.years[currentYear].kpis;

  // --- Score Territorial: icono + color de tarjeta segun nivel de riesgo ---
  // Semantica: MAYOR score = MAYOR presion sobre el territorio = PEOR.
  const ICONS = { "Estable":"✓", "Riesgo Alto":"⚠", "Crítico":"⛔" };
  $("kpiScore").textContent = k.score_territorial;
  $("kpiScoreIcon").textContent = ICONS[k.nivel] || "";
  $("kpiScoreIcon").style.color = COLORS[k.nivel] || "var(--muted)";
  $("kpiScoreFoot").textContent = k.nivel;
  $("kpiScoreFoot").style.color = COLORS[k.nivel] || "var(--muted)";
  // color de fondo/borde de la tarjeta segun nivel
  const card = $("kpiScoreCard");
  card.classList.remove("lvl-estable","lvl-riesgo","lvl-critico");
  if (k.nivel === "Estable")      card.classList.add("lvl-estable");
  else if (k.nivel === "Riesgo Alto") card.classList.add("lvl-riesgo");
  else if (k.nivel === "Crítico") card.classList.add("lvl-critico");

  $("kpiZonas").textContent = k.zonas_prioritarias;
  $("kpiAlertas").textContent = k.alertas_activas;

  // --- Tendencia: flecha + texto explicito de si mejora o empeora ---
  // Score sube => presion sube => EMPEORA (rojo, flecha arriba).
  const t = k.tendencia;
  const tCard = $("kpiTendCard");
  tCard.classList.remove("lvl-estable","lvl-riesgo","lvl-critico");
  if (t == null){
    $("kpiTend").textContent = "—";
    $("kpiTendArrow").textContent = "";
    $("kpiTendFoot").textContent = "sin año previo";
    $("kpiTendFoot").style.color = "var(--muted)";
  } else if (t > 0.05){
    $("kpiTend").textContent = "+" + t + " pts";
    $("kpiTendArrow").textContent = "▲";
    $("kpiTendArrow").style.color = COLORS["Crítico"];
    $("kpiTendFoot").textContent = "Empeora · más presión que el año anterior";
    $("kpiTendFoot").style.color = COLORS["Crítico"];
    tCard.classList.add("lvl-critico");
  } else if (t < -0.05){
    $("kpiTend").textContent = t + " pts";
    $("kpiTendArrow").textContent = "▼";
    $("kpiTendArrow").style.color = COLORS["Estable"];
    $("kpiTendFoot").textContent = "Mejora · menos presión que el año anterior";
    $("kpiTendFoot").style.color = COLORS["Estable"];
    tCard.classList.add("lvl-estable");
  } else {
    $("kpiTend").textContent = (t>0?"+":"") + t + " pts";
    $("kpiTendArrow").textContent = "＝";
    $("kpiTendArrow").style.color = "var(--muted)";
    $("kpiTendFoot").textContent = "Sin cambio relevante";
    $("kpiTendFoot").style.color = "var(--muted)";
  }
}

// Centroide aproximado de una geometria (para ubicar el marcador de zona)
function centroide(geom){
  const pts = [];
  (function walk(c){
    if (typeof c[0] === "number") pts.push(c);
    else c.forEach(walk);
  })(geom.coordinates);
  const lng = pts.reduce((s,p)=>s+p[0],0)/pts.length;
  const lat = pts.reduce((s,p)=>s+p[1],0)/pts.length;
  return [lat, lng];
}

function loadMap(){
  const gj = DATA.years[currentYear].mapa;
  if (geoLayer) geoLayer.remove();
  if (zoneMarkers) zoneMarkers.remove();

  geoLayer = L.geoJSON(gj, {
    style: f => ({
      color:"#ffffff", weight:1, fillOpacity:.72,
      fillColor: COLORS[f.properties.nivel] || "#c8cfda"
    }),
    onEachFeature: (f, layer) => {
      const p = f.properties;
      layer.bindTooltip(
        `<div class="zone-tip">${titleCase(p.zona)}</div>score: ${p.score ?? "—"}`,
        { sticky:true });
      layer.on({
        mouseover: e => e.target.setStyle({ weight:2.5, color:"#1a2233" }),
        mouseout:  e => geoLayer.resetStyle(e.target),
        click:     () => selectZona(p.zona)
      });
    }
  }).addTo(map);

  // Marcadores por zona: muchas de las 31 son corregimientos diminutos y no se
  // ven como poligono. El marcador los hace visibles y clickeables siempre.
  zoneMarkers = L.layerGroup();
  gj.features.forEach(f => {
    const p = f.properties;
    if (p.score == null) return;
    const c = centroide(f.geometry);
    L.circleMarker(c, {
      radius: 7,
      color: "#ffffff",
      weight: 2,
      fillColor: COLORS[p.nivel] || "#c8cfda",
      fillOpacity: 1
    })
    .bindTooltip(`<div class="zone-tip">${titleCase(p.zona)}</div>score: ${p.score}`, { sticky:true })
    .on("click", () => selectZona(p.zona))
    .addTo(zoneMarkers);
  });
  zoneMarkers.addTo(map);

  // Encuadre inicial: que entren las 31 zonas (las rurales llegan lejos al este)
  if (!mapFitted){
    map.fitBounds(geoLayer.getBounds(), { padding:[20,20] });
    mapFitted = true;
  }
}

// ---- zone selection --------------------------------------------------------
function selectZona(nombre){
  selectedZona = nombre;
  const zonaData = DATA.zonas[currentYear][nombre];
  if (!zonaData) return;  // zona sin datos ese año
  const d = zonaData.detalle;
  const reco = zonaData.reco;
  const evo = DATA.evolucion[nombre];

  // decision panel
  $("decEmpty").classList.add("hidden");
  $("decBody").classList.remove("hidden");
  $("decZona").textContent = titleCase(d.zona);
  $("decZona").style.color = COLORS[d.nivel] || "var(--ink)";
  $("decScore").textContent = d.score_local;
  $("decNivel").textContent = d.nivel;
  $("decNivel").style.color = COLORS[d.nivel] || "var(--muted)";
  $("decTend").textContent = d.tendencia_local==null ? "—" : (d.tendencia_local>0?"+":"") + d.tendencia_local + " pts";
  $("decReco").textContent = reco.general;

  // drivers — color semaforico: >60% rojo, 30-60% amarillo, <30% verde
  // (son factores de RIESGO: a mayor %, peor)
  const barColor = v => v >= 60 ? COLORS["Crítico"]
                     : v >= 30 ? COLORS["Riesgo Alto"]
                     : COLORS["Estable"];
  $("drivers").innerHTML = d.drivers.map(dr => `
    <div class="driver">
      <div class="driver-top"><span>${dr.nombre}</span><span style="color:${barColor(dr.valor)};font-weight:700">${dr.valor}%</span></div>
      <div class="bar"><i style="width:${Math.min(dr.valor,100)}%;background:${barColor(dr.valor)}"></i></div>
    </div>`).join("");

  // acciones
  $("acciones").innerHTML = reco.acciones.map(a => `<li>${a}</li>`).join("");

  // evolution chart
  drawEvo(evo);
}

function drawEvo(evo){
  const ctx = $("evoChart");
  if (evoChart) evoChart.destroy();
  evoChart = new Chart(ctx, {
    type:"line",
    data:{ labels:evo.labels, datasets:[
      { label:titleCase(evo.nombre), data:evo.zona, borderColor:"#8b5cf6", backgroundColor:"transparent", borderWidth:2, tension:.35, pointRadius:2 },
      { label:"Territorial", data:evo.territorial, borderColor:"#22a06b", borderDash:[5,4], borderWidth:2, tension:.35, pointRadius:0 }
    ]},
    options:{
      responsive:true, plugins:{ legend:{ labels:{ boxWidth:12, font:{size:11} } } },
      scales:{ y:{ grid:{color:"#eef1f6"} }, x:{ grid:{display:false} } }
    }
  });
}

// ---- utils -----------------------------------------------------------------
function titleCase(s){
  return s.toLowerCase().replace(/(^|\s|\()\S/g, c => c.toUpperCase());
}
