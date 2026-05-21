from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from .config import (
    BACKEND_DIR,
    RUNTIME_DIR,
    UPLOAD_DIR,
    OUTPUT_DIR,
    ATTENDANCE_DIR,
    ALLOWED_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
)

app = Flask(
    __name__,
    template_folder=str(BACKEND_DIR / "templates"),
    static_folder=str(BACKEND_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024 * 1024


def ensure_runtime_dirs() -> None:
    # Create the configured runtime directories
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (ATTENDANCE_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    (ATTENDANCE_DIR / "marked").mkdir(parents=True, exist_ok=True)


def allowed_video(filename: str) -> bool:
    return Path(filename.lower()).suffix in ALLOWED_EXTENSIONS


def allowed_media(filename: str) -> bool:
    return Path(filename.lower()).suffix in ALLOWED_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS


def artifact_url(job_id: str, kind: str) -> str:
    return f"/api/jobs/{job_id}/download/{kind}"


def clip_url(job_id: str, relative_path: str) -> str:
    return f"/api/jobs/{job_id}/clips/{relative_path}"


def attendance_artifact_url(filename: str) -> str:
    return f"/api/attendance/artifacts/{filename}"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/attendance/status")
def attendance_status():
    import importlib.util
    from .attendance_service import get_attendance_service

    service = get_attendance_service()
    # Check whether heavy packages are available without importing them directly
    pkg_check = {
        "cv2": bool(importlib.util.find_spec("cv2")),
        "insightface": bool(importlib.util.find_spec("insightface")),
        "onnxruntime": bool(importlib.util.find_spec("onnxruntime")),
    }
    students = service.list_students()
    return jsonify({"ok": True, "model_ready": pkg_check.get("insightface") and pkg_check.get("onnxruntime"), "packages": pkg_check, "students_count": len(students)}), 200


@app.get("/api/attendance/roster")
def attendance_roster():
    from .attendance_service import get_attendance_service

    service = get_attendance_service()
    return jsonify({"ok": True, "students": service.list_students(), "attendance": service.list_attendance(limit=20)})


@app.delete("/api/attendance/students/<student_id>")
def attendance_delete_student(student_id: str):
    from .attendance_service import get_attendance_service

    service = get_attendance_service()
    try:
        result = service.delete_student(student_id)
    except KeyError:
        return jsonify({"ok": False, "error": "Student not found."}), 404
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    return jsonify({"ok": True, **result})


@app.post("/api/attendance/enroll")
def attendance_enroll():
    from .attendance_service import get_attendance_service

    uploaded_files = request.files.getlist("media")
    student_name = request.form.get("student_name", "").strip()

    if not student_name:
        return jsonify({"ok": False, "error": "Enter a student name."}), 400
    if not uploaded_files:
        return jsonify({"ok": False, "error": "Upload at least one photo or video."}), 400

    service = get_attendance_service()
    saved_paths: list[Path] = []
    for uploaded_file in uploaded_files:
        if not uploaded_file or not uploaded_file.filename:
            continue
        if not allowed_media(uploaded_file.filename):
            return jsonify({"ok": False, "error": "Use image or video files for enrollment."}), 400
        media_name = secure_filename(uploaded_file.filename)
        media_path = ATTENDANCE_DIR / "uploads" / f"{uuid.uuid4().hex[:12]}_{media_name}"
        media_path.parent.mkdir(parents=True, exist_ok=True)
        uploaded_file.save(media_path)
        saved_paths.append(media_path)

    if not saved_paths:
        return jsonify({"ok": False, "error": "No valid media files were uploaded."}), 400

    try:
        result = service.enroll_student(student_name=student_name, media_paths=saved_paths)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    return jsonify({"ok": True, **result, "students": service.list_students()})


@app.post("/api/attendance/mark")
def attendance_mark():
    from .attendance_service import get_attendance_service

    uploaded_file = request.files.get("photo")
    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"ok": False, "error": "Upload a classroom photo first."}), 400

    if not allowed_media(uploaded_file.filename):
        return jsonify({"ok": False, "error": "Use an image or video file for attendance marking."}), 400

    service = get_attendance_service()
    photo_name = secure_filename(uploaded_file.filename)
    photo_path = ATTENDANCE_DIR / "uploads" / f"{uuid.uuid4().hex[:12]}_{photo_name}"
    photo_path.parent.mkdir(parents=True, exist_ok=True)
    uploaded_file.save(photo_path)

    try:
        result = service.mark_attendance(photo_path)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    result["marked_url"] = attendance_artifact_url(Path(result["marked_url"]).name)
    return jsonify({"ok": True, **result})


@app.post("/api/process")
def process_video():
    ensure_runtime_dirs()

    from .pipeline_loader import get_pipeline

    uploaded_file = request.files.get("video")
    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"ok": False, "error": "Upload a video file first."}), 400

    if not allowed_video(uploaded_file.filename):
        return jsonify({"ok": False, "error": "Use an .mp4, .mov, .avi, .mkv, or .webm file."}), 400

    job_id = uuid.uuid4().hex[:12]
    filename = secure_filename(uploaded_file.filename)
    input_path = UPLOAD_DIR / f"{job_id}_{filename}"
    output_path = OUTPUT_DIR / job_id

    uploaded_file.save(input_path)

    try:
        pipeline = get_pipeline()
        result = pipeline.process_video(video_path=input_path, output_dir=output_path, annotate=True)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    summary = result["summary"]
    job_output = OUTPUT_DIR / job_id
    clip_entries = []
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
    response = {
        "ok": True,
        "job_id": job_id,
        "summary": summary,
        "paths": {
            "summary_json": result["summary_path"],
            "csv": result["csv_path"],
            "clip_dir": result["clip_dir"],
            "annotated_video": result["annotated_video"],
        },
        "download_urls": {
            "summary_json": artifact_url(job_id, "summary"),
            "csv": artifact_url(job_id, "csv"),
            "annotated_video": artifact_url(job_id, "annotated"),
        },
        "clips": clip_entries,
    }
    return jsonify(response)


@app.get("/api/jobs/<job_id>/download/<kind>")
def download_artifact(job_id: str, kind: str):
    job_output = OUTPUT_DIR / job_id
    summary_path = next(job_output.glob("*_summary.json"), None)
    csv_path = next(job_output.glob("*_per_student_predictions.csv"), None)
    annotated_path = next(job_output.glob("*_sampled_annotated.mp4"), None)

    if kind == "summary" and summary_path is not None and summary_path.exists():
        return send_file(summary_path, as_attachment=True, download_name=summary_path.name)
    if kind == "csv" and csv_path is not None and csv_path.exists():
        return send_file(csv_path, as_attachment=True, download_name=csv_path.name)
    if kind == "annotated" and annotated_path is not None and annotated_path.exists():
        return send_file(annotated_path, as_attachment=True, download_name=annotated_path.name)

    return jsonify({"ok": False, "error": "Artifact not found."}), 404


@app.get("/api/jobs/<job_id>/clips/<path:relative_path>")
def serve_clip(job_id: str, relative_path: str):
    job_output = OUTPUT_DIR / job_id
    clip_path = (job_output / relative_path).resolve()
    try:
        clip_path.relative_to(job_output.resolve())
    except Exception:
        return jsonify({"ok": False, "error": "Clip not found."}), 404

    if not clip_path.exists() or not clip_path.is_file():
        return jsonify({"ok": False, "error": "Clip not found."}), 404

    return send_file(clip_path, as_attachment=False, download_name=clip_path.name)


@app.get("/api/attendance/artifacts/<path:filename>")
def serve_attendance_artifact(filename: str):
    artifact_path = (ATTENDANCE_DIR / "marked" / filename).resolve()
    marked_dir = (ATTENDANCE_DIR / "marked").resolve()
    try:
        artifact_path.relative_to(marked_dir)
    except Exception:
        return jsonify({"ok": False, "error": "Artifact not found."}), 404

    if not artifact_path.exists() or not artifact_path.is_file():
        return jsonify({"ok": False, "error": "Artifact not found."}), 404

    return send_file(artifact_path, as_attachment=False, download_name=artifact_path.name)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
