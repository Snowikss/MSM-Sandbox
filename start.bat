@echo off
setlocal
cd /d %~dp0

if not exist .venv (
  py -3.11 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

start "" http://127.0.0.1:8000/
uvicorn app.main:app --host 127.0.0.1 --port 8000

endlocal
