"""
Configuration module for DevTrackr application.

Loads and validates environment variables from .env file.
All environment configuration is centralized here.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


def get_required_env(var_name: str, description: str = None) -> str:
    """
    Get a required environment variable.
    
    Args:
        var_name: Name of the environment variable
        description: Optional description of what the variable is used for
        
    Returns:
        The environment variable value
        
    Raises:
        ConfigError: If the environment variable is not set or is empty
    """
    value = os.getenv(var_name)
    
    if not value or not value.strip():
        error_msg = f"Missing required environment variable: {var_name}"
        if description:
            error_msg += f"\n  Purpose: {description}"
        error_msg += "\n  Please set this variable in your .env file or as an environment variable."
        raise ConfigError(error_msg)
    
    return value


def get_optional_env(var_name: str, default: str = None) -> str:
    """
    Get an optional environment variable with a default value.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if not set
        
    Returns:
        The environment variable value or the default
    """
    return os.getenv(var_name, default)


def validate_config() -> None:
    """
    Validate that all required environment variables are set.
    
    Call this function during application startup to ensure
    all necessary configuration is in place.
    
    Raises:
        ConfigError: If any required environment variable is missing
    """
    required_vars = [
        ("GITHUB_USERNAME", "GitHub username for fetching public events"),
        ("GITHUB_TOKEN", "GitHub personal access token for API authentication"),
    ]
    
    errors = []
    for var_name, description in required_vars:
        try:
            get_required_env(var_name, description)
        except ConfigError as e:
            errors.append(str(e))
    
    if errors:
        error_message = "Configuration validation failed:\n\n" + "\n\n".join(errors)
        raise ConfigError(error_message)


# Load and validate configuration
GITHUB_USERNAME = get_required_env("GITHUB_USERNAME", "GitHub username for fetching public events")
GITHUB_TOKEN = get_required_env("GITHUB_TOKEN", "GitHub personal access token for API authentication")
GITHUB_API_BASE = get_optional_env("GITHUB_API_BASE", "https://api.github.com")

# Database Configuration
DATABASE_URL = get_optional_env(
    "DATABASE_URL",
    "sqlite:///./devtrackr.db"
)

# Convert SQLite URLs for SQLAlchemy compatibility
# SQLite URLs need 4 slashes: sqlite:////absolute/path or sqlite:///relative/path
if DATABASE_URL.startswith("sqlite://"):
    # Ensure proper SQLite URL format
    if not DATABASE_URL.startswith("sqlite:////") and not DATABASE_URL.startswith("sqlite:///"):
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite:///")

# Validate on module import
try:
    validate_config()
except ConfigError as e:
    print(f"⚠️  Configuration Error:\n{e}")
    raise
