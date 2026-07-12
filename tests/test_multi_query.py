import json
import re
import time

import pytest

from db.db_client import DBClient
from utils.chat import wait_for_complete_response
from utils.jsonhandler import load_test_data


# -------------------------------
# Test Data
# -------------------------------

multi_query_data = load_test_data("multi_query.json")


def normalize_response(text: str) -> str:
    """
    Normalize UI and DB responses so formatting differences
    (markdown, code blocks, toolbar text, etc.) don't cause failures.
    """

    if not text:
        return ""

    # Remove reasoning header
    text = re.sub(
        r"^Thought for \d+\s+seconds\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove markdown code fences
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")

    # Remove inline markdown
    text = text.replace("`", "")
    text = text.replace("**", "")

    # Remove OpenWebUI toolbar text
    for token in (
            "Collapse",
            "Run",
            "Save",
            "Copy",
            "python",
    ):
        text = text.replace(token, "")

    # Remove line numbers in rendered code blocks
    text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)

    # Remove expand icon
    text = text.replace("⌄", "")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


@pytest.mark.parametrize(
    "test_case",
    multi_query_data.values(),
    ids=multi_query_data.keys()
)
@pytest.mark.chat
def test_verify_multi_query(authenticated_page, test_case):

    page = authenticated_page
    db = DBClient()

    print("\n========================================")
    print("      MULTI QUERY TEST STARTED")
    print("========================================")

    response_times = []
    failures = []

    for index, query in enumerate(test_case["queries"], start=1):

        prompt = query["prompt"]
        contains_all = query.get("contains_all", [])
        contains_any = query.get("contains_any", [])

        print(f"\n========== QUERY {index} ==========")
        print(f"Prompt : {prompt}")

        start_time = time.perf_counter()

        page.locator("#chat-input").click()
        page.locator("#chat-input").fill(prompt)
        page.locator("#send-message-button").click()

        response = wait_for_complete_response(page)

        latency = round(time.perf_counter() - start_time, 2)
        response_times.append(latency)

        print(f"Latency : {latency:.2f} seconds")
        print(f"Response:\n{response}\n")

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

        if len(rows) < 2:
            failures.append(
                f"Query {index}: Expected at least two chat_message records."
            )
            continue

        assistant_row = rows[0]
        user_row = rows[1]

        print("--------------------------------------")
        print("DATABASE VALIDATION")
        print("--------------------------------------")
        print(f"Assistant Role : {assistant_row[0]}")
        print(f"User Role      : {user_row[0]}")

        # -------------------------------
        # Validate User Record
        # -------------------------------

        if user_row[0] != "user":
            failures.append(
                f"Query {index}: Expected DB role 'user', got '{user_row[0]}'."
            )

        if prompt.lower() not in (user_row[1] or "").lower():
            failures.append(
                f"Query {index}: Prompt not stored correctly in DB."
            )

        # -------------------------------
        # Validate Assistant Record
        # -------------------------------

        if assistant_row[0] != "assistant":
            failures.append(
                f"Query {index}: Expected DB role 'assistant', got '{assistant_row[0]}'."
            )

        db_output = assistant_row[2]
        db_response = ""

        try:
            parsed = json.loads(db_output)

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
            db_response = assistant_row[2] or assistant_row[1] or ""

        if not db_response.strip():
            failures.append(
                f"Query {index}: Assistant response is empty in DB."
            )

        # Normalize both responses
        ui_response = normalize_response(response)
        db_response = normalize_response(db_response)

        # Compare normalized content
        if (
                ui_response != db_response
                and ui_response not in db_response
                and db_response not in ui_response
        ):
            failures.append(
                f"""
=========================================
Query {index}

UI response and DB response do not match.

Normalized UI Response:
{ui_response}

Normalized DB Response:
{db_response}
=========================================
"""
            )
        else:
            print("DB Validation : PASS")

        # =====================================================
        # CONTENT VALIDATION
        # =====================================================

        print("Validation Results:")

        # contains_all
        for keyword in contains_all:
            if keyword.lower() in ui_response.lower():
                print(f"  ✅ Found: {keyword}")
            else:
                print(f"  ❌ Missing: {keyword}")
                failures.append(
                    f"Query {index}: Expected '{keyword}' not found."
                )

        # contains_any
        if contains_any:

            found = [
                keyword
                for keyword in contains_any
                if keyword.lower() in ui_response.lower()
            ]

            if found:
                print(f"  ✅ Found one of: {found}")
            else:
                print(f"  ❌ None of {contains_any} found.")
                failures.append(
                    f"Query {index}: None of {contains_any} found."
                )

        print("✅ Query execution completed")

    # =====================================================
    # LATENCY REPORT
    # =====================================================

    print("\n========================================")
    print("LATENCY REPORT")
    print("========================================")

    for i, latency in enumerate(response_times, start=1):
        print(f"Query {i}: {latency:.2f} sec")

    average = sum(response_times) / len(response_times)

    print("----------------------------------------")
    print(f"Average : {average:.2f} sec")
    print(f"Maximum : {max(response_times):.2f} sec")
    print(f"Minimum : {min(response_times):.2f} sec")

    # =====================================================
    # FINAL ASSERTION SUMMARY
    # =====================================================

    print("\n========================================")
    print("ASSERTION SUMMARY")
    print("========================================")

    if failures:

        for failure in failures:
            print(f"❌ {failure}")

        pytest.fail(
            "\n\n========== VALIDATION FAILURES ==========\n\n"
            + "\n".join(failures)
        )

    print("✅ All UI, DB and content validations passed.")

    print("\n========================================")
    print("TEST PASSED")
    print("========================================")