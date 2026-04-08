"""
Configuration Module for DevTrackr

This module centralizes all environment variable management and validation
for the DevTrackr application. It ensures that:

1. All required configuration is present before the app starts
2. Clear error messages guide users on what's missing
3. Configuration is loaded from .env file using python-dotenv
4. Invalid configurations prevent app startup

Usage:
    from app.config import GITHUB_USERNAME, GITHUB_TOKEN, validate_config
    
    # Configuration is automatically validated on module import
    # If validation fails, a ConfigError is raised with helpful messages
    
    # In your code:
    validate_config()  # Call explicitly for additional validation
    username = GITHUB_USERNAME  # Use the validated variables
    token = GITHUB_TOKEN

Environment Variables:
    REQUIRED:
        - GITHUB_USERNAME: Your GitHub username
        - GITHUB_TOKEN: GitHub personal access token (read:user, public_repo scopes)
    
    OPTIONAL:
        - GITHUB_API_BASE: GitHub API endpoint (default: https://api.github.com)
        - DATABASE_URL: Database connection string
            * Production (PostgreSQL): postgresql://user:password@host:port/database
            * Local (SQLite): sqlite:///./devtrackr.db (default)
            * Render (convert postgres:// to postgresql:// automatically)
        - GROQ_API_KEY: Groq API key for AI features (optional)

Files:
    - .env: Local configuration (NOT in Git, created from .env.example)
    - .env.example: Template with all available options
    - .gitignore: Contains .env to prevent accidental commits
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file in project root
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


def get_required_env(var_name: str, description: Optional[str] = None) -> str:
    """
    Get a required environment variable with validation.
    
    This function ensures that critical configuration values are set before
    the application starts. If a required variable is missing or empty,
    it raises a detailed ConfigError to help users fix the issue.
    
    Args:
        var_name (str): Name of the environment variable to retrieve
        description (str, optional): Human-readable description of what this variable is used for.
                                     This appears in error messages to help users understand
                                     why a variable is required.
    
    Returns:
        str: The environment variable value
    
    Raises:
        ConfigError: If the variable is not set, is empty, or contains only whitespace.
                    The error message includes the variable name, description, and
                    guidance on how to fix it.
    
    Examples:
        >>> token = get_required_env("GITHUB_TOKEN", "Personal access token")
        >>> # If GITHUB_TOKEN is not set:
        >>> # ConfigError: Missing required environment variable: GITHUB_TOKEN
        >>> #   Purpose: Personal access token
        >>> #   Please set this variable in your .env file or as an environment variable.
    """
    value = os.getenv(var_name)
    
    if not value or not value.strip():
        error_msg = f"Missing required environment variable: {var_name}"
        if description:
            error_msg += f"\n  Purpose: {description}"
        error_msg += "\n  Please set this variable in your .env file or as an environment variable."
        raise ConfigError(error_msg)
    
    return value.strip()


def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an optional environment variable with a default fallback.
    
    This function safely retrieves configuration values that are not critical
    to application startup. If the variable is not set, a sensible default is used.
    
    Args:
        var_name (str): Name of the environment variable to retrieve
        default (str, optional): Default value if the variable is not set.
                                Defaults to None if not provided.
    
    Returns:
        str: The environment variable value if set, otherwise the default value.
    
    Examples:
        >>> api_base = get_optional_env("GITHUB_API_BASE", "https://api.github.com")
        >>> # Returns either the env var value or "https://api.github.com"
    """
    value = os.getenv(var_name)
    return value.strip() if value else default


def validate_config() -> None:
    """
    Validate that all required environment variables are properly set.
    
    This function performs comprehensive validation of the application's
    configuration. It should be called during application startup to ensure
    all necessary configuration is in place before any business logic runs.
    
    The function collects ALL validation errors and displays them together,
    rather than failing on the first error. This helps users fix all issues
    at once instead of playing a game of whack-a-mole with missing variables.
    
    Raises:
        ConfigError: If any required environment variable is missing or invalid.
                    The error message lists all issues found, with descriptions
                    and guidance for each one.
    
    Examples:
        >>> try:
        ...     validate_config()
        ... except ConfigError as e:
        ...     print(f"Configuration Error: {e}")
        ...     sys.exit(1)
    """
    # Define all required configuration variables with descriptions
    required_vars = [
        ("GITHUB_USERNAME", "GitHub username for fetching public events"),
        ("GITHUB_TOKEN", "GitHub personal access token for API authentication"),
    ]
    
    # Collect all validation errors
    errors = []
    for var_name, description in required_vars:
        try:
            get_required_env(var_name, description)
        except ConfigError as e:
            errors.append(str(e))
    
    # If any errors were found, combine them into a single message
    if errors:
        error_message = "Configuration validation failed:\n\n" + "\n\n".join(errors)
        raise ConfigError(error_message)


# ============================================================================
# Load and Export Configuration
# ============================================================================

# Validate configuration on module import
# This ensures that missing configuration is caught immediately when the
# module is imported, rather than later when a variable is actually used
try:
    validate_config()
except ConfigError as e:
    print(f"⚠️  Configuration Error:\n{e}")
    raise

# Load required environment variables
# These are guaranteed to exist and be non-empty due to validate_config() above
GITHUB_USERNAME = get_required_env("GITHUB_USERNAME", "GitHub username for fetching public events")
GITHUB_TOKEN = get_required_env("GITHUB_TOKEN", "GitHub personal access token for API authentication")

# Load optional environment variables with sensible defaults
GITHUB_API_BASE = get_optional_env("GITHUB_API_BASE", "https://api.github.com")

# Groq AI Configuration (for /trainer/analyze endpoint)
GROQ_API_KEY = get_optional_env("GROQ_API_KEY", None)

# Database Configuration
DATABASE_URL = get_optional_env(
    "DATABASE_URL",
    "sqlite:///./devtrackr.db"
)

# ============================================================================
# Database URL Validation and Conversion
# ============================================================================

# Fix postgres:// to postgresql:// for SQLAlchemy 2.0+ compatibility
# Render might return postgres://, but SQLAlchemy 2.0+ requires postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure SQLite URLs have proper format
# SQLite URLs need 3 slashes for relative paths: sqlite:///./devtrackr.db
# or 4 slashes for absolute paths: sqlite:////absolute/path
if DATABASE_URL and DATABASE_URL.startswith("sqlite://"):
    if not DATABASE_URL.startswith("sqlite:////") and not DATABASE_URL.startswith("sqlite:///"):
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite:///", 1)

# ============================================================================
# Configuration Summary (for debugging)
# ============================================================================
#
# To verify your configuration is loaded correctly, run:
#   python -c "from app.config import GITHUB_USERNAME; print(GITHUB_USERNAME)"
#
# To check all configuration values including database:
#   python -c "from app import config; print(f'User: {config.GITHUB_USERNAME}'); print(f'API: {config.GITHUB_API_BASE}'); print(f'DB: {config.DATABASE_URL}')"
#
# Database Support:
#   - SQLite (default local): sqlite:///./devtrackr.db
#   - PostgreSQL (production): postgresql://user:password@host:port/database
#   - Render PostgreSQL: Automatically converts postgres:// to postgresql://
#
# ============================================================================

