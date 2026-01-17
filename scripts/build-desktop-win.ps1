$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

param(
  [switch]$SkipNpmInstall,
  [switch]$SkipUvSync,
  [switch]$SkipLicenseKeys,
  [switch]$NoLicense,
  [switch]$Clean
)

function Info($msg) { Write-Host "[build] $msg" }

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Require-Cmd($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "Missing required command: $name" }
}

Require-Cmd "node"
Require-Cmd "npm"
Require-Cmd "uv"

function Write-DesktopConfig {
  $desktopResDir = Join-Path $root "apps/desktop/resources"
  New-Item -ItemType Directory -Force -Path $desktopResDir | Out-Null

  $cfgPath = Join-Path $desktopResDir "desktop_config.json"
  if ($NoLicense) {
    $cfg = @{ license_required = $false }
    $cfg | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $cfgPath
    Info "Wrote desktop config (no-license) to apps/desktop/resources/desktop_config.json"
  } else {
    if (Test-Path $cfgPath) {
      Info "Desktop config already exists: apps/desktop/resources/desktop_config.json"
    }
  }
}

function Ensure-LicenseKeys {
  if ($NoLicense) {
    Info "No-license build enabled (-NoLicense). Licensing is disabled in desktop_config.json."
    return
  }
  if ($SkipLicenseKeys) {
    Info "Skip license key setup (-SkipLicenseKeys)."
    return
  }

  $apiDir = Join-Path $root "apps/api"
  $keysDir = Join-Path $apiDir "license_keys"
  $privKey = Join-Path $keysDir "license_private_key.txt"
  $pubKey = Join-Path $keysDir "license_public_key.txt"

  if (-not (Test-Path $privKey) -or -not (Test-Path $pubKey)) {
    Info "Generating offline license keypair at apps/api/license_keys/ ..."
    Push-Location $apiDir
    try {
      uv run python -m app.tools.license_gen generate-keypair --out-dir ./license_keys | Out-Host
    } finally {
      Pop-Location
    }
  } else {
    Info "Reusing existing license keys at apps/api/license_keys/."
  }

  $desktopResDir = Join-Path $root "apps/desktop/resources"
  New-Item -ItemType Directory -Force -Path $desktopResDir | Out-Null
  Copy-Item -Force -Path $pubKey -Destination (Join-Path $desktopResDir "license_public_key.txt")
  Info "Copied license public key to apps/desktop/resources/license_public_key.txt"
  Info "Keep private key safe: apps/api/license_keys/license_private_key.txt"
}

if ($Clean) {
  Info "Cleaning build outputs..."
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $root "apps/web/build")
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $root "apps/api/dist")
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $root "apps/desktop/dist")
}

Write-DesktopConfig
Ensure-LicenseKeys

Info "1/3 Build web (static)..."
Push-Location (Join-Path $root "apps/web")
try {
  if (-not $SkipNpmInstall) {
    npm ci | Out-Host
  }
  $env:SVELTE_ADAPTER = "static"
  $env:PUBLIC_API_BASE_URL = ""
  npm run build | Out-Host
} finally {
  Pop-Location
}

Info "2/3 Build API binary (PyInstaller)..."
Push-Location (Join-Path $root "apps/api")
try {
  if (-not $SkipUvSync) {
    uv sync | Out-Host
  }
  uv run pyinstaller --name writer-agent-api --onefile app/desktop_server.py | Out-Host
} finally {
  Pop-Location
}

Info "3/3 Build desktop installer (electron-builder / NSIS)..."
Push-Location (Join-Path $root "apps/desktop")
try {
  if (-not $SkipNpmInstall) {
    npm ci | Out-Host
  }
  npm run build | Out-Host
} finally {
  Pop-Location
}

$dist = Join-Path $root "apps/desktop/dist"
Info "Done."
Info "Desktop artifacts: $dist"
if (Test-Path $dist) {
  Get-ChildItem $dist -Recurse | Select-Object FullName, Length | Format-Table -AutoSize
}
