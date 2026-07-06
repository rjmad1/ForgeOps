# ForgeOps (AI Runtime Manager)

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#supported-environments)

**ForgeOps (AI Runtime Manager)** is an enterprise-grade, local AI orchestration and control plane platform designed to manage and monitor heterogeneous AI runtimes on Windows workstations and servers. 

ForgeOps automates the process lifecycle, configuration synthesis, health evaluation, and resource monitoring for local AI tools: **Ollama**, **LiteLLM**, **OpenClaw**, and **Model Context Protocol (MCP)** servers.

---

## Key Features

- ⚙️ **Idempotent Windows Installer & Service Host**: Easily register the orchestration engine as a native Windows Service (`AIRuntimeManager`) starting automatically on boot.
- 🔌 **Dynamic Configuration Synthesis**: Automatically generates routing maps and config files (e.g. `litellm-config.yaml`) based on active SQLite models and aliases.
- 📊 **Unified React Dashboard**: A polished single-page interface showing process status, model catalogs, active CPU/RAM/VRAM consumption, and live system metrics.
- 🎛️ **Powerful CLI Tool**: Fully-featured `arm` Command Line Interface for direct service management, history queries, and diagnostics.
- 🛡️ **Hardened Local Security**: Employs Windows native Access Control Lists (ACLs) to protect the session API key, restricting access to administrators and the system account.
- 🏥 **Self-Healing & Auto-Restart Policies**: Configurable exponential backoff and circuit-breaker logic to detect and recover crashed runtimes.
- 📦 **Operational Tooling**: Built-in support for configuration backups, system restores, performance benchmarks, and diagnostic support bundles.

---

## System Architecture

ForgeOps uses a decoupled architecture to manage local processes and expose them via a secure loopback API:

```
                  ┌───────────────────────────────────────────────┐
                  │              Vite + React UI                  │
                  │             (Static Dashboard)                │
                  └──────────────────────┬────────────────────────┘
                                         │ REST API / WebSockets
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │            FastAPI Web Gateway                │
                  │               (Port 8088)                     │
                  └──────────────────────┬────────────────────────┘
                                         │ Command Bus / Events
                                         ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                            ForgeOps Kernel                               │
    │                                                                          │
    │  ┌───────────────────────┐ ┌──────────────────────┐ ┌─────────────────┐  │
    │  │   Service Registry    │ │    Health Engine     │ │  Policy Engine  │  │
    │  └───────────┬───────────┘ └───────────┬──────────┘ └────────┬────────┘  │
    │              │                         │                     │           │
    │  ┌───────────▼───────────┐ ┌───────────▼──────────┐ ┌────────▼────────┐  │
    │  │  Sqlite DB (arm.db)   │ │  Scheduler & Metrics │ │ Process Manager │  │
    │  └───────────────────────┘ └──────────────────────┘ └────────┬────────┘  │
    └──────────────────────────────────────────────────────────────┼───────────┘
                                                                   │ Subprocesses
                                                                   ▼
                                        ┌─────────────────────────────────────┐
                                        │ 🔌 Local AI Runtimes                │
                                        │    - Ollama (11434)                 │
                                        │    - LiteLLM (8000)                 │
                                        │    - OpenClaw (8080)                │
                                        │    - MCP Servers (stdio)            │
                                        └─────────────────────────────────────┘
```

---

## Supported Environments

- **Operating System**: Windows 10 / Windows 11 / Windows Server 2019+ (Fully certified with Windows APIs)
- **Runtime Environment**: Python 3.10+
- **Database**: SQLite 3 (WAL mode enabled)

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/forgeops.git
cd forgeops
```

### 2. Run the Installer
Run the PowerShell or Command Prompt as **Administrator** and execute:
```cmd
install.bat
```
*For local testing without admin privileges, pass the developer flag:*
```bash
python scripts/install.py --dev
```

### 3. Verify the Installation
Run the system validation suite to certify that all modules are configured correctly:
```bash
.venv\Scripts\python scripts/validate_system.py
```

---

## CLI Quick Reference

The platform installs a command-line interface alias `arm`. You can run CLI commands using the virtual environment python launcher:

```bash
# List all registered services and their current status
python -m src.cli.main services

# Show discovered system capabilities (models/tool providers)
python -m src.cli.main inventory

# Start/Stop/Restart a specific runtime
python -m src.cli.main start litellm
python -m src.cli.main stop litellm
python -m src.cli.main restart mcp

# View recent operational events and history log
python -m src.cli.main history

# Generate a diagnostic report and system health summary
python -m src.cli.main diagnostics

# Create a zip support bundle containing logs, configs, and DB schemas
python -m src.cli.main export-support-bundle
```

---

## REST API Gateway

The FastAPI daemon runs by default on `http://127.0.0.1:8088`. All API requests require the session token passed in the `X-API-Key` header (written to `%PROGRAMDATA%\AIRuntimeManager\.session_api_key`).

### Key Endpoints
- `GET /health` - Liveness check (Bypasses Auth)
- `GET /api/v1/services` - List services and status
- `POST /api/v1/services/{service_id}/start` - Launch a service process
- `POST /api/v1/services/{service_id}/stop` - Terminate a service process
- `GET /api/v1/models` - List capabilities / active LLM models
- `GET /api/v1/system/metrics` - Fetch real-time CPU, RAM, and GPU stats
- `GET /api/v1/diagnostics/report` - Get health diagnostics summary

*To explore and run requests interactively, visit the Swagger UI at `http://127.0.0.1:8088/docs`.*

---

## React Web Dashboard

Once the service is started, the static UI is accessible directly via the loopback port:
👉 **[http://127.0.0.1:8088/index.html](http://127.0.0.1:8088/index.html)**

The dashboard updates in real-time, providing controls to start/stop subsystems and monitor VRAM allocation, GPU utilization, and latency metrics.

---

## Developer Guide

If you want to contribute or build custom plugins, please review our [Developer Guide](docs/DeveloperGuide.md) and [Contributing Guidelines](CONTRIBUTING.md).

### Run Unit Tests
```bash
pip install -r requirements.txt
pytest
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
