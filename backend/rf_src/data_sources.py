"""
data_sources.py
----------------
Thin wrapper functions around each government API listed in config.py.
Every function degrades gracefully (returns None / empty DataFrame and logs
a warning) if the service is unreachable, rate-limited, or returns bad data —
the pipeline should never crash just because one field station is down.
"""

import logging
import time
from datetime import datetime, timedelta

import requests
import pandas as pd

from . import config

log = logging.getLogger("landslide.data_sources")
logging.basicConfig(level=logging.INFO)


def _get(url, params=None, headers=None, retries=3, backoff=2):
    """Generic GET with retry/backoff — every fetcher below routes through this."""
    headers = headers or config.REQUEST_HEADERS
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url, params=params, headers=headers, timeout=config.REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.warning(f"GET {url} attempt {attempt}/{retries} failed: {e}")
            time.sleep(backoff * attempt)
    log.error(f"Giving up on {url} after {retries} attempts.")
    return None


# ---------------------------------------------------------------------------
# 1. NASA Global Landslide Catalog (COOLR) — labeled landslide EVENTS
# ---------------------------------------------------------------------------
def fetch_landslide_events(bbox=None, max_records=2000):
    """
    Pull historical landslide event points from NASA's COOLR catalog.

    bbox: (min_lon, min_lat, max_lon, max_lat) or None for worldwide.
    Returns a DataFrame with columns: lat, lon, event_date, trigger, fatality_count
    """
    params = {
        "where": "1=1",
        "outFields": "event_date,event_trigger,fatality_count,landslide_category",
        "f": "geojson",
        "resultRecordCount": max_records,
    }
    if bbox:
        params["geometry"] = ",".join(map(str, bbox))
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = 4326

    resp = _get(config.NASA_GLC_URL, params=params)
    if resp is None:
        return pd.DataFrame()

    try:
        gj = resp.json()
        rows = []
        for feat in gj.get("features", []):
            geom = feat.get("geometry", {}) or {}
            coords = geom.get("coordinates", [None, None])
            props = feat.get("properties", {}) or {}
            rows.append(
                {
                    "lon": coords[0],
                    "lat": coords[1],
                    "event_date": props.get("event_date"),
                    "trigger": props.get("event_trigger"),
                    "fatality_count": props.get("fatality_count"),
                    "category": props.get("landslide_category"),
                }
            )
        return pd.DataFrame(rows)
    except Exception as e:
        log.error(f"Failed to parse NASA GLC response: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# 2. USGS Earthquake catalog — seismic trigger feature
# ---------------------------------------------------------------------------
def fetch_earthquake_features(lat, lon, on_date, radius_km=100, days_lookback=30):
    """
    Returns count and max magnitude of earthquakes within `radius_km` of
    (lat, lon) in the `days_lookback` days before `on_date`.
    """
    end = pd.to_datetime(on_date)
    start = end - timedelta(days=days_lookback)
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%d"),
        "endtime": end.strftime("%Y-%m-%d"),
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": radius_km,
        "minmagnitude": 2.5,
    }
    resp = _get(config.USGS_EARTHQUAKE_URL, params=params)
    if resp is None:
        return {"eq_count_30d": 0, "eq_max_mag_30d": 0.0}

    try:
        gj = resp.json()
        mags = [f["properties"]["mag"] for f in gj.get("features", []) if f["properties"]["mag"] is not None]
        return {
            "eq_count_30d": len(mags),
            "eq_max_mag_30d": max(mags) if mags else 0.0,
        }
    except Exception as e:
        log.error(f"Failed to parse USGS earthquake response: {e}")
        return {"eq_count_30d": 0, "eq_max_mag_30d": 0.0}


# ---------------------------------------------------------------------------
# 3. NOAA / NWS — recent + forecast precipitation (rainfall trigger)
# ---------------------------------------------------------------------------
def fetch_nws_precip_forecast(lat, lon):
    """
    Uses api.weather.gov (US only) to get quantitative precipitation forecast
    for the next 48h. Returns total forecast precip in mm.
    """
    point_resp = _get(f"{config.NWS_API_BASE}/points/{lat},{lon}")
    if point_resp is None:
        return {"forecast_precip_mm_48h": None}

    try:
        forecast_grid_url = point_resp.json()["properties"]["forecastGridData"]
    except Exception as e:
        log.error(f"Could not resolve NWS grid endpoint: {e}")
        return {"forecast_precip_mm_48h": None}

    grid_resp = _get(forecast_grid_url)
    if grid_resp is None:
        return {"forecast_precip_mm_48h": None}

    try:
        qpf = grid_resp.json()["properties"].get("quantitativePrecipitation", {})
        values = qpf.get("values", [])[:2]  # next ~2 periods (~48h)
        total_mm = sum(v.get("value") or 0 for v in values)
        return {"forecast_precip_mm_48h": round(total_mm, 1)}
    except Exception as e:
        log.error(f"Could not parse NWS QPF: {e}")
        return {"forecast_precip_mm_48h": None}


def fetch_noaa_cdo_recent_precip(station_id, start_date, end_date):
    """
    Historical daily precipitation (PRCP) from NOAA's Climate Data Online.
    Requires config.NOAA_CDO_TOKEN. Returns total precip in tenths of mm summed.
    """
    if not config.NOAA_CDO_TOKEN:
        log.warning("NOAA_CDO_TOKEN not set — skipping historical precip fetch.")
        return {"historical_precip_mm": None}

    headers = {"token": config.NOAA_CDO_TOKEN}
    params = {
        "datasetid": "GHCND",
        "stationid": station_id,
        "startdate": start_date,
        "enddate": end_date,
        "datatypeid": "PRCP",
        "limit": 1000,
        "units": "metric",
    }
    resp = _get(f"{config.NOAA_CDO_BASE}/data", params=params, headers=headers)
    if resp is None:
        return {"historical_precip_mm": None}
    try:
        results = resp.json().get("results", [])
        total = sum(r["value"] for r in results) / 10.0  # tenths of mm -> mm
        return {"historical_precip_mm": round(total, 1)}
    except Exception as e:
        log.error(f"Could not parse NOAA CDO precip: {e}")
        return {"historical_precip_mm": None}


# ---------------------------------------------------------------------------
# 4. USGS National Map — elevation (used to derive local slope)
# ---------------------------------------------------------------------------
def fetch_elevation(lat, lon):
    resp = _get(config.USGS_ELEVATION_URL, params={"x": lon, "y": lat, "units": "Meters", "wkid": 4326, "includeDate": False})
    if resp is None:
        return None
    try:
        return float(resp.json()["value"])
    except Exception as e:
        log.error(f"Could not parse USGS elevation response: {e}")
        return None


def estimate_slope_degrees(lat, lon, delta=0.001):
    """
    Approximates local slope by sampling elevation at 4 neighboring points
    (N/S/E/W of the target) and computing rise/run. delta ~ 0.001 deg (~110m).
    """
    center = fetch_elevation(lat, lon)
    north = fetch_elevation(lat + delta, lon)
    south = fetch_elevation(lat - delta, lon)
    east = fetch_elevation(lat, lon + delta)
    west = fetch_elevation(lat, lon - delta)

    pts = [p for p in [center, north, south, east, west] if p is not None]
    if len(pts) < 3:
        return None

    import math
    meters_per_deg_lat = 111_320
    meters_per_deg_lon = 111_320 * math.cos(math.radians(lat))
    dz_ns = (north - south) if (north is not None and south is not None) else 0
    dz_ew = (east - west) if (east is not None and west is not None) else 0
    dx = 2 * delta * meters_per_deg_lon
    dy = 2 * delta * meters_per_deg_lat
    slope_x = dz_ew / dx if dx else 0
    slope_y = dz_ns / dy if dy else 0
    slope_rad = math.atan(math.sqrt(slope_x ** 2 + slope_y ** 2))
    return math.degrees(slope_rad)


# ---------------------------------------------------------------------------
# 5. USDA NRCS Soil Data Access — soil drainage / hydrologic group
# ---------------------------------------------------------------------------
def fetch_soil_hydrologic_group(lat, lon):
    """
    Runs a spatial SQL query against USDA's Soil Data Access service to get
    the dominant hydrologic soil group (A/B/C/D — D drains worst, highest
    runoff & landslide-relevant saturation risk) at a point.
    """
    query = f"""
    SELECT TOP 1 mu.muname, c.hydgrp
    FROM mapunit mu
    INNER JOIN component c ON mu.mukey = c.mukey
    WHERE mu.mukey IN (
        SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
        'POINT({lon} {lat})')
    )
    ORDER BY c.comppct_r DESC
    """
    resp = requests.post(
        config.USDA_SOIL_SDA_URL,
        json={"query": query, "format": "JSON"},
        headers=config.REQUEST_HEADERS,
        timeout=config.REQUEST_TIMEOUT,
    ) if config.USE_LIVE_DATA else None

    if resp is None or resp.status_code != 200:
        return {"soil_hydrologic_group": None}
    try:
        table = resp.json().get("Table", [])
        if not table:
            return {"soil_hydrologic_group": None}
        return {"soil_hydrologic_group": table[0][1]}
    except Exception as e:
        log.error(f"Could not parse USDA soil response: {e}")
        return {"soil_hydrologic_group": None}


# ---------------------------------------------------------------------------
# Orchestrator: build one feature row for a given point/date
# ---------------------------------------------------------------------------
def build_feature_row(lat, lon, on_date):
    """Combine every live source into one dict of features for a location/date."""
    row = {"lat": lat, "lon": lon, "date": on_date}
    row.update(fetch_earthquake_features(lat, lon, on_date))
    row.update(fetch_nws_precip_forecast(lat, lon))
    row["elevation_m"] = fetch_elevation(lat, lon)
    row["slope_deg"] = estimate_slope_degrees(lat, lon)
    row.update(fetch_soil_hydrologic_group(lat, lon))
    return row
