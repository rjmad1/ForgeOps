# ForgeOps Security Guide

This document describes the security controls, authentication mechanisms, directory permissions, and threat boundaries of the ForgeOps (AI Runtime Manager) orchestration platform.

---

## 1. Threat Model & Boundaries

ForgeOps is designed strictly for local developer workstation execution.

```
+---------------------------------------------------------------+
|                  Workstation Security Boundary                |
|                                                               |
|   Local Client/IDE  ======>  FastAPI Daemon (127.0.0.1:8088)  |
|                                     ||                        |
|                                     ▼▼                        |
|                           LiteLLM Proxy (127.0.0.1:8000)      |
|                                     ||                        |
|                                     ▼▼                        |
|                           Ollama Daemon (127.0.0.1:11434)     |
+---------------------------------------------------------------+
```

### Threat Classification Table
| Threat | Risk Level | Mitigation Strategy |
|---|---|---|
| **Remote Code Execution (RCE)** | High | Loopback-only interface binding. All runtimes bind strictly to `127.0.0.1`. Remote requests are blocked by host OS firewalls. |
| **Unauthorized Local Access** | Medium | Secure session API key validation. The orchestrator key file has Windows DACLs restricting read access to current user and admin processes. |
| **Cross-Site Scripting (XSS) / CSRF** | Low | CORS headers restricted to loopback origin ports (`http://localhost:5173`, `http://127.0.0.1:5173`, etc.). Cookie flags set to `SameSite=Strict`. |
| **Information Disclosure** | Low | Support bundles and database files require local administrative credentials to retrieve or view. |

---

## 2. Authentication & Authorization

All endpoints exposed under `/api/` are protected by a token-verification middleware.

### A. Token Generation & Storage
1. On backend startup, the context lifespan generates a secure, randomized 32-byte hexadecimal key:
   ```python
   session_api_key = secrets.token_hex(32)
   ```
2. The key is written to the file: `%PROGRAMDATA%\AIRuntimeManager\.session_api_key`.
3. Standard API requests must provide this key in the `X-API-Key` HTTP header.

### B. Same-Origin Cookies
For dashboard browsers, the root path (`/`) sets a secure same-origin cookie:
* **Cookie Key**: `session_api_key`
* **SameSite Attribute**: `Strict` (cookie is only sent in first-party contexts)
* **HttpOnly Attribute**: `False` (allowing local Vite scripts to extract and pass keys securely)

---

## 3. Directory & File Access Control Lists (ACLs)

On Windows 11 systems, the database and credentials folders are secured using NTFS native Access Control Lists (ACLs).

### NTFS Permission Policy:
* **Secured Target**: `C:\ProgramData\AIRuntimeManager\.session_api_key`
* **Inheritance**: Explicitly disabled (protecting the file from inheriting weaker permissions from parent folders).
* **Allowed Access Rights**:
  * `SYSTEM` (S-1-5-18): Full Control.
  * `Administrators` (S-1-5-32-544): Full Control.
  * `Process Token Owner SID` (current user running the service): Full Control.
* **All other users**: Access Denied.

---

## 4. Support Bundle Security

The diagnostics support bundle is compiled as a zip file containing log files and database state records. 

> [!CAUTION]
> Support bundles contain local system environment variables, local username strings, paths, database configuration values, and raw stdout log lines from model runs.
> * **Protection**: Support bundles are saved only to paths designated by administrators.
> * **Access**: Restrict access to generated zip bundles. Purge support bundles once incident diagnostics are completed.

---

## 5. Security Recommendations
1. **Never Bind to `0.0.0.0`**: Do not configure `arm-config.yaml` or downstream yaml configurations to bind to the wildcard address (`0.0.0.0`), as this exposes your local LLMs to your local network.
2. **Restrict Service Privileges**: Run the `AIRuntimeManager` Windows Service under an unprivileged user service account (e.g. `NT SERVICE\AIRuntimeManager`) rather than `LocalSystem` where possible. Ensure this account has exclusive write permissions to `C:\ProgramData\AIRuntimeManager\`.
3. **Use HTTPS for External Proxies**: If you configure a proxy (like NGINX) to expose LiteLLM externally, enforce HTTPS and authenticate incoming client connections using separate API keys.
