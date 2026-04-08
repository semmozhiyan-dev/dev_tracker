"""
Database connection and session management for DevTrackr.

Sets up SQLAlchemy engine and session factory for database operations.
Supports both SQLite (local development) and PostgreSQL (production).

Database Backends:
- SQLite (default): sqlite:///./devtrackr.db (local development)
- PostgreSQL: postgresql://user:password@host:port/database (production on Render)
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Any
from app.config import DATABASE_URL

# ============================================================================
# SQLAlchemy Engine Configuration
# ============================================================================

# Detect database type from URL
is_sqlite = "sqlite" in DATABASE_URL
is_postgresql = "postgresql" in DATABASE_URL

# Configure connection arguments based on database type
connect_args = {}
if is_sqlite:
    # SQLite specific: disable check_same_thread for multi-threaded servers
    connect_args = {"check_same_thread": False}

# Configure engine kwargs based on database type
engine_kwargs: dict[str, Any] = {
    "echo": False,  # Set to True for SQL query logging during development
}

if is_postgresql:
    # PostgreSQL specific: connection pool settings for production
    engine_kwargs["pool_pre_ping"] = True  # Verify connections before using
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections every hour

# Create SQLAlchemy engine with appropriate configuration
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs
)

# SQLite specific: enforce foreign keys on every connection
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session.
    
    Provides a SQLAlchemy session for each request. Automatically closes
    the session when the request is complete.
    
    Usage in route:
        from fastapi import Depends
        from sqlalchemy.orm import Session
        from app.database import get_db
        
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    
    This function:
    1. Creates all tables defined in app.models
    2. Works with both SQLite (local) and PostgreSQL (production)
    3. Is safe to call multiple times (only creates missing tables)
    
    Call this function during application startup to ensure the database
    schema is ready before the app starts handling requests.
    
    Example:
        if __name__ == "__main__":
            init_db()
            # start FastAPI app
    """
    from app.models import Base
    
    try:
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        
        # Log success with database info
        db_type = "PostgreSQL" if is_postgresql else "SQLite"
        print(f"✅ Database initialized successfully ({db_type})")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


def test_db_connection() -> bool:
    """
    Test the database connection.
    
    Useful for debugging connection issues. Raises an exception if
    the connection fails.
    
    Example:
        try:
            test_db_connection()
            print("Database connection OK!")
        except Exception as e:
            print(f"Connection failed: {e}")
    """
    try:
        with engine.connect() as connection:
            # Simple query to test connection
            connection.execute(text("SELECT 1"))
            print(f"✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
