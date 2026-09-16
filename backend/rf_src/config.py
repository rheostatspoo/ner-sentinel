"""
config.py
---------
Central place for every government / public data endpoint the pipeline talks to.
All of these are free, public APIs run by government (or government-funded) agencies.
Some require a free API token (noted below) — register once and drop the token
into a `.env` file or environment variable, never hard-code it.

Sources used
============
1. NASA Global Landslide Catalog (GLC) / COOLR
   - Historical, labeled landslide EVENTS (our positive class).
   - Hosted on NASA's ArcGIS Online (public REST API, no key needed).
   URL: https://maps.nccs.nasa.gov/arcgis/rest/services/Landslides/COOLR_Public/MapServer/0/query

2. USGS Earthquake Catalog (FDSN Event Web Service)
   - Seismic activity near a location/date — a major landslide trigger.
   - No key needed.
   URL: https://earthquake.usgs.gov/fdsnws/event/1/query

3. NOAA National Weather Service (NWS) API
   - Forecast + observed precipitation (rainfall is the #1 landslide trigger).
   - No key needed, but requires a descriptive User-Agent header.
   URL: https://api.weather.gov

4. NOAA NCEI Climate Data Online (CDO)
   - Historical daily precipitation / climate normals.
   - FREE API TOKEN required: https://www.ncdc.noaa.gov/cdo-web/token
   URL: https://www.ncei.noaa.gov/cdo-web/api/v2

5. USGS National Map — Elevation Point Query Service (EPQS)
   - Elevation at a lat/lon, used to derive local slope/relief.
   - No key needed.
   URL: https://epqs.nationalmap.gov/v1/json

6. USDA NRCS Soil Data Access (SDA)
   - Soil texture / permeability / hydrologic group (affects infiltration).
   - No key needed (SQL-like query over SOAP/REST).
   URL: https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest

Notes
-----
- This module only stores endpoints + light request helpers. The actual
  network calls happen in `data_sources.py`.
- This sandboxed environment has no outbound network access, so
  `train.py` will fall back to a synthetic generator (see `synthetic_data.py`)
  that mimics the real schema. Point `USE_LIVE_DATA = True` and run this
  project on your own machine to pull real data.
"""

import os

USE_LIVE_DATA = False  # flip to True when running with real internet access

# --- Endpoints -------------------------------------------------------------
NASA_GLC_URL = (
    "https://maps.nccs.nasa.gov/arcgis/rest/services/"
    "Landslides/COOLR_Public/MapServer/0/query"
)
USGS_EARTHQUAKE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
NWS_API_BASE = "https://api.weather.gov"
NOAA_CDO_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2"
USGS_ELEVATION_URL = "https://epqs.nationalmap.gov/v1/json"
USDA_SOIL_SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"

# --- Credentials / headers ---------------------------------------------------
# NOAA requires a free token: https://www.ncdc.noaa.gov/cdo-web/token
NOAA_CDO_TOKEN = os.environ.get("NOAA_CDO_TOKEN", "")

# NWS requires a descriptive User-Agent identifying your app + contact email
REQUEST_HEADERS = {
    "User-Agent": "landslide-risk-rf-model (contact: you@example.com)"
}

REQUEST_TIMEOUT = 20  # seconds
