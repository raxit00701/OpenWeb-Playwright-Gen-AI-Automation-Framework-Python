"""
drivers/driver_factory.py
=========================
DriverFactory is the single source of truth for creating Playwright
browsers, contexts, and pages.

Responsibilities
----------------
* Map the browser name from Settings → correct Playwright launcher
* Apply headless / slow_mo / incognito / video / viewport options
* Return a ready-to-use (browser, context, page) triple
* Provide a teardown helper that saves artefacts and closes everything
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from config.settings import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Browser channel map  (name used in pytest.ini → playwright channel/type)
# ---------------------------------------------------------------------------
_BROWSER_MAP = {
    # Playwright built-in browsers
    "chromium": ("chromium", None),
    "firefox": ("firefox", None),
    "webkit": ("webkit", None),
    # Real-browser channels (need those browsers installed on the OS)
    "chrome": ("chromium", "chrome"),
    "edge": ("chromium", "msedge"),
}


class DriverFactory:
    """
    Creates and tears down Playwright browser stacks.

    Usage (typically inside conftest fixtures):
    -------------------------------------------
        factory = DriverFactory(settings)
        browser, context, page = factory.create()
        yield page
        factory.teardown(browser, context, test_name, test_failed)
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._playwright: Optional[Playwright] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self) -> Tuple[Browser, BrowserContext, Page]:
        """Launch browser → create context → open page."""
        self._playwright = sync_playwright().start()

        browser = self._launch_browser()
        context = self._create_context(browser)
        page = context.new_page()
        page.set_default_timeout(self.settings.timeout)

        logger.info(
            "Browser ready: %s | headless=%s | incognito=%s | env=%s",
            self.settings.browser,
            self.settings.headless,
            self.settings.incognito,
            self.settings.env,
        )
        return browser, context, page

    def teardown(
            self,
            browser: Browser,
            context: BrowserContext,
            page: Page,
            test_name: str,
            failed: bool,
    ) -> Optional[str]:
        """
        1. Capture screenshot when required
        2. Close context  (flushes video to disk)
        3. Close browser
        4. Stop playwright
        5. Return final video path (or None)

        Returns the path to the saved video file so conftest can attach
        it to the Allure report.
        """
        screenshot_path: Optional[str] = None
        video_path: Optional[str] = None

        # ---- screenshot ----
        if self._should_capture_screenshot(failed):
            screenshot_path = self._save_screenshot(page, test_name)

        # ---- remember video source before context close ----
        raw_video = page.video

        # ---- close context (this finalises the video file) ----
        context.close()

        # ---- move / rename video ----
        if raw_video:
            video_path = self._finalise_video(raw_video, test_name, failed)

        # ---- close browser & playwright ----
        browser.close()
        if self._playwright:
            self._playwright.stop()

        return video_path, screenshot_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _launch_browser(self) -> Browser:
        browser_key = self.settings.browser.lower()
        if browser_key not in _BROWSER_MAP:
            raise ValueError(
                f"Unknown browser '{browser_key}'. "
                f"Valid options: {list(_BROWSER_MAP)}"
            )

        launcher_name, channel = _BROWSER_MAP[browser_key]
        launcher = getattr(self._playwright, launcher_name)

        launch_kwargs = self.settings.launch_kwargs()
        if channel:
            launch_kwargs["channel"] = channel

        logger.debug("Launching %s (channel=%s)", launcher_name, channel)
        return launcher.launch(**launch_kwargs)

    def _create_context(self, browser: Browser) -> BrowserContext:
        # Ensure video output dir exists
        videos_dir = Path(self.settings.videos_dir)
        videos_dir.mkdir(parents=True, exist_ok=True)

        ctx_kwargs = self.settings.context_kwargs(
            tmp_video_dir=str(videos_dir)
        )

        if self.settings.incognito:
            # Use an isolated storage state (no cookies / localStorage)
            ctx_kwargs.pop("storage_state", None)
            context = browser.new_context(**ctx_kwargs)
        else:
            context = browser.new_context(**ctx_kwargs)

        return context

    def _should_capture_screenshot(self, failed: bool) -> bool:
        mode = self.settings.screenshot
        if mode == "on":
            return True
        if mode == "only-on-failure":
            return failed
        return False  # "off"

    def _save_screenshot(self, page: Page, test_name: str) -> str:
        shots_dir = Path(self.settings.screenshots_dir)
        shots_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _safe_filename(test_name)
        path = str(shots_dir / f"{safe_name}.png")
        try:
            page.screenshot(path=path, full_page=True)
            logger.info("Screenshot saved → %s", path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not capture screenshot: %s", exc)
        return path

    def _finalise_video(self, raw_video, test_name: str, failed: bool) -> Optional[str]:
        """Move the temp video to a named file; delete if not needed."""
        mode = self.settings.video
        if mode == "off":
            try:
                raw_video.delete()
            except Exception:  # noqa: BLE001
                pass
            return None

        if mode == "retain-on-failure" and not failed:
            try:
                raw_video.delete()
            except Exception:  # noqa: BLE001
                pass
            return None

        # Save with a meaningful name
        videos_dir = Path(self.settings.videos_dir)
        dest = str(videos_dir / f"{_safe_filename(test_name)}.webm")
        try:
            raw_video.save_as(dest)
            logger.info("Video saved → %s", dest)
            return dest
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save video: %s", exc)
            return None


def _safe_filename(name: str) -> str:
    """Strip characters that are invalid in filenames."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)