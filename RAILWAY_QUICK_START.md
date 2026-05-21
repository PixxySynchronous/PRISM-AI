# Railway Deployment - Quick Reference

## 🚀 Quick Start (5 minutes)

```bash
# 1. Ensure code is in GitHub
git push origin main

# 2. Go to railway.app → New Project → Deploy from GitHub
# 3. Select your repository
# 4. Wait for deployment (logs will show progress)
# 5. Railway gives you a public URL - done!
```

## ⚙️ What to Configure in Railway Dashboard

| Setting | Value | Why |
|---------|-------|-----|
| **PORT** | `8080` | App listens on this port |
| **PYTHONUNBUFFERED** | `1` | See logs in real-time |
| **ACTIVITY_WEB_RUNTIME_DIR** | `/data/activity_runtime` | Persistent storage location |
| **Volume Mount** | `/data` | Persists uploads & models |

## 📊 Deployment Timeline

| Stage | Duration | What's Happening |
|-------|----------|------------------|
| Build Start | 0s | Railway detects Dockerfile |
| System Setup | 1-2m | Installs ffmpeg, git, etc. |
| Python Deps | 5-10m | Installs torch, CV libraries |
| Build Complete | 10-15m | Docker image ready |
| Container Start | 1m | Gunicorn server launching |
| **Total** | **15-20m** | ✅ Live and ready |

First deployment takes longer. Subsequent pushes are faster (uses cache).

## 🤖 Model Files - Choose One Strategy

### Option A: Auto-Download (Easiest, Free)
- ✅ No setup needed
- ✅ Free
- ❌ Slow first startup (5-10 min)
- Models cache in `/data/activity_runtime/`

### Option B: AWS S3 (Best for Production)
- ✅ Fast startup (30s)
- ✅ Scalable
- ❌ Costs ~$1-5/month
- See `MODELS_ON_RAILWAY.md` for setup

### Option C: Persistent Volume Upload
- ✅ Free
- ✅ Simple
- ❌ Manual upload needed
- See `MODELS_ON_RAILWAY.md` for setup

**Recommendation for first deployment**: Use Option A (auto-download). Upgrade to S3 later if needed.

## 🔍 Monitor Your Deployment

```
Railway Dashboard → Your Service → [TAB NAME]
├── Deployments  ← See build progress, logs
├── Logs         ← Watch app output in real-time
├── Metrics      ← CPU, memory, network usage
├── Data         ← Manage persistent storage
├── Variables    ← Add environment variables
└── Networking   ← See your public URL
```

### Check if Live:
```bash
curl https://your-railway-url.railway.app/
# Should return HTML (Flask running)
```

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Build fails | Large files in repo | Check `.dockerignore` |
| App crashes | Missing dependency | Add to `requirements.txt` |
| Out of memory | Large models | Upgrade Railway tier or use S3 |
| Models not found | Auto-download failed | Wait 10+ min, check internet |
| Slow first request | Models downloading | Expected, wait 5-10 min |
| Data disappears | No volume mount | Check Data tab has `/data` volume |
| File not found at runtime | Wrong path | Use `ACTIVITY_WEB_RUNTIME_DIR` env var |

## 📁 File Locations After Deploy

```
Railway Container
├── /app                          ← Your app code
├── /data                         ← Persistent storage (survives restarts)
│   └── activity_runtime/
│       ├── uploads/              ← Uploaded videos
│       ├── outputs/              ← Generated CSVs, JSONs
│       ├── attendance/           ← Attendance data
│       └── torch_cache/          ← Downloaded models
└── /var/log/                     ← Container logs
```

## 🔄 Deploy Updates

Once live, to deploy new code:

```bash
# Make changes locally
code app.py

# Commit & push
git add .
git commit -m "Fixed feature X"
git push origin main

# Railway auto-deploys!
# Check Deployments tab to watch progress
```

## 💰 Costs

**Free Tier Includes:**
- 500 execution hours/month (enough for always-on service)
- 5GB storage
- 3 services per project
- No credit card required

**Paid Tier (if you exceed free tier):**
- ~$5/month to keep running 24/7
- Additional cost for more CPU/RAM

Check Railroad dashboard → "Billing" to see usage.

## 📞 Need Help?

| Resource | For |
|----------|-----|
| [railway.app/docs](https://docs.railway.app) | Official docs |
| [RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md) | Detailed setup |
| [MODELS_ON_RAILWAY.md](./MODELS_ON_RAILWAY.md) | ML model strategies |
| [RAILWAY_CHECKLIST.md](./RAILWAY_CHECKLIST.md) | Step-by-step checklist |
| Discord: railway.app | Community support |

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] Railway service created & connected to GitHub
- [ ] Environment variables set (PORT, ACTIVITY_WEB_RUNTIME_DIR, etc.)
- [ ] Volume mounted at `/data`
- [ ] Deployment completed (green checkmark)
- [ ] Public URL is accessible
- [ ] Can upload a test video
- [ ] Outputs are saved to persistent storage

**Congratulations! Your app is live on Railway.** 🎉

---

**Next Steps:**
1. Share the URL with collaborators
2. Test with sample videos
3. Monitor performance in Railway dashboard
4. Upgrade tier if needed for better performance
5. Consider S3 for models if auto-download is too slow
