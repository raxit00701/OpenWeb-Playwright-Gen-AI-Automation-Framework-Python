from playwright.sync_api import Page


class HomeScreen:
    def __init__(self, page: Page):
        self.page = page

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    @property
    def new_chat_button(self):
        return self.page.get_by_role("button", name="New Chat")

    @property
    def chat_input(self):
        return self.page.get_by_role("paragraph")

    @property
    def send_message_button(self):
        return self.page.locator("#send-message-button")

    @property
    def open_sidebar_button(self):
        return self.page.get_by_role("button", name="Open Sidebar", exact=True)

    @property
    def notes_link(self):
        return self.page.get_by_role("link", name="Notes")

    @property
    def workspace_link(self):
        return self.page.get_by_role("link", name="Workspace")

    @property
    def knowledge_link(self):
        return self.page.get_by_role("link", name="Knowledge")

    @property
    def prompts_link(self):
        return self.page.get_by_role("link", name="Prompts")

    @property
    def skills_link(self):
        return self.page.get_by_role("link", name="Skills")

    @property
    def tools_link(self):
        return self.page.get_by_role("link", name="Tools")

    @property
    def folder_link(self):
        return self.page.get_by_role("button", name="Folders")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def click_new_chat(self):
        self.new_chat_button.click()

    def enter_prompt(self, prompt: str):
        self.chat_input.click()
        self.chat_input.fill(prompt)

    def click_send(self):
        self.send_message_button.click()

    def open_sidebar(self):
        self.open_sidebar_button.click()

    def open_notes(self):
        self.notes_link.click()

    def open_workspace(self):
        self.workspace_link.click()

    def open_knowledge(self):
        self.knowledge_link.click()

    def open_prompts(self):
        self.prompts_link.click()

    def open_skills(self):
        self.skills_link.click()

    def open_tools(self):
        self.tools_link.click()

    def open_folder(self):
        self.folder_link.click()