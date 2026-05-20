# app/api.py
import hashlib
import datetime
import ee
from google import genai
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    UNCERTAINTY, GEMINI_MODEL
)
from app.carbon import estimate_carbon
from app.ndvi import initialize
from app.report import generate_report
from app.scheduler import lifespan, trigger_now
from app.db import get_db
from app.monitor import monitor_project

# Initialize Earth Engine once at startup
initialize()

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:8080", "null"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    biomass_coefficient_used: float
    methodology: str
    generated_at: str
    run_hash: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    bbox: list[float]               # [min_lon, min_lat, max_lon, max_lat]
    forest_type_code: int = 220     # USFS FIA FORTYPCD
    canopy_cover_pct: float = 60.0
    stand_age: int = 40
    basal_area_live: float = 25.0


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


# --- Existing Routes ---

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
            biomass_coefficient=results.get("biomass_coefficient_used", 53.0),
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


# --- Monitor Routes ---

@app.post("/projects", status_code=201)
async def create_project(payload: ProjectCreate):
    """Register a forest project for autonomous monitoring."""
    if len(payload.bbox) != 4:
        raise HTTPException(400, "bbox must be [min_lon, min_lat, max_lon, max_lat]")
    try:
        project = get_db().create_project(payload.model_dump())
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"status": "registered", "project": project}


@app.get("/projects")
async def list_projects():
    """List all registered forest projects."""
    return get_db().list_projects()


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a single project by ID."""
    project = get_db().get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project by ID."""
    if not get_db().delete_project(project_id):
        raise HTTPException(404, "Project not found")
    return {"status": "deleted"}


@app.get("/alerts")
async def get_alerts(project_id: Optional[str] = None):
    """Get all alerts, optionally filtered by project_id."""
    return get_db().get_alerts(project_id=project_id)


@app.get("/projects/{project_id}/alerts")
async def get_project_alerts(project_id: str):
    """Get all alerts for a specific project."""
    if not get_db().get_project(project_id):
        raise HTTPException(404, "Project not found")
    return get_db().get_alerts(project_id=project_id)


@app.get("/projects/{project_id}/ndvi-history")
async def get_ndvi_history(project_id: str):
    """Get NDVI history snapshots for a project."""
    if not get_db().get_project(project_id):
        raise HTTPException(404, "Project not found")
    return get_db().get_ndvi_history(project_id)


@app.post("/monitor/trigger")
async def trigger_monitor():
    """Manually trigger a monitoring cycle for all projects."""
    alerts = await trigger_now()
    return {
        "status": "complete",
        "alerts_generated": len(alerts),
        "alerts": alerts,
    }


@app.post("/monitor/trigger/{project_id}")
async def trigger_monitor_project(project_id: str):
    """Manually trigger a monitoring cycle for one specific project."""
    project = get_db().get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    alert = await monitor_project(project)
    return {
        "status": "complete",
        "alert": alert,
    }

# --- AI Interpretation ---

class InterpretRequest(BaseModel):
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
    forest_type_code: int
    canopy_cover_pct: float
    stand_age: int
    basal_area_live: float
    baseline_start: str
    baseline_end: str
    monitoring_start: str
    monitoring_end: str


@app.post("/interpret")
async def interpret(req: InterpretRequest):
    """Use Gemini to interpret carbon estimate results in plain English."""
    import asyncio
    from functools import partial

    prompt = f"""
You are an expert forest carbon scientist reviewing a satellite-based carbon verification report.
Analyze the following results and provide a concise, insightful interpretation in 3 short paragraphs.

Project: {req.project_name}
Forest Type Code: {req.forest_type_code} (100=Pine, 200=Spruce/Fir, 220=Loblolly Pine, 400=Oak/Hardwood, 500=Mixed)
Stand Age: {req.stand_age} years
Canopy Cover: {req.canopy_cover_pct}%
Basal Area: {req.basal_area_live} ft2/ac
Area: {req.area_ha} hectares

Baseline Period: {req.baseline_start} to {req.baseline_end}
Monitoring Period: {req.monitoring_start} to {req.monitoring_end}

Baseline NDVI: {req.baseline_ndvi}
Monitoring NDVI: {req.monitoring_ndvi}
NDVI Change: {req.ndvi_change}
Biomass Change: {req.biomass_change_tonnes} tonnes
Carbon Sequestered: {req.carbon_sequestered_tonnes_c} tonnes C
CO2e Sequestered: {req.co2e_tonnes} tonnes CO2e (range: {req.co2e_low} to {req.co2e_high})
Uncertainty: {req.uncertainty_pct}%

Write exactly 3 paragraphs with no headers or bullet points:

Paragraph 1 - Interpret the results: what does the CO2e number mean in practical terms? Is this forest performing well for its type and age? What is likely driving the sequestration level?

Paragraph 2 - Analyze the change between baseline and monitoring periods: what story do the NDVI and biomass numbers tell? Is this change significant, expected, or concerning?

Paragraph 3 - Flag any suspicious or unusual inputs or results. If everything looks plausible, say so and give a brief confidence assessment. Be specific.

Write in clear, professional language a non-scientist can understand. No markdown formatting.
""".strip()

    def call_gemini():
        client = genai.Client()
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text.strip()

    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, call_gemini)
        return {"interpretation": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")