# ForgeOps Web Dashboard Guide

This guide explains how to monitor, configure, and manage your local AI runtimes using the React Web Dashboard.

## 1. Web Dashboard Operations

The Web Dashboard runs at `http://127.0.0.1:8088/`. It is structured into ten main pages, accessible via the left-side navigation menu:

```
+-------------------------------------------------------------+
| Home          | Key system statistics, active counts, resource gauges |
| Services      | Process toggle switches, port maps, status indicator   |
| Models        | Capabilities lists, provider details, metadata viewer|
| Health/Inv    | Hardware capabilities, tool environment logs         |
| Observability | Live hardware usage graphs (CPU, RAM, GPU, VRAM)      |
| Workflows     | Sequential setup steppers, start status indicators   |
| Event Stream  | Event audits, command dispatch history log          |
| Logs          | Live terminal output from child runtimes            |
| Settings      | Policy thresholds, retry limit, delays tuning       |
| Maintenance   | Updates dashboard, backup/restore buttons, bundle   |
+-------------------------------------------------------------+
```

### Key Daily Tasks on the Dashboard:
* **Toggle Theme**: Click the Sun/Moon icon in the upper-right corner to toggle between Dark Mode (default) and Light Mode.
* **Command Palette**: Press **Ctrl+K** to open the command search box. Type the name of any tab (e.g., "Logs") or action (e.g., "Toggle Theme") and press **Enter** to execute.
* **Monitor Transitions**: Real-time toast notifications will slide in at the bottom-right of the screen whenever a service changes status (e.g., `STARTING` -> `RUNNING`).

---
