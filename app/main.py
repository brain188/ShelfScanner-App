"""
FastAPI application entry point.
Configures middleware, routes, and startup/shutdown events.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.logging import logger
from app.api.v1 import auth, scan, books, recommendations, users
from app.db.supabase import SupabaseClient
from app.db.vector_db import VectorDBClient


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Initialize Sentry for error tracking
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        environment=settings.environment,
        release=settings.app_version,
    )
    logger.info("Sentry initialized", environment=settings.environment)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment
    )
    
    # Initialize database connections
    try:
        supabase_client = SupabaseClient()
        vector_db_client = VectorDBClient()
        
        # Health checks
        supabase_healthy = await supabase_client.health_check()
        vector_healthy = await vector_db_client.health_check()
        
        if supabase_healthy and vector_healthy:
            logger.info("All database connections healthy")
        else:
            logger.warning(
                "Some database connections unhealthy",
                supabase=supabase_healthy,
                vector_db=vector_healthy
            )
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered book shelf scanner with OCR and recommendations",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host
    )
    
    response = await call_next(request)
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    )
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    # Convert errors to JSON-serializable format
    def make_json_safe(errors):
        """Convert Pydantic validation errors to JSON-safe format"""
        json_safe_errors = []
        for error in errors:
            json_safe_error = {}
            for key, value in error.items():
                if isinstance(value, list):
                    # Handle lists that might contain non-serializable items
                    json_safe_error[key] = [
                        str(item) if not isinstance(item, (str, int, float, bool, type(None))) 
                        else item 
                        for item in value
                    ]
                elif isinstance(value, (str, int, float, bool, type(None))):
                    json_safe_error[key] = value
                else:
                    # Convert any other types to string
                    json_safe_error[key] = str(value)
            json_safe_errors.append(json_safe_error)
        return json_safe_errors
    
    errors = make_json_safe(exc.errors())
    
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.is_development else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.is_development else "Documentation disabled in production"
    }


# Include API routers
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"]
)

app.include_router(
    scan.router,
    prefix=f"{settings.api_v1_prefix}/scan",
    tags=["Scanning"]
)

app.include_router(
    books.router,
    prefix=f"{settings.api_v1_prefix}/books",
    tags=["Books"]
)

app.include_router(
    recommendations.router,
    prefix=f"{settings.api_v1_prefix}/recommendations",
    tags=["Recommendations"]
)

app.include_router(
    users.router,
    prefix=f"{settings.api_v1_prefix}",
    tags=["Users"]
)


# Metrics endpoint (Prometheus)
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Metrics endpoint enabled", port=settings.metrics_port)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level,
        workers=1 if settings.is_development else settings.workers
    )