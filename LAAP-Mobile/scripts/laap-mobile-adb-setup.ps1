#requires -Version 5.1
<#
.SYNOPSIS
    一键卸载/安装/重置 LAAP-Mobile 的 rootfs（ADB 开发调试脚本）。

.DESCRIPTION
    1. 检查 adb 是否可用
    2. 卸载旧版本 org.laap.mobile
    3. 安装指定 APK
    4. 启动 LAAP 主界面
    5. 发送广播触发 RootfsDebugReceiver 重置 rootfs
    6. 等待并重试 rootfs 状态检测
    7. 输出验证命令供进一步排查

.PARAMETER ApkPath
    APK 文件路径。默认使用当前构建输出的 debug APK。

.PARAMETER KeepUserData
    重置 rootfs 时保留 /root 目录数据。

.PARAMETER Verify
    安装并重置后，通过 adb shell 检查 bin/sh 与 bin/busybox 是否存在。

.EXAMPLE
    .\scripts\laap-mobile-adb-setup.ps1
    .\scripts\laap-mobile-adb-setup.ps1 -ApkPath "C:\Users\lorry\Downloads\laap.apk" -Verify
#>
param(
    [string]$ApkPath = "$PSScriptRoot\..\src\android\app\build\outputs\apk\debug\app-debug.apk",
    [switch]$KeepUserData,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"
$packageName = "org.laap.mobile"
$rootfsRel = "files/alpine-rootfs"

function Test-Adb {
    $adb = Get-Command adb -ErrorAction SilentlyContinue
    if (-not $adb) {
        Write-Error "adb 命令未找到。请安装 Android SDK Platform-Tools 并将 adb 加入 PATH。"
    }
    Write-Host "[OK] adb 路径: $($adb.Source)" -ForegroundColor Green
}

function Invoke-Adb {
    param([string]$Arguments, [int]$TimeoutSeconds = 60)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "adb"
    $psi.Arguments = $Arguments
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $completed = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $completed) {
        $proc.Kill()
        throw "adb 命令超时: adb $Arguments"
    }
    return @{ ExitCode = $proc.ExitCode; StdOut = $stdout; StdErr = $stderr }
}

function Wait-ForDevice {
    Write-Host "[INFO] 等待设备连接..." -ForegroundColor Cyan
    $result = Invoke-Adb "wait-for-device" -TimeoutSeconds 30
    if ($result.ExitCode -ne 0) {
        throw "设备连接失败: $($result.StdErr)"
    }
    $result = Invoke-Adb "shell getprop ro.product.model"
    $model = ($result.StdOut -split "`r?`n")[0].Trim()
    Write-Host "[OK] 已连接设备: $model" -ForegroundColor Green
}

function Uninstall-Package {
    Write-Host "[INFO] 卸载旧版本 $packageName ..." -ForegroundColor Cyan
    $result = Invoke-Adb "shell pm uninstall $packageName"
    if ($result.ExitCode -eq 0) {
        Write-Host "[OK] 卸载成功" -ForegroundColor Green
    } elseif ($result.StdOut -match "DELETE_FAILED_INTERNAL_ERROR|DELETE_FAILED_ABORTED") {
        Write-Host "[WARN] 卸载返回错误，可能本就没有安装: $($result.StdOut)" -ForegroundColor Yellow
    } elseif ($result.StdOut -match "Failure.*not installed") {
        Write-Host "[OK] 设备上未安装旧版本" -ForegroundColor Green
    } else {
        throw "卸载失败: $($result.StdOut) $($result.StdErr)"
    }
}

function Install-Apk {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "APK 文件不存在: $Path"
    }
    $full = (Resolve-Path $Path).Path
    $sizeMB = [math]::Round((Get-Item $full).Length / 1MB, 1)
    Write-Host "[INFO] 安装 APK ($sizeMB MB): $full" -ForegroundColor Cyan
    $result = Invoke-Adb "install -r -d `"$full`"" -TimeoutSeconds 180
    if ($result.ExitCode -ne 0 -or $result.StdOut -notmatch "Success") {
        throw "安装失败: $($result.StdOut) $($result.StdErr)"
    }
    Write-Host "[OK] 安装成功" -ForegroundColor Green
}

function Start-App {
    Write-Host "[INFO] 启动 LAAP 主界面..." -ForegroundColor Cyan
    $result = Invoke-Adb "shell am start -n $packageName/.MainActivity"
    if ($result.ExitCode -ne 0) {
        throw "启动失败: $($result.StdOut) $($result.StdErr)"
    }
    Write-Host "[OK] 已启动" -ForegroundColor Green
}

function Reset-Rootfs {
    param([switch]$KeepHome)
    Write-Host "[INFO] 等待应用初始化 (3s)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    $action = if ($KeepHome) { "org.laap.mobile.action.RESET_ROOTFS_KEEP_HOME" } else { "org.laap.mobile.action.RESET_ROOTFS" }
    Write-Host "[INFO] 发送广播触发 rootfs 重置 ($action)..." -ForegroundColor Cyan
    $result = Invoke-Adb "shell am broadcast -a $action -n $packageName/.sandbox.RootfsDebugReceiver"
    if ($result.ExitCode -ne 0) {
        throw "广播发送失败: $($result.StdOut) $($result.StdErr)"
    }
    Write-Host "[OK] 广播已发送，rootfs 正在后台重置" -ForegroundColor Green
}

function Test-RootfsFiles {
    param([int]$MaxAttempts = 6)
    Write-Host "[INFO] 等待 rootfs 解压完成（最多 60 秒）..." -ForegroundColor Cyan
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        Start-Sleep -Seconds 10
        $result = Invoke-Adb "shell run-as $packageName ls -l $rootfsRel/bin/sh $rootfsRel/bin/busybox 2>&1"
        $out = $result.StdOut
        if ($out -match "No such file|denied|couldn't|not exist") {
            Write-Host "  尝试 $i/$MaxAttempts：关键文件尚未就绪" -ForegroundColor Yellow
            continue
        }
        if ($out -match "busybox" -and $out -match "sh") {
            Write-Host "[OK] rootfs 关键文件已存在:" -ForegroundColor Green
            Write-Host $out -ForegroundColor Gray
            return $true
        }
    }
    return $false
}

# ── Main ────────────────────────────────────────────────────────────────────
Test-Adb
Wait-ForDevice
Uninstall-Package
Install-Apk -Path $ApkPath
Start-App
Reset-Rootfs -KeepHome:$KeepUserData

if ($Verify) {
    $ok = Test-RootfsFiles
    if (-not $ok) {
        Write-Host "[ERROR] 60 秒内未检测到 bin/sh 与 bin/busybox，请查看 logcat: adb logcat -d | findstr Rootfs" -ForegroundColor Red
        Write-Host "[INFO] 手动验证命令:" -ForegroundColor Cyan
        Write-Host "  adb shell run-as $packageName ls -l files/alpine-rootfs/bin/sh files/alpine-rootfs/bin/busybox"
        Write-Host "  adb shell run-as $packageName cat files/alpine-rootfs/.arch"
        exit 1
    }
}

Write-Host "`n[INFO] 后续可用手动验证命令:" -ForegroundColor Cyan
Write-Host "  adb shell run-as $packageName ls -l files/alpine-rootfs/bin/sh files/alpine-rootfs/bin/busybox"
Write-Host "  adb shell run-as $packageName ls files/alpine-rootfs/bin | head"
Write-Host "  adb logcat -d | findstr Rootfs"
