<#
Helper to build and run Docker compose on Windows.

Usage (from repo root):
  .\scripts\docker_run.ps1            # run docker compose up --build
  .\scripts\docker_run.ps1 -Detach   # run detached (background)
  .\scripts\docker_run.ps1 -Rebuild  # force rebuild images
#>

[CmdletBinding()]
param(
    [switch]$Detach,
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DockerCmd {
    if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
        return 'docker'
    }
    throw 'Docker CLI not found on PATH. Install Docker Desktop and ensure `docker` is available.'
}

$docker = Get-DockerCmd
Push-Location (Resolve-Path "$PSScriptRoot\..")

if ($Rebuild) {
    Write-Host "Forcing rebuild of images..."
    & $docker compose build --no-cache
}

if ($Detach) {
    Write-Host "Starting containers (detached)..."
    & $docker compose up --build -d
} else {
    Write-Host "Starting containers (foreground). Press Ctrl+C to stop."
    & $docker compose up --build
}

Pop-Location
