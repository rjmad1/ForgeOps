import os
import shutil
import logging
import subprocess
import socket
import sys
import json
from typing import Optional, Dict, Any, List
from src.backend.app.domain.models import Service, ServiceStatus, ServiceCheckResult
from src.backend.app.domain.registry import ServiceRegistry, CapabilityRegistry
from src.backend.app.engine.health import HealthEngine

logger = logging.getLogger("engine.inventory")

def run_cmd(args: List[str]) -> Optional[str]:
    try:
        # Use shell=True on Windows to support PATH search for batch/cmd commands without absolute path
        res = subprocess.run(args, capture_output=True, text=True, timeout=1.5, shell=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None

class InventoryEngine:
    def __init__(
        self,
        service_registry: ServiceRegistry,
        capability_registry: CapabilityRegistry,
        health_engine: Optional[HealthEngine] = None,
        inventory_repo: Optional[Any] = None
    ):
        self.service_registry = service_registry
        self.capability_registry = capability_registry
        self.health_engine = health_engine
        self.inventory_repo = inventory_repo
        
    def discover_and_populate(self) -> None:
        """Discovers the machine's state (binaries/ports/runtimes) and populates repositories."""
        logger.info("Starting machine state inventory discovery...")
        
        # 1. Discover broader machine runtimes & tools
        if self.inventory_repo:
            try:
                self._discover_host_environment()
            except Exception as e:
                logger.error(f"Failed to scan host environment: {e}")

        # 2. Check and register each plugin service if it exists/is supported on the machine
        for plugin in self.service_registry.list_plugins():
            identifier = plugin.get_identifier()
            service_id = identifier
            
            service = self.service_registry.get_service(service_id)
            is_supported = self._check_plugin_supported(identifier)
            
            if is_supported:
                if not service:
                    service = self._create_default_service(identifier)
                    logger.info(f"Discovered and created default service configuration for: {identifier}")
                
                check_result = plugin.get_raw_checks(service)
                if self.health_engine:
                    self.health_engine.evaluate_and_update(service, check_result)
                else:
                    service.status = ServiceStatus.RUNNING if check_result.pid_running else ServiceStatus.STOPPED
                
                self.service_registry.register_service(service)
                
        # Trigger capability discovery to sync model list
        self.capability_registry.refresh_capabilities(self.service_registry)
        logger.info("Inventory discovery completed.")

    def _discover_host_environment(self) -> None:
        """Probes the host OS for installed runtimes, tools, hardware capabilities, and ports."""
        # 1. Python Check
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.inventory_repo.save("python", "runtime", json.dumps({
            "version": py_version,
            "executable": sys.executable
        }))

        # 2. Node.js Check
        node_raw = run_cmd(["node", "--version"])
        self.inventory_repo.save("node", "runtime", json.dumps({
            "installed": node_raw is not None,
            "version": node_raw if node_raw else None
        }))

        # 3. Git Check
        git_raw = run_cmd(["git", "--version"])
        self.inventory_repo.save("git", "tool", json.dumps({
            "installed": git_raw is not None,
            "version": git_raw if git_raw else None
        }))

        # 4. Docker Check
        docker_raw = run_cmd(["docker", "--version"])
        self.inventory_repo.save("docker", "tool", json.dumps({
            "installed": docker_raw is not None,
            "version": docker_raw if docker_raw else None
        }))

        # 5. CUDA Check
        cuda_raw = run_cmd(["nvcc", "--version"])
        cuda_path = os.environ.get("CUDA_PATH", "")
        has_cuda = cuda_raw is not None or bool(cuda_path)
        self.inventory_repo.save("cuda", "hardware", json.dumps({
            "available": has_cuda,
            "version": cuda_raw.split("release")[-1].strip() if cuda_raw else None,
            "cuda_path": cuda_path if cuda_path else None
        }))

        # 6. GPU Check
        gpu_raw = run_cmd(["nvidia-smi", "--query-gpu=gpu_name,driver_version,memory.total", "--format=csv,noheader,nounits"])
        gpu_info = {}
        if gpu_raw:
            parts = gpu_raw.split(",")
            if len(parts) >= 3:
                gpu_info = {
                    "name": parts[0].strip(),
                    "driver_version": parts[1].strip(),
                    "memory_total_mb": int(parts[2].strip())
                }
        self.inventory_repo.save("gpu", "hardware", json.dumps({
            "has_nvidia_gpu": bool(gpu_raw),
            "details": gpu_info
        }))

        # 7. WSL Check
        wsl_raw = run_cmd(["wsl", "--list", "--quiet"])
        self.inventory_repo.save("wsl", "runtime", json.dumps({
            "available": wsl_raw is not None,
            "distributions": wsl_raw.split() if wsl_raw else []
        }))

        # 8. Network port scanner (check key AI runtime ports)
        target_ports = [8000, 8080, 11434, 9000]
        in_use_ports = []
        for port in target_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    in_use_ports.append(port)
        self.inventory_repo.save("ports", "network", json.dumps({
            "probed_ports": target_ports,
            "in_use": in_use_ports
        }))

        # 9. Key environment variables
        env_keys = ["PATH", "APPDATA", "LOCALAPPDATA", "CUDA_PATH", "OLLAMA_HOST"]
        env_vars = {k: os.environ.get(k) for k in env_keys if k in os.environ}
        self.inventory_repo.save("env", "environment", json.dumps(env_vars))

    def _check_plugin_supported(self, identifier: str) -> bool:
        if identifier == "ollama":
            if shutil.which("ollama"):
                return True
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("ProgramFiles", "")
            if os.path.exists(os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")):
                return True
            if os.path.exists(os.path.join(program_files, "Ollama", "ollama.exe")):
                return True
            return False
            
        elif identifier == "litellm":
            return shutil.which("litellm") is not None or shutil.which("pip") is not None
            
        elif identifier == "openclaw":
            return shutil.which("openclaw") is not None or os.path.exists(os.path.expanduser("~/.openclaw"))
            
        elif identifier == "mcp":
            return True
            
        return False

    def _create_default_service(self, identifier: str) -> Service:
        if identifier == "ollama":
            return Service(
                id="ollama",
                name="Ollama Daemon",
                type="ollama",
                port=11434,
                status=ServiceStatus.STOPPED,
                binary_path=self._find_binary("ollama"),
                args=["serve"]
            )
        elif identifier == "litellm":
            return Service(
                id="litellm",
                name="LiteLLM Gateway",
                type="litellm",
                port=8000,
                status=ServiceStatus.STOPPED,
                binary_path=self._find_binary("litellm"),
                args=[]
            )
        elif identifier == "openclaw":
            return Service(
                id="openclaw",
                name="OpenClaw Supervisor",
                type="openclaw",
                port=8080,
                status=ServiceStatus.STOPPED,
                binary_path=self._find_binary("openclaw"),
                args=[]
            )
        elif identifier == "mcp":
            return Service(
                id="mcp",
                name="Model Context Protocol Hub",
                type="mcp",
                port=None,
                status=ServiceStatus.RUNNING,
                binary_path=None,
                args=[]
            )
        raise ValueError(f"Unknown plugin type: {identifier}")

    def _find_binary(self, name: str) -> Optional[str]:
        path = shutil.which(name)
        if path:
            return path
            
        if name == "ollama":
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("ProgramFiles", "")
            p1 = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
            if os.path.exists(p1):
                return p1
            p2 = os.path.join(program_files, "Ollama", "ollama.exe")
            if os.path.exists(p2):
                return p2
        return None
