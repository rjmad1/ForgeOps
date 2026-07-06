# ForgeOps Installation Guide

This guide details how to install, configure, validate, and manage the ForgeOps (AI Runtime Manager) orchestration platform on Windows systems.

---

## 1. Prerequisites Checklist
ForgeOps requires specific hardware and software components to function. Run a diagnostic scan to see what is already installed:
```powershell
python scripts/install.py --dry-run
```

### System Requirements
| Component | Minimum Requirement | Notes |
|---|---|---|
| **OS** | Windows 11 Professional / Windows 10 | 64-bit architecture is required. |
| **Python** | Version 3.10+ | Must be added to the system PATH. |
| **Node.js & npm** | Node 18+ & npm 9+ | Required for Model Context Protocol (MCP) servers. |
| **Git** | Git for Windows | Required for repository cloning and dependency fetching. |
| **Docker** | Docker Desktop | Optional (required only if running containers). |
| **WSL 2** | Windows Subsystem for Linux 2 | Optional (supported distro check). |
| **GPU** | NVIDIA GPU (e.g. RTX 30/40 series) | Required for local GPU acceleration. |
| **NVIDIA Driver** | Driver version 520+ | Required for CUDA interface. |
| **CUDA Toolkit** | Version 11.8+ | Verified via `nvcc --version` and `CUDA_PATH`. |

---

## 2. Installation Methods

> [!IMPORTANT]
> The installation commands below must be run in a **PowerShell** or **Command Prompt** window launched with **Administrator privileges** (Run as Administrator), unless running in developer mode.

### A. Fresh Installation
Performs a clean, idempotent install of the entire platform:
```powershell
python scripts/install.py --action install
```
**What happens under the hood:**
1. Scans system for prerequisites. If Git or Ollama is missing, the installer attempts to fetch and install them via Windows Package Manager (`winget`).
2. Initializes the SQLite database file at `C:\ProgramData\AIRuntimeManager\db\arm.db`.
3. Seeds default service profiles (Ollama, LiteLLM, OpenClaw, MCP).
4. Generates a secure session API key and applies native Windows Access Control Lists (ACLs) to restrict access to `SYSTEM`, `Administrators`, and the current user process token.
5. Registers the FastAPI backend daemon as a Windows Service named `AIRuntimeManager` and starts it.
6. Performs a loopback port validation.
7. Writes a detailed markdown installation report to `C:\ProgramData\AIRuntimeManager\installation_report.md`.

*To run in Developer/User mode (bypassing Administrator validation and service registration):*
```powershell
python scripts/install.py --action install --dev
```

### B. Repair Installation
If database tables are corrupted or the Windows Service registration is deleted, run a repair to re-initialize tables and services:
```powershell
python scripts/install.py --action repair
```

### C. System Upgrade
Upgrades the platform, applying schema migrations to the database and preserving existing configurations:
```powershell
python scripts/install.py --action upgrade
```
**Mechanism:**
1. Automatically calls `backup_config()` to store a database snapshot in `%PROGRAMDATA%\AIRuntimeManager\backups\`.
2. Inspects database schema and runs structural updates.
3. Stops the Windows Service, updates the system binaries, and restarts the service.

### D. System Rollback
Rolls back database tables and service binaries to the last saved backup state:
```powershell
python scripts/install.py --action rollback
```
**Mechanism:**
1. Stops the `AIRuntimeManager` service.
2. Locates the latest backup directory inside `C:\ProgramData\AIRuntimeManager\backups\`.
3. Restores `arm.db` and `litellm_config.yaml`.
4. Restarts the service.

### E. Restore from Specific File
To restore from a specific configuration zip archive:
```powershell
python scripts/install.py --action restore --file "C:\path\to\backup.zip"
```

### F. Reinstallation
Executes a complete uninstall of current services and files, followed by a fresh installation:
```powershell
python scripts/install.py --action reinstall
```

### G. Uninstallation
To cleanly wipe ForgeOps from the workstation:
```powershell
python scripts/install.py --action uninstall
```
**Uninstall steps:**
1. Stops the running `AIRuntimeManager` Windows Service.
2. Deletes the Windows Service registration.
3. Deletes the SQLite database file (`arm.db`).
4. *Note: Downstream runtimes (Ollama, Node, Git) installed via winget are preserved and must be uninstalled manually if no longer needed.*

---

## 3. Post-Installation Verification Checklist

Verify your installation by completing the following checklist:

- [ ] **Daemon Process**: Open a terminal and verify the service is registered:
  ```powershell
  sc.exe query AIRuntimeManager
  ```
  The state should be `RUNNING`.
- [ ] **Database Integrity**: Verify the database tables have been seeded:
  ```powershell
  python scripts/validate_system.py
  ```
  Look for the `[DATABASE] Database Schema Verification: PASS` status.
- [ ] **Security Key Hardening**: Verify the session key is secured:
  ```powershell
  icacls.exe C:\ProgramData\AIRuntimeManager\.session_api_key
  ```
  Confirm only `SYSTEM`, `Administrators`, and your current user account have access. Inheritance should be disabled.
- [ ] **API Endpoint Accessibility**: Run an HTTP check to the daemon:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8088/health"
  ```
  Should return `{"status": "healthy"}`.
- [ ] **Dashboard Access**: Open `http://127.0.0.1:8088/` in your browser. Ensure the connection dot is green and says **Daemon: Connected**.

---

## 4. Troubleshooting Common Problems

### Symptom: "This installer must be run as Administrator"
* **Cause**: Script executed in standard user shell.
* **Solution**: Right-click PowerShell and choose **Run as Administrator**, then re-run command.

### Symptom: API gateway fails to start / Port 8088 in use
* **Cause**: Another local service is using port 8088.
* **Solution**: Check process occupancy and free the port:
  ```powershell
  Get-NetTCPConnection -LocalPort 8088 | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```

### Symptom: "Failed to apply Windows-native ACL to session API key"
* **Cause**: pywin32 extension package is missing or corrupted.
* **Solution**: Install pywin32 manually or run the installer with `--dev` flag to use local filesystem fallback permissions.
  ```powershell
  pip install pywin32
  ```
