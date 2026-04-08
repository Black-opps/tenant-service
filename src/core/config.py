"""
Configuration management for tenant service.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_VERSION: str = "v1"
    API_PORT: int = 8004
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = Field("sqlite:///./tenants.db", env="DATABASE_URL")
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8003"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()