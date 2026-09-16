"""
train_model.py
---------------
Trains a Random Forest classifier to predict landslide occurrence risk.

Usage:
    python -m src.train_model            # uses synthetic data (offline demo)

To train on real data once you have internet access:
    1. Set config.USE_LIVE_DATA = True
    2. Build a labeled dataset: for each historical landslide EVENT from
       fetch_landslide_events() (positive class) and an equal number of
       random non-landslide locations/dates (negative class), call
       data_sources.build_feature_row(lat, lon, date) and stack the rows.
    3. Pass that DataFrame into train(df=...) below instead of the synthetic one.
"""

import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    confusion_matrix,
    RocCurveDisplay,
)
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt

from .feature_engineering import build_preprocessor, ALL_FEATURES, TARGET
from .synthetic_data import generate_dataset

log = logging.getLogger("landslide.train")
logging.basicConfig(level=logging.INFO)

MODEL_PATH = "models/landslide_rf_pipeline.joblib"


def train(df: pd.DataFrame = None, tune_hyperparams=True, random_state=42):
    if df is None:
        log.info("No dataset supplied — generating synthetic demo dataset.")
        df = generate_dataset(n_samples=6000, random_state=random_state)

    X = df[ALL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=random_state
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced",
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    if tune_hyperparams:
        param_grid = {
            "clf__n_estimators": [200, 400],
            "clf__max_depth": [None, 10, 20],
            "clf__min_samples_leaf": [1, 2, 5],
            "clf__max_features": ["sqrt", "log2"],
        }
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        search = GridSearchCV(
            pipeline, param_grid, scoring="roc_auc", cv=cv, n_jobs=-1, verbose=1
        )
        log.info("Running GridSearchCV hyperparameter tuning...")
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        log.info(f"Best params: {search.best_params_}")
        log.info(f"Best CV ROC-AUC: {search.best_score_:.4f}")
    else:
        pipeline.fit(X_train, y_train)

    # --- Evaluation ---------------------------------------------------------
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n=== Classification report (test set) ===")
    print(classification_report(y_test, y_pred, digits=3))
    auc = roc_auc_score(y_test, y_proba)
    print(f"ROC-AUC: {auc:.4f}")

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion matrix:")
    print(cm)

    # --- Feature importance --------------------------------------------------
    ohe = pipeline.named_steps["preprocess"].named_transformers_["cat"].named_steps["onehot"]
    cat_names = list(ohe.get_feature_names_out(["soil_hydrologic_group"]))
    from .feature_engineering import NUMERIC_FEATURES

    feature_names = NUMERIC_FEATURES + cat_names
    importances = pipeline.named_steps["clf"].feature_importances_
    imp_df = pd.DataFrame({"feature": feature_names, "importance": importances}).sort_values(
        "importance", ascending=False
    )
    print("\n=== Feature importances ===")
    print(imp_df.to_string(index=False))

    _plot_feature_importance(imp_df)
    _plot_roc(y_test, y_proba)

    joblib.dump(pipeline, MODEL_PATH)
    log.info(f"Saved trained pipeline to {MODEL_PATH}")

    return pipeline, imp_df, auc


def _plot_feature_importance(imp_df, path="models/feature_importance.png"):
    plt.figure(figsize=(8, 5))
    plt.barh(imp_df["feature"][::-1], imp_df["importance"][::-1], color="#7a5c3e")
    plt.xlabel("Importance")
    plt.title("Random Forest Feature Importance — Landslide Risk")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _plot_roc(y_test, y_proba, path="models/roc_curve.png"):
    plt.figure(figsize=(5, 5))
    RocCurveDisplay.from_predictions(y_test, y_proba)
    plt.title("ROC Curve — Landslide Risk Model")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


if __name__ == "__main__":
    train()
