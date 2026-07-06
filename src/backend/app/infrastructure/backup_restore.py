import os
import zipfile
import shutil
from datetime import datetime
from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path

def backup_system_config(output_zip: str = None) -> str:
    """Creates a timestamped zip backup containing database and configuration files."""
    program_data = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager")
    if not output_zip:
        backups_dir = os.path.join(program_data, "backups") if os.path.exists(program_data) else "backups"
        os.makedirs(backups_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_zip = os.path.join(backups_dir, f"arm-backup-{timestamp}.zip")
    else:
        parent = os.path.dirname(output_zip)
        if parent:
            os.makedirs(parent, exist_ok=True)

    db_path = get_db_path()
    configs = ["litellm_config.yaml", "openclaw_config.yaml", "mcp_config.json"]

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Write DB
        if os.path.exists(db_path):
            temp_db = db_path + ".bkp_snap"
            try:
                shutil.copy2(db_path, temp_db)
                zip_file.write(temp_db, "arm.db")
                os.remove(temp_db)
            except Exception:
                try:
                    zip_file.write(db_path, "arm.db")
                except Exception:
                    pass

        # Write configs
        for cfg in configs:
            if os.path.exists(cfg):
                zip_file.write(cfg, os.path.basename(cfg))

    return output_zip

def restore_system_config(zip_path: str) -> bool:
    """Restores database and configuration files from a zip backup."""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Backup file not found: {zip_path}")

    # Extract to a temp directory
    temp_dir = zip_path + "_extracted"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp_dir)

        db_path = get_db_path()
        
        # Restore DB
        extracted_db = os.path.join(temp_dir, "arm.db")
        if os.path.exists(extracted_db):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            shutil.copy2(extracted_db, db_path)

        # Restore configs
        configs = ["litellm_config.yaml", "openclaw_config.yaml", "mcp_config.json"]
        for cfg in configs:
            extracted_cfg = os.path.join(temp_dir, cfg)
            if os.path.exists(extracted_cfg):
                shutil.copy2(extracted_cfg, cfg)

        return True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
