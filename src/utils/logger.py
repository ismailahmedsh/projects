"""Provide a lightweight logger abstraction."""
from __future__ import annotations

import logging
from typing import Any

try:  # pragma: no cover - optional dependency
    from loguru import logger as loguru_logger
except Exception:  # pragma: no cover
    loguru_logger = None  # type: ignore


class _FallbackLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("dynamic_expert_system")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._logger, item)


def get_logger() -> Any:
    if loguru_logger is not None:
        return loguru_logger
    return _FallbackLogger()
