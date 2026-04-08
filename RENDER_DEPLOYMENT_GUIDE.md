# DevTrackr FastAPI - Complete Deployment Guide for Render

This guide walks you through deploying your DevTrackr FastAPI application to Render for free.

## Prerequisites

Before starting, make sure you have:
- ✅ GitHub account with your DevTrackr repository
- ✅ Render account (free tier available) - https://render.com
- ✅ Your GitHub Personal Access Token (for GITHUB_TOKEN env var)
- ✅ Groq API Key (optional, for AI features)

---

## Part 1: Create a Render Account and Get Started

### Step 1.1: Sign Up for Render
1. Go to https://render.com
2. Click **Sign Up**
3. Choose **Sign up with GitHub** (easiest option)
4. Authorize Render to access your GitHub account
5. Verify your email and complete setup

### Step 1.2: Create a New Service
1. In Render Dashboard, click **New +** (top right)
2. Select **Web Service**

---

## Part 2: Connect Your GitHub Repository

### Step 2.1: Authorize GitHub Access
1. You'll see a prompt to connect GitHub
2. Click **Connect account** next to GitHub
3. Choose **Only select repositories**
4. Select your `dev_tracker` repository
5. Click **Install & Authorize**

### Step 2.2: Deploy from Repository
1. Back on Render, you should now see your repositories
2. Find **dev_tracker** in the list
3. Click **Connect** next to it
4. Select the branch: **main**
5. Click **Next**

---

## Part 3: Configure Build and Start Commands

### Step 3.1: Set the Service Name
- **Name:** `devtrackr` (will be used in your URL)
- The URL will be something like: `https://devtrackr-xxxx.onrender.com`

### Step 3.2: Choose the Environment
- **Environment:** Python 3
- **Region:** Choose the closest region to you (e.g., Ohio for US)
- **Branch:** main

### Step 3.3: Set Build Command
Copy and paste this exact build command:

```bash
pip install -r requirements.txt
```

### Step 3.4: Set Start Command
Copy and paste this exact start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Explanation:**
- `app.main:app` refers to the FastAPI app instance in your code
- `--host 0.0.0.0` listens on all network interfaces (required for Render)
- `--port 8000` exposes port 8000

---

## Part 4: Add Environment Variables

### Step 4.1: Add Variables in Render Dashboard

Before you deploy, you need to add all environment variables from your `.env` file.

**Important:** Do NOT paste your actual `.env` file content as-is. Add each variable individually.

In the Render dashboard, look for the **Environment** section and add these variables:

#### Required Variables:

1. **GITHUB_USERNAME**
   - Click **Add Environment Variable**
   - Key: `GITHUB_USERNAME`
   - Value: Your GitHub username (e.g., `octocat`)
   - Click **Add**

2. **GITHUB_TOKEN**
   - Key: `GITHUB_TOKEN`
   - Value: Your GitHub Personal Access Token
   - ⚠️ Keep this PRIVATE!
   - Click **Add**

#### Optional Variables:

3. **GROQ_API_KEY** (for AI features)
   - Key: `GROQ_API_KEY`
   - Value: Your Groq API key (or leave empty if you don't have it)
   - Click **Add**

4. **DATABASE_URL** (PostgreSQL - we'll set this up in Part 5)
   - **DO NOT ADD THIS YET** - We'll add it after setting up the database
   - Key: `DATABASE_URL`
   - Value: Will be provided by Render after creating PostgreSQL

#### Optional Variables (Defaults):

- **GITHUB_API_BASE:** `https://api.github.com` (usually no need to change)
- **PYTHONUNBUFFERED:** `1` (recommended for Docker logging)

---

## Part 5: Set Up Free PostgreSQL Database

### Step 5.1: Create a PostgreSQL Instance

1. In Render Dashboard, click **New +** (top right)
2. Select **PostgreSQL**
3. Fill in the details:
   - **Name:** `devtrackr-db` (same for all instances)
   - **Database:** `devtrackr` (the database name)
   - **User:** `devtrackr` (the database user)
   - **Region:** Same as your web service
   - **PostgreSQL Version:** Latest available
   - **Pricing Plan:** Free (you'll see "$0/mo")

4. Click **Create Database**

**⏳ Wait:** Database creation takes 1-2 minutes

---

### Step 5.2: Get Your PostgreSQL Connection String

Once the database is created:

1. Go to your PostgreSQL instance in Render Dashboard
2. In the **Connections** section, find the **External Database URL**
3. Copy the entire URL - it looks like:
   ```
   postgresql://username:password@dpg-xxxxxxxxxxxxx.oregon-postgres.render.com:5432/devtrackr
   ```

### Step 5.3: Add DATABASE_URL to Your Web Service

1. Go back to your **Web Service** (devtrackr)
2. Click **Environment** (or scroll to current environment variables)
3. Click **Add Environment Variable**
4. Key: `DATABASE_URL`
5. Value: Paste the PostgreSQL connection string from Step 5.2
6. Click **Save**

---

## Part 6: Deploy Your Application

### Step 6.1: Trigger the Deployment

1. On your Web Service page, scroll to the top
2. Click the **Deploy** button (or it may auto-deploy)
3. You'll see a deployment log in real-time

### Step 6.2: Monitor the Deployment

Watch for these messages in the deployment log:

✅ **"Installing dependencies..."** - pip is installing packages  
✅ **"Build succeeded"** - Your code compiled successfully  
✅ **"Service is live"** or **"Deployment succeeded!"** - App is running  

**If you see errors:**
- Check the full log output
- Verify all environment variables are set correctly
- Make sure your start command is exactly: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

## Part 7: Verify the Deployment is Working

### Step 7.1: Get Your Live URL

1. Once deployment succeeds, go to your Web Service in Render
2. At the top, you'll see your service URL:
   ```
   https://devtrackr-xxxx.onrender.com
   ```
3. Copy this URL

### Step 7.2: Test the Root Endpoint

Open your browser and visit:

```
https://devtrackr-xxxx.onrender.com/
```

You should see the FastAPI dashboard or a welcome message.

### Step 7.3: Test API Endpoints

Try these endpoints to verify the app is working:

**1. Health Check:**
```
https://devtrackr-xxxx.onrender.com/health
```
Expected response: `200 OK`

**2. FastAPI Documentation (Interactive Swagger UI):**
```
https://devtrackr-xxxx.onrender.com/docs
```
You should see the interactive API documentation

**3. Alternative Documentation (ReDoc):**
```
https://devtrackr-xxxx.onrender.com/redoc
```

### Step 7.4: Test a Real API Call (using curl or Postman)

**Get commit data:**
```bash
curl https://devtrackr-xxxx.onrender.com/commits
```

Expected: Returns JSON data with your commits

**Create a task:**
```bash
curl -X POST https://devtrackr-xxxx.onrender.com/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Test deployment"}'
```

Expected: `201 Created` with task details

---

## Part 8: Common Issues and Troubleshooting

### Issue: "Build failed" or "Module not found"

**Solution:**
1. Check that `requirements.txt` has all dependencies
2. Verify the file is in the root directory
3. Try re-deploying by clicking **Deploy** again

### Issue: "Configuration Error: Missing required environment variable"

**Solution:**
1. Go to **Environment** section of your web service
2. Verify `GITHUB_USERNAME` and `GITHUB_TOKEN` are set
3. Make sure there are no extra spaces or typos
4. Click **Save** and re-deploy

### Issue: "Cannot connect to the database"

**Solution:**
1. Verify PostgreSQL instance is running (check Render dashboard)
2. Check that `DATABASE_URL` is set correctly in Environment
3. Ensure PostgreSQL instance is in the same region as your web service
4. Wait a few seconds and refresh - Render sometimes takes time to propagate

### Issue: Page shows "Service Unhealthy" or "504 Gateway Timeout"

**Solution:**
1. Check the deployment logs for errors
2. Verify the Start Command is exactly: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Check all environment variables are present
4. Try a manual re-deploy from the Render dashboard

### Issue: Static files (html/css) not loading

**Solution:**
1. Verify your FastAPI app mounts static files in `app/main.py`
2. The static folder must be in the same location as the app code
3. Rebuild and deploy

---

## Part 9: Monitor Your Deployment (Optional)

### View Logs in Real-Time

1. Go to your Web Service in Render
2. Click **Logs** (tab at the top)
3. You'll see all requests and errors in real-time

### Set Up Deployment Notifications (Optional)

1. In Render, go to **Account Settings** → **Notifications**
2. Enable email notifications for deployment updates
3. You'll get alerts when deployments succeed or fail

---

## Part 10: Auto-Deploy on GitHub Push

If you set up the GitHub Actions workflows from earlier:

1. Every push to `main` branch will trigger CI tests
2. If tests pass, the Deploy workflow will automatically call your Render deploy hook
3. Your app updates automatically!

**To check deploy hook status:**
1. Go to your Web Service → **Settings**
2. Scroll to **Deploy Hook**
3. You'll see the webhook URL used by GitHub Actions

---

## Part 11: Database Initialization

### First-Time Setup

When your app first starts, it should automatically create database tables.

**To verify database was initialized:**

1. In Render dashboard, go to your PostgreSQL instance
2. Click **"Connect"** (blue button)
3. Copy the **PSQL Command**
4. Paste it in your terminal - this opens a database shell
5. Run SQL commands to check:

```sql
-- List all tables
\dt

-- Check tasks table structure
\d tasks

-- Count tasks
SELECT COUNT(*) FROM tasks;

-- Exit
\q
```

---

## Part 12: File Structure Reminder

Make sure your GitHub repository has this structure:

```
dev_tracker/
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── app/
│   ├── __init__.py
│   ├── main.py          ← FastAPI app
│   ├── config.py        ← Environment config
│   ├── database.py      ← SQLAlchemy setup
│   ├── models.py
│   ├── analyzer.py
│   └── trainer.py
├── static/
│   └── dashboard.html
├── tests/
├── Dockerfile           ← For containerization
├── docker-compose.yml   ← For local dev
├── requirements.txt     ← Dependencies
├── .dockerignore
└── .env                 ← LOCAL ONLY (not in GitHub)
```

---

## Summary: Commands & URLs Reference

| Item | Value |
|------|-------|
| **Render Dashboard** | https://dashboard.render.com |
| **Your Live App** | https://devtrackr-xxxx.onrender.com |
| **API Documentation** | https://devtrackr-xxxx.onrender.com/docs |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Database Type** | PostgreSQL (free tier available) |
| **Required Env Vars** | `GITHUB_USERNAME`, `GITHUB_TOKEN`, `DATABASE_URL` |
| **Optional Env Vars** | `GROQ_API_KEY` |

---

## Next Steps

After deployment:

1. ✅ Test all API endpoints
2. ✅ Check logs for any errors
3. ✅ Verify database has data
4. ✅ Share your app URL with others!
5. ✅ Set up monitoring/alerts (optional)

## Support & Documentation

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org

---

**Happy deploying! 🚀**
