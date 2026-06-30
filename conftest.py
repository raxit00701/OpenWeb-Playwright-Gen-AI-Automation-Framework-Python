"""
conftest.py  (root)
===================
Single entry-point that:
  • Registers all custom pytest.ini keys
  • Builds the global Settings object
  • Provides the `page` fixture (browser → context → page lifecycle)
  • Integrates Allure: attaches screenshot, video, and logs per test
  • Implements retry logic via pytest-rerunfailures configuration
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

import allure
import pytest
from APIs.login import login

from config.settings import Settings, build_settings
from drivers.driver_factory import DriverFactory
from utils.logger import setup_logger
from dotenv import load_dotenv
logger = logging.getLogger(__name__)


load_dotenv()


@pytest.fixture()
def authenticated_page(
        page,
        settings: Settings,
):
    """
    Returns a logged-in page.
    """

    token = login(settings.base_url)

    page.add_init_script(f"""
        window.localStorage.setItem("token", "{token}");
    """)

    page.goto("/")
    page.wait_for_load_state("networkidle")

    return page

# ---------------------------------------------------------------------------
# 1.  Register custom ini-options so pytest doesn't raise warnings
# ---------------------------------------------------------------------------
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini("env",         default="test",                 help="Environment: test|dev|prod")
    parser.addini("browser",     default="chromium",             help="Browser: chromium|firefox|webkit|chrome|edge")
    parser.addini("headless",    default="true",                 help="Headless mode: true|false")
    parser.addini("incognito",   default="false",                help="Incognito mode: true|false")
    parser.addini("video",       default="retain-on-failure",    help="Video: on|off|retain-on-failure")
    parser.addini("screenshot",  default="only-on-failure",      help="Screenshot: on|off|only-on-failure")
    parser.addini("slow_mo",     default="0",                    help="Slow-motion delay in ms")
    parser.addini("timeout",     default="30000",                help="Default timeout in ms")
    parser.addini("retries",     default="2",                    help="Retry count for failed tests")


# ---------------------------------------------------------------------------
# 2.  Session-scoped Settings fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def settings(pytestconfig) -> Settings:
    s = build_settings(pytestconfig)
    setup_logger(s.log_level, s.logs_dir)
    logger.info(
        "Framework started  env=%s  browser=%s  headless=%s  incognito=%s",
        s.env, s.browser, s.headless, s.incognito,
    )
    return s


# ---------------------------------------------------------------------------
# 3.  page fixture  (function scope → fresh browser per test)
# ---------------------------------------------------------------------------
@pytest.fixture()
def page(settings: Settings, request: pytest.FixtureRequest):
    """
    Yields a Playwright Page object.
    On teardown: captures screenshot/video, attaches them to Allure,
    then closes browser.
    """
    factory = DriverFactory(settings)
    browser, context, pw_page = factory.create()

    yield pw_page

    # ---- determine pass/fail ----
    failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    test_name = request.node.nodeid.replace("/", "_").replace("::", "__")

    # ---- teardown: screenshot + video ----
    video_path, screenshot_path = factory.teardown(
        browser, context, pw_page, test_name, failed
    )

    # ---- attach to Allure ----
    _attach_screenshot(screenshot_path)
    _attach_video(video_path)
    _attach_logs(test_name, settings.logs_dir)


# ---------------------------------------------------------------------------
# 4.  Capture pass/fail result BEFORE teardown runs
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ---------------------------------------------------------------------------
# 5.  Retry via pytest-rerunfailures
#     pytest.ini  retries = 2  →  --reruns 2  injected automatically
# ---------------------------------------------------------------------------
def pytest_configure(config: pytest.Config) -> None:
    retries = config.getini("retries")
    try:
        n = int(retries)
    except (ValueError, TypeError):
        n = 0
    if n > 0:
        # Inject --reruns only if pytest-rerunfailures is installed
        try:
            import pytest_rerunfailures  # noqa: F401
            config.option.reruns = n
            config.option.reruns_delay = 1  # 1 s between retries
        except ImportError:
            pass  # gracefully degrade if plugin not installed


# ---------------------------------------------------------------------------
# 6.  Parallel execution
#     pytest.ini  addopts = --numprocesses=4  activates xdist automatically
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _attach_screenshot(path: str | None) -> None:
    if path and Path(path).exists():
        allure.attach.file(
            path,
            name="Screenshot",
            attachment_type=allure.attachment_type.PNG,
        )


def _attach_video(path: str | None) -> None:
    if path and Path(path).exists():
        allure.attach.file(
            path,
            name="Video",
            attachment_type=allure.attachment_type.WEBM,
        )


def _attach_logs(test_name: str, logs_dir: str) -> None:
    log_file = Path(logs_dir) / f"{test_name}.log"
    if log_file.exists():
        allure.attach.file(
            str(log_file),
            name="Log",
            attachment_type=allure.attachment_type.TEXT,
        )