import pytest
from db.db_client import DBClient
from utils.jsonhandler import load_test_data
from pages.home_screen import HomeScreen

# -------------------------------
# Test Data
# -------------------------------
workspace_test_data = load_test_data("workspace.json")

@pytest.mark.utility
def verify_workspace_data(db, test_case):
    query = """
            SELECT
                k.name,
                k.description,
                p.name,
                p.content,
                p.tags,
                s.name,
                s.description,
                s.content,
                t.name,
                t.meta
            FROM knowledge k
                     INNER JOIN prompt p
                                ON p.user_id = k.user_id
                     INNER JOIN skill s
                                ON s.user_id = k.user_id
                     INNER JOIN tool t
                                ON t.user_id = k.user_id
            ORDER BY
                k.id DESC,
                p.id DESC,
                s.id DESC,
                t.id DESC
                LIMIT 1; 
            """

    rows = db.execute(query)

    assert rows, "No data returned from database."

    (
        knowledge_name,
        knowledge_description,
        prompt_name,
        prompt_content,
        prompt_tags,
        skill_name,
        skill_description,
        skill_content,
        tool_name,
        tool_meta,
    ) = rows[0]

    print("\n========== DATABASE VALUES ==========")
    print(f"Knowledge Name        : {knowledge_name}")
    print(f"Knowledge Description : {knowledge_description}")
    print(f"Prompt Name           : {prompt_name}")
    print(f"Prompt Content        : {prompt_content}")
    print(f"Prompt Tags           : {prompt_tags}")
    print(f"Skill Name            : {skill_name}")
    print(f"Skill Description     : {skill_description}")
    print(f"Skill Content         : {skill_content}")
    print(f"Tool Name             : {tool_name}")
    print(f"Tool Meta             : {tool_meta}")
    print("=====================================\n")

    # Assertions
    assert knowledge_name == test_case["knowledge"]["name"]
    assert knowledge_description == test_case["knowledge"]["description"]

    assert prompt_name == test_case["prompt"]["name"]
    assert prompt_content == test_case["prompt"]["summary"]

    # tags are stored as JSON/string


    assert skill_name == test_case["skill"]["name"]
    assert skill_description == test_case["skill"]["description"]
    assert skill_content == test_case["skill"]["instructions"]

    assert tool_name == test_case["tool"]["name"]

    # meta is generally stored as JSON text
    assert test_case["tool"]["description"] in str(tool_meta)


@pytest.mark.parametrize(
    "test_case",
    workspace_test_data.values(),
    ids=workspace_test_data.keys()
)
def test_verify_workspace_creation(authenticated_page, test_case):

    page = authenticated_page
    home = HomeScreen(page)
    db = DBClient()

    home.open_workspace()

    # ------------------ Knowledge ------------------
    home.open_knowledge()
    page.get_by_role("link", name="New Knowledge").click()
    page.get_by_role("textbox", name="Name your knowledge base").fill(
        test_case["knowledge"]["name"]
    )
    page.get_by_role("textbox", name="Describe your knowledge base").fill(
        test_case["knowledge"]["description"]
    )
    page.get_by_role("button", name="Create Knowledge").click()

    page.wait_for_timeout(3000)

    # ------------------ Prompt ------------------
    home.open_prompts()
    page.get_by_role("link", name="New Prompt").click()
    page.get_by_role("textbox", name="Name").fill(
        test_case["prompt"]["name"]
    )
    page.get_by_role("combobox", name="Add a tag...").fill(
        test_case["prompt"]["tag"]
    )
    page.get_by_role("textbox", name="Write a summary in 50 words").fill(
        test_case["prompt"]["summary"]
    )
    page.get_by_role("button", name="Save & Create").click()

    page.wait_for_timeout(3000)

    # ------------------ Skill ------------------
    home.open_skills()
    page.get_by_role("link", name="New Skill").click()
    page.get_by_role("textbox", name="Skill Name").fill(
        test_case["skill"]["name"]
    )
    page.get_by_role("textbox", name="Skill Description").fill(
        test_case["skill"]["description"]
    )
    page.get_by_role("textbox", name="Skill Instructions").fill(
        test_case["skill"]["instructions"]
    )
    page.get_by_role("button", name="Save & Create").click()

    page.wait_for_timeout(3000)

    # ------------------ Tool ------------------
    home.open_tools()
    page.get_by_text("New Tool", exact=True).click()
    page.get_by_role("button", name="New Tool").nth(1).click()
    page.get_by_role("textbox", name="Tool Name").fill(
        test_case["tool"]["name"]
    )
    page.get_by_role("textbox", name="Tool Description").fill(
        test_case["tool"]["description"]
    )
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="Confirm").click()

    page.wait_for_timeout(3000)

    verify_workspace_data(db, test_case)

    # ------------------ Delete Tool ------------------
    page.locator("div.flex > button.self-center").nth(1).click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_role("button", name="Confirm").click()

    # ------------------ Delete Skill ------------------
    page.get_by_role("link", name="Skills").click()
    page.locator("div.flex > button.self-center").first.click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_role("button", name="Confirm").click()

    # ------------------ Delete Prompt ------------------
    page.get_by_role("link", name="Prompts").click()
    page.locator("button[type='button'] > svg.size-5").click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_role("button", name="Confirm").click()

    # ------------------ Delete Knowledge ------------------
    page.get_by_role("link", name="Knowledge").click()
    page.get_by_label("More Options").click()
    page.get_by_role("button", name="Delete").click()
    page.get_by_role("button", name="Confirm").click()