# DevTrackr Frontend - Complete Deployment Guide for Vercel

This guide walks you through deploying your DevTrackr static frontend to Vercel for free.

## Prerequisites

Before starting, make sure you have:
- ✅ GitHub account with your DevTrackr repository
- ✅ Vercel account (free tier available) - https://vercel.com
- ✅ Render backend already deployed and running (see RENDER_DEPLOYMENT_GUIDE.md)
- ✅ Your Render backend URL (e.g., `https://devtrackr-xxxx.onrender.com`)

---

## Part 1: Create a Vercel Account and Connect GitHub

### Step 1.1: Sign Up for Vercel
1. Go to https://vercel.com
2. Click **Sign Up**
3. Click **"Continue with GitHub"** (easiest option)
4. Authorize Vercel to access your GitHub repositories
5. Verify your email if needed

### Step 1.2: Import Your Repository
1. You should automatically be taken to the "Import Project" page
2. If not, click **"New Project"** (top right of dashboard)
3. Paste your repository URL:
   ```
   https://github.com/YOUR_USERNAME/dev_tracker
   ```
4. Click **"Continue"**

---

## Part 2: Configure the Root Directory

### Step 2.1: Set the Root Directory to `static/`

On the import page, you'll see configuration options:

1. **Project Name:** Keep as `dev_tracker` (or rename if you prefer)
2. **Framework Preset:** Select **"Other"** (it's a static site)
3. **Root Directory:** 
   - Click on the **Root Directory** dropdown or input field
   - Change from `./` to **`./static`**
   - This tells Vercel to deploy from your `static/` folder

4. **Environment Variables Section:** Skip for now - we'll add the API URL in the next step

### Step 2.2: Verify the Configuration
- **Build Command:** Should be empty (for static sites)
- **Output Directory:** Should be empty or `.`
- **Install Command:** Should be empty

Click **"Deploy"** - but WAIT! We need to add environment variables first if you want.

---

## Part 3: Add Environment Variables for Render Backend URL

### Step 3.1: Add Environment Variables BEFORE Deployment

You have two options:

**Option A: Add during deployment (recommended)**
1. Before clicking Deploy, you should see **Environment Variables** section
2. Click **"Continue"** to add environment variables
3. Add the following:
   - **Key:** `REACT_APP_API_URL`
   - **Value:** Your Render backend URL (e.g., `https://devtrackr-xxxx.onrender.com`)
   - Click **"Add Environment Variable"**

4. Now click **"Deploy"**

**Option B: Add after deployment**
1. Deploy first (without environment variables)
2. In your Vercel dashboard, go to your project
3. Click **Settings** → **Environment Variables**
4. Add the variable as described above
5. The deployment will automatically rebuild

### Step 3.2: How Vercel Uses Environment Variables

When you add environment variables in Vercel, they're injected during the build process. Since your HTML file is static, we need to use a different approach.

**The solution:** We've already added code to your dashboard.html that:
1. Checks for `window.API_BASE_URL`
2. Falls back to `//` (same-origin) for relative URLs
3. Uses `http://localhost:8000` for local development

Since your static HTML won't have access to environment variables at runtime, we'll use a different approach:

---

## Part 3B: Update HTML with Environment Variables (Frontend Approach)

### Step 3B.1: Create a config.js File

Create a new file at `static/config.js`:

```javascript
// API Configuration
window.API_BASE_URL = process.env.REACT_APP_API_URL || '';
```

**BUT** - Static HTML doesn't process `process.env`. Instead, use this approach:

### Step 3B.2: Use Window Configuration

Your HTML already has this logic:

```javascript
const API_BASE_URL = (function() {
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    return '';
})();
```

### Step 3B.3: Inject Environment Variable via index.html

Since we're using static files, we need to create a simple workaround. Add this to your Vercel Environment Variables:

In Vercel Dashboard → Project Settings → Environment Variables:

1. **Key:** `API_URL`
2. **Value:** Your Render backend URL
3. Click **Save**

Then, create a `public` folder in your project root and add a deployment script (or follow the next approach).

---

## Part 3C: RECOMMENDED - Use Vercel Build Configuration with vercel.json

### Step 3C.1: Create `vercel.json`

Create a file at the root of your project: `vercel.json`

```json
{
  "buildCommand": "echo 'Building static site'",
  "outputDirectory": "static",
  "cleanUrls": true,
  "env": {
    "API_URL": {
      "description": "Backend API URL for Render deployment",
      "required": false
    }
  }
}
```

### Step 3C.2: Create a Build Script (Optional but Recommended)

Create `static/init.js` at the top of your HTML `<head>`:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevTrackr - Dashboard</title>
    <script>
        // Set API URL from Vercel environment variable
        // This will be replaced during Vercel deployment
        window.API_BASE_URL = '{{API_URL}}' || '';
    </script>
    <!-- Rest of head content -->
</head>
```

---

## Part 4: SIMPLEST APPROACH - Create a .env.production File

Create a file in your project root: `.env.production`

```
REACT_APP_API_URL=https://devtrackr-xxxx.onrender.com
```

Replace `https://devtrackr-xxxx.onrender.com` with your actual Render backend URL.

**Note:** This file should NOT be committed to git if you want to use different URLs for different deployments. Add to `.gitignore`:

```
.env.production
.env.local
```

---

## Part 5: Deploy to Vercel

### Step 5.1: Click Deploy

1. Once you've set the root directory to `./static`
2. Added any environment variables (if using the complex approach)
3. Click the **"Deploy"** button (big blue button)

**⏳ Wait:** Vercel will build and deploy your project (usually 30-60 seconds)

### Step 5.2: Verify Deployment

Once complete, you'll see:
- ✅ **"Congratulations! Your site is live"** message
- A URL like: `https://dev-tracker-xxxx.vercel.app`
- You can click the URL to view your live site

---

## Part 6: Configure API URL in Deployed Site

### Step 6.1: Update Dashboard.html for Production

Edit `static/dashboard.html` and find the API configuration section (around line 875):

```javascript
const API_BASE_URL = (function() {
    // Check if set via window config (for Vercel environment variables)
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    // Check if in development (localhost)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // Default to empty string (same domain) - will be overridden by Vercel env var
    return '';
})();
```

Replace the empty string default with your Render URL:

```javascript
const API_BASE_URL = (function() {
    if (window.API_BASE_URL) {
        return window.API_BASE_URL;
    }
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // Default to your Render backend URL for production
    return 'https://devtrackr-xxxx.onrender.com';
})();
```

Replace `https://devtrackr-xxxx.onrender.com` with your actual Render URL.

### Step 6.2: Commit and Push to GitHub

```bash
git add static/dashboard.html
git commit -m "Update API URL for Render backend"
git push origin main
```

### Step 6.3: Vercel Auto-Redeploys

Since you connected GitHub, Vercel automatically redeploys when you push to `main`:
- Watch your Vercel dashboard for deployment progress
- Once complete, your site will be live with the new API URL

---

## Part 7: Enable CORS on Render Backend (IMPORTANT)

For your frontend to communicate with your backend, you need to allow Cross-Origin Requests.

### Step 7.1: Update your FastAPI app (app/main.py)

Add CORS middleware to allow your Vercel URL:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",            # Local development
        "http://localhost:8000",            # Local development
        "https://dev-tracker-xxxx.vercel.app",  # Your Vercel URL
        "https://*.vercel.app",             # All Vercel preview URLs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 7.2: Update CORS for Production

Replace `dev-tracker-xxxx` with your actual Vercel deployment name:

```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:8000",
    "https://YOUR-VERCEL-PROJECT-NAME.vercel.app",
    "https://*.vercel.app",
]
```

### Step 7.3: Deploy Updated FastAPI Code to Render

1. Commit and push your changes:
   ```bash
   git add app/main.py
   git commit -m "Add CORS for Vercel frontend"
   git push origin main
   ```

2. Render will automatically redeploy (thanks to GitHub Actions workflow)
3. Wait for deployment to complete

---

## Part 8: Verify the Live Dashboard is Fetching Data

### Step 8.1: Open Your Live Vercel URL

1. Go to your Vercel dashboard
2. Click on your project
3. Click the **"Visit"** button to open your live site
4. Or go to: `https://dev-tracker-xxxx.vercel.app`

### Step 8.2: Check Browser Console

1. Open Developer Tools: **F12** or **Right-click → Inspect**
2. Go to **Console** tab
3. Look for any error messages
4. You should see network requests being made to your Render backend

**Possible Errors:**
- `CORS error` → Need to update CORS settings on Render
- `404 Not Found` → Wrong API URL or Render backend is down
- `Cannot reach backend` → Check if your Render URL is correct

### Step 8.3: Test API Endpoints

1. Open the **Network** tab in Developer Tools
2. Refresh the page
3. Look for requests like:
   - `commits/weekly` → Should show commit data
   - `streak` → Should show streak data
   - `tasks/today` → Should show tasks
   - `trainer/message` → Should show trainer message

All should return **HTTP 200** with data.

### Step 8.4: Verify Data is Loading

Check if these appear on your dashboard:
- ✅ **Commit stats** (Today's Commits, Current Streak)
- ✅ **Weekly chart** with commit bars
- ✅ **Daily Quests** list (with any existing tasks)
- ✅ **Coach message** box (trainer message)
- ✅ **AI buttons** (Get AI Review, Suggest Tasks)

If all these are showing with real data from your GitHub, you're good to go! 🎉

---

## Part 9: Troubleshooting

### Issue: "Failed to fetch data" or "Cannot connect to backend"

**Solution:**
1. Check your API_BASE_URL is correct: Open Console → Type `API_BASE_URL`
2. Verify Render backend is running: Try visiting `https://devtrackr-xxxx.onrender.com/docs`
3. Check CORS settings in your FastAPI app
4. Verify environment variables are set in both Vercel and Render

### Issue: "CORS error: Cross-Origin Request Blocked"

**Solution:**
1. Verify your Vercel URL is in the CORS allowed origins
2. Restart/redeploy your Render backend
3. Check that your CORS middleware is correctly configured

### Issue: Dashboard shows but no data appears

**Solution:**
1. Check Network tab for failed requests
2. Verify your GitHub credentials are set on Render
3. Try hitting `https://devtrackr-xxxx.onrender.com/commits/weekly` directly in browser
4. Check Render logs for errors

### Issue: Can't find my Vercel URL

**Solution:**
1. Go to https://vercel.com/dashboard
2. Click on your project (`dev_tracker`)
3. At the top, you'll see your deployment URL
4. Click **"Visit"** button to view your live site

---

## Part 10: Custom Domain (Optional)

### Add Your Own Domain to Vercel

1. In Vercel Dashboard, go to your project
2. Click **Settings** → **Domains**
3. Enter your custom domain (e.g., `devtrackr.com`)
4. Follow the DNS configuration steps

---

## Summary: API Configuration Reference

| Environment | API_BASE_URL | Access |
|-------------|--------------|--------|
| **Local (both frontend & backend)** | `` (empty) or `/` | `http://localhost:3000` + `http://localhost:8000` |
| **Production (Vercel + Render)** | `https://devtrackr-xxxx.onrender.com` | `https://dev-tracker.vercel.app` |
| **Preview (Vercel PR preview)** | `https://devtrackr-xxxx.onrender.com` | `https://dev-tracker-preview-xxxx.vercel.app` |

---

## Complete Deployment Checklist

- [ ] Vercel account created
- [ ] GitHub repo connected to Vercel
- [ ] Root directory set to `./static`
- [ ] Dashboard.html updated with Render backend URL
- [ ] Changes committed and pushed to GitHub
- [ ] Vercel deployment completed successfully
- [ ] CORS configured in FastAPI (Render backend)
- [ ] Render backend redeployed with CORS changes
- [ ] Visited live Vercel URL
- [ ] Verified Dashboard loads with real data
- [ ] Network requests showing successful API calls (HTTP 200)
- [ ] All components displaying (commits, streak, quests, trainer)

---

## Next Steps

After successful deployment:

1. **Share your dashboard:** Send your Vercel URL to friends
2. **Monitor performance:** Check Vercel & Render dashboards regularly
3. **Set up analytics:** Optional - Vercel provides built-in analytics
4. **Custom domain:** Add your own domain if desired
5. **Continuous deployment:** Every push to main = automatic deployment!

---

## Support & Documentation

- **Vercel Docs:** https://vercel.com/docs
- **GitHub Pages:** https://pages.github.com/
- **CORS Documentation:** https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- **JavaScript Fetch API:** https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API

---

**Happy deploying! Your DevTrackr dashboard is now live! 🚀**
