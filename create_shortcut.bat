@echo off
title Create desktop shortcut - EVE Tracking Meter
cd /d "%~dp0"
set "D=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d='%D%'; $desk=[Environment]::GetFolderPath('Desktop'); $w=New-Object -ComObject WScript.Shell;" ^
  "$s=$w.CreateShortcut((Join-Path $desk 'EVE Tracking Meter.lnk')); $s.TargetPath=(Join-Path $d 'run_tracking_meter.bat'); $s.WorkingDirectory=$d; $s.IconLocation=(Join-Path $d 'icons\tracking_meter.ico'); $s.WindowStyle=7; $s.Save()"
if errorlevel 1 (
  echo Failed to create the shortcut.
) else (
  echo "EVE Tracking Meter" shortcut was created on your desktop.
)
pause
