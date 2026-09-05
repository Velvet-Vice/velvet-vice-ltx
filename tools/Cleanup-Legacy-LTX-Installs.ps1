[CmdletBinding()]
param(
    [string]$ComfyUIRoot,
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Resolve-ComfyRoot {
    param([string]$Explicit)
    if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
        return [IO.Path]::GetFullPath($Explicit.Trim('"'))
    }
    $candidates = @(
        (Join-Path $env:USERPROFILE 'Desktop\ComfyUI_windows_portable\ComfyUI'),
        (Join-Path $env:USERPROFILE 'ComfyUI_windows_portable\ComfyUI'),
        (Join-Path $env:USERPROFILE 'ComfyUI')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate 'main.py') -PathType Leaf) {
            return [IO.Path]::GetFullPath($candidate)
        }
    }
    $entered = Read-Host 'Full ComfyUI path'
    return [IO.Path]::GetFullPath($entered.Trim('"'))
}

function Test-VelvetViceLTXFolder {
    param([string]$Path)
    if (-not (Test-Path $Path -PathType Container)) { return $false }

    $pyproject = Join-Path $Path 'pyproject.toml'
    if (Test-Path $pyproject -PathType Leaf) {
        $raw = Get-Content -LiteralPath $pyproject -Raw -ErrorAction SilentlyContinue
        if ($raw -match '(?im)^\s*name\s*=\s*["'']velvet-vice-ltx["'']') { return $true }
    }

    $version = Join-Path $Path 'version.py'
    if (Test-Path $version -PathType Leaf) {
        $raw = Get-Content -LiteralPath $version -Raw -ErrorAction SilentlyContinue
        if ($raw -match 'SUPPORTED_LTX_VERSIONS') { return $true }
        if ($raw -match 'ComfyUI-Velvet-Vice-LTX') { return $true }
        if ($raw -match 'velvet-vice-ltx') { return $true }
    }

    return $false
}

$root = Resolve-ComfyRoot $ComfyUIRoot
if (-not (Test-Path (Join-Path $root 'main.py') -PathType Leaf)) {
    throw "Invalid ComfyUI folder: $root"
}

$customNodes = Join-Path $root 'custom_nodes'
$legacyNames = @(
    'ComfyUI-Velvet-Vice-LTX',
    'ComfyUI-Velvet-Vice-LTX.disabled',
    'ComfyUI-Velvet-Vice-LTX-main',
    'ComfyUI-Velvet-Vice-LTX-main.disabled',
    'velvet-vice-ltx-main',
    'velvet-vice-ltx-main.disabled'
)

$found = @()
foreach ($name in $legacyNames) {
    $path = Join-Path $customNodes $name
    if (Test-VelvetViceLTXFolder $path) { $found += $path }
}

if ($found.Count -eq 0) {
    Write-Host 'No legacy Velvet Vice LTX duplicate folders were found.'
    Write-Host 'The Manager-owned canonical folder is velvet-vice-ltx and is intentionally not removed by this cleanup tool.'
    exit 0
}

Write-Host 'Detected legacy Velvet Vice LTX folder(s):' -ForegroundColor Cyan
$found | ForEach-Object { Write-Host " - $_" }

if (-not $Yes) {
    $answer = (Read-Host 'Close ComfyUI. Remove ALL detected legacy LTX copies? Type JA').Trim().ToUpperInvariant()
    if ($answer -ne 'JA') { throw 'Cancelled.' }
}

foreach ($path in $found) {
    Remove-Item -LiteralPath $path -Recurse -Force
    Write-Host "Removed: $path" -ForegroundColor Green
}

Write-Host ''
Write-Host 'Legacy Velvet Vice LTX copies removed.' -ForegroundColor Green
Write-Host 'Restart ComfyUI completely and hard-refresh the browser (Ctrl+F5).'
Write-Host 'For future installs/updates/uninstalls, use only the Manager package velvet-vice-ltx.'
