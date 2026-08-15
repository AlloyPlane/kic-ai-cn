# 密钥扫描：提交前/CI 用。命中即退出码 1。
# 用法: powershell -File scripts/check-secrets.ps1
$ErrorActionPreference = 'Stop'
$patterns = @(
  'sk-[A-Za-z0-9]{16,}',          # DeepSeek/OpenAI 风格
  'ghp_[A-Za-z0-9]{30,}',         # GitHub PAT
  'github_pat_[A-Za-z0-9_]{30,}',
  'AKIA[0-9A-Z]{16}',             # AWS
  'AIza[0-9A-Za-z_-]{30,}',       # Google
  'xox[baprs]-[A-Za-z0-9-]{20,}', # Slack
  '-----BEGIN [A-Z ]+ PRIVATE KEY',
  'Bearer [A-Za-z0-9._-]{20,}'
)
$hits = @()
$files = git ls-files 2>$null
foreach ($f in $files) {
  if (-not (Test-Path $f)) { continue }
  $content = Get-Content $f -Raw -ErrorAction SilentlyContinue
  if (-not $content) { continue }
  foreach ($p in $patterns) {
    if ($content -match $p) {
      $hits += $f
      break
    }
  }
}
if ($hits.Count -gt 0) {
  Write-Output '✋ 检测到疑似密钥，请检查以下文件（值已隐藏）：'
  $hits | ForEach-Object { Write-Output ('  - ' + $_) }
  exit 1
}
Write-Output '✓ 未检测到密钥'
