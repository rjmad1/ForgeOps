# ForgeOps Glossary

This glossary defines terms and systems utilized across the ForgeOps AI Runtime Manager.

* **ForgeOps / AI Runtime Manager**: The local orchestration control plane daemon running as a Windows Service (`AIRuntimeManager`).
* **Ollama**: An open-source local LLM execution engine running as a background daemon.
* **LiteLLM**: An OpenAI-compatible proxy gateway that maps custom endpoints to local model runtimes.
* **OpenClaw**: A supervisor agent coordinator that executes and monitors local AI tool runs.
* **Model Context Protocol (MCP)**: An open standard protocol connecting AI models to desktop data, tools, and servers.
* **FastAPI**: The asynchronous Python web framework hosting the ForgeOps REST gateway.
* **Service Registry**: The SQLite database table tracking onboarded plugins and status configurations.
* **Capabilities Discovery**: The scanning process by which plugins query runtimes to synchronize active models into the SQLite database.
* **Circuit Breaker**: A software pattern that halts auto-restart loops when consecutive failures exceed a threshold.
* **Support Bundle**: A diagnostic zip file gathering logs, database state, and hardware specs for troubleshooting.
