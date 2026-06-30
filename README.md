```markdown
<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:03001C,30:0f3443,60:34e89e,100:00D4FF&height=230&section=header&text=OPEN%20WEBUI%20AUTOMATION&fontSize=52&fontColor=ffffff&fontAlignY=38&fontAlign=50&desc=Enterprise-Grade%20Python%20Test%20Automation%20Framework&descAlignY=60&descSize=17&descColor=C8B8FF&animation=fadeIn" width="100%"/>
  <br/><br/>

  **API-Assisted · Docker-Integrated DB Client · Multi-Environment · Fixture-Driven**

  *A scalable, robust framework built to test the Open WebUI platform.*
</div>

---

## 🚧 Active Development

> **This project is currently a Work In Progress (WIP).**

It is actively being developed to showcase advanced SDET capabilities, including:

- **Direct Container Interaction:** Executing SQLite queries directly inside the `open-webui` Docker container via Python subprocesses.
- **Hybrid Testing Strategy:** Combining UI validation (Playwright) with API-level state injection (bypassing the UI for login/auth via local storage).
- **Scalable Architecture:** Utilizing Pytest fixtures, externalized JSON data, dynamic environment configurations, and comprehensive Allure reporting.

---

## 📋 Table of Contents

| #  | Section                          | #  | Section                              |
|----|----------------------------------|----|--------------------------------------|
| 01 | [🏗️ Framework Architecture](#-framework-architecture) | 05 | [🐳 Docker DB Integration](#-docker-db-integration) |
| 02 | [✨ Key Features](#-key-features) | 06 | [📡 API Layer & State Injection](#-api-layer--state-injection) |
| 03 | [📁 Project Structure](#-project-structure) | 07 | [📈 Execution & Reporting](#-execution--reporting) |
| 04 | [🎯 Current Test Coverage](#-current-test-coverage) | 08 | [📜 License](#-license) |

---

## 🏗️ Framework Architecture

```text
╔═════════════════════════════════════════════════════════════════════════╗
║                OPEN WEBUI AUTOMATION — FRAMEWORK OVERVIEW               ║
╠══════════════╦══════════════╦══════════════╦══════════════════════════╣
║ 🧪 TESTS/    ║ 🐳 DB/       ║ 📡 APIs/     ║ ⚙️ UTILS/                ║
║ Test Specs   ║ DB Client    ║ API Helpers  ║ Logging, JSON, Retries   ║
║ (.py)        ║ (SQLite)     ║ (Auth/Tokens)║ (Core Logic)             ║
╠══════════════╩══════════════╩══════════════╩══════════════════════════╣
║ 📦 DATA/ (JSON)                                                         ║
║ Chat Functions · Folder Creation · Workspace · Notes Creation           ║
╠═════════════════════════════════════════════════════════════════════════╣
║ 🛠️ conftest.py & config/settings.py                                    ║
║ ENV · BROWSER · HEADLESS · INCOGNITO · WORKERS · FIXTURES · DRIVERS     ║
╠══════════════╦═══════════════════════════╦══════════════════════════════╣
║ 📊 Allure    ║ 🎬 Test Artifacts         ║ 🌐 Environment               ║
║ Reports      ║ Logs, Videos, Screenshots ║ Test | Dev | Prod            ║
╚══════════════╩═══════════════════════════╩══════════════════════════════╝
```

---

## ✨ Key Features

| 🔷 Feature                  | 📝 Description |
|-----------------------------|---------------|
| 🌍 **Dynamic Configurations** | Switch between `test`, `dev`, and `prod` targets via `pytest.ini`. |
| 🐳 **Dockerized DB Queries** | The `DBClient` executes SQL directly inside the `open-webui` container using `subprocess` and returns parsed JSON data. |
| 📡 **API-Assisted Setup**    | UI tests start instantly. The `authenticated_page` fixture hits the login API and injects the token into `localStorage`. |
| 🗂️ **Data-Driven Execution** | Configurations and test parameters are fully externalized into the `data/` directory via JSON. |
| 🎬 **Rich Artifacts**        | Automatically attaches screenshots, videos, and per-test logs to Allure on test failure. |
| 🔄 **Smart Retries**         | Configured via `pytest-rerunfailures` in the master `pytest.ini` setup. |
| 🚙 **Driver Factory**        | Centralized Playwright browser, context, and page generation in `drivers/`. |

---

## 📁 Project Structure

The project is heavily modularized to separate configuration, test logic, data, and reporting.

- **🧪 `tests/`** — Pytest test specifications
  - `test_folder_created.py`
  - `test_notes_created.py`
  - `test_verify_chat.py`
  - `test_workspace_created.py`

- **⚙️ `config/`** — Global configuration
  - `settings.py` — Multi-environment dataclass

- **📡 `APIs/`** — Programmatic API helpers
  - `login.py` — REST-based auth token extraction

- **🐳 `db/`** — Database interaction layer
  - `db_client.py` — Docker-exec wrapper for internal SQLite DB

- **🚙 `drivers/`** — Browser instantiation logic
  - `driver_factory.py` — Playwright context/page setup and teardown

- **📦 `data/`** — Externalized test inputs (JSON)
  - `chat_func.json`, `folder_creation.json`, `notes_creation.json`, `workspace.json`

- **🛠️ `utils/`** — Shared helper functions
  - `chat.py`, `jsonhandler.py`, `logger.py`, `retry.py`

- **🎬 `reports/`**, **📝 `logs/`**, **🎥 `videos/`** — Automatically generated artifacts
- **📄 `conftest.py`** — Pytest fixtures, Allure hooks, page setup
- **🔧 `pytest.ini`** — Master framework configuration

---

## 🎯 Current Test Coverage

| Feature                        | Status | Automatable with Playwright? |
|--------------------------------|--------|------------------------------|
| Chat (Send prompt & response)  | ✅     | ✅ |
| Streaming responses            | ✅     | ✅ |
| Loading spinner                | ✅     | ✅ |
| Stop Generation                | ✅     | ✅ |
| Regenerate Response            | ✅     | ✅ |
| New Chat / Chat History        | ✅     | ✅ |
| Rename / Delete Chat           | ✅     | ✅ |
| Prompt Input (edge cases)      | ✅     | ✅ |
| Markdown & Code Block Rendering| ✅     | ✅ |
| File Upload (PDF, DOCX, etc.)  | ✅     | ✅ |
| **PDF Context Retrieval**      | ✅     | ✅ |
| **Hallucination / Groundedness** | ✅   | ✅ *(with controlled test doc)* |
| Network Failure & Error Recovery | ✅  | ✅ |
| Session Expiry                 | ✅     | ✅ |

---

## 🐳 Docker DB Integration

A standout feature is the ability to query the backend database directly for absolute state verification.

```python
class DBClient:
    CONTAINER_NAME = "open-webui"
    DB_PATH = "/app/backend/data/webui.db"

    def execute(self, query, params=None):
        """Executes SQL directly inside the running Docker container."""
        script = f"""
import sqlite3, json
conn = sqlite3.connect('{self.DB_PATH}')
cursor = conn.cursor()
cursor.execute({query!r}, {params!r})
print(json.dumps(cursor.fetchall()))
conn.close()
"""
        result = subprocess.run(
            ["docker", "exec", self.CONTAINER_NAME, "python", "-c", script],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout.strip())
```

---

## 📡 API Layer & State Injection

The `authenticated_page` fixture bypasses slow UI login by using REST auth and injecting the token directly into `localStorage`.

```python
@pytest.fixture()
def authenticated_page(page, settings: Settings):
    """Returns a fully logged-in page. Bypasses the UI login screen."""
    # 1. Fetch token via REST API
    token = login(settings.base_url)
    
    # 2. Inject directly into local storage
    page.add_init_script(f"""
        window.localStorage.setItem("token", "{token}");
    """)
    
    # 3. Navigate straight to the dashboard
    page.goto("/")
    page.wait_for_load_state("networkidle")
    return page
```

---

## 📈 Execution & Reporting

### Local Execution

```bash
# Run all tests (serial)
pytest

# Run in specific environment
pytest --env=dev

# Run specific test file
pytest tests/test_verify_chat.py
```

### Allure Reporting

On failure, the framework automatically attaches:
- Screenshot of the failure state
- Video recording of the session
- Per-test log file

```bash
allure serve reports/allure-results
```

---

## 📜 License

*(Add your license information here)*

---

**Built with ❤️ for robust Open WebUI testing.**
```

This version is cleaner, better aligned, uses proper Markdown tables, improved code blocks, consistent emojis, and clearer hierarchy. Let me know if you'd like any specific sections expanded or further adjustments!
