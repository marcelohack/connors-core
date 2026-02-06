"""Colorful logging utilities for Connors Trading System.

Provides colorful console logging that works both locally and in Docker containers.
Uses ANSI color codes that are preserved by Docker logs.
"""

import logging
import sys
import colorlog


def get_colorful_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a logger with colorful output.

    Creates a logger with colored output that works in Docker containers.
    The color codes are ANSI escape sequences that Docker preserves.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger with colorful output

    Example:
        >>> logger = get_colorful_logger(__name__)
        >>> logger.info("This is blue")
        >>> logger.warning("This is yellow")
        >>> logger.error("This is red")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create color formatter
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False

    return logger


def setup_strategy_logger(strategy_name: str, level: str = "INFO") -> logging.Logger:
    """Setup colorful logger specifically for strategy logic.

    Convenience function for creating loggers for strategy classes.

    Args:
        strategy_name: Name of the strategy (e.g., "LCRSI2")
        level: Logging level

    Returns:
        Configured colorful logger
    """
    logger_name = f"connors.strategies.{strategy_name}"
    return get_colorful_logger(logger_name, level)
