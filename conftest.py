"""
conftest.py  (root)
===================
Single entry-point that:
  • Registers all custom pytest.ini keys
  • Builds the global Settings object
  • Provides the `page` fixture (browser → context → page lifecycle)
  • Integrates Allure: attaches screenshot, video, and logs per test
  • Implements retry logic via pytest-rerunfailures configuration
  • Registers custom pytest markers (chat, utility)
"""

from __future__ import annotations

import logging
from pathlib import Path
import json
import allure
import pytest
from dotenv import load_dotenv

from APIs.login import login
from config.settings import Settings, build_settings
from drivers.driver_factory import DriverFactory
from utils.logger import setup_logger

logger = logging.getLogger(__name__)

load_dotenv()


# ---------------------------------------------------------------------------
# Authenticated Page Fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def authenticated_page(page, settings: Settings):
    """
    Returns an authenticated Playwright page.
    """

    token = login(settings.base_url)

    page.add_init_script(
        f"""
        window.localStorage.setItem("token", "{token}");
    """
    )

    page.goto(settings.base_url)
    page.wait_for_load_state("networkidle")

    return page


# ---------------------------------------------------------------------------
# Register pytest.ini options
# ---------------------------------------------------------------------------
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        "env",
        default="test",
        help="Environment: test|dev|prod",
    )
    parser.addini(
        "browser",
        default="chromium",
        help="Browser: chromium|firefox|webkit|chrome|edge",
    )
    parser.addini(
        "headless",
        default="true",
        help="Headless mode: true|false",
    )
    parser.addini(
        "incognito",
        default="false",
        help="Incognito mode: true|false",
    )
    parser.addini(
        "video",
        default="retain-on-failure",
        help="Video: on|off|retain-on-failure",
    )
    parser.addini(
        "screenshot",
        default="only-on-failure",
        help="Screenshot: on|off|only-on-failure",
    )
    parser.addini(
        "slow_mo",
        default="0",
        help="Slow motion delay (ms)",
    )
    parser.addini(
        "timeout",
        default="30000",
        help="Default timeout (ms)",
    )
    parser.addini(
        "retries",
        default="2",
        help="Retry count",
    )


# ---------------------------------------------------------------------------
# Session Settings Fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def settings(pytestconfig) -> Settings:
    settings = build_settings(pytestconfig)

    setup_logger(settings.log_level, settings.logs_dir)

    logger.info(
        "Framework started | env=%s | browser=%s | headless=%s | incognito=%s",
        settings.env,
        settings.browser,
        settings.headless,
        settings.incognito,
    )

    # Generate Allure metadata
    _write_allure_environment(settings, pytestconfig)
    _write_executor(settings)

    return settings


# ---------------------------------------------------------------------------
# Playwright Page Fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def page(settings: Settings, request: pytest.FixtureRequest):
    """
    Creates browser, context and page.
    Automatically attaches screenshot, video and logs to Allure.
    """

    factory = DriverFactory(settings)
    browser, context, pw_page = factory.create()

    yield pw_page

    failed = (
        request.node.rep_call.failed
        if hasattr(request.node, "rep_call")
        else False
    )

    test_name = (
        request.node.nodeid
        .replace("/", "_")
        .replace("\\", "_")
        .replace("::", "__")
    )

    video_path, screenshot_path = factory.teardown(
        browser=browser,
        context=context,
        page=pw_page,
        test_name=test_name,
        failed=failed,
    )

    _attach_screenshot(screenshot_path)
    _attach_video(video_path)
    _attach_logs(test_name, settings.logs_dir)


# ---------------------------------------------------------------------------
# Capture test result before teardown
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------
def pytest_configure(config: pytest.Config) -> None:
    """
    Register markers and configure retries.
    """

    # ----------------------------
    # Custom Test Groups
    # ----------------------------
    config.addinivalue_line(
        "markers",
        "chat: Chat related test cases",
    )

    config.addinivalue_line(
        "markers",
        "utility: Utility/Workspace/Knowledge/Notes/Tools related test cases",
    )

    # ----------------------------
    # Retry Configuration
    # ----------------------------
    retries = config.getini("retries")

    try:
        reruns = int(retries)
    except (ValueError, TypeError):
        reruns = 0

    if reruns > 0:
        try:
            import pytest_rerunfailures  # noqa: F401

            config.option.reruns = reruns
            config.option.reruns_delay = 1

        except ImportError:
            pass


# ---------------------------------------------------------------------------
# Helper Methods
# ---------------------------------------------------------------------------
def _write_allure_environment(
        settings: Settings,
        config: pytest.Config,
) -> None:
    """
    Creates reports/allure-results/environment.properties
    which Allure automatically displays in the Environment tab.
    """

    allure_results = Path(settings.reports_dir)
    allure_results.mkdir(parents=True, exist_ok=True)

    group = config.option.markexpr or "All"
    environment = settings.environment_info(group)

    env_file = allure_results / "environment.properties"

    with env_file.open("w", encoding="utf-8") as f:
        for key, value in environment.items():
            f.write(f"{key}={value}\n")


def _write_executor(settings: Settings) -> None:
    """
    Creates executor.json displayed in the Allure report header.
    """

    allure_results = Path(settings.reports_dir)
    allure_results.mkdir(parents=True, exist_ok=True)

    executor = settings.executor_info()

    with open(allure_results / "executor.json", "w", encoding="utf-8") as fp:
        json.dump(executor, fp, indent=4)


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
            name="Execution Log",
            attachment_type=allure.attachment_type.TEXT,
        )