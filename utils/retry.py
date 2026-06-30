"""
utils/retry.py
==============
Provides two retry mechanisms:

1. `@retry(times, exceptions, delay)`  – decorator for any callable
2. `retry_action(fn, *args, **kwargs)` – inline helper for page actions

The test-level retry (rerunning the whole test on failure) is handled
by pytest-rerunfailures, configured via pytest.ini `retries`.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry(
        times: int = 3,
        exceptions: Tuple[Type[BaseException], ...] = (Exception,),
        delay: float = 0.5,
        backoff: float = 1.0,
):
    """
    Decorator – retries the wrapped function up to `times` times.

    Parameters
    ----------
    times      : maximum retry attempts (total calls = times + 1)
    exceptions : tuple of exception types that trigger a retry
    delay      : initial wait between retries (seconds)
    backoff    : multiplier applied to `delay` after each attempt
                 (backoff=2.0 → exponential back-off)

    Example
    -------
    @retry(times=3, exceptions=(TimeoutError,), delay=1.0)
    def click_submit(page):
        page.locator("#submit").click()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exc: BaseException | None = None

            for attempt in range(1, times + 2):  # +2 so range includes final attempt
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt <= times:
                        logger.warning(
                            "[retry] %s failed (attempt %d/%d): %s – retrying in %.1fs",
                            func.__qualname__,
                            attempt,
                            times + 1,
                            exc,
                            current_delay,
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "[retry] %s exhausted %d retries. Last error: %s",
                            func.__qualname__,
                            times,
                            exc,
                        )
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def retry_action(
        fn: Callable,
        *args,
        times: int = 3,
        delay: float = 0.5,
        exceptions: Tuple[Type[BaseException], ...] = (Exception,),
        **kwargs,
):
    """
    Inline retry helper – useful inside page-object methods.

    Example
    -------
    retry_action(page.locator("#btn").click, times=3, delay=0.3)
    """
    current_delay = delay
    last_exc: BaseException | None = None

    for attempt in range(1, times + 2):
        try:
            return fn(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt <= times:
                logger.warning(
                    "[retry_action] attempt %d/%d failed: %s – retrying in %.1fs",
                    attempt, times + 1, exc, current_delay,
                             )
                time.sleep(current_delay)
                current_delay *= 1.5
            else:
                logger.error("[retry_action] exhausted retries. Last error: %s", exc)

    raise last_exc  # type: ignore[misc]