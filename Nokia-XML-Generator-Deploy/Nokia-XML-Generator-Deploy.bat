@echo off
REM Simple helper to rebuild and restart Nokia WebEM Generator from GitHub
REM Usage: double‑click this file (Windows) with Docker Desktop running.

cd /d "%~dp0"
setlocal EnableExtensions EnableDelayedExpansion

REM ---- Ensure Docker Desktop is running ----
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Docker does not seem to be running. Starting Docker Desktop...
    echo.
    set "DOCKER_DESKTOP_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    if exist "%DOCKER_DESKTOP_EXE%" (
        start "" "%DOCKER_DESKTOP_EXE%"
    ) else (
        set "DOCKER_DESKTOP_EXE=%LocalAppData%\Docker\Docker Desktop.exe"
        if exist "%DOCKER_DESKTOP_EXE%" (
            start "" "%DOCKER_DESKTOP_EXE%"
        ) else (
            echo [ERROR] Could not find Docker Desktop executable.
            echo Please start Docker Desktop manually, then run this file again.
            echo.
            pause
            exit /b 1
        )
    )

    echo Waiting for Docker to become ready...
    for /l %%i in (1,1,90) do (
        docker info >nul 2>nul
        if not errorlevel 1 goto DOCKER_READY
        timeout /t 2 >nul
    )

    echo.
    echo [ERROR] Docker did not become ready in time.
    echo Please check Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

:DOCKER_READY
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
start "" "http://localhost:5000/modernization"
pause

