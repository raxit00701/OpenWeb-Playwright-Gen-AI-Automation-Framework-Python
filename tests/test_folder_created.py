import pytest
import json
from db.db_client import DBClient
from utils.jsonhandler import load_test_data
from pages.home_screen import HomeScreen

# -------------------------------
# Test Data
# -------------------------------
folder_test_data = load_test_data("folder_creation.json")


@pytest.mark.parametrize("test_case", folder_test_data.values(), ids=folder_test_data.keys())
@pytest.mark.utility
def test_verify_folder_created(authenticated_page, test_case):

    page = authenticated_page
    home = HomeScreen(page)
    db = DBClient()

    home.open_sidebar()
    home.open_folder()
    page.get_by_role("button").nth(4).click()

    page.get_by_role("textbox", name="Enter folder name").click()
    page.get_by_role("textbox", name="Enter folder name").fill(test_case["folder_name"])

    page.get_by_role("button", name="Upload", exact=True).click()
    page.locator("input[type='file']").nth(0).set_input_files(r"D:\test.png")

    page.get_by_role("textbox", name="Write your model system").click()
    page.get_by_role("textbox", name="Write your model system").fill(test_case["system_prompt"])

    page.get_by_role("button", name="Select Knowledge").click()
    page.get_by_role("button", name="-06-28").click()

    page.get_by_role("button", name="Save").click()
    page.get_by_role("button").nth(3).click()
    page.get_by_text(test_case["folder_name"], exact=True).click()



# Get current user's id
    user_result = db.execute("""
                             SELECT id
                             FROM user
                             ORDER BY rowid DESC
                                 LIMIT 1;
                             """)

    user_id = user_result[0][0]

    # Verify folder
    query = """
            SELECT
                folder.name,
                folder.data,
                file.filename
            FROM folder
                     INNER JOIN file
                                ON folder.user_id = file.user_id
            WHERE folder.user_id = ?; \
            """

    result = db.execute(query, (user_id,))

    assert result, "No folder record found in database."

    for row in result:
        folder_name, folder_data, filename = row

        print(f"\nFolder Name   : {folder_name}")
        print(f"File Name   : {filename}")

        if (
                folder_name == test_case["folder_name"]
                and filename == "test.png"
        ):
            data = json.loads(folder_data)

            print(f"System Prompt: {data['system_prompt']}")
            assert data["system_prompt"] == test_case["system_prompt"]
            break
    else:
        pytest.fail("Matching folder record not found in database.")