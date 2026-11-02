@echo off
echo =========================================================
echo Starting Gnani.ai Enterprise Chatbot with Guardrails...
echo =========================================================

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Starting server at http://localhost:8000 ...
python -m uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
pause

