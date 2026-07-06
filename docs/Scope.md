# Scope: AI Runtime Manager

This document clarifies what lies within the boundaries of the AI Runtime Manager implementation and what is explicitly excluded.

## In-Scope

1. **Service Orchestration**:
   - Automatic registration, startup, shutdown, and restart of local processes: Ollama, LiteLLM, OpenClaw, and MCP Servers.
   - Hosting the runtime manager as a background Windows Service (`win32service`).
   - Clean shutdown sequences (no orphaned processes).

2. **Model & Configuration Management**:
   - Dynamic discovery of installed Ollama models and LiteLLM aliases.
   - Categorization of models into embedding, vision, reasoning, coding, and general tasks.
   - Programmatic generation of YAML configurations for LiteLLM, Ollama, and OpenClaw.

3. **Metrics & Health**:
   - Polling of local hardware metrics: VRAM usage, GPU utilization, CPU, RAM.
   - HTTP/TCP health checks for active endpoints.
   - Tracking connection count, latency (Average Response Time), and requests queue.

4. **User Interfaces**:
   - Single-page React dashboard visualizing hardware, services status, logs, and controls (Start/Stop/Restart/Update/Backup/Restore/Benchmark/Diagnostics).
   - Unified REST API exposing control endpoints.
   - PowerShell/Python CLI for administration commands.

## Out-of-Scope

1. **Multi-User / RBAC Security**:
   - Multi-tenant model routing or granular permissions. The platform assumes single-user local developer workstations.
2. **Multi-Host Orchestration**:
   - Clustering multiple workstations or connecting to remote Kubernetes/Docker pools.
3. **Cloud Model Deployments**:
   - Deploying or managing cloud-hosted endpoints (e.g., AWS Bedrock, GCP Vertex AI), except as configured as local proxies via LiteLLM aliases.
4. **Model Training & Fine-Tuning**:
   - The platform is strictly an inference runtime orchestrator. Training, fine-tuning, and dataset management are excluded.
5. **Non-Windows Environments**:
   - Native deployment on Linux, macOS, or WSL. All service management is oriented around native Windows Services, paths, and PowerShell scripts.
