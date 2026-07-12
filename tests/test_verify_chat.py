import json
from pages.home_screen import HomeScreen
import pytest

from db.db_client import DBClient
from utils.chat import wait_for_complete_response
from utils.jsonhandler import load_test_data


# -------------------------------
# Test Data
# -------------------------------

chat_test_data = load_test_data("chat_func.json")


@pytest.mark.parametrize(
    "test_case",
    chat_test_data.values(),
    ids=chat_test_data.keys()
)
@pytest.mark.chat
def test_verify_chat_created(authenticated_page, test_case):

    page = authenticated_page
    home = HomeScreen(page)
    db = DBClient()

    prompt = test_case["input"]["prompt"]
    expected_response = test_case["expected"]["response_contains"]

    # -------------------------------
    # Create New Chat
    # -------------------------------

    home.click_new_chat()
    home.enter_prompt(prompt)
    home.click_send()

    # -------------------------------
    # Wait for Assistant Response
    # -------------------------------

    response_text = wait_for_complete_response(page)

    # -------------------------------
    # Verify UI
    # -------------------------------

    print("\n========== UI ==========")
    print(f"Prompt   : {prompt}")
    print(f"Response : {response_text}")

    for keyword in expected_response:
        assert keyword.lower() in response_text.lower(), (
            f"'{keyword}' not found in assistant response."
        )

    print("✅ UI response matches expected output")

    # -------------------------------
    # Verify Database
    # -------------------------------

    chat_id = page.url.split("/c/")[-1]
    print(f"\nChat ID: {chat_id}")

    rows = db.execute(
        """
        SELECT role, content, output
        FROM chat_message
        WHERE chat_id = ?
        ORDER BY created_at
        """,
        (chat_id,)
    )

    assert rows, "No chat messages found in the database."

    print("\n========== DATABASE ==========")

    user_found = False
    assistant_found = False

    for role, content, output in rows:

        print(f"\nRole    : {role}")
        print(f"Content : {content}")

        if role == "user":
            if prompt.lower() in (content or "").lower():
                user_found = True
                print("✅ User prompt found")

        elif role == "assistant":

            assistant_text = ""

            if output:
                try:
                    output_json = json.loads(output)

                    for item in output_json:
                        if item.get("type") == "message":
                            for message in item.get("content", []):
                                assistant_text += message.get("text", "") + " "

                except Exception as e:
                    print(f"Unable to parse assistant output: {e}")

            print(f"Assistant Response : {assistant_text.strip()}")

            if all(
                    keyword.lower() in assistant_text.lower()
                    for keyword in expected_response
            ):
                assistant_found = True
                print("✅ Assistant response found")

    # -------------------------------
    # Final Assertions
    # -------------------------------

    print("\n========== RESULT ==========")

    assert user_found, "User prompt was not stored in the database."
    assert assistant_found, "Assistant response was not stored in the database."

    print("✅ User prompt successfully stored in DB")
    print("✅ Assistant response successfully stored in DB")

    after_chat_count = db.execute(
        "SELECT COUNT(*) FROM chat"
    )[0][0]

    print(f"\nChat count after : {after_chat_count}")