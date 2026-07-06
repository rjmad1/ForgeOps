# Developer Guide: AI Runtime Manager

This guide walks you through setting up your development environment, writing plugins, running tests, and validating your code.

## Development Setup

### 1. Initialize Python Environment
Use Python 3.10+ on Windows 11:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Backend in Development Mode
To run the FastAPI server with hot-reloading:
```powershell
uvicorn src.backend.app.main:app --host 127.0.0.1 --port 8088 --reload
```

### 3. Run Frontend in Development Mode
Set up Vite development environment:
```powershell
cd src/frontend
npm install
npm run dev
```

---

## Writing a Runtime Plugin

To add a new AI runtime engine, create a file in `src/backend/app/plugins/your_plugin.py` implementing `BasePlugin`:

```python
from src.backend.app.plugins.base import BasePlugin

class MyCustomPlugin(BasePlugin):
    def name(self) -> str:
        return "my_custom_engine"

    def on_register(self):
        # Insert database schema records, initialize directories
        pass

    def build_config(self) -> dict:
        # Return synthesized configuration dict
        return {
            "port": 9999,
            "host": "127.0.0.1"
        }
```
Register the plugin class in `src/backend/app/plugins/__init__.py`.

---

## Testing

We use `pytest` for all test suites.

### Run Unit Tests
```powershell
pytest tests/unit
```

### Run Integration Tests
Integration tests spin up mock subprocesses or verify communication with the SQLite test DB:
```powershell
pytest tests/integration
```

### Check Code Coverage
Ensure coverage remains high:
```powershell
pytest --cov=src tests/
```
