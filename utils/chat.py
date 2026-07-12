from playwright.sync_api import Page, expect


def wait_for_complete_response(
        page: Page,
        timeout: int = 120000,
        poll_interval: int = 1000,
        stable_checks: int = 3,
) -> str:
    """
    Wait until the latest assistant response has finished streaming.

    Works for:
    - Single query
    - Multi-query conversations
    - Reasoning models
    - Code blocks
    - Markdown
    """

    assistant_locator = page.locator("#response-content-container").last

    expect(assistant_locator).to_be_visible(timeout=timeout)

    previous_text = ""
    stable_count = 0
    waited = 0

    while waited < timeout:

        current_text = assistant_locator.inner_text().strip()

        if not current_text:
            page.wait_for_timeout(poll_interval)
            waited += poll_interval
            continue

        if current_text.lower() == "thinking...":
            page.wait_for_timeout(poll_interval)
            waited += poll_interval
            continue

        if current_text == previous_text:
            stable_count += 1
        else:
            stable_count = 0
            previous_text = current_text

        if stable_count >= stable_checks:
            return current_text

        page.wait_for_timeout(poll_interval)
        waited += poll_interval

    raise TimeoutError("Timed out waiting for assistant response.")


def stop_response_generation(
        page: Page,
        wait_before_stop_ms: int = 500,
        timeout: int = 120000,
        poll_interval: int = 200,
) -> bool:
    """
    Wait until the assistant starts streaming, then click Stop.

    Returns:
        True  -> Stop button clicked.
        False -> Response completed before Stop could be clicked.
    """

    assistant_locator = page.locator("#response-content-container").last
    expect(assistant_locator).to_be_visible(timeout=timeout)

    stop_button = page.locator("#stop-message-generation")

    waited = 0

    while waited < timeout:

        text = assistant_locator.inner_text().strip()

        # Response has started
        if text and text.lower() != "thinking...":

            if stop_button.is_visible():

                page.wait_for_timeout(wait_before_stop_ms)

                if stop_button.is_visible():
                    stop_button.click(force=True)
                    page.wait_for_timeout(500)
                    return True

            # Response already finished
            return False

        page.wait_for_timeout(poll_interval)
        waited += poll_interval

    return False