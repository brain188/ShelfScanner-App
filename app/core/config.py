"""
Core configuration module using Pydantic Settings for type-safe configuration management.
Implements the singleton pattern for global settings access.
"""

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation and type checking.
    Automatically loads from environment variables and .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="ShelfScanner", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    allowed_hosts: List[str] = Field(default=["*"], description="Allowed CORS hosts")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    log_level: str = Field(default="info", description="Logging level")
    
    # Security Settings
    secret_key: str = Field(..., min_length=32, description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    bcrypt_rounds: int = Field(default=12, description="Bcrypt cost factor")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    
    # Supabase Settings
    supabase_url: AnyHttpUrl = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_key: str = Field(..., description="Supabase service key")
    
    # Database Settings
    database_url: str = Field(..., description="PostgreSQL database URL")
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Database max overflow connections")
    
    # Redis Cache Settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    cache_prefix: str = Field(default="shelfscanner", description="Cache key prefix")
    
    # Celery Settings
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    
    # Vector Database Settings (Qdrant)
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    qdrant_collection_name: str = Field(default="book_embeddings", description="Qdrant collection name")
    
    # OCR Settings
    tesseract_path: str = Field(default="/usr/bin/tesseract", description="Tesseract executable path")
    ocr_lang: str = Field(default="eng", description="OCR language")
    max_image_size_mb: int = Field(default=10, description="Maximum image size in MB")
    
    # AI Services Settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    llm_model: str = Field(default="gpt-4-turbo-preview", description="LLM model name")
    
    # External APIs
    google_books_api_key: Optional[str] = Field(default=None, description="Google Books API key")
    openlibrary_api_url: str = Field(
        default="https://openlibrary.org/api",
        description="Open Library API URL"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")
    
    # File Storage
    upload_dir: str = Field(default="/tmp/shelfscanner/uploads", description="Upload directory")
    max_upload_size_mb: int = Field(default=10, description="Maximum upload size in MB")
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "pdf"],
        description="Allowed file extensions"
    )
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Logging
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file_path: str = Field(
        default="/var/log/shelfscanner/app.log",
        description="Log file path"
    )
    log_rotation: str = Field(default="10 MB", description="Log rotation size")
    log_retention: str = Field(default="30 days", description="Log retention period")
    
    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes"""
        return self.max_upload_size_mb * 1024 * 1024
    
    @property
    def max_image_size_bytes(self) -> int:
        """Get max image size in bytes"""
        return self.max_image_size_mb * 1024 * 1024
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_production:
            # In production, return specific allowed origins
            return [str(origin) for origin in self.allowed_hosts if origin != "*"]
        return ["*"]
        

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (Singleton pattern).
    Uses lru_cache to ensure only one instance is created.
    """
    return Settings()


# Global settings instance
settings = get_settings()