# ForgeOps Core Policies

This guide documents the runtime management policies, restart behaviors, and circuit breakers governing the local AI Control Plane.

## 1. Auto-Restart Policy

If a managed subprocess (Ollama, LiteLLM, OpenClaw, or MCP server) crashes unexpectedly, the policy engine intercepts the state change and schedules an automatic restart.

* **Multiplier**: Auto-restarts follow an exponential backoff retry curve.
* **Equation**:
  $$\text{Delay} = \text{base\_delay} \times (\text{multiplier}^{\text{attempt} - 1}) \pm \text{jitter}$$

## 2. Circuit Breaker Policy

To prevent thrashing host hardware and wasting CPU cycles, the policy engine enforces a circuit breaker mechanism:
* **Trigger**: If consecutive start failures exceed the `auto_restart_limit` (configured in Settings, default is `3`), the circuit breaker trips `OPEN`.
* **State**: The service status changes to `ERROR`, and further automated restart attempts are halted.
* **Reset**: Clicking **Start** on the Web Dashboard or executing `arm start <service>` manually resets the failure counters and attempts a clean reload.

## 3. Active Session Protection Policy

The `PreventLiteLLMStopWithActiveRequestsPolicy` safeguards developer operations:
* **Rule**: If the active request count to the LiteLLM gateway (`litellm_active_requests`) is greater than `0`, stopping the gateway is blocked.
* **Safety**: This prevents termination of long-running API inference queries or agentic loops.
