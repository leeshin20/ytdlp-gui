[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$buildDir = Join-Path $projectRoot "build"
$distDir = Join-Path $projectRoot "dist"
$appDir = Join-Path $distDir "ytdlp-gui"
$archivePath = Join-Path $distDir "ytdlp-gui-windows.zip"
$specPath = Join-Path $projectRoot "build_windows.spec"
$requiredBundledFiles = @(
    (Join-Path $projectRoot "third_party\ffmpeg.exe"),
    (Join-Path $projectRoot "third_party\ffprobe.exe"),
    (Join-Path $projectRoot "third_party\deno.exe")
)
$buildSucceeded = $false

foreach ($path in $requiredBundledFiles) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing bundled binary: $path. Run scripts\prepare_ffmpeg_windows.ps1 and scripts\prepare_deno_windows.ps1 first."
    }
}

Push-Location $projectRoot
try {
    if (Test-Path -LiteralPath $buildDir) {
        Remove-Item -LiteralPath $buildDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $appDir) {
        Remove-Item -LiteralPath $appDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }

    python -m PyInstaller --clean --noconfirm --workpath $buildDir --distpath $distDir $specPath
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }

    $requiredArtifacts = @(
        (Join-Path $appDir "ytdlp-gui.exe"),
        (Join-Path $appDir "ffmpeg.exe"),
        (Join-Path $appDir "ffprobe.exe"),
        (Join-Path $appDir "deno.exe")
    )
    foreach ($path in $requiredArtifacts) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Missing build artifact: $path"
        }
    }
    foreach ($scriptName in @("core.min.js", "lib.min.js")) {
        $ejsScript = Get-ChildItem -LiteralPath $appDir -Recurse -Filter $scriptName |
            Where-Object { $_.FullName.Replace("\", "/") -match "/yt_dlp_ejs/yt/solver/[^/]+$" } |
            Select-Object -First 1
        if (-not $ejsScript) {
            throw "Missing bundled yt-dlp-ejs script: $scriptName"
        }
    }

    Compress-Archive -Path $appDir -DestinationPath $archivePath -Force

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $entryNames = $archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") }
        foreach ($entry in @(
            "ytdlp-gui/ytdlp-gui.exe",
            "ytdlp-gui/ffmpeg.exe",
            "ytdlp-gui/ffprobe.exe",
            "ytdlp-gui/deno.exe"
        )) {
            if ($entryNames -notcontains $entry) {
                throw "ZIP is missing required entry: $entry"
            }
        }
        foreach ($scriptName in @("core.min.js", "lib.min.js")) {
            if (-not ($entryNames -match "/yt_dlp_ejs/yt/solver/$([regex]::Escape($scriptName))$")) {
                throw "ZIP is missing bundled yt-dlp-ejs script: $scriptName"
            }
        }
    }
    finally {
        $archive.Dispose()
    }

    $buildSucceeded = $true
    Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
}
finally {
    if (-not $buildSucceeded -and (Test-Path -LiteralPath $archivePath)) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    Pop-Location
}
