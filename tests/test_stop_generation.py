import json
import re
import time
from difflib import SequenceMatcher

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect

from db.db_client import DBClient
from utils.jsonhandler import load_test_data

stop_generation_data = load_test_data("stop_generation.json")


def normalize_response(text: str) -> str:
    """
    Normalize UI and DB responses so formatting differences
    (extra spaces/newlines/markdown/UI controls) do not cause failures.
    """

    if not text:
        return ""

    # Remove thinking banner
    text = re.sub(
        r"^Thought for \d+\s+seconds\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove markdown
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")
    text = text.replace("`", "")
    text = text.replace("**", "")

    # Remove UI actions
    for token in (
            "Collapse",
            "Run",
            "Save",
            "Copy",
            "python",
    ):
        text = text.replace(token, "")

    # Remove line numbers
    text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)

    text = text.replace("⌄", "")

    # -------------------------------
    # Normalize whitespace
    # -------------------------------

    # Windows -> Unix
    text = text.replace("\r\n", "\n")

    # Remove spaces before newline
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Collapse repeated spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Trim every line
    text = "\n".join(line.strip() for line in text.splitlines())

    # Remove leading/trailing whitespace
    return text.strip()


@pytest.mark.parametrize(
    "test_case",
    stop_generation_data.values(),
    ids=stop_generation_data.keys(),
)
@pytest.mark.chat
def test_stop_generation(authenticated_page, test_case):

    page = authenticated_page
    db = DBClient()

    print("\n=============================")
    print("STOP GENERATION TEST")
    print("=============================")

    page.locator("#chat-input").fill(test_case["prompt"])

    start = time.perf_counter()

    page.locator("#send-message-button").click()

    assistant = page.locator("#response-content-container").last
    expect(assistant).to_be_visible(timeout=10000)

    stop_button = page.locator(
        "//div[@class='self-end flex space-x-1 mr-1 shrink-0 gap-[0.5px]']//div[@class='flex']"
    ).first

    try:

        expect(stop_button).to_be_visible(timeout=1000)

        # Poll the text aggressively (every 50ms instead of 100ms)
        while True:
            text = assistant.inner_text().strip()

            # Check if we have actual generation (ignoring thinking state)
            if (
                    text
                    and text.lower() not in ("thinking...", "thought")
                    and len(text) >= test_case.get("min_response_length", 40)
            ):
                # INSTANTLY click stop the moment the threshold is hit
                print(f"Stream active (Length: {len(text)}). Intersecting now...")
                stop_button.click(force=True)
                break

            page.wait_for_timeout(50)

    except PlaywrightTimeoutError:

        pytest.fail(
            "Stop button never appeared before the response completed."
        )

    latency = round(time.perf_counter() - start, 2)

    # Wait until UI stabilizes
    previous = ""
    stable = 0

    while stable < 5:

        current = assistant.inner_text().strip()

        if current == previous:
            stable += 1
        else:
            stable = 0
            previous = current

        page.wait_for_timeout(500)

    final_response = previous

    print("--------------------------------")
    print(f"Stop Latency        : {latency:.2f}s")
    print(f"Characters Generated: {len(final_response)}")

    assert final_response, "Assistant response is empty."

    # =====================================================
    # DATABASE VALIDATION
    # =====================================================

    time.sleep(2)

    rows = db.execute("""
                      SELECT role, content, output
                      FROM chat_message
                      ORDER BY created_at DESC
                          LIMIT 2
                      """)

    assert len(rows) >= 2, (
        "Expected at least two chat_message records."
    )

    assistant_row = rows[0]
    user_row = rows[1]

    print("--------------------------------")
    print("DATABASE VALIDATION")
    print("--------------------------------")
    print(f"Assistant Role : {assistant_row[0]}")
    print(f"User Role      : {user_row[0]}")

    # Validate roles

    assert assistant_row[0] == "assistant", (
        f"Expected assistant role, got {assistant_row[0]}"
    )

    assert user_row[0] == "user", (
        f"Expected user role, got {user_row[0]}"
    )

    # Validate prompt

    assert test_case["prompt"].lower() in (
            user_row[1] or ""
    ).lower(), "Prompt not stored correctly."

    # Extract assistant response

    db_response = ""

    try:

        parsed = json.loads(assistant_row[2])

        for block in parsed:

            if block.get("type") != "message":
                continue

            for content in block.get("content", []):

                if content.get("type") == "output_text":
                    db_response = content.get("text", "")
                    break

            if db_response:
                break

    except Exception:

        db_response = (
                assistant_row[2]
                or assistant_row[1]
                or ""
        )

    assert db_response.strip(), (
        "Assistant response missing from DB."
    )

    # Normalize

    ui_response = normalize_response(final_response)
    db_response = normalize_response(db_response)

    # Remove all whitespace for comparison
    ui_comp = re.sub(r"\s+", "", ui_response)
    db_comp = re.sub(r"\s+", "", db_response)

    # Prefix comparison for streaming
    if (
            ui_comp == db_comp
            or ui_comp.startswith(db_comp)
            or db_comp.startswith(ui_comp)
    ):
        similarity = 1.0
    else:
        similarity = SequenceMatcher(None, ui_comp, db_comp).ratio()

    assert similarity >= 0.98, (
        f"\nSimilarity = {similarity:.3f}\n\n"
        f"UI:\n{ui_response}\n\n"
        f"DB:\n{db_response}"
    )

    print(f"Similarity Score : {similarity:.3f}")
    print("DB Validation : PASS")

    print("--------------------------------")
    print("PASS - Response stabilized after Stop.")