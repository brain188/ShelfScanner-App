"""
Logging configuration module with structured logging support.
Implements JSON logging for production and colored console logging for development.
"""
import sys
import logging
from pathlib import Path
from typing import Any, Dict
from loguru import logger
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging and redirect to loguru.
    This allows us to use loguru for all logging, including third-party libraries.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to loguru"""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds additional context to log records.
    """
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add application metadata
        log_record["app_name"] = settings.app_name
        log_record["app_version"] = settings.app_version
        log_record["environment"] = settings.environment
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name


def setup_logging() -> None:
    """
    Configure logging for the application.
    Sets up different logging configurations based on environment.
    """
    # Remove default loguru handler
    logger.remove()
    
    # Determine log level
    log_level = settings.log_level.upper()
    
    # Console logging configuration
    if settings.is_development:
        # Colored console logging for development
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # JSON logging for production
        logger.add(
            sys.stderr,
            format="{message}",
            level=log_level,
            serialize=True,  # Output as JSON
        )
    
    # File logging (always enabled)
    log_file_path = Path(settings.log_file_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_file_path),
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        format="{message}",
        level=log_level,
        serialize=True,  # Always use JSON for file logs
        enqueue=True,  # Asynchronous logging
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set log levels for third-party libraries
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logger.info(
        "Logging configured",
        environment=settings.environment,
        log_level=log_level,
        log_format=settings.log_format,
    )


def get_logger(name: str) -> Any:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logger.bind(module=name)


# Context manager for adding request context to logs
class LogContext:
    """
    Context manager for adding contextual information to logs.
    Useful for adding request IDs, user IDs, etc.
    """
    
    def __init__(self, **kwargs: Any):
        """Initialize with context data"""
        self.context = kwargs
        self.token = None
    
    def __enter__(self) -> "LogContext":
        """Enter context"""
        self.token = logger.contextualize(**self.context)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context"""
        if self.token:
            logger.remove(self.token)


# Initialize logging on module import
setup_logging()

# Export logger instance
__all__ = ["logger", "get_logger", "LogContext", "setup_logging"]