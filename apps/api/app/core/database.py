"""Database setup — lightweight JSON-file storage for analyses.

For a local-first tool we avoid requiring Postgres at startup.
Analyses are persisted as JSON files under data/analyses/.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.core.config import DATA_DIR

ANALYSES_DIR = DATA_DIR / "analyses"
ANALYSES_DIR.mkdir(parents=True, exist_ok=True)


def save_analysis(analysis: dict) -> str:
    analysis_id = analysis.get("id") or str(uuid.uuid4())
    analysis["id"] = analysis_id
    analysis["timestamp"] = analysis.get("timestamp") or datetime.now(timezone.utc).isoformat()
    path = ANALYSES_DIR / f"{analysis_id}.json"
    path.write_text(json.dumps(analysis, default=str, indent=2))
    return analysis_id


def get_analysis(analysis_id: str) -> dict | None:
    path = ANALYSES_DIR / f"{analysis_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_analyses(limit: int = 20) -> list[dict]:
    files = sorted(ANALYSES_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    results = []
    for f in files[:limit]:
        try:
            results.append(json.loads(f.read_text()))
        except Exception:
            continue
    return results
