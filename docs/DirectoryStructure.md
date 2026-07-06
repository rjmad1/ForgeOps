# Repository Structure: AI Runtime Manager

This document maps out the folder and file layout of the AI Runtime Manager repository.

```
ai-runtime-manager/
├── docs/                      # Phase 0 Design and Specification Docs
├── src/
│   ├── backend/               # FastAPI Backend Service
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py        # FastAPI endpoints and service lifecycle
│   │   │   ├── database.py    # SQLite engine and schema migrations
│   │   │   ├── registry.py    # Service registration and status query
│   │   │   ├── process.py     # Windows subprocess runner and killer
│   │   │   ├── config.py      # Config auto-generator and synchronizer
│   │   │   ├── health.py      # TCP/HTTP health monitor threads
│   │   │   ├── models.py      # Dynamic model discovery & category router
│   │   │   ├── metrics.py     # Windows hardware utilization poller
│   │   │   └── plugins/       # Plugin engine & implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py    # Abstract BasePlugin class
│   │   │       ├── ollama.py  # Ollama manager plugin
│   │   │       ├── litellm.py # LiteLLM manager plugin
│   │   │       ├── mcp.py     # MCP Server connector plugin
│   │   │       └── openclaw.py# OpenClaw supervisor plugin
│   │   └── setup_service.py   # pywin32 Windows Service wrapper
│   │
│   ├── cli/                   # CLI entry points
│   │   ├── __init__.py
│   │   └── main.py            # CLI commands implementation
│   │
│   └── frontend/              # Single Page Dashboard (Vite + React + TypeScript)
│       ├── public/
│       ├── src/
│       │   ├── assets/
│       │   ├── components/    # Reusable dashboard widgets
│       │   ├── hooks/         # Custom queries and API wrappers
│       │   ├── App.tsx        # Dashboard shell and routes
│       │   ├── index.css      # Core Vanilla CSS styling variables
│       │   └── main.tsx
│       ├── package.json
│       └── vite.config.ts
│
├── tests/                     # Test Suites
│   ├── unit/                  # Unit tests (Mock processes, databases)
│   ├── integration/           # Subprocess controls & API integration tests
│   ├── smoke/                 # Fast environment validation scripts
│   └── performance/           # TTFT, throughput, and hardware load tests
│
├── scripts/                   # PowerShell operational utilities
│   ├── register-service.ps1   # NSSM/win32 service installer
│   ├── backup-config.ps1      # Backup SQLite and config files
│   ├── restore-config.ps1     # Restore database and config backups
│   └── check-health.ps1       # Low-level PowerShell diagnostics script
│
├── pyproject.toml             # Python build and packaging config
├── requirements.txt           # Main python dependency list
└── README.md                  # Project overview and quick start
```
