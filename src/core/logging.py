import logging
import sys
from logging import Logger
from typing import Dict, Any

try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_uvicorn_log_config() -> Dict[str, Any]:
    """Get uvicorn-compatible log configuration"""
    # Use standard StreamHandler for uvicorn to avoid pickling issues with Rich Console
    # Our middleware will use Rich for better formatting
    handler_config = {
        "()": "logging.StreamHandler",
        "stream": "ext://sys.stderr",
    }
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": format_str,
                "datefmt": "[%X]",
            },
        },
        "handlers": {
            "default": handler_config,
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": [],  # Disable uvicorn access log, we use our own middleware
                "level": "INFO",
                "propagate": False,
            },
            "rag-system": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["default"],
            "level": "INFO",
        },
    }


def configure_logging() -> Logger:
    """Configure logging for the application"""
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    if RICH_AVAILABLE:
        # Create console and handler
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True
        )
        format_str = "%(message)s"
        datefmt = "[%X]"
    else:
        # Fallback to standard logging
        handler = logging.StreamHandler(sys.stderr)
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=format_str,
        datefmt=datefmt,
        handlers=[handler],
        force=True  # Override any existing configuration
    )
    
    # Get the rag-system logger
    logger = logging.getLogger("rag-system")
    logger.setLevel(logging.INFO)
    
    # Disable uvicorn default access log (we use our own middleware)
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = True
    uvicorn_access.handlers.clear()
    
    # Ensure logger outputs properly
    logger.info("日志系统已初始化，所有API请求将记录到控制台")
    
    return logger

