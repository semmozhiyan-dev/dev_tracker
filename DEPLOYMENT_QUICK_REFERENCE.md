# DevTrackr Deployment - Quick Reference Card

## 🎯 Quick Deployment Path

### Frontend (Static HTML → Vercel)
```
1. Go to vercel.com → Sign up with GitHub
2. Import dev_tracker repository
3. Set Root Directory to: ./static
4. Deploy!
5. Copy your Vercel URL (e.g., https://dev-tracker-xxxx.vercel.app)
```

### Backend (FastAPI → Render)
```
1. Go to render.com → Deploy from GitHub
2. Set Build Command: pip install -r requirements.txt
3. Set Start Command: uvicorn app.main:app --host 0.0.0.0 --port 8000
4. Add Env Vars: GITHUB_USERNAME, GITHUB_TOKEN, GROQ_API_KEY, DATABASE_URL
5. Add PostgreSQL database
6. Deploy!
7. Copy your Render URL (e.g., https://devtrackr-xxxx.onrender.com)
```

---

## 📝 API Configuration (Frontend Communicates with Backend)

### File: `static/dashboard.html`

Find this section (around line 875):
```javascript
const API_BASE_URL = (function() {
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    return '';  // ← Replace this
})();
```

Replace the empty string with your Render URL:
```javascript
return 'https://devtrackr-xxxx.onrender.com';  // Your Render URL
```

---

## 🔐 CORS Configuration (Backend Allows Requests)

### File: `app/main.py`

Add this after `app = FastAPI()`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000", 
        "https://dev-tracker-xxxx.vercel.app",  # Your Vercel URL
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 API Calls Made by Frontend

All these calls now support both local and production URLs:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/commits/weekly` | GET | Fetch weekly commit data |
| `/streak` | GET | Get current streak |
| `/tasks/today` | GET | Get today's tasks |
| `/tasks` | POST | Create new task |
| `/tasks/{id}/done` | PATCH | Mark task complete |
| `/trainer/message` | GET | Get coach message |
| `/trainer/analyze` | GET | Get AI performance review |
| `/trainer/suggest` | GET | Get AI task suggestions |

---

## 📊 Verification Checklist

### Frontend (Vercel)
- [ ] Vercel URL loads without errors
- [ ] Open DevTools Console - no red errors
- [ ] Dashboard shows stats (today's commits, streak)
- [ ] Weekly chart displays with bars
- [ ] Daily quests list shows tasks
- [ ] Coach message box shows message

### Backend (Render)  
- [ ] Render URL + `/docs` shows API documentation
- [ ] All environment variables set (check Settings)
- [ ] PostgreSQL database is running
- [ ] CORS configuration updated with Vercel URL

### Network Calls
- [ ] Check DevTools Network tab
- [ ] Look for `/commits/weekly`, `/streak`, `/tasks/today`
- [ ] All should return HTTP 200 (green)
- [ ] No CORS errors (red blocked requests)
- [ ] Response shows real data from GitHub

---

## 🔗 Deployment URLs

| Service | URL Format | Example |
|---------|-----------|---------|
| Vercel Frontend | `https://[project-name].vercel.app` | `https://dev-tracker-abc123.vercel.app` |
| Render Backend | `https://[service-name].onrender.com` | `https://devtrackr-xyz789.onrender.com` |
| Render Database | Included in `DATABASE_URL` env var | `postgresql://user:pass@...` |

---

## 📋 Environment Variables

### On Render (Backend)
```
GITHUB_USERNAME = your-github-username
GITHUB_TOKEN = ghp_xxxxxxxxxxxxx
GROQ_API_KEY = (optional, for AI features)
DATABASE_URL = postgresql://... (auto-set by Render)
```

### On Vercel (Frontend)
- No auth variables needed on Vercel
- The frontend only needs to know the Render backend URL (hardcoded in HTML)

### On Your Local Machine
```
GITHUB_USERNAME = your-github-username
GITHUB_TOKEN = ghp_xxxxxxxxxxxxx
GROQ_API_KEY = (optional)
DATABASE_URL = sqlite:///./devtrackr.db (SQLite for local dev)
```

---

## 🔄 Update Flow

```
1. You make code changes locally
   ↓
2. Git push to GitHub main branch
   ↓
3. GitHub Actions CI workflow runs tests + builds Docker
   ↓
4. If CI passes, Deploy workflow triggers Render (backend)
   ↓
5. Vercel watches GitHub too - auto-deploys frontend
   ↓
6. Both live sites update automatically! ✨
```

---

## ⚠️ Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Dashboard loads but no data | API URL is wrong | Check `getApiUrl()` returns correct Render URL |
| CORS error in console | Backend doesn't allow frontend | Add Vercel URL to CORS origins in `app/main.py` |
| 404 errors on API calls | Render backend is down | Check Render dashboard, redeploy if needed |
| Blank page | Wrong root directory on Vercel | Ensure Root Directory is set to `./static` |
| Tasks/commits not showing | Render database issue | Check PostgreSQL is running on Render |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **RENDER_DEPLOYMENT_GUIDE.md** | Complete backend deployment to Render |
| **VERCEL_DEPLOYMENT_GUIDE.md** | Complete frontend deployment to Vercel |
| **CORS_CONFIGURATION.md** | CORS setup for frontend-backend communication |
| **Dockerfile** | Container configuration (optional, for reference) |
| **docker-compose.yml** | Local development with Docker (optional) |
| **.github/workflows/ci.yml** | GitHub Actions CI pipeline |
| **.github/workflows/deploy.yml** | GitHub Actions deployment |

---

## 🎓 Key Concepts

### API_BASE_URL
- **What:** The domain where your FastAPI backend is running
- **Local Dev:** `http://localhost:8000`
- **Production:** `https://devtrackr-xxxx.onrender.com`
- **How Set:** In `dashboard.html` `getApiUrl()` function

### CORS
- **What:** Security feature that controls which websites can access your API
- **Why Needed:** Frontend (Vercel) and Backend (Render) are on different domains
- **How Fix:** Add Vercel URL to `CORSMiddleware` in `app/main.py`

### Static vs Dynamic
- **Frontend (Vercel):** Static HTML/CSS/JS - served as-is
- **Backend (Render):** Dynamic FastAPI server - runs Python code, connects to database

---

## 🚀 Final Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Render
- [ ] Backend has PostgreSQL database configured
- [ ] Frontend dashboard.html has correct Render URL
- [ ] Backend app.main.py has CORS configured with Vercel URL
- [ ] All env vars set in Render dashboard
- [ ] GitHub Actions workflows configured for auto-deploy
- [ ] Verified live dashboard shows real data
- [ ] Network calls to backend return HTTP 200
- [ ] No errors in browser console

---

**Once all checkboxes are done, you're fully deployed! 🎉**

Share your Vercel URL: `https://dev-tracker-xxxx.vercel.app`
