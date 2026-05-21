import cv2
import os
from pathlib import Path
from insightface.app import FaceAnalysis

VIDEO = "ACTIVITY CLASSIFICATION PIPELINE/outputs/video_3_first_10s_5fps.mp4"
OUT_DIR = Path("ACTIVITY CLASSIFICATION PIPELINE/outputs/debug_face_crops")
OUT_DIR.mkdir(parents=True, exist_ok=True)

face_det_size = 640
face_det_thresh = 0.35
crop_padding = 0.5
sample_frames = 15

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(face_det_size, face_det_size), det_thresh=face_det_thresh)

cap = cv2.VideoCapture(VIDEO)
if not cap.isOpened():
    raise SystemExit("Cannot open video")

saved = []
for i in range(sample_frames):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if not ret:
        break
    dets = app.get(frame)
    for j, det in enumerate(dets):
        x1, y1, x2, y2 = [int(v) for v in det.bbox]
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        pad_x = int(w * crop_padding)
        pad_y = int(h * crop_padding)
        x1p = max(0, x1 - pad_x)
        y1p = max(0, y1 - pad_y)
        x2p = min(frame.shape[1] - 1, x2 + pad_x)
        y2p = min(frame.shape[0] - 1, y2 + pad_y)
        crop = frame[y1p:y2p, x1p:x2p]
        fname = OUT_DIR / f"frame_{i:02d}_det_{j:02d}.jpg"
        cv2.imwrite(str(fname), crop)
        saved.append(fname.name)

cap.release()

# write simple index
index = OUT_DIR / "index.html"
with index.open("w") as f:
    f.write("<html><body><h1>Face crops (first window)</h1>\n")
    for p in saved:
        f.write(f'<div style="display:inline-block;margin:8px;text-align:center"><img src="{p}" style="max-width:200px;display:block"/><small>{p}</small></div>\n')
    f.write("</body></html>")

print('Saved', len(saved), 'crops to', OUT_DIR)
print('Index:', index)
