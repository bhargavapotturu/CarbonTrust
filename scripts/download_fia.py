# scripts/download_fia.py

import requests
import pandas as pd
import os

# FIA DataMart public API - no auth needed
BASE_URL = "https://apps.fs.usda.gov/fia/datamart/CSV"

# We want the TREE and PLOT tables for Virginia (state code 51)
TABLES = {
    "tree": f"{BASE_URL}/VA_TREE.csv",
    "plot": f"{BASE_URL}/VA_PLOT.csv",
    "cond": f"{BASE_URL}/VA_COND.csv",
}

OUTPUT_DIR = "data/fia_raw"


def download_table(name: str, url: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")

    if os.path.exists(out_path):
        print(f"[{name}] Already downloaded, skipping.")
        return out_path

    print(f"[{name}] Downloading from {url} ...")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"[{name}] Saved to {out_path}")
    return out_path


def main():
    for name, url in TABLES.items():
        download_table(name, url)
    print("\nAll FIA tables downloaded.")


if __name__ == "__main__":
    main()