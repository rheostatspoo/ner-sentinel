"""
feature_engineering.py
-----------------------
Builds the sklearn preprocessing pipeline (imputation + one-hot encoding for
categorical soil group) that feeds the Random Forest. Kept separate from
train_model.py so the exact same transform can be reused at prediction time.
"""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUMERIC_FEATURES = [
    "slope_deg",
    "elevation_m",
    "forecast_precip_mm_48h",
    "historical_precip_mm",
    "eq_count_30d",
    "eq_max_mag_30d",
    "ndvi",
    "distance_to_fault_km",
]
CATEGORICAL_FEATURES = ["soil_hydrologic_group"]
TARGET = "landslide_occurred"

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def build_preprocessor():
    numeric_pipe = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor
