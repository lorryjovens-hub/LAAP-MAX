"""Cleanup stale Aris processes"""
import subprocess, time, os

print("=== Step 1: Killing stale processes ===")

# Kill all pi_psi_server, watchdog, daemon, feishu, gateway, ao, standalone
r = subprocess.run(
    ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/format:csv"],
    capture_output=True, text=True, timeout=8
)

pids_to_kill = []
for line in r.stdout.split("\n"):
    lower = line.lower()
    if any(kw in lower for kw in ["pi_psi_server", "watchdog", "aris_daemon", "feishu",
                                   "gateway", "ao_v10", "aris_standalone", "aris_qlg",
                                   "v11_agi", "start_feishu"]):
        parts = line.strip().split(",")
        if len(parts) >= 3:
            pid = parts[-1].strip()
            if pid.isdigit():
                pids_to_kill.append(pid)

print(f"Found {len(pids_to_kill)} stale PIDs to kill")
for pid in pids_to_kill:
    try:
        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=5)
        print(f"  Killed PID={pid}")
    except Exception as e:
        print(f"  Failed PID={pid}: {e}")

# Kill pythonw.exe gateways
r2 = subprocess.run(
    ["wmic", "process", "where", "name='pythonw.exe'", "get", "ProcessId,CommandLine", "/format:csv"],
    capture_output=True, text=True, timeout=5
)
for line in r2.stdout.split("\n"):
    lower = line.lower()
    if any(kw in lower for kw in ["feishu", "gateway", "start_feishu"]):
        parts = line.strip().split(",")
        if len(parts) >= 3:
            pid = parts[-1].strip()
            if pid.isdigit():
                try:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=5)
                    print(f"  Killed pythonw PID={pid}")
                except:
                    pass

# Clean lock files
appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\user\AppData\Local")
lock_files = [
    os.path.join(appdata, "hermes", "gateway.lock"),
    os.path.join(appdata, "hermes", "gateway.pid"),
    os.path.join(appdata, "hermes", "gateway_state.json"),
    os.path.join(appdata, "hermes", "profiles", "aris", "gateway.lock"),
    os.path.join(appdata, "hermes", "profiles", "aris", "gateway.pid"),
    os.path.join(appdata, "hermes", "profiles", "aris", "gateway_state.json"),
]
for fp in lock_files:
    try:
        if os.path.exists(fp):
            os.remove(fp)
            print(f"  Cleaned: {fp}")
    except Exception as e:
        print(f"  Failed to clean {fp}: {e}")

time.sleep(2)
print("\n=== Cleanup complete ===")
