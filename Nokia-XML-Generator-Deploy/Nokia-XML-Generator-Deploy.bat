@echo off
REM ============================================================
REM  Nokia WebEM Generator - Deploy / Update from GitHub
REM  Double-click to install or update. Requires Docker Desktop.
REM ============================================================

cd /d "%~dp0"
setlocal EnableExtensions EnableDelayedExpansion

REM ---- Ensure Docker Desktop is running ----
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo  Docker is not running. Starting Docker Desktop...
    echo.
    set "DOCKER_DESKTOP_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    if exist "!DOCKER_DESKTOP_EXE!" (
        start "" "!DOCKER_DESKTOP_EXE!"
    ) else (
        set "DOCKER_DESKTOP_EXE=%LocalAppData%\Docker\Docker Desktop.exe"
        if exist "!DOCKER_DESKTOP_EXE!" (
            start "" "!DOCKER_DESKTOP_EXE!"
        ) else (
            echo [ERROR] Could not find Docker Desktop.
            echo Please start Docker Desktop manually, then run this file again.
            echo.
            pause
            exit /b 1
        )
    )

    echo  Waiting for Docker to become ready...
    for /l %%i in (1,1,90) do (
        docker info >nul 2>nul
        if not errorlevel 1 goto DOCKER_READY
        timeout /t 2 >nul
    )

    echo.
    echo [ERROR] Docker did not become ready in time.
    pause
    exit /b 1
)

:DOCKER_READY
echo.
echo  ================================================
echo    Nokia WebEM Generator - Deploying from GitHub
echo    (always pulls latest code)
echo  ================================================
echo.

REM Force fresh git clone by busting Docker cache
set CACHE_BUST=%RANDOM%%RANDOM%

docker-compose build --no-cache --build-arg CACHE_BUST=%CACHE_BUST%
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b %errorlevel%
)

docker-compose up -d
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] docker-compose up failed.
    pause
    exit /b %errorlevel%
)

echo.
echo  ================================================
echo    Done! Application is running:
echo.
echo    React UI:    http://localhost
echo    Old UI:      http://localhost:5000
echo  ================================================
echo.
start "" "http://localhost/modernization"
pause
