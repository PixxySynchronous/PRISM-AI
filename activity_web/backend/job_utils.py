from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import OUTPUT_DIR


def process_job_dir(job_id: str) -> Path:
    return OUTPUT_DIR / job_id


def process_job_status_path(job_id: str) -> Path:
    return process_job_dir(job_id) / "job_status.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_process_job_status(job_id: str, status: str, **payload) -> None:
    job_dir = process_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    status_path = process_job_status_path(job_id)
    data = {
        "ok": True,
        "job_id": job_id,
        "status": status,
        "updated_at": now_iso(),
        **payload,
    }
    status_path.write_text(json.dumps(data, indent=2))


def read_process_job_status(job_id: str) -> dict | None:
    status_path = process_job_status_path(job_id)
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text())
    except Exception:
        return None


def build_process_console_output(summary: dict, result: dict) -> str:
    lines = [json.dumps(summary, indent=2), f"Saved summary: {result['summary_path']}", f"Saved CSV: {result['csv_path']}", f"Saved clips: {result['clip_dir']}"]
    if result.get("annotated_video"):
        lines.append(f"Saved annotated video: {result['annotated_video']}")
    return "\n".join(lines)