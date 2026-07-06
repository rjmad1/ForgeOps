# ForgeOps Project Closure: Lessons Learned

This document summarizes the technical insights and operational lessons learned during the development of **ForgeOps Version 1.0 (AI Runtime Manager)**.

---

## 1. Environment Automation & Setup
* **Lesson**: Automated prerequisites detection via `install.py` is critical for developers. Using `winget` to automatically install missing dependencies (like Git and Ollama) reduced workstation setup times from hours to minutes.
* **Takeaway**: Maintain and update `install.py` package identifiers to ensure setup scripts remain idempotent and reliable over time.

---

## 2. Windows Service Wrapper Integration
* **Lesson**: Integrating pywin32 bindings in `setup_service.py` to wrap the FastAPI backend inside a Windows Service solved persistent execution issues.
* **Takeaway**: Hardcoding Windows commands (like `sc.exe`) made deployment robust on Windows but limited the application's cross-platform potential. Future releases should abstract system service calls behind OS-agnostic interfaces.

---

## 3. Database Selection & Concurrency
* **Lesson**: SQLite is lightweight and easy to deploy on local workstations. However, concurrent database writes from the GUI, CLI, and background metrics poller occasionally triggered `database is locked` errors.
* **Takeaway**: While SQLite is suitable for single-user workstation workloads, the database should be configured to run in **Write-Ahead Logging (WAL)** mode by default in subsequent releases to handle concurrent operations smoothly.

---

## 4. Virtual Environment Execution Realities
* **Lesson**: Running validation or installation scripts using the system's global Python interpreter led to dependency errors (e.g. missing `fastapi` or `psutil`).
* **Takeaway**: All tools, tests, and operational commands must be executed within the project's virtual environment:
  ```powershell
  .\.venv\Scripts\python.exe scripts\validate_system.py --dev
  ```
  Updating documentation to highlight this requirement is essential for user onboarding.

---

## 5. Security & Secret Leakage Risks
* **Lesson**: Packaging console logs from all subprocesses into a diagnostics zip makes troubleshooting easier, but runs the risk of exporting plaintext tokens.
* **Takeaway**: Incorporate log sanitization into the support bundle compilation step in future releases to strip API keys, database tokens, and personal identifying info.
