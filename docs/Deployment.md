# Deployment & Installation: AI Runtime Manager

This document provides step-by-step instructions for deploying and installing the AI Runtime Manager on Windows 11 Professional.

## Prerequisites

1. **Operating System**: Windows 11 Professional (with Administrator access).
2. **Python**: Python 3.10 or 3.11 installed and added to the system PATH.
3. **Node.js & npm**: Node.js v18+ for building the React dashboard interface.
4. **Ollama**: Installed locally on the workstation.
5. **NSSM (Non-Sucking Service Manager)**: Recommended for wrapping the Python FastAPI server as a Windows Service, or python `pywin32` library.

## Step-by-Step Installation

### Step 1: Clone and Set Up Workspace
Create the project folder and navigate to it:
```powershell
cd C:\Users\rjkum\.gemini\antigravity-ide\scratch\ai-runtime-manager
```

### Step 2: Initialize Python Virtual Environment
Initialize a local virtual environment to isolate dependencies:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Initialize Database Schema
Run the database migrations tool to initialize the SQLite database:
```powershell
python -m src.backend.app.database init
```

### Step 4: Build Frontend Dashboard
Build the React single-page application:
```powershell
cd src/frontend
npm install
npm run build
cd ../..
```
This compiles the static assets into `src/backend/app/static`. The FastAPI backend serves these static files to act as the web dashboard.

### Step 5: Install Windows Service
Use the provided PowerShell script (running as Administrator) to register the background orchestrator service:
```powershell
# Run in Elevated PowerShell
PowerShell -ExecutionPolicy Bypass -File .\scripts\register-service.ps1
```
The script registers the service under the name `AIRuntimeManager` and sets the startup type to `Automatic`.

## Verification

Verify the service is running and query its status:
```powershell
Get-Service -Name "AIRuntimeManager"
```
Or check via the CLI tool:
```powershell
arm status
```
Inspect logs to ensure sub runtimes have successfully started:
```powershell
Get-Content -Path "C:\ProgramData\AIRuntimeManager\logs\orchestrator.log" -Tail 50
```
