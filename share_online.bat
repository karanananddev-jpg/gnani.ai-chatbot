@echo off
title Gnani.ai Chatbot - Public Share Launcher
echo ======================================================================
echo    Starting Gnani.ai Chatbot with Instant Public HTTPS Link...
echo ======================================================================
echo.

REM 1. Activate Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Setting up Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM 2. Start Chatbot Server in Background Window
echo [2/3] Launching FastAPI Backend on http://localhost:8000 ...
start /B "GnaniBackend" python -m uvicorn src.server:app --host 127.0.0.1 --port 8000

REM Wait 3 seconds for server initialization
timeout /t 3 /nobreak >nul

REM 3. Start Cloudflare Tunnel to generate Instant Public HTTPS URL
echo [3/3] Generating Secure Public HTTPS Link...
echo.
echo ======================================================================
echo  YOUR SHAREABLE PUBLIC LINK WILL APPEAR BELOW (look for .trycloudflare.com):
echo  Share that link with anyone - it works on any mobile or desktop browser!
echo ======================================================================
echo.

.\cloudflared.exe tunnel --url http://127.0.0.1:8000

pause

