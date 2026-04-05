from fastapi import FastAPI, HTTPException
import os
import requests
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(title="DevTrackr", version="0.1.0")

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
