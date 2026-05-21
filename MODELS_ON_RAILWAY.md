# ML Models on Railway - Setup Guide

This project requires large pre-trained ML models (torch, insightface, ultralytics). Since these shouldn't be in Git and are too large for Railway's build system, here's how to handle them.

## Option 1: AWS S3 (Recommended for Production)

### Setup

1. **Upload models to S3**
   ```bash
   # Create an S3 bucket
   aws s3 mb s3://your-classroom-ai-models
   
   # Upload your models
   aws s3 cp "ACTIVITY CLASSIFICATION PIPELINE/models/" s3://your-classroom-ai-models/activity/ --recursive
   aws s3 cp "other stuff/models/" s3://your-classroom-ai-models/other/ --recursive
   ```

2. **Create IAM User for Railway**
   - Go to AWS IAM console
   - Create a new user: `railway-models`
   - Attach policy:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-classroom-ai-models",
           "arn:aws:s3:::your-classroom-ai-models/*"
         ]
       }
     ]
   }
   ```
   - Generate access keys

3. **Add to Railway Variables**
   ```
   AWS_ACCESS_KEY_ID=your_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_S3_BUCKET=your-classroom-ai-models
   AWS_REGION=us-east-1
   ```

4. **Update `pipeline_loader.py`** to download models from S3 on startup:
   ```python
   import boto3
   import os
   
   def download_models_from_s3():
       s3 = boto3.client('s3')
       bucket = os.environ.get('AWS_S3_BUCKET')
       prefix = 'activity/'
       
       # Download if not already cached
       models_dir = Path('/data/activity_runtime/models')
       if not models_dir.exists():
           models_dir.mkdir(parents=True, exist_ok=True)
           # Download from S3
           response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
           for obj in response.get('Contents', []):
               local_path = models_dir / obj['Key'].replace(prefix, '')
               local_path.parent.mkdir(parents=True, exist_ok=True)
               s3.download_file(bucket, obj['Key'], str(local_path))
   ```

### Pros & Cons
✅ Scalable, works for any size  
✅ Fast downloads  
❌ Costs money (small for occasional use)  
❌ Slightly slower first startup  

---

## Option 2: Railway Persistent Volumes + Manual Upload

### Setup

1. **Create persistent volume in Railway**
   - In Railway dashboard → Service → Data
   - Add volume at `/data` (already recommended)

2. **Upload models via your app**
   - Add an admin endpoint to upload models:
   ```python
   @app.route('/admin/upload-models', methods=['POST'])
   def upload_models():
       # Upload models manually via web form
       file = request.files['file']
       model_path = RUNTIME_DIR / 'models' / file.filename
       file.save(model_path)
       return {'status': 'uploaded'}
   ```

3. **Load from persistent storage**
   ```python
   # In pipeline_loader.py
   MODEL_PATH = RUNTIME_DIR / 'models'
   MODEL_PATH.mkdir(parents=True, exist_ok=True)
   ```

### Pros & Cons
✅ No external costs  
✅ Simple setup  
✅ Accessible from web UI  
❌ Manual upload needed  
❌ Slow initial startup  
❌ 2GB volume limit  

---

## Option 3: Pre-trained Models Auto-Download (Torch Hub / Ultralytics)

If your models can be automatically downloaded from public sources:

```python
# In requirements.txt, add
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0  # Auto-downloads YOLOv5/v8 on first use

# In your app, models auto-download to ~/.cache on first load
# For Railway, persist the cache:
ENV TORCH_HOME=/data/activity_runtime/torch_cache
ENV HF_HOME=/data/activity_runtime/huggingface_cache
```

### Pros & Cons
✅ Zero setup  
✅ Automatic  
✅ Free  
❌ Slower first startup (5-10 min)  
❌ Requires internet  

---

## Option 4: Docker Layer Caching (For Small Models < 500MB)

If your total models are < 500MB:

1. **Commit models to Git** (git-lfs optional)
   ```bash
   git add "ACTIVITY CLASSIFICATION PIPELINE/models/"
   git add "other stuff/models/"
   git commit -m "add model files"
   git push
   ```

2. **Update .dockerignore** to NOT exclude models:
   ```bash
   # Remove "models" from .dockerignore
   ```

3. **Railway builds and caches the layer**
   - First build: slow
   - Subsequent deploys: fast (uses cache)

### Pros & Cons
✅ Simple  
✅ Fast  
❌ Git repo bloats  
❌ Slow first build  
❌ Max 500MB recommended  

---

## Recommended Setup for This Project

Based on your project size, **use Option 1 (S3) or Option 2 (Persistent Volume)**:

### If models < 100MB total:
→ Commit to Git (Option 4) + Option 3 auto-download fallback

### If models 100MB - 1GB:
→ Use Persistent Volume (Option 2) + upload via web admin panel

### If models > 1GB:
→ Use S3 (Option 1) or split into multiple layers

---

## Quick Start: Using Option 3 (Auto-Download)

The easiest for Railway:

1. **Update requirements.txt**
   ```
   Flask==3.0.0
   gunicorn
   python-dotenv
   numpy
   Pillow
   opencv-python-headless
   ultralytics>=8.0.0  # Auto-downloads models
   insightface  # Downloads from Hugging Face
   torch>=2.0.0  # Auto-caches models
   torchvision>=0.15.0
   ```

2. **Set cache directories as env vars in Railway:**
   ```
   TORCH_HOME=/data/activity_runtime/torch_cache
   HF_HOME=/data/activity_runtime/huggingface_cache
   ULTRALYTICS_HOME=/data/activity_runtime/ultralytics
   ```

3. **Deploy and wait for first startup** (5-10 minutes for downloads)

4. **Models persist** in Railway volume for subsequent starts

---

## Troubleshooting

### Models downloading but app crashes
- Check Railway **Logs** tab
- Ensure `/data` volume exists and has write permissions
- Increase Railway tier if out of disk/memory

### Build times out
- Reduce model download size
- Use S3 option instead
- Pre-download models on local machine and use Persistent Volume option

### Slow first startup
- Expected: 5-10 minutes on first request
- Use Railway **Jobs** feature for background model download
- Consider keeping app tier upgrade to cache models faster

---

## Verify Models Loaded

Once deployed, check if models are loading:

```bash
# In Railway Logs, look for:
# ✓ Model loaded from cache
# ✓ Pipeline initialized successfully
# ✗ Model download failed (check internet/permissions)

# Or add a test endpoint:
@app.route('/api/health')
def health():
    return {'status': 'ok', 'models_loaded': True}
```

Check: `curl https://your-app.railway.app/api/health`
