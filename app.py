from flask import Flask, jsonify, Response, request
import requests
import time

VEHICLES_URL = "https://gtfsrt.renfe.com/vehicle_positions.json"
ALERTS_URL = "https://gtfsrt.renfe.com/alerts.json"  # lo dejamos preparado (opcional)

app = Flask(__name__)

HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>RENFE Cercanías – Mapa en tiempo real</title>

  <!-- Leaflet -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

  <!-- MarkerCluster (para que sea usable con muchos puntos) -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>

  <style>
    html, body { height: 100%; margin: 0; }
    #map { height: 100%; width: 100%; }

    .panel {
      position: absolute;
      z-index: 999;
      top: 12px;
      left: 12px;
      background: white;
      padding: 10px 12px;
      border-radius: 12px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.12);
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      width: 320px;
    }
    .row { display: flex; gap: 8px; align-items: center; }
    .row + .row { margin-top: 8px; }
    .title { font-weight: 700; font-size: 14px; }
    .muted { color: #666; font-size: 12px; }
    .chip {
      font-size: 12px; padding: 4px 8px; border-radius: 999px;
      background: #f2f2f2; display: inline-block;
    }
    input, select, button {
      font-size: 13px; padding: 7px 9px; border-radius: 10px;
      border: 1px solid #ddd; outline: none;
    }
    button {
      cursor: pointer;
      background: #111; color: #fff; border: 1px solid #111;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .spacer { flex: 1; }
    .small { font-size: 12px; }
    .link { color: #0a58ca; text-decoration: none; }
  </style>
</head>
<body>
  <div id="map"></div>

  <div class="panel">
    <div class="row">
      <div>
        <div class="title">RENFE Cercanías · tiempo real</div>
        <div class="muted">Actualiza cada 30 s (sin recargar)</div>
      </div>
      <div class="spacer"></div>
      <div class="chip" id="count">—</div>
    </div>

    <div class="row">
      <select id="lineFilter" style="width: 140px;">
        <option value="">Todas</option>
      </select>

      <input id="search" placeholder="Buscar (label / tripId)" style="flex:1;" />
    </div>

    <div class="row">
      <button id="refreshBtn">Actualizar ahora</button>
      <div class="spacer"></div>
      <div class="small muted" id="lastUpdate">—</div>
    </div>
  </div>

  <!-- JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>

  <script>
    const map = L.map('map', { zoomControl: true }).setView([40.4168, -3.7038], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    const cluster = L.markerClusterGroup({ disableClusteringAtZoom: 12 });
    cluster.addTo(map);

    // marker cache para actualizar sin recrear todo
    const markers = new Map(); // key -> marker
    let lastData = [];

    const lineFilterEl = document.getElementById('lineFilter');
    const searchEl = document.getElementById('search');
    const countEl = document.getElementById('count');
    const lastUpdateEl = document.getElementById('lastUpdate');
    const refreshBtn = document.getElementById('refreshBtn');

    function lineFromLabel(label) {
      if (!label) return "";
      // Ej: "C5-23727-PLATF.(5)" -> "C5"
      const m = label.match(/^([A-Z]\\d+|C\\d+[a-z]?|R\\d+[A-Z]?)/i);
      if (!m) return "";
      return m[1].toUpperCase();
    }

    function escapeHtml(s) {
      return (s ?? "").toString()
        .replaceAll('&','&amp;').replaceAll('<','&lt;')
        .replaceAll('>','&gt;').replaceAll('"','&quot;')
        .replaceAll("'","&#039;");
    }

    function popupHtml(v) {
      const label = escapeHtml(v.label || "");
      const tripId = escapeHtml(v.tripId || "");
      const stopId = escapeHtml(v.stopId || "");
      const status = escapeHtml(v.status || "");
      const line = escapeHtml(v.line || "");

      return `
        <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; min-width:240px;">
          <div style="font-weight:700; font-size:14px;">${label || "Tren"}</div>
          <div style="color:#666; font-size:12px; margin-top:2px;">${line ? "Línea: " + line + " · " : ""}${status}</div>
          <hr style="border:none;border-top:1px solid #eee; margin:10px 0;" />
          <div style="font-size:12px;"><b>tripId:</b> ${tripId || "—"}</div>
          <div style="font-size:12px;"><b>stopId:</b> ${stopId || "—"}</div>
          <div style="font-size:12px; color:#666; margin-top:8px;">
            lat: ${v.lat.toFixed(5)} · lon: ${v.lon.toFixed(5)}
          </div>
        </div>
      `;
    }

    function applyUIFilters(data) {
      const line = lineFilterEl.value.trim();
      const q = searchEl.value.trim().toLowerCase();

      return data.filter(v => {
        const okLine = !line || (v.line === line);
        const okQ = !q || (v.label || "").toLowerCase().includes(q) || (v.tripId || "").toLowerCase().includes(q);
        return okLine && okQ;
      });
    }

    function rebuildLineFilter(data) {
      // llena el selector con líneas existentes
      const lines = Array.from(new Set(data.map(v => v.line).filter(Boolean))).sort();
      const current = lineFilterEl.value;

      // reset
      lineFilterEl.innerHTML = '<option value="">Todas</option>';
      for (const l of lines) {
        const opt = document.createElement('option');
        opt.value = l;
        opt.textContent = l;
        lineFilterEl.appendChild(opt);
      }

      // intenta mantener selección
      if (lines.includes(current)) lineFilterEl.value = current;
    }

    function render(data) {
      const filtered = applyUIFilters(data);
      countEl.textContent = `${filtered.length} trenes`;

      // marca los que hay ahora
      const seen = new Set();

      for (const v of filtered) {
        const key = v.entity_id || (v.tripId + ":" + v.label);
        seen.add(key);

        if (markers.has(key)) {
          const mk = markers.get(key);
          mk.setLatLng([v.lat, v.lon]);
          mk.setPopupContent(popupHtml(v));
        } else {
          const mk = L.circleMarker([v.lat, v.lon], { radius: 5 });
          mk.bindPopup(popupHtml(v), { maxWidth: 420 });
          markers.set(key, mk);
          cluster.addLayer(mk);
        }
      }

      // elimina los que ya no están (o que no pasan filtro)
      for (const [key, mk] of markers.entries()) {
        if (!seen.has(key)) {
          cluster.removeLayer(mk);
          markers.delete(key);
        }
      }
    }

    async function fetchVehicles() {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Actualizando…";

      try {
        const r = await fetch('/api/vehicles');
        const payload = await r.json();
        lastData = payload.vehicles || [];
        rebuildLineFilter(lastData);

        render(lastData);

        const t = new Date(payload.fetched_at * 1000);
        lastUpdateEl.textContent = t.toLocaleTimeString();
      } catch (e) {
        console.error(e);
        lastUpdateEl.textContent = "Error";
      } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Actualizar ahora";
      }
    }

    // refresco automático + eventos UI
    refreshBtn.addEventListener('click', fetchVehicles);
    lineFilterEl.addEventListener('change', () => render(lastData));
    searchEl.addEventListener('input', () => render(lastData));

    fetchVehicles();
    setInterval(fetchVehicles, 30000);
  </script>
</body>
</html>
"""

def get_json(url: str) -> dict:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.get("/api/vehicles")
def api_vehicles():
    feed = get_json(VEHICLES_URL)
    out = []
    for e in feed.get("entity", []):
        v = e.get("vehicle", {}) or {}
        pos = v.get("position", {}) or {}
        veh = v.get("vehicle", {}) or {}
        trip = v.get("trip", {}) or {}

        lat = pos.get("latitude")
        lon = pos.get("longitude")
        if lat is None or lon is None:
            continue

        label = veh.get("label") or veh.get("id") or e.get("id") or "tren"
        tripId = trip.get("tripId")
        stopId = v.get("stopId")
        status = v.get("currentStatus")

        # “línea” simple: prefijo del label (C5, R1, etc.)
        line = ""
        if isinstance(label, str) and "-" in label:
            line = label.split("-", 1)[0].upper()

        out.append({
            "entity_id": e.get("id"),
            "label": label,
            "tripId": tripId,
            "stopId": stopId,
            "status": status,
            "lat": float(lat),
            "lon": float(lon),
            "line": line
        })

    return jsonify({"fetched_at": time.time(), "vehicles": out})

# (Opcional) endpoint de alerts si luego lo quieres pintar como banner/panel
@app.get("/api/alerts")
def api_alerts():
    feed = get_json(ALERTS_URL)
    alerts = []
    for e in feed.get("entity", []):
        alert = e.get("alert", {}) or {}
        trans = (alert.get("descriptionText", {}) or {}).get("translation", []) or []
        txt = (trans[0].get("text") or "").strip() if trans else ""
        if not txt:
            continue
        alerts.append({"id": e.get("id"), "text": txt})
    return jsonify({"fetched_at": time.time(), "alerts": alerts})

if __name__ == "__main__":
    print("Arrancando servidor en http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)