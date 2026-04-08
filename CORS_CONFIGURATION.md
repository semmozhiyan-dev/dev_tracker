# CORS Configuration for DevTrackr FastAPI Backend

This file contains the exact code needed to enable CORS in your FastAPI app to allow requests from your Vercel frontend.

## Quick Setup

Add this code to your `app/main.py` file, right after creating the FastAPI app instance:

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# ... other imports ...

app = FastAPI()

# ============================================================================
# CORS Configuration - Allow requests from Frontend
# ============================================================================
# This enables your Vercel frontend to communicate with your Render backend

# List of allowed origins (domains that can make requests to your API)
allowed_origins = [
    # Local development
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    
    # Production - Update these with your actual Vercel URL
    "https://dev-tracker-xxxx.vercel.app",  # Replace 'xxxx' with your Vercel project name
    
    # Allow all Vercel preview/staging URLs
    "https://*.vercel.app",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers (Content-Type, Authorization, etc.)
)

# ============================================================================
# Rest of your FastAPI routes and configuration
# ============================================================================
# ... your existing code ...
```

## Step-by-Step Installation

### Step 1: Find Your Vercel URL

From your Vercel dashboard:
1. Click on your project (`dev_tracker`)
2. Look at the top of the page - you'll see your deployment URL
3. Copy it (e.g., `https://dev-tracker-xxxx.vercel.app`)

### Step 2: Update the CORS Configuration

In the code above, replace:
```
"https://dev-tracker-xxxx.vercel.app",
```

With your actual Vercel URL (e.g.):
```
"https://dev-tracker-unique123.vercel.app",
```

### Step 3: Commit and Push

```bash
git add app/main.py
git commit -m "Add CORS configuration for Vercel frontend"
git push origin main
```

Render will automatically redeploy!

### Step 4: Verify CORS is Working

1. Open your Vercel frontend: `https://dev-tracker-xxxx.vercel.app`
2. Open Developer Tools (F12) → Console
3. You should see the dashboard loading with real data
4. Check the Network tab - API calls should return HTTP 200 (not 403 or CORS errors)

---

## Explanation of CORS Settings

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,      # Which domains can access your API
    allow_credentials=True,             # Allow cookies/credentials in requests
    allow_methods=["*"],                # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                # Allow all headers (Content-Type, etc.)
)
```

### What Each Setting Does:

| Setting | Purpose | Example Value |
|---------|---------|----------------|
| `allow_origins` | Domains allowed to request your API | `["https://vercel.com", "http://localhost:3000"]` |
| `allow_credentials` | Allow authentication cookies/tokens | `True` / `False` |
| `allow_methods` | HTTP methods allowed | `["GET", "POST"]` or `["*"]` (all) |
| `allow_headers` | Headers clients can send | `["Content-Type"]` or `["*"]` (all) |

---

## Common CORS Errors & Fixes

### Error: "Access to XMLHttpRequest has been blocked by CORS policy"

**Cause:** Your Vercel URL is not in the `allowed_origins` list

**Fix:**
1. Get your Vercel URL
2. Add it to the `allowed_origins` list in the code
3. Redeploy to Render
4. Wait ~2 minutes and refresh your frontend

### Error: "Preflight request failed"

**Cause:** Usually CORS configuration issue

**Fix:**
1. Ensure `allow_methods` includes `["*"]` or `["OPTIONS"]`
2. Ensure `allow_headers` includes `["*"]` or `["Content-Type"]`
3. Clear browser cache and refresh

### Error: "Credentials mode is 'include' but Access-Control-Allow-Credentials is missing"

**Cause:** `allow_credentials` is set to `False`

**Fix:**
```python
allow_credentials=True,  # Change to True
```

---

## Production Checklist

Before deploying to production:

- [ ] Get your Vercel frontend URL
- [ ] Update `allowed_origins` with your Vercel URL
- [ ] Remove `http://localhost:*` entries (optional - for security)
- [ ] Test API calls from your Vercel frontend
- [ ] Verify no CORS errors in Console
- [ ] Check that data loads correctly on Dashboard

---

## Advanced: Restrict CORS for Security

For maximum security in production, you can be more restrictive:

```python
allowed_origins = [
    # Only your Vercel production domain
    "https://dev-tracker-production.vercel.app",
]
```

But during development, keeping `localhost` entries is recommended.

---

## Related Files

- `app/main.py` - Your FastAPI app (where this code goes)
- `VERCEL_DEPLOYMENT_GUIDE.md` - Full Vercel deployment guide
- `RENDER_DEPLOYMENT_GUIDE.md` - Full Render deployment guide

---

**Need help? Check the troubleshooting section in VERCEL_DEPLOYMENT_GUIDE.md**
