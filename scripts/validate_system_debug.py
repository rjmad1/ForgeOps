import os
import sys
import subprocess
import time
import shutil
import sqlite3
import zipfile
import json
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import httpx

# Set target paths
PROGRAM_DATA = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
if os.path.exists(PROGRAM_DATA):
    REPORT_PATH = os.path.join(PROGRAM_DATA, "validation_report.md")
else:
    REPORT_PATH = "validation_report.md"

class SystemValidator:
    def __init__(self, is_dev: bool = True):
        self.is_dev = is_dev
        self.results = {}
        self.api_process = None
        self.api_url = "http://127.0.0.1:8088"
        self.dev_flag = ["--dev"] if is_dev else []

    def get_headers(self) -> Dict[str, str]:
        key = ""
        path = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager\.session_api_key")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    key = f.read().strip()
            except Exception:
                pass
        if not key:
            local_path = ".session_api_key"
            if os.path.exists(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        key = f.read().strip()
                except Exception:
                    pass
        return {"X-API-Key": key} if key else {}

    def api_get(self, path: str, **kwargs) -> httpx.Response:
        headers = self.get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        return httpx.get(f"{self.api_url}{path}", **kwargs)

    def api_post(self, path: str, **kwargs) -> httpx.Response:
        headers = self.get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        return httpx.post(f"{self.api_url}{path}", **kwargs)

    def log_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        if category not in self.results:
            self.results[category] = []
        self.results[category].append({
            "name": test_name,
            "status": "PASS" if passed else "FAIL",
            "details": details
        })
        status_str = "PASS" if passed else "FAIL"
        print(f"[{category.upper()}] {test_name}: {status_str} {f'({details})' if details else ''}")

    def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, shell=True)

    def validate_installation_actions(self):
        print("\n--- Validating Installation Action Flows ---")
        
        # 1. Dry run
        res = self.run_command([sys.executable, "scripts/install.py", "--dry-run"] + self.dev_flag)
        self.log_result(
            "Installation Action",
            "Dry Run Scan",
            res.returncode == 0 and "Dry run complete" in res.stdout,
            f"Exit code: {res.returncode}"
        )
        
        # 2. Fresh Installation
        res = self.run_command([sys.executable, "scripts/install.py", "--action", "install"] + self.dev_flag)
        db_exists = False
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        if os.path.exists(db_path):
            db_exists = True
        self.log_result(
            "Installation Action",
            "Fresh Installation Action",
            res.returncode == 0 and db_exists,
            f"DB Exists: {db_exists}, exit code: {res.returncode}"
        )

        # 3. Database seeding checks
        seeded_correctly = False
        count = 0
        if db_exists:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM services;")
                count = cursor.fetchone()[0]
                seeded_correctly = (count > 0)
                conn.close()
            except Exception as e:
                seeded_correctly = False
        self.log_result(
            "Database",
            "Database Seeding Verification",
            seeded_correctly,
            f"Seeded service count: {count}"
        )

        # 4. Repair Installation simulation
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
        res = self.run_command([sys.executable, "scripts/install.py", "--action", "repair"] + self.dev_flag)
        repaired_ok = os.path.exists(db_path)
        self.log_result(
            "Installation Action",
            "Repair Installation Action",
            res.returncode == 0 and repaired_ok,
            f"Database successfully re-created during repair: {repaired_ok}"
        )

        # 5. Upgrade Installation simulation
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
        val = "N/A"
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE system_config (key TEXT PRIMARY KEY, value TEXT);")
            conn.execute("INSERT INTO system_config (key, value) VALUES ('current_version', '0.1.0');")
            conn.commit()
            conn.close()
        except Exception:
            pass
        res = self.run_command([sys.executable, "scripts/install.py", "--action", "upgrade"] + self.dev_flag)
        upgraded_ok = False
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_config WHERE key = 'current_version';")
                val = cursor.fetchone()[0]
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='services';")
                tbl_exists = cursor.fetchone() is not None
                upgraded_ok = (val == "1.0.0" and tbl_exists)
                conn.close()
            except Exception:
                upgraded_ok = False
        self.log_result(
            "Installation Action",
            "Upgrade Action",
            res.returncode == 0 and upgraded_ok,
            f"DB Upgraded version: {val}"
        )

        # 6. Rollback simulation
        rollback_ok = False
        restored_val = "N/A"
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('test_rollback_key', 'original_val');")
            conn.commit()
            conn.close()
            
            # Execute backup
            from scripts.install import backup_config
            backup_dir = backup_config()
            
            # Make a change
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('test_rollback_key', 'changed_val');")
            conn.commit()
            conn.close()
            
            # Rollback
            res_rollback = self.run_command([sys.executable, "scripts/install.py", "--action", "rollback"] + self.dev_flag)
            
            # Verify restored
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = 'test_rollback_key';")
            restored_val = cursor.fetchone()[0]
            conn.close()
            
            rollback_ok = (restored_val == "original_val" and res_rollback.returncode == 0)
        except Exception as e:
            rollback_ok = False
            
        self.log_result(
            "Installation Action",
            "Rollback Action",
            rollback_ok,
            f"Restored key status: {restored_val}"
        )
        
        # 7. Reinstall Action
        res = self.run_command([sys.executable, "scripts/install.py", "--action", "reinstall"] + self.dev_flag)
        self.log_result(
            "Installation Action",
            "Reinstall Action",
            res.returncode == 0 and os.path.exists(db_path),
            f"Exit code: {res.returncode}"
        )

        # 8. Uninstall simulation
        res = self.run_command([sys.executable, "scripts/install.py", "--action", "uninstall"] + self.dev_flag)
        db_removed = not os.path.exists(db_path)
        self.log_result(
            "Installation Action",
            "Uninstall Action",
            res.returncode == 0 and db_removed,
            f"DB file deleted: {db_removed}, exit code: {res.returncode}"
        )

        # Re-run fresh install to leave system in clean configured state for subsystem checks
        self.run_command([sys.executable, "scripts/install.py", "--action", "install"] + self.dev_flag)

    def start_api_server(self):
        print("\n--- Starting API Server for Subsystem Validations ---")
        # Redirect uvicorn output to file
        self.uvicorn_log = open("uvicorn_debug.log", "w")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        self.api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.backend.app.main:app", "--host", "127.0.0.1", "--port", "8088"],
            stdout=self.uvicorn_log,
            stderr=self.uvicorn_log,
            env=env,
            text=True
        )
        
        # Wait for API to respond (Wait longer: 30 retries of 0.5s = 15 seconds)
        retries = 30
        api_online = False
        while retries > 0:
            try:
                res = self.api_get("/health", timeout=1.0)
                if res.status_code == 200:
                    api_online = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
            retries -= 1
            
        if api_online:
            print("API Server online on port 8088.")
        else:
            print("WARNING: API Server failed to respond on port 8088. Validation checks may fail.")

    def stop_api_server(self):
        print("\n--- Stopping API Server ---")
        if self.api_process:
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5.0)
                print("API Server stopped.")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                print("API Server killed forcefully.")
        if hasattr(self, 'uvicorn_log'):
            self.uvicorn_log.close()

    def validate_database_subsystem(self):
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        passed = False
        details = ""
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cursor.fetchall()]
                expected = ["services", "models", "performance_metrics", "system_config", "system_inventory", "operational_history"]
                missing = [t for t in expected if t not in tables]
                if not missing:
                    passed = True
                    details = f"All {len(expected)} tables verified."
                else:
                    details = f"Missing tables: {missing}"
                conn.close()
            except Exception as e:
                details = f"DB Exception: {e}"
        else:
            details = "DB file does not exist"
            
        self.log_result("Database", "Database Schema Verification", passed, details)

    def validate_windows_services(self):
        passed = False
        details = ""
        if self.is_dev:
            setup_script = r"src\backend\setup_service.py"
            reg_script = r"scripts\register-service.ps1"
            if os.path.exists(setup_script) and os.path.exists(reg_script):
                passed = True
                details = "Service scripts present (Dev Mode Bypass)"
            else:
                details = f"Missing setup service script or registration script"
        else:
            res = self.run_command(["sc.exe", "query", "AIRuntimeManager"])
            if res.returncode == 0 and "SERVICE_NAME: AIRuntimeManager" in res.stdout:
                passed = True
                details = "AIRuntimeManager registered in Windows Service Control Manager"
            else:
                details = f"Service not found, sc return code: {res.returncode}"
                
        self.log_result("Windows Services", "Service Registration", passed, details)

    def validate_rest_api_and_cli(self):
        # 1. REST API
        endpoints = [
            ("/health", "Health endpoint"),
            ("/api/v1/services", "List services"),
            ("/api/v1/plugins", "List plugins"),
            ("/api/v1/models", "List capabilities"),
            ("/api/v1/inventory", "List inventory"),
            ("/api/v1/history", "List history"),
            ("/api/v1/metrics", "List metrics"),
            ("/api/v1/system/metrics", "System performance metrics"),
            ("/api/v1/diagnostics/report", "Diagnostics report")
        ]
        
        for path, name in endpoints:
            passed = False
            details = ""
            try:
                res = self.api_get(path, timeout=3.0)
                if res.status_code == 200:
                    passed = True
                    details = "Status 200 OK"
                else:
                    details = f"HTTP {res.status_code}"
            except Exception as e:
                details = f"HTTP error: {e}"
            self.log_result("REST API", f"GET {path} ({name})", passed, details)
            
        # 2. CLI integration
        cli_subcommands = [
            ("services", "List services"),
            ("inventory", "List inventory"),
            ("history", "List history"),
            ("diagnostics", "Diagnostics summary")
        ]
        for cmd, name in cli_subcommands:
            passed = False
            details = ""
            res = self.run_command([sys.executable, "-m", "src.cli.main", cmd])
            if res.returncode == 0 and res.stdout:
                passed = True
                details = f"Command succeeded, stdout size: {len(res.stdout)} chars"
            else:
                details = f"Return code: {res.returncode}, stderr: {res.stderr.strip()}"
            self.log_result("CLI", f"arm {cmd} ({name})", passed, details)

    def validate_dashboard(self):
        passed = False
        details = ""
        index_html_path = r"src\frontend\dist\index.html"
        if os.path.exists(index_html_path):
            passed = True
            details = "Vite static bundle index.html exists at src/frontend/dist"
        else:
            details = "Static bundle not built yet (run npm run build in frontend)"
        self.log_result("Dashboard", "Dashboard Build Distribution", passed, details)

    def validate_plugins_and_policies(self):
        passed = False
        details = ""
        try:
            res = self.api_get("/api/v1/plugins", timeout=3.0)
            if res.status_code == 200:
                plugins = res.json()
                plugin_ids = [p["id"] for p in plugins]
                expected = ["ollama", "litellm", "openclaw", "mcp"]
                missing = [p for p in expected if p not in plugin_ids]
                if not missing:
                    passed = True
                    details = f"Registered plugins: {plugin_ids}"
                else:
                    details = f"Missing expected plugins: {missing}"
            else:
                details = f"HTTP {res.status_code}"
        except Exception as e:
            details = f"Connection error: {e}"
        self.log_result("Plugins", "Plugin Load Registry", passed, details)

        # Policies
        policy_passed = False
        policy_details = ""
        try:
            res_config = self.api_get("/api/v1/diagnostics/report", timeout=3.0)
            if res_config.status_code == 200:
                cfg = res_config.json().get("configs", {})
                if "auto_restart_enabled" in cfg and "auto_restart_limit" in cfg:
                    policy_passed = True
                    policy_details = f"Auto restart enabled: {cfg['auto_restart_enabled']}, Limit: {cfg['auto_restart_limit']}"
                else:
                    policy_details = f"Missing configs in report: {cfg}"
            else:
                policy_details = f"HTTP {res_config.status_code}"
        except Exception as e:
            policy_details = f"Connection error: {e}"
        self.log_result("Policies", "Policy Config Constraints", policy_passed, policy_details)

    def validate_scheduler_and_workflows(self):
        passed = False
        details = ""
        try:
            res = self.api_get("/api/v1/history", timeout=3.0)
            if res.status_code == 200:
                history = res.json()
                if len(history) > 0:
                    passed = True
                    details = f"Found {len(history)} total events logged in history."
                else:
                    details = "No events logged in SQLite history"
            else:
                details = f"HTTP {res.status_code}"
        except Exception as e:
            details = f"Connection error: {e}"
        self.log_result("Workflow Engine", "Execution History Tracking", passed, details)

        # Configuration generator
        config_gen_passed = False
        config_gen_details = ""
        try:
            from src.backend.app.plugins.litellm import LiteLLMPlugin
            from src.backend.app.domain.models import Service
            plugin = LiteLLMPlugin()
            svc = Service(
                id="litellm",
                name="LiteLLM",
                type="litellm",
                port=8000,
                status="STOPPED",
                binary_path="litellm",
                args=[],
                config_path="test_litellm_config.yaml"
            )
            plugin.generate_runtime_files(svc)
            if os.path.exists("test_litellm_config.yaml"):
                config_gen_passed = True
                config_gen_details = "Configuration generator successfully wrote config file."
                os.remove("test_litellm_config.yaml")
            else:
                config_gen_details = "Configuration generator failed to produce output file."
        except Exception as e:
            config_gen_details = str(e)
        self.log_result("Configuration Generator", "LiteLLM Config Generation", config_gen_passed, config_gen_details)

        # Inventory Engine
        inv_passed = False
        inv_details = ""
        try:
            res_inv = self.api_get("/api/v1/inventory", timeout=3.0)
            if res_inv.status_code == 200:
                inv = res_inv.json()
                if len(inv) > 0:
                    inv_passed = True
                    inv_details = f"Host inventory items categories: {list(set([item['category'] for item in inv]))}"
                else:
                    inv_details = "Inventory table is empty"
            else:
                inv_details = f"HTTP {res_inv.status_code}"
        except Exception as e:
            inv_details = str(e)
        self.log_result("Inventory Engine", "Host Environment Scan", inv_passed, inv_details)

    def validate_logs_and_metrics(self):
        # Logs
        log_passed = False
        log_details = ""
        log_paths = [
            os.path.join(PROGRAM_DATA, "logs", "install.log"),
            os.path.join(PROGRAM_DATA, "logs", "service.log"),
            "service.log",
            "install.log"
        ]
        existing_logs = [p for p in log_paths if os.path.exists(p)]
        if existing_logs:
            log_passed = True
            log_details = f"Active log files: {[os.path.basename(p) for p in existing_logs]}"
        else:
            log_details = "No log files found"
        self.log_result("Logs", "Logs Audit Integrity", log_passed, log_details)

        # Metrics
        metric_passed = False
        metric_details = ""
        try:
            res_met = self.api_get("/api/v1/system/metrics", timeout=3.0)
            if res_met.status_code == 200:
                met = res_met.json()
                if "cpu" in met and "ram" in met:
                    metric_passed = True
                    metric_details = f"CPU: {met['cpu']['utilization_pct']}%, RAM available: {met['ram']['available_bytes'] // (1024*1024)} MB"
                else:
                    metric_details = f"Invalid schema: {met}"
            else:
                metric_details = f"HTTP {res_met.status_code}"
        except Exception as e:
            metric_details = str(e)
        self.log_result("Metrics", "Performance Metrics Collection", metric_passed, metric_details)

    def validate_security_hardening(self):
        print("\n--- Validating Security Hardening ---")
        passed = False
        details = ""
        path = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager\.session_api_key")
        if not os.path.exists(path):
            local_path = ".session_api_key"
            if os.path.exists(local_path):
                path = local_path
                
        if os.path.exists(path):
            if sys.platform == "win32":
                try:
                    import win32api
                    import win32con
                    import win32security
                    import ntsecuritycon as con
                    
                    sd = win32security.GetNamedSecurityInfo(
                        path,
                        win32security.SE_FILE_OBJECT,
                        win32security.DACL_SECURITY_INFORMATION
                    )
                    control, revision = sd.GetSecurityDescriptorControl()
                    is_protected = bool(control & win32security.SE_DACL_PROTECTED)
                    
                    dacl = sd.GetSecurityDescriptorDacl()
                    ace_count = dacl.GetAceCount() if dacl else 0
                    
                    system_sid = win32security.ConvertStringSidToSid("S-1-5-18")
                    admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
                    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
                    user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
                    
                    allowed_sids = {
                        win32security.ConvertSidToStringSid(system_sid),
                        win32security.ConvertSidToStringSid(admins_sid),
                        win32security.ConvertSidToStringSid(user_sid)
                    }
                    
                    unexpected_sids = []
                    for i in range(ace_count):
                        ace = dacl.GetAce(i)
                        sid_str = win32security.ConvertSidToStringSid(ace[2])
                        if sid_str not in allowed_sids:
                            unexpected_sids.append(sid_str)
                            
                    if is_protected and ace_count > 0 and len(unexpected_sids) == 0:
                        passed = True
                        details = f"Native Windows ACL verified: DACL is protected, SIDs allowed: {list(allowed_sids)}"
                    else:
                        details = f"Fails verification: protected={is_protected}, unexpected_sids={unexpected_sids}, ace_count={ace_count}"
                except Exception as e:
                    details = f"Failed checking security info: {e}"
            else:
                try:
                    mode = os.stat(path).st_mode
                    passed = (mode & 0o777) == 0o600
                    details = f"Unix file mode: {oct(mode & 0o777)}"
                except Exception as e:
                    details = f"Failed checking mode: {e}"
        else:
            details = "Session API key file not found"
            
        self.log_result("Security", "Windows Native API Key Protection", passed, details)

    def validate_diagnostics_and_bundle(self):
        # Support Bundle Generation
        passed = False
        details = ""
        output_zip = "test_support_bundle.zip"
        if os.path.exists(output_zip):
            try:
                os.remove(output_zip)
            except Exception:
                pass
                
        res = self.run_command([sys.executable, "-m", "src.cli.main", "support-bundle", "--output", output_zip])
        if res.returncode == 0 and os.path.exists(output_zip):
            try:
                with zipfile.ZipFile(output_zip, "r") as z:
                    file_list = z.namelist()
                    has_db = "arm.db" in file_list
                    has_meta = "metadata.json" in file_list
                    if has_db and has_meta:
                        passed = True
                        details = f"Generated ZIP contains: {file_list}"
                    else:
                        details = f"ZIP missing critical files: {file_list}"
            except Exception as e:
                details = f"Failed to parse ZIP: {e}"
        else:
            details = f"CLI export failed. exit code: {res.returncode}, stderr: {res.stderr.strip()}"
            
        if os.path.exists(output_zip):
            try:
                os.remove(output_zip)
            except Exception:
                pass
                
        self.log_result("Support Bundle", "Archive Compiling & Download", passed, details)

    def validate_advanced_acceptance_scenarios(self):
        print("\n--- Validating Advanced Acceptance Scenarios ---")
        import socket
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        
        # Backup original mcp config row in database to restore it after the test
        original_mcp = None
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM services WHERE id = ?;", ("mcp",))
                row = cursor.fetchone()
                if row:
                    original_mcp = dict(row)
                conn.close()
            except Exception as e:
                print(f"Failed to backup original mcp row: {e}")
                
        # 1. Update mcp service in db to run dummy python code
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    UPDATE services 
                    SET binary_path = ?, args = ?, status = 'STOPPED', pid = NULL 
                    WHERE id = ?;
                """, (sys.executable, json.dumps(["-c", "import time; time.sleep(30)"]), "mcp"))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Failed to prepare mcp row for lifecycle test: {e}")

        # --- A. REST API Service Lifecycle (Start, Stop, Restart) ---
        lifecycle_ok = False
        start_pid = None
        try:
            # Start via REST API
            res = self.api_post("/api/v1/services/mcp/start", timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                start_pid = data.get("pid")
                if start_pid and data.get("status") == "RUNNING":
                    # Restart via REST API
                    res_restart = self.api_post("/api/v1/services/mcp/restart", timeout=5.0)
                    if res_restart.status_code == 200:
                        restart_data = res_restart.json()
                        restart_pid = restart_data.get("pid")
                        if restart_pid and restart_pid != start_pid and restart_data.get("status") == "RUNNING":
                            # Stop via REST API
                            res_stop = self.api_post("/api/v1/services/mcp/stop", timeout=5.0)
                            if res_stop.status_code == 200:
                                stop_data = res_stop.json()
                                if stop_data.get("status") == "STOPPED":
                                    lifecycle_ok = True
        except Exception as e:
            print(f"Error during REST API lifecycle test: {e}")
            
        self.log_result("Acceptance Tests", "REST API Service Lifecycle", lifecycle_ok, f"Start PID: {start_pid}")

        # --- B. CLI Service Lifecycle (Start, Stop) ---
        cli_lifecycle_ok = False
        try:
            # Start via CLI
            res_start = self.run_command([sys.executable, "-m", "src.cli.main", "start", "mcp"])
            if res_start.returncode == 0:
                # Stop via CLI
                res_stop = self.run_command([sys.executable, "-m", "src.cli.main", "stop", "mcp"])
                if res_stop.returncode == 0:
                    cli_lifecycle_ok = True
        except Exception as e:
            print(f"Error during CLI lifecycle test: {e}")
            
        self.log_result("Acceptance Tests", "CLI Service Lifecycle", cli_lifecycle_ok)

        # --- C. Policy Enforcement (Prevent LiteLLM stop with active requests) ---
        policy_ok = False
        policy_reason = ""
        try:
            # 1. Update config 'litellm_active_requests' in DB
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('litellm_active_requests', '3');")
            conn.commit()
            conn.close()
            
            # 2. Try to stop litellm service
            res = self.api_post("/api/v1/services/litellm/stop", timeout=5.0)
            if res.status_code in [400, 500]:
                detail = res.json().get("detail", "")
                if "active request sessions" in detail:
                    policy_ok = True
                    policy_reason = detail
            else:
                policy_reason = f"Response code was {res.status_code}"
                
            # Reset active requests config
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('litellm_active_requests', '0');")
            conn.commit()
            conn.close()
        except Exception as e:
            policy_reason = str(e)
            
        self.log_result("Acceptance Tests", "Policy Enforcement (LiteLLM Active Requests)", policy_ok, policy_reason)

        # --- D. Workflow Rollback (Port Conflict) ---
        rollback_ok = False
        rollback_reason = ""
        conflict_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conflict_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            conflict_sock.bind(("127.0.0.1", 8000))
            conflict_sock.listen(1)
            
            # Try to start litellm service
            res = self.api_post("/api/v1/services/litellm/start", timeout=5.0)
            if res.status_code in [400, 500]:
                detail = res.json().get("detail", "")
                if "Port 8000 is already in use" in detail or "failed" in detail.lower():
                    # Verify status rolled back to STOPPED
                    res_status = self.api_get("/api/v1/services/litellm")
                    if res_status.status_code == 200 and res_status.json().get("status") in ["STOPPED", "ERROR"]:
                        rollback_ok = True
                        rollback_reason = f"Status rolled back cleanly. Detail: {detail}"
                else:
                    rollback_reason = f"Detail did not match key phrases: {detail}"
            else:
                rollback_reason = f"Start command succeeded unexpectedly. Status code: {res.status_code}"
        except Exception as e:
            rollback_reason = str(e)
        finally:
            conflict_sock.close()
            
        self.log_result("Acceptance Tests", "Workflow Rollback on Port Conflict", rollback_ok, rollback_reason)

        # --- E. Health Engine & Auto-Restart Policy ---
        auto_restart_ok = False
        auto_restart_reason = ""
        try:
            # 1. Set auto_restart limit to 5 and ensure it's enabled with quick delay for validation
            conn = sqlite3.connect(db_path)
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_restart_enabled', 'true');")
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_restart_limit', '5');")
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_restart_base_delay', '0.1');")
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_restart_jitter_pct', '0.0');")
            conn.commit()
            conn.close()
            
            # 2. Start the service first using REST API to make sure stopping_intent is reset to False!
            self.api_post("/api/v1/services/mcp/start", timeout=5.0)
            
            # 3. Set status of mcp to RUNNING in database but pid to a dead pid (e.g. 999999)
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE services SET status = 'RUNNING', pid = 999999 WHERE id = 'mcp';")
            conn.commit()
            conn.close()
            
            # 4. Call services list with refresh=True
            res = self.api_get("/api/v1/services?refresh=true", timeout=5.0)
            if res.status_code == 200:
                time.sleep(5.0)
                # Check status of mcp now
                res_check = self.api_get("/api/v1/services/mcp")
                if res_check.status_code == 200:
                    data = res_check.json()
                    new_pid = data.get("pid")
                    if data.get("status") == "RUNNING" and new_pid and new_pid != 999999:
                        auto_restart_ok = True
                        auto_restart_reason = f"Successfully auto-restarted dead process. New PID: {new_pid}"
                        # Stop the service to cleanup
                        self.api_post("/api/v1/services/mcp/stop", timeout=5.0)
                    else:
                        auto_restart_reason = f"Status: {data.get('status')}, PID: {new_pid}"
            else:
                auto_restart_reason = f"Refresh failed: {res.status_code}"
        except Exception as e:
            auto_restart_reason = str(e)
            
        self.log_result("Acceptance Tests", "Health Engine Auto-Restart", auto_restart_ok, auto_restart_reason)

        # Restore original mcp row in database
        if original_mcp and os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("""
                    UPDATE services 
                    SET binary_path = ?, args = ?, status = ?, pid = ? 
                    WHERE id = ?;
                """, (original_mcp["binary_path"], original_mcp["args"], original_mcp["status"], original_mcp["pid"], "mcp"))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Failed to restore original mcp row: {e}")

    def generate_validation_report(self):
        print(f"\n--- Saving Validation Report to: {REPORT_PATH} ---")
        total_tests = 0
        passed_tests = 0
        
        report = f"""# AI Control Plane Version 1.0 System Validation Report

**Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: {"SUCCESS" if all(all(t["status"] == "PASS" for t in list) for list in self.results.values()) else "FAILED"}

## Summary table

| Category | Test Case Name | Status | Details |
|---|---|---|---|
"""
        for cat, list in self.results.items():
            for t in list:
                total_tests += 1
                if t["status"] == "PASS":
                    passed_tests += 1
                report += f"| {cat} | {t['name']} | **{t['status']}** | {t['details']} |\n"
                
        pass_pct = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report = report.replace("**SUCCESS**", f"**SUCCESS** ({passed_tests}/{total_tests} passed - {pass_pct:.1f}%)")
        
        try:
            os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
            with open(REPORT_PATH, "w", encoding="utf-8") as f:
                f.write(report)
            print("Validation report successfully saved.")
        except Exception as e:
            print(f"Failed to write report: {e}")

    def execute_all(self):
        self.validate_installation_actions()
        self.start_api_server()
        
        try:
            self.validate_database_subsystem()
            self.validate_security_hardening()
            self.validate_windows_services()
            self.validate_rest_api_and_cli()
            self.validate_dashboard()
            self.validate_plugins_and_policies()
            self.validate_scheduler_and_workflows()
            self.validate_logs_and_metrics()
            self.validate_diagnostics_and_bundle()
            self.validate_advanced_acceptance_scenarios()
        finally:
            self.stop_api_server()
            
        self.generate_validation_report()

if __name__ == "__main__":
    is_dev = "--prod" not in sys.argv
    validator = SystemValidator(is_dev=is_dev)
    validator.execute_all()
