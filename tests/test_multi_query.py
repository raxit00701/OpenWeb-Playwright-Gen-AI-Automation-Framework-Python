import json
import re
import time
from difflib import SequenceMatcher

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
    (markdown, code blocks, bullets, toolbar text, etc.)
    don't cause false failures.
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

    # Normalize newlines
    text = text.replace("\r\n", "\n")

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

    # Remove expand icon
    text = text.replace("⌄", "")

    # Remove line numbers in code blocks
    text = re.sub(r"^\d+$", "", text, flags=re.MULTILINE)

    # Remove markdown bullets
    text = re.sub(r"^[ \t]*[-*•]\s*", "", text, flags=re.MULTILINE)

    # Remove numbered list prefixes
    text = re.sub(r"^\d+\.\s*", "", text, flags=re.MULTILINE)

    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

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

        # Step 1: Extract the current chat id from the browser
        chat_id = page.url.rstrip("/").split("/")[-1]

        # Step 2: Query only that chat
        # Note: We must keep 'output' in SELECT for the assistant response,
        # but we will ignore it when validating the user row where it is NULL.
        rows = db.execute(
            """
            SELECT role, content, output
            FROM chat_message
            WHERE id LIKE ?
            ORDER BY created_at ASC
            """,
            (f"{chat_id}-%",)
        )

        if not rows:
            failures.append(
                f"Query {index}: Expected chat_message records for chat {chat_id}, but found none."
            )
            continue

        # Step 3: Get the latest assistant and user from that chat
        assistant_row = None
        user_row = None

        for row in reversed(rows):
            if assistant_row is None and row[0] == "assistant":
                assistant_row = row
            elif user_row is None and row[0] == "user":
                user_row = row

            if assistant_row and user_row:
                break

        if not assistant_row or not user_row:
            failures.append(
                f"Query {index}: Missing required user or assistant record for this query."
            )
            continue

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

        # Decode JSON string if OpenWebUI stored it with extra quotes/escaping
        raw_user_content = user_row[1] or ""
        try:
            parsed_content = json.loads(raw_user_content)
            if isinstance(parsed_content, str):
                raw_user_content = parsed_content
        except Exception:
            pass

        db_prompt = normalize_response(raw_user_content)
        normalized_expected_prompt = normalize_response(prompt)

        print("\nExpected Prompt:")
        print(repr(normalized_expected_prompt))

        print("DB Prompt:")
        print(repr(db_prompt))

        if normalized_expected_prompt.lower() not in db_prompt.lower():
            failures.append(
                f"Query {index}: Prompt not stored correctly in DB."
            )

        # -------------------------------
        # Validate Assistant Record
        # -------------------------------

        # Step 4: Now that we correctly assigned assistant_row, parsing output is safe
        if assistant_row[0] != "assistant":
            failures.append(
                f"Query {index}: Expected DB role 'assistant', got '{assistant_row[0]}'."
            )

        db_output = assistant_row[2]
        db_response = ""

        try:
            if db_output:
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
            pass

        # Fallback if json parsing didn't trigger
        if not db_response:
            db_response = assistant_row[2] or assistant_row[1] or ""

        if not db_response.strip():
            failures.append(
                f"Query {index}: Assistant response is empty in DB."
            )

        # Normalize both responses
        ui_response = normalize_response(response)
        db_response = normalize_response(db_response)

        # Compare normalized content
        similarity = SequenceMatcher(
            None,
            ui_response,
            db_response,
        ).ratio()

        print(f"Similarity : {similarity:.3f}")

        if similarity < 0.97:
            failures.append(
                f"""
=========================================
Query {index}

UI response and DB response do not match.

Similarity : {similarity:.3f}

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
