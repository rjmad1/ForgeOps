import sqlite3
import logging
from typing import Any
from src.backend.app.infrastructure.persistence.sqlite_db import get_connection

logger = logging.getLogger("engine.metrics")

class MetricsEngine:
    def __init__(self, service_registry: Any, history_repo: Any):
        self.service_registry = service_registry
        self.history_repo = history_repo

    def collect_metrics(self) -> None:
        """Collects resource consumption (CPU/RAM/GPU) from all active subprocesses and persists to SQLite."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            for service in self.service_registry.list_services():
                if service.status == "RUNNING":
                    plugin = self.service_registry.get_plugin(service.type)
                    if plugin:
                        try:
                            metrics = plugin.get_metrics(service)
                            
                            # vram/gpu might be None from standard process metric collections
                            vram = getattr(metrics, 'vram_used_bytes', None)
                            gpu = getattr(metrics, 'gpu_utilization_pct', None)
                            
                            cursor.execute("""
                            INSERT INTO performance_metrics (
                                service_id, cpu_utilization_pct, ram_used_bytes, vram_used_bytes, gpu_utilization_pct
                            ) VALUES (?, ?, ?, ?, ?);
                            """, (
                                service.id,
                                metrics.cpu_utilization_pct,
                                metrics.ram_used_bytes,
                                vram,
                                gpu
                            ))
                        except Exception as pe:
                            logger.error(f"Error querying plugin metrics for {service.id}: {pe}")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to run metrics collection loop: {e}")
        finally:
            conn.close()
