import os
import sys

# Add project root to sys.path to support imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import shutil
import subprocess
import socket
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
LOG_DIR = r"C:\ProgramData\AIRuntimeManager\logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "install.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("installer")

# Helper to run system commands
def run_command(cmd: List[str], timeout: float = 5.0) -> Optional[str]:
    try:
        # Use shell=True for path checks / native tools on Windows
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception as e:
        logger.debug(f"Failed to execute command '{' '.join(cmd)}': {e}")
    return None

def stop_service_and_wait(service_name: str, timeout_seconds: int = 30) -> None:
    import time
    try:
        res = subprocess.run(["sc.exe", "query", service_name], capture_output=True, text=True, timeout=5.0, shell=True)
        if "SERVICE_NAME" not in res.stdout:
            return
            
        if "STOPPED" in res.stdout:
            return
            
        print(f"[INSTALLER] Stopping service {service_name}...")
        subprocess.run(["sc.exe", "stop", service_name], capture_output=True, shell=True)
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            res = subprocess.run(["sc.exe", "query", service_name], capture_output=True, text=True, timeout=5.0, shell=True)
            if "STOPPED" in res.stdout:
                print(f"[INSTALLER] Service {service_name} successfully stopped.")
                time.sleep(1.5)
                return
            time.sleep(0.5)
        print(f"[INSTALLER] [WARNING] Service {service_name} did not stop in time.")
    except Exception as e:
        print(f"[INSTALLER] [WARNING] Failed to query/stop service {service_name}: {e}")

def check_admin() -> bool:
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

class PreReqDetector:
    @staticmethod
    def detect_python() -> Dict[str, Any]:
        return {
            "name": "Python",
            "installed": True,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "details": f"Path: {sys.executable}"
        }

    @staticmethod
    def detect_git() -> Dict[str, Any]:
        git_ver = run_command(["git", "--version"])
        return {
            "name": "Git",
            "installed": git_ver is not None,
            "version": git_ver.replace("git version ", "") if git_ver else None,
            "details": git_ver if git_ver else "Not installed"
        }

    @staticmethod
    def detect_docker() -> Dict[str, Any]:
        docker_ver = run_command(["docker", "--version"])
        return {
            "name": "Docker",
            "installed": docker_ver is not None,
            "version": docker_ver.replace("Docker version ", "").split(",")[0] if docker_ver else None,
            "details": docker_ver if docker_ver else "Not installed"
        }

    @staticmethod
    def detect_cuda() -> Dict[str, Any]:
        cuda_ver = run_command(["nvcc", "--version"])
        cuda_path = os.environ.get("CUDA_PATH")
        has_cuda = cuda_ver is not None or cuda_path is not None
        version = None
        if cuda_ver and "release" in cuda_ver:
            version = cuda_ver.split("release")[-1].strip().split(",")[0]
        return {
            "name": "CUDA Toolkit",
            "installed": has_cuda,
            "version": version,
            "details": f"CUDA_PATH: {cuda_path}" if cuda_path else "No CUDA_PATH set"
        }

    @staticmethod
    def detect_nvidia_driver() -> Dict[str, Any]:
        nvidia_smi = shutil.which("nvidia-smi") or os.path.exists(r"C:\Windows\System32\nvidia-smi.exe")
        driver_ver = None
        gpu_name = None
        if nvidia_smi:
            out = run_command(["nvidia-smi", "--query-gpu=driver_version,gpu_name", "--format=csv,noheader"])
            if out:
                parts = out.split(",")
                if len(parts) >= 2:
                    driver_ver = parts[0].strip()
                    gpu_name = parts[1].strip()
        return {
            "name": "NVIDIA Driver",
            "installed": nvidia_smi,
            "version": driver_ver,
            "details": gpu_name if gpu_name else "Not detected"
        }

    @staticmethod
    def detect_wsl() -> Dict[str, Any]:
        wsl_ver = run_command(["wsl", "--status"])
        wsl_list = run_command(["wsl", "--list", "--quiet"])
        distros = []
        if wsl_list:
            clean_list = wsl_list.replace('\x00', '').strip()
            distros = [d.strip() for d in clean_list.split() if d.strip()]
        return {
            "name": "Windows Subsystem for Linux (WSL)",
            "installed": wsl_ver is not None,
            "version": "WSL 2" if wsl_ver else None,
            "details": f"Distributions: {distros}" if distros else "No active distros"
        }

    @staticmethod
    def detect_ollama() -> Dict[str, Any]:
        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            p = os.path.join(local_appdata, "Programs", "Ollama", "ollama.exe")
            if os.path.exists(p):
                ollama_bin = p
        
        ollama_ver = run_command([ollama_bin or "ollama", "--version"]) if ollama_bin or shutil.which("ollama") else None
        return {
            "name": "Ollama",
            "installed": ollama_bin is not None or shutil.which("ollama") is not None,
            "version": ollama_ver if ollama_ver else None,
            "details": f"Executable: {ollama_bin}" if ollama_bin else "Not installed"
        }

    @staticmethod
    def detect_litellm() -> Dict[str, Any]:
        litellm_bin = shutil.which("litellm")
        # Check python environment
        has_pkg = False
        try:
            import litellm
            has_pkg = True
        except ImportError:
            pass

        return {
            "name": "LiteLLM",
            "installed": litellm_bin is not None or has_pkg,
            "version": "Installed" if has_pkg else None,
            "details": f"CLI Executable: {litellm_bin}" if litellm_bin else "Library installed in .venv"
        }

    @staticmethod
    def detect_openclaw() -> Dict[str, Any]:
        openclaw_bin = shutil.which("openclaw")
        has_config = os.path.exists(os.path.expanduser("~/.openclaw"))
        return {
            "name": "OpenClaw",
            "installed": openclaw_bin is not None or has_config,
            "version": "Detected" if openclaw_bin else None,
            "details": f"Executable: {openclaw_bin}" if openclaw_bin else "Configuration folder detected"
        }

    @staticmethod
    def detect_mcp() -> Dict[str, Any]:
        node_ver = run_command(["node", "--version"])
        npm_ver = run_command(["npm", "--version"])
        return {
            "name": "Model Context Protocol Node Runtime",
            "installed": node_ver is not None,
            "version": node_ver,
            "details": f"npm version: {npm_ver}" if npm_ver else "npm not found"
        }

def install_system_prereq(name: str, winget_id: str) -> bool:
    print(f"[INSTALLER] Attempting to install missing system prerequisite: {name} via winget...")
    logger.info(f"Installing {name} via winget ID {winget_id}")
    res = run_command(["winget", "install", "--id", winget_id, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements"], timeout=180.0)
    if res is not None:
        print(f"[INSTALLER] Successfully installed {name}.")
        return True
    print(f"[INSTALLER] Failed to install {name} via winget. Please install it manually.")
    return False

def configure_database():
    print("[INSTALLER] Initializing SQLite database...")
    logger.info("Initializing SQLite database")
    try:
        from src.backend.app.infrastructure.persistence.sqlite_db import init_db, get_connection
        init_db()
        
        # Seed default service entries if table is empty
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM services;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("[INSTALLER] Seeding initial service list...")
            logger.info("Seeding services table")
            
            # Find Ollama binary path
            ollama_path = shutil.which("ollama")
            if not ollama_path:
                local_appdata = os.environ.get("LOCALAPPDATA", "")
                p = os.path.join(local_appdata, "Programs", "Ollama", "ollama.exe")
                if os.path.exists(p):
                    ollama_path = p
                    
            services_data = [
                ("ollama", "Ollama Daemon", "ollama", 11434, "STOPPED", ollama_path, "serve", None, 1),
                ("litellm", "LiteLLM Gateway", "litellm", 8000, "STOPPED", "litellm", "", "litellm_config.yaml", 1),
                ("openclaw", "OpenClaw Supervisor", "openclaw", 8080, "STOPPED", "openclaw", "", None, 1),
                ("mcp", "Model Context Protocol Hub", "mcp", None, "RUNNING", None, "", None, 1)
            ]
            
            for s in services_data:
                cursor.execute("""
                    INSERT INTO services (id, name, type, port, status, binary_path, args, config_path, auto_start)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, s)
                
            # Seed default system configs
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_enabled', 'true');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_limit', '2');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('litellm_active_requests', '0');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_base_delay', '2.0');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_max_delay', '30.0');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_multiplier', '2.0');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_jitter_pct', '0.2');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_cooldown', '10.0');")
            cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_restart_window', '60.0');")
            
            conn.commit()
            print("[INSTALLER] Seeding database succeeded.")
        else:
            print("[INSTALLER] Database already contains service configurations. Skipping seed.")
            
        conn.close()
    except Exception as e:
        print(f"[INSTALLER] [ERROR] Database initialization failed: {e}")
        logger.error("Database setup failed", exc_info=True)
        raise e

def configure_windows_service():
    print("[INSTALLER] Configuring Windows Service 'AIRuntimeManager'...")
    logger.info("Registering Windows Service")
    python_exe = sys.executable
    service_script = os.path.abspath(r"src\backend\setup_service.py")
    
    # 1. Install or update the service registration
    # Stop service if running
    run_command(["sc.exe", "stop", "AIRuntimeManager"])
    
    # Register service
    cmd = [python_exe, service_script, "install"]
    res = run_command(cmd)
    if res is None:
        # Service might already exist, try to update config
        cmd_update = [python_exe, service_script, "update"]
        run_command(cmd_update)
        
    # Configure Startup type to Automatic
    run_command(["sc.exe", "config", "AIRuntimeManager", "start=auto"])
    
    # Start the service
    print("[INSTALLER] Launching service...")
    run_command(["sc.exe", "start", "AIRuntimeManager"])

def run_validation(is_dev: bool = False) -> bool:
    print("[INSTALLER] Running system validation checks...")
    logger.info("Running installation validation")
    
    if is_dev:
        print("[INSTALLER] [DEV MODE] Skipping port responsiveness check.")
        logger.info("Skipped port check in dev mode")
        return True
        
    # 1. Port conflict check
    ports_to_check = [8088]  # AI Control Plane port
    for port in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            # Try to connect to see if the server started
            if s.connect_ex(("127.0.0.1", port)) == 0:
                logger.info(f"Control plane gateway responsive on port {port}.")
                return True
    
    # Wait a bit and check again
    import time
    time.sleep(2.0)
    for port in ports_to_check:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
                
    return False

def produce_installation_report(detect_results: Dict[str, Any], validation_success: bool):
    print("[INSTALLER] Generating installation report...")
    report_path = r"C:\ProgramData\AIRuntimeManager\installation_report.md"
    
    report_content = f"""# AI Control Plane Version 1.0 Installation Report

**Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Installer ID**: Version 1.0.0 (Idempotent)

## System Prerequisite Detection Details

"""
    for key, value in detect_results.items():
        status_str = "✅ Detected" if value["installed"] else "❌ Missing / Not Found"
        ver_str = f" (Version: {value['version']})" if value["version"] else ""
        report_content += f"- **{value['name']}**: {status_str}{ver_str}\n  * Details: {value['details']}\n\n"
        
    report_content += f"""## Services Configuration

- **AIRuntimeManager Service**: Registered and configured.
- **Database**: SQLite database initialized.

## Installation Validation Status

- **Status**: {"SUCCESS" if validation_success else "PARTIAL / ACTION REQUIRED"}
- **Control Plane API Endpoint**: http://127.0.0.1:8088/health
- **FastAPI / Swagger Documentation**: http://127.0.0.1:8088/docs

"""
    if not validation_success:
        report_content += """
> [!WARNING]
> The orchestrator gateway port (8088) could not be contacted. The Windows Service 'AIRuntimeManager' may be starting up or has failed to start.
> Please inspect the logs at `C:\\ProgramData\\AIRuntimeManager\\logs\\service.log` for details.
"""
    else:
        report_content += """
> [!NOTE]
> The AI Control Plane daemon is running. You can now use the `arm` CLI or browse to the React Dashboard.
"""
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"[INSTALLER] Report saved to: {report_path}")

def scan_prereqs() -> Dict[str, Any]:
    return {
        "python": PreReqDetector.detect_python(),
        "git": PreReqDetector.detect_git(),
        "docker": PreReqDetector.detect_docker(),
        "cuda": PreReqDetector.detect_cuda(),
        "nvidia_driver": PreReqDetector.detect_nvidia_driver(),
        "wsl": PreReqDetector.detect_wsl(),
        "ollama": PreReqDetector.detect_ollama(),
        "litellm": PreReqDetector.detect_litellm(),
        "openclaw": PreReqDetector.detect_openclaw(),
        "mcp": PreReqDetector.detect_mcp()
    }

def backup_config(backup_dir: str = None) -> Optional[str]:
    print("[INSTALLER] Creating configuration backup...")
    try:
        program_data = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
        if not backup_dir:
            backup_dir = os.path.join(program_data, "backups", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup db
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(backup_dir, "arm.db"))
            print(f"[INSTALLER] Database backed up to {backup_dir}")
            logger.info(f"Database backed up to {backup_dir}")
            
        # Backup litellm config if exists
        if os.path.exists("litellm_config.yaml"):
            shutil.copy2("litellm_config.yaml", os.path.join(backup_dir, "litellm_config.yaml"))
            
        return backup_dir
    except Exception as e:
        print(f"[INSTALLER] [WARNING] Backup failed: {e}")
        logger.warning(f"Backup failed: {e}")
        return None

def rollback_system(backup_dir: str = None) -> bool:
    print("[INSTALLER] Initiating system rollback...")
    logger.info("System rollback initiated")
    try:
        program_data = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
        if not backup_dir:
            # find latest backup folder
            backups_parent = os.path.join(program_data, "backups")
            if not os.path.exists(backups_parent):
                print("[INSTALLER] [ERROR] No backups found for rollback.")
                return False
            dirs = [os.path.join(backups_parent, d) for d in os.listdir(backups_parent) if os.path.isdir(os.path.join(backups_parent, d))]
            if not dirs:
                print("[INSTALLER] [ERROR] No backup directories found.")
                return False
            backup_dir = max(dirs, key=os.path.getmtime)
            
        print(f"[INSTALLER] Restoring from backup: {backup_dir}")
        logger.info(f"Restoring from backup: {backup_dir}")
        
        # Stop service
        stop_service_and_wait("AIRuntimeManager")
        
        # Restore db
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        backup_db = os.path.join(backup_dir, "arm.db")
        if os.path.exists(backup_db):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(backup_db, db_path)
            print(f"[INSTALLER] Restored database to {db_path}")
            
        # Restore config
        backup_cfg = os.path.join(backup_dir, "litellm_config.yaml")
        if os.path.exists(backup_cfg):
            shutil.copy2(backup_cfg, "litellm_config.yaml")
            print("[INSTALLER] Restored litellm_config.yaml")
            
        # Start service
        run_command(["sc.exe", "start", "AIRuntimeManager"])
        print("[INSTALLER] Rollback finished successfully.")
        return True
    except Exception as e:
        print(f"[INSTALLER] [ERROR] Rollback failed: {e}")
        logger.error(f"Rollback failed: {e}", exc_info=True)
        return False

def uninstall_service_and_files(is_dev: bool = False):
    print("[INSTALLER] Uninstalling AI Control Plane service and files...")
    logger.info("Uninstall started")
    
    # 1. Stop service
    if not is_dev:
        stop_service_and_wait("AIRuntimeManager")
        
        # 2. Delete service
        python_exe = sys.executable
        service_script = os.path.abspath(r"src\backend\setup_service.py")
        print("[INSTALLER] Removing service registration...")
        run_command([python_exe, service_script, "remove"])
        run_command(["sc.exe", "delete", "AIRuntimeManager"])
        
    # 3. Clean up DB and configurations
    from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
    db_path = get_db_path()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"[INSTALLER] Deleted database file: {db_path}")
        except Exception as e:
            print(f"[INSTALLER] [WARNING] Could not delete database file: {e}")
            
    print("[INSTALLER] Uninstall completed.")

def upgrade_system(is_dev: bool = False):
    print("[INSTALLER] Upgrading system...")
    logger.info("Upgrade started")
    
    # 1. Backup first
    backup_config()
    
    # 2. Update database tables/migration checks
    print("[INSTALLER] Running database schema migration updates...")
    configure_database()
    
    # Update current version in database config
    try:
        from src.backend.app.infrastructure.persistence.sqlite_db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('current_version', '1.0.0');")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[INSTALLER] [WARNING] Failed to update version key: {e}")
        
    # 3. Restart service
    if not is_dev:
        print("[INSTALLER] Restarting service 'AIRuntimeManager' to apply upgrade...")
        stop_service_and_wait("AIRuntimeManager")
        run_command(["sc.exe", "start", "AIRuntimeManager"])
        
    print("[INSTALLER] Upgrade completed.")

def repair_installation(is_dev: bool = False):
    print("[INSTALLER] Repairing installation...")
    logger.info("Repair started")
    
    # 1. Ensure DB exists and is configured
    configure_database()
    
    # 2. Ensure Service is configured
    if not is_dev:
        configure_windows_service()
        
    print("[INSTALLER] Repair completed.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Control Plane Version 1.0 Installer")
    parser.add_argument("--action", type=str, default="install", choices=["install", "uninstall", "repair", "upgrade", "rollback", "reinstall", "restore"], help="Installation action to perform")
    parser.add_argument("--file", type=str, help="Zip file path for restore/rollback")
    parser.add_argument("--dev", action="store_true", help="Run in developer mode (bypasses admin check and service installation)")
    parser.add_argument("--dry-run", action="store_true", help="Scan prerequisites and print validation parameters without making changes")
    parser.add_argument("--version", action="store_true", help="Print installer version")
    args_parsed = parser.parse_args()
    
    if args_parsed.version:
        print("AI Control Plane Installer Version 1.0.0")
        sys.exit(0)
        
    is_dev = args_parsed.dev
    action = args_parsed.action
    dry_run = args_parsed.dry_run
    
    if dry_run:
        print("[INSTALLER] [DRY RUN] Performing dry run prerequisite scan...")
        results = scan_prereqs()
        print(f"[INSTALLER] Dry run complete. Scan results:\n{json.dumps(results, indent=2)}")
        sys.exit(0)
        
    if not is_dev and not check_admin():
        print("[INSTALLER] [ERROR] This installer must be run as Administrator.")
        sys.exit(1)
        
    if action == "uninstall":
        uninstall_service_and_files(is_dev)
        sys.exit(0)
        
    if action == "rollback":
        rollback_success = rollback_system()
        sys.exit(0 if rollback_success else 1)
        
    if action == "restore":
        if not args_parsed.file:
            print("[INSTALLER] [ERROR] Restore action requires a --file argument specifying the zip backup file.")
            sys.exit(1)
        print(f"[INSTALLER] Restoring system from backup file: {args_parsed.file}")
        if not is_dev:
            stop_service_and_wait("AIRuntimeManager")
        from src.backend.app.infrastructure.backup_restore import restore_system_config
        try:
            restore_system_config(args_parsed.file)
            print("[INSTALLER] System configuration restored successfully.")
            restore_ok = True
        except Exception as ex:
            print(f"[INSTALLER] [ERROR] Restore failed: {ex}")
            restore_ok = False
        if not is_dev:
            run_command(["sc.exe", "start", "AIRuntimeManager"])
        sys.exit(0 if restore_ok else 1)
        
    if action == "upgrade":
        upgrade_system(is_dev)
        validation_success = run_validation(is_dev)
        if validation_success:
            print("[INSTALLER] Upgrade finished successfully.")
            sys.exit(0)
        else:
            print("[INSTALLER] Upgrade completed with validation warnings.")
            sys.exit(0)
            
    if action == "repair":
        repair_installation(is_dev)
        validation_success = run_validation(is_dev)
        sys.exit(0 if validation_success else 1)
        
    if action == "reinstall":
        print("[INSTALLER] Initiating reinstall sequence...")
        uninstall_service_and_files(is_dev)
        print("[INSTALLER] Performing fresh installation...")
        
    # Standard fresh install (or remainder of reinstall)
    print("[INSTALLER] Scanning prerequisites...")
    results = scan_prereqs()
    
    # Log results
    logger.info(f"Prerequisite results: {json.dumps(results, indent=2)}")
    
    # Try installing missing dependencies
    if not results["git"]["installed"]:
        try:
            install_system_prereq("Git", "Git.Git")
            results["git"] = PreReqDetector.detect_git()
        except Exception as e:
            logger.warning(f"Skipping Git installation: {e}")
        
    if not results["ollama"]["installed"]:
        try:
            install_system_prereq("Ollama", "Ollama.Ollama")
            results["ollama"] = PreReqDetector.detect_ollama()
        except Exception as e:
            logger.warning(f"Skipping Ollama installation: {e}")
        
    # Configure Database
    configure_database()
    
    # Configure Service
    if not is_dev:
        configure_windows_service()
    else:
        print("[INSTALLER] [DEV MODE] Skipping Windows Service configuration.")
        logger.info("Skipped Windows Service configuration in dev mode")
    
    # Validate
    validation_success = run_validation(is_dev)
    
    # Produce Report
    produce_installation_report(results, validation_success)
    
    if validation_success:
        print("[INSTALLER] Installation finished successfully.")
        sys.exit(0)
    else:
        print("[INSTALLER] Installation completed with warnings. See report for details.")
        sys.exit(0)


if __name__ == "__main__":
    main()
