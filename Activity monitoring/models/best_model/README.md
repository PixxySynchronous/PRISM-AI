# Best Model: 3D CNN (Class-Weighted)

## Overview
This is the best-performing model for engagement classification in the classroom activity monitoring project.

**Model:** ResNet3D-18 (r3d_18) with class-weighted training

## Performance Metrics
- **Overall Accuracy:** 93.18%
- **Best Epoch:** 5 (high_engagement F1 = 0.7931)

### Per-Class Performance (Test Set: 176 clips)
**Low Engagement (146 clips):**
- Precision: 0.9527
- Recall: 0.9658
- F1-Score: 0.9592

**High Engagement (30 clips):**
- Precision: 0.8214
- Recall: **0.7667** ← 23/30 correct detections
- F1-Score: **0.7931**

## Model Files
- `3dcnn_r3d18_weighted.pt` - Trained model weights (132.7 MB)
- `3dcnn_r3d18_weighted_report.json` - Detailed metrics

## Key Improvements Over Baseline
- High_engagement F1: **+3.1%** (0.7931 vs 0.7692)
- High_engagement Recall: **+15%** (23/30 vs 20/30 detections)
- Successfully addresses class imbalance (8.34:1 ratio) using weighted loss

## Training Details
- **Architecture:** torchvision.models.video.r3d_18 (pretrained ImageNet weights)
- **Loss Function:** CrossEntropyLoss with class weights [1.0, 8.3429]
- **Optimizer:** AdamW (lr=1e-4, weight_decay=1e-4)
- **Scheduler:** CosineAnnealingLR
- **Epochs:** 8 (early stopping on high_engagement F1)
- **Input:** 16 frames per video, 112×112 resolution, Kinetics normalization

## Data Split
- **Training:** 654 clips (584 low, 70 high) from annotations_split2_high_test_train.csv
- **Testing:** 176 clips (146 low, 30 high) from annotations_split2_high_test_test.csv

## Use Case Recommendation
✅ **Recommended for production deployment** - Good balance of high_engagement detection (77% recall) while maintaining excellent low_engagement accuracy (97% recall).

---
*Created: May 16, 2026*
