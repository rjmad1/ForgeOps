# Operations & Troubleshooting Guide: AI Runtime Manager

This guide describes operational procedures, logging architecture, backup/restore strategies, and troubleshooting steps.

## Logging Architecture

All system components log to stdout and a rolling file in JSON format. Logs are located at:
`C:\ProgramData\AIRuntimeManager\logs\service.log`

### Structured Log Format
Each line is a single JSON object containing standard schema keys:
```json
{
  "timestamp": "2026-07-05T15:51:53Z",
  "level": "INFO",
  "module": "process_manager",
  "message": "Subprocess Ollama started successfully",
  "pid": 4812,
  "service_id": "ollama"
}
```

---

## Operations Procedures

### 1. Backup Configuration and Database
A backup packages the SQLite database (`arm.db`), `arm-config.yaml`, and generated plugin configurations into a timestamped zip archive.
- **REST API Call**: `POST /api/operations/backup`
- **CLI Command**: `arm backup`

### 2. Restore System Configuration
Restoring replaces the local database and configuration files with the target zip, then restarts the orchestrator service.
- **REST API Call**: `POST /api/operations/restore` (JSON Body: `{"backup_file": "C:\\backups\\arm-backup.zip"}`)
- **CLI Command**: `arm restore --file C:\backups\arm-backup.zip`

### 3. Run Benchmark Suite
Evaluates local inference capabilities:
- Measures Time-To-First-Token (TTFT) in milliseconds.
- Calculates average generation throughput (tokens per second).
- Generates a markdown report saved in `C:\ProgramData\AIRuntimeManager\benchmarks\`.
- **REST API Call**: `POST /api/operations/benchmark`
- **CLI Command**: `arm benchmark`

---

## Troubleshooting Guide

### Issue 1: Port 8000 (LiteLLM) or 11434 (Ollama) is already in use
- **Symptoms**: Service fails to start. Logs show `OSError: [Errno 10048] Only one usage of each socket address is normally permitted`.
- **Solution**: Identify the process using the port and terminate it:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```
  Restart the AI Runtime Manager service.

### Issue 2: Zombie Subprocesses
- **Symptoms**: Memory utilization is high, but the orchestrator lists the service as stopped.
- **Solution**: Terminate orphaned processes manually using their names:
  ```powershell
  Stop-Process -Name "ollama" -Force
  Stop-Process -Name "litellm" -Force
  ```
