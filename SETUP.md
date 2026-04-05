# DevTrackr Setup Guide

## Quick Start

### 1. Create Your `.env` File

Copy the example configuration:
```bash
cp .env.example .env
```

### 2. Configure GitHub Credentials

Edit `.env` and add your GitHub credentials:

```env
GITHUB_USERNAME=your-github-username
GITHUB_TOKEN=ghp_your_personal_access_token
```

#### Getting Your GitHub Personal Access Token

1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "DevTrackr")
4. Select required scopes:
   - ✅ `public_repo` - read access to public repositories
   - ✅ `read:user` - read user profile data
5. Click "Generate token"
6. Copy the token immediately (you won't see it again!)
7. Paste it into your `.env` file as `GITHUB_TOKEN`

### 3. Verify Configuration

The app validates your configuration on startup:

```bash
python -c "from app.config import GITHUB_USERNAME, GITHUB_TOKEN; print(f'✓ Configured: {GITHUB_USERNAME}')"
```

If this works, your setup is correct!

## Configuration Details

### Environment Variables

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `GITHUB_USERNAME` | ✅ Yes | GitHub username for fetching events | `octocat` |
| `GITHUB_TOKEN` | ✅ Yes | Personal access token for API auth | `ghp_xxxxx...` |
| `GITHUB_API_BASE` | ❌ No | GitHub API endpoint | `https://api.github.com` |
| `DATABASE_URL` | ❌ No | Database connection string | `sqlite:///./devtrackr.db` |

### Validation System

The app uses a centralized configuration system in `app/config.py`:

```python
# get_required_env(var_name, description)
# - Fetches required env variable
# - Raises ConfigError if missing or empty
# - Used at module import time

# get_optional_env(var_name, default)
# - Fetches optional env variable
# - Returns default value if not set

# validate_config()
# - Validates all required variables
# - Called on app startup
# - Displays detailed error messages if validation fails
```

### Error Handling

If validation fails, you'll see:

```
❌ Configuration validation failed:

Missing required environment variable: GITHUB_TOKEN
  Purpose: GitHub personal access token for API authentication
  Please set this variable in your .env file or as an environment variable.
```

**Fix:**
1. Check your `.env` file exists
2. Verify `GITHUB_TOKEN` is set and not empty
3. Restart the app

## Security Best Practices

### ✅ DO

- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Never commit real credentials to Git
- ✅ Use `.env.example` as a template
- ✅ Rotate tokens regularly
- ✅ Use minimal scope permissions
- ✅ Store sensitive values in environment variables

### ❌ DON'T

- ❌ Commit `.env` file to Git
- ❌ Share your GitHub token
- ❌ Hardcode credentials in code
- ❌ Use overly permissive token scopes
- ❌ Commit token values anywhere

## Running the App

### Development

```bash
# Terminal 1: Start the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Expected output:
# ✅ Configuration validated successfully
# ✅ Database initialized successfully
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup.

## Troubleshooting

### "Missing required environment variable"

1. Check `.env` file exists in project root
2. Verify variable is set and not empty
3. Check for typos in variable name
4. Restart the app

### "GitHub API error: 401 Unauthorized"

- Your token is invalid or expired
- Generate a new token at https://github.com/settings/tokens
- Update `.env` with new token

### "RuntimeError: Directory 'static' does not exist"

- Create the `static/` directory
- Move HTML files there
- Restart the app

### Token keeps getting exposed

1. Revoke the exposed token at https://github.com/settings/tokens
2. Generate a new token
3. Update `.env`
4. Push changes to Git
5. Contact GitHub Support if suspicious activity

## Configuration Validation Flow

```
Application Start
    ↓
Load .env file (python-dotenv)
    ↓
Import app/config.py
    ↓
Validate config on module load
    ├─ Check GITHUB_USERNAME
    ├─ Check GITHUB_TOKEN
    └─ Raise ConfigError if any missing
    ↓
FastAPI startup event
    ↓
Call validate_config() again
    ├─ Additional verification
    └─ Clear error messages
    ↓
Initialize database
    ↓
✅ App ready to serve requests
```

## File Structure

```
.env                    # Your actual credentials (NOT in Git)
.env.example           # Template for credentials (in Git)
.gitignore             # Contains .env, .env.local, etc.
app/
  config.py             # Centralized configuration management
  main.py               # FastAPI app with validation on startup
  database.py           # Database setup
  models.py             # ORM models
```

## Next Steps

1. ✅ Set up `.env` file
2. ✅ Add GitHub token
3. ✅ Verify with config check
4. ✅ Start the app
5. 🚀 Open http://127.0.0.1:8000/static/dashboard.html

Questions? Check the error messages—they provide detailed guidance!
