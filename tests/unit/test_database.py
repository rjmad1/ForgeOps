import os
import sqlite3
import pytest
from datetime import datetime
from src.backend.app.infrastructure.persistence.sqlite_db import get_connection, init_db, get_db_path
from src.backend.app.infrastructure.persistence.sqlite_repositories import (
    SqliteServiceRepository,
    SqliteCapabilityRepository,
    SqliteSystemConfigRepository
)
from src.backend.app.domain.models import Service, Capability, ServiceStatus, CapabilityType

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    # Route DB path to temp folder for testing
    test_db = os.path.join(tmp_path, "test_arm.db")
    monkeypatch.setenv("ARM_DB_PATH", test_db)
    init_db()
    yield
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except OSError:
            pass

def test_db_tables_exist():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query sqlite_master to verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    
    assert "services" in tables
    assert "models" in tables
    assert "performance_metrics" in tables
    assert "system_config" in tables
    conn.close()

def test_foreign_key_enforcement():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Try inserting into performance_metrics with non-existent service_id
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
        INSERT INTO performance_metrics (service_id, request_path, response_time_ms)
        VALUES ('non-existent-service', '/api/test', 150);
        """)
        conn.commit()
    conn.close()

def test_service_repository():
    repo = SqliteServiceRepository()
    
    # Test saving new service
    service = Service(
        id="test-ollama",
        name="Test Ollama Service",
        type="ollama",
        port=11434,
        status=ServiceStatus.STOPPED,
        binary_path="C:\\path\\to\\ollama.exe",
        args=["serve"],
        config_path=None,
        auto_start=True
    )
    repo.save(service)
    
    # Test retrieve
    retrieved = repo.get_by_id("test-ollama")
    assert retrieved is not None
    assert retrieved.name == "Test Ollama Service"
    assert retrieved.status == ServiceStatus.STOPPED
    assert retrieved.args == ["serve"]
    assert retrieved.auto_start is True
    
    # Test update
    retrieved.status = ServiceStatus.RUNNING
    retrieved.pid = 9999
    repo.save(retrieved)
    
    updated = repo.get_by_id("test-ollama")
    assert updated.status == ServiceStatus.RUNNING
    assert updated.pid == 9999
    
    # Test get_all
    all_services = repo.get_all()
    assert len(all_services) == 1
    assert all_services[0].id == "test-ollama"
    
    # Test delete
    repo.delete("test-ollama")
    assert repo.get_by_id("test-ollama") is None

def test_capability_repository():
    repo = SqliteCapabilityRepository()
    
    capability = Capability(
        id="ollama/llama3",
        name="llama3",
        type=CapabilityType.MODEL,
        provider="ollama",
        metadata={
            "size_bytes": 4661224679,
            "family": "llama",
            "parameter_size": "8B",
            "context_length": 8192
        }
    )
    repo.save(capability)
    
    retrieved = repo.get_by_id("ollama/llama3")
    assert retrieved is not None
    assert retrieved.name == "llama3"
    assert retrieved.type == CapabilityType.MODEL
    assert retrieved.provider == "ollama"
    assert retrieved.metadata["size_bytes"] == 4661224679
    assert retrieved.metadata["family"] == "llama"
    assert retrieved.metadata["parameter_size"] == "8B"
    assert retrieved.metadata["context_length"] == 8192
    
    # Test list / get by provider
    assert len(repo.get_all()) == 1
    assert len(repo.get_by_provider("ollama")) == 1
    assert len(repo.get_by_provider("litellm")) == 0
    
    # Clear by provider
    repo.clear_by_provider("ollama")
    assert len(repo.get_by_provider("ollama")) == 0

def test_system_config_repository():
    repo = SqliteSystemConfigRepository()
    
    repo.set("test_key", "test_value")
    assert repo.get("test_key") == "test_value"
    assert repo.get("nonexistent_key") is None

def test_wal_mode_enabled():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    assert mode.lower() == "wal"
    conn.close()

def test_database_write_concurrency():
    import threading
    import time
    
    repo = SqliteSystemConfigRepository()
    errors = []
    
    def worker(worker_id: int):
        try:
            for i in range(15):
                repo.set(f"concurrent_key_{worker_id}_{i}", f"val_{i}")
                time.sleep(0.005)
        except Exception as e:
            errors.append(e)
            
    threads = []
    for t_id in range(6):
        t = threading.Thread(target=worker, args=(t_id,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    assert len(errors) == 0
