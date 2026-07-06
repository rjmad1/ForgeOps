# ForgeOps Diagnostics Guide

This guide details the system diagnostics, health checks, metrics capture, and log bundles used to monitor and debug local AI runtimes.

## 1. Health Checks & Telemetry

The ForgeOps orchestrator runs an asynchronous health daemon:
* **Liveness Probes**: Evaluates service liveness using HTTP GET checks or raw TCP port tests at regular intervals.
* **Telemetry**: Stores performance records (CPU, RAM, GPU, VRAM) in the `performance_metrics` SQLite database table.
* **Dashboard charts**: Observability metrics are rendered dynamically in the **Observability** tab of the dashboard.

## 2. CLI Diagnostics

You can retrieve quick status summaries directly from the terminal:
```powershell
# Run self-diagnostic report of configurations, PIDs, and DB entries
arm diagnostics
```

## 3. Support Bundles

To troubleshoot complex issues:
```powershell
# Generate a compressed support archive containing service logs and database state
arm support-bundle --output "C:\users\public\support_bundle.zip"
```
The support bundle zips the following:
* Service configuration records.
* Database state dumps (`arm.db`).
* Standard output / standard error logs from the runtimes.
* System environmental variables.
