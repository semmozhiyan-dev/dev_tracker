"""
Database connection and session management for DevTrackr.

Sets up SQLAlchemy engine and session factory for database operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

# Create SQLAlchemy engine
# connect_args is needed for SQLite to enable check_same_thread
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.
    
    Usage in route:
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
    
    Call this function during application startup.
    
    Example:
        if __name__ == "__main__":
            init_db()
            # run app
    """
    from app.models import Base
    
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
