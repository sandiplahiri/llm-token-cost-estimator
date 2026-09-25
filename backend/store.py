import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import Estimate

DB_PATH = Path(os.environ.get("ESTIMATOR_DB", "data/estimates.sqlite3"))


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS estimates (id TEXT PRIMARY KEY, name TEXT, updated TEXT, body TEXT)"
        )
        db.execute("CREATE TABLE IF NOT EXISTS catalog (id INTEGER PRIMARY KEY, body TEXT)")
        yield db


def save(estimate: Estimate):
    now = datetime.now(timezone.utc).isoformat()
    with connection() as db:
        db.execute(
            "INSERT OR REPLACE INTO estimates VALUES (?, ?, ?, ?)",
            (estimate.id, estimate.name, now, estimate.model_dump_json()),
        )
    return {"id": estimate.id, "updated": now}


def list_estimates():
    with connection() as db:
        return [
            dict(zip(("id", "name", "updated"), row))
            for row in db.execute("SELECT id, name, updated FROM estimates ORDER BY updated DESC")
        ]


def get(estimate_id: str):
    with connection() as db:
        row = db.execute("SELECT body FROM estimates WHERE id = ?", (estimate_id,)).fetchone()
    return Estimate.model_validate_json(row[0]) if row else None


def get_catalog():
    with connection() as db:
        row = db.execute("SELECT body FROM catalog WHERE id = 1").fetchone()
    return json.loads(row[0]) if row else None


def save_catalog(catalog):
    with connection() as db:
        db.execute("INSERT OR REPLACE INTO catalog VALUES (1, ?)", (json.dumps(catalog),))
