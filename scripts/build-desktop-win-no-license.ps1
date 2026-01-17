[CmdletBinding()]
param(
  [switch]$SkipNpmInstall,
  [switch]$SkipUvSync,
  [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$extraArgs = @()
if ($SkipNpmInstall) { $extraArgs += "-SkipNpmInstall" }
if ($SkipUvSync) { $extraArgs += "-SkipUvSync" }
if ($Clean) { $extraArgs += "-Clean" }

& (Join-Path $root "scripts/build-desktop-win.ps1") -NoLicense -SkipLicenseKeys @extraArgs
