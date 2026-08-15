# 兼容入口：调用 Python 扫描器（Qoder 风格规则）
$ErrorActionPreference = 'Stop'
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
& $py (Join-Path $PSScriptRoot 'check-secrets.py') @args
exit $LASTEXITCODE
