"""
config/settings.py
==================
Loads the active environment config from pytest.ini → env = test|dev|prod
and exposes a single `Settings` object consumed by the rest of the framework.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Per-environment base URLs / credentials / feature flags
# ---------------------------------------------------------------------------
_ENV_CONFIG: dict[str, dict] = {
    "test": {
        "base_url": "http://localhost:3000/",
        "api_base_url": "https://api-test.example.com",
        "db_host": "db-test.example.com",
        "db_port": 5432,
        "db_name": "openwebui_test",
        "log_level": "DEBUG",
    },
    "dev": {
        "base_url": "https://openwebui-dev.example.com",
        "api_base_url": "https://api-dev.example.com",
        "db_host": "db-dev.example.com",
        "db_port": 5432,
        "db_name": "openwebui_dev",
        "log_level": "DEBUG",
    },
    "prod": {
        "base_url": "https://openwebui.example.com",
        "api_base_url": "https://api.example.com",
        "db_host": "db.example.com",
        "db_port": 5432,
        "db_name": "openwebui_prod",
        "log_level": "WARNING",
    },
}


@dataclass
class Settings:
    # --- resolved from pytest.ini ---
    env: str = "test"
    browser: str = "chromium"
    headless: bool = True
    incognito: bool = False
    video: str = "retain-on-failure"
    screenshot: str = "only-on-failure"
    slow_mo: int = 0
    timeout: int = 30_000
    retries: int = 2

    # --- populated from _ENV_CONFIG ---
    base_url: str = ""
    api_base_url: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    log_level: str = "DEBUG"

    # --- paths ---
    reports_dir: str = "reports/allure-results"
    logs_dir: str = "logs"
    videos_dir: str = "videos"
    screenshots_dir: str = "screenshots"

    def __post_init__(self) -> None:
        env_data = _ENV_CONFIG.get(self.env, _ENV_CONFIG["test"])
        for key, value in env_data.items():
            setattr(self, key, value)

        # Allow env-var overrides (useful in CI pipelines)
        if override := os.getenv("BASE_URL"):
            self.base_url = override

    # ------------------------------------------------------------------
    # Playwright launch / context kwargs derived from settings
    # ------------------------------------------------------------------
    def launch_kwargs(self) -> dict:
        return {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
        }

    def context_kwargs(self, tmp_video_dir: Optional[str] = None) -> dict:
        kwargs: dict = {
            "ignore_https_errors": True,
            "base_url": self.base_url,
        }

        # ---------- video ----------
        if self.video != "off":
            kwargs["record_video_dir"] = tmp_video_dir or self.videos_dir
            kwargs["record_video_size"] = {"width": 1280, "height": 720}

        # ---------- screenshot is handled per-test, not at context level ----------

        # ---------- incognito = no persistent storage ----------
        if self.incognito:
            # storage_state=None is default; explicitly clear any cookies/origins
            kwargs["storage_state"] = None

        return kwargs


def build_settings(config) -> Settings:
    """
    Called from conftest.py with the pytest `config` object.
    Reads every custom ini option and returns a fully-populated Settings.
    """

    def _bool(val: str) -> bool:
        return val.strip().lower() in {"true", "1", "yes"}

    return Settings(
        env=config.getini("env"),
        browser=config.getini("browser"),
        headless=_bool(config.getini("headless")),
        incognito=_bool(config.getini("incognito")),
        video=config.getini("video"),
        screenshot=config.getini("screenshot"),
        slow_mo=int(config.getini("slow_mo")),
        timeout=int(config.getini("timeout")),
        retries=int(config.getini("retries")),
    )