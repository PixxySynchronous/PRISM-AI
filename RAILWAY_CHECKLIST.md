# Railway Deployment Checklist

Follow this step-by-step to deploy your project to Railway.

## Pre-Deployment (Local)

- [ ] **Commit to Git**
  ```bash
  git init
  git add .
  git commit -m "Initial commit for Railway deployment"
  ```

- [ ] **Push to GitHub**
  ```bash
  git remote add origin https://github.com/YOUR_USERNAME/classroom-ai-project.git
  git branch -M main
  git push -u origin main
  ```

- [ ] **Create `.env` file** (for local testing)
  ```bash
  echo "PORT=8080" > .env
  echo "ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime" >> .env
  echo "PYTHONUNBUFFERED=1" >> .env
  ```

- [ ] **Test Docker build locally** (optional but recommended)
  ```bash
  docker build -t classroom-ai:test .
  docker run -p 8080:8080 classroom-ai:test
  # Visit http://localhost:8080 to verify
  ```

## Railway Setup

- [ ] **Create Railway Account**
  - Go to [railway.app](https://railway.app)
  - Sign up (can use GitHub account)

- [ ] **Create New Project**
  - Click "New Project" in Railway dashboard
  - Select "Deploy from GitHub repo"
  - Grant Railway access to your GitHub account

- [ ] **Select Repository**
  - Choose `classroom-ai-project` repo
  - Railway automatically detects Dockerfile

- [ ] **Configure Service**
  Once Railway creates the service:
  
  **Variables Tab:**
  - [ ] Add `PORT=8080`
  - [ ] Add `ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime`
  - [ ] Add `PYTHONUNBUFFERED=1`
  
  **Data Tab:**
  - [ ] Add a Volume:
    - Mount Path: `/data`
    - This stores uploaded videos, outputs, and cached models
  
  **Networking Tab:**
  - [ ] Generate domain (Railway provides public URL)
  - [ ] Note the URL for testing

- [ ] **Choose Model Strategy** (see MODELS_ON_RAILWAY.md)
  
  For fastest setup, pick one:
  
  | Strategy | Setup Time | Startup Time | Cost |
  |----------|-----------|--------------|------|
  | **Auto-download** (easiest) | 1 min | 5-10 min first run | Free |
  | **S3** (production) | 30 min | 30 sec | ~$1-5/mo |
  | **Persistent Volume** (simple) | 10 min | Manual upload | Free |
  
  - [ ] Selected strategy: ________________
  
  If Auto-download:
  - [ ] No additional setup needed, proceed to deploy
  
  If S3:
  - [ ] Create S3 bucket and upload models
  - [ ] Add AWS env vars to Railway
  - [ ] Update `pipeline_loader.py`
  
  If Persistent Volume:
  - [ ] Plan to upload models after first deploy

## Deployment

- [ ] **Start First Deployment**
  - In Railway dashboard, go to **Deployments**
  - Should auto-deploy when you pushed to GitHub
  - Wait for "Deployment Successful"

- [ ] **Monitor Build Process**
  - Click the active deployment to see logs
  - First build takes **10-20 minutes** (normal)
  - Look for these success indicators:
    ```
    ✓ Python dependencies installed
    ✓ Dockerfile build completed
    ✓ Container started on port 8080
    ✓ Gunicorn server listening
    ```

- [ ] **Check Deployment Status**
  - Look for a green checkmark on the deployment
  - Note the Railway-provided URL (e.g., `https://classroom-ai-production.railway.app`)

## Post-Deployment Verification

- [ ] **Test Public URL**
  ```bash
  curl https://your-railway-app.railway.app/
  # Should return HTML (Flask app responding)
  ```

- [ ] **Check Logs for Errors**
  - In Railway → Logs tab
  - Look for any Python errors or missing dependencies
  - Common errors:
    ```
    ModuleNotFoundError → Missing in requirements.txt
    OutOfMemory → Upgrade Railway tier
    Connection refused → Port not set correctly
    ```

- [ ] **Monitor Health**
  - Use Railway **Metrics** tab
  - Check CPU, Memory, Network usage
  - Should be idle unless processing video

- [ ] **Test Core Features**
  - Visit `https://your-app.railway.app/`
  - Try uploading a small test video
  - Check if outputs are generated

- [ ] **Upload Models (if using Persistent Volume)**
  - After first successful deployment
  - Add endpoint to Railway app for model upload
  - OR use SSH access to Railway container
  
## Optimization

- [ ] **Enable Auto-Deploy on Push**
  - Already enabled by default
  - Every `git push` triggers new build

- [ ] **Monitor Costs**
  - Railway Pricing page in dashboard
  - Free tier includes:
    - 500 execution hours/month
    - 5GB storage
    - Should be enough for development

- [ ] **Set Up Alerts** (optional)
  - Railway → Settings → Notifications
  - Get alerts on deployment failures

## Scaling (After Initial Success)

- [ ] **Upgrade Railway Tier if Needed**
  - Current: Basic tier (2GB RAM)
  - If slow: Upgrade to Standard (4GB RAM)
  - If lots of concurrent uploads: Add replicas

- [ ] **Increase Storage**
  - Current: 2GB volume
  - If running out: Increase in Data tab

- [ ] **Add Database** (if needed later)
  - For persistent job tracking
  - Railway supports PostgreSQL

- [ ] **Set Up Scheduled Jobs** (if needed)
  - For automated activity processing
  - Railway Jobs feature

## Troubleshooting

**If deployment fails:**
1. Check **Build Logs** → look for error messages
2. Verify `Dockerfile` and `requirements.txt` are present
3. Check for syntax errors: `docker build .` locally
4. Retry deployment from Railway dashboard

**If app crashes after deploy:**
1. Check **Logs** tab for error messages
2. Common issues:
   - Module not found → Update requirements.txt
   - Port not accessible → Check PORT env var
   - Out of memory → Upgrade tier
3. Re-push fix to GitHub to trigger rebuild

**If uploads/outputs disappear:**
1. Verify volume is mounted at `/data`
2. Ensure env var `ACTIVITY_WEB_RUNTIME_DIR=/data/activity_runtime` is set
3. Check Railway → Data tab → Volume is attached

**Slow first request (models downloading):**
- [ ] Normal behavior (5-10 minutes expected)
- [ ] Wait for models to cache
- [ ] Subsequent requests will be fast
- [ ] Consider S3 option for faster performance

## Next Steps

- [ ] Share the Railway app URL with classmates
- [ ] Gather feedback on accuracy/speed
- [ ] Optimize based on usage patterns
- [ ] Consider adding CI/CD tests before deploy

## Helpful Commands

```bash
# Deploy latest changes
git add .
git commit -m "Updates"
git push origin main
# Railway auto-deploys!

# Check Railway app logs
railway logs

# View all deployments
railway deployments

# Open Railway dashboard
railway open

# Set a variable from CLI
railway variables set PYTHONUNBUFFERED=1
```

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Status**: https://railway.app/status
- **Discord Community**: https://discord.gg/railway
- **GitHub Issues**: Check your repo's issues for deployment-related discussions

---

**You're all set!** Once you've completed the checklist, your app will be live on Railway. 🚀
