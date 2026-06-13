param(
    [string]$Distro = "Ubuntu",
    [string]$SparkRepo = "https://github.com/EtaYang10th/spark-skills.git",
    [string]$SparkRoot = "/opt/spark/spark-skills",
    [string]$WindowsBackendRoot = "$env:USERPROFILE\wsl2-spark-backend"
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This script must run in an elevated PowerShell window."
    }
}

Assert-Admin

New-Item -ItemType Directory -Force $WindowsBackendRoot | Out-Null
Write-Host "Windows backend root: $WindowsBackendRoot"
Write-Host "WSL Spark root: $SparkRoot"

Write-Host "[1/6] Enabling Windows optional features for WSL2..."
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

Write-Host "[2/6] Installing WSL platform package if needed..."
Write-Host "Running: wsl --install --no-distribution --web-download"
$previousPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
wsl --install --no-distribution --web-download
$wslInstallExit = $LASTEXITCODE
$ErrorActionPreference = $previousPreference
Write-Host "wsl platform installer exit code: $wslInstallExit"
if ($wslInstallExit -ne 0) {
    Write-Host "If the installer reports that a reboot is required, reboot Windows and rerun this script."
}

Write-Host "[3/6] Setting WSL default version to 2..."
$ErrorActionPreference = "Continue"
wsl --set-default-version 2
$setDefaultExit = $LASTEXITCODE
$ErrorActionPreference = $previousPreference
Write-Host "wsl --set-default-version exit code: $setDefaultExit"
if ($setDefaultExit -ne 0) {
    throw "WSL default version could not be set. Reboot may be required before continuing."
}

Write-Host "[4/6] Ensuring distro exists: $Distro"
$distros = (wsl -l -q) -join "`n"
if ($distros -notmatch [regex]::Escape($Distro)) {
    Write-Host "Installing $Distro. Windows may request a reboot or first-run Linux user setup."
    wsl --install -d $Distro --web-download
}

Write-Host "[5/6] Installing Linux dependencies inside $Distro..."
wsl -d $Distro -- bash -lc "sudo apt-get update && sudo apt-get install -y git curl ca-certificates build-essential python3 python3-pip python3-venv"

Write-Host "[6/6] Installing uv and cloning SPARK-PDI repo..."
wsl -d $Distro -- bash -lc "curl -LsSf https://astral.sh/uv/install.sh | sh || true"
wsl -d $Distro -- bash -lc "sudo mkdir -p /opt/spark && sudo chown `$(whoami):`$(whoami) /opt/spark"
wsl -d $Distro -- bash -lc "if [ ! -d '$SparkRoot/.git' ]; then git clone --depth 1 '$SparkRepo' '$SparkRoot'; else cd '$SparkRoot' && git pull --ff-only; fi"

Write-Host "[verify] Verifying SPARK checkout..."
wsl -d $Distro -- bash -lc "cd '$SparkRoot' && test -f run_pipeline.py && test -d spark_skills_gen && echo 'SPARK backend ready at $SparkRoot'"

Write-Host ""
Write-Host "WSL2/SPARK backend setup finished. If any step asked for reboot or Linux user creation, reboot/finish first and rerun this script."
