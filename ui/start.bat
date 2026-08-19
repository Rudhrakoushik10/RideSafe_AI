@echo off
echo ==========================================
echo   RideSafe AI - Dashboard (Streamlit)
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo Starting RideSafe AI Dashboard...
echo Dashboard will open at: http://localhost:8501
echo.

streamlit run app.py

pause
