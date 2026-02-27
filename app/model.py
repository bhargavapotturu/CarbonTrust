# app/model.py

import pickle
import os
import numpy as np

MODEL_PATH = os.path.join("data", "model", "biomass_model.pkl")

_model = None
_features = None


def _load():
    global _model, _features
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run scripts/train_model.py first."
            )
        with open(MODEL_PATH, "rb") as f:
            payload = pickle.load(f)
        _model = payload["model"]
        _features = payload["features"]


def predict_biomass_coefficient(
    forest_type_code: int = 400,
    canopy_cover_pct: float = 60.0,
    stand_age: float = 40.0,
    basal_area_live: float = 80.0,
) -> float:
    """
    Predict biomass coefficient (tonnes/ha) using the trained FIA model.
    Falls back to 53.0 if the model is unavailable.

    Args:
        forest_type_code: FIA forest type code (default 400 = oak/gum/cypress)
        canopy_cover_pct: Live canopy cover percentage (0-100)
        stand_age:        Stand age in years
        basal_area_live:  Basal area of live trees (sq ft/acre)
    """
    try:
        _load()
        X = np.array([[forest_type_code, canopy_cover_pct, stand_age, basal_area_live]])
        coefficient = float(_model.predict(X)[0])
        # Clamp to physically realistic range
        return max(10.0, min(coefficient, 300.0))
    except Exception:
        # Graceful fallback to literature value
        return 53.0