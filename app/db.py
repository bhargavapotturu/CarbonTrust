"""
app/db.py — Lightweight JSON-backed persistence for CarbonTrust

Stores:
  - registered forest projects  → data/projects.json
  - monitoring alerts           → data/alerts.json
  - NDVI history snapshots      → data/ndvi_history.json

This is intentionally simple — swap for PostgreSQL/SQLite when scaling.
Thread-safe via file locking (filelock).

Install: pip install filelock
"""

import json
import uuid
import logging
from pathlib import Path
from filelock import FileLock

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

PROJECTS_FILE = DATA_DIR / "projects.json"
ALERTS_FILE = DATA_DIR / "alerts.json"
NDVI_HISTORY_FILE = DATA_DIR / "ndvi_history.json"


def _read(path: Path) -> list | dict:
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def _write(path: Path, data):
    lock = FileLock(str(path) + ".lock")
    with lock:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


class _DB:
    # ── Projects ──────────────────────────────

    def list_projects(self) -> list[dict]:
        return _read(PROJECTS_FILE)

    def get_project(self, project_id: str) -> dict | None:
        for p in self.list_projects():
            if p["id"] == project_id:
                return p
        return None

    def create_project(self, project: dict) -> dict:
        projects = self.list_projects()
        project["id"] = project.get("id") or str(uuid.uuid4())[:8]
        # Check duplicate name
        if any(p["name"] == project["name"] for p in projects):
            raise ValueError(f"Project '{project['name']}' already exists")
        projects.append(project)
        _write(PROJECTS_FILE, projects)
        logger.info(f"[DB] Created project {project['id']}: {project['name']}")
        return project

    def delete_project(self, project_id: str) -> bool:
        projects = self.list_projects()
        updated = [p for p in projects if p["id"] != project_id]
        if len(updated) == len(projects):
            return False
        _write(PROJECTS_FILE, updated)
        return True

    # ── Alerts ────────────────────────────────

    def save_alert(self, alert: dict) -> dict:
        alerts = _read(ALERTS_FILE)
        alert["alert_id"] = str(uuid.uuid4())[:8]
        alerts.append(alert)
        _write(ALERTS_FILE, alerts)
        return alert

    def get_alerts(self, project_id: str | None = None) -> list[dict]:
        alerts = _read(ALERTS_FILE)
        if project_id:
            alerts = [a for a in alerts if a["project_id"] == project_id]
        return sorted(alerts, key=lambda a: a["timestamp"], reverse=True)

    # ── NDVI History ──────────────────────────

    def append_ndvi_snapshot(self, project_id: str, snapshot: dict):
        history = _read(NDVI_HISTORY_FILE)
        if not isinstance(history, list):
            history = []
        snapshot["project_id"] = project_id
        history.append(snapshot)
        _write(NDVI_HISTORY_FILE, history)

    def get_ndvi_history(self, project_id: str) -> list[dict]:
        history = _read(NDVI_HISTORY_FILE)
        return [s for s in history if s["project_id"] == project_id]


# Singleton
_db_instance = _DB()

def get_db() -> _DB:
    return _db_instance