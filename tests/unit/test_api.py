from fastapi.testclient import TestClient
from src.backend.app.main import app, session_api_key
import pytest
import os

@pytest.fixture
def auth_client():
    from src.backend.app.main import session_api_key
    client = TestClient(app)
    # We set X-API-Key header
    client.headers["X-API-Key"] = session_api_key
    return client

def test_unauthenticated_api_endpoints_fail():
    client = TestClient(app)
    # Endpoints starting with /api/ must fail with 401
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 401
    
    response2 = client.get("/api/v1/services")
    assert response2.status_code == 401

def test_bypassed_endpoints_pass_without_auth():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    
    response2 = client.get("/health")
    assert response2.status_code == 200
    
    response3 = client.get("/api/v1/auth/token")
    assert response3.status_code == 200
    assert "token" in response3.json()

def test_system_metrics_endpoint(auth_client):
    response = auth_client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    data = response.json()
    
    # Assert CPU structure
    assert "cpu" in data
    assert "utilization_pct" in data["cpu"]
    assert isinstance(data["cpu"]["utilization_pct"], (int, float))
    
    # Assert RAM structure
    assert "ram" in data
    assert "total_bytes" in data["ram"]
    assert "available_bytes" in data["ram"]
    assert "used_bytes" in data["ram"]
    assert "utilization_pct" in data["ram"]
    assert isinstance(data["ram"]["utilization_pct"], (int, float))
    
    # Assert GPU structure
    assert "gpu" in data
    assert "available" in data["gpu"]
    assert "name" in data["gpu"]
    assert "utilization_pct" in data["gpu"]
    assert "vram_used_bytes" in data["gpu"]
    assert "vram_total_bytes" in data["gpu"]

def test_service_logs_endpoint(auth_client):
    # Check 404 behavior for invalid service ID
    res = auth_client.get("/api/v1/services/non_existent_service/logs")
    assert res.status_code == 404

def test_litellm_loopback_only():
    from src.backend.app.plugins.litellm import LiteLLMPlugin
    from src.backend.app.domain.models import Service, ServiceStatus
    plugin = LiteLLMPlugin()
    svc = Service(
        id="litellm",
        name="LiteLLM Gateway",
        type="litellm",
        port=8000,
        status=ServiceStatus.STOPPED,
        binary_path="litellm",
        args=[],
        config_path="litellm_config.yaml"
    )
    
    # Mock process_manager.start_process to verify arguments passed to it
    import src.backend.app.infrastructure.process_manager as pm
    started_args = []
    def mock_start_process(binary, args, env=None, log_file_path=None):
        started_args.extend(args)
        return 9999
        
    original_start = pm.start_process
    pm.start_process = mock_start_process
    try:
        plugin.start_service(svc)
    finally:
        pm.start_process = original_start
        
    # Verify that "--host" and "127.0.0.1" are in the startup args (IVV-SEC-03)
    assert "--host" in started_args
    assert "127.0.0.1" in started_args

def test_log_sanitization():
    from src.backend.app.infrastructure.process_manager import sanitize_command
    raw_cmd = ["litellm", "--port", "8000", "--api-key", "sk-1234567890abcdef", "--password=mysecret", "-k", "mykey"]
    sanitized = sanitize_command(raw_cmd)
    
    # Verify sensitive data is redacted (IVV-SEC-04)
    assert "sk-1234567890abcdef" not in sanitized
    assert "mysecret" not in sanitized
    assert "mykey" not in sanitized
    assert "[REDACTED]" in sanitized

def test_support_bundle_scrubbing():
    from src.backend.app.infrastructure.support_bundle import scrub_log_content, redact_dict_keys, redact_mcp_config
    
    # Test log scrubbing
    raw_log = "Error connecting with key sk-1234567890abcdef1234567890abcdef1234567890abcdef or token sk-123456"
    scrubbed = scrub_log_content(raw_log)
    assert "sk-1234567890abcdef1234567890abcdef1234567890abcdef" not in scrubbed
    assert "[REDACTED]" in scrubbed
    
    # Test config dict key redaction
    config_dict = {
        "litellm_settings": {
            "api_key": "sk-12345",
            "db_password": "supersecret"
        },
        "general": {
            "port": 8000
        }
    }
    redacted = redact_dict_keys(config_dict)
    assert redacted["litellm_settings"]["api_key"] == "[REDACTED]"
    assert redacted["litellm_settings"]["db_password"] == "[REDACTED]"
    assert redacted["general"]["port"] == 8000

def test_backup_restore_and_benchmark_endpoints(auth_client):
    # Test backup endpoint
    res_backup = auth_client.post("/api/operations/backup")
    assert res_backup.status_code == 200
    backup_data = res_backup.json()
    assert backup_data["status"] == "success"
    assert "backup_file" in backup_data
    backup_file = backup_data["backup_file"]
    
    # Test benchmark endpoint
    res_bench = auth_client.post("/api/operations/benchmark")
    assert res_bench.status_code == 200
    bench_data = res_bench.json()
    assert bench_data["status"] == "success"
    assert "ttft_ms" in bench_data
    assert "tokens_per_second" in bench_data
    
    # Clean up backup file
    if os.path.exists(backup_file):
        try:
            os.remove(backup_file)
        except Exception:
            pass
