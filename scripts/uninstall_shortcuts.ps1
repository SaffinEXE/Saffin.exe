<#
Remove desktop/start menu shortcuts and scheduled task for Saffin.

Usage:
  .\scripts\uninstall_shortcuts.ps1 -RemoveDesktop -Name "Saffin Assistant"
  .\scripts\uninstall_shortcuts.ps1 -RemoveStartMenu -RemoveTask -TaskName SaffinMorning -Name "Saffin Assistant"
#>

[param(
    [switch]$RemoveDesktop,
    [switch]$RemoveStartMenu,
    [switch]$RemoveTask,
    [string]$TaskName = 'SaffinMorning',
    [string]$Name = 'Saffin Assistant'
)]

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($RemoveDesktop) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $path = Join-Path $desktop ("$Name.lnk")
    if (Test-Path $path) { Remove-Item $path -Force; Write-Host "Removed desktop shortcut: $path" } else { Write-Host "Desktop shortcut not found: $path" }
}

if ($RemoveStartMenu) {
    $startMenu = [Environment]::GetFolderPath('StartMenu')
    $progDir = Join-Path $startMenu 'Programs'
    $path = Join-Path $progDir ("$Name.lnk")
    if (Test-Path $path) { Remove-Item $path -Force; Write-Host "Removed Start Menu shortcut: $path" } else { Write-Host "Start Menu shortcut not found: $path" }
}

if ($RemoveTask) {
    $cmd = "schtasks /Delete /TN $TaskName /F"
    Write-Host "Deleting scheduled task: $TaskName"
    cmd /c $cmd | Out-Null
}

Write-Host 'Done.'
