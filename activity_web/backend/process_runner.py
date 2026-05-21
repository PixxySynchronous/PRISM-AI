from __future__ import annotations

import json
import contextlib
import io
import re
import sys
from pathlib import Path

from .job_utils import (
    build_process_console_output,
    process_job_dir,
    update_process_job_status,
    write_process_job_status,
)
from .pipeline_loader import get_pipeline


def artifact_url(job_id: str, kind: str) -> str:
    return f"/api/jobs/{job_id}/download/{kind}"


def clip_url(job_id: str, relative_path: str) -> str:
    return f"/api/jobs/{job_id}/clips/{relative_path}"


PROGRESS_PATTERN = re.compile(r"Progress:\s*\[(?P<bar>[#\-\?]+)\]\s*(?P<current>\d+)/(?:\s*)?(?P<total>\d+)\s*\((?P<pct>[\d.]+)%\)")


class ProgressCapture(io.TextIOBase):
    def __init__(self, job_id: str):
        super().__init__()
        self.job_id = job_id
        self.buffer = ""
        self.last_progress_key: tuple[int, int, float] | None = None

    def write(self, text: str) -> int:
        if not text:
            return 0
        self.buffer += text
        self._flush_progress_matches()
        return len(text)

    def flush(self) -> None:
        self._flush_progress_matches()

    def _flush_progress_matches(self) -> None:
        matches = list(PROGRESS_PATTERN.finditer(self.buffer))
        if not matches:
            return

        for match in matches:
            current = int(match.group("current"))
            total = int(match.group("total"))
            percent = float(match.group("pct"))
            progress_key = (current, total, percent)
            if progress_key == self.last_progress_key:
                continue
            self.last_progress_key = progress_key
            update_process_job_status(
                self.job_id,
                "running",
                progress={
                    "current_frame": current,
                    "total_frames": total,
                    "percent": percent,
                },
            )

        self.buffer = ""


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
        write_process_job_status(job_id, "running")
        pipeline = get_pipeline()
        progress_capture = ProgressCapture(job_id)
        with contextlib.redirect_stdout(progress_capture), contextlib.redirect_stderr(progress_capture):
            result = pipeline.process_video(video_path=input_path, output_dir=output_path, annotate=True)

        summary_path = Path(result["summary_path"])
        csv_path = Path(result["csv_path"])
        annotated_video = result.get("annotated_video")
        summary = json.loads(summary_path.read_text())
        clip_entries = _build_clip_entries(job_id, summary, output_path)

        write_process_job_status(
            job_id,
            "completed",
            summary=summary,
            console_output=build_process_console_output(summary, result),
            progress={
                "current_frame": summary.get("total_frames", 0),
                "total_frames": summary.get("total_frames", 0),
                "percent": 100.0,
            },
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
        write_process_job_status(job_id, "failed", error=str(exc))


if __name__ == "__main__":
    main()