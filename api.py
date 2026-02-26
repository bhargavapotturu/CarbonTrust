import ee
import hashlib
import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Initialize Earth Engine
ee.Initialize(project='carbontrust-488607')

app = FastAPI(
    title="CarbonTrust API",
    description="Reproducible satellite-based carbon verification infrastructure",
    version="0.1.0"
)

# --- Request and Response Models ---
class CarbonEstimateRequest(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    baseline_start: str   # format: YYYY-MM-DD
    baseline_end: str
    monitoring_start: str
    monitoring_end: str
    project_name: Optional[str] = "Unnamed Project"

class CarbonEstimateResponse(BaseModel):
    project_name: str
    area_ha: float
    baseline_ndvi: float
    monitoring_ndvi: float
    ndvi_change: float
    biomass_change_tonnes: float
    carbon_sequestered_tonnes_c: float
    co2e_tonnes: float
    co2e_low: float
    co2e_high: float
    uncertainty_pct: int
    methodology: str
    generated_at: str
    run_hash: str

# --- Constants ---
BIOMASS_COEFFICIENT = 53.0
CARBON_FRACTION = 0.47
CO2_CONVERSION = 3.67
UNCERTAINTY = 0.20

# --- Core pipeline functions ---
def get_ndvi(boundary, start_date, end_date):
    image = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
             .filterBounds(boundary)
             .filterDate(start_date, end_date)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
             .median())
    ndvi = image.normalizedDifference(['B8', 'B4'])
    result = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=boundary,
        scale=100
    ).getInfo()
    return result['nd']

def estimate_carbon(boundary, baseline_start, baseline_end, monitoring_start, monitoring_end):
    area_m2 = boundary.area().getInfo()
    area_ha = area_m2 / 10000

    baseline_ndvi = get_ndvi(boundary, baseline_start, baseline_end)
    monitoring_ndvi = get_ndvi(boundary, monitoring_start, monitoring_end)
    ndvi_change = monitoring_ndvi - baseline_ndvi

    biomass_change = ndvi_change * BIOMASS_COEFFICIENT * area_ha
    carbon = biomass_change * CARBON_FRACTION
    co2e = carbon * CO2_CONVERSION
    co2e_low = co2e * (1 - UNCERTAINTY)
    co2e_high = co2e * (1 + UNCERTAINTY)

    return {
        "area_ha": round(area_ha, 1),
        "baseline_ndvi": round(baseline_ndvi, 4),
        "monitoring_ndvi": round(monitoring_ndvi, 4),
        "ndvi_change": round(ndvi_change, 4),
        "biomass_change_tonnes": round(biomass_change, 1),
        "carbon_sequestered_tonnes_c": round(carbon, 1),
        "co2e_tonnes": round(co2e, 1),
        "co2e_low": round(co2e_low, 1),
        "co2e_high": round(co2e_high, 1),
    }

def hash_result(data: dict) -> str:
    content = str(sorted(data.items())).encode()
    return hashlib.sha256(content).hexdigest()

# --- Routes ---
@app.get("/")
def root():
    return {
        "service": "CarbonTrust API",
        "version": "0.1.0",
        "status": "running"
    }

@app.post("/estimate", response_model=CarbonEstimateResponse)
def estimate(req: CarbonEstimateRequest):
    try:
        boundary = ee.Geometry.Rectangle([
            req.min_lon, req.min_lat,
            req.max_lon, req.max_lat
        ])

        results = estimate_carbon(
            boundary,
            req.baseline_start,
            req.baseline_end,
            req.monitoring_start,
            req.monitoring_end
        )

        generated_at = datetime.datetime.utcnow().isoformat() + "Z"
        run_hash = hash_result({**results, "generated_at": generated_at})

        return CarbonEstimateResponse(
            project_name=req.project_name,
            **results,
            uncertainty_pct=int(UNCERTAINTY * 100),
            methodology="IPCC 2006 AFOLU Guidelines, Sentinel-2 SR Harmonized",
            generated_at=generated_at,
            run_hash=run_hash
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)