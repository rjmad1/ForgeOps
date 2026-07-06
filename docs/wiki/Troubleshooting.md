# ForgeOps Troubleshooting Guide

This guide is organized by symptoms to help support engineers, administrators, and developers diagnose and resolve issues with the ForgeOps (AI Runtime Manager) ecosystem.

---

## 1. System-Level Issues

### Symptom: ForgeOps Daemon Will Not Start / Status Offline
* **Likely Causes**:
  * Port `8088` (control plane api) is blocked or occupied by another application.
  * Python virtual environment is not activated or dependencies are missing.
* **Diagnostic Steps**:
  1. Check if the port is in use:
     ```powershell
     Get-NetTCPConnection -LocalPort 8088 -ErrorAction SilentlyContinue
     ```
  2. View the log file at `%PROGRAMDATA%\AIRuntimeManager\logs\service.log` for execution errors.
* **Resolution**:
  1. Kill the blocking process:
     ```powershell
     Stop-Process -Id (Get-NetTCPConnection -LocalPort 8088).OwningProcess -Force
     ```
  2. Start the service manually:
     ```powershell
     Start-Service -Name AIRuntimeManager
     ```
* **Verification**:
  * Execute `arm status` and confirm services are listed.

---

### Symptom: Windows Service Failures (`sc.exe` errors)
* **Likely Causes**:
  * Service script was registered using a relative python path.
  * Permissions on the project directory are restricted.
* **Diagnostic Steps**:
  1. Inspect the service configuration:
     ```powershell
     sc.exe qc AIRuntimeManager
     ```
  2. Verify the `BINARY_PATH_NAME` correctly routes to your active python executable and `src\backend\setup_service.py`.
* **Resolution**:
  1. Re-install the service wrapper:
     ```powershell
     python src/backend/setup_service.py remove
     python src/backend/setup_service.py install
     ```
  2. Verify start configuration:
     ```powershell
     sc.exe config AIRuntimeManager start=auto
     ```
* **Verification**:
  * Start the service and verify it stays in the `RUNNING` state.

---

## 2. API & Security Issues

### Symptom: HTTP 401 Unauthorized / Credentials Missing
* **Likely Causes**:
  * The API Client or CLI is not passing the correct `X-API-Key` header.
  * The session API key file was not written, or has incorrect permissions.
* **Diagnostic Steps**:
  1. Print the location and check for file existence:
     ```powershell
     Test-Path "$env:PROGRAMDATA\AIRuntimeManager\.session_api_key"
     ```
  2. Check the logs for `Failed applying Windows-native ACL`.
* **Resolution**:
  1. Clean the database and re-install to regenerate keys:
     ```powershell
     python scripts/install.py --action repair
     ```
  2. If running in user mode, pass the `--dev` flag to use project-root file mappings:
     ```powershell
     python scripts/install.py --action install --dev
     ```
* **Verification**:
  * Run `arm status` and verify that the command succeeds without printing connection credentials errors.

---

## 3. Subprocess & Plugin Issues

### Symptom: LiteLLM Unavailable (HTTP 8000 Port Error)
* **Likely Causes**:
  * LiteLLM failed to build the YAML configuration because Ollama was offline during the discovery scan.
  * Port `8000` is occupied.
* **Diagnostic Steps**:
  1. Query LiteLLM status:
     ```powershell
     arm services
     ```
  2. View `C:\ProgramData\AIRuntimeManager\logs\litellm.log`.
* **Resolution**:
  1. Ensure Ollama is started first:
     ```powershell
     arm start ollama
     ```
  2. Re-trigger model discovery:
     ```powershell
     arm discover
     ```
  3. Restart LiteLLM:
     ```powershell
     arm restart litellm
     ```
* **Verification**:
  * Run `Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/models" -Headers @{"X-API-Key"="arm-local-token-secure"}`.

---

### Symptom: Ollama Service Fails to Start (Status STOPPED)
* **Likely Causes**:
  * The Ollama executable path was not detected by the plugin.
  * Port `11434` is blocked.
* **Diagnostic Steps**:
  1. Tail Ollama log output:
     ```powershell
     Get-Content -Path "C:\ProgramData\AIRuntimeManager\logs\ollama.log" -Tail 50
     ```
  2. Test execution of `ollama.exe` from a standard shell.
* **Resolution**:
  1. Update `binary_path` in SQLite `services` table to the absolute path of your `ollama.exe`.
  2. Free port `11434` if occupied.
* **Verification**:
  * Run `arm start ollama` and verify state shifts to `RUNNING`.

---

## 4. Recovery Procedures

### System Restore Procedure
If the database or configuration gets corrupted, perform a system restore:
1. Locate the backup zip file in `C:\ProgramData\AIRuntimeManager\backups\`.
2. Stop the daemon:
   ```powershell
   Stop-Service -Name AIRuntimeManager
   ```
3. Run the restore command:
   ```powershell
   python scripts/install.py --action restore --file "C:\ProgramData\AIRuntimeManager\backups\<backup_file>.zip"
   ```
4. Start the daemon:
   ```powershell
   Start-Service -Name AIRuntimeManager
   ```
5. Verify health:
   ```powershell
   arm status
   ```
