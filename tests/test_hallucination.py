import json
import re
import time
from difflib import SequenceMatcher

import pytest

from db.db_client import DBClient
from utils.chat import wait_for_complete_response
from utils.jsonhandler import load_test_data
from utils.evaluator import evaluate_response

hallucination_data = load_test_data("hallucination.json")


def normalize_response(text: str) -> str:
    """
    Normalize UI and DB responses so formatting differences
    (markdown, RAG statuses, UI controls) do not cause false mismatches.
    """
    if not text:
        return ""

    # Remove thinking banner
    text = re.sub(r"^Thought for \d+\s+seconds\s*", "", text, flags=re.IGNORECASE)

    # Remove OpenWebUI RAG/Tool invocation statuses (e.g., "Exploring query_knowledge_bases")
    text = re.sub(r"Exploring\s+[a-zA-Z0-9_]+", "", text, flags=re.IGNORECASE)

    # Markdown links
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\2", text)

    # Remove markdown formatting
    text = re.sub(r"[*_~]", "", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(https?://\S+)[).,]", r"\1", text)
    text = re.sub(r"^\s*[-*•]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "").replace("`", "")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s*", "", text, flags=re.MULTILINE)

    # Remove OpenWebUI toolbar words
    for token in ("Collapse", "Run", "Save", "Copy", "python"):
        text = text.replace(token, "")
    text = text.replace("⌄", "")

    # Normalize whitespace
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return "\n".join(line.strip() for line in text.splitlines()).strip()


@pytest.mark.parametrize(
    "test_case",
    hallucination_data.values(),
    ids=hallucination_data.keys()
)
@pytest.mark.chat
def test_hallucination(authenticated_page, test_case):

    page = authenticated_page
    db = DBClient()

    failures = []

    print("\n==============================")
    print("HALLUCINATION + DB VALIDATION TEST")
    print("==============================")

    for index, query in enumerate(test_case["queries"], start=1):

        prompt = query["prompt"]

        print(f"\nQuery {index}")
        print(f"Prompt: {prompt}")

        start = time.perf_counter()

        # -------------------------------------------------
        # Send Prompt
        # -------------------------------------------------
        page.locator("#chat-input").click()
        page.locator("#chat-input").fill(prompt)
        page.locator("#send-message-button").click()

        response = wait_for_complete_response(page)

        # Small stabilization fetch in case wait_for_complete_response
        # returns prematurely during RAG tool expansion
        page.wait_for_timeout(1000)
        final_ui_text = page.locator("#response-content-container").last.inner_text().strip()
        response = final_ui_text if final_ui_text else response

        latency = round(time.perf_counter() - start, 2)

        # -------------------------------------------------
        # DATABASE VALIDATION (Dynamic Polling)
        # -------------------------------------------------
        deadline = time.time() + 10
        while True:
            rows = db.execute("""
                              SELECT role, content, output
                              FROM chat_message
                              ORDER BY created_at DESC
                                  LIMIT 2
                              """)
            if len(rows) >= 2:
                break
            if time.time() > deadline:
                pytest.fail(f"Query {index}: DB message not written within 10 seconds.")
            time.sleep(0.5)

        assistant_row = rows[0]
        user_row = rows[1]

        print("--------------------------------------")
        print("DATABASE VALIDATION")
        print("--------------------------------------")
        print(f"Assistant Role : {assistant_row[0]}")
        print(f"User Role      : {user_row[0]}")

        # -----------------------------
        # User Validation
        # -----------------------------
        if user_row[0] != "user":
            failures.append(
                f"Query {index}: Expected role 'user', got '{user_row[0]}'."
            )

        if prompt.lower() not in (user_row[1] or "").lower():
            failures.append(
                f"Query {index}: Prompt not stored correctly."
            )

        # -----------------------------
        # Assistant Validation
        # -----------------------------
        if assistant_row[0] != "assistant":
            failures.append(
                f"Query {index}: Expected role 'assistant', got '{assistant_row[0]}'."
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

        # -----------------------------
        # Normalize & Compare Responses
        # -----------------------------
        ui_norm = normalize_response(response)
        db_norm = normalize_response(db_response)

        # Remove ALL whitespace for strict comparison
        ui_compare = re.sub(r"\s+", "", ui_norm)
        db_compare = re.sub(r"\s+", "", db_norm)

        # Exact match after normalization
        if ui_compare == db_compare:
            similarity = 1.0
        # Streaming/prefix match
        elif ui_compare.startswith(db_compare) or db_compare.startswith(ui_compare):
            similarity = 1.0
        # Fallback similarity
        else:
            similarity = SequenceMatcher(None, ui_compare, db_compare).ratio()

        if similarity < 0.95:
            failures.append(
                f"""
=========================================
Query {index}

Similarity: {similarity:.3f}

UI Response:
{ui_norm}

DB Response:
{db_norm}
=========================================
"""
            )
        else:
            print(f"✅ DB Validation : PASS ({similarity:.3f})")

        # -------------------------------------------------
        # Hallucination Validation
        # -------------------------------------------------
        result = evaluate_response(
            response=ui_norm,  # Pass the cleaned text to the evaluator
            required_keywords=query["required_keywords"],
            forbidden_keywords=query.get("forbidden_keywords", []),
            semantic_reference=query["semantic_reference"],
            threshold=query.get("threshold", 0.70),
        )

        print("--------------------------------------")
        print(f"Latency           : {latency:.2f}s")
        print(f"Semantic Score    : {result['score']:.2f}")
        print(f"Missing Keywords  : {result['missing']}")
        print(f"Forbidden Found   : {result['hallucinated']}")
        print(f"Cleaned Response:\n{ui_norm}")

        if result["passed"]:
            print("✅ Hallucination Validation : PASS")
        else:
            print("❌ Hallucination Validation : FAIL")

            failures.append(
                f"""
=========================================
Query {index}

Prompt:
{prompt}

Response:
{ui_norm}

Missing Keywords:
{result['missing']}

Forbidden Keywords:
{result['hallucinated']}

Semantic Score:
{result['score']:.2f}
=========================================
"""
            )

    # -------------------------------------------------
    # Final Report
    # -------------------------------------------------
    if failures:
        print("\n====================================")
        print("FAILED VALIDATIONS")
        print("====================================")

        for failure in failures:
            print(failure)

        pytest.fail("\n".join(failures))

    print("\n====================================")
    print("✅ ALL HALLUCINATION & DB VALIDATIONS PASSED")
    print("====================================")