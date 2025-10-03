"""Logging utilities."""

import logging


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """Get a logger instance with optional level override.

    Args:
        name: Logger name (usually __name__)
        level: Optional logging level override

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
