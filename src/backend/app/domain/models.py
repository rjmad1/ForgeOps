from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class ServiceStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    CONFIGURING = "CONFIGURING"
    UPDATING = "UPDATING"

@dataclass
class Service:
    id: str
    name: str
    type: str  # 'ollama', 'litellm', 'openclaw', 'mcp', etc.
    port: Optional[int]
    status: ServiceStatus
    pid: Optional[int] = None
    binary_path: Optional[str] = None
    args: List[str] = field(default_factory=list)
    config_path: Optional[str] = None
    auto_start: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CapabilityType(str, Enum):
    MODEL = "model"
    TOOL = "tool"
    API_GATEWAY = "api_gateway"
    AGENT_RUNNER = "agent_runner"

@dataclass
class Capability:
    id: str
    name: str
    type: CapabilityType
    provider: str  # 'ollama', 'litellm', 'openclaw', 'mcp'
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_discovered: Optional[datetime] = None

@dataclass
class ServiceMetrics:
    cpu_utilization_pct: float
    ram_used_bytes: int
    vram_used_bytes: Optional[int] = None
    gpu_utilization_pct: Optional[float] = None
    timestamp: Optional[datetime] = None

@dataclass
class ServiceCheckResult:
    pid_running: bool
    port_responsive: bool
    api_responsive: bool
    raw_details: Dict[str, Any] = field(default_factory=field)
