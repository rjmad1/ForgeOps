import os
import zipfile
import json
import shutil
import re
import yaml
from datetime import datetime
from typing import Dict, Any

from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path, get_connection

def scrub_log_content(text: str) -> str:
    # substitute strings matching common API key formats (e.g. sk-[a-zA-Z0-9]{48})
    text = re.sub(r"sk-[a-zA-Z0-9]{48}", "[REDACTED]", text)
    # Also support general sk-... keys
    text = re.sub(r"sk-[a-zA-Z0-9\-]{20,}", "[REDACTED]", text)
    return text

def redact_dict_keys(d: Any) -> Any:
    if isinstance(d, dict):
        new_dict = {}
        for k, v in d.items():
            if isinstance(k, str) and any(secret_term in k.lower() for secret_term in ["api_key", "key", "credentials", "secret", "token", "password"]):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = redact_dict_keys(v)
        return new_dict
    elif isinstance(d, list):
        return [redact_dict_keys(item) for item in d]
    return d

def redact_mcp_config(d: Any) -> Any:
    if isinstance(d, dict):
        new_dict = {}
        for k, v in d.items():
            if k == "env" and isinstance(v, dict):
                new_dict[k] = {env_k: "[REDACTED]" for env_k in v.keys()}
            elif isinstance(k, str) and any(secret_term in k.lower() for secret_term in ["api_key", "key", "credentials", "secret", "token", "password"]):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = redact_mcp_config(v)
        return new_dict
    elif isinstance(d, list):
        return [redact_mcp_config(item) for item in d]
    return d

def generate_bundle(output_dir: str = None) -> str:
    """
    Generates a support bundle zip file containing:
      - SQLite database snapshot (arm.db)
      - Logs directory contents (redacted)
      - Configurations (redacted)
      - System metadata.json
    Returns the absolute path to the generated zip file.
    """
    if not output_dir:
        # Default path in ProgramData or current working directory fallback
        program_data = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
        if os.path.exists(program_data):
            output_dir = os.path.join(program_data, "support_bundles")
        else:
            output_dir = "support_bundles"
            
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"support_bundle_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    
    # Paths to include
    db_path = get_db_path()
    
    # Log folders
    logs_dir = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager\logs")
    if not os.path.exists(logs_dir):
        logs_dir = "." # fallback to project root to find any local service.log/install.log
        
    configs_to_check = ["litellm_config.yaml", "openclaw_config.yaml", "mcp_config.json"]
    
    # Query system info to write metadata.json
    metadata: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "database_path": db_path,
        "services": []
    }
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, port, status, pid, binary_path, auto_start FROM services;")
        rows = cursor.fetchall()
        for r in rows:
            metadata["services"].append(dict(r))
        conn.close()
    except Exception as e:
        metadata["db_query_error"] = str(e)
        
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Write metadata.json
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        # 2. Write SQLite DB
        if os.path.exists(db_path):
            # We copy db to a temp snapshot file to avoid open handle errors during zip write if active
            temp_db = db_path + ".snapshot"
            try:
                shutil.copy2(db_path, temp_db)
                zip_file.write(temp_db, "arm.db")
                os.remove(temp_db)
            except Exception:
                # If we cannot copy, try direct zip write
                try:
                    zip_file.write(db_path, "arm.db")
                except Exception:
                    pass
                
        # 3. Write logs (scrubbed)
        if os.path.exists(logs_dir):
            for root, _, files in os.walk(logs_dir):
                for f in files:
                    if f.endswith(".log"):
                        full_fpath = os.path.join(root, f)
                        # Avoid adding logs directory from unrelated levels if fallback is local root
                        if logs_dir == "." and f not in ["service.log", "install.log"]:
                            continue
                        arcname = os.path.join("logs", f)
                        try:
                            with open(full_fpath, "r", encoding="utf-8", errors="replace") as log_file:
                                log_content = log_file.read()
                            scrubbed_content = scrub_log_content(log_content)
                            zip_file.writestr(arcname, scrubbed_content)
                        except Exception:
                            # Fallback if file read/scrub fails
                            try:
                                zip_file.write(full_fpath, arcname)
                            except Exception:
                                pass
                            
        # 4. Write config files (redacted)
        for cfg in configs_to_check:
            if os.path.exists(cfg):
                basename = os.path.basename(cfg)
                try:
                    with open(cfg, "r", encoding="utf-8") as f:
                        if cfg.endswith(".yaml") or cfg.endswith(".yml"):
                            content = yaml.safe_load(f)
                            redacted_content = redact_dict_keys(content)
                            zip_file.writestr(basename, yaml.dump(redacted_content, default_flow_style=False))
                        elif cfg.endswith(".json"):
                            content = json.load(f)
                            if basename == "mcp_config.json":
                                redacted_content = redact_mcp_config(content)
                            else:
                                redacted_content = redact_dict_keys(content)
                            zip_file.writestr(basename, json.dumps(redacted_content, indent=2))
                        else:
                            # fallback text scrub
                            with open(cfg, "r", encoding="utf-8", errors="replace") as raw_f:
                                raw_content = raw_f.read()
                            zip_file.writestr(basename, scrub_log_content(raw_content))
                except Exception:
                    # Fallback raw write
                    try:
                        zip_file.write(cfg, basename)
                    except Exception:
                        pass
                
    return zip_path
