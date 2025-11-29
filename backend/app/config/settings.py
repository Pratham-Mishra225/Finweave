from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings using Pydantic Settings for environment variable management.
    
    Note: All required fields without defaults must be provided in the .env file or
    as environment variables. If any required field is missing, the application will
    fail to start with a validation error. Ensure all required configuration values
    are set before running the application.
    """
    
    # Firebase Configuration
    firebase_credentials_path: str
    
    # MongoDB Configuration
    mongodb_uri: str
    mongodb_db_name: str = "mumai_db"
    
    # Gemini AI Configuration
    gemini_api_key: str
    
    # CORS Configuration
    cors_origins: str
    
    # Security
    secret_key: str
    
    # Application Settings
    app_env: str = "development"
    debug: bool = True
    
    # Redis Configuration (for background tasks)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
