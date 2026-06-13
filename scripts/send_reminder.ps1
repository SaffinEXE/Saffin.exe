<#
Send a desktop reminder. Used by scheduled tasks.

Usage (invoked by scheduled task):
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/send_reminder.ps1 -Message "Log your session"

If BurntToast is installed, it will use a toast notification; otherwise it falls back to a message box.
#>

[param(
    [string]$Message = 'Time to log your session',
    [switch]$UseToast
)]

Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

try {
    if ($UseToast) {
        Import-Module BurntToast -ErrorAction Stop
        New-BurntToastNotification -Text $Message
        exit 0
    }
} catch {
    # fallback to message box
}

Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show($Message, 'Saffin Reminder')
