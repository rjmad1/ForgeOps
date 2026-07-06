import os
import sys
import argparse
import httpx
from typing import List, Optional

DEFAULT_API_URL = os.environ.get("ARM_API_URL", "http://127.0.0.1:8088")

# API key setup for Local Authentication (IVV-SEC-02)
def get_api_key() -> str:
    # First check default ProgramData location
    path = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager\.session_api_key")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
            
    # Check local fallback
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(cli_dir))
    local_path = os.path.join(project_root, ".session_api_key")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
            
    return ""

def get_client() -> httpx.Client:
    key = get_api_key()
    headers = {}
    if key:
        headers["X-API-Key"] = key
    return httpx.Client(headers=headers, timeout=15.0)

def check_daemon_online() -> bool:
    try:
        with get_client() as client:
            res = client.get(f"{DEFAULT_API_URL}/health", timeout=1.0)
            return res.status_code == 200
    except Exception:
        return False

def print_offline_warning() -> None:
    print(f"Error: Control plane daemon is offline at {DEFAULT_API_URL}.", file=sys.stderr)
    print("Ensure the FastAPI service is running. Start it with:", file=sys.stderr)
    print("  uvicorn src.backend.app.main:app --reload", file=sys.stderr)

def handle_services(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        with get_client() as client:
            res = client.get(f"{DEFAULT_API_URL}/api/v1/services", timeout=5.0)
            if res.status_code == 200:
                services = res.json()
                print(f"{'Service ID':<15} | {'Service Name':<30} | {'Port':<6} | {'Status':<12} | {'PID':<6}")
                print("-" * 75)
                for s in services:
                    pid_str = str(s['pid']) if s['pid'] else "-"
                    port_str = str(s['port']) if s['port'] else "-"
                    print(f"{s['id']:<15} | {s['name']:<30} | {port_str:<6} | {s['status']:<12} | {pid_str:<6}")
            else:
                print(f"Error listing services: {res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)

def handle_status(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        with get_client() as client:
            services_res = client.get(f"{DEFAULT_API_URL}/api/v1/services")
            metrics_res = client.get(f"{DEFAULT_API_URL}/api/v1/system/metrics")
            
            if services_res.status_code == 200:
                services = services_res.json()
                print("=== Managed Services ===")
                print(f"{'Service ID':<15} | {'Service Name':<30} | {'Port':<6} | {'Status':<12} | {'PID':<6}")
                print("-" * 75)
                for s in services:
                    pid_str = str(s['pid']) if s['pid'] else "-"
                    port_str = str(s['port']) if s['port'] else "-"
                    print(f"{s['id']:<15} | {s['name']:<30} | {port_str:<6} | {s['status']:<12} | {pid_str:<6}")
                print()
            else:
                print(f"Error fetching services: {services_res.text}", file=sys.stderr)
                
            if metrics_res.status_code == 200:
                metrics = metrics_res.json()
                print("=== System Resource Consumption ===")
                print(f"  CPU Utilization : {metrics['cpu']['utilization_pct']}%")
                ram = metrics['ram']
                print(f"  RAM Utilization : {ram['utilization_pct']}% ({ram['used_bytes'] // (1024*1024)} MB / {ram['total_bytes'] // (1024*1024)} MB)")
                gpu = metrics['gpu']
                if gpu['available']:
                    print(f"  GPU Utilization : {gpu['utilization_pct']}% ({gpu['name']})")
                    print(f"  VRAM Utilization: {gpu['vram_used_bytes'] // (1024*1024)} MB / {gpu['vram_total_bytes'] // (1024*1024)} MB")
                else:
                    print("  GPU Availability: No NVIDIA GPU detected or nvidia-smi failed.")
            else:
                print(f"Error fetching system metrics: {metrics_res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)

def handle_start(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print(f"Dispatching start command for '{args.service_id}'...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/v1/services/{args.service_id}/start", timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                print(f"Success. Service status: {data['status']}, PID: {data.get('pid', '-')}")
            else:
                print(f"Error starting service: {res.json().get('detail', res.text)}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_stop(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print(f"Dispatching stop command for '{args.service_id}'...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/v1/services/{args.service_id}/stop", timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                print(f"Success. Service status: {data['status']}")
            else:
                print(f"Error stopping service: {res.json().get('detail', res.text)}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_restart(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print(f"Dispatching restart command for '{args.service_id}'...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/v1/services/{args.service_id}/restart", timeout=15.0)
            if res.status_code == 200:
                data = res.json()
                print(f"Success. Service status: {data['status']}, PID: {data.get('pid', '-')}")
            else:
                print(f"Error restarting service: {res.json().get('detail', res.text)}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_inventory(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        with get_client() as client:
            res = client.get(f"{DEFAULT_API_URL}/api/v1/inventory", timeout=5.0)
            if res.status_code == 200:
                items = res.json()
                print("=== Discovered Host System Inventory ===")
                for item in items:
                    print(f"\n[{item['category'].upper()}] {item['key']}:")
                    if isinstance(item['value'], dict):
                        for k, v in item['value'].items():
                            print(f"  {k}: {v}")
                    else:
                        print(f"  value: {item['value']}")
            else:
                print(f"Error fetching inventory: {res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)

def handle_discover(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print("Dispatching discovery scan command...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/models/discover", timeout=15.0)
            if res.status_code == 200:
                data = res.json()
                print(f"Success. Status: {data['status']}. Local models discovered: {data.get('models_discovered', 0)}")
            else:
                print(f"Error running discovery: {res.text}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_history(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        with get_client() as client:
            res = client.get(f"{DEFAULT_API_URL}/api/v1/history?limit={args.limit}", timeout=5.0)
            if res.status_code == 200:
                events = res.json()
                print(f"{'Timestamp':<23} | {'Type':<18} | {'Severity':<8} | {'Message':<50}")
                print("-" * 110)
                for ev in events:
                    msg = ev['message'][:47] + "..." if len(ev['message']) > 50 else ev['message']
                    print(f"{ev['timestamp'][:23]:<23} | {ev['event_type']:<18} | {ev['severity']:<8} | {msg:<50}")
            else:
                print(f"Error fetching history: {res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)

def handle_diagnostics(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        with get_client() as client:
            health_res = client.get(f"{DEFAULT_API_URL}/api/v1/health", timeout=5.0)
            services_res = client.get(f"{DEFAULT_API_URL}/api/v1/services", timeout=5.0)
            models_res = client.get(f"{DEFAULT_API_URL}/api/v1/models", timeout=5.0)
            
            if health_res.status_code == 200 and services_res.status_code == 200:
                health = health_res.json()
                services = services_res.json()
                models = models_res.json() if models_res.status_code == 200 else []
                
                print("=== AI Control Plane Diagnostics ===")
                print(f"Overall status: {health['status'].upper()}")
                print(f"Active Plugins/Services count: {len(services)}")
                print(f"Active Discovered Models count: {len(models)}")
                
                print("\nService Health Breakdown:")
                for s in services:
                    print(f"  - {s['name']} ({s['id']}): {s['status']}")
                    
                if models:
                    print("\nDiscovered Local Models:")
                    for m in models:
                        print(f"  - {m['name']} (Provider: {m['provider']}, Type: {m['type']})")
            else:
                print("Error executing diagnostics checks.", file=sys.stderr)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)

def handle_support_bundle(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print("Requesting support bundle generation from control plane...")
        with get_client() as client:
            res = client.get(f"{DEFAULT_API_URL}/api/v1/diagnostics/support-bundle", timeout=30.0)
            if res.status_code == 200:
                with open(args.output, "wb") as f:
                    f.write(res.content)
                print(f"Success. Support bundle saved to: {os.path.abspath(args.output)}")
            else:
                print(f"Error generating support bundle: {res.text}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_backup(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print("Initiating configuration and database backup...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/operations/backup")
            if res.status_code == 200:
                data = res.json()
                print(f"Success. Backup zip file created at: {data['backup_file']}")
            else:
                print(f"Error creating backup: {res.text}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def handle_restore(args) -> None:
    import subprocess
    print(f"Initiating system restore from zip: {args.file}")
    
    # Determine project root path and find install.py
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(cli_dir))
    install_script = os.path.join(project_root, "scripts", "install.py")
    
    # Run the installer action restore
    cmd = [sys.executable, install_script, "--action", "restore", "--file", args.file]
    
    # Check if we are running with user options that bypass admin
    # If the user sets the dev flag on arm CLI, we pass it down
    # But usually restore requires proper file permissions. Let's see if we are in dev context
    # by checking if a local .session_api_key exists (instead of ProgramData)
    program_data_key = os.path.expandvars(r"%PROGRAMDATA%\AIRuntimeManager\.session_api_key")
    if not os.path.exists(program_data_key):
        cmd.append("--dev")
        
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("System restore completed successfully.")
    else:
        print(f"System restore failed with exit code: {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)

def handle_benchmark(args) -> None:
    if not check_daemon_online():
        print_offline_warning()
        sys.exit(1)
        
    try:
        print("Running inference benchmark suite (evaluating active model)...")
        with get_client() as client:
            res = client.post(f"{DEFAULT_API_URL}/api/operations/benchmark")
            if res.status_code == 200:
                data = res.json()
                print("Benchmark Execution Succeeded.")
                print(f"  Model   : {data['model']}")
                print(f"  Provider: {data['provider']}")
                print(f"  TTFT    : {data['ttft_ms']:.1f} ms")
                print(f"  Speed   : {data['tokens_per_second']:.1f} tokens/sec")
                print(f"  Report  : {data['report_path']}")
            else:
                print(f"Benchmark run failed: {res.text}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Connection failure: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Runtime Manager (arm) CLI Client")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # services command
    subparsers.add_parser("services", help="List all AI services and their status")
    
    # status command
    subparsers.add_parser("status", help="Show status of services and resource consumption")

    # start command
    start_parser = subparsers.add_parser("start", help="Start an AI runtime service")
    start_parser.add_argument("service_id", type=str, help="The ID of the service to start")

    # stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an AI runtime service")
    stop_parser.add_argument("service_id", type=str, help="The ID of the service to stop")

    # restart command
    restart_parser = subparsers.add_parser("restart", help="Restart an AI runtime service")
    restart_parser.add_argument("service_id", type=str, help="The ID of the service to restart")

    # inventory command
    subparsers.add_parser("inventory", help="List discovered system environment and tools")
    
    # discover command
    subparsers.add_parser("discover", help="Trigger capabilities discovery scan")

    # history command
    history_parser = subparsers.add_parser("history", help="List recent operational history logs")
    history_parser.add_argument("--limit", type=int, default=20, help="Number of records to return")

    # diagnostics command
    subparsers.add_parser("diagnostics", help="Generate self-diagnostics report of the control plane")

    # support-bundle command
    sb_parser = subparsers.add_parser("support-bundle", help="Generate and download system support bundle")
    sb_parser.add_argument("--output", type=str, default="support_bundle.zip", help="Output path for the support bundle zip file")

    # backup command
    subparsers.add_parser("backup", help="Package database and configuration files into zip backup")

    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore database and configurations from zip backup")
    restore_parser.add_argument("--file", type=str, required=True, help="Path to zip backup file")

    # benchmark command
    subparsers.add_parser("benchmark", help="Measure TTFT and tokens/sec latency benchmark on active models")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch_map = {
        "services": handle_services,
        "status": handle_status,
        "start": handle_start,
        "stop": handle_stop,
        "restart": handle_restart,
        "inventory": handle_inventory,
        "discover": handle_discover,
        "history": handle_history,
        "diagnostics": handle_diagnostics,
        "support-bundle": handle_support_bundle,
        "backup": handle_backup,
        "restore": handle_restore,
        "benchmark": handle_benchmark
    }

    handler = dispatch_map.get(args.command)
    if handler:
        handler(args)

if __name__ == "__main__":
    main()
