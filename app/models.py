"""
SQLAlchemy ORM models for DevTrackr database.

Defines the database schema for Users, Commits, and Tasks tables.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

# Base class for all models
Base = declarative_base()


class User(Base):
    """
    Users table - stores GitHub user information.
    
    Attributes:
        id: Primary key
        username: GitHub username
        github_id: GitHub unique identifier
        created_at: Timestamp when user record was created
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', github_id={self.github_id})>"


class Commit(Base):
    """
    Commits table - stores aggregated commit data from GitHub events.
    
    Attributes:
        id: Primary key
        date: Date of the commits (YYYY-MM-DD)
        repo: Repository name (e.g., "username/repo-name")
        count: Number of commits on this date in this repo
        created_at: Timestamp when record was created
    """
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    repo = Column(String(255), index=True, nullable=False)
    count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Commit(id={self.id}, date={self.date}, repo='{self.repo}', count={self.count})>"


class TaskStatus(str, enum.Enum):
    """Enum for task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    """
    Tasks table - stores development tasks and their status.
    
    Attributes:
        id: Primary key
        task: Task description
        status: Current status (pending, in_progress, completed, cancelled)
        date: Date the task is due or was created
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String(500), nullable=False)
    status = Column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    date = Column(Date, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Task(id={self.id}, task='{self.task}', status={self.status.value}, date={self.date})>"
