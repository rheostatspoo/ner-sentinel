# NER Sentinel — AI Early-Warning Platform for Landslides (North Eastern Region)

A working prototype for the problem statement: real-time monitoring, ML-based
landslide risk prediction, GIS visualization, citizen/field reporting, and
multilingual early-warning alerts for the North Eastern Region.

**Live demo:** run `./run.sh` from this folder, then open **http://localhost:8000**.

## What's actually working right now

- **Random Forest prediction engine** — the model built earlier
  (`backend/rf_src/`), trained on slope, elevation, rainfall, seismic
  activity, soil drainage, vegetation cover, and fault distance. Wrapped
  behind a real API (`POST /api/predict`) that the dashboard's "Run the
  model" panel calls live.
- **GIS risk map** — 24 real NER settlements (Shillong, Sohra/Cherrapunji,
  Mawsynram, Aizawl, Kohima, Imphal, Gangtok, Tawang, and more) plotted with
  real coordinates, each scored by the model and color-coded by severity.
- **Road connectivity status** — highway segments between those towns, with
  status (Open / At risk / Blocked) derived from the risk at each endpoint —
  the "which roads might get cut off" view district authorities need.
- **Auto-generated early-warning feed** — turns every High/Severe zone into a
  structured alert with a message, timestamp, and the channels it would go
  out on (SMS / app push / district control room).
- **Response prioritisation** — ranks zones by risk × a population-exposure
  proxy, with a suggested action per zone (dispatch now / stage equipment /
  monitor).
- **Citizen & field-officer reporting** — a geo-tagged form (with a "use my
  location" button and photo upload) that posts to the backend and shows up
  in a live feed. Submissions made while offline are queued in the browser
  and sent automatically the moment connectivity returns.
- **Multilingual UI** — English, অসমীয়া (Assamese), हिंदी (Hindi) toggle,
  covering every label and the alert feed — extendable to Khasi, Mizo,
  Manipuri, Nyishi, etc. by adding one more entry to `frontend/i18n.js`.
- **Dashboard KPIs** — zones monitored, active alerts, roads blocked/
  restricted, field reports received, refreshed every 45 seconds like a real
  ops screen.

## What's simulated, and why

This environment has no outbound internet access, so I couldn't wire up the
*actual* IMD/NOAA/USGS/soil-sensor feeds inside this conversation. The
rainfall, seismic, and sensor readings you see are simulated
(`backend/data/ner_locations.py`) on top of **real terrain facts** (actual
coordinates, elevation, slope, fault distances). The integration code for
the real government APIs already exists and was built and tested in the
earlier model project — see "Going from prototype to production" below.

## Architecture

```
ner-sentinel/
├── run.sh                     # one-command start
├── backend/
│   ├── app.py                  # FastAPI: risk-zones, roads, alerts, weather,
│   │                           #   summary, predict, reports — serves the
│   │                           #   frontend too, so it's one process/port
│   ├── model/
│   │   └── landslide_rf_pipeline.joblib   # trained Random Forest
│   ├── rf_src/                 # the model project: training, feature eng,
│   │                           #   and the real government-API fetchers
│   │   ├── data_sources.py     #   NASA/USGS/NOAA/USDA integrations
│   │   ├── feature_engineering.py
│   │   └── train_model.py
│   └── data/
│       └── ner_locations.py    # NER settlement + road seed data
└── frontend/
    ├── index.html               # dashboard shell
    ├── style.css                # design system
    ├── app.js                   # map, data fetching, forms, offline queue
    └── i18n.js                  # EN / Assamese / Hindi dictionary
```

**Why FastAPI serves the frontend too:** one process, one port, one command
for judges to run — no CORS setup, no separate dev server. `StaticFiles`
mounts the frontend folder; everything under `/api/*` is the real API.

## Running it

```bash
cd ner-sentinel
./run.sh
# open http://localhost:8000
```

(`run.sh` creates a virtualenv, installs `backend/requirements.txt`, and
starts the server. The map's tile layer and Google Fonts need real internet
access in the browser — everything else works fully offline against your
local backend.)

## Mapping to the problem statement

| Ask | Where |
|---|---|
| Collect rainfall, soil, satellite, terrain, historical data | `backend/rf_src/data_sources.py` (real API integrations) + `ner_locations.py` (terrain facts) |
| AI/ML model to identify high-risk zones | Random Forest, `backend/rf_src/train_model.py`, served via `/api/predict` and `/api/risk-zones` |
| Real-time alerts to authorities & communities | `/api/alerts`, rendered in the early-warning feed panel |
| GIS mapping of roads/villages/infrastructure | Leaflet map + `/api/roads` connectivity panel |
| Citizens/field officials upload geo-tagged photos | "Report an incident" modal → `/api/reports` |
| Dashboards: severity, connectivity, forecasts, prioritisation | KPI strip + four dashboard panels |
| Multilingual notifications | Language switch (EN/অসমীয়া/हिंदी) across UI + alert text |
| Low-network/offline functionality | Offline banner + `localStorage` report queue that auto-syncs on reconnect |

## Going from prototype to production

1. Flip `USE_LIVE_DATA = True` in `backend/rf_src/config.py`.
2. Set a free `NOAA_CDO_TOKEN` for historical rainfall.
3. Replace `ner_locations.simulate_live_readings()` with real calls to
   `data_sources.build_feature_row(lat, lon, date)` for each settlement,
   plus real IMD/state disaster-management feeds where available.
4. Swap the in-memory `REPORTS` list and offline queue for a proper DB
   (Postgres/PostGIS) and a service worker + IndexedDB for true offline
   photo persistence.
5. Wire the alert feed to actual SMS (e.g. via a gateway) and push
   notification delivery instead of the simulated "channels" list.
6. Retrain the Random Forest on NASA's real Global Landslide Catalog events
   for the NER region specifically, once enough labeled local events are
   collected — the training pipeline (`train_model.py`) is unchanged either way.
