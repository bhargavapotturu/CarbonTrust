# app/api.py

import hashlib
import datetime
import ee
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    UNCERTAINTY
)
from app.carbon import estimate_carbon
from app.ndvi import initialize
from app.report import generate_report

# Initialize Earth Engine once at startup
initialize()

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
)


# --- Request / Response Models ---

class CarbonEstimateRequest(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    baseline_start: str    # YYYY-MM-DD
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


# --- Helpers ---

def build_boundary(req: CarbonEstimateRequest) -> ee.Geometry:
    return ee.Geometry.Rectangle([
        req.min_lon, req.min_lat,
        req.max_lon, req.max_lat
    ])


def hash_result(data: dict) -> str:
    content = str(sorted(data.items())).encode()
    return hashlib.sha256(content).hexdigest()


def run_estimate(req: CarbonEstimateRequest) -> tuple[dict, str, str]:
    """Shared logic used by both /estimate and /report."""
    boundary = build_boundary(req)
    results = estimate_carbon(
        boundary,
        req.baseline_start,
        req.baseline_end,
        req.monitoring_start,
        req.monitoring_end,
    )
    generated_at = datetime.datetime.utcnow().isoformat() + "Z"
    run_hash = hash_result({**results, "generated_at": generated_at})
    return results, generated_at, run_hash


# --- Routes ---

@app.get("/")
def root():
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "status": "running",
    }


@app.post("/estimate", response_model=CarbonEstimateResponse)
def estimate(req: CarbonEstimateRequest):
    try:
        results, generated_at, run_hash = run_estimate(req)
        return CarbonEstimateResponse(
            project_name=req.project_name,
            **results,
            uncertainty_pct=int(UNCERTAINTY * 100),
            methodology="IPCC 2006 AFOLU Guidelines, Sentinel-2 SR Harmonized",
            generated_at=generated_at,
            run_hash=run_hash,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report")
def report(req: CarbonEstimateRequest):
    """Run the carbon pipeline and return a signed PDF report."""
    try:
        results, generated_at, run_hash = run_estimate(req)

        pdf_path = generate_report(
            project_name=req.project_name,
            results=results,
            generated_at=generated_at,
            run_hash=run_hash,
        )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"carbontrust_{req.project_name.replace(' ', '_')}.pdf",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))