@echo off
echo ============================================
echo RideSafe AI - Single Server
echo ============================================
echo.

call .venv\Scripts\activate.bat

echo Starting FastAPI server on port 8000...
echo Open http://localhost:8000 in your browser
echo.
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
