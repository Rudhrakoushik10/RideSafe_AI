@echo off
echo ============================================
echo RideSafe AI - Starting Full Application
echo ============================================
echo.

call .venv\Scripts\activate.bat

echo [1/2] Starting FastAPI backend on port 8000...
start "RideSafe API" cmd /c "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Streamlit dashboard on port 8501...
start "RideSafe UI" cmd /c "cd ui && streamlit run app.py"

echo.
echo ============================================
echo   Both services starting:
echo   Backend API:  http://localhost:8000
echo   Dashboard:    http://localhost:8501
echo ============================================
echo.
echo Close this window or press Ctrl+C to stop.
pause
