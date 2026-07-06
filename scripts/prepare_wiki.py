import os
import re

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
docs_dir = os.path.join(project_root, "docs")
wiki_docs_dir = os.path.join(docs_dir, "wiki")
scratch_wiki_dir = r"C:\Users\rjkum\.gemini\antigravity-ide\brain\f85e5114-9144-40b0-9661-9e7dfe594359\scratch\wiki"

os.makedirs(wiki_docs_dir, exist_ok=True)
os.makedirs(scratch_wiki_dir, exist_ok=True)

# Link translation map
link_map = {
    r"docs/01-Quick-Start\.md": "Quick-Start",
    r"01-Quick-Start\.md": "Quick-Start",
    r"docs/02-Installation-Guide\.md": "Installation-Guide",
    r"02-Installation-Guide\.md": "Installation-Guide",
    r"docs/03-User-Guide\.md": "User-Guide",
    r"03-User-Guide\.md": "User-Guide",
    r"docs/04-Administrator-Guide\.md": "Administrator-Guide",
    r"04-Administrator-Guide\.md": "Administrator-Guide",
    r"docs/05-Troubleshooting-Guide\.md": "Troubleshooting",
    r"05-Troubleshooting-Guide\.md": "Troubleshooting",
    r"docs/06-Operations-Manual\.md": "Operations-Manual",
    r"06-Operations-Manual\.md": "Operations-Manual",
    r"docs/07-REST-API-Reference\.md": "REST-API",
    r"07-REST-API-Reference\.md": "REST-API",
    r"docs/08-CLI-Reference\.md": "CLI-Guide",
    r"08-CLI-Reference\.md": "CLI-Guide",
    r"docs/09-Plugin-Developer-Guide\.md": "Plugin-SDK",
    r"09-Plugin-Developer-Guide\.md": "Plugin-SDK",
    r"docs/10-Architecture-Guide\.md": "Architecture",
    r"10-Architecture-Guide\.md": "Architecture",
    r"docs/11-Security-Guide\.md": "Security-Guide",
    r"11-Security-Guide\.md": "Security-Guide",
    r"docs/12-FAQ\.md": "FAQ",
    r"12-FAQ\.md": "FAQ",
    r"docs/13-Release-Notes-v1.0.0\.md": "Release-Notes",
    r"13-Release-Notes-v1.0.0\.md": "Release-Notes",
    r"docs/Configuration\.md": "Configuration",
    r"Configuration\.md": "Configuration",
    r"docs/Changelog\.md": "CHANGELOG.md",
    r"Changelog\.md": "CHANGELOG.md",
    r"docs/Roadmap\.md": "ROADMAP.md",
    r"Roadmap\.md": "ROADMAP.md",
    r"docs/DeveloperGuide\.md": "Plugin-SDK",
    r"DeveloperGuide\.md": "Plugin-SDK"
}

def translate_links(content: str) -> str:
    # Remove absolute file URLs first
    content = re.sub(r"file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/docs/", "", content)
    content = re.sub(r"file:///d:/Raja%20Jeevan%20Kumar%20Maduri/AI%20Infrastructure_OpenClawLiteLLMOllama/", "", content)
    content = re.sub(r"file:///C:/ProgramData/AIRuntimeManager/", "", content)
    
    # Translate file paths to wiki names
    for pattern, wiki_name in link_map.items():
        # Match markdown links [Text](path)
        content = re.sub(rf"\]\({pattern}\)", f"]({wiki_name})", content)
        content = re.sub(rf"\]\(\.\./{pattern}\)", f"]({wiki_name})", content)
    return content

def save_wiki_page(name: str, content: str):
    filename = f"{name}.md"
    path1 = os.path.join(wiki_docs_dir, filename)
    path2 = os.path.join(scratch_wiki_dir, filename)
    
    with open(path1, "w", encoding="utf-8") as f:
        f.write(content)
    with open(path2, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved wiki page: {filename}")

# Generate _Sidebar.md
sidebar_content = """### [[Home]]

### Core Guides
* [[Quick Start]]
* [[Installation Guide]]
* [[User Guide]]
* [[Administrator Guide]]

### Component References
* [[Dashboard Guide]]
* [[CLI Guide]]
* [[REST API]]
* [[Plugin SDK]]
* [[Configuration]]

### Operations & Maintenance
* [[Workflows]]
* [[Policies]]
* [[Diagnostics]]
* [[Troubleshooting]]
* [[Operations Manual]]
* [[Security Guide]]

### Resources
* [[FAQ]]
* [[Release Notes]]
* [[Glossary]]
"""
save_wiki_page("_Sidebar", sidebar_content)

# Generate Home.md
home_content = """# ForgeOps (AI Runtime Manager) Wiki

Welcome to the official technical wiki for **ForgeOps** (AI Runtime Manager)! 

ForgeOps is an enterprise-grade local AI orchestration and control plane platform designed to manage and monitor heterogeneous AI runtimes on Windows workstations. It automates process lifecycle, configuration synthesis, health evaluation, and resource monitoring for local AI tools: Ollama, LiteLLM, OpenClaw, and Model Context Protocol (MCP) servers.

```mermaid
graph TD
    Client[Developer Client / IDE] -->|OpenAI API / REST| APIGateway[FastAPI API Gateway]
    APIGateway -->|Read/Write| DB[(SQLite Database)]
    APIGateway -->|Process Control| PM[Process Manager]
    
    PM -->|Spawn child| Ollama[Ollama Daemon]
    PM -->|Spawn child| LiteLLM[LiteLLM Gateway]
    PM -->|Spawn child| OpenClaw[OpenClaw Agent]
    PM -->|Spawn child| MCP[MCP Servers]
```

## Documentation Roadmap

Use the sidebar navigation or the direct links below to explore the documentation:

### Core Guides
* **[[Quick Start]]**: Get ForgeOps up and running in under 10 minutes.
* **[[Installation Guide]]**: Complete prerequisites, installation parameters, and post-installation verification checks.
* **[[User Guide]]**: Daily operational tasks using the CLI and Web Dashboard.
* **[[Administrator Guide]]**: Hardened security policies, Windows Service configurations, and system directory tuning.

### Component References
* **[[Dashboard Guide]]**: A complete walkthrough of the Vite + React Web Dashboard and tabs.
* **[[CLI Guide]]**: Interactive CLI commands for the `arm` command line tool.
* **[[REST API]]**: Complete FastAPI gateway REST endpoint specifications.
* **[[Plugin SDK]]**: Abstract `RuntimePlugin` developer guide for custom extensions.
* **[[Configuration]]**: Configuration syntax for `arm-config.yaml`, `litellm_config.yaml`, and `openclaw_config.yaml`.

### Operations & Maintenance
* **[[Workflows]]**: Lifecycle sequence diagrams for startup, port checks, and capabilities discovery.
* **[[Policies]]**: Auto-restart backoffs, circuit breakers, and active session protection thresholds.
* **[[Diagnostics]]**: Quick troubleshooting telemetry, metrics table, and support bundle handling.
* **[[Troubleshooting]]**: Symptom-to-resolution recovery procedures.
* **[[Operations Manual]]**: Scheduled SRE maintenance routines.
* **[[Security Guide]]**: Local security sandbox details, NTFS DACLs, and API key management.

### Project Resources
* **[[FAQ]]**: Answers to frequently asked questions.
* **[[Release Notes]]**: Feature highlights and known limitations for Version 1.0.0.
* **[[Glossary]]**: Terminology definitions.
"""
save_wiki_page("Home", home_content)

# Source guide copy list
sources = {
    "01-Quick-Start.md": "Quick-Start",
    "02-Installation-Guide.md": "Installation-Guide",
    "03-User-Guide.md": "User-Guide",
    "04-Administrator-Guide.md": "Administrator-Guide",
    "05-Troubleshooting-Guide.md": "Troubleshooting",
    "06-Operations-Manual.md": "Operations-Manual",
    "07-REST-API-Reference.md": "REST-API",
    "08-CLI-Reference.md": "CLI-Guide",
    "09-Plugin-Developer-Guide.md": "Plugin-SDK",
    "10-Architecture-Guide.md": "Architecture",
    "11-Security-Guide.md": "Security-Guide",
    "12-FAQ.md": "FAQ",
    "13-Release-Notes-v1.0.0.md": "Release-Notes",
    "Configuration.md": "Configuration"
}

# Translate and save basic guides
for src_file, dest_name in sources.items():
    src_path = os.path.join(docs_dir, src_file)
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Run translations
    content = translate_links(content)
    
    # Save pages
    save_wiki_page(dest_name, content)

# Synthesize Dashboard-Guide.md
user_guide_path = os.path.join(docs_dir, "03-User-Guide.md")
with open(user_guide_path, "r", encoding="utf-8") as f:
    user_guide_content = f.read()

# Extract Section 1 (from Web Dashboard Operations to CLI Daily Workflows)
dashboard_section_match = re.search(r"(## 1\. Web Dashboard Operations.*?)(?=\n## 2\.)", user_guide_content, re.DOTALL)
if dashboard_section_match:
    dashboard_content = "# ForgeOps Web Dashboard Guide\n\nThis guide explains how to monitor, configure, and manage your local AI runtimes using the React Web Dashboard.\n\n" + dashboard_section_match.group(1)
    dashboard_content = translate_links(dashboard_content)
    save_wiki_page("Dashboard-Guide", dashboard_content)

# Synthesize Workflows.md
arch_guide_path = os.path.join(docs_dir, "10-Architecture-Guide.md")
with open(arch_guide_path, "r", encoding="utf-8") as f:
    arch_content = f.read()

# Extract workflows info (Section 2B and Section 3)
workflows_section = "# ForgeOps Core Workflows\n\nThis document details the software execution workflows, startup sequence, and command dispatch transactions.\n\n"
sec2b_match = re.search(r"(### B\. The Workflow Engine.*?)(?=\n### C\.)", arch_content, re.DOTALL)
sec3_match = re.search(r"(## 3\. Data Flow Diagrams.*?)(?=\n## 4\.)", arch_content, re.DOTALL)

if sec2b_match:
    workflows_section += sec2b_match.group(1) + "\n\n"
if sec3_match:
    workflows_section += sec3_match.group(1)

workflows_section = translate_links(workflows_section)
save_wiki_page("Workflows", workflows_section)

# Synthesize Policies.md
policies_section = """# ForgeOps Core Policies

This guide documents the runtime management policies, restart behaviors, and circuit breakers governing the local AI Control Plane.

## 1. Auto-Restart Policy

If a managed subprocess (Ollama, LiteLLM, OpenClaw, or MCP server) crashes unexpectedly, the policy engine intercepts the state change and schedules an automatic restart.

* **Multiplier**: Auto-restarts follow an exponential backoff retry curve.
* **Equation**:
  $$\\text{Delay} = \\text{base\\_delay} \\times (\\text{multiplier}^{\\text{attempt} - 1}) \\pm \\text{jitter}$$

## 2. Circuit Breaker Policy

To prevent thrashing host hardware and wasting CPU cycles, the policy engine enforces a circuit breaker mechanism:
* **Trigger**: If consecutive start failures exceed the `auto_restart_limit` (configured in Settings, default is `3`), the circuit breaker trips `OPEN`.
* **State**: The service status changes to `ERROR`, and further automated restart attempts are halted.
* **Reset**: Clicking **Start** on the Web Dashboard or executing `arm start <service>` manually resets the failure counters and attempts a clean reload.

## 3. Active Session Protection Policy

The `PreventLiteLLMStopWithActiveRequestsPolicy` safeguards developer operations:
* **Rule**: If the active request count to the LiteLLM gateway (`litellm_active_requests`) is greater than `0`, stopping the gateway is blocked.
* **Safety**: This prevents termination of long-running API inference queries or agentic loops.
"""
save_wiki_page("Policies", policies_section)

# Synthesize Diagnostics.md
diagnostics_section = """# ForgeOps Diagnostics Guide

This guide details the system diagnostics, health checks, metrics capture, and log bundles used to monitor and debug local AI runtimes.

## 1. Health Checks & Telemetry

The ForgeOps orchestrator runs an asynchronous health daemon:
* **Liveness Probes**: Evaluates service liveness using HTTP GET checks or raw TCP port tests at regular intervals.
* **Telemetry**: Stores performance records (CPU, RAM, GPU, VRAM) in the `performance_metrics` SQLite database table.
* **Dashboard charts**: Observability metrics are rendered dynamically in the **Observability** tab of the dashboard.

## 2. CLI Diagnostics

You can retrieve quick status summaries directly from the terminal:
```powershell
# Run self-diagnostic report of configurations, PIDs, and DB entries
arm diagnostics
```

## 3. Support Bundles

To troubleshoot complex issues:
```powershell
# Generate a compressed support archive containing service logs and database state
arm support-bundle --output "C:\\users\\public\\support_bundle.zip"
```
The support bundle zips the following:
* Service configuration records.
* Database state dumps (`arm.db`).
* Standard output / standard error logs from the runtimes.
* System environmental variables.
"""
save_wiki_page("Diagnostics", diagnostics_section)

# Synthesize Glossary.md
glossary_section = """# ForgeOps Glossary

This glossary defines terms and systems utilized across the ForgeOps AI Runtime Manager.

* **ForgeOps / AI Runtime Manager**: The local orchestration control plane daemon running as a Windows Service (`AIRuntimeManager`).
* **Ollama**: An open-source local LLM execution engine running as a background daemon.
* **LiteLLM**: An OpenAI-compatible proxy gateway that maps custom endpoints to local model runtimes.
* **OpenClaw**: A supervisor agent coordinator that executes and monitors local AI tool runs.
* **Model Context Protocol (MCP)**: An open standard protocol connecting AI models to desktop data, tools, and servers.
* **FastAPI**: The asynchronous Python web framework hosting the ForgeOps REST gateway.
* **Service Registry**: The SQLite database table tracking onboarded plugins and status configurations.
* **Capabilities Discovery**: The scanning process by which plugins query runtimes to synchronize active models into the SQLite database.
* **Circuit Breaker**: A software pattern that halts auto-restart loops when consecutive failures exceed a threshold.
* **Support Bundle**: A diagnostic zip file gathering logs, database state, and hardware specs for troubleshooting.
"""
save_wiki_page("Glossary", glossary_section)

print("Wiki preparation complete.")
