# ForgeOps Quick Start Guide

Welcome to **ForgeOps** (formally the **AI Runtime Manager**). ForgeOps is a local orchestration control plane designed for managing heterogeneous AI runtimes (Ollama, LiteLLM, OpenClaw, and Model Context Protocol/MCP) on Windows 11 Professional.

This guide will walk you through installing ForgeOps, starting the background service, and running your first model in under 10 minutes.

---

## 1. Prerequisites Checklist
Before installing, ensure your machine meets these basic requirements:
* **Operating System**: Windows 11 Professional (64-bit)
* **Python**: Version 3.10 or higher
* **Git**: Installed and available in your PowerShell PATH
* **CUDA & GPU**: NVIDIA GPU with current drivers and CUDA Toolkit 11.8+ (strongly recommended for local inference acceleration, though CPU fallback is supported)

---

## 2. Installation
To install ForgeOps, open **PowerShell as Administrator** and execute the bootstrap script in the root directory:

```powershell
# In the root folder of the project
.\install.bat
```

### What the installer does:
1. Detects system prerequisites (Python, Git, CUDA, nvidia-smi).
2. Initializes the local SQLite database (`arm.db`) and seeds initial service configurations.
3. Automatically secures your session API key using native Windows DACLs at `%PROGRAMDATA%\AIRuntimeManager\.session_api_key`.
4. Registers and starts the background Windows Service: **`AIRuntimeManager`**.
5. Generates an installation report at `C:\ProgramData\AIRuntimeManager\installation_report.md`.

---

## 3. First Launch and Health Check
Once installation completes, verify the control plane daemon is running and healthy.

### Verification via CLI
Run the `arm` command-line interface tool to check daemon health:
```powershell
arm status
```
**Expected Output:**
```text
=== Managed Services ===
Service ID      | Service Name                   | Port   | Status       | PID
---------------------------------------------------------------------------
ollama          | Ollama Daemon                  | 11434  | STOPPED      | -
litellm         | LiteLLM Gateway                | 8000   | STOPPED      | -
openclaw        | OpenClaw Supervisor            | 8080   | STOPPED      | -
mcp             | Model Context Protocol Hub     | -      | RUNNING      | 5244

=== System Resource Consumption ===
  CPU Utilization : 12.4%
  RAM Utilization : 45.2% (7405 MB / 16384 MB)
  GPU Utilization : 0.0% (NVIDIA GeForce RTX 4070)
  VRAM Utilization: 1200 MB / 12288 MB
```

### Verification via Browser
Navigate to the local health endpoint in your browser:
* URL: `http://127.0.0.1:8088/health`
* Response: `{"status": "healthy"}`

---

## 4. Starting Your Runtimes and Models
Let's start the AI engines and discover available local models.

### Step 1: Start the Ollama Service
Execute the start command:
```powershell
arm start ollama
```
**Expected Output:**
```text
Dispatching start command for 'ollama'...
Success. Service status: RUNNING, PID: 7420
```

### Step 2: Trigger Model Discovery
Trigger a capabilities scan to detect active model models:
```powershell
arm discover
```
**Expected Output:**
```text
Dispatching discovery scan command...
Success. Status: completed. Local models discovered: 3
```

### Step 3: Start LiteLLM Gateway
The LiteLLM gateway aggregates all your local models into an OpenAI-compatible endpoint. Start it with:
```powershell
arm start litellm
```
**Expected Output:**
```text
Dispatching start command for 'litellm'...
Success. Service status: RUNNING, PID: 8116
```

---

## 5. Web Dashboard Overview
ForgeOps includes a premium local React Dashboard. Access it by opening:
`http://127.0.0.1:8088/`

```
┌──────────────────────────────────────────────────────────────┐
│  [A] AI Control Plane                               [Sun/Moon]│
├──────────────────────────────────────────────────────────────┤
│  • Home              │                                       │
│  • Services          │   System Load                         │
│  • Models            │   CPU [■■■       ] 12%                │
│  • Health/Inventory  │   RAM [■■■■■     ] 45%                │
│  • Observability     │   GPU [          ] 0%                 │
│  • Workflows         │                                       │
│  • Event Stream      │   Active Services                     │
│  • Logs              │   - Ollama Daemon  [RUNNING]          │
│  • Settings          │   - LiteLLM Gateway [RUNNING]         │
│  • Maintenance       │                                       │
└──────────────────────────────────────────────────────────────┘
```

### Key Tabs:
* **Home**: Operational charts, system metrics, and quick-restart controls.
* **Services**: Turn Ollama, LiteLLM, OpenClaw, and MCP runtimes on/off.
* **Models**: List and categorize all discovered local model capabilities.
* **Observability**: Live metrics charting CPU, RAM, GPU, and VRAM utilization.
* **Logs**: Terminal output showing stdout/stderr of each background service process.

> [!TIP]
> Use the **Ctrl+K** command palette shortcut anywhere in the Web Dashboard to quickly execute navigation paths and system settings.

---

## 6. Next Steps
Now that you have configured and verified your installation:
* To configure custom model routing and mappings, proceed to the [User Guide](User-Guide).
* To manage service settings, API security, and backups, see the [Administrator Guide](Administrator-Guide).
* For detailed troubleshooting steps on port blockages or process terminations, reference the [Troubleshooting Guide](Troubleshooting).
