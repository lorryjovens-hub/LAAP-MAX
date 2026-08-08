# 更新 recall-bench 的两个文件（contents API + sha）
$ErrorActionPreference = "Continue"
$repo = "lorryjovens-hub/recall-bench"
$root = "D:\LAAP\recall-bench"

$files = @(
  "recall_bench/backends/laap_vault.py",
  "recall_bench/backends/hybrid.py"
)

foreach ($f in $files) {
  $sha = gh api "repos/$repo/contents/$f" -q .sha 2>&1 | Select-Object -First 1
  if ($sha -notmatch '^[0-9a-f]{40}$') {
    Write-Host "SHA FAIL ${f} :: $sha"
    continue
  }
  $local = Join-Path $root ($f -replace '/', '\')
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($local))
  $msg = "update ${f}: add prewarm + list_recent"
  $r = gh api --method PUT "repos/$repo/contents/$f" -f message=$msg -f content=$b64 -f branch=main -f sha=$sha 2>&1
  if ($LASTEXITCODE -eq 0 -and ($r -join '') -match '"sha"') {
    Write-Host "OK   $f"
  } else {
    Write-Host "FAIL $f :: $($r | Select-Object -First 1)"
  }
  Start-Sleep -Milliseconds 400
}
Write-Host "=== done ==="
