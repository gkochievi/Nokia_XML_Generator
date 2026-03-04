@echo off
REM Simple helper to rebuild and restart Nokia WebEM Generator from GitHub
REM Usage: double‑click this file (Windows) with Docker Desktop running.

cd /d "%~dp0"
echo.
echo ============================================
echo   Rebuilding image and restarting container
echo   (pulling latest code from GitHub)
echo ============================================
echo.

docker-compose up --build -d

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] docker-compose command failed. Make sure:
    echo   - Docker Desktop is running
    echo   - docker-compose is installed and in PATH
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo Done. Application should be available on http://localhost:5000
echo.
pause

