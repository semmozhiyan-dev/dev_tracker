# PostgreSQL Quick Setup Card

## Local Development (SQLite - Automatic)

```bash
# 1. Install dependencies (nothing special needed)
pip install -r requirements.txt

# 2. Run the app (SQLite used automatically)
uvicorn app.main:app --reload

# ✅ Database: sqlite:///./devtrackr.db (created automatically)
# ✅ No env vars needed
```

## Production on Render (PostgreSQL)

### Step 1: Create PostgreSQL on Render
```
1. Render Dashboard → New + → PostgreSQL
2. Name: devtrackr-db
3. Database: devtrackr
4. Region: Same as web service
5. Plan: Free
6. Create Database

Copy the External Database URL (starts with postgresql://)
```

### Step 2: Add to Render Environment Variables

In your DevTrackr Web Service:
```
Settings → Environment Variables

KEY: DATABASE_URL
VALUE: postgresql://user:password@host:port/database
```

### Step 3: Deploy

```bash
git add -A
git commit -m "Add PostgreSQL support"
git push origin main

# Render auto-redeploys and initializes PostgreSQL
```

## Local Testing with PostgreSQL (Optional)

If you want to test PostgreSQL locally:

```bash
# 1. Run PostgreSQL in Docker
docker run -e POSTGRES_PASSWORD=password -d -p 5432:5432 postgres:15

# 2. Create .env file
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres" > .env

# 3. Run app
uvicorn app.main:app --reload
```

## What Changed in Your Code

### `app/config.py`
- ✅ Automatically converts `postgres://` to `postgresql://` (Render compatibility)
- ✅ Defaults to SQLite if DATABASE_URL not set
- ✅ No breaking changes - works seamlessly

### `app/database.py`
- ✅ Enhanced with proper PostgreSQL connection pooling
- ✅ New `test_db_connection()` function
- ✅ Automatic database type detection
- ✅ Works with both SQLite and PostgreSQL

### `requirements.txt`
- ✅ `psycopg2-binary==2.9.11` already installed
- ✅ All dependencies ready

## Verification

### Verify Locally
```bash
python -c "from app.database import test_db_connection; test_db_connection()"
# Output: ✅ Database connection successful
```

### Verify on Render
After deployment, check logs:
```
✅ Database initialized successfully (PostgreSQL)
```

## URL Format Reference

| Database | URL Format | Example |
|----------|-----------|---------|
| **SQLite** (Local) | `sqlite:///./devtrackr.db` | Automatic |
| **PostgreSQL** | `postgresql://user:pass@host:5432/db` | `postgresql://devtrackr:abc@host.render.com:5432/devtrackr` |
| **Render Output** | `postgres://...` | Auto-converted to `postgresql://` |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No DATABASE_URL set | SQLite used automatically ✓ |
| `postgres://` URL | Auto-converted to `postgresql://` ✓ |
| Connection refused | Check DATABASE_URL format |
| ModuleNotFoundError postgres | `pip install psycopg2-binary` |

## Everything Works Automatically ✨

Your code now:
- ✅ Uses SQLite locally (no setup)
- ✅ Uses PostgreSQL on Render (auto-detected)
- ✅ Converts URL formats automatically
- ✅ Handles both simultaneously in different environments

**No code changes needed in FastAPI - just set DATABASE_URL!**
