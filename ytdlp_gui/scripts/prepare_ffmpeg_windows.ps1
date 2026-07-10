[CmdletBinding()]
param(
    [string]$DownloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    [string]$ChecksumUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$projectRoot = Split-Path -Parent $PSScriptRoot
$downloadDir = Join-Path $projectRoot "build\ffmpeg-download"
$archivePath = Join-Path $downloadDir "ffmpeg-release-essentials.zip"
$checksumPath = "$archivePath.sha256"
$extractDir = Join-Path $downloadDir "extracted"
$thirdPartyDir = Join-Path $projectRoot "third_party"

New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
Invoke-WebRequest -Uri $DownloadUrl -OutFile $archivePath
Invoke-WebRequest -Uri $ChecksumUrl -OutFile $checksumPath

$expectedHash = ((Get-Content -LiteralPath $checksumPath -Raw).Trim() -split "\s+")[0]
$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) {
    throw "FFmpeg checksum mismatch: expected $expectedHash, got $actualHash"
}

if (Test-Path -LiteralPath $extractDir) {
    Remove-Item -LiteralPath $extractDir -Recurse -Force
}
Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir

$ffmpeg = Get-ChildItem -LiteralPath $extractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
$ffprobe = Get-ChildItem -LiteralPath $extractDir -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
if (-not $ffmpeg -or -not $ffprobe) {
    throw "The verified FFmpeg archive does not contain ffmpeg.exe and ffprobe.exe"
}

New-Item -ItemType Directory -Force -Path $thirdPartyDir | Out-Null
Copy-Item -LiteralPath $ffmpeg.FullName -Destination (Join-Path $thirdPartyDir "ffmpeg.exe") -Force
Copy-Item -LiteralPath $ffprobe.FullName -Destination (Join-Path $thirdPartyDir "ffprobe.exe") -Force

Write-Output "Prepared FFmpeg binaries (SHA256: $actualHash)"
