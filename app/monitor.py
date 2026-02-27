"""
app/monitor.py — Autonomous Project Monitor for CarbonTrust

Monitors registered forest projects by:
1. Fetching NDVI snapshots from Sentinel-2 via GEE
2. Comparing against historical baseline
3. Detecting anomalies: deforestation, fire, degradation
4. Generating structured alerts with severity levels
5. Using Gemini to produce a natural-language summary
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import google.generativeai as genai

from app.config import (
    NDVI_ANOMALY_THRESHOLD,
    NDVI_FIRE_THRESHOLD,
    NDVI_DEFORESTATION_THRESHOLD,
    MONITOR_LOOKBACK_DAYS,
    GEMINI_MODEL,
)
from app.ndvi import compute_ndvi  # your existing NDVI function
from app.db import get_db          # lightweight JSON/SQLite store (see db.py)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Data models (plain dicts — swap for Pydantic)
# ──────────────────────────────────────────────

def make_alert(
    project_id: str,
    severity: str,          # "info" | "warning" | "critical"
    anomaly_type: str,      # "degradation" | "fire" | "deforestation" | "recovery"
    ndvi_current: float,
    ndvi_baseline: float,
    delta: float,
    summary: str,
    timestamp: Optional[str] = None,
) -> dict:
    return {
        "project_id": project_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "anomaly_type": anomaly_type,
        "ndvi_current": round(ndvi_current, 4),
        "ndvi_baseline": round(ndvi_baseline, 4),
        "ndvi_delta": round(delta, 4),
        "summary": summary,
    }


# ──────────────────────────────────────────────
# Anomaly classification
# ──────────────────────────────────────────────

def classify_anomaly(ndvi_current: float, ndvi_baseline: float) -> Optional[dict]:
    """
    Returns anomaly metadata dict if an anomaly is detected, else None.

    Thresholds (configurable in config.py):
      - NDVI drop > 0.30  → deforestation (critical)
      - NDVI drop > 0.15  → fire / severe degradation (critical)
      - NDVI drop > 0.08  → degradation (warning)
      - NDVI gain > 0.10  → recovery (info)
    """
    delta = ndvi_current - ndvi_baseline

    if delta <= -NDVI_DEFORESTATION_THRESHOLD:
        return {
            "severity": "critical",
            "anomaly_type": "deforestation",
            "delta": delta,
        }
    elif delta <= -NDVI_FIRE_THRESHOLD:
        return {
            "severity": "critical",
            "anomaly_type": "fire_or_severe_degradation",
            "delta": delta,
        }
    elif delta <= -NDVI_ANOMALY_THRESHOLD:
        return {
            "severity": "warning",
            "anomaly_type": "degradation",
            "delta": delta,
        }
    elif delta >= 0.10:
        return {
            "severity": "info",
            "anomaly_type": "recovery",
            "delta": delta,
        }
    return None  # no significant change


# ──────────────────────────────────────────────
# Gemini summary generation
# ──────────────────────────────────────────────

def generate_alert_summary(project: dict, anomaly: dict, ndvi_current: float, ndvi_baseline: float) -> str:
    """Calls Gemini Flash to produce a human-readable alert summary."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
You are an AI carbon credit verification assistant analyzing satellite NDVI data.

Forest Project: {project['name']} (ID: {project['id']})
Location: {project.get('description', 'Virginia, USA')}
Boundary: {project['bbox']}

Current NDVI: {ndvi_current:.4f}
Baseline NDVI (30-day avg): {ndvi_baseline:.4f}
NDVI Change: {anomaly['delta']:+.4f}
Anomaly Type: {anomaly['anomaly_type']}
Severity: {anomaly['severity']}

Write a concise (2-3 sentence) alert summary for a carbon credit verifier. 
Include: what happened, likely cause, and recommended action.
Be factual and specific. No markdown.
""".strip()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini summary failed: {e}")
        delta_pct = abs(anomaly["delta"] / ndvi_baseline * 100) if ndvi_baseline else 0
        return (
            f"{anomaly['anomaly_type'].replace('_', ' ').title()} detected in project "
            f"'{project['name']}'. NDVI dropped {delta_pct:.1f}% from baseline "
            f"({ndvi_baseline:.3f} → {ndvi_current:.3f}). Manual review recommended."
        )


# ──────────────────────────────────────────────
# Core monitor function
# ──────────────────────────────────────────────

async def monitor_project(project: dict) -> Optional[dict]:
    """
    Runs a single monitoring cycle for one project.

    Args:
        project: dict with keys: id, name, bbox, forest_type_code,
                 canopy_cover_pct, stand_age, basal_area_live

    Returns:
        Alert dict if anomaly detected, else None.
    """
    project_id = project["id"]
    bbox = project["bbox"]  # [min_lon, min_lat, max_lon, max_lat]

    now = datetime.now(timezone.utc)

    # Date windows
    current_end = now.strftime("%Y-%m-%d")
    current_start = (now - timedelta(days=15)).strftime("%Y-%m-%d")
    baseline_end = (now - timedelta(days=15)).strftime("%Y-%m-%d")
    baseline_start = (now - timedelta(days=15 + MONITOR_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    logger.info(f"[Monitor] Project {project_id}: fetching NDVI ({current_start} → {current_end})")

    try:
        ndvi_current = await compute_ndvi(bbox, current_start, current_end)
        ndvi_baseline = await compute_ndvi(bbox, baseline_start, baseline_end)
    except Exception as e:
        logger.error(f"[Monitor] GEE error for project {project_id}: {e}")
        return None

    if ndvi_current is None or ndvi_baseline is None:
        logger.warning(f"[Monitor] No NDVI data for project {project_id} — likely cloudy period.")
        return None

    # Store NDVI history
    db = get_db()
    db.append_ndvi_snapshot(project_id, {
        "timestamp": now.isoformat(),
        "ndvi": ndvi_current,
        "window": f"{current_start}/{current_end}",
    })

    # Classify anomaly
    anomaly = classify_anomaly(ndvi_current, ndvi_baseline)
    if anomaly is None:
        logger.info(f"[Monitor] Project {project_id}: no anomaly (NDVI {ndvi_current:.4f}, baseline {ndvi_baseline:.4f})")
        return None

    # Generate Gemini summary
    summary = generate_alert_summary(project, anomaly, ndvi_current, ndvi_baseline)

    alert = make_alert(
        project_id=project_id,
        severity=anomaly["severity"],
        anomaly_type=anomaly["anomaly_type"],
        ndvi_current=ndvi_current,
        ndvi_baseline=ndvi_baseline,
        delta=anomaly["delta"],
        summary=summary,
    )

    # Persist alert
    db.save_alert(alert)

    logger.warning(
        f"[Monitor] ALERT [{alert['severity'].upper()}] project={project_id} "
        f"type={alert['anomaly_type']} delta={alert['ndvi_delta']:+.4f}"
    )
    return alert


async def run_all_monitors() -> list[dict]:
    """
    Runs monitoring cycle for all registered projects.
    Called by the scheduler on a cron interval.
    Returns list of alerts generated (may be empty).
    """
    db = get_db()
    projects = db.list_projects()
    alerts = []

    if not projects:
        logger.info("[Monitor] No registered projects to monitor.")
        return alerts

    logger.info(f"[Monitor] Starting cycle — {len(projects)} project(s)")

    for project in projects:
        try:
            alert = await monitor_project(project)
            if alert:
                alerts.append(alert)
        except Exception as e:
            logger.error(f"[Monitor] Unhandled error for project {project.get('id')}: {e}")

    logger.info(f"[Monitor] Cycle complete — {len(alerts)} alert(s) generated")
    return alerts