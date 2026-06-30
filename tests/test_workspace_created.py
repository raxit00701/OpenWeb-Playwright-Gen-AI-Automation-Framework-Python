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

page.get_by_role("link", name="Workspace").click()
page.get_by_role("link", name="Knowledge").click()
page.get_by_role("link", name="New Knowledge").click()
page.get_by_role("textbox", name="Name your knowledge base").click()
page.get_by_role("textbox", name="Name your knowledge base").fill("this is for testing")
page.get_by_role("textbox", name="Describe your knowledge base").click()
page.get_by_role("textbox", name="Describe your knowledge base").fill("this is for testing")
page.get_by_role("button", name="Create Knowledge").click()
page.get_by_role("link", name="Prompts").click()
page.get_by_role("link", name="New Prompt").click()
page.get_by_role("textbox", name="Name").click()
page.get_by_role("textbox", name="Name").fill("this is for testing")
page.get_by_role("textbox", name="Add a tag...").click()
page.get_by_role("textbox", name="Add a tag...").fill("test")
page.get_by_text("Prompt Content").click()
page.get_by_role("textbox", name="Write a summary in 50 words").click()
page.get_by_role("textbox", name="Write a summary in 50 words").fill("this is for testing")
page.get_by_role("button", name="Save & Create").click()
page.get_by_role("link", name="Skills").click()
page.get_by_role("link", name="New Skill").click()
page.get_by_role("textbox", name="Skill Instructions").click()
page.get_by_role("textbox", name="Skill Instructions").fill("")
page.get_by_role("textbox", name="Skill Name").click()
page.get_by_role("textbox", name="Skill Name").fill("this is for testing")
page.get_by_role("textbox", name="Skill Instructions").click()
page.get_by_role("textbox", name="Skill Instructions").fill("this is for testing")
page.get_by_role("textbox", name="Skill Description").click()
page.get_by_role("textbox", name="Skill Description").fill("test")
page.get_by_role("button", name="Save & Create").click()
page.get_by_role("link", name="Tools").click()
page.get_by_role("textbox", name="Tool Name").fill("test")
page.get_by_role("textbox", name="Tool Description").fill("test")
