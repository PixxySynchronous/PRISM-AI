from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np


BACKEND_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BACKEND_DIR.parent / "runtime"
ATTENDANCE_DIR = RUNTIME_DIR / "attendance"
UPLOAD_DIR = ATTENDANCE_DIR / "uploads"
MARKED_DIR = ATTENDANCE_DIR / "marked"
STORE_PATH = ATTENDANCE_DIR / "attendance_store.json"
PHOTOS_PER_VIDEO = 12
FACE_SIMILARITY_THRESHOLD = 0.45


def ensure_attendance_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MARKED_DIR.mkdir(parents=True, exist_ok=True)
    ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _normalize(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        return vector
    return vector / norm


def _cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    a = _normalize(vector_a)
    b = _normalize(vector_b)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        return -1.0
    return float(np.dot(a, b) / denom)


@dataclass
class FaceSample:
    embedding: np.ndarray
    bbox: tuple[int, int, int, int]
    score: float


class AttendanceService:
    def __init__(self) -> None:
        ensure_attendance_dirs()
        self._face_analysis = None
            try:
                from insightface.app import FaceAnalysis
                model_name = os.environ.get("INSIGHTFACE_MODEL_NAME", "buffalo_l")
                self._face_analysis = FaceAnalysis(name=model_name, providers=["CPUExecutionProvider"])
                self._face_analysis.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)
            except MemoryError as mem_err:
                raise RuntimeError(
                    "Failed to initialize the face model (out of memory). "
                    "Consider increasing the instance memory, using a smaller model via the INSIGHTFACE_MODEL_NAME env var, "
                    "or running the attendance service on a machine with more RAM."
                ) from mem_err
            except Exception as exc:
                raise RuntimeError(f"Failed to initialize the face model: {exc}") from exc
        data.setdefault("students", [])
        data.setdefault("attendance", [])
        return data

    def _write_store(self, data: dict) -> None:
        ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
        STORE_PATH.write_text(json.dumps(data, indent=2))

    def _load_image(self, media_path: Path) -> np.ndarray | None:
        image = cv2.imread(str(media_path))
        return image

    def _sample_video_frames(self, media_path: Path) -> list[np.ndarray]:
        capture = cv2.VideoCapture(str(media_path))
        if not capture.isOpened():
            return []

        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frames: list[np.ndarray] = []

        if frame_count > 0:
            indices = np.linspace(0, max(0, frame_count - 1), min(PHOTOS_PER_VIDEO, frame_count), dtype=int)
            for frame_index in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
                ok, frame = capture.read()
                if ok and frame is not None:
                    frames.append(frame)
        else:
            while len(frames) < PHOTOS_PER_VIDEO:
                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                frames.append(frame)

        capture.release()
        return frames

    def _frames_from_media(self, media_path: Path) -> list[np.ndarray]:
        suffix = media_path.suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            image = self._load_image(media_path)
            return [image] if image is not None else []
        return self._sample_video_frames(media_path)

    def _detect_samples(self, frame: np.ndarray) -> list[FaceSample]:
        faces = self._get_face_analysis().get(frame)
        samples: list[FaceSample] = []
        for face in faces:
            embedding = getattr(face, "normed_embedding", None)
            if embedding is None:
                embedding = getattr(face, "embedding", None)
            if embedding is None:
                continue
            bbox = tuple(int(value) for value in face.bbox)
            samples.append(
                FaceSample(
                    embedding=_normalize(np.asarray(embedding, dtype=np.float32)),
                    bbox=bbox,
                    score=float(getattr(face, "det_score", 0.0)),
                )
            )
        return samples

    def _select_primary_sample(self, samples: list[FaceSample]) -> FaceSample | None:
        if not samples:
            return None
        return max(samples, key=lambda sample: (sample.score, (sample.bbox[2] - sample.bbox[0]) * (sample.bbox[3] - sample.bbox[1])))

    def _collect_embeddings_from_media(self, media_path: Path) -> list[np.ndarray]:
        embeddings: list[np.ndarray] = []
        for frame in self._frames_from_media(media_path):
            if frame is None:
                continue
            samples = self._detect_samples(frame)
            primary = self._select_primary_sample(samples)
            if primary is not None:
                embeddings.append(primary.embedding)
        return embeddings

    def _aggregate_embeddings(self, embeddings: list[np.ndarray]) -> np.ndarray:
        stacked = np.stack([_normalize(embedding) for embedding in embeddings], axis=0).astype(np.float32)
        mean_embedding = stacked.mean(axis=0)
        return _normalize(mean_embedding)

    def list_students(self) -> list[dict]:
        store = self._read_store()
        students = store.get("students", [])
        students.sort(key=lambda student: student.get("name", "").lower())
        return students

    def list_attendance(self, limit: int = 20) -> list[dict]:
        store = self._read_store()
        attendance = store.get("attendance", [])
        return attendance[-limit:][::-1]

    def delete_student(self, student_id: str) -> dict:
        store = self._read_store()
        students = store.get("students", [])
        attendance = store.get("attendance", [])

        target_index = next((index for index, student in enumerate(students) if student.get("student_id") == student_id), None)
        if target_index is None:
            raise KeyError(f"Student not found: {student_id}")

        removed_student = students.pop(target_index)
        removed_name = str(removed_student.get("name", "")).strip().lower()
        store["attendance"] = [
            row
            for row in attendance
            if str(row.get("student_name", "")).strip().lower() != removed_name
        ]
        self._write_store(store)

        return {
            "student": self._student_public(removed_student),
            "students": self.list_students(),
            "attendance": self.list_attendance(limit=20),
        }

    def enroll_student(self, student_name: str, media_paths: list[Path]) -> dict:
        normalized_name = student_name.strip()
        if not normalized_name:
            raise ValueError("student_name cannot be empty")
        if not media_paths:
            raise ValueError("Provide at least one photo or video for enrollment")

        collected_embeddings: list[np.ndarray] = []
        media_summaries: list[dict] = []
        for media_path in media_paths:
            embeddings = self._collect_embeddings_from_media(media_path)
            media_summaries.append(
                {
                    "file_name": media_path.name,
                    "frame_samples": len(embeddings),
                }
            )
            collected_embeddings.extend(embeddings)

        if not collected_embeddings:
            raise RuntimeError("No face embeddings could be extracted from the supplied media")

        prototype = self._aggregate_embeddings(collected_embeddings)
        store = self._read_store()
        students = store["students"]

        existing = next((student for student in students if student["name"].strip().lower() == normalized_name.lower()), None)
        if existing is None:
            existing = {
                "student_id": uuid.uuid4().hex[:12],
                "name": normalized_name,
                "observations": 0,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "embeddings": [],
                "prototype": [],
            }
            students.append(existing)

        previous_observations = int(existing.get("observations", 0))
        previous_embeddings = [np.asarray(embedding, dtype=np.float32) for embedding in existing.get("embeddings", [])]
        all_embeddings = previous_embeddings + [prototype]
        merged_prototype = self._aggregate_embeddings(all_embeddings)

        existing.update(
            {
                "name": normalized_name,
                "observations": previous_observations + len(collected_embeddings),
                "updated_at": _now_iso(),
                "prototype": merged_prototype.tolist(),
                "embeddings": [embedding.tolist() for embedding in all_embeddings],
                "media_samples": media_summaries,
            }
        )

        self._write_store(store)

        return {
            "student": self._student_public(existing),
            "media_samples": media_summaries,
        }

    def _student_public(self, student: dict) -> dict:
        return {
            "student_id": student.get("student_id"),
            "name": student.get("name"),
            "observations": int(student.get("observations", 0)),
            "updated_at": student.get("updated_at"),
        }

    def match_student(self, embedding: np.ndarray) -> dict:
        students = self.list_students()
        if not students:
            return {"match": None, "similarity": -1.0}

        best_student: dict | None = None
        best_similarity = -1.0
        normalized_embedding = _normalize(embedding)

        for student in students:
            prototype = np.asarray(student.get("prototype") or [], dtype=np.float32)
            if prototype.size == 0:
                continue
            similarity = _cosine_similarity(normalized_embedding, prototype)
            if similarity > best_similarity:
                best_similarity = similarity
                best_student = student

        if best_student is None:
            return {"match": None, "similarity": best_similarity}

        if best_similarity < FACE_SIMILARITY_THRESHOLD:
            return {"match": None, "similarity": best_similarity}

        return {"match": self._student_public(best_student), "similarity": best_similarity}

    def mark_attendance(self, media_path: Path) -> dict:
        if not media_path.exists():
            raise FileNotFoundError(f"File not found: {media_path}")

        suffix = media_path.suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            image = self._load_image(media_path)
            if image is None:
                raise RuntimeError("Could not read classroom photo")
            frame = image
        else:
            frames = self._sample_video_frames(media_path)
            if not frames:
                raise RuntimeError("Could not read classroom video")
            frame = frames[0]

        detections = self._detect_samples(frame)
        marked_frame = frame.copy()
        recognized: list[dict] = []
        unknown_faces = 0
        store = self._read_store()
        attendance_log = store["attendance"]
        seen_names: set[str] = set()

        for detection in detections:
            match = self.match_student(detection.embedding)
            x1, y1, x2, y2 = detection.bbox
            if match["match"] is None:
                unknown_faces += 1
                color = (0, 0, 255)
                label = f"Unknown {match['similarity']:.2f}"
            else:
                student = match["match"]
                color = (0, 200, 0)
                label = f"{student['name']} {match['similarity']:.2f}"
                if student["name"] not in seen_names:
                    seen_names.add(student["name"])
                    attendance_log.append(
                        {
                            "student_name": student["name"],
                            "recognized_at": _now_iso(),
                            "source": "classroom_photo",
                            "confidence": round(float(match["similarity"]), 4),
                        }
                    )
                recognized.append(
                    {
                        "student": student,
                        "confidence": round(float(match["similarity"]), 4),
                        "bbox": [x1, y1, x2, y2],
                    }
                )

            cv2.rectangle(marked_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                marked_frame,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

        store["attendance"] = attendance_log
        self._write_store(store)

        marked_name = f"{media_path.stem}_marked.jpg"
        marked_path = MARKED_DIR / marked_name
        cv2.imwrite(str(marked_path), marked_frame)

        return {
            "recognized": recognized,
            "unknown_faces": unknown_faces,
            "marked_path": str(marked_path),
            "marked_url": f"/api/attendance/artifacts/{marked_name}",
            "roster": self.list_students(),
            "attendance_log": self.list_attendance(limit=20),
        }


@lru_cache(maxsize=1)
def get_attendance_service() -> AttendanceService:
    return AttendanceService()
