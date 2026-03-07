# CarbonTrust

Satellite-based carbon MRV (Measurement, Reporting, and Verification) infrastructure. CarbonTrust uses Sentinel-2 imagery, a trained ML model, and IPCC methodology to produce reproducible, audit-grade carbon sequestration estimates for forestry projects.

## What it does

Given a geographic boundary and two time periods, CarbonTrust:

1. Ingests Sentinel-2 SR Harmonized imagery via Google Earth Engine
2. Computes NDVI (Normalized Difference Vegetation Index) for baseline and monitoring periods
3. Predicts a forest-specific biomass coefficient using a Gradient Boosting ML model trained on 8,500+ USFS FIA forest plots
4. Estimates biomass change using the ML-predicted coefficient
5. Converts biomass to CO₂e using IPCC 2006 AFOLU Guidelines
6. Calculates uncertainty bands (±20%)
7. Generates a SHA-256 signed PDF verification report
8. Provides plain-English AI interpretation via Gemini 2.5 Flash
9. Autonomously monitors registered forest projects over time, detecting anomalies such as deforestation, fire, and degradation

## Tech Stack

- **Google Earth Engine** — satellite imagery and NDVI computation
- **FastAPI** — REST API backend
- **React + Vite** — frontend dashboard with dark mode and live Leaflet map preview
- **scikit-learn** — Gradient Boosting ML model for biomass coefficient prediction
- **Google Gemini 2.5 Flash** — AI interpretation and alert summaries
- **ReportLab** — PDF report generation
- **APScheduler** — autonomous daily monitoring via cron scheduler
- **Python** — core pipeline

## Methodology

- **Satellite:** Sentinel-2 SR Harmonized (`COPERNICUS/S2_SR_HARMONIZED`)
- **Vegetation Index:** NDVI = (B8 - B4) / (B8 + B4)
- **Biomass Coefficient:** Predicted by GradientBoostingRegressor (R²=0.61, MAE=6.73 t/ha) trained on USFS FIA Virginia data. Falls back to 53.0 t/ha if model is unavailable.
- **Carbon Fraction:** 0.47 (IPCC 2006 AFOLU)
- **CO₂ Conversion:** 3.67 (molecular weight ratio CO₂/C, i.e. 44/12)
- **Uncertainty:** ±20%

## ML Model

- **Data source:** USFS Forest Inventory Analysis (FIA) — Virginia state data (8,523 forest plots)
- **Algorithm:** GradientBoostingRegressor (`n_estimators=200`, `max_depth=4`, `learning_rate=0.05`)
- **Features:** forest type code, canopy cover %, stand age, basal area
- **Target:** aboveground biomass (tonnes/ha)
- **Performance:** R²=0.61, MAE=6.73 t/ha on held-out test set
- **Saved to:** `data/model/biomass_model.pkl` (excluded from git — retrain locally)

## Project Structure

```
CarbonTrust/
├── app/
│   ├── api.py          # FastAPI backend — all routes
│   ├── ndvi.py         # Sentinel-2 NDVI extraction via Google Earth Engine
│   ├── carbon.py       # Biomass → CO₂e conversion (IPCC methodology)
│   ├── model.py        # ML model loader and biomass coefficient predictor
│   ├── monitor.py      # Autonomous anomaly detection and alert generation
│   ├── scheduler.py    # APScheduler — daily monitoring cron (06:00 UTC)
│   ├── report.py       # PDF report generation with SHA-256 hash
│   ├── agent.py        # Gemini 2.5 Flash AI agent with tool use
│   ├── db.py           # JSON-backed persistence (projects, alerts, NDVI history)
│   └── config.py       # All methodology constants and thresholds
├── frontend/
│   └── src/
│       ├── App.jsx               # Sidebar layout — Analyze and Monitor tabs
│       ├── components/
│       │   ├── ForestForm.jsx    # Input form with live Leaflet map preview
│       │   ├── ResultsPanel.jsx  # Metric cards, CO₂e chart, SHA-256, Gemini output
│       │   └── MonitorPanel.jsx  # Project cards, alert badges, NDVI delta
├── scripts/
│   ├── download_fia.py   # Downloads FIA data from USFS public API
│   └── train_model.py    # Trains and saves biomass_model.pkl
├── tests/
│   └── test_carbon.py    # 8 unit tests for compute_co2e()
├── data/
│   └── model/
│       └── biomass_model.pkl   # Trained model (not tracked in git)
├── main.py             # Uvicorn entrypoint
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/bhargavapotturu/CarbonTrust.git
cd CarbonTrust
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
earthengine authenticate
```

### Train the ML model (required before first run)

```bash
python scripts/download_fia.py   # Downloads VA FIA data to data/raw/
python scripts/train_model.py    # Trains model, saves to data/model/biomass_model.pkl
```

### Set environment variables

```bash
export GOOGLE_API_KEY=your_gemini_api_key
```

## Running the API

```bash
python main.py
```

API live at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend live at `http://localhost:5173`

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/estimate` | Returns JSON carbon sequestration estimate |
| `POST` | `/report` | Returns signed PDF verification report |
| `POST` | `/interpret` | Gemini-powered plain-English interpretation |
| `POST` | `/projects` | Register a forest project for monitoring |
| `GET` | `/projects` | List all registered projects |
| `GET` | `/projects/{id}` | Get a single project |
| `DELETE` | `/projects/{id}` | Delete a project |
| `GET` | `/alerts` | Get all anomaly alerts |
| `GET` | `/projects/{id}/alerts` | Get alerts for a specific project |
| `GET` | `/projects/{id}/ndvi-history` | Get NDVI snapshots over time |
| `POST` | `/monitor/trigger` | Manually trigger a full monitoring cycle |
| `POST` | `/monitor/trigger/{id}` | Trigger monitoring for one project |

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
    "forest_type_code": 121,
    "canopy_cover_pct": 75.0,
    "stand_age": 45,
    "basal_area_live": 28.5,
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
  "biomass_coefficient": 61.3,
  "co2e_tonnes": 1650012.9,
  "co2e_low": 1320010.3,
  "co2e_high": 1980015.5,
  "uncertainty_pct": 20,
  "methodology": "IPCC 2006 AFOLU Guidelines, Sentinel-2 SR Harmonized",
  "run_hash": "726c6184b4a049b801eec5ff37c86e14efc9e821abeeb44b2e4de39b09dc2b5c"
}
```

## Running Tests

```bash
pytest tests/
```

## Known Issues

- **sklearn feature names warning** — minor warning when passing raw array to GradientBoostingRegressor. Fix: pass a named DataFrame in `model.py`.
- **Gemini async bug** — `google.genai` async client has a known issue with `_async_httpx_client`. Workaround: sync Gemini calls run via `loop.run_in_executor` inside async FastAPI endpoints.
- **JSON persistence** — `app/db.py` uses flat JSON files which are wiped on Render restarts. PostgreSQL migration (SQLModel + asyncpg) is planned before production deployment.

## Roadmap

- [ ] Replace `app/db.py` with PostgreSQL (SQLModel + asyncpg)
- [ ] Deploy backend to Render.com
- [ ] Deploy frontend to Vercel
- [ ] Email/SMS alerts via AWS SES or Twilio
- [ ] Tokenize verified carbon credits as NFTs on Polygon

## Author

Built by Bhargava Potturu — Virginia Tech CS  
[github.com/bhargavapotturu](https://github.com/bhargavapotturu)