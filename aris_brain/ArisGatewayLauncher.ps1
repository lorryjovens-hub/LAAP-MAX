# Aris Feishu Gateway Launcher — 带互斥锁与指数退避的自愈守护
# 功能：
#   1. 启动前检测是否已有同配置 gateway 在运行，防止多实例抢同一个 Feishu app_id
#   2. 强制飞书域名直连（绕过系统代理残留配置）
#   3. 网关崩溃后按指数退避重试，连续失败达到上限后进入长休眠，避免进程泛滥
#   4. 详细日志写入 %USERPROFILE%\.aris\gateway_launcher.log

$ErrorActionPreference = "Stop"

# ---------- 配置 ----------
$HermesHome    = "$env:LOCALAPPDATA\hermes\hermes-agent"
$HermesExe     = "$HermesHome\venv\Scripts\hermes.exe"
$Profile       = "aris"
$LockDir       = "$env:LOCALAPPDATA\hermes\profiles\$Profile"
$LogDir        = "$env:USERPROFILE\.aris"
$LogFile       = "$LogDir\gateway_launcher.log"
$MaxFastRetries= 5          # 连续快速重启上限
$BaseWaitSec   = 10         # 首次失败后等待秒数
$MaxWaitSec    = 600        # 最大等待秒数（10分钟）
$LongHibernate = 3600       # 达到上限后休眠1小时

# ---------- 日志函数 ----------
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    try {
        Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    } catch {}
    # 调试时可在控制台看到
    # Write-Host $line
}

# ---------- 初始化 ----------
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
New-Item -ItemType Directory -Path $LockDir -Force | Out-Null
Write-Log "--- Aris Gateway Launcher started ---"

# 环境变量：强制飞书域名直连，避免读取到系统代理 127.0.0.1:7890
$env:NO_PROXY   = "open.feishu.cn,open.larksuite.com,localhost,127.0.0.1"
$env:HTTP_PROXY  = ""
$env:HTTPS_PROXY = ""
$env:http_proxy  = ""
$env:https_proxy = ""
$env:all_proxy   = ""
$env:HERMES_PROFILE = $Profile

# 如果 hermes.exe 不存在，尝试 fallback 路径
if (-not (Test-Path $HermesExe)) {
    $HermesExe = "$HermesHome\.venv\Scripts\hermes.exe"
}
if (-not (Test-Path $HermesExe)) {
    $HermesExe = "hermes"
}
Write-Log "Hermes executable: $HermesExe"

# ---------- 检测是否已有同 profile gateway 在运行 ----------
function Test-GatewayRunning {
    $lockFile = "$LockDir\gateway.lock"
    if (Test-Path $lockFile) {
        try {
            $lockJson = Get-Content $lockFile -Raw | ConvertFrom-Json
            $pidFromLock = $lockJson.pid
            if ($pidFromLock) {
                $proc = Get-Process -Id $pidFromLock -ErrorAction SilentlyContinue
                if ($proc) {
                    # 再确认命令行包含 hermes gateway
                    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$pidFromLock" -ErrorAction SilentlyContinue).CommandLine
                    if ($cmd -and ($cmd -match 'hermes.*gateway')) {
                        return $true
                    }
                }
            }
        } catch {
            Write-Log "Failed to parse gateway.lock: $_" "WARN"
        }
    }

    # 兜底：扫描当前用户下所有 hermes gateway 进程
    $running = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match 'hermes|python' -and $_.CommandLine -match 'gateway'
    }
    return ($running -ne $null)
}

# ---------- 清理陈旧锁文件 ----------
function Clear-StaleLocks {
    @('gateway.lock','gateway.pid') | ForEach-Object {
        $f = "$LockDir\$_"
        if (Test-Path $f) {
            Remove-Item $f -Force -ErrorAction SilentlyContinue
            Write-Log "Cleared stale lock: $f" "INFO"
        }
    }
}

# ---------- 主循环 ----------
$fastRetryCount = 0
while ($true) {
    try {
        if (Test-GatewayRunning) {
            Write-Log "Another Aris gateway is already running. Skip start." "WARN"
            Start-Sleep -Seconds $LongHibernate
            continue
        }

        Clear-StaleLocks

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $HermesExe
        $psi.Arguments = "gateway run --replace"
        $psi.WorkingDirectory = $HermesHome
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true

        $proc = [System.Diagnostics.Process]::Start($psi)
        Write-Log "Started hermes gateway (PID $($proc.Id))" "INFO"

        # 同步等待进程退出
        $proc.WaitForExit()
        $exitCode = $proc.ExitCode
        $stdout = $proc.StandardOutput.ReadToEnd()
        $stderr = $proc.StandardError.ReadToEnd()

        if ($stdout) { Write-Log "STDOUT: $stdout" "INFO" }
        if ($stderr) { Write-Log "STDERR: $stderr" "WARN" }

        Write-Log "hermes gateway exited with code $exitCode" "WARN"

        # 如果正常退出码 0，认为用户主动停止，不再快速重启
        if ($exitCode -eq 0) {
            Write-Log "Clean exit. Sleeping before next check..." "INFO"
            Start-Sleep -Seconds $LongHibernate
            $fastRetryCount = 0
            continue
        }

        # 错误退出：指数退避
        $fastRetryCount++
        if ($fastRetryCount -gt $MaxFastRetries) {
            $waitSec = $LongHibernate
            Write-Log "Fast retry limit ($MaxFastRetries) reached. Hibernating for ${waitSec}s." "ERROR"
            $fastRetryCount = 0
        } else {
            $waitSec = [math]::Min($BaseWaitSec * [math]::Pow(2, $fastRetryCount - 1), $MaxWaitSec)
            Write-Log "Retry $fastRetryCount/$MaxFastRetries. Waiting ${waitSec}s before restart..." "WARN"
        }

        Start-Sleep -Seconds $waitSec

    } catch {
        Write-Log "Launcher exception: $_" "ERROR"
        $fastRetryCount++
        $waitSec = if ($fastRetryCount -gt $MaxFastRetries) { $LongHibernate } else { [math]::Min($BaseWaitSec * [math]::Pow(2, $fastRetryCount - 1), $MaxWaitSec) }
        Start-Sleep -Seconds $waitSec
    }
}
