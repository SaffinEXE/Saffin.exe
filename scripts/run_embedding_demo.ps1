<#
Run a full embedding demo on Windows (PowerShell).

This script will:
- create and activate a venv (in .venv)
- install requirements and sentence-transformers
- build the embedding index
- run a sample semantic search
- run the assistant search CLI (embeddings)

Run from repository root:
  powershell -ExecutionPolicy Bypass -File .\scripts\run_embedding_demo.ps1
#>

Set-StrictMode -Version Latest

$ErrorActionPreference = 'Stop'

$venvDir = Join-Path $PSScriptRoot '..' '.venv' | Resolve-Path -Relative
$venvPath = (Resolve-Path $venvDir).Path

Write-Host "Using venv path: $venvPath"

if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

# Activate venv
if (Test-Path "$venvPath/Scripts/Activate.ps1") {
    . "$venvPath/Scripts/Activate.ps1"
} else {
    Write-Error "Cannot find venv activation script. Ensure Python is installed and on PATH."
    exit 1
}

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install sentence-transformers

Write-Host "Building embedding index (this may download a model)..."
python scripts/rag.py --build --embeddings

Write-Host "Running a semantic search demo..."
python scripts/rag.py "auth refactor" --embeddings

Write-Host "Running assistant search (embeddings)..."
PYTHONPATH=. python scripts/assistant.py search_reviews "refactor or auth" --embeddings

Write-Host "Done."
