<#
Simple GUI installer for Windows to create Start Menu entries, desktop shortcut,
and schedule daily reminders. Run from the repo root.

Usage:
  .\scripts\installer_windows.ps1         # interactive GUI
  .\scripts\installer_windows.ps1 -Uninstall  # run GUI in uninstall mode

This script uses Windows Forms for a minimal installer experience and calls
the existing helper scripts in `scripts/`.
#>

[param(
    [switch]$Uninstall = $false
)]

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$root = (Resolve-Path "$PSScriptRoot\..").Path

$form = New-Object System.Windows.Forms.Form
$form.Text = if ($Uninstall) { 'Saffin Installer - Uninstall' } else { 'Saffin Installer' }
$form.Size = New-Object System.Drawing.Size(420,260)
$form.StartPosition = 'CenterScreen'

# Checkboxes
$chkStartMenu = New-Object System.Windows.Forms.CheckBox
$chkStartMenu.Location = New-Object System.Drawing.Point(20,20)
$chkStartMenu.Size = New-Object System.Drawing.Size(360,20)
$chkStartMenu.Text = 'Create Start Menu shortcut (Programs -> Saffin Assistant)'
$chkStartMenu.Checked = -not $Uninstall
$form.Controls.Add($chkStartMenu)

$chkDesktop = New-Object System.Windows.Forms.CheckBox
$chkDesktop.Location = New-Object System.Drawing.Point(20,50)
$chkDesktop.Size = New-Object System.Drawing.Size(360,20)
$chkDesktop.Text = 'Create Desktop shortcut'
$chkDesktop.Checked = -not $Uninstall
$form.Controls.Add($chkDesktop)

$chkTask = New-Object System.Windows.Forms.CheckBox
$chkTask.Location = New-Object System.Drawing.Point(20,80)
$chkTask.Size = New-Object System.Drawing.Size(360,20)
$chkTask.Text = 'Schedule daily reminder (09:00 by default)'
$chkTask.Checked = -not $Uninstall
$form.Controls.Add($chkTask)

# Time input
$lblTime = New-Object System.Windows.Forms.Label
$lblTime.Location = New-Object System.Drawing.Point(20,110)
$lblTime.Size = New-Object System.Drawing.Size(120,20)
$lblTime.Text = 'Reminder time (HH:MM)'
$form.Controls.Add($lblTime)

$txtTime = New-Object System.Windows.Forms.TextBox
$txtTime.Location = New-Object System.Drawing.Point(150,108)
$txtTime.Size = New-Object System.Drawing.Size(80,20)
$txtTime.Text = '09:00'
$form.Controls.Add($txtTime)

# Task name
$lblTaskName = New-Object System.Windows.Forms.Label
$lblTaskName.Location = New-Object System.Drawing.Point(20,140)
$lblTaskName.Size = New-Object System.Drawing.Size(120,20)
$lblTaskName.Text = 'Scheduled Task Name'
$form.Controls.Add($lblTaskName)

$txtTaskName = New-Object System.Windows.Forms.TextBox
$txtTaskName.Location = New-Object System.Drawing.Point(150,138)
$txtTaskName.Size = New-Object System.Drawing.Size(200,20)
$txtTaskName.Text = 'SaffinMorning'
$form.Controls.Add($txtTaskName)

# Buttons
$btnOk = New-Object System.Windows.Forms.Button
$btnOk.Location = New-Object System.Drawing.Point(80,180)
$btnOk.Size = New-Object System.Drawing.Size(100,30)
$btnOk.Text = if ($Uninstall) { 'Uninstall' } else { 'Install' }
$btnOk.Add_Click({
    $form.Tag = 'ok'
    $form.Close()
})
$form.Controls.Add($btnOk)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Location = New-Object System.Drawing.Point(220,180)
$btnCancel.Size = New-Object System.Drawing.Size(100,30)
$btnCancel.Text = 'Cancel'
$btnCancel.Add_Click({
    $form.Tag = 'cancel'
    $form.Close()
})
$form.Controls.Add($btnCancel)

$form.Topmost = $true
$form.Add_Shown({$form.Activate()})
$form.ShowDialog() | Out-Null

if ($form.Tag -ne 'ok') { Write-Host 'Cancelled'; exit 0 }

# Prepare names and paths
$name = 'Saffin Assistant'
$taskName = $txtTaskName.Text
$time = $txtTime.Text

if ($Uninstall) {
    if ($chkDesktop.Checked) {
        Write-Host "Removing desktop shortcut: $name"
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\uninstall_shortcuts.ps1" -RemoveDesktop -Name $name
    }
    if ($chkStartMenu.Checked) {
        Write-Host "Removing Start Menu shortcut: $name"
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\uninstall_shortcuts.ps1" -RemoveStartMenu -Name $name
    }
    if ($chkTask.Checked) {
        Write-Host "Removing scheduled task: $taskName"
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\uninstall_shortcuts.ps1" -RemoveTask -TaskName $taskName
    }
    Write-Host 'Uninstall complete.'
    exit 0
}

# Install mode
if ($chkDesktop.Checked) {
    Write-Host 'Creating desktop shortcut...'
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\create_desktop_shortcut.ps1" -Name $name
}

if ($chkStartMenu.Checked) {
    Write-Host 'Creating Start Menu shortcut...'
    # create Start Menu shortcut by calling the same function used by create_desktop_shortcut.ps1 but targetting Start Menu
    $startMenu = [Environment]::GetFolderPath('StartMenu')
    $progDir = Join-Path $startMenu 'Programs'
    $lnkPath = Join-Path $progDir ("$name.lnk")

    $target = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $scriptToRun = Join-Path $root 'scripts\start_saffin.ps1'
    $arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File `"$scriptToRun`" -Mode cli"

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($lnkPath)
    $shortcut.TargetPath = $target
    $shortcut.Arguments = $arguments
    $shortcut.WorkingDirectory = $root
    $shortcut.Description = 'Launch Saffin CLI assistant'
    $shortcut.Save()
    Write-Host "Start Menu shortcut created: $lnkPath"
}

if ($chkTask.Checked) {
    Write-Host "Scheduling daily reminder: $time"
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$root\scripts\schedule_reminder.ps1" -TaskName $taskName -Time $time -Message 'Log your session for today'
}

Write-Host 'Install complete.'
