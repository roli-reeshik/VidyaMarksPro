@echo off
chcp 65001 > nul
title VidyaMarksheet Launcher - VidyaLabs

echo ===============================================================================
echo        VidyaMarksheet: B.Sc. Nursing Marksheet Generation System
echo   Compliant with Indian Nursing Council (INC) ^& SGPGIMS Lucknow Regulations
echo ===============================================================================
echo  Developed at VidyaLabs ^| Copyright (c) 2026 VidyaLabs. All Rights Reserved.
echo  Contact: Priyanka Kumari ^| Mobile: +91-9140189586
echo ===============================================================================
echo.

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/4] Checking environment prerequisites...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH! Please install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not found in PATH! Please install Node.js 18+.
    pause
    exit /b 1
)
echo       - Python ^& Node.js environment detected.

rem Check database configuration (.env)
if not exist "backend\.env" (
    echo [NOTICE] backend\.env not detected.
    if exist "backend\.env.home" (
        echo         Auto-configuring backend\.env using Home PC template [.env.home]...
        copy /y "backend\.env.home" "backend\.env" >nul
    ) else if exist "backend\.env.office" (
        echo         Auto-configuring backend\.env using Office PC template [.env.office]...
        copy /y "backend\.env.office" "backend\.env" >nul
    ) else (
        echo [WARNING] No backend\.env or templates found! Database connections may fail.
    )
) else (
    echo       - Active database configuration [backend\.env] verified.
)

rem Check PostgreSQL port 5432 liveness
netstat -an | findstr ":5432" | findstr "LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo       - PostgreSQL database service active on Port 5432.
) else (
    echo       - [WARNING] PostgreSQL service does not appear to be listening on Port 5432.
    echo         If the backend fails to connect, please ensure the PostgreSQL service is started.
)

echo.
echo [2/4] Terminating any stale processes on Ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo.
echo [3/4] Launching FastAPI Backend Engine on http://127.0.0.1:8000 ...
start "VidyaMarksheet - FastAPI Backend (Port 8000)" cmd /k "title FastAPI Backend [Port 8000] && echo Starting FastAPI Backend on Port 8000... && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo [4/4] Launching Next.js Web Frontend on http://localhost:3000 ...
start "VidyaMarksheet - Next.js Frontend (Port 3000)" cmd /k "cd frontend && title Next.js Frontend [Port 3000] && echo Starting Next.js Frontend on Port 3000... && npm run dev"

echo.
echo ===============================================================================
echo  Both services launched in dedicated consoles!
echo  - Backend API:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo  - Web Frontend: http://localhost:3000
echo ===============================================================================
echo.
echo Waiting 5 seconds for services to initialize before opening browser...
ping -n 6 127.0.0.1 > nul

echo Opening VidyaMarksheet in your default browser...
start http://localhost:3000/login

echo.
echo Application is active. To stop both services, simply run stop.bat or close the windows.
echo.
