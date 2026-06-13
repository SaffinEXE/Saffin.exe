<#
Create a desktop shortcut (.lnk) that launches the CLI assistant.

Usage (from repo root):
  .\scripts\create_desktop_shortcut.ps1 -Name "Saffin Assistant"

The created shortcut launches PowerShell which runs `scripts/start_saffin.ps1 -Mode cli`.
#>

[param(
    [string]$Name = 'Saffin Assistant'
)]

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path "$PSScriptRoot\..").Path
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop ("$Name.lnk")

$target = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$scriptToRun = Join-Path $root 'scripts\start_saffin.ps1'
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File `"$scriptToRun`" -Mode cli"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $root
$shortcut.Description = 'Launch Saffin CLI assistant'
$shortcut.Save()

Write-Host "Shortcut created: $shortcutPath"
