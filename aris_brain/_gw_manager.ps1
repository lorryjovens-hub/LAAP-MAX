<#
.SYNOPSIS
  Hermes Gateway 启动管理器 — 防 PowerShell 线程泄漏版
.DESCRIPTION
  设置 PYTHONIOENCODING=utf-8 防止子进程 reader 线程泄漏，
  启动网关，监控健康状态，自动重试。
#>

$ErrorActionPreference = "Stop"
$LogFile = "D:\LAAP\aris_brain\state\gateway_manager.log"
$PidFile = "D:\LAAP\aris_brain\state\gateway_pid.txt"

function Write-Log {
    param([string]$Message)
    $Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Time | $Message" | Out-File -FilePath $LogFile -Encoding utf8 -Append
    Write-Host "$Time | $Message"
}

Write-Log "=== Gateway Manager 启动 ==="

# 1. 设置环境变量（防 GBK 线程泄漏）
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"

# 2. 检查旧进程并清理
$OldPid = $null
if (Test-Path $PidFile) {
    $OldPid = Get-Content $PidFile -Raw -ErrorAction SilentlyContinue
    if ($OldPid) {
        $OldProc = Get-Process -Id $OldPid -ErrorAction SilentlyContinue
        if ($OldProc) {
            Write-Log "发现旧网关进程 PID=$OldPid，正在终止..."
            Stop-Process -Id $OldPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    }
}

# 3. 启动网关
$HermesDir = "D:\hermes-agent-main (1)\hermes-agent-main"
$HermesExe = Join-Path $HermesDir ".venv\Scripts\hermes.exe"
if (-not (Test-Path $HermesExe)) {
    $HermesExe = Join-Path $HermesDir ".venv\Scripts\hermes"
}

Write-Log "启动: $HermesExe gateway run --replace --profile aris"

$Process = Start-Process -FilePath $HermesExe -ArgumentList @(
    "gateway", "run", "--replace", "--profile", "aris"
) -WorkingDirectory $HermesDir -NoNewWindow -PassThru -RedirectStandardOutput "D:\LAAP\aris_brain\state\gateway_stdout.log" -RedirectStandardError "D:\LAAP\aris_brain\state\gateway_stderr.log"

# 4. 保存 PID
$Process.ID | Out-File -FilePath $PidFile -Encoding utf8 -Force
Write-Log "已启动: PID=$($Process.Id)"

# 5. 健康检测（最长等 60 秒）
$MaxWait = 60
$WaitCount = 0
$Healthy = $false

while ($WaitCount -lt $MaxWait) {
    Start-Sleep -Seconds 3
    $WaitCount += 3
    
    # 检查进程是否还在
    $Proc = Get-Process -Id $Process.Id -ErrorAction SilentlyContinue
    if (-not $Proc) {
        Write-Log "进程已退出（等待 ${WaitCount}s）"
        break
    }
    
    # 检查 API 端口
    $PortCheck = netstat -ano 2>$null | findstr ":$($Process.Id)`$"
    if ($PortCheck) {
        Write-Log "网关已就绪！(${WaitCount}s)"
        $Healthy = $true
        break
    }
    
    if ($WaitCount -ge $MaxWait) {
        Write-Log "等待超时 ($MaxWait s)"
    }
}

# 6. 输出结果
if ($Healthy) {
    Write-Log "=== Gateway 启动成功 ==="
} else {
    Write-Log "=== Gateway 启动异常 ==="
    Write-Log "检查日志: D:\LAAP\aris_brain\state\gateway_stderr.log"
}

Write-Log ""
