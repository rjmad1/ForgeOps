# ForgeOps Operations Manual

This manual defines the regular maintenance procedures, health monitoring protocols, and operational checklists required to keep the ForgeOps (AI Runtime Manager) platform running optimally.

---

## 1. Routine Operational Calendars

### Daily Checklists
- [ ] **Daemon Uptime Verification**: Confirm the FastAPI gateway is responsive.
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8088/health"
  ```
- [ ] **Service Status Scan**: Scan status of subruntimes.
  ```powershell
  arm status
  ```
- [ ] **Resource Leak Check**: Inspect CPU and RAM usage. Ensure memory usage matches expectations (typically <1GB when idle, spikes during active inference).
- [ ] **Log File Inspection**: Scan the active error logs:
  ```powershell
  # Search for ERROR entries in general service logs
  Select-String -Path "C:\ProgramData\AIRuntimeManager\logs\service.log" -Pattern "ERROR" | Select-Object -First 10
  ```

### Weekly Maintenance
- [ ] **Log Compression**: Subprocess logs can grow rapidly under heavy use. Compress and archive logs exceeding 100MB:
  ```powershell
  # Compress inactive logs
  Compress-Archive -Path "C:\ProgramData\AIRuntimeManager\logs\*.log" -DestinationPath "C:\ProgramData\AIRuntimeManager\logs\archive_logs.zip" -Update
  ```
- [ ] **Storage Capacity Scan**: Local LLMs are stored in `%USERPROFILE%\.ollama\models\`. Ensure disk partitions have at least 20GB of headroom.
- [ ] **Automated Backup**: Create a system snapshot:
  ```powershell
  arm backup
  ```

### Monthly Housekeeping
- [ ] **Database Vacuuming**: Shrink the SQLite database and rebuild indexes:
  ```powershell
  sqlite3 C:\ProgramData\AIRuntimeManager\db\arm.db "VACUUM;"
  ```
- [ ] **Metrics History Pruning**: Clean old performance metrics records to prevent database bloat:
  ```powershell
  sqlite3 C:\ProgramData\AIRuntimeManager\db\arm.db "DELETE FROM performance_metrics WHERE timestamp < date('now', '-30 days');"
  ```
- [ ] **Recovery Drills**: Run a mock restore verification on a test database instance to validate backup viability.

---

## 2. Health & Performance Monitoring

ForgeOps exposes key metrics for operations integration.

### Health Telemetry Endpoints
* **Overall Health**: `GET /api/v1/health`
  * Returns JSON detailing individual service states:
    ```json
    {
      "status": "healthy",
      "services": {
        "ollama": "RUNNING",
        "litellm": "RUNNING",
        "openclaw": "STOPPED",
        "mcp": "RUNNING"
      }
    }
    ```

### Performance Benchmarking
Run the built-in benchmarking suite to check inference performance:
```powershell
arm benchmark
```
**Output Parameters**:
* **TTFT (Time-To-First-Token)**: Measures time (in ms) to return the initial token (ideal target: <500ms).
* **Speed (Tokens/Second)**: Measures throughput speed during generation (ideal target: >15 tokens/sec).
* **Report Generation**: Benchmarking writes reports directly to `C:\ProgramData\AIRuntimeManager\benchmarks\`.

---

## 3. Operational Procedures

### A. Support Bundle Collection
If an outage or degradation occurs, generate the support bundle for analysis:
```powershell
arm support-bundle --output "C:\temp\incident_report.zip"
```
**Included Assets:**
1. Database copy (`arm.db`).
2. General orchestrator logs (`service.log`, `install.log`).
3. Subprocess logs (`ollama.log`, `litellm.log`, `openclaw.log`).
4. System environment variables.

### B. Upgrades & Patches Validation
Before certifying an upgrade:
1. Trigger the upgrade command:
   ```powershell
   python scripts/install.py --action upgrade
   ```
2. Verify system compliance by running the validator:
   ```powershell
   python scripts/validate_system.py
   ```
3. Confirm the SQLite database version tag is updated:
   ```powershell
   sqlite3 C:\ProgramData\AIRuntimeManager\db\arm.db "SELECT value FROM system_config WHERE key = 'current_version';"
   ```
