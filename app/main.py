from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional
from collections import defaultdict
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_API_BASE, GROQ_API_KEY, validate_config, ConfigError
from app.database import init_db, get_db
from app.models import Commit, Task, TaskStatus
from app.trainer import get_trainer_message
from app.analyzer import analyze_with_groq, get_task_suggestions
from groq import Groq

app = FastAPI(title="DevTrackr", version="0.1.0")

# Enable CORS for all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database and validate configuration when the app starts."""
    try:
        validate_config()
        print("✅ Configuration validated successfully")
    except ConfigError as e:
        print(f"❌ Configuration validation failed:\n{e}")
        raise
    
    init_db()
    print("✅ Database initialized successfully")


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Helper function to fetch and aggregate commits from GitHub
def _fetch_github_commits(username: Optional[str] = None) -> list:
    """
    Helper function to fetch GitHub push events and aggregate commit counts by date and repo.
    
    Args:
        username: GitHub username (override env var if provided)
    
    Returns:
        List of commits aggregated by date and repo
        
    Raises:
        HTTPException: If GitHub API call fails or user not found
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
        List of commits aggregated by date and repo
    """
    return _fetch_github_commits(username)


@app.post("/commits/sync")
def sync_commits(username: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch GitHub commits and sync them to the SQLite database.
    
    Fetches all push events from GitHub, aggregates commits by date and repo,
    then saves them to the database. Avoids duplicate entries for the same
    date and repo combination.
    
    Args:
        username: GitHub username (override env var if provided)
        db: Database session (injected by FastAPI)
    
    Returns:
        JSON response with sync results:
        {
            "status": "success",
            "total_fetched": 5,
            "new_synced": 3,
            "duplicates_skipped": 2,
            "message": "Successfully synced 3 new commit records"
        }
    """
    try:
        # Fetch commits from GitHub
        github_commits = _fetch_github_commits(username)
        
        total_fetched = len(github_commits)
        new_synced = 0
        duplicates_skipped = 0
        
        for commit_data in github_commits:
            # Parse date string to datetime.date object
            date_obj = datetime.strptime(commit_data["date"], "%Y-%m-%d").date()
            repo = commit_data["repo"]
            count = commit_data["commit_count"]
            
            # Check if this date + repo combination already exists
            existing = db.query(Commit).filter(
                Commit.date == date_obj,
                Commit.repo == repo
            ).first()
            
            if existing:
                # Skip duplicate - but optionally update count
                duplicates_skipped += 1
            else:
                # Create new commit record
                new_commit = Commit(
                    date=date_obj,
                    repo=repo,
                    count=count
                )
                db.add(new_commit)
                new_synced += 1
        
        # Commit all new records to database
        if new_synced > 0:
            db.commit()
        
        return {
            "status": "success",
            "total_fetched": total_fetched,
            "new_synced": new_synced,
            "duplicates_skipped": duplicates_skipped,
            "message": f"Successfully synced {new_synced} new commit records"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions from GitHub API
        raise
    except Exception as e:
        # Rollback on any database error
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing commits: {str(e)}"
        )


@app.get("/commits/weekly")
def get_commits_weekly(db: Session = Depends(get_db)):
    """
    Get total commits per day for the last 7 days.
    
    Queries the database for all commit entries from the past 7 days,
    groups them by date, and returns the total commit count per day.
    
    Returns:
        List of daily commit summaries:
        [
            {
                "date": "2024-01-15",
                "total_commits": 12
            },
            {
                "date": "2024-01-14",
                "total_commits": 8
            }
        ]
    """
    try:
        # Calculate date range: last 7 days from today
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        
        # Query commits from the last 7 days
        commits = db.query(Commit).filter(
            Commit.date >= seven_days_ago,
            Commit.date <= today
        ).all()
        
        # Aggregate commits by date
        daily_totals = defaultdict(int)
        for commit in commits:
            daily_totals[commit.date] += commit.count
        
        # Convert to list format, sorted by date descending
        result = []
        for date_key in sorted(daily_totals.keys(), reverse=True):
            result.append({
                "date": date_key.isoformat(),
                "total_commits": daily_totals[date_key]
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weekly commits: {str(e)}"
        )


@app.get("/streak")
def get_commit_streak(db: Session = Depends(get_db)):
    """
    Calculate the current commit streak.
    
    Determines how many consecutive days the user has made at least 1 commit.
    Starting from the most recent commit date, counts backward to find consecutive
    days with commits.
    
    Returns:
        JSON response with streak information:
        {
            "streak_days": 5,
            "start_date": "2024-01-11",
            "end_date": "2024-01-15",
            "message": "Current streak: 5 consecutive days with commits"
        }
    """
    try:
        # Get all unique dates with commits, sorted descending
        commits = db.query(Commit.date).distinct().order_by(Commit.date.desc()).all()
        
        if not commits:
            return {
                "streak_days": 0,
                "start_date": None,
                "end_date": None,
                "message": "No commits found"
            }
        
        # Extract date objects and sort them
        commit_dates = sorted([c[0] for c in commits], reverse=True)
        
        # Start counting from the most recent date
        streak_count = 1
        current_date = commit_dates[0]
        
        # Check for consecutive days going backward
        for i in range(1, len(commit_dates)):
            previous_date = commit_dates[i]
            days_diff = (current_date - previous_date).days
            
            # If the difference is exactly 1 day, continue the streak
            if days_diff == 1:
                streak_count += 1
                current_date = previous_date
            else:
                # Gap found, streak ends
                break
        
        # Calculate streak start date
        most_recent_date = commit_dates[0]
        streak_start_date = most_recent_date - timedelta(days=streak_count - 1)
        
        return {
            "streak_days": streak_count,
            "start_date": streak_start_date.isoformat(),
            "end_date": most_recent_date.isoformat(),
            "message": f"Current streak: {streak_count} consecutive days with commits"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating streak: {str(e)}"
        )


# ==================== Task Management Routes ====================

@app.post("/tasks")
def create_task(task_name: str, db: Session = Depends(get_db)):
    """
    Create a new task with today's date.
    
    Args:
        task_name: Description of the task (up to 500 characters)
        db: Database session (injected by FastAPI)
    
    Returns:
        Created task with full details:
        {
            "id": 1,
            "task": "Fix login bug",
            "status": "pending",
            "date": "2024-01-15",
            "created_at": "2024-01-15T14:30:22.123456",
            "updated_at": "2024-01-15T14:30:22.123456"
        }
    """
    try:
        if not task_name or not task_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Task name cannot be empty"
            )
        
        # Create new task with today's date and PENDING status
        new_task = Task(
            task=task_name.strip(),
            status=TaskStatus.PENDING,
            date=date.today()
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return {
            "id": new_task.id,
            "task": new_task.task,
            "status": new_task.status.value,
            "date": new_task.date.isoformat(),
            "created_at": new_task.created_at.isoformat(),
            "updated_at": new_task.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating task: {str(e)}"
        )


@app.get("/tasks/today")
def get_tasks_today(db: Session = Depends(get_db)):
    """
    Get all tasks for today.
    
    Retrieves all tasks created or due today from the database.
    
    Returns:
        List of tasks for today:
        [
            {
                "id": 1,
                "task": "Fix login bug",
                "status": "pending",
                "date": "2024-01-15",
                "created_at": "2024-01-15T14:30:22.123456",
                "updated_at": "2024-01-15T14:30:22.123456"
            },
            {
                "id": 2,
                "task": "Write unit tests",
                "status": "in_progress",
                "date": "2024-01-15",
                "created_at": "2024-01-15T14:32:15.654321",
                "updated_at": "2024-01-15T14:35:00.000000"
            }
        ]
    """
    try:
        today = date.today()
        
        # Query all tasks for today, sorted by created_at descending
        tasks = db.query(Task).filter(Task.date == today).order_by(Task.created_at.desc()).all()
        
        result = []
        for task in tasks:
            result.append({
                "id": task.id,
                "task": task.task,
                "status": task.status.value,
                "date": task.date.isoformat(),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching today's tasks: {str(e)}"
        )


@app.patch("/tasks/{task_id}/done")
def mark_task_done(task_id: int, db: Session = Depends(get_db)):
    """
    Mark a task as completed.
    
    Updates the task status to COMPLETED and saves the update timestamp.
    
    Args:
        task_id: ID of the task to mark as done
        db: Database session (injected by FastAPI)
    
    Returns:
        Updated task:
        {
            "id": 1,
            "task": "Fix login bug",
            "status": "completed",
            "date": "2024-01-15",
            "created_at": "2024-01-15T14:30:22.123456",
            "updated_at": "2024-01-15T14:35:45.654321"
        }
    """
    try:
        # Query for the task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )
        
        # Update status to COMPLETED
        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        
        return {
            "id": task.id,
            "task": task.task,
            "status": task.status.value,
            "date": task.date.isoformat(),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating task: {str(e)}"
        )


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task.
    
    Removes a task from the database permanently.
    
    Args:
        task_id: ID of the task to delete
        db: Database session (injected by FastAPI)
    
    Returns:
        Confirmation message:
        {
            "id": 1,
            "message": "Task deleted successfully",
            "deleted_task": "Fix login bug"
        }
    """
    try:
        # Query for the task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task_id} not found"
            )
        
        # Store task details before deletion
        task_name = task.task
        
        # Delete the task
        db.delete(task)
        db.commit()
        
        return {
            "id": task_id,
            "message": "Task deleted successfully",
            "deleted_task": task_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting task: {str(e)}"
        )


@app.get("/trainer/message")
def get_trainer_motivation(db: Session = Depends(get_db)):
    """
    Get a gym coach-style motivation message based on today's commits.
    
    Analyzes today's GitHub commit activity and returns an aggressive,
    funny coaching message. The tone adapts based on performance:
    - 0 commits: Harsh warning
    - 1-4 commits: Motivational push
    - 5+ commits: Celebration
    
    Returns:
        JSON response with trainer message:
        {
            "message": "YOOO! You're DEAD, buddy! ZERO commits?!...",
            "style": "danger",
            "intensity": "MAXIMUM WARNING",
            "commits_today": 0
        }
    """
    try:
        # Get today's date
        today = date.today()
        
        # Query commits for today
        today_commits = db.query(Commit).filter(
            Commit.date == today
        ).all()
        
        # Sum up all commits for today
        total_commits = sum(commit.count for commit in today_commits)
        
        # Get the trainer message
        trainer_response = get_trainer_message(total_commits)
        
        # Add the commit count to response
        trainer_response["commits_today"] = total_commits
        
        return trainer_response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trainer message: {str(e)}"
        )


@app.get("/trainer/analyze")
async def analyze_performance(db: Session = Depends(get_db)):
    """
    Get AI-powered performance analysis for the last 7 days of commits.
    
    Uses Groq's LLM to generate a drill sergeant style performance review
    based on your commit history from the past 7 days. Requires GROQ_API_KEY
    to be configured in your .env file.
    
    Returns:
        JSON response with AI analysis:
        {
            "analysis": "You absolute beast! 15 commits this week...",
            "commits_total": 15,
            "unique_repositories": 3,
            "active_days": 5,
            "available": true
        }
        
        If Groq API key is not configured:
        {
            "analysis": null,
            "message": "Groq API key not configured. Add GROQ_API_KEY to your .env file.",
            "available": false
        }
    """
    try:
        # Check if Groq API key is available
        if not GROQ_API_KEY:
            print("[Route] Groq API key not configured")
            return {
                "analysis": None,
                "message": "Groq API key not configured. Add GROQ_API_KEY to your .env file.",
                "available": False
            }
        
        print("[Route] Groq API key found, proceeding with analysis")
        
        # Get the last 7 days
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        
        # Query commits from the last 7 days
        commits = db.query(Commit).filter(
            Commit.date >= seven_days_ago,
            Commit.date <= today
        ).all()
        
        print(f"[Route] Found {len(commits)} commits in last 7 days")
        
        # Convert to JSON-serializable format for analyzer
        commits_data = [
            {
                "date": str(c.date),
                "repo": c.repo,
                "count": c.count
            }
            for c in commits
        ]
        
        # Calculate summary stats
        total_commits = sum(c.count for c in commits)
        unique_repos = len(set(c.repo for c in commits))
        active_days = len(set(c.date for c in commits))
        
        print(f"[Route] Initializing Groq client...")
        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"[Route] Groq client created, calling analyzer...")
        
        # Get AI analysis (not async, synchronous call)
        analysis = analyze_with_groq(commits_data, groq_client)
        print(f"[Route] Analysis result: {type(analysis)} - {bool(analysis)}")
        
        return {
            "analysis": analysis,
            "commits_total": total_commits,
            "unique_repositories": unique_repos,
            "active_days": active_days,
            "available": True
        }
    
    except Exception as e:
        print(f"[Route] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing performance: {str(e)}"
        )


@app.get("/trainer/suggest")
def suggest_tasks(db: Session = Depends(get_db)):
    """
    Get AI-powered task suggestions for tomorrow based on recent commit activity.
    
    Uses Groq's LLM to suggest exactly 3 specific, actionable coding tasks
    the developer should work on tomorrow based on their recent commit history
    and repositories.
    
    Returns:
        JSON response with task suggestions:
        {
            "suggestions": [
                "Add error handling to user authentication flow",
                "Refactor database queries to reduce N+1 problems",
                "Write unit tests for payment processing module"
            ],
            "available": true,
            "commits_analyzed": 6,
            "repos_used": 2
        }
        
        If Groq API key is not configured:
        {
            "suggestions": null,
            "message": "Groq API key not configured",
            "available": false
        }
    """
    try:
        # Check if Groq API key is available
        if not GROQ_API_KEY:
            print("[TaskSuggest] Groq API key not configured")
            return {
                "suggestions": None,
                "message": "Groq API key not configured. Add GROQ_API_KEY to your .env file.",
                "available": False
            }
        
        print("[TaskSuggest] Starting task suggestion generation")
        
        # Get the last 30 days of commit data to provide context
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Query commits from the last 30 days
        commits = db.query(Commit).filter(
            Commit.date >= thirty_days_ago,
            Commit.date <= today
        ).all()
        
        print(f"[TaskSuggest] Found {len(commits)} commits in last 30 days")
        
        # Convert to JSON-serializable format for analyzer
        commits_data = [
            {
                "date": str(c.date),
                "repo": c.repo,
                "count": c.count
            }
            for c in commits
        ]
        
        # Get unique repository names
        unique_repos = sorted(set(c.repo for c in commits))
        
        print(f"[TaskSuggest] Working with {len(unique_repos)} unique repos: {unique_repos}")
        
        # Initialize Groq client
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"[TaskSuggest] Groq client created, requesting suggestions...")
        
        # Get task suggestions from Groq
        suggestions = get_task_suggestions(commits_data, unique_repos, groq_client)
        
        if not suggestions:
            print("[TaskSuggest] Failed to get suggestions from Groq")
            suggestions = [
                "Review and refactor recent code changes",
                "Add more comprehensive unit tests",
                "Optimize database queries for performance"
            ]
        
        print(f"[TaskSuggest] Generated {len(suggestions)} suggestions")
        
        return {
            "suggestions": suggestions,
            "available": True,
            "commits_analyzed": len(commits),
            "repos_used": len(unique_repos)
        }
    
    except Exception as e:
        print(f"[TaskSuggest] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating task suggestions: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
