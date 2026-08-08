# ============================================================
#  Aris x LAAP fusion launcher (dual harness)
#  Usage: powershell -ExecutionPolicy Bypass -File launch-aris.ps1 -Harness pi|omp
#  Injects DEEPSEEK_API_KEY from config/secrets.json then starts the harness.
#  NOTE: ASCII only - PowerShell 5.1 parses non-BOM UTF-8 as ANSI.
# ============================================================
param(
    [ValidateSet("pi", "omp")]
    [string]$Harness = "pi"
)

$ErrorActionPreference = "Continue"

# -- Inject DeepSeek key (pi uses models.json, omp uses env var) --
try {
    $secrets = Get-Content "D:\LAAP\Pi\aris\config\secrets.json" -Raw | ConvertFrom-Json
    if ($secrets.deepseek.api_key) {
        $env:DEEPSEEK_API_KEY = $secrets.deepseek.api_key
        Write-Host "[LAAP] DeepSeek key injected"
    }
} catch {
    Write-Host "[LAAP] secrets.json not found, relying on existing DEEPSEEK_API_KEY"
}

switch ($Harness) {
    "pi" {
        Write-Host "[LAAP] Starting Aris fusion (pi 0.83.0)"
        Set-Location "D:\LAAP\Pi\pi-windows-x64"
        & "D:\LAAP\Pi\pi-windows-x64\pi.exe" @args
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            Write-Host "[LAAP] pi exited with code $LASTEXITCODE"
            Read-Host "Press Enter to close"
        }
    }
    "omp" {
        Write-Host "[LAAP] Starting Aris fusion (omp 17.2.4)"
        # 干净工作目录：避免 OH-WorkSpace/N.E.K.O 等项目规则劫持人格
        Set-Location "D:\LAAP\Pi"
        $env:PI_CONFIG_DIR = ".pi"
        $env:PATH = "$env:USERPROFILE\.bun\bin;$env:PATH"
        $ompEntry = "C:\Users\user\AppData\Roaming\npm\node_modules\@oh-my-pi\pi-coding-agent\dist\cli.js"
        & "$env:USERPROFILE\.bun\bin\bun.exe" $ompEntry @args
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            Write-Host "[LAAP] omp exited with code $LASTEXITCODE"
            Read-Host "Press Enter to close"
        }
    }
}
