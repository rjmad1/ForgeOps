# ForgeOps Release Notes - Version 1.0.0

ForgeOps (AI Runtime Manager) Version 1.0.0 is the first official release of the local station AI orchestrator designed to run on Windows 11 Professional.

---

## 1. Feature Highlights

### Dynamic Process Management
* Runs as a background Windows Service (`AIRuntimeManager`) that wraps a FastAPI gateway.
* Spawns downstream runtimes (Ollama daemon, LiteLLM proxy gateway, OpenClaw agent, and Model Context Protocol servers) as child processes.
* Captures real-time process PIDs and cleans up child runtimes on service termination to prevent zombie subprocesses.

### Automated Capabilities Discovery
* The Ollama and LiteLLM plugins query local APIs and sync installed models into the SQLite database.
* LiteLLM proxies (`litellm_config.yaml`) are automatically regenerated, matching your local Ollama models.

### Security Hardening
* All services bind strictly to loopback interfaces (`127.0.0.1`), blocking external connections.
* The session API key is secured with Windows-native DACLs, restricting read/write capabilities to `SYSTEM`, `Administrators`, and the current user process owner.

### Reactive Auto-Restart & Circuit Breakers
* Monitors subprocess health and automatically triggers restarts with exponential backoff delay and randomized jitter.
* The circuit breaker trips `OPEN` if retries exceed limits (default = `2` or `3` attempts), halting restart loops and protecting hardware resources.

### Local Observability Dashboard
* Visualizes real-time CPU, RAM, GPU, and VRAM utilization.
* Integrates a global **Ctrl+K Command Palette** for keyboard-driven navigation.
* Tails subprocess logs directly in the browser and handles state transition alerts via toasts.

---

## 2. Supported Platforms & Requirements
* **OS**: Windows 11 Professional / Windows 10 (64-bit).
* **Python**: Version 3.10 or higher.
* **Node.js**: Version 18 or higher (required for MCP hub).
* **GPU**: NVIDIA graphics cards with active display drivers.
* **CUDA**: CUDA Toolkit 11.8 or higher.

---

## 3. Known Limitations
1. **Remote Execution Restrictions**: The control plane binds to `127.0.0.1` and cannot be accessed over local networks without configuring reverse proxies.
2. **NVIDIA Driver Requirement**: GPU and VRAM utilization charting relies on the availability of `nvidia-smi.exe`. Non-NVIDIA graphics cards will fallback to CPU metrics only.
3. **Database Concurrency**: The SQLite storage engine does not support concurrent write operations.

---

## 4. Upgrade Guidelines

As this is the initial **v1.0.0** release, no migration path is required. 
* To start a clean installation:
  ```powershell
  python scripts/install.py --action install
  ```
* To repair or verify configurations:
  ```powershell
  python scripts/install.py --action repair
  python scripts/validate_system.py
  ```
