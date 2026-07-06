# register-service.ps1
# PowerShell script to register AI Runtime Manager as a Windows Service.
# Run from an Elevated (Administrator) PowerShell prompt.

$ProjectDir = "C:\Users\rjkum\.gemini\antigravity-ide\scratch\ai-runtime-manager"
$PythonExe = "$ProjectDir\.venv\Scripts\python.exe"
$ServiceScript = "$ProjectDir\src\backend\setup_service.py"

# Create log directory in ProgramData
$LogDir = "C:\ProgramData\AIRuntimeManager\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "Created log directory at $LogDir"
}

# Verify dependencies
if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment python.exe not found at $PythonExe. Please set up the virtual env first."
    Exit 1
}

Write-Host "Installing Windows Service: AIRuntimeManager..."
# Install the service
& $PythonExe $ServiceScript install

# Configure service to start automatically
Set-Service -Name "AIRuntimeManager" -StartupType Automatic

Write-Host "Starting Windows Service: AIRuntimeManager..."
Start-Service -Name "AIRuntimeManager"

Write-Host "Service registration completed."
Get-Service -Name "AIRuntimeManager"
