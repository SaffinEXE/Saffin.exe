<#
Create a self-extracting EXE installer using 7-Zip.

Prerequisites:
- 7z.exe must be available either on PATH or provided via `-SevenZipPath`.

Usage:
  # create SFX from existing ZIP
  .\scripts\create_sfx_installer.ps1 -InputZip .\dist\SaffinInstaller.zip -OutputExe .\dist\SaffinInstaller.exe

  # create package first (uses package_installer.ps1) then SFX
  .\scripts\create_sfx_installer.ps1 -CreateFromZipIfMissing

  # specify local 7z.exe
  .\scripts\create_sfx_installer.ps1 -SevenZipPath 'C:\Program Files\7-Zip\7z.exe'
#>

[CmdletBinding()]
param(
    [string]$SevenZipPath = '',
    [string]$InputZip = '.\dist\SaffinInstaller.zip',
    [string]$OutputExe = '.\dist\SaffinInstaller.exe',
    [switch]$CreateFromZipIfMissing
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path "$PSScriptRoot\..").Path

function Find-7Zip {
    param([string]$hint)
    if ($hint -and (Test-Path $hint)) { return (Resolve-Path $hint).Path }
    $candidates = @(
        $hint,
        'C:\Program Files\7-Zip\7z.exe',
        'C:\Program Files (x86)\7-Zip\7z.exe'
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return (Resolve-Path $c).Path }
    }
    try {
        $cmd = Get-Command 7z.exe -ErrorAction Stop
        return $cmd.Source
    } catch {
        return $null
    }
}

$seven = Find-7Zip -hint $SevenZipPath
if (-not $seven) {
    Write-Error "7z.exe not found. Provide -SevenZipPath or install 7-Zip and ensure 7z.exe is on PATH."
    exit 2
}

Write-Host "Using 7z: $seven"

if ($CreateFromZipIfMissing -and -not (Test-Path $InputZip)) {
    Write-Host "Input ZIP not found; running package_installer.ps1 to create it..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\package_installer.ps1" -UsePSADT -OutputPath $InputZip
}

if (-not (Test-Path $InputZip)) {
    Write-Error "Input ZIP not found: $InputZip"
    exit 3
}

$temp = Join-Path ([IO.Path]::GetTempPath()) ("sfx_payload_{0}" -f ([guid]::NewGuid().ToString('N')))
New-Item -ItemType Directory -Path $temp | Out-Null

Write-Host "Extracting ZIP to staging: $temp"
Expand-Archive -Path $InputZip -DestinationPath $temp -Force

# Create SFX executable using 7z: add files to an SFX archive (7z a -sfx)
Write-Host "Creating SFX EXE: $OutputExe"

# Ensure output dir exists
$outDir = Split-Path -Parent (Resolve-Path $OutputExe)
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$args = @('a','-r','-sfx', (Resolve-Path $OutputExe).Path, (Join-Path $temp '*'))
& $seven @args

$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "7z failed with exit code $code"
    Remove-Item -Recurse -Force $temp
    exit $code
}

Write-Host "SFX created: $OutputExe"

Remove-Item -Recurse -Force $temp
