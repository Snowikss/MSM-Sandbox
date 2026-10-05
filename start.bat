@echo off
setlocal
cd /d "%~dp0"
title MSM Sandbox

echo [1/5] Checking Python...
set "PYTHON_CMD="

rem The new Windows Python launcher can exist even when no runtime is installed.
rem Do not trust `py -3.11 --version` alone; require Python code to actually run.
py -3.11 -c "print('MSM_PY_OK')" 2>nul | findstr /x "MSM_PY_OK" >nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
  echo Python 3.11 runtime is not installed. Installing it now...
  where py >nul 2>nul
  if not errorlevel 1 (
    py install 3.11
    echo.
    echo Verifying Python 3.11...
    py -3.11 -c "print('MSM_PY_OK')" 2>nul | findstr /x "MSM_PY_OK" >nul
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
  )
)

rem Fallback for a normal python.exe already present on PATH.
if not defined PYTHON_CMD (
  python -c "import sys; assert sys.version_info >= (3, 11); print('MSM_PY_OK')" 2>nul | findstr /x "MSM_PY_OK" >nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD goto :no_python

echo [2/5] Python ready: %PYTHON_CMD%

echo [3/5] Preparing virtual environment...
if not exist ".venv\Scripts\python.exe" (
  if exist ".venv" rmdir /s /q ".venv"
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :failed
)

set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" goto :failed

echo [4/5] Installing dependencies...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :failed

set "LAN_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$ip = Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } ^| Sort-Object InterfaceMetric ^| Select-Object -First 1 -ExpandProperty IPAddress; if($ip){$ip}"`) do set "LAN_IP=%%I"
if not defined LAN_IP set "LAN_IP=YOUR-PC-IP"

echo [5/5] Starting MSM Sandbox...
echo.
echo PC panel:     http://127.0.0.1:8000/
echo Phone/LAN:   http://%LAN_IP%:8000/
echo API:          http://127.0.0.1:8000/docs
echo Client logs:  http://127.0.0.1:8000/api/compat/logs
echo WebSocket:    ws://%LAN_IP%:8000/msm/socket
echo.
echo Keep this window open while using the sandbox.
echo If Windows Firewall asks about Python, allow Private networks.
echo Press Ctrl+C to stop the server.
echo.

start "MSM Sandbox browser waiter" /min powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='http://127.0.0.1:8000/api/health'; for($i=0;$i -lt 120;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1;if($r.StatusCode -eq 200){Start-Process 'http://127.0.0.1:8000/';exit}}catch{};Start-Sleep -Milliseconds 500}"

"%VENV_PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
set "SERVER_EXIT=%ERRORLEVEL%"

echo.
if not "%SERVER_EXIT%"=="0" (
  echo Server stopped with error code %SERVER_EXIT%.
  echo Copy the error text above and send it to me.
) else (
  echo Server stopped.
)
echo.
pause
exit /b %SERVER_EXIT%

:no_python
echo.
echo ERROR: Python 3.11 could not be installed automatically.
echo.
echo Run this manually in Command Prompt:
echo   py install 3.11
echo.
echo Then run start.bat again.
echo If that command fails too, install Python 3.11 from python.org
 echo and enable "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:failed
echo.
echo ERROR: MSM Sandbox setup failed.
echo Copy the error text above and send it to me.
echo.
pause
exit /b 1
