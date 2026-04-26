# Epsimo CLI Installer for Windows
# Usage:
#   Install:   irm https://raw.githubusercontent.com/thierryteisseire/epsimo-cli/main/install.ps1 | iex
#   Uninstall: & { irm https://raw.githubusercontent.com/thierryteisseire/epsimo-cli/main/install.ps1 -OutFile $env:TEMP\ep.ps1; & $env:TEMP\ep.ps1 -Uninstall }
param([switch]$Uninstall)
$ErrorActionPreference = "Stop"

$Version   = if ($env:EPSIMO_VERSION) { $env:EPSIMO_VERSION } else { "latest" }
$InstallDir = if ($env:EPSIMO_HOME) { $env:EPSIMO_HOME } else { "$env:USERPROFILE\.epsimo" }
$Repo      = "thierryteisseire/epsimo-cli"

# --- Uninstall ---
if ($Uninstall) {
    Write-Host "▸ Uninstalling Epsimo CLI..." -ForegroundColor Green
    $BinDir = "$InstallDir\venv\Scripts"
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -like "*$BinDir*") {
        $NewPath = ($UserPath.Split(";") | Where-Object { $_ -ne $BinDir }) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        Write-Host "▸ Removed $BinDir from PATH" -ForegroundColor Green
    }
    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir
        Write-Host "▸ Removed $InstallDir" -ForegroundColor Green
    }
    Write-Host "▸ ✅ Epsimo CLI uninstalled." -ForegroundColor Green
    Write-Host "  Note: ~/.epsimo_token was preserved. Remove manually if desired."
    exit 0
}

Write-Host "▸ Epsimo CLI Installer" -ForegroundColor Green
Write-Host ""

# --- Check Python 3.8+ ---
$Python = $null
foreach ($cmd in @("python", "python3", "py -3")) {
    try {
        $ver = & ($cmd.Split(" ")[0]) ($cmd.Split(" ") | Select-Object -Skip 1) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $parts = $ver.Split(".")
        if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 8) {
            $Python = $cmd
            Write-Host "▸ Using $cmd ($ver)" -ForegroundColor Green
            break
        }
    } catch { }
}
if (-not $Python) {
    Write-Host "✖ Python 3.8+ is required. Download from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# --- Check git ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "✖ git is required. Download from https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

# --- Clone / Update ---
$RepoDir = "$InstallDir\repo"
if (Test-Path $RepoDir) {
    Write-Host "▸ Updating existing installation..." -ForegroundColor Yellow
    Push-Location $RepoDir
    git pull --quiet origin main 2>$null
    if ($LASTEXITCODE -ne 0) { git pull --quiet origin master 2>$null }
    Pop-Location
} else {
    Write-Host "▸ Installing to $InstallDir" -ForegroundColor Green
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    if ($Version -eq "latest") {
        git clone --quiet --depth 1 "https://github.com/$Repo.git" $RepoDir
    } else {
        git clone --quiet --depth 1 --branch $Version "https://github.com/$Repo.git" $RepoDir
    }
}

# --- Venv ---
$Venv = "$InstallDir\venv"
if (-not (Test-Path $Venv)) {
    Write-Host "▸ Creating virtual environment..." -ForegroundColor Green
    & $Python.Split(" ")[0] ($Python.Split(" ") | Select-Object -Skip 1) -m venv $Venv
}

$PipExe    = "$Venv\Scripts\pip.exe"
$EpsimoBin = "$Venv\Scripts\epsimo.exe"

Write-Host "▸ Installing epsimo package..." -ForegroundColor Green
& $PipExe install --quiet --upgrade pip 2>$null
& $PipExe install --quiet -e $RepoDir

# --- Add to PATH ---
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$BinDir   = "$Venv\Scripts"

if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$UserPath", "User")
    $env:Path = "$BinDir;$env:Path"
    Write-Host "▸ Added $BinDir to user PATH" -ForegroundColor Green
    Write-Host "  Restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
}

# --- Done ---
Write-Host ""
Write-Host "▸ ✅ Epsimo CLI installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Get started:"
Write-Host "    epsimo auth          # Login to your account"
Write-Host "    epsimo init          # Initialize a project"
Write-Host "    epsimo chat          # Start chatting"
Write-Host "    epsimo tools         # List available tools"
Write-Host ""
Write-Host "  Uninstall:"
Write-Host "    irm https://raw.githubusercontent.com/$Repo/main/install.ps1 -OutFile `$env:TEMP\ep.ps1; & `$env:TEMP\ep.ps1 -Uninstall"
Write-Host ""
