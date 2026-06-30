"""
utils/logger.py
===============
Configures the root Python logger once per session.
Each test gets its own log file so Allure can attach it individually.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(log_level: str = "DEBUG", logs_dir: str = "logs") -> None:
    """
    Call once at session start.
    Sets the root logger to `log_level`, outputs to console + rotating file.
    """
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on re-import (e.g. xdist workers)
    if root.handlers:
        return

    # ---- Console handler ----
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(ch)

    # ---- Session-wide file handler ----
    session_log = Path(logs_dir) / "session.log"
    fh = logging.FileHandler(str(session_log), encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(fh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


class TestLogger:
    """
    Per-test logger that writes to a dedicated file.
    Instantiate in a test fixture; call .close() on teardown.

    Usage:
        tlog = TestLogger("tests_login__test_valid", "logs")
        tlog.info("page loaded")
        tlog.close()
    """

    def __init__(self, test_name: str, logs_dir: str = "logs") -> None:
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        self._path = Path(logs_dir) / f"{test_name}.log"
        self._logger = logging.getLogger(test_name)
        self._logger.setLevel(logging.DEBUG)

        # Only add the file handler once
        if not any(
                isinstance(h, logging.FileHandler)
                and getattr(h, "baseFilename", None) == str(self._path.resolve())
                for h in self._logger.handlers
        ):
            fh = logging.FileHandler(str(self._path), encoding="utf-8")
            fh.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
            self._logger.addHandler(fh)

    # Delegate common log methods
    def debug(self, msg, *args, **kwargs):   self._logger.debug(msg, *args, **kwargs)
    def info(self, msg, *args, **kwargs):    self._logger.info(msg, *args, **kwargs)
    def warning(self, msg, *args, **kwargs): self._logger.warning(msg, *args, **kwargs)
    def error(self, msg, *args, **kwargs):   self._logger.error(msg, *args, **kwargs)

    def close(self) -> str:
        """Flush / close file handlers and return log file path."""
        for h in list(self._logger.handlers):
            h.flush()
            h.close()
            self._logger.removeHandler(h)
        return str(self._path)