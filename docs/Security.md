# Security Architecture: AI Runtime Manager

This document describes the security model, authorization mechanisms, and access control boundaries of the AI Runtime Manager.

## Security Model

AI Runtime Manager is designed strictly for local developer workstation execution.

```
┌────────────────────────────────────────────────────────┐
│               Local Workstation Boundary               │
│                                                        │
│   Developer Client  ──>  FastAPI (localhost:8088)       │
│                                │                       │
│                                ▼                       │
│                     LiteLLM (localhost:8000)           │
│                                │                       │
│                                ▼                       │
│                     Ollama (localhost:11434)           │
└────────────────────────────────────────────────────────┘
```

## Security Best Practices

### 1. Loopback Network Binding
- All services managed by the platform (FastAPI, LiteLLM, Ollama, OpenClaw, MCP) must bind strictly to the loopback interface (`127.0.0.1` or `localhost`). 
- Binding to `0.0.0.0` is prohibited to prevent exposing AI services to the local network unless explicitly modified in system firewalls by administrators.

### 2. Windows Service Privileges & ACLs
- The `AIRuntimeManager` Windows Service runs under the `LocalSystem` security context or a dedicated, unprivileged service account (e.g., `NT SERVICE\AIRuntimeManager`).
- Directory Access Control Lists (ACLs) are configured on the database and configurations folders:
  - Path: `C:\ProgramData\AIRuntimeManager`
  - Access: Full Control to `SYSTEM`, `Administrators`, and the service account. Read-only or No Access to standard workstation users.

### 3. API Gateway Authentication
- The LiteLLM gateway uses a programmatically generated master API key (stored securely in SQLite/YAML) to authorize incoming OpenAI-compatible connections.
- The React Dashboard utilizes session tokens or API keys dynamically generated on first-load of the background service and injected into the client interface config.

### 4. Sandbox Limits on MCP Servers
- Model Context Protocol (MCP) servers run as child processes.
- The orchestrator configures each MCP server configuration with strict argument checking to prevent remote code execution (RCE) via command-injection patterns.
