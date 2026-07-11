@echo off
REM Colors don't work well in Windows cmd, so using simple text

echo.
echo ========================================
echo   Data Quality Platform - Local Setup
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt > nul 2>&1

REM Create necessary directories
if not exist uploads mkdir uploads
if not exist logs mkdir logs

echo.
echo Setup complete!
echo.
echo To start the application:
echo.
echo Terminal 1 - Start Backend:
echo    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Terminal 2 - Start Frontend:
echo    streamlit run frontend/app.py
echo.
echo Then open:
echo    API:      http://localhost:8000/docs
echo    Frontend: http://localhost:8501
echo.
pause
