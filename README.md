<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:03001C,30:0f3443,60:34e89e,100:00D4FF&height=230&section=header&text=OPEN%20WEBUI%20AUTOMATION&fontSize=52&fontColor=ffffff&fontAlignY=38&fontAlign=50&desc=Enterprise-Grade%20Python%20Test%20Automation%20Framework&descAlignY=60&descSize=17&descColor=C8B8FF&animation=fadeIn" width="100%"/>

<br/>



> **API-Assisted · Docker-Integrated DB Client · Multi-Environment · Fixture-Driven**
> *A scalable, robust framework built to test the Open WebUI platform.*



## 🚧 Active Development

> **This project is currently a Work In Progress (WIP).**
> It is actively being developed to showcase advanced SDET capabilities, including:
> * **Direct Container Interaction:** Executing SQLite queries directly inside the `open-webui` Docker container via Python subprocesses.
> * **Hybrid Testing Strategy:** Combining UI validation (Playwright) with API-level state injection (bypassing the UI for login/auth via local storage).
> * **Scalable Architecture:** Utilizing Pytest fixtures, externalized JSON data, dynamic environment configurations, and comprehensive Allure reporting.
> 
> 

---

## 📋 Table of Contents

| # | Section | # | Section |
| --- | --- | --- | --- |
| 01 | [🏗️ Framework Architecture](https://www.google.com/search?q=%23%EF%B8%8F-framework-architecture) | 05 | [🐳 Docker DB Integration](https://www.google.com/search?q=%23-docker-db-integration) |
| 02 | [✨ Key Features](https://www.google.com/search?q=%23-key-features) | 06 | [📡 API Layer & State Injection](https://www.google.com/search?q=%23-api-layer--state-injection) |
| 03 | [📁 Project Structure](https://www.google.com/search?q=%23-project-structure) | 07 | [📈 Execution & Reporting](https://www.google.com/search?q=%23-execution--reporting) |
| 04 | [🎯 Current Test Coverage](https://www.google.com/search?q=%23-current-test-coverage) | 08 | [📜 License](https://www.google.com/search?q=%23-license) |

---

## 🏗️ Framework Architecture

```text
╔═════════════════════════════════════════════════════════════════════════╗
║                   OPEN WEBUI AUTOMATION — FRAMEWORK OVERVIEW            ║
╠══════════════╦══════════════╦══════════════╦══════════════════════════╣
║   🧪 TESTS/  ║   🐳 DB/     ║   📡 APIs/   ║      ⚙️ UTILS/           ║
║  Test Specs  ║  DB Client   ║ API Helpers  ║ Logging, JSON, Retries   ║
║    (.py)     ║  (SQLite)    ║ (Auth/Tokens)║    (Core Logic)          ║
╠══════════════╩══════════════╩══════════════╩══════════════════════════╣
║                          📦 DATA/ (JSON)                              ║
║     Chat Functions · Folder Creation · Workspace · Notes Creation     ║
╠═════════════════════════════════════════════════════════════════════════╣
║                 🛠️ conftest.py & config/settings.py                   ║
║  ENV · BROWSER · HEADLESS · INCOGNITO · WORKERS · FIXTURES · DRIVERS  ║
╠══════════════╦═══════════════════════════╦══════════════════════════╣
║  📊 Allure   ║      🎬 Test Artifacts    ║    🌐 Environment         ║
║   Reports    ║    Logs, Videos, Screens  ║    Test | Dev | Prod      ║
╚══════════════╩═══════════════════════════╩══════════════════════════╝

```

---

## ✨ Key Features

| 🔷 Feature | 📝 Description |
| --- | --- |
| 🌍 **Dynamic Configurations** | Switch between `test`, `dev`, and `prod` targets via `pytest.ini`. |
| 🐳 **Dockerized DB Queries** | The `DBClient` executes SQL directly inside the `open-webui` container using `subprocess` and returns parsed JSON data. |
| 📡 **API-Assisted Setup** | UI tests start instantly. The `authenticated_page` fixture hits the login API and injects the token into `localStorage`. |
| 🗂️ **Data-Driven Execution** | Configurations and test parameters are fully externalized into the `data/` directory via JSON. |
| 🎬 **Rich Artifacts** | Automatically attaches screenshots, videos, and per-test logs to Allure on test failure. |
| 🔄 **Smart Retries** | Configured via `pytest-rerunfailures` in the master `pytest.ini` setup. |
| 🚙 **Driver Factory** | Centralized Playwright browser, context, and page generation in `drivers/`. |

---

## 📁 Project Structure

The project has been heavily modularized to separate configuration, test logic, data, and reporting.


OpenWebUI_Playwright_python_web_auto/
│
├── 🧪 tests/                      # Pytest specifications
│   ├── test_folder_created.py     # Folder creation and management tests
│   ├── test_notes_created.py      # Note taking and saving tests
│   ├── test_verify_chat.py        # LLM chat interactions and streaming
│   └── test_workspace_created.py  # Workspace environment tests
│
├── ⚙️ config/                     # Global configuration
│   └── settings.py                # Dataclass handling multi-env parameters
│
├── 📡 APIs/                       # Programmatic API helpers
│   └── login.py                   # REST-based auth token extraction
│
├── 🐳 db/                         # Database interaction layer
│   └── db_client.py               # Docker-exec wrapper for internal SQLite DB
│
├── 🚙 drivers/                    # Browser instantiation logic
│   └── driver_factory.py          # Playwright context/page setup and teardown
│
├── 📦 data/                       # Externalized test inputs (JSON)
│   ├── chat_func.json             
│   ├── folder_creation.json       
│   ├── notes_creation.json        
│   └── workspace.json             
│
├── 🛠️ utils/                      # Shared helper functions
│   ├── chat.py                    # Chat interaction utilities
│   ├── jsonhandler.py             # JSON parsing/writing
│   ├── logger.py                  # Per-session & per-test dedicated loggers
│   └── retry.py                   # Custom explicit wait/retry logic
│
├── 🎬 reports/                    # Automatically generated test reports
│   └── allure-results/            # Raw allure JSON/Attachment payloads
├── 📝 logs/                       # Auto-generated execution logs
├── 🎥 videos/                     # Auto-recorded test failure videos
│
├── 📄 conftest.py                 # Pytest fixtures, Allure hooks, Page setup
└── 🔧 pytest.ini                  # Master framework configuration (markers, plugins)

```

---

## 🎯 Current Test Coverage

The following table tracks the test automation progress for Open WebUI features.

| Feature | What to Test next | Automatable with Playwright? |
| --- | --- | --- |
| Chat | Send prompt and receive response | ✅ |
| Streaming | Response streams and completes | ✅ |
| Loading | Spinner appears and disappears | ✅ |
| Stop Generation | User can stop generation | ✅ |
| Regenerate | New response is generated | ✅ |
| New Chat | Creates a fresh conversation | ✅ |
| Chat History | Previous chats persist after refresh | ✅ |
| Rename/Delete Chat | CRUD operations work | ✅ |
| Prompt Input | Empty, long, emoji, Unicode, multiline | ✅ |
| Markdown | Lists, tables, code blocks render correctly | ✅ |
| Code Blocks | Syntax highlighting and Copy button | ✅ |
| Copy Response | Clipboard receives content | ✅ |
| File Upload | PDF, DOCX, CSV, image upload | ✅ |
| Invalid Files | Unsupported file types show an error | ✅ |
| **PDF Context Retrieval** | Upload a PDF and verify answers are grounded in its content | ✅ |
| **Hallucination / Groundedness** | Verify the AI does **not** invent info not present in the PDF; should respond with "not found" | ✅ *(with a controlled test document)* |
| Network Failure | Graceful error handling | ✅ |
| Session Expiry | Redirect to login or refresh token | ✅ |
| Error Recovery | Retry after failed request | ✅ |

---

## 🐳 Docker DB Integration

A standout feature of this framework is the ability to bypass the UI/API layers and query the backend database directly to verify absolute state. Because Open WebUI runs in a Docker container using a local SQLite instance, the `DBClient` executes queries through the Docker daemon.

```python
class DBClient:
    CONTAINER_NAME = "open-webui"
    DB_PATH = "/app/backend/data/webui.db"

    def execute(self, query, params=None):
        """
        Executes SQL directly inside the running Docker container.
        Returns parsed JSON results.
        """
        # Python script executed directly inside the container
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

To prevent slow, flaky UI login sequences before every test, the `conftest.py` utilizes the `authenticated_page` fixture. It relies on the `APIs/login.py` helper to grab a session token via HTTP and injects it straight into the browser's `localStorage`.

```python
@pytest.fixture()
def authenticated_page(page, settings: Settings):
    """
    Returns a fully logged-in page. Bypasses the UI login screen.
    """
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
# Run all tests with 0 parallel workers (Serial)
pytest

# Run tests in a specific environment (Test, Dev, Prod)
pytest --env=dev

# Run specific suite 
pytest tests/test_verify_chat.py

```

### Allure Reporting

On failure, the `page` fixture in `conftest.py` automatically intercepts the teardown phase to attach:

1. **Screenshot** of the exact failure state.
2. **Video** recording of the session.
3. **Log file** generated via the `TestLogger` class.

To view the generated report:

```bash
allure serve reports/allure-results

```

---
