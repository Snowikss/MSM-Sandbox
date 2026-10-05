@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title MSM Sandbox

echo [1/5] Checking Python...
set "PYTHON_CMD="

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

rem Method 1: ask Windows routing which IPv4 address would be used off-host.
for /f "usebackq delims=" %%I in (`"%VENV_PYTHON%" -c "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('1.1.1.1',80)); print(s.getsockname()[0]); s.close()" 2^>nul`) do set "LAN_IP=%%I"

rem Method 2: inspect IPv4 addresses attached to this hostname and prefer private LAN ranges.
if not defined LAN_IP (
  for /f "usebackq delims=" %%I in (`"%VENV_PYTHON%" -c "import socket,ipaddress; ips=[]; [ips.append(a[4][0]) for a in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET) if a[4][0] not in ips]; print(next((x for x in ips if ipaddress.ip_address(x).is_private and not x.startswith('127.')),''))" 2^>nul`) do set "LAN_IP=%%I"
)

rem Method 3: active adapter with a default gateway.
if not defined LAN_IP (
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$cfg=Get-NetIPConfiguration ^| Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } ^| Select-Object -First 1; if($cfg){$cfg.IPv4Address.IPAddress}"`) do set "LAN_IP=%%I"
)

for /f "tokens=*" %%I in ("!LAN_IP!") do set "LAN_IP=%%I"
if "!LAN_IP!"=="" set "LAN_IP=YOUR-PC-IP"
if "!LAN_IP:~0,4!"=="127." set "LAN_IP=YOUR-PC-IP"
if "!LAN_IP:~0,8!"=="169.254." set "LAN_IP=YOUR-PC-IP"

echo [5/5] Starting MSM Sandbox...
echo.
echo PC panel:     http://127.0.0.1:8000/
echo Phone/LAN:   http://!LAN_IP!:8000/
echo API:          http://127.0.0.1:8000/docs
echo Client logs:  http://127.0.0.1:8000/api/compat/logs
echo WebSocket:    ws://!LAN_IP!:8000/msm/socket
echo.
if "!LAN_IP!"=="YOUR-PC-IP" (
  echo WARNING: Could not auto-detect the LAN IPv4 address.
  echo Run: ipconfig
  echo Then use the IPv4 Address from your active Wi-Fi/Ethernet adapter.
  echo Example: http://192.168.1.25:8000/
  echo.
  echo IPv4 candidates found by Windows:
  ipconfig | findstr /i "IPv4"
  echo.
)
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
