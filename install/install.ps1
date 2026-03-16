# MinerU CLI installer for Windows
# Usage: irm https://mineru.net/install.ps1 | iex
#
# Environment variables:
#   MINERU_VERSION   - version to install (default: "latest")
#   MINERU_BASE_URL  - override OSS base URL
#   INSTALL_DIR      - install directory (default: $HOME\.mineru\bin)

$ErrorActionPreference = "Stop"

$Version = if ($env:MINERU_VERSION) { $env:MINERU_VERSION } else { "latest" }
$BaseURL = if ($env:MINERU_BASE_URL) { $env:MINERU_BASE_URL } else { "https://mineru.net/mineru-open-api" }
$InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { "$HOME\.mineru\bin" }

$Arch = if ([Environment]::Is64BitOperatingSystem) {
    if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
} else {
    Write-Error "32-bit Windows is not supported"; exit 1
}

$Binary = "mineru-open-api-cli-windows-${Arch}.exe"
$URL = "${BaseURL}/${Version}/${Binary}"
$DestPath = Join-Path $InstallDir "mineru-open-api.exe"

Write-Host "Downloading mineru ${Version} for windows/${Arch}..."
Write-Host "  ${URL}"

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

try {
    Invoke-WebRequest -Uri $URL -OutFile $DestPath -UseBasicParsing
} catch {
    Write-Error "Download failed: $_"
    exit 1
}

if (-not (Test-Path $DestPath) -or (Get-Item $DestPath).Length -eq 0) {
    Write-Error "Download failed or file is empty"
    exit 1
}

# Add to PATH if not already there
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$InstallDir", "User")
    $env:Path = "$env:Path;$InstallDir"
    Write-Host "Added $InstallDir to user PATH"
}

Write-Host ""
Write-Host "Installed successfully!"
& $DestPath version
Write-Host ""
Write-Host "Run 'mineru-open-api auth' to configure your API token."
