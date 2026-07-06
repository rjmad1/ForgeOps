import os
import subprocess
import psutil
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("process_manager")

def sanitize_command(cmd: List[str]) -> List[str]:
    sanitized = []
    redact_next = False
    for token in cmd:
        if redact_next:
            sanitized.append("[REDACTED]")
            redact_next = False
            continue
        # Catch common key arguments
        if token in ["--api-key", "-k", "--key", "--password", "-p", "--token", "--api_key"]:
            redact_next = True
        elif "=" in token and any(k in token.lower() for k in ["api_key", "password", "secret", "token"]):
            parts = token.split("=", 1)
            token = f"{parts[0]}=[REDACTED]"
        sanitized.append(token)
    return sanitized

def start_process(
    binary_path: str, 
    args: List[str], 
    env: Optional[Dict[str, str]] = None, 
    log_file_path: Optional[str] = None
) -> int:
    """Spawns a subprocess on Windows and redirects stdout/stderr to a log file.
    
    Args:
        binary_path: Absolute path to the executable.
        args: List of command-line arguments.
        env: Environment variables to inject.
        log_file_path: Path to log file on disk. Auto-generated if not provided.
    """
    import shutil
    if not os.path.exists(binary_path) and not shutil.which(binary_path):
        raise FileNotFoundError(f"Binary path not found: {binary_path}")
        
    cmd = [binary_path] + args
    
    # Merge existing env with injected env
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
        
    # CREATE_NEW_PROCESS_GROUP is a Windows-specific flag to allow sending break events
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    
    # Auto-generate log path if not provided
    if not log_file_path:
        from src.backend.app.infrastructure.persistence.sqlite_db import get_db_path
        db_path = get_db_path()
        base_dir = os.path.dirname(db_path) or "."
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        bin_name = os.path.basename(binary_path).replace(".exe", "").lower()
        log_file_path = os.path.join(logs_dir, f"{bin_name}.log")
    else:
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
    logger.info(f"Starting subprocess: {sanitize_command(cmd)} (Logs: {log_file_path})")
    
    # Open file handle for redirecting output
    log_file = open(log_file_path, "a", encoding="utf-8", errors="replace")
    
    proc = subprocess.Popen(
        cmd,
        env=process_env,
        stdout=log_file,
        stderr=log_file,
        creationflags=creationflags,
        text=True
    )
    
    # Close duplicate handle in parent process
    log_file.close()
    
    return proc.pid

def is_process_running(pid: int) -> bool:
    """Checks if a process with the given PID is currently active."""
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False

def stop_process(pid: int, timeout: float = 3.0) -> bool:
    """Terminates a process and all of its descendants recursively.
    
    Returns True if successfully terminated or already dead.
    """
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return True
        
    try:
        # Get all child processes recursively
        children = parent.children(recursive=True)
        
        # Terminate children first, then parent
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        parent.terminate()
        
        # Wait for processes to exit
        gone, alive = psutil.wait_procs(children + [parent], timeout=timeout)
        
        # Force kill any survivors
        for survivor in alive:
            try:
                logger.warning(f"Process {survivor.pid} failed to terminate. Killing forcefully.")
                survivor.kill()
            except psutil.NoSuchProcess:
                pass
                
        return True
    except Exception as e:
        logger.error(f"Error terminating process tree for PID {pid}: {e}")
        return False

def get_process_metrics(pid: int) -> Dict[str, Any]:
    """Retrieves CPU and RAM utilization for a given PID and all its children.
    
    Returns:
        Dict containing cpu_percent and memory_rss_bytes.
    """
    metrics = {
        "cpu_percent": 0.0,
        "memory_rss_bytes": 0
    }
    
    try:
        parent = psutil.Process(pid)
        processes = [parent] + parent.children(recursive=True)
        
        total_cpu = 0.0
        total_ram = 0
        
        for p in processes:
            try:
                # cpu_percent(interval=None) returns immediate value since last call
                total_cpu += p.cpu_percent(interval=None)
                total_ram += p.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        metrics["cpu_percent"] = total_cpu
        metrics["memory_rss_bytes"] = total_ram
    except psutil.NoSuchProcess:
        pass
        
    return metrics
