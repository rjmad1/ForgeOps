# ForgeOps Frequently Asked Questions (FAQ)

Here are the answers to the most common questions about the ForgeOps (AI Runtime Manager) orchestration platform.

---

### Q: What is ForgeOps?
**A**: ForgeOps is a local orchestration control plane running as a Windows Service that automatically manages local LLM runtimes (Ollama), proxy gateways (LiteLLM), supervisors (OpenClaw), and connection brokers (MCP servers) on Windows 11 workstation platforms.

---

### Q: Can I query the REST API or run the CLI remotely?
**A**: By default, **no**. For security (IVV-SEC-01), the control plane binds exclusively to the loopback interface (`127.0.0.1`). Access attempts from other machines on the local network will fail.

---

### Q: Why does the system refuse to stop the LiteLLM service?
**A**: This is due to the `PreventLiteLLMStopWithActiveRequestsPolicy`. If LiteLLM has active request sessions (when `litellm_active_requests > 0` in settings), the control plane rejects stopping requests to protect active developer API calls. 

---

### Q: How does the auto-restart mechanism work?
**A**: If a managed runtime (e.g. Ollama) crashes or fails health probes unexpectedly:
1. The Policy Engine schedules a restart task in a background thread.
2. It applies an **exponential backoff** delay: 
   $$\text{delay} = \text{base\_delay} \times (\text{multiplier}^{\text{attempt} - 1})$$
3. A random **jitter** is added to prevent CPU thrashing.
4. If it fails consecutively up to `auto_restart_limit` times, the circuit breaker trips (`OPEN`) and halts restarts.

---

### Q: Where are the configurations and databases stored?
**A**:
* **SQLite Database**: `C:\ProgramData\AIRuntimeManager\db\arm.db` (seeded and maintained automatically).
* **Security Key**: `C:\ProgramData\AIRuntimeManager\.session_api_key` (contains the active token).
* **Console Logs**: `C:\ProgramData\AIRuntimeManager\logs\` (tail logs for ollama, litellm, openclaw, etc.).

---

### Q: How do I add new LLM models to the gateway?
**A**:
1. Pull the model using Ollama:
   ```powershell
   ollama pull mistral
   ```
2. Trigger ForgeOps capability discovery:
   ```powershell
   arm discover
   ```
3. ForgeOps will scan Ollama's endpoints, sync the model list to SQLite, and automatically regenerate the LiteLLM config list proxying the model.

---

### Q: What should I do if the Windows Service fails with access errors?
**A**: Open PowerShell using **Run as Administrator** and repair the service registration:
```powershell
python scripts/install.py --action repair
```
This re-registers the `AIRuntimeManager` service and resets folder access control lists.
