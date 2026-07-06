import logging
import time
import random
from dataclasses import dataclass
from typing import Dict, Any, List
from src.backend.app.domain.command import Command, StopServiceCommand, StartServiceCommand, RestartServiceCommand
from src.backend.app.domain.event import HealthChangedEvent

logger = logging.getLogger("domain.policy")

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str = ""


class Policy:
    def evaluate(self, command: Command, kernel: Any) -> PolicyDecision:
        """Evaluates whether the command is allowed to execute."""
        return PolicyDecision(allowed=True)


class PreventLiteLLMStopWithActiveRequestsPolicy(Policy):
    def evaluate(self, command: Command, kernel: Any) -> PolicyDecision:
        if isinstance(command, StopServiceCommand) and command.service_id == "litellm":
            # Read from system config variable to determine if litellm has mock active sessions
            active_reqs = kernel.config_repo.get("litellm_active_requests")
            if active_reqs:
                try:
                    count = int(active_reqs)
                    if count > 0:
                        return PolicyDecision(
                            allowed=False,
                            reason=f"LiteLLM has {count} active request sessions and cannot be stopped."
                        )
                except ValueError:
                    pass
        return PolicyDecision(allowed=True)


class ModelPreferencePolicy(Policy):
    def evaluate(self, command: Command, kernel: Any) -> PolicyDecision:
        # In a real setup, this would validate commands targeting cloud providers 
        # to ensure local overrides are respected.
        return PolicyDecision(allowed=True)


class PolicyEngine:
    def __init__(self):
        self._policies: List[Policy] = []
        self._retry_counts: Dict[str, int] = {}
        self._stopping_intent: Dict[str, bool] = {}
        self._first_failure_time: Dict[str, float] = {}
        self._healthy_since: Dict[str, float] = {}
        self._circuit_breakers: Dict[str, str] = {}

    def register_policy(self, policy: Policy) -> None:
        self._policies.append(policy)
        logger.info(f"Registered policy: {policy.__class__.__name__}")

    def evaluate(self, command: Command, kernel: Any) -> PolicyDecision:
        # Record stopping intent and reset auto-restart states during manual/explicit commands
        if isinstance(command, StopServiceCommand):
            self._stopping_intent[command.service_id] = True
            self._retry_counts[command.service_id] = 0
            self._circuit_breakers[command.service_id] = "CLOSED"
            self._first_failure_time.pop(command.service_id, None)
            self._healthy_since.pop(command.service_id, None)
        elif isinstance(command, StartServiceCommand):
            self._stopping_intent[command.service_id] = False
            self._retry_counts[command.service_id] = 0
            self._circuit_breakers[command.service_id] = "CLOSED"
            self._first_failure_time.pop(command.service_id, None)
            self._healthy_since[command.service_id] = time.time()
        elif isinstance(command, RestartServiceCommand):
            self._stopping_intent[command.service_id] = False
            self._retry_counts[command.service_id] = 0
            self._circuit_breakers[command.service_id] = "CLOSED"
            self._first_failure_time.pop(command.service_id, None)
            self._healthy_since[command.service_id] = time.time()

        for policy in self._policies:
            decision = policy.evaluate(command, kernel)
            if not decision.allowed:
                return decision
        return PolicyDecision(allowed=True)

    def handle_health_change(self, event: HealthChangedEvent, kernel: Any) -> None:
        """Handles auto-restart logic reactively based on health events."""
        service_id = event.service_id
        old_status = event.old_status
        new_status = event.new_status

        # Record when service transitions to RUNNING
        if new_status == "RUNNING":
            self._healthy_since[service_id] = time.time()
            return

        # Trigger auto-restart if transitioned to ERROR or STOPPED unexpectedly
        if new_status in ["ERROR", "STOPPED"] and old_status == "RUNNING":
            # Check if this was a manual stop command intent
            if self._stopping_intent.get(service_id):
                logger.info(f"Service {service_id} stopped intentionally. Skipping auto-restart.")
                self._stopping_intent[service_id] = False
                self._retry_counts[service_id] = 0
                self._circuit_breakers[service_id] = "CLOSED"
                self._first_failure_time.pop(service_id, None)
                self._healthy_since.pop(service_id, None)
                return

            # Check if auto-restart is enabled
            auto_restart_val = kernel.config_repo.get("auto_restart_enabled")
            if auto_restart_val == "false":
                return

            # Read configuration parameters with robust defaults
            limit_val = kernel.config_repo.get("auto_restart_limit")
            limit = int(limit_val) if limit_val else 3

            base_delay_val = kernel.config_repo.get("auto_restart_base_delay")
            base_delay = float(base_delay_val) if base_delay_val else 2.0

            max_delay_val = kernel.config_repo.get("auto_restart_max_delay")
            max_delay = float(max_delay_val) if max_delay_val else 30.0

            multiplier_val = kernel.config_repo.get("auto_restart_multiplier")
            multiplier = float(multiplier_val) if multiplier_val else 2.0

            jitter_pct_val = kernel.config_repo.get("auto_restart_jitter_pct")
            jitter_pct = float(jitter_pct_val) if jitter_pct_val else 0.2

            cooldown_val = kernel.config_repo.get("auto_restart_cooldown")
            cooldown = float(cooldown_val) if cooldown_val else 10.0

            window_val = kernel.config_repo.get("auto_restart_window")
            window = float(window_val) if window_val else 60.0

            now = time.time()

            # 1. Cooldown Period Reset Check
            if service_id in self._healthy_since:
                healthy_duration = now - self._healthy_since[service_id]
                if healthy_duration >= cooldown:
                    logger.info(f"Service {service_id} was healthy for {healthy_duration:.2f}s (>= cooldown {cooldown}s). Resetting retry count.")
                    self._retry_counts[service_id] = 0
                    self._circuit_breakers[service_id] = "CLOSED"
                    self._first_failure_time.pop(service_id, None)
                self._healthy_since.pop(service_id, None)

            # 2. Maximum Retry Window Reset Check
            if service_id in self._first_failure_time:
                window_duration = now - self._first_failure_time[service_id]
                if window_duration > window:
                    logger.info(f"Retry window of {window}s exceeded for service {service_id} ({window_duration:.2f}s elapsed). Resetting retry chain.")
                    self._retry_counts[service_id] = 0
                    self._circuit_breakers[service_id] = "CLOSED"
                    self._first_failure_time[service_id] = now
            else:
                self._first_failure_time[service_id] = now

            # 3. Circuit Breaker Enforcement
            if self._circuit_breakers.get(service_id) == "OPEN":
                logger.warning(f"Auto-restart blocked: Circuit Breaker is OPEN for service {service_id}.")
                return

            current_retries = self._retry_counts.get(service_id, 0)
            if current_retries >= limit:
                self._circuit_breakers[service_id] = "OPEN"
                logger.error(f"Service {service_id} reached auto-restart limit ({limit}). Circuit Breaker tripped (OPEN).")
                kernel.history_repo.log(
                    event_type="SERVICE_RESTART",
                    severity="ERROR",
                    message=f"Service {service_id} reached auto-restart limit of {limit} attempts. Circuit Breaker tripped.",
                    service_id=service_id,
                    details={"limit": limit, "circuit_breaker": "OPEN"}
                )
                return

            # 4. Schedule auto-restart with exponential backoff and jitter
            next_attempt = current_retries + 1
            self._retry_counts[service_id] = next_attempt

            delay = base_delay * (multiplier ** (next_attempt - 1))
            if jitter_pct > 0:
                jitter = delay * jitter_pct
                delay = delay + random.uniform(-jitter, jitter)
            delay = max(0.0, min(delay, max_delay))

            logger.info(f"Auto-restart policy triggered for service {service_id}. Attempt {next_attempt}/{limit}. Backoff delay: {delay:.2f}s.")
            
            kernel.history_repo.log(
                event_type="SERVICE_RESTART",
                severity="WARNING",
                message=f"Service {service_id} failed. Auto-restarting in {delay:.2f}s (attempt {next_attempt}/{limit}).",
                service_id=service_id,
                details={"attempt": next_attempt, "limit": limit, "delay_seconds": delay}
            )

            # Asynchronous background daemon execution
            def execute_delayed_restart(svc_id=service_id, d_val=delay, att=next_attempt, lim=limit):
                time.sleep(d_val)
                try:
                    service = kernel.service_registry.get_service(svc_id)
                    if service.status.value in ["STOPPED", "ERROR"]:
                        logger.info(f"Executing background auto-restart for {svc_id} (attempt {att}/{lim}).")
                        kernel.command_bus.dispatch(StartServiceCommand(service_id=svc_id), kernel)
                    else:
                        logger.info(f"Skipping background auto-restart for {svc_id} because status is {service.status.value}")
                except Exception as e:
                    logger.error(f"Background auto-restart failed for {svc_id}: {e}")

            import threading
            threading.Thread(target=execute_delayed_restart, daemon=True).start()
