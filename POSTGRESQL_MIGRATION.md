# DevTrackr PostgreSQL Migration Guide

This guide documents the migration from SQLite to PostgreSQL for the DevTrackr FastAPI application.

## Overview

The application now supports **both SQLite and PostgreSQL**:
- **Local Development**: Automatically uses SQLite (`sqlite:///./devtrackr.db`)
- **Production (Render)**: Uses PostgreSQL with automatic `postgres://` to `postgresql://` conversion

## What Was Updated

### 1. `app/config.py`
- Added automatic conversion of `postgres://` to `postgresql://` (for Render compatibility)
- DATABASE_URL defaults to SQLite for local development
- Supports PostgreSQL connection strings in production
- No breaking changes - still works seamlessly with SQLite locally

### 2. `app/database.py`
- Enhanced SQLAlchemy engine configuration
- Database type detection (SQLite vs PostgreSQL)
- SQLite: Disables `check_same_thread` for multi-threaded servers
- PostgreSQL: Adds connection pooling and health checks
- New `test_db_connection()` function to verify database connectivity

### 3. `requirements.txt`
- Already includes `psycopg2-binary==2.9.11` ✓
- Already includes `SQLAlchemy==2.0.49` ✓
- Already includes `python-dotenv==1.2.2` ✓

## Local Development (SQLite - Default)

No changes needed! SQLite continues to work automatically:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Database file created at: ./devtrackr.db
# No DATABASE_URL env var needed
```

**Features:**
- ✅ Lightweight, file-based database
- ✅ No external service needed
- ✅ Perfect for development and testing
- ✅ Easy to reset: just delete `devtrackr.db`

## Production (PostgreSQL on Render)

### Step 1: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `devtrackr-db`
   - **Database**: `devtrackr`
   - **User**: `devtrackr`
   - **Region**: Same as your web service
   - **Plan**: Free tier (0/mo)
4. Click **Create Database**

### Step 2: Get Connection String

1. Wait for database to be created (1-2 minutes)
2. Click on your PostgreSQL instance
3. Copy the **External Database URL**
   - Format: `postgresql://user:password@host:port/database`
   - ⚠️ Render might show `postgres://` - don't worry, we convert it automatically

### Step 3: Add to Render Environment Variables

**In your Web Service (FastAPI app):**

1. Go to **Settings** → **Environment Variables**
2. **Key**: `DATABASE_URL`
3. **Value**: Paste your PostgreSQL connection string
   - Examples:
     - `postgresql://devtrackr:password@host.render.com:5432/devtrackr`
     - Or use the Render provided URL (we handle `postgres://` conversion)
4. Click **Save**

### Step 4: Deploy

```bash
# Your updated code automatically:
# 1. Detects if DATABASE_URL is PostgreSQL or SQLite
# 2. Converts postgres:// to postgresql:// if needed
# 3. Uses appropriate connection settings
# 4. Creates tables on startup

git add -A
git commit -m "Switch to PostgreSQL with automatic SQLite fallback"
git push origin main
```

Render will automatically redeploy and initialize PostgreSQL tables.

## Environment Variables

### Local Development (`.env`)
```
GITHUB_USERNAME=your-username
GITHUB_TOKEN=your-token
GROQ_API_KEY=optional
# DATABASE_URL not needed - defaults to SQLite
```

### Production (Render Dashboard)
```
GITHUB_USERNAME=your-username
GITHUB_TOKEN=your-token
GROQ_API_KEY=optional
DATABASE_URL=postgresql://user:password@host:port/database
```

## Testing Database Connection

### Test Locally with SQLite
```bash
python -c "from app.database import test_db_connection; test_db_connection()"
# Output: ✅ Database connection successful
```

### Test Production PostgreSQL

After deploying to Render, the database initializes automatically. You can verify in Render logs:
```
✅ Database initialized successfully (PostgreSQL)
```

## Troubleshooting

### Issue: `SQLALCHEMY_WARN_20` or `LegacySchemaAlchemyWarning`

**Cause**: Using deprecated SQLAlchemy 1.x syntax with 2.0

**Solution**: Already fixed in our config - no action needed

### Issue: `postgresql://` conversion not working

**Symptoms**: `ModuleNotFoundError: No module named 'postgres'`

**Solution**: 
```bash
# Ensure psycopg2 is installed
pip install psycopg2-binary==2.9.11

# Or update it
pip install --upgrade psycopg2-binary
```

### Issue: "FATAL: too many connections"

**Cause**: PostgreSQL connection pool not recycling connections properly

**Solution**: Already fixed with pool settings in `database.py`:
```python
pool_recycle=3600  # Recycle connections every hour
pool_pre_ping=True  # Verify connections before using
```

### Issue: Connection string format incorrect

**Check**: Is your DATABASE_URL in the correct format?

**Valid formats:**
```
✓ postgresql://user:password@host.render.com:5432/devtrackr
✓ postgresql://user%40email.com:password@host.render.com:5432/devtrackr  (URL-encoded)
✗ postgres://user:password@host/devtrackr  (old format - will be converted)
```

## Database URL Formats

### SQLite (Local Development)
```
sqlite:///./devtrackr.db           # Relative path (recommended for dev)
sqlite:////absolute/path/to/db.db  # Absolute path (4 slashes)
```

### PostgreSQL (Production)
```
postgresql://user:password@localhost:5432/devtrackr              # Local PostgreSQL
postgresql://user:password@db.example.com:5432/devtrackr       # Custom host
postgresql://user%40company.com:pass@host:5432/db              # URL-encoded username
postgres://user:password@host:5432/devtrackr                   # Old format (auto-converted)
```

## Auto-Conversion Logic

The code automatically handles URL conversions:

```python
# Convert Render's postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure SQLite URLs are formatted correctly
if DATABASE_URL.startswith("sqlite://"):
    if not DATABASE_URL.startswith("sqlite:///"):
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite:///", 1)
```

## Migration from SQLite to PostgreSQL

To migrate existing data from SQLite to PostgreSQL:

### Option 1: Fresh Start (Recommended for Development)
```bash
# Delete local SQLite database
rm devtrackr.db

# On Render, database tables are created automatically
# No manual migration needed
```

### Option 2: Migrate Data

If you need to preserve existing data:

```bash
# 1. Export from SQLite
sqlite3 devtrackr.db ".dump" > dump.sql

# 2. Create tables in PostgreSQL first
# (They're created automatically on app startup)

# 3. Import custom data as needed
# Use a migration tool or manual INSERT statements
```

## Connection Pool Settings

### SQLite Settings
```python
connect_args = {"check_same_thread": False}
```
- Allows multiple threads to access the same connection
- Required for multi-threaded servers like Uvicorn

### PostgreSQL Settings
```python
pool_pre_ping=True          # Verify connection before use
pool_recycle=3600           # Recycle connections every hour
pool_size=5                 # Default connection pool size
max_overflow=10             # Max overflow connections
```

These settings ensure:
- Stale connections are detected and replaced
- Connection pool doesn't exceed limits
- Connections are recycled to prevent timeouts

## Model Compatibility

**Good news**: Your SQLAlchemy models don't need changes!

Your existing models work with both SQLite and PostgreSQL:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    task = Column(String(500), nullable=False)
    date = Column(String(50))
    # ... etc
```

Both databases handle this identically - no migration code needed!

## Performance Considerations

### SQLite (Development)
- Single file-based database
- Good for: Local development, testing
- Limitations: Not suitable for concurrent requests in production

### PostgreSQL (Production)
- Professional relational database
- Good for: Production, multiple users, high concurrency
- Features: Full ACID compliance, connection pooling, transactions

## Deployment Commands

### Local Development
```bash
# Install dependencies (includes psycopg2-binary)
pip install -r requirements.txt

# Run with SQLite (automatic)
uvicorn app.main:app --reload
```

### Production (Render)
```bash
# Git push triggers:
# 1. GitHub Actions CI (tests)
# 2. Render deployment (redeploys)
# 3. Database initialization (automatic)

git push origin main
```

## Verifying PostgreSQL is Working

### Check Render Logs
```bash
# View deployment logs in Render Dashboard
# Look for: "✅ Database initialized successfully (PostgreSQL)"
```

### Test API Endpoint
```bash
curl https://your-render-app.onrender.com/commits/weekly
# Should return commit data from PostgreSQL
```

### Check Database Size
In Render PostgreSQL dashboard:
- Tables created: `commits`, `tasks`, `task_status`
- Data stored and retrievable

## FAQ

**Q: Do I need to change my code to use PostgreSQL?**
A: No! The database switching is automatic. Your FastAPI code doesn't change.

**Q: What if DATABASE_URL is not set?**
A: Falls back to SQLite automatically. Perfect for local development.

**Q: Is my data safe on Render's free PostgreSQL?**
A: Yes, but remember:
- Free tier ips databases after 7 days of inactivity
- For production, consider upgrading to paid plan
- Always backup important data

**Q: Can I test PostgreSQL locally?**
A: Yes! Run PostgreSQL in Docker:
```bash
docker run -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
```
Then set:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
```

**Q: How do I reset the database?**
A: 
- **SQLite**: Delete `devtrackr.db` and restart
- **PostgreSQL**: Drop and recreate the database on Render dashboard

## Summary

✅ **Local**: Use SQLite automatically (no setup)
✅ **Production**: Use PostgreSQL on Render (DATABASE_URL in env vars)
✅ **Automatic**: `postgres://` → `postgresql://` conversion handled
✅ **Compatible**: All models work with both databases
✅ **No Code Changes**: FastAPI code unchanged

Your DevTrackr app now seamlessly switches between SQLite and PostgreSQL! 🎉
