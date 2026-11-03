@echo off
cd /d "%~dp0"
set "PYW="
where pyw >nul 2>nul && set "PYW=pyw -3"
if not defined PYW (where pythonw >nul 2>nul && set "PYW=pythonw")
if not defined PYW (
  echo Python was not found. Install it from https://www.python.org and check "Add python.exe to PATH".
  pause
  exit /b 1
)
start "" %PYW% "%~dp0eve_tracking_meter.py"
