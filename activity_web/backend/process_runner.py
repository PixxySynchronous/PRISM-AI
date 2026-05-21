from __future__ import annotations

import json
import sys
from pathlib import Path

from .app import (
    artifact_url,
    clip_url,
    _now_iso,
    _write_process_job_status,
    process_job_dir,
)
from .pipeline_loader import get_pipeline


def _build_clip_entries(job_id: str, summary: dict, output_path: Path) -> list[dict]:
    job_output = process_job_dir(job_id)
    clip_entries: list[dict] = []
    for clip in summary.get("clips", []):
        clip_path_value = clip.get("clip_path")
        clip_relative_path = None
        if clip_path_value:
            try:
                clip_relative_path = str(Path(clip_path_value).resolve().relative_to(job_output.resolve()))
            except Exception:
                clip_relative_path = None
        clip_entries.append(
            {
                **clip,
                "clip_relative_path": clip_relative_path,
                "clip_url": clip_url(job_id, clip_relative_path) if clip_relative_path else None,
            }
        )
    return clip_entries


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python -m activity_web.backend.process_runner <job_id> <input_path> <output_path>")

    job_id = sys.argv[1]
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    try:
        _write_process_job_status(job_id, "running")
        pipeline = get_pipeline()
        result = pipeline.process_video(video_path=input_path, output_dir=output_path, annotate=True)

        summary_path = Path(result["summary_path"])
        csv_path = Path(result["csv_path"])
        annotated_video = result.get("annotated_video")
        summary = json.loads(summary_path.read_text())
        clip_entries = _build_clip_entries(job_id, summary, output_path)

        _write_process_job_status(
            job_id,
            "completed",
            summary=summary,
            paths={
                "summary_json": str(summary_path),
                "csv": str(csv_path),
                "clip_dir": result["clip_dir"],
                "annotated_video": annotated_video,
            },
            download_urls={
                "summary_json": artifact_url(job_id, "summary"),
                "csv": artifact_url(job_id, "csv"),
                "annotated_video": artifact_url(job_id, "annotated"),
            },
            clips=clip_entries,
        )
    except Exception as exc:
        _write_process_job_status(job_id, "failed", error=str(exc))


if __name__ == "__main__":
    main()