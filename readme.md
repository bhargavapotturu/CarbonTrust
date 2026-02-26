# CarbonTrust

Satellite-based carbon verification infrastructure. CarbonTrust uses Sentinel-2 imagery and IPCC methodology to produce reproducible, audit-grade carbon sequestration estimates for forestry projects.

## What it does

Given a geographic boundary and two time periods, CarbonTrust:

1. Ingests Sentinel-2 satellite imagery via Google Earth Engine
2. Computes NDVI (Normalized Difference Vegetation Index) for both periods
3. Estimates biomass change using published allometric coefficients
4. Converts biomass to CO₂e using IPCC 2006 AFOLU Guidelines
5. Calculates uncertainty bands (±20%)
6. Returns a verifiable result with a unique SHA-256 run hash

## Tech Stack

- **Google Earth Engine** — satellite imagery and NDVI computation
- **FastAPI** — REST API backend
- **ReportLab** — PDF report generation
- **Python** — core pipeline

## Methodology

- Satellite: Sentinel-2 SR Harmonized (COPERNICUS/S2_SR_HARMONIZED)
- Vegetation Index: NDVI (B8 - B4) / (B8 + B4)
- Biomass Coefficient: 53.0 t/ha per NDVI unit (temperate forest literature)
- Carbon Fraction: 0.47 (IPCC 2006)
- CO₂ Conversion: 3.67 (molecular weight ratio CO₂/C)
- Uncertainty: ±20%

## Setup
```bash
git clone https://github.com/your-username/CarbonTrust.git
cd CarbonTrust
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
```

## Running the API
```bash
python3 api.py
```

API will be live at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

## Example Request
```bash
curl -X POST http://localhost:8000/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "min_lon": -79.5,
    "min_lat": 38.0,
    "max_lon": -78.5,
    "max_lat": 38.5,
    "baseline_start": "2021-06-01",
    "baseline_end": "2021-09-01",
    "monitoring_start": "2023-06-01",
    "monitoring_end": "2023-09-01",
    "project_name": "George Washington National Forest"
  }'
```

## Example Response
```json
{
  "project_name": "George Washington National Forest",
  "area_ha": 485492.9,
  "baseline_ndvi": 0.7265,
  "monitoring_ndvi": 0.7637,
  "ndvi_change": 0.0372,
  "co2e_tonnes": 1650012.9,
  "co2e_low": 1320010.3,
  "co2e_high": 1980015.5,
  "uncertainty_pct": 20,
  "methodology": "IPCC 2006 AFOLU Guidelines, Sentinel-2 SR Harmonized",
  "run_hash": "726c6184b4a049b801eec5ff37c86e14efc9e821abeeb44b2e4de39b09dc2b5c"
}
```

## Project Structure
```
CarbonTrust/
├── api.py          # FastAPI backend
├── ndvi.py         # NDVI extraction pipeline
├── carbon.py       # Carbon estimation
├── report.py       # PDF report generation
├── requirements.txt
└── README.md
```

## Author

Built by Bhargava Potturu — Virginia Tech CS
```