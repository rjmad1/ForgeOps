import os
import time
import pytest
import sys
from src.backend.app.infrastructure.process_manager import (
    start_process,
    is_process_running,
    stop_process,
    get_process_metrics
)

def test_start_and_stop_process():
    # On Windows, we use ping.exe as a dummy long-running command (pinging localhost)
    if os.name == 'nt':
        binary = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "ping.exe")
        args = ["127.0.0.1", "-n", "10"]
    else:
        # Fallback for non-Windows (e.g. if run on CI)
        binary = "/bin/sleep"
        args = ["10"]

    assert os.path.exists(binary), f"Test helper binary not found: {binary}"

    # Start the process
    pid = start_process(binary, args)
    assert pid > 0
    assert is_process_running(pid) is True

    # Get metrics
    metrics = get_process_metrics(pid)
    assert "cpu_percent" in metrics
    assert "memory_rss_bytes" in metrics
    assert metrics["memory_rss_bytes"] > 0

    # Stop the process
    success = stop_process(pid)
    assert success is True
    
    # Wait a moment for OS cleanup
    time.sleep(0.5)
    assert is_process_running(pid) is False

def test_invalid_binary():
    with pytest.raises(FileNotFoundError):
        start_process("C:\\nonexistent_file_path_123.exe", [])

def test_stop_nonexistent_pid():
    # Large PID that is highly unlikely to exist
    assert stop_process(999999) is True
    assert is_process_running(999999) is False
