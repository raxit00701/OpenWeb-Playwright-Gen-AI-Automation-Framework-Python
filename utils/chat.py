from playwright.sync_api import Page, expect


def wait_for_complete_response(
        page: Page,
        timeout: int = 40000,
        stable_time: int = 2000,
        max_wait: int = 60,
) -> str:

    assistant_locator = page.locator(
        "div[id='response-content-container'] div p[dir='auto']"
    ).last

    expect(assistant_locator).to_be_visible(timeout=timeout)

    response = ""

    for _ in range(max_wait):
        current = assistant_locator.inner_text().strip()

        if current == response and current:
            page.wait_for_timeout(stable_time)

            if assistant_locator.inner_text().strip() == current:
                return current

        response = current
        page.wait_for_timeout(1000)

    raise TimeoutError("Assistant response did not complete.")