"""Logging configuration utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from loguru import logger


DEFAULT_LOG_PATH = Path("logs/system.log")


def configure_logging(log_path: Optional[str | Path] = None) -> None:
    path = Path(log_path) if log_path else DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(path, rotation="10 MB", retention="7 days")
    logger.add(lambda msg: print(msg, end=""))
