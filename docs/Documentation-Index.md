# ForgeOps Technical Documentation Index

Welcome to the official technical documentation library for **ForgeOps** (the **AI Runtime Manager**). This platform orchestrates local LLM, proxy, agent, and MCP runtimes on Windows 11 Professional workstations.

---

## Technical Documentation Library

Use the links below to navigate the guides. Each document is tailored to a specific audience and operational role:

### 1. [Quick Start Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/01-Quick-Start.md)
* **Audience**: First-time users, developers, and evaluators.
* **Target Reading Time**: 10 minutes.
* **Contents**: Core overview, automated bootstrap, first health check, starting Ollama & LiteLLM, running your first query, and using the React Web Dashboard.

### 2. [Installation Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/02-Installation-Guide.md)
* **Audience**: Administrators, operations, and end-users.
* **Contents**: Full prerequisite matrices, installation methods (`install`, `repair`, `upgrade`, `rollback`, `reinstall`, `uninstall`), Windows Service parameters, post-install checks, and verification checklists.

### 3. [User Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/03-User-Guide.md)
* **Audience**: Daily operators and software developers.
* **Contents**: Command Line Interface (`arm`) commands, React Web Dashboard view configurations, model catalog additions, diagnostics checklists, support bundle creation, and backup routines.

### 4. [Administrator Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/04-Administrator-Guide.md)
* **Audience**: Systems administrators and platform engineers.
* **Contents**: System topology layouts, dynamic registry variables, Windows Service controls (`sc.exe`), security policies, network loopback binds, DACL file permissions, and performance tuning configurations.

### 5. [Troubleshooting Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/05-Troubleshooting-Guide.md)
* **Audience**: Support engineers and operations staff.
* **Contents**: Symptom-to-resolution flowcharts covering port blockage exceptions, zombie child processes, HTTP unauthorized errors, database initialization issues, and full recovery procedures.

### 6. [Operations Manual](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/06-Operations-Manual.md)
* **Audience**: Site Reliability Engineers (SREs) and IT operations.
* **Contents**: Daily uptime verification checks, weekly logs archiving, monthly SQLite database vacuuming, performance latency benchmarking, upgrade validation, and support bundle handling.

### 7. [REST API Reference](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/07-REST-API-Reference.md)
* **Audience**: Backend developers and systems integrators.
* **Contents**: Detailed schemas for every endpoint exposed on port `8088`, HTTP verb usage, security cookie parameters, JSON request payloads, response bodies, and error response examples.

### 8. [CLI Reference](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/08-CLI-Reference.md)
* **Audience**: Terminal users and script developers.
* **Contents**: Complete CLI command reference listing all arguments, subcommands (`services`, `status`, `start`, `stop`, `restart`, `discover`, `inventory`, `history`, `diagnostics`, `support-bundle`, `backup`, `restore`, `benchmark`), syntax structures, and stdout examples.

### 9. [Plugin Developer Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/09-Plugin-Developer-Guide.md)
* **Audience**: Software engineers developing custom extensions.
* **Contents**: Abstract base class (`RuntimePlugin`) documentation, registration sequences, capabilities discovery structures, process management interfaces, and plugin build best practices.

### 10. [Architecture Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/10-Architecture-Guide.md)
* **Audience**: Enterprise architects and core contributors.
* **Contents**: Complete system topology map, kernel registry buses, workflow execution steps (transactional pre-flight/launch/wait with rollback), backoff delay formulas, and database schemas.

### 11. [Security Guide](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/11-Security-Guide.md)
* **Audience**: Security engineers and compliance officers.
* **Contents**: Loopback network binding policies, token session authentication, Windows NTFS DACL controls, CORS constraints, and vulnerability threat assessments.

### 12. [Frequently Asked Questions (FAQ)](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/12-FAQ.md)
* **Audience**: All users.
* **Contents**: Quick troubleshooting, model pull mapping, session locks, and folder structure references.

### 13. [Release Notes v1.0.0](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/13-Release-Notes-v1.0.0.md)
* **Audience**: All stakeholders.
* **Contents**: Stable v1.0.0 feature highlights, platform requirements, known limitations, and upgrade pathways.

### 14. [Documentation Validation Report](file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/Documentation-Validation-Report.md)
* **Audience**: Release managers and QA teams.
* **Contents**: Matrix mapping all documented CLI commands, REST endpoints, UI views, and databases directly to code blocks verified by system validators.
