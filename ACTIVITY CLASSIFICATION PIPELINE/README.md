# ACTIVITY CLASSIFICATION PIPELINE

This folder contains the end-to-end classroom video pipeline for:

1. Sampling 15 consecutive frames every 30 seconds from an input video.
2. Detecting faces in each sampled frame with InsightFace `buffalo_l`.
3. Grouping each face across the 15-frame window with a small IoU matcher.
4. Cropping each face very tightly into a clip.
5. Classifying each face clip with the fine-tuned 3D CNN R-18 checkpoint in `Activity monitoring/models/best_model`.

The current checkpoint is binary, so the output labels are:

- `low_engagement`
- `high_engagement`

## Main Script

Run the pipeline with:

```bash
/Users/satyam/Desktop/classroom-ai-project/.venv/bin/python "ACTIVITY CLASSIFICATION PIPELINE/student_activity_pipeline.py" \
  --video /path/to/classroom_video.mp4
```

By default, the script writes outputs to:

- `ACTIVITY CLASSIFICATION PIPELINE/outputs/<video_stem>_per_student_predictions.csv`
- `ACTIVITY CLASSIFICATION PIPELINE/outputs/<video_stem>_summary.json`
- `ACTIVITY CLASSIFICATION PIPELINE/outputs/classified_clips/<video_stem>/`
- `ACTIVITY CLASSIFICATION PIPELINE/outputs/<video_stem>_sampled_annotated.mp4`

## Notes

- The face detector defaults to `InsightFace buffalo_l` and runs on CPU by default.
- The classifier defaults to `Activity monitoring/models/best_model/3dcnn_r3d18_weighted.pt`.
- The pipeline samples 15 frames per window, then pads to 16 frames internally for the 3D CNN.
- Face crops are resized to 112×112 and normalized with Kinetics statistics.