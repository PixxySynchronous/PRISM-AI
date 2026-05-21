# Deploy to Railway

This guide explains how to deploy the classroom-ai-project to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your project to GitHub (Railway connects to GitHub for CI/CD)
3. **Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   ```

## Quick Setup

### Option 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/classroom-ai-project.git
   git push -u origin main
   ```

2. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway with your GitHub account
   - Select your `classroom-ai-project` repository
   - Railway will automatically detect the Dockerfile

3. **Configure Environment Variables**
   - In Railway project dashboard, go to **Variables**
   - Add these variables:
     ```
     PORT=8080
     ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime
     PYTHONUNBUFFERED=1
     ```

4. **Add Persistent Storage** (for model files and runtime data)
   - In Railway dashboard, click your service
   - Go to **Data** tab
   - Add a volume:
     - Mount Path: `/data`
     - This persists your activity_runtime directory

5. **Deploy**
   - Railway automatically deploys when you push to GitHub
   - Check deployment status in the **Deployments** tab

### Option 2: Deploy Using Railway CLI

```bash
# Login to Railway
railway login

# Initialize Railway project
railway init

# Set up service name
railway service add

# Add variables
railway variables set PORT=8080
railway variables set ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime
railway variables set PYTHONUNBUFFERED=1

# Deploy
railway up
```

## Important Notes

### Build Size & Duration
- Your dependencies (torch, torchvision, insightface, ultralytics) are large (~2-3GB)
- Initial build may take **10-20 minutes**
- Railway has generous build timeouts, but be patient

### Storage Considerations
- **Models**: Should ideally be fetched from a cloud storage (S3, Google Cloud Storage) or committed to Git if <100MB
- **Runtime Data**: Upload outputs and temporary files go to the persistent volume
- **Persistent Volume**: Currently configured at `/data` with 2GB limit (can upgrade)

### Memory & CPU
- Railway starter tier provides **2GB RAM** and **shared CPU**
- For heavy ML inference (like activity classification), consider upgrading to a higher tier
- Monitor in the **Logs** and **Metrics** tab

### Limiting Model Downloads
The Dockerfile installs large pre-trained models. To optimize:

**Option A: Skip Model Download in Dockerfile** (if models are on S3/Cloud)
```dockerfile
# Update Dockerfile to not auto-download models
# Instead, load them from remote storage on first request
```

**Option B: Pre-Package Models** (if <500MB total)
```bash
# Commit model files to Git
git add ACTIVITY\ CLASSIFICATION\ PIPELINE/models/
git add other\ stuff/models/
git commit -m "add ML models"
git push
```

**Option C: Use S3 for Models** (recommended for >500MB)
- Upload models to S3
- Update `pipeline_loader.py` to download from S3 on startup
- Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in Railway Variables

## Verify Deployment

Once deployed, Railway provides you with a public URL (e.g., `https://your-project.railway.app`).

Test your deployment:
```bash
# Check health
curl https://your-project.railway.app/

# Check logs in Railway dashboard for any errors
```

## Troubleshooting

### Build Fails / Timeout
- The large ML libraries sometimes fail to build
- Railway automatically retries failed builds
- Check **Build Logs** tab for specific errors
- Try reducing model complexity or pre-fetching models from S3

### Out of Memory Errors
- Increase Railway tier to get more RAM
- Implement model caching to avoid reloading
- Process videos in smaller chunks

### Model Files Not Found
- Ensure models are either:
  1. In Git repository (small models)
  2. In persistent storage (uploaded via app)
  3. Downloaded from S3/cloud storage on startup

### Port Issues
- Ensure `PORT=8080` environment variable is set
- Railway dynamically assigns ports; ensure your app reads from the `PORT` env var
- Current Dockerfile correctly uses the PORT variable ✓

## Scaling

Once live, you can:
- **Upgrade Railway tier** for more resources
- **Add more replicas** for load balancing (in Railway dashboard)
- **Use background jobs** (Railway Job) for long-running video processing
- **Cache models** in persistent storage to avoid reloading

## Next Steps

1. Set up GitHub repository
2. Connect Railway to GitHub
3. Configure environment variables and persistent storage
4. Monitor first deployment in Railway dashboard
5. Test the web interface at the provided Railway URL

For additional help:
- Railway Docs: https://docs.railway.app
- Railway Community: https://discord.gg/railway
