/*
 * app.js — NER Sentinel dashboard logic.
 * Talks to the FastAPI backend (same origin, /api/*) which wraps the trained
 * Random Forest model. See backend/app.py for the endpoints consumed here.
 */

const RISK_COLORS = { Low: "#1e8a5b", Moderate: "#c99a1e", High: "#d97b26", Severe: "#c0392b" };
const RISK_RADIUS = { Low: 7, Moderate: 9, High: 11, Severe: 13 };

let map, markerLayer;
let latestZones = [];

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initMap();
  initLangSwitch();
  initPredictForm();
  initReportModal();
  refreshAll();
  setInterval(refreshAll, 45_000); // periodic re-sync, like a real ops dashboard
  initOfflineHandling();
});

function initClock() {
  const el = document.getElementById("clock");
  const tick = () => (el.textContent = new Date().toLocaleTimeString("en-GB"));
  tick();
  setInterval(tick, 1000);
}

function initLangSwitch() {
  const sel = document.getElementById("langSelect");
  sel.addEventListener("change", () => applyI18n(sel.value));
}

// ---------------------------------------------------------------------------
// Map
// ---------------------------------------------------------------------------
function initMap() {
  map = L.map("map", { zoomControl: true, attributionControl: true }).setView([25.7, 92.8], 6);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
}

function renderZones(zones) {
  markerLayer.clearLayers();
  zones.forEach((z) => {
    const marker = L.circleMarker([z.lat, z.lon], {
      radius: RISK_RADIUS[z.risk_tier] || 8,
      color: "#ffffff",
      weight: 2,
      fillColor: RISK_COLORS[z.risk_tier] || "#888",
      fillOpacity: 0.85,
      className: "risk-marker",
    });
    marker.bindPopup(
      `<div class="popup-title">${z.name}</div>` +
        `<div class="popup-row">${z.state}</div>` +
        `<div class="popup-row">Risk: <strong>${z.risk_tier}</strong> (${(z.risk_probability * 100).toFixed(1)}%)</div>` +
        `<div class="popup-row">Slope ${z.slope_deg}\u00b0 \u00b7 ${z.elevation_m}m elevation</div>` +
        `<div class="popup-row">48h rain forecast: ${z.forecast_precip_mm_48h}mm</div>`
    );
    marker.addTo(markerLayer);
  });
}

// ---------------------------------------------------------------------------
// Data refresh
// ---------------------------------------------------------------------------
async function refreshAll() {
  document.getElementById("lastSync").textContent = t("syncing");
  try {
    const [zones, alerts, forecast, roads, summary, reports] = await Promise.all([
      fetchJSON("/api/risk-zones"),
      fetchJSON("/api/alerts"),
      fetchJSON("/api/weather"),
      fetchJSON("/api/roads"),
      fetchJSON("/api/summary"),
      fetchJSON("/api/reports"),
    ]);

    latestZones = zones.features.map((f) => f.properties);
    renderZones(latestZones);
    renderAlerts(alerts);
    renderForecast(forecast);
    renderRoads(roads);
    renderPriority(latestZones);
    renderSummary(summary);
    renderReports(reports);

    document.getElementById("lastSync").textContent =
      new Date().toLocaleTimeString("en-GB") + " sync";
  } catch (err) {
    console.error("Refresh failed", err);
    document.getElementById("lastSync").textContent = "sync failed \u2014 retrying";
  }
}

async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Renderers
// ---------------------------------------------------------------------------
function renderAlerts(alerts) {
  const el = document.getElementById("alertsList");
  if (!alerts.length) {
    el.innerHTML = `<div class="empty-state">No High/Severe zones right now \u2014 all clear.</div>`;
    return;
  }
  el.innerHTML = alerts
    .map(
      (a) => `
    <div class="alert-item">
      <span class="alert-sev" style="background:${RISK_COLORS[a.severity]}"></span>
      <div class="alert-body">
        <div class="alert-loc">${a.location}, ${a.state} <span class="tier-badge tier-${a.severity}">${a.severity}</span></div>
        <div class="alert-msg">${a.message}</div>
        <span class="alert-time">${timeAgo(a.issued_at)} \u00b7 ${a.channels.join(" / ")}</span>
      </div>
    </div>`
    )
    .join("");
}

function renderForecast(forecast) {
  const el = document.getElementById("forecastList");
  const sorted = [...forecast].sort((a, b) => b.forecast_precip_mm_48h - a.forecast_precip_mm_48h);
  el.innerHTML = sorted
    .map(
      (f) => `
    <div class="forecast-item">
      <div>
        <div class="forecast-name">${f.name}</div>
        <div class="forecast-meta">${f.outlook}</div>
      </div>
      <div class="forecast-mm">${f.forecast_precip_mm_48h}mm</div>
    </div>`
    )
    .join("");
}

function renderRoads(roads) {
  const el = document.getElementById("roadsList");
  el.innerHTML = roads
    .map(
      (r) => `
    <div class="road-item">
      <div class="road-top">
        <span class="road-label">${r.label}</span>
        <span class="road-highway">${r.highway}</span>
      </div>
      <div class="road-status">${r.status}</div>
    </div>`
    )
    .join("");
}

function renderPriority(zones) {
  // Simple response-prioritisation proxy: risk probability weighted by a
  // rough population-exposure factor (state capitals & larger towns weighted higher).
  const POP_WEIGHT = {
    Shillong: 1.4, Guwahati: 1.6, Kohima: 1.3, Dimapur: 1.4, Aizawl: 1.4,
    Imphal: 1.5, Agartala: 1.5, Itanagar: 1.2, Gangtok: 1.3,
  };
  const ranked = [...zones]
    .map((z) => {
      const weightKey = Object.keys(POP_WEIGHT).find((k) => z.name.startsWith(k));
      const weight = weightKey ? POP_WEIGHT[weightKey] : 1.0;
      return { ...z, exposure_score: z.risk_probability * weight };
    })
    .sort((a, b) => b.exposure_score - a.exposure_score)
    .slice(0, 8);

  const el = document.getElementById("priorityList");
  el.innerHTML = ranked
    .map(
      (z) => `
    <div class="priority-item">
      <div class="road-top">
        <span class="road-label">${z.name}, ${z.state}</span>
        <span class="tier-badge tier-${z.risk_tier}">${z.risk_tier}</span>
      </div>
      <div class="priority-action">${priorityAction(z)}</div>
    </div>`
    )
    .join("");
}

function priorityAction(z) {
  if (z.risk_tier === "Severe") return "Dispatch response team now \u00b7 pre-position evacuation transport";
  if (z.risk_tier === "High") return "Alert district control room \u00b7 stage equipment nearby";
  if (z.risk_tier === "Moderate") return "Increase monitoring frequency";
  return "Routine monitoring";
}

function renderSummary(s) {
  document.getElementById("kpiZones").textContent = s.zones_monitored;
  document.getElementById("kpiAlerts").textContent = s.active_alerts;
  document.getElementById("kpiBlocked").textContent = s.roads_blocked;
  document.getElementById("kpiRestricted").textContent = s.roads_at_risk;
  document.getElementById("kpiReports").textContent = s.reports_received;
}

function renderReports(reports) {
  const el = document.getElementById("reportsList");
  if (!reports.length) {
    el.innerHTML = `<div class="empty-state">No field reports yet.</div>`;
    return;
  }
  el.innerHTML = reports
    .map(
      (r) => `
    <div class="report-item">
      <div>
        <div class="report-cat">${r.category}</div>
        <div class="report-meta">${r.lat.toFixed(3)}, ${r.lon.toFixed(3)} \u00b7 ${r.reporter_name}</div>
      </div>
      <div class="report-meta">${timeAgo(r.submitted_at)}</div>
    </div>`
    )
    .join("");
}

function timeAgo(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.max(0, Math.round(diffMs / 60000));
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  return `${hrs}h ago`;
}

// ---------------------------------------------------------------------------
// Predict "what-if" panel
// ---------------------------------------------------------------------------
function initPredictForm() {
  const bind = (id, out, fmt) => {
    const input = document.getElementById(id);
    const outEl = out ? document.getElementById(out) : null;
    const update = () => outEl && (outEl.textContent = fmt ? fmt(input.value) : input.value);
    input.addEventListener("input", update);
    update();
  };
  bind("f_slope", "o_slope");
  bind("f_elev", "o_elev");
  bind("f_precip48", "o_precip48");
  bind("f_histprecip", "o_histprecip");
  bind("f_ndvi", "o_ndvi", (v) => (v / 100).toFixed(2));

  document.getElementById("predictForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      slope_deg: Number(document.getElementById("f_slope").value),
      elevation_m: Number(document.getElementById("f_elev").value),
      forecast_precip_mm_48h: Number(document.getElementById("f_precip48").value),
      historical_precip_mm: Number(document.getElementById("f_histprecip").value),
      eq_count_30d: Number(document.getElementById("f_eqcount").value),
      eq_max_mag_30d: Number(document.getElementById("f_eqmag").value),
      soil_hydrologic_group: document.getElementById("f_soil").value,
      ndvi: Number(document.getElementById("f_ndvi").value) / 100,
      distance_to_fault_km: Number(document.getElementById("f_fault").value),
    };
    try {
      const result = await fetchJSON("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const box = document.getElementById("predictResult");
      box.hidden = false;
      document.getElementById("predictTier").textContent = result.risk_tier;
      document.getElementById("predictTier").style.color = RISK_COLORS[result.risk_tier];
      document.getElementById("predictProb").textContent =
        (result.risk_probability * 100).toFixed(1) + "% probability";
    } catch (err) {
      console.error(err);
      alert("Could not reach the prediction model. Check the backend is running.");
    }
  });
}

// ---------------------------------------------------------------------------
// Citizen report modal + offline queue
// ---------------------------------------------------------------------------
const OFFLINE_QUEUE_KEY = "ner_sentinel_offline_reports";

function initReportModal() {
  const modal = document.getElementById("reportModal");
  document.getElementById("reportFab").addEventListener("click", () => {
    modal.showModal();
    renderQueuedNote();
  });
  document.getElementById("closeModal").addEventListener("click", () => modal.close());

  document.getElementById("useLocationBtn").addEventListener("click", () => {
    if (!navigator.geolocation) return alert("Geolocation isn't available on this device.");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        document.getElementById("r_lat").value = pos.coords.latitude.toFixed(5);
        document.getElementById("r_lon").value = pos.coords.longitude.toFixed(5);
      },
      () => alert("Couldn't get your location \u2014 enter it manually.")
    );
  });

  document.getElementById("reportForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = new FormData();
    form.append("lat", document.getElementById("r_lat").value);
    form.append("lon", document.getElementById("r_lon").value);
    form.append("category", document.getElementById("r_category").value);
    form.append("description", document.getElementById("r_desc").value);
    form.append("reporter_name", document.getElementById("r_name").value || "Anonymous");
    const photoInput = document.getElementById("r_photo");
    if (photoInput.files[0]) form.append("photo", photoInput.files[0]);

    if (!navigator.onLine) {
      queueOfflineReport(form);
      alert("Saved offline \u2014 it'll be sent automatically once you're back online.");
      document.getElementById("reportForm").reset();
      return;
    }

    try {
      await fetch("/api/reports", { method: "POST", body: form });
      document.getElementById("reportForm").reset();
      const reports = await fetchJSON("/api/reports");
      renderReports(reports);
      const summary = await fetchJSON("/api/summary");
      renderSummary(summary);
    } catch (err) {
      queueOfflineReport(form);
      alert("Network issue \u2014 report saved locally and will retry automatically.");
    }
  });
}

function queueOfflineReport(formData) {
  // FormData (with a File) can't be JSON-stringified directly; store the
  // plain fields, and skip the photo for the queued copy (kept in the input
  // until resubmitted manually in this demo — a production PWA would use
  // IndexedDB to persist the file blob too).
  const plain = {};
  for (const [k, v] of formData.entries()) {
    if (!(v instanceof File)) plain[k] = v;
  }
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || "[]");
  queue.push(plain);
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  updateOfflineQueueBadge();
}

function updateOfflineQueueBadge() {
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || "[]");
  const el = document.getElementById("offlineQueueCount");
  el.textContent = queue.length ? `${queue.length} report(s) queued` : "";
}

function renderQueuedNote() {
  updateOfflineQueueBadge();
}

async function trySyncOfflineQueue() {
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || "[]");
  if (!queue.length) return;
  const remaining = [];
  for (const plain of queue) {
    try {
      const form = new FormData();
      Object.entries(plain).forEach(([k, v]) => form.append(k, v));
      await fetch("/api/reports", { method: "POST", body: form });
    } catch {
      remaining.push(plain);
    }
  }
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
  updateOfflineQueueBadge();
  if (remaining.length === 0) refreshAll();
}

function initOfflineHandling() {
  const banner = document.getElementById("offlineBanner");
  const setState = () => {
    const offline = !navigator.onLine;
    banner.hidden = !offline;
    updateOfflineQueueBadge();
    if (!offline) trySyncOfflineQueue();
  };
  window.addEventListener("online", setState);
  window.addEventListener("offline", setState);
  setState();
}
