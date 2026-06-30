import pytest
import uuid
from db.db_client import DBClient
from utils.jsonhandler import load_test_data
import json


# -------------------------------
# Test Data
# -------------------------------
notes_test_data = load_test_data("notes_creation.json")


@pytest.mark.parametrize("test_case", notes_test_data.values(), ids=notes_test_data.keys())
def test_verify_notes_created(authenticated_page, test_case):

    page = authenticated_page
    db = DBClient()

    # Open Notes
    page.get_by_role("button", name="Open Sidebar", exact=True).click()
    page.get_by_role("link", name="Notes").click()
    page.get_by_role("button", name="New Note").click()

    # Editor
    editor = page.get_by_role("paragraph").first
    editor.click()
    editor.fill(test_case["note"])

    print("\n========== Note State ==========")
    print(f"Step 0:\n{page.locator('.ProseMirror').first.inner_html()}\n")

    # First formatting icon
    editor.click(click_count=3)
    page.locator(".hover\\:bg-gray-50.dark\\:hover\\:bg-gray-700").first.click()

    page.keyboard.press("ArrowRight")

    print(f"Step 1:\n{page.locator('.ProseMirror').first.inner_html()}\n")

    paragraph2 = page.get_by_text(test_case["note"])

    # Remaining formatting icons
    for i in range(2, 12):
        paragraph2.click(click_count=3)

        # Everything below is now properly indented inside the loop
        page.locator(f"div:nth-child({i}) > .hover\\:bg-gray-50").click()

        page.keyboard.press("ArrowRight")

        selection = page.evaluate("() => window.getSelection().toString()")

        print(f"Step {i:02d}")
        print(f"Selected: '{selection}'")
        print(page.locator(".ProseMirror").first.inner_html())
        print("-" * 60)


        # Wait for autosave (adjust if necessary)
        page.wait_for_timeout(1000)

        # Fetch latest saved note
        row = db.execute(
            "SELECT data FROM note ORDER BY created_at DESC LIMIT 1"
        )

        print("\n========== Latest Note ==========")
        print(row[0][0])


