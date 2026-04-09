from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from typing import Optional, List
from collections import defaultdict
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.config import GITHUB_USERNAME, GITHUB_TOKEN, GITHUB_API_BASE, GROQ_API_KEY, validate_config, ConfigError
from app.database import init_db, get_db
from app.models import Commit, Task, TaskStatus
from app.trainer import get_trainer_message
from app.analyzer import analyze_with_groq, get_task_suggestions
from groq import Groq

# ==================== Pydantic Request/Response Models ====================

class TaskCreateRequest(BaseModel):
    """Request schema for creating a task"""
    task: str = Field(..., min_length=1, max_length=500, description="Task description")
    
    class Config:
        example = {"task": "Implement user authentication"}


class TaskResponse(BaseModel):
    """Response schema for task"""
    id: int
    task: str
    status: str
    date: str
    created_at: str
    updated_at: str


class CommitResponse(BaseModel):
    """Response schema for commit data"""
    date: str
    total_commits: int


class StreakResponse(BaseModel):
    """Response schema for streak data"""
    streak_days: int
    start_date: Optional[str]
    end_date: Optional[str]
    message: str


class TrainerResponse(BaseModel):
    """Response schema for trainer message"""
    message: str
    style: str  # danger, warning, success
    intensity: str
    commits_today: int


class AnalysisResponse(BaseModel):
    """Response schema for AI analysis"""
    analysis: Optional[str]
    commits_total: int
    unique_repositories: int
    active_days: int
    available: bool
    message: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """Response schema for task suggestions"""
    suggestions: Optional[List[str]]
    available: bool
    commits_analyzed: int
    repos_used: int
    message: Optional[str] = None


class StatsResponse(BaseModel):
    """Response schema for overall statistics"""
    total_commits: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    current_streak: int
    active_days: int
    unique_repositories: int

app = FastAPI(title="DevTrackr", version="0.1.0")

# ============================================================================
# CORS Configuration
# ============================================================================
# Allow requests from specific origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        
        # Production - Render backend (for local testing)
        "https://dev-tracker-10ms.onrender.com",
        
        # Production - Vercel frontend (specific URL)
        "https://dev-tracker-k4oz-ekscygkm3-semmozhidoubles-projects.vercel.app",
        
        # Allow all Vercel preview URLs for preview deployments
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
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
    """Serve the dashboard HTML file"""
    return FileResponse("static/dashboard.html")


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


@app.get("/commits/weekly", response_model=List[CommitResponse])
def get_commits_weekly(db: Session = Depends(get_db)):
    """
    Get total commits per day for the last 7 days.
    
    Queries the database for all commit entries from the past 7 days,
    groups them by date, and returns the total commit count per day.
    
    Returns:
        List of daily commit summaries
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
            count_val = commit.count if commit.count is not None else 0
            # Type ignore: SQLAlchemy Column values are ints at runtime
            daily_totals[commit.date] = daily_totals[commit.date] + count_val  # type: ignore
        
        # Convert to list format, sorted by date descending
        result = []
        for date_key in sorted(daily_totals.keys(), reverse=True):
            result.append(CommitResponse(
                date=date_key.isoformat(),
                total_commits=daily_totals[date_key]
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching weekly commits: {str(e)}"
        )


@app.get("/streak", response_model=StreakResponse)
def get_commit_streak(db: Session = Depends(get_db)):
    """
    Calculate the current commit streak.
    
    Determines how many consecutive days the user has made at least 1 commit.
    Starting from the most recent commit date, counts backward to find consecutive
    days with commits.
    
    Returns:
        JSON response with streak information
    """
    try:
        # Get all unique dates with commits, sorted descending
        commits = db.query(Commit.date).distinct().order_by(Commit.date.desc()).all()
        
        if not commits:
            return StreakResponse(
                streak_days=0,
                start_date=None,
                end_date=None,
                message="No commits found"
            )
        
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
        
        return StreakResponse(
            streak_days=streak_count,
            start_date=streak_start_date.isoformat(),
            end_date=most_recent_date.isoformat(),
            message=f"Current streak: {streak_count} consecutive days with commits"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating streak: {str(e)}"
        )


# ==================== Task Management Routes ====================

@app.post("/tasks", response_model=TaskResponse)
def create_task_json(task_data: TaskCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new task with today's date.
    
    Args:
        task_data: Request body with task description
        db: Database session (injected by FastAPI)
    
    Returns:
        Created task with full details
    """
    try:
        if not task_data.task or not task_data.task.strip():
            raise HTTPException(
                status_code=400,
                detail="Task cannot be empty"
            )
        
        # Create new task with today's date and PENDING status
        new_task = Task(
            task=task_data.task.strip(),
            status=TaskStatus.PENDING,
            date=date.today()
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return TaskResponse(  # type: ignore
            id=new_task.id,  # type: ignore
            task=new_task.task,  # type: ignore
            status=new_task.status.value,
            date=new_task.date.isoformat(),
            created_at=new_task.created_at.isoformat(),
            updated_at=new_task.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating task: {str(e)}"
        )


@app.post("/tasks")
def create_task_query(task_name: str, db: Session = Depends(get_db)):
    """
    Create a new task with today's date (legacy query param version).
    Supports task_name as query parameter for backward compatibility.
    
    Args:
        task_name: Task description via query parameter
        db: Database session (injected by FastAPI)
    
    Returns:
        Created task with full details
    """
    if not task_name or not task_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Task cannot be empty"
        )
    
    req = TaskCreateRequest(task=task_name.strip())
    return create_task_json(req, db)


@app.get("/tasks/today", response_model=List[TaskResponse])
def get_tasks_today(db: Session = Depends(get_db)):
    """
    Get all tasks for today.
    
    Retrieves all tasks created or due today from the database.
    
    Returns:
        List of tasks for today
    """
    try:
        today = date.today()
        
        # Query all tasks for today, sorted by created_at descending
        tasks = db.query(Task).filter(Task.date == today).order_by(Task.created_at.desc()).all()
        
        return [
            TaskResponse(  # type: ignore
                id=task.id,  # type: ignore
                task=task.task,  # type: ignore
                status=task.status.value,
                date=task.date.isoformat(),
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat()
            )
            for task in tasks
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching today's tasks: {str(e)}"
        )


@app.patch("/tasks/{task_id}/done", response_model=TaskResponse)
def mark_task_done(task_id: int, db: Session = Depends(get_db)):
    """
    Mark a task as completed.
    
    Updates the task status to COMPLETED and saves the update timestamp.
    
    Args:
        task_id: ID of the task to mark as done
        db: Database session (injected by FastAPI)
    
    Returns:
        Updated task
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
        setattr(task, 'status', TaskStatus.COMPLETED)
        setattr(task, 'updated_at', datetime.utcnow())
        db.commit()
        db.refresh(task)
        
        return TaskResponse(  # type: ignore
            id=task.id,  # type: ignore
            task=task.task,  # type: ignore
            status=task.status.value,
            date=task.date.isoformat(),
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat()
        )
    
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


@app.get("/trainer/message", response_model=TrainerResponse)
def get_trainer_motivation(db: Session = Depends(get_db)):
    """
    Get a gym coach-style motivation message based on today's commits.
    
    Analyzes today's GitHub commit activity and returns an aggressive,
    funny coaching message. The tone adapts based on performance:
    - 0 commits: Harsh warning
    - 1-4 commits: Motivational push
    - 5+ commits: Celebration
    
    Returns:
        JSON response with trainer message
    """
    try:
        # Get today's date
        today = date.today()
        
        # Query commits for today
        today_commits = db.query(Commit).filter(
            Commit.date == today
        ).all()
        
        # Sum up all commits for today
        commit_counts = [c.count for c in today_commits if c.count is not None]  # type: ignore
        total_commits = sum(commit_counts) if commit_counts else 0  # type: ignore
        
        # Get the trainer message
        trainer_data = get_trainer_message(int(total_commits))  # type: ignore
        
        return TrainerResponse(
            message=trainer_data["message"],
            style=trainer_data["style"],
            intensity=trainer_data["intensity"],
            commits_today=int(total_commits)  # type: ignore
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trainer message: {str(e)}"
        )


@app.get("/trainer/analyze", response_model=AnalysisResponse)
def analyze_performance(db: Session = Depends(get_db)):
    """
    Get AI-powered performance analysis for the last 7 days of commits.
    
    Uses Groq's LLM to generate a drill sergeant style performance review
    based on your commit history from the past 7 days. Requires GROQ_API_KEY
    to be configured in your .env file.
    
    Returns:
        JSON response with AI analysis and statistics
    """
    try:
        # Initialize response with defaults
        total_commits = 0
        unique_repos_list = []
        active_days = 0
        analysis = None
        
        # Get the last 7 days
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        
        # Query commits from the last 7 days
        commits = db.query(Commit).filter(
            Commit.date >= seven_days_ago,
            Commit.date <= today
        ).all()
        
        if commits:
            # Calculate summary stats
            commit_counts = [c.count for c in commits if c.count is not None]  # type: ignore
            total_commits = sum(commit_counts) if commit_counts else 0  # type: ignore
            unique_repos_list = sorted([str(r) for r in set(c.repo for c in commits)])  # type: ignore
            active_days = len(set(c.date for c in commits))
            
            # Only attempt AI analysis if we have commits and Groq key
            if GROQ_API_KEY:
                # Convert to JSON-serializable format for analyzer
                commits_data = [
                    {
                        "date": str(c.date),
                        "repo": str(c.repo),
                        "count": c.count if c.count is not None else 0
                    }
                    for c in commits
                ]
                
                try:
                    groq_client = Groq(api_key=GROQ_API_KEY)
                    analysis = analyze_with_groq(commits_data, groq_client)
                except Exception as groq_error:
                    print(f"[Analyzer] Groq error: {type(groq_error).__name__}: {groq_error}")
                    analysis = "AI analysis temporarily unavailable"
            else:
                analysis = "Groq API key not configured"
        else:
            analysis = "No commits found in the last 7 days"
        
        return AnalysisResponse(
            analysis=analysis if analysis else "No commits found",
            commits_total=int(total_commits),  # type: ignore
            unique_repositories=len(unique_repos_list),
            active_days=active_days,
            available=bool(analysis and analysis != "Groq API key not configured"),
            message=None if GROQ_API_KEY else "Groq API key not configured"
        )
    
    except Exception as e:
        print(f"[Analyzer] Error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing performance: {str(e)}"
        )


@app.get("/trainer/suggest", response_model=SuggestionsResponse)
def suggest_tasks(db: Session = Depends(get_db)):
    """
    Get AI-powered task suggestions for tomorrow based on recent commit activity.
    
    Uses Groq's LLM to suggest exactly 3 specific, actionable coding tasks
    the developer should work on tomorrow based on their recent commit history.
    
    Returns:
        JSON response with task suggestions
    """
    try:
        # Get the last 30 days of commit data to provide context
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Query commits from the last 30 days
        commits = db.query(Commit).filter(
            Commit.date >= thirty_days_ago,
            Commit.date <= today
        ).all()
        
        commits_analyzed = len(commits)
        
        # Get unique repository names
        unique_repos = sorted(set(c.repo for c in commits)) if commits else []
        repos_used = len(unique_repos)
        
        # Provide default suggestions if no commits or no Groq key
        suggestions = None
        message = None
        
        if not GROQ_API_KEY:
            message = "Groq API key not configured"
            suggestions = [
                "Review and refactor recent code changes",
                "Add more comprehensive unit tests",
                "Optimize database queries for performance"
            ]
        elif commits:
            # Convert to JSON-serializable format for analyzer
            commits_data = [
                {
                    "date": str(c.date),
                    "repo": c.repo,
                    "count": c.count
                }
                for c in commits
            ]
            
            try:
                groq_client = Groq(api_key=GROQ_API_KEY)
                suggestions = get_task_suggestions(commits_data, sorted([str(r) for r in set(c.repo for c in commits)]), groq_client)
                
                if not suggestions:
                    suggestions = [
                        "Review and refactor recent code changes",
                        "Add more comprehensive unit tests",
                        "Optimize database queries for performance"
                    ]
            except Exception as groq_error:
                print(f"[TaskSuggest] Groq error: {type(groq_error).__name__}: {groq_error}")
                suggestions = [
                    "Review and refactor recent code changes",
                    "Add more comprehensive unit tests",
                    "Optimize database queries for performance"
                ]
        else:
            unique_repos_list = []
            message = "No commits found in recent history"
            suggestions = [
                "Start a new feature or bug fix",
                "Improve code documentation",
                "Set up development environment"
            ]
        
        return SuggestionsResponse(
            suggestions=suggestions,
            available=bool(GROQ_API_KEY and commits),
            commits_analyzed=commits_analyzed,
            repos_used=repos_used,
            message=message
        )
    
    except Exception as e:
        print(f"[TaskSuggest] Error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating task suggestions: {str(e)}"
        )


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    Get overall statistics about commits and tasks.
    
    Returns a comprehensive summary of all activity:
    - Total commits from all time
    - Task statistics (pending, completed, in progress)
    - Current streak
    - Unique repositories
    - Active days
    
    Returns:
        JSON response with aggregated statistics
    """
    try:
        # Get all commits
        all_commits = db.query(Commit).all()
        total_commits = sum(c.count for c in all_commits)
        unique_repos = len(set(c.repo for c in all_commits)) if all_commits else 0
        active_days = len(set(c.date for c in all_commits)) if all_commits else 0
        
        # Get task statistics
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        
        # Get current streak
        streak_response = get_commit_streak(db)
        current_streak = streak_response.streak_days
        
        return StatsResponse(
            total_commits=int(total_commits),  # type: ignore
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            current_streak=current_streak,
            active_days=active_days,
            unique_repositories=unique_repos
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching statistics: {str(e)}"
        )


@app.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    """
    Get all tasks (optionally filter by status).
    
    Query Parameters:
        - status: Filter by status (pending, in_progress, completed, cancelled)
    
    Returns:
        List of all tasks
    """
    try:
        tasks = db.query(Task).order_by(Task.created_at.desc()).all()
        
        return [
            TaskResponse(  # type: ignore
                id=task.id,  # type: ignore
                task=task.task,  # type: ignore
                status=task.status.value,
                date=task.date.isoformat(),
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat()
            )
            for task in tasks
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching tasks: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
