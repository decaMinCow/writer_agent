$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

param(
  [switch]$SkipNpmInstall,
  [switch]$SkipUvSync,
  [switch]$Clean
)

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

& (Join-Path $root "scripts/build-desktop-win.ps1") `
  -NoLicense `
  -SkipLicenseKeys `
  @(
    if ($SkipNpmInstall) { "-SkipNpmInstall" }
    if ($SkipUvSync) { "-SkipUvSync" }
    if ($Clean) { "-Clean" }
  )

