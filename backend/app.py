"""
app.py
------
Backend for the NER Sentinel platform.

Wires the trained Random Forest (from the earlier `landslide_rf` project)
into a small API the dashboard consumes:

  GET  /api/risk-zones   -> GeoJSON of every monitored settlement + live risk score
  GET  /api/roads        -> connectivity status for highway segments between them
  GET  /api/alerts       -> auto-generated early-warning feed for High/Severe zones
  GET  /api/weather      -> per-location rainfall-linked forecast summary
  GET  /api/summary      -> KPI counts for the dashboard header
  POST /api/predict      -> score a single custom set of features (manual "what-if" panel)
  GET  /api/reports      -> citizen/field-officer incident reports received so far
  POST /api/reports      -> submit a new geo-tagged report (optionally with a photo)

Data note: rainfall/seismic readings are simulated (see backend/data/ner_locations.py)
because this environment has no outbound internet access to call the real IMD /
USGS / NOAA / sensor feeds the production system would use. The terrain facts
(coordinates, elevation, slope, fault distance, soil) are real. Swap
`simulate_live_readings` for real API calls — the model and every endpoint
below are already wired to accept that data unchanged.
"""

import io
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from rf_src.feature_engineering import ALL_FEATURES
from data.ner_locations import all_locations_live, ROAD_SEGMENTS

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "landslide_rf_pipeline.joblib"
FRONTEND_DIR = BASE_DIR.parent / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="NER Sentinel API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline = joblib.load(MODEL_PATH)

# --- in-memory stores (swap for a real DB in production) --------------------
REPORTS = []


def risk_tier(p):
    if p < 0.2:
        return "Low"
    elif p < 0.5:
        return "Moderate"
    elif p < 0.75:
        return "High"
    return "Severe"


def score_row(row: dict) -> float:
    X = pd.DataFrame([{k: row.get(k) for k in ALL_FEATURES}])
    return float(_pipeline.predict_proba(X)[0, 1])


def scored_locations():
    """Live locations + model risk score, cached for the process lifetime per call."""
    locs = all_locations_live()
    for loc in locs:
        proba = score_row(loc)
        loc["risk_probability"] = round(proba, 4)
        loc["risk_tier"] = risk_tier(proba)
    return locs


# ---------------------------------------------------------------------------
# GIS risk zones
# ---------------------------------------------------------------------------
@app.get("/api/risk-zones")
def risk_zones():
    locs = scored_locations()
    features = []
    for loc in locs:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [loc["lon"], loc["lat"]]},
                "properties": loc,
            }
        )
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# Road connectivity
# ---------------------------------------------------------------------------
@app.get("/api/roads")
def roads():
    locs = {loc["name"]: loc for loc in scored_locations()}
    out = []
    for highway, label, a, b in ROAD_SEGMENTS:
        ra = locs.get(a, {}).get("risk_probability", 0)
        rb = locs.get(b, {}).get("risk_probability", 0)
        worst = max(ra, rb)
        if worst >= 0.75:
            status = "Blocked / impassable"
        elif worst >= 0.5:
            status = "At risk \u2014 restricted"
        elif worst >= 0.2:
            status = "Open \u2014 monitor"
        else:
            status = "Open"
        out.append(
            {
                "highway": highway,
                "label": label,
                "from": a,
                "to": b,
                "status": status,
                "risk_probability": round(worst, 4),
            }
        )
    out.sort(key=lambda r: -r["risk_probability"])
    return out


# ---------------------------------------------------------------------------
# Alerts feed (auto-generated from High/Severe zones)
# ---------------------------------------------------------------------------
@app.get("/api/alerts")
def alerts():
    locs = [l for l in scored_locations() if l["risk_tier"] in ("High", "Severe")]
    locs.sort(key=lambda l: -l["risk_probability"])
    now = datetime.now(timezone.utc)
    out = []
    for i, loc in enumerate(locs):
        minutes_ago = i * 7 + 3
        ts = now.timestamp() - minutes_ago * 60
        out.append(
            {
                "id": f"AL-{loc['name'][:3].upper()}-{i}",
                "location": loc["name"],
                "state": loc["state"],
                "severity": loc["risk_tier"],
                "risk_probability": loc["risk_probability"],
                "message": _alert_message(loc),
                "issued_at": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "channels": ["SMS", "App push", "District control room"],
            }
        )
    return out


def _alert_message(loc):
    if loc["risk_tier"] == "Severe":
        return (
            f"Severe landslide risk near {loc['name']}, {loc['state']}. "
            f"48h rainfall forecast {loc['forecast_precip_mm_48h']}mm on {loc['slope_deg']}\u00b0 slope. "
            "Evacuate vulnerable slopes; restrict travel on adjoining roads."
        )
    return (
        f"High landslide risk building near {loc['name']}, {loc['state']}. "
        "Increase slope monitoring and prepare road diversion plans."
    )


# ---------------------------------------------------------------------------
# Weather-linked forecast summary
# ---------------------------------------------------------------------------
@app.get("/api/weather")
def weather():
    locs = scored_locations()
    out = []
    for loc in locs:
        out.append(
            {
                "name": loc["name"],
                "state": loc["state"],
                "forecast_precip_mm_48h": loc["forecast_precip_mm_48h"],
                "historical_precip_mm": loc["historical_precip_mm"],
                "risk_tier": loc["risk_tier"],
                "outlook": _outlook(loc),
            }
        )
    return out


def _outlook(loc):
    if loc["forecast_precip_mm_48h"] > 70:
        return "Heavy rain expected \u2014 saturation risk rising"
    elif loc["forecast_precip_mm_48h"] > 40:
        return "Moderate rain expected \u2014 monitor slopes"
    return "Light rain expected \u2014 stable"


# ---------------------------------------------------------------------------
# Dashboard KPI summary
# ---------------------------------------------------------------------------
@app.get("/api/summary")
def summary():
    locs = scored_locations()
    tiers = {"Low": 0, "Moderate": 0, "High": 0, "Severe": 0}
    for loc in locs:
        tiers[loc["risk_tier"]] += 1
    road_data = roads()
    blocked = sum(1 for r in road_data if r["status"] == "Blocked / impassable")
    at_risk = sum(1 for r in road_data if r["status"] == "At risk \u2014 restricted")
    return {
        "zones_monitored": len(locs),
        "risk_tiers": tiers,
        "active_alerts": len([l for l in locs if l["risk_tier"] in ("High", "Severe")]),
        "roads_blocked": blocked,
        "roads_at_risk": at_risk,
        "reports_received": len(REPORTS),
        "last_sync": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Manual "what-if" prediction panel
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    slope_deg: float = Field(..., ge=0, le=90)
    elevation_m: float = Field(..., ge=0)
    forecast_precip_mm_48h: float = Field(..., ge=0)
    historical_precip_mm: float = Field(..., ge=0)
    eq_count_30d: int = Field(0, ge=0)
    eq_max_mag_30d: float = Field(0.0, ge=0)
    soil_hydrologic_group: str = Field(..., pattern="^[ABCD]$")
    ndvi: float = Field(..., ge=-1, le=1)
    distance_to_fault_km: float = Field(..., ge=0)


@app.post("/api/predict")
def predict(req: PredictRequest):
    proba = score_row(req.model_dump())
    return {
        "risk_probability": round(proba, 4),
        "risk_tier": risk_tier(proba),
    }


# ---------------------------------------------------------------------------
# Citizen / field-officer reporting
# ---------------------------------------------------------------------------
@app.get("/api/reports")
def get_reports():
    return list(reversed(REPORTS))


@app.post("/api/reports")
async def submit_report(
    lat: float = Form(...),
    lon: float = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    reporter_name: str = Form("Anonymous"),
    photo: UploadFile = File(None),
):
    report_id = str(uuid.uuid4())[:8]
    photo_path = None
    if photo is not None and photo.filename:
        ext = Path(photo.filename).suffix or ".jpg"
        dest = UPLOAD_DIR / f"{report_id}{ext}"
        contents = await photo.read()
        dest.write_bytes(contents)
        photo_path = f"/api/uploads/{dest.name}"

    report = {
        "id": report_id,
        "lat": lat,
        "lon": lon,
        "category": category,
        "description": description,
        "reporter_name": reporter_name,
        "photo_url": photo_path,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "status": "Received \u2014 pending review",
    }
    REPORTS.append(report)
    return report


@app.get("/api/uploads/{filename}")
def get_upload(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
