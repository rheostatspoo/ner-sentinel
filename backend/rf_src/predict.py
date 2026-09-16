"""
predict.py
----------
Load the trained pipeline and score a location.

Live mode (requires internet + config.USE_LIVE_DATA = True):
    python -m src.predict --lat 34.05 --lon -118.25 --date 2026-09-12 --live

Manual mode (you supply the feature values yourself, e.g. from your own data):
    python -m src.predict --slope 32 --elevation 850 --precip48 60 \\
        --histprecip 320 --eqcount 2 --eqmag 4.1 --soil C --ndvi 0.2 --fault 12
"""

import argparse
import joblib
import pandas as pd

from .feature_engineering import ALL_FEATURES
from .train_model import MODEL_PATH


def predict_from_features(feature_dict, model_path=MODEL_PATH):
    pipeline = joblib.load(model_path)
    row = {k: feature_dict.get(k) for k in ALL_FEATURES}
    X = pd.DataFrame([row])
    proba = pipeline.predict_proba(X)[0, 1]
    pred = pipeline.predict(X)[0]
    return {
        "landslide_risk_probability": round(float(proba), 4),
        "predicted_class": int(pred),
        "risk_tier": _risk_tier(proba),
    }


def _risk_tier(p):
    if p < 0.2:
        return "Low"
    elif p < 0.5:
        return "Moderate"
    elif p < 0.75:
        return "High"
    return "Severe"


def predict_from_location(lat, lon, on_date, model_path=MODEL_PATH):
    """Live mode — pulls fresh features from the government APIs in data_sources.py."""
    from . import data_sources

    row = data_sources.build_feature_row(lat, lon, on_date)
    return predict_from_features(row, model_path=model_path)


def _build_arg_parser():
    p = argparse.ArgumentParser(description="Predict landslide risk.")
    p.add_argument("--live", action="store_true", help="Fetch live features for --lat/--lon/--date")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--date", type=str)

    p.add_argument("--slope", type=float, dest="slope_deg")
    p.add_argument("--elevation", type=float, dest="elevation_m")
    p.add_argument("--precip48", type=float, dest="forecast_precip_mm_48h")
    p.add_argument("--histprecip", type=float, dest="historical_precip_mm")
    p.add_argument("--eqcount", type=int, dest="eq_count_30d", default=0)
    p.add_argument("--eqmag", type=float, dest="eq_max_mag_30d", default=0.0)
    p.add_argument("--soil", type=str, dest="soil_hydrologic_group", choices=["A", "B", "C", "D"])
    p.add_argument("--ndvi", type=float)
    p.add_argument("--fault", type=float, dest="distance_to_fault_km")
    return p


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    if args.live:
        result = predict_from_location(args.lat, args.lon, args.date)
    else:
        result = predict_from_features(vars(args))
    print(result)
