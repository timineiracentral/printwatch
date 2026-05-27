# Scan arquivos versionados por dados reais de infra (segunda linha de defesa).
# Uso: .\scripts\check-no-secrets.ps1 [--staged]
# Exit 1 = bloqueia commit/push.

param(
    [switch]$Staged
)

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $root ".git"))) {
    $root = Split-Path $PSScriptRoot -Parent
}

Set-Location $root

$patterns = @(
    @{ Name = "IP VM real (10.35.11.x)"; Regex = "10\.35\.11\.\d{1,3}" },
    @{ Name = "Segmento de rede corporativo (REDACTED_LAN)"; Regex = "10\.35\.x(?!\.x)" },
    @{ Name = "Placeholder vazado 192.0.2.50"; Regex = "10\.35\.x\.x" },
    @{ Name = "Usuario SSH real"; Regex = "admin-user" },
    @{ Name = "Email/operador real"; Regex = "felipe\.jardim|Maria Silva" }
)

$skipPathRegex = @(
    "scripts[\\/]check-no-secrets",
    "replacements-filter-repo",
    "\\CONTRIBUTING\.md$",
    "\\.secrets\.baseline$",
    "\\.cursor\\rules$",
    "\\.svg$",
    "\\.png$",
    "\\.jpg$"
)

function Should-Skip([string]$path) {
    foreach ($s in $skipPathRegex) {
        if ($path -match $s) { return $true }
    }
    return $false
}

if ($Staged) {
    $files = git diff --cached --name-only --diff-filter=ACM | ForEach-Object { $_.Trim() }
} else {
    $files = git ls-files
}

$hits = @()
foreach ($rel in $files) {
    if (-not $rel) { continue }
    $full = Join-Path $root $rel
    if (-not (Test-Path $full -PathType Leaf)) { continue }
    if (Should-Skip $rel) { continue }
    $content = Get-Content -LiteralPath $full -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { continue }
    foreach ($p in $patterns) {
        if ($content -match $p.Regex) {
            $hits += [PSCustomObject]@{ File = $rel; Pattern = $p.Name }
        }
    }
}

if ($hits.Count -gt 0) {
    Write-Host "BLOQUEADO: dados sensiveis detectados (use VM_HOST, admin-user, 192.0.2.x, DOMAIN\user.example):" -ForegroundColor Red
    $hits | Format-Table -AutoSize
    Write-Host "Ver CONTRIBUTING.md e .cursor/rules/no-secrets-in-repo.mdc"
    exit 1
}

Write-Host "OK: nenhum padrao sensivel encontrado."
exit 0
