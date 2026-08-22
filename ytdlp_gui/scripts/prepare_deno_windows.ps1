[CmdletBinding()]
param(
    [string]$DownloadUrl = "https://github.com/denoland/deno/releases/download/v2.7.13/deno-x86_64-pc-windows-msvc.zip",
    [string]$ExpectedSha256 = "3925338E4548F54076BD24285779D5D2A1640A7941F564E7C7D992EF10D68D41"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$projectRoot = Split-Path -Parent $PSScriptRoot
$downloadDir = Join-Path $projectRoot "build\deno-download"
$archivePath = Join-Path $downloadDir "deno.zip"
$extractDir = Join-Path $downloadDir "extracted"
$thirdPartyDir = Join-Path $projectRoot "third_party"

New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
Invoke-WebRequest -Uri $DownloadUrl -OutFile $archivePath
$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($actualHash -ne $ExpectedSha256) {
    throw "Deno checksum mismatch: expected $ExpectedSha256, got $actualHash"
}
if (Test-Path -LiteralPath $extractDir) {
    Remove-Item -LiteralPath $extractDir -Recurse -Force
}
Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir

$deno = Get-ChildItem -LiteralPath $extractDir -Recurse -Filter "deno.exe" | Select-Object -First 1
if (-not $deno) {
    throw "The Deno archive does not contain deno.exe"
}

New-Item -ItemType Directory -Force -Path $thirdPartyDir | Out-Null
Copy-Item -LiteralPath $deno.FullName -Destination (Join-Path $thirdPartyDir "deno.exe") -Force
Write-Output "Prepared Deno 2.7.13 (SHA256: $actualHash)"
