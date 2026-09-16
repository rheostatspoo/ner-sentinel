"""
synthetic_data.py
------------------
This sandbox has no outbound internet access, so live calls to NASA/USGS/NOAA/USDA
in data_sources.py can't actually be exercised here. This module generates a
synthetic dataset with the EXACT same feature schema `build_feature_row()`
would produce, so you can develop, test, and sanity-check the whole Random
Forest pipeline right now — and swap in real data later with zero code changes
(just set config.USE_LIVE_DATA = True and call data_sources.build_feature_row
in a loop over your real coordinates/dates instead of this generator).

The generative rules below encode well-established landslide risk factors
(steep slope + high rainfall + poor drainage + seismic shaking + weak soil
history = higher risk) so the synthetic labels are realistic enough to train
and evaluate a meaningful model.
"""

import numpy as np
import pandas as pd


def generate_dataset(n_samples=6000, random_state=42):
    rng = np.random.default_rng(random_state)

    slope_deg = rng.uniform(0, 60, n_samples)
    elevation_m = rng.uniform(0, 3500, n_samples)
    forecast_precip_mm_48h = rng.gamma(shape=2.0, scale=15.0, size=n_samples)
    historical_precip_mm = forecast_precip_mm_48h * rng.uniform(3, 8, n_samples)
    eq_count_30d = rng.poisson(0.6, n_samples)
    eq_max_mag_30d = np.where(eq_count_30d > 0, rng.uniform(2.5, 6.5, n_samples), 0.0)
    soil_hydrologic_group = rng.choice(["A", "B", "C", "D"], size=n_samples, p=[0.25, 0.35, 0.25, 0.15])
    ndvi = rng.uniform(-0.1, 0.9, n_samples)  # vegetation cover, proxy from remote sensing
    distance_to_fault_km = rng.exponential(scale=40, size=n_samples)

    hydgrp_risk = pd.Series(soil_hydrologic_group).map({"A": 0.1, "B": 0.3, "C": 0.6, "D": 1.0}).to_numpy()

    # Latent risk score combining known real-world drivers, plus noise
    risk_score = (
        0.035 * slope_deg
        + 0.010 * (forecast_precip_mm_48h / 10)
        + 0.006 * (historical_precip_mm / 10)
        + 0.35 * eq_max_mag_30d / 6.5
        + 0.9 * hydgrp_risk
        - 0.6 * ndvi  # more vegetation -> more root cohesion -> less risk
        - 0.01 * (distance_to_fault_km / 10)
        + rng.normal(0, 0.6, n_samples)
    )

    # Convert to binary label via a threshold calibrated to ~12% positive rate
    threshold = np.quantile(risk_score, 0.88)
    landslide_occurred = (risk_score >= threshold).astype(int)

    df = pd.DataFrame(
        {
            "slope_deg": slope_deg,
            "elevation_m": elevation_m,
            "forecast_precip_mm_48h": forecast_precip_mm_48h,
            "historical_precip_mm": historical_precip_mm,
            "eq_count_30d": eq_count_30d,
            "eq_max_mag_30d": eq_max_mag_30d,
            "soil_hydrologic_group": soil_hydrologic_group,
            "ndvi": ndvi,
            "distance_to_fault_km": distance_to_fault_km,
            "landslide_occurred": landslide_occurred,
        }
    )
    return df
