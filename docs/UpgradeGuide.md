# Upgrade Guide: Upgrading to Version 1.0.0

This guide outlines the steps to upgrade an existing pre-release deployment of the AI Runtime Manager to **ForgeOps Version 1.0.0**.

---

## Upgrade Steps

### 1. Stop Current Service
Run PowerShell as **Administrator** and stop the existing service to release active file handles:
```powershell
sc.exe stop AIRuntimeManager
```

### 2. Backup Database & Configuration
Backup your current database and settings by running the installer backup action:
```bash
python scripts/install.py --action install --dev
```
This automatically backs up the database to `%PROGRAMDATA%\AIRuntimeManager\backups\backup_<timestamp>\`.

### 3. Pull Version 1.0.0 Code
Fetch the release branch and check out Version 1.0.0:
```bash
git fetch --all
git checkout tags/v1.0.0
```

### 4. Run Upgrade Script
Execute the upgrade action in the installer. This will migrate the SQLite database structure and update the configuration files:
```bash
python scripts/install.py --action upgrade
```

### 5. Verify the Upgrade
Validate that all subsystems are fully online and passing:
```bash
python scripts/validate_system.py
```
Check that the `current_version` configuration in your database is updated to `1.0.0`:
```bash
python -m src.cli.main diagnostics
```
