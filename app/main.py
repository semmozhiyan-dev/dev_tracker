from fastapi import FastAPI, HTTPException
import requests
from typing import Optional
from collections import defaultdict
from app.config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_API_BASE
from app.database import init_db

app = FastAPI(title="DevTrackr", version="0.1.0")


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database when the app starts."""
    init_db()


@app.get("/")
def read_root():
    """Hello world route"""
    return {"message": "Welcome to DevTrackr API", "status": "running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/github/events")
def get_github_events(username: Optional[str] = None):
    """
    Fetch public events for a GitHub user.

    Args:
        username: GitHub username (override env var if provided)

    Returns:
        List of public events as JSON
    """
    user = username or GITHUB_USERNAME

    if not user:
        raise HTTPException(
            status_code=400,
            detail="GitHub username not provided in query params or .env file"
        )

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    headers["Accept"] = "application/vnd.github.v3+json"

    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/users/{user}/events/public",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 500
        if status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{user}' not found")
        detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=status_code,
            detail=f"GitHub API error: {detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@app.get("/github/commits")
def get_github_commits(username: Optional[str] = None):
    """
    Fetch GitHub push events and aggregate commit counts by date and repository.

    Args:
        username: GitHub username (override env var if provided)

    Returns:
        List of commits aggregated by date and repo with format:
        [
            {
                "date": "2024-01-15",
                "repo": "username/repo-name",
                "commit_count": 5
            }
        ]
    """
    user = username or GITHUB_USERNAME

    if not user:
        raise HTTPException(
            status_code=400,
            detail="GitHub username not provided in query params or .env file"
        )

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    headers["Accept"] = "application/vnd.github.v3+json"

    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/users/{user}/events/public",
            headers=headers
        )
        response.raise_for_status()
        events = response.json()

        # Aggregate push events by date and repo
        commits_by_date_repo = defaultdict(lambda: defaultdict(int))

        for event in events:
            # Filter only PushEvents
            if event.get("type") != "PushEvent":
                continue

            # Extract date from ISO timestamp (YYYY-MM-DD)
            created_at = event.get("created_at", "")
            date = created_at.split("T")[0] if created_at else "unknown"

            # Extract repo name
            repo = event.get("repo", {}).get("name", "unknown")

            # Count commits from the push payload
            commit_count = len(event.get("payload", {}).get("commits", []))
            commits_by_date_repo[date][repo] += commit_count

        # Convert to clean JSON list format
        result = []
        for date in sorted(commits_by_date_repo.keys(), reverse=True):
            for repo in sorted(commits_by_date_repo[date].keys()):
                result.append({
                    "date": date,
                    "repo": repo,
                    "commit_count": commits_by_date_repo[date][repo]
                })

        return result

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 500
        if status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub user '{user}' not found")
        detail = e.response.text if e.response else str(e)
        raise HTTPException(
            status_code=status_code,
            detail=f"GitHub API error: {detail}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
