<#
One-click helper to prepare environment and start Saffin on Windows.

Usage (PowerShell, run from repo root):
  .\scripts\start_saffin.ps1            # start Streamlit UI (recommended)
  .\scripts\start_saffin.ps1 -Mode cli  # start CLI assistant
  .\scripts\start_saffin.ps1 -InstallDeps  # install/upgrade deps first
  .\scripts\start_saffin.ps1 -WithEmbeddings  # also install sentence-transformers

This script creates/activates a venv at `.venv`, installs requirements,
and launches Streamlit (or the CLI assistant). It does not install or run
Ollama (download from https://ollama.com/download and run `ollama serve`).
#>

[param(
    [ValidateSet('ui','cli')]
    [string]$Mode = 'ui',
    [switch]$InstallDeps = $false,
    [switch]$WithEmbeddings = $false
)]

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Resolve-Path "$PSScriptRoot\.."
Set-Location $root

$venv = Join-Path $root '.venv'

if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment at $venv..."
    python -m venv $venv
}

Write-Host "Activating venv..."
. "$venv/Scripts/Activate.ps1"

if ($InstallDeps) {
    Write-Host "Installing dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if ($WithEmbeddings) {
        python -m pip install sentence-transformers
    }
}

if ($Mode -eq 'ui') {
    Write-Host "Starting Streamlit UI..."
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "streamlit", "run", "app.py"
} else {
    Write-Host "Starting CLI assistant (interactive)..."
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "scripts/saffin.py", "chat"
}

Write-Host "If you plan to use Ollama, start it in another terminal: `ollama serve`"
Write-Host "Script finished."
