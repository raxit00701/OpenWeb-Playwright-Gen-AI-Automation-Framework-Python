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
def test_verify_chat_created(authenticated_page, test_case):

    page = authenticated_page
    db = DBClient()

    prompt = test_case["input"]["prompt"]
    expected_response = test_case["expected"]["response_contains"]

    # -------------------------------
    # Create New Chat
    # -------------------------------

    page.get_by_role("button", name="New Chat").click()

    chat_input = page.get_by_role("paragraph")
    chat_input.click()
    chat_input.fill(prompt)

    page.locator("#send-message-button").click()

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
        SELECT id, content
        FROM chat_message
        WHERE id LIKE ?
        ORDER BY id
        """,
        (f"{chat_id}-%",)
    )

    assert rows, "No chat messages found in the database."

    print("\n========== DATABASE ==========")

    user_found = False
    assistant_found = False

    for message_id, content in rows:
        print(f"\nID      : {message_id}")
        print(f"Content : {content}")

        if prompt.lower() in content.lower():
            user_found = True
            print("✅ User prompt found")

        if all(
                keyword.lower() in content.lower()
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