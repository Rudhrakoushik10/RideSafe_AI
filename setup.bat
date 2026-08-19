@echo off
echo ============================================
echo RideSafe AI - Deployment Setup
echo ============================================
echo.

echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo Installing inference dependencies...
pip install -r requirements-inference.txt

echo.
echo Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file from template. Please edit it with your settings.
) else (
    echo .env file already exists.
)

echo.
echo Setting up database...
python -c "from database.models import init_db, seed_rules; init_db(); seed_rules(); print('Database initialized and rules seeded.')"

echo.
echo ============================================
echo Setup complete! Run 'start.bat' to launch.
echo ============================================
pause
