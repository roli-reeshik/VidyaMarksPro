@echo off
chcp 65001 > nul
title VidyaMarksheet Service Stopper - VidyaLabs

echo ===============================================================================
echo        VidyaMarksheet: B.Sc. Nursing Marksheet Generation System
echo                 Stopping Background Services
echo ===============================================================================
echo  Developed at VidyaLabs ^| Contact: Priyanka Kumari (+91-9140189586)
echo ===============================================================================
echo.

echo Searching and terminating processes on Port 8000 (FastAPI Backend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Terminating PID %%a on port 8000...
    taskkill /F /PID %%a >nul 2>nul
)

echo Searching and terminating processes on Port 3000 (Next.js Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo Terminating PID %%a on port 3000...
    taskkill /F /PID %%a >nul 2>nul
)

echo.
echo All VidyaMarksheet services have been successfully stopped.
ping -n 4 127.0.0.1 > nul
