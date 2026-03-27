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
echo    Nokia WebEM Generator - Deploy / update
echo    Rebuilds app from latest GitHub ^(uploads stay on disk^)
echo  ================================================
echo.

REM Bust Docker cache for the git-clone layer only (see Dockerfile ARG CACHE_BUST).
REM No --no-cache: base images and early layers stay cached = faster updates.
set "CACHE_BUST=%RANDOM%%RANDOM%%RANDOM%"

REM One command: build if needed, recreate container when image changes.
REM Named volumes uploads/generated are NOT removed (data kept).
docker compose version >nul 2>nul
if not errorlevel 1 (
    docker compose up -d --build
) else (
    docker-compose up -d --build
)
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker Compose up --build failed.
    echo If you see a container name conflict, remove the old container once:
    echo   docker rm -f nokia-webem-generator
    echo Then run this script again.
    pause
    exit /b %errorlevel%
)

echo.
echo  ================================================
echo    Done! Application is running:
echo.
echo    React UI:    http://localhost:3000
echo    Old UI:      http://localhost:5000
echo  ================================================
echo.
start "" "http://localhost:3000/"
pause
