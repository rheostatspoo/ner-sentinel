"""
ner_locations.py
-----------------
Seed data for the North Eastern Region: a spread of real towns/villages and
the highway segments connecting them, each tagged with terrain features that
feed the Random Forest (slope, elevation, soil, distance to fault — the
Shillong Plateau fault system runs through Meghalaya/Assam). Coordinates are
real; sensor/rainfall readings are simulated for the demo the same way
described in the model README (swap for live IMD/NWS/sensor feeds in
production).
"""

import random

random.seed(7)

# name, state, lat, lon, elevation_m, slope_deg, dist_to_fault_km, soil group, base ndvi
LOCATIONS = [
    ("Sohra (Cherrapunji)", "Meghalaya", 25.2840, 91.7273, 1484, 38, 22, "C", 0.55),
    ("Mawsynram", "Meghalaya", 25.2971, 91.5822, 1400, 41, 26, "C", 0.58),
    ("Shillong", "Meghalaya", 25.5788, 91.8933, 1496, 22, 15, "B", 0.60),
    ("Jowai", "Meghalaya", 25.4500, 92.2000, 1360, 30, 20, "C", 0.52),
    ("Guwahati (Narengi Hills)", "Assam", 26.1584, 91.7898, 130, 27, 35, "B", 0.40),
    ("Haflong", "Assam", 25.1667, 93.0167, 900, 35, 45, "D", 0.48),
    ("Kohima", "Nagaland", 25.6751, 94.1086, 1444, 33, 60, "C", 0.50),
    ("Dimapur", "Nagaland", 25.9091, 93.7267, 260, 12, 55, "B", 0.35),
    ("Mokokchung", "Nagaland", 26.3230, 94.5280, 1325, 36, 70, "C", 0.55),
    ("Aizawl", "Mizoram", 23.7271, 92.7176, 1132, 40, 80, "D", 0.53),
    ("Lunglei", "Mizoram", 22.8879, 92.7320, 1100, 37, 90, "C", 0.51),
    ("Champhai", "Mizoram", 23.4667, 93.3167, 1560, 34, 95, "C", 0.49),
    ("Imphal", "Manipur", 24.8170, 93.9368, 786, 15, 65, "B", 0.42),
    ("Churachandpur", "Manipur", 24.3333, 93.6833, 915, 32, 70, "C", 0.47),
    ("Ukhrul", "Manipur", 25.0500, 94.3667, 1697, 39, 78, "D", 0.50),
    ("Agartala", "Tripura", 23.8315, 91.2868, 40, 9, 100, "A", 0.38),
    ("Ambassa", "Tripura", 23.9333, 91.8500, 90, 20, 92, "B", 0.44),
    ("Itanagar", "Arunachal Pradesh", 27.0844, 93.6053, 470, 34, 40, "C", 0.62),
    ("Along (Aalo)", "Arunachal Pradesh", 28.1667, 94.8000, 300, 42, 55, "D", 0.65),
    ("Tawang", "Arunachal Pradesh", 27.5859, 91.8594, 3048, 46, 30, "D", 0.30),
    ("Ziro", "Arunachal Pradesh", 27.5500, 93.8333, 1688, 28, 45, "B", 0.60),
    ("Gangtok", "Sikkim", 27.3389, 88.6065, 1650, 44, 18, "D", 0.57),
    ("Mangan", "Sikkim", 27.5167, 88.5333, 1050, 48, 12, "D", 0.59),
    ("Namchi", "Sikkim", 27.1667, 88.3500, 1675, 43, 20, "C", 0.56),
]

# Highway/road segments connecting locations, used for the connectivity list
ROAD_SEGMENTS = [
    ("NH-6", "Shillong \u2192 Sohra (Cherrapunji)", "Shillong", "Sohra (Cherrapunji)"),
    ("NH-206", "Shillong \u2192 Jowai", "Shillong", "Jowai"),
    ("NH-27", "Guwahati \u2192 Haflong", "Guwahati (Narengi Hills)", "Haflong"),
    ("NH-2", "Dimapur \u2192 Kohima", "Dimapur", "Kohima"),
    ("NH-29", "Kohima \u2192 Mokokchung", "Kohima", "Mokokchung"),
    ("NH-6", "Aizawl \u2192 Lunglei", "Aizawl", "Lunglei"),
    ("NH-102B", "Aizawl \u2192 Champhai", "Aizawl", "Champhai"),
    ("NH-2", "Imphal \u2192 Ukhrul", "Imphal", "Ukhrul"),
    ("NH-102", "Imphal \u2192 Churachandpur", "Imphal", "Churachandpur"),
    ("NH-8", "Agartala \u2192 Ambassa", "Agartala", "Ambassa"),
    ("NH-415", "Itanagar \u2192 Ziro", "Itanagar", "Ziro"),
    ("NH-13", "Ziro \u2192 Along (Aalo)", "Ziro", "Along (Aalo)"),
    ("NH-13", "Tezpur \u2192 Tawang", "Itanagar", "Tawang"),
    ("NH-10", "Gangtok \u2192 Mangan", "Gangtok", "Mangan"),
    ("NH-10", "Gangtok \u2192 Namchi", "Gangtok", "Namchi"),
]


def simulate_live_readings(loc):
    """Randomized-but-seeded rainfall/seismic readings layered on top of static terrain facts."""
    name, state, lat, lon, elevation_m, slope_deg, dist_fault, soil, ndvi_base = loc
    rng = random.Random(hash(name) % (2**31))
    monsoon_boost = 1.6 if state in ("Meghalaya", "Sikkim", "Arunachal Pradesh") else 1.0
    forecast_precip = round(rng.uniform(10, 90) * monsoon_boost, 1)
    historical_precip = round(forecast_precip * rng.uniform(3, 7), 1)
    eq_count = rng.choices([0, 1, 2, 3, 4], weights=[35, 30, 20, 10, 5])[0]
    eq_mag = round(rng.uniform(2.5, 6.2), 1) if eq_count > 0 else 0.0
    ndvi = round(max(0.05, min(0.9, ndvi_base + rng.uniform(-0.08, 0.08))), 2)
    return {
        "name": name,
        "state": state,
        "lat": lat,
        "lon": lon,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "distance_to_fault_km": dist_fault,
        "soil_hydrologic_group": soil,
        "forecast_precip_mm_48h": forecast_precip,
        "historical_precip_mm": historical_precip,
        "eq_count_30d": eq_count,
        "eq_max_mag_30d": eq_mag,
        "ndvi": ndvi,
    }


def all_locations_live():
    return [simulate_live_readings(loc) for loc in LOCATIONS]
