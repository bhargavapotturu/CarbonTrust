# scripts/train_model.py

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

DATA_DIR = "data/fia_raw"
MODEL_DIR = "data/model"
MODEL_PATH = os.path.join(MODEL_DIR, "biomass_model.pkl")


def load_data():
    print("Loading FIA tables...")
    tree = pd.read_csv(os.path.join(DATA_DIR, "tree.csv"), low_memory=False)
    cond = pd.read_csv(os.path.join(DATA_DIR, "cond.csv"), low_memory=False)
    plot = pd.read_csv(os.path.join(DATA_DIR, "plot.csv"), low_memory=False)
    return tree, cond, plot


def build_features(tree, cond, plot):
    print("Building features...")

    # DRYBIO_AG = aboveground dry biomass in lbs/acre, convert to tonnes/ha
    # 1 lb/acre = 0.001121 tonnes/ha
    tree["biomass_tonnes_ha"] = tree["DRYBIO_AG"] * 0.001121

    # Aggregate biomass per plot
    plot_biomass = (
        tree.groupby("PLT_CN")["biomass_tonnes_ha"]
        .sum()
        .reset_index()
        .rename(columns={"biomass_tonnes_ha": "total_biomass_tonnes_ha"})
    )

    # Merge with condition table for forest type and canopy cover
    cond_cols = ["PLT_CN", "FORTYPCD", "LIVE_CANOPY_CVR_PCT", "STDAGE", "BALIVE"]
    cond_clean = cond[cond_cols].dropna()

    # Aggregate cond by plot (take mean for multi-condition plots)
    cond_agg = cond_clean.groupby("PLT_CN").mean().reset_index()

    # Merge everything
    df = plot_biomass.merge(cond_agg, on="PLT_CN", how="inner")
    df = df.dropna()

    # Filter to realistic ranges
    df = df[df["total_biomass_tonnes_ha"] > 0]
    df = df[df["total_biomass_tonnes_ha"] < 1000]
    df = df[df["STDAGE"] > 0]
    df = df[df["LIVE_CANOPY_CVR_PCT"] > 0]

    print(f"Dataset size after cleaning: {len(df):,} plots")
    return df


def train(df):
    print("Training model...")

    features = ["FORTYPCD", "LIVE_CANOPY_CVR_PCT", "STDAGE", "BALIVE"]
    target = "total_biomass_tonnes_ha"

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\nModel Performance:")
    print(f"  R²  : {r2:.4f}")
    print(f"  MAE : {mae:.2f} tonnes/ha")

    return model, features


def save_model(model, features):
    os.makedirs(MODEL_DIR, exist_ok=True)
    payload = {"model": model, "features": features}
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)
    print(f"\nModel saved to {MODEL_PATH}")


def main():
    tree, cond, plot = load_data()
    df = build_features(tree, cond, plot)
    model, features = train(df)
    save_model(model, features)


if __name__ == "__main__":
    main()