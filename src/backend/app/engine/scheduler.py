import time
import threading
import logging
from typing import Any

logger = logging.getLogger("engine.scheduler")

class Scheduler:
    def __init__(self, kernel: Any):
        self.kernel = kernel
        self._stop_event = threading.Event()
        self._thread = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="arm-scheduler")
        self._thread.start()
        logger.info("Background scheduler thread started.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
            logger.info("Background scheduler thread stopped.")

    def _run_loop(self) -> None:
        last_health_check = 0.0
        last_metrics_check = 0.0
        last_inventory_check = time.time()  # skip immediate scan at startup

        # Intervals in seconds
        health_interval = 10.0
        metrics_interval = 10.0
        inventory_interval = 60.0

        while not self._stop_event.is_set():
            now = time.time()

            # 1. Health check for running services
            if now - last_health_check >= health_interval:
                try:
                    for service in self.kernel.service_registry.list_services():
                        plugin = self.kernel.service_registry.get_plugin(service.type)
                        if plugin:
                            check_result = plugin.get_raw_checks(service)
                            self.kernel.health_engine.evaluate_and_update(service, check_result)
                except Exception as e:
                    logger.error(f"Scheduler health check loop error: {e}")
                last_health_check = now

            # 2. Performance metrics collection
            if now - last_metrics_check >= metrics_interval:
                try:
                    if self.kernel.metrics_engine:
                        self.kernel.metrics_engine.collect_metrics()
                except Exception as e:
                    logger.error(f"Scheduler metrics collection loop error: {e}")
                last_metrics_check = now

            # 3. Inventory sync/refresh
            if now - last_inventory_check >= inventory_interval:
                try:
                    logger.info("Scheduler running periodic inventory scan...")
                    self.kernel.inventory_engine.discover_and_populate()
                except Exception as e:
                    logger.error(f"Scheduler inventory scan loop error: {e}")
                last_inventory_check = now

            # Sleep in small steps to remain responsive to stop events
            time.sleep(1.0)
