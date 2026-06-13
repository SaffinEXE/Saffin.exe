<#
Register a per-user scheduled task that runs `scripts/send_reminder.ps1`.

Usage (from repo root):
  .\scripts\schedule_reminder.ps1 -TaskName SaffinMorning -Time 09:00 -Message "Log your session"

This script uses `schtasks.exe` to create a daily task for the current user.
#>

[param(
    [string]$TaskName = 'SaffinReminder',
    [string]$Time = '09:00',
    [string]$Message = 'Time to log your session'
)]

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path "$PSScriptRoot\..").Path
$scriptPath = Join-Path $root 'scripts\send_reminder.ps1'

if (-not (Test-Path $scriptPath)) {
    Write-Error "Reminder script not found: $scriptPath"
    exit 1
}

$timeRe = '^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$'
if ($Time -notmatch $timeRe) {
    Write-Error "Time must be HH:MM (24h). Got: $Time"
    exit 1
}

$action = "powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" -Message `"$Message`""

Write-Host "Creating scheduled task '$TaskName' at $Time (daily) for current user..."

schtasks /Create /SC DAILY /TN $TaskName /TR "$action" /ST $Time /F | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Scheduled task created: $TaskName"
} else {
    Write-Error "Failed to create scheduled task (exit code $LASTEXITCODE)."
}
