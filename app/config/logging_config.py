"""
Logging Configuration Module

This module provides colored console logging with structured formatters for the KIVI system.
Configures log levels, colors, and creates logger instances for different modules.

Dependencies:
- logging (standard library)
- colorlog (for colored console output)

Usage:
    from app.config.logging_config import setup_logging, logger, ai_logger
    
    setup_logging()
    logger.info("Application started")
    ai_logger.debug("AI prompt sent")
"""

import logging
import sys
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False
    print("Warning: colorlog not installed. Install with: pip install colorlog")


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Initialize logging configuration with colored console output.
    
    Configures:
    - Colored console formatter with timestamp, level, module, function
    - Log levels: DEBUG (blue), INFO (green), WARNING (yellow), ERROR (red)
    - Logger instances for different modules
    
    Args:
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR)
                  Defaults to INFO if not specified
    """
    # Determine log level
    if log_level is None:
        log_level = "INFO"
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    if HAS_COLORLOG:
        # Colored formatter with colorlog
        formatter = colorlog.ColoredFormatter(
            fmt="%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            reset=True,
            style='%'
        )
    else:
        # Standard formatter without colors
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add console handler
    root_logger.addHandler(console_handler)
    
    # Configure module-specific loggers
    loggers = [
        "kivi",
        "kivi.ai",
        "kivi.webhook",
        "kivi.db"
    ]
    
    for logger_name in loggers:
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(level)
        module_logger.propagate = True  # Propagate to root logger
    
    # Log initialization
    logger.info(f"Logging initialized with level: {log_level.upper()}")


# Create logger instances for different modules
logger = logging.getLogger("kivi")
ai_logger = logging.getLogger("kivi.ai")
webhook_logger = logging.getLogger("kivi.webhook")
db_logger = logging.getLogger("kivi.db")


# Example usage (commented out)
if __name__ == "__main__":
    # Test logging configuration
    setup_logging("DEBUG")
    
    logger.debug("This is a DEBUG message from main logger")
    logger.info("This is an INFO message from main logger")
    logger.warning("This is a WARNING message from main logger")
    logger.error("This is an ERROR message from main logger")
    
    ai_logger.info("AI provider called with prompt")
    webhook_logger.info("Webhook received from WhatsApp")
    db_logger.debug("Database query executed")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
