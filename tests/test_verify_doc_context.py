import json
import time
from pathlib import Path
import pytest

from playwright.sync_api import Page

from APIs.chat_query import chat_query
from APIs.login import login
from APIs.upload_doc import upload_doc
from APIs.wait_for_processing import wait_for_processing
from db.db_client import DBClient

BASE_URL = "http://localhost:3000"
MODEL = "qwen/qwen3-14b"

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

FILE_PATH = DATA_DIR / "context_testpdf.pdf"
JSON_PATH = DATA_DIR / "context.json"

@pytest.mark.chat
def test_verify_doc_context(page: Page):

    db = DBClient()

    with open(JSON_PATH, encoding="utf-8") as f:
        test_data = json.load(f)

    page.goto(BASE_URL)

    token = login(BASE_URL)

    page.evaluate(
        """token => {
            localStorage.setItem("token", token);
        }""",
        token,
    )

    page.reload()
    page.wait_for_load_state("networkidle")

    # =====================================================
    # Upload Document
    # =====================================================

    uploaded = upload_doc(
        BASE_URL,
        token,
        str(FILE_PATH),
    )

    print(f"Uploaded File : {uploaded['filename']}")
    print(f"File ID       : {uploaded['id']}")

    wait_for_processing(
        BASE_URL,
        token,
        uploaded["id"],
    )

    print("\nDocument processing completed.\n")

    failures = []
    response_times = []

    # =====================================================
    # Query Loop
    # =====================================================

    for index, query in enumerate(test_data["queries"], start=1):

        prompt = query["prompt"]
        expected = query.get("contains_all", [])

        print("=" * 80)
        print(f"QUESTION {index}")
        print(f"Prompt : {prompt}")

        start = time.perf_counter()

        response = chat_query(
            base_url=BASE_URL,
            token=token,
            model=MODEL,
            prompt=prompt,
            file_data=uploaded,
        )

        latency = round(time.perf_counter() - start, 2)
        response_times.append(latency)

        answer = response["choices"][0]["message"]["content"]

        print("\nResponse:\n")
        print(answer)

        # =====================================================
        # DATABASE VALIDATION
        # =====================================================

        time.sleep(2)

        rows = db.execute("""
                          SELECT f.filename, c.title, c.chat
                          FROM file f
                                   INNER JOIN chat c ON f.user_id = c.user_id
                          WHERE c.title LIKE '%User Insult%'
                            AND f.filename LIKE '%context_testpdf%';
                          """)

        if not rows:

            failures.append(
                f"Question {index}: No matching file/chat record found in database."
            )

        else:

            filename, chat_title, chat_id = rows[0]

            print("\n----------------------------------------")
            print("DATABASE VALIDATION")
            print("----------------------------------------")

            print(f"Filename   : {filename}")
            print(f"Chat Title : {chat_title}")
            print(f"Chat ID    : {chat_id}")

            # -------------------------------------------------

            if filename != uploaded["filename"]:

                failures.append(
                    f"""
Question {index}

Uploaded filename does not match database.

Expected:
{uploaded['filename']}

Actual:
{filename}
"""
                )

            if not chat_title:

                failures.append(
                    f"Question {index}: Chat title is empty in database."
                )

            if not chat_id:

                failures.append(
                    f"Question {index}: Chat ID is NULL in database."
                )

            else:

                print("DB Validation : PASS")

        # =====================================================
        # CONTEXT VALIDATION
        # =====================================================

        print("\nValidation:")

        for keyword in expected:

            if keyword.lower() in answer.lower():

                print(f"  PASS : {keyword}")

            else:

                print(f"  FAIL : {keyword}")

                failures.append(
                    f"""
Question {index}

Prompt:
{prompt}

Expected:
{keyword}

Actual:
{answer}
"""
                )

        print(f"Latency : {latency:.2f}s")

    # =====================================================
    # LATENCY REPORT
    # =====================================================

    print("\n" + "=" * 80)
    print("LATENCY REPORT")
    print("=" * 80)

    for i, latency in enumerate(response_times, start=1):
        print(f"Question {i}: {latency:.2f}s")

    print("-" * 80)
    print(f"Average : {sum(response_times)/len(response_times):.2f}s")
    print(f"Maximum : {max(response_times):.2f}s")
    print(f"Minimum : {min(response_times):.2f}s")

    # =====================================================
    # ASSERTION SUMMARY
    # =====================================================

    if failures:

        print("\n" + "=" * 80)
        print("VALIDATION FAILURES")
        print("=" * 80)

        for failure in failures:
            print(failure)

        raise AssertionError("\n".join(failures))

    print("\n" + "=" * 80)
    print("ALL CONTEXT & DB VALIDATIONS PASSED")
    print("=" * 80)