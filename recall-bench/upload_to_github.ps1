# 用 GitHub Contents API 逐个上传 recall-bench 文件（绕过被墙的 git 协议）
$ErrorActionPreference = "Continue"
$root = "D:\LAAP\recall-bench"
$repo = "lorryjovens-hub/recall-bench"

$files = @(
  ".gitignore",
  "LICENSE",
  "README.md",
  "pyproject.toml",
  "examples/results/example_laap_vault_clean.json",
  "examples/results/example_memory_clean.json",
  "recall_bench/__init__.py",
  "recall_bench/cli.py",
  "recall_bench/probe_set.py",
  "recall_bench/runner.py",
  "recall_bench/backends/__init__.py",
  "recall_bench/backends/base.py",
  "recall_bench/backends/hierarchy_backend.py",
  "recall_bench/backends/hybrid.py",
  "recall_bench/backends/laap_vault.py",
  "recall_bench/backends/memory.py",
  "recall_bench/backends/quantum_backend.py",
  "recall_bench/backends/relation_model.py",
  "recall_bench/backends/self_model.py",
  "recall_bench/backends/vector_backend.py",
  "tests/test_laap_backends.py",
  "tests/test_runner.py"
)

$ok = 0; $fail = 0
foreach ($f in $files) {
  $local = Join-Path $root ($f -replace '/', '\')
  if (-not (Test-Path $local)) { Write-Host "MISSING: $f"; $fail++; continue }
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($local))
  $result = gh api --method PUT "repos/$repo/contents/$f" `
    -f message="add $f" -f content=$b64 -f branch=main 2>&1
  if ($LASTEXITCODE -eq 0 -and $result -match '"sha"') {
    Write-Host "OK   $f"; $ok++
  } else {
    Write-Host "FAIL $f :: $($result | Select-Object -First 1)"; $fail++
  }
  Start-Sleep -Milliseconds 300
}
Write-Host "=== done: $ok ok, $fail fail ==="
