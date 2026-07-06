from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class ModelProxyConfig:
    name: str
    runtime: str          # e.g., 'ollama', 'litellm'
    source_model: str     # e.g., 'llama3:latest'
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemConfiguration:
    global_api_port: int = 8088
    enable_cors: bool = True
    models: List[ModelProxyConfig] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validates configuration parameters."""
        if self.global_api_port <= 0 or self.global_api_port > 65535:
            return False
        for m in self.models:
            if not m.name or not m.runtime or not m.source_model:
                return False
        return True
