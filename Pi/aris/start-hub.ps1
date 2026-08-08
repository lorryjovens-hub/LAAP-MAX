# ============================================================
#  LAAP Consciousness Hub launcher
#  Usage: powershell -NoProfile -ExecutionPolicy Bypass -File start-hub.ps1
#  - Port free      -> start hub (foreground)
#  - Port held by a real hub -> friendly message, keep window
#  - Port held by other proc -> error message, keep window
#  ASCII only (PS 5.1 parses non-BOM UTF-8 as ANSI).
# ============================================================
param(
    [int]$Port = 47110
)

$HUB_PY = "D:\LAAP\Pi\aris\hub\consciousness_hub.py"
$PYTHON = "C:\Python313\python.exe"

function Test-LaapHub([int]$port) {
    # Probe: connect + hello handshake, returns true if a real hub answers.
    $script = @"
import socket, json
try:
    s = socket.create_connection(("127.0.0.1", $port), timeout=2)
    s.settimeout(3)
    f = s.makefile("r", encoding="utf-8")
    s.sendall((json.dumps({"id": 0, "cmd": "ping"}) + "\n").encode("utf-8"))
    line = f.readline()
    s.close()
    if line and "\"ok\": true" in line and "consciousness" in line:
        print("HUB")
    else:
        print("NO")
except Exception:
    print("NO")
"@
    $tmp = Join-Path $env:TEMP "laap_hub_probe.py"
    Set-Content -Path $tmp -Value $script -Encoding UTF8
    $out = & $PYTHON $tmp 2>$null
    Remove-Item $tmp -ErrorAction SilentlyContinue
    return ($out -contains "HUB")
}

# -- port check --
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $owner = $listener | Select-Object -First 1 -ExpandProperty OwningProcess
    $procName = (Get-Process -Id $owner -ErrorAction SilentlyContinue).ProcessName
    if (Test-LaapHub -port $Port) {
        Write-Host "[LAAP] Consciousness Hub already running (PID=$owner, started $((Get-Process -Id $owner).StartTime))"
        Write-Host "[LAAP] This is the unified brain - pi/omp/IM all connect to it."
    } else {
        Write-Host "[LAAP] ERROR: port $Port is occupied by $procName (PID=$owner), not a LAAP hub."
        Write-Host "[LAAP] Close that process or change LAAP_HUB_PORT, then retry."
    }
    Read-Host "Press Enter to close"
    exit 0
}

# -- start hub --
Write-Host "[LAAP] Starting Consciousness Hub on port $Port ..."
Write-Host "[LAAP] Event stream: D:\LAAP\Pi\aris\hub\stream.jsonl"
Write-Host "[LAAP] Press Ctrl+C to stop the hub."
& $PYTHON $HUB_PY --port $Port
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "[LAAP] Hub exited with code $code"
    Read-Host "Press Enter to close"
}
