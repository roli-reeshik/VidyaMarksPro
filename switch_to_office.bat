@echo off
title VidyaMarksPro - Switch to Office Mode
echo Switching to Office configuration (No Password)...
copy /y "backend\.env.office" "backend\.env" >nul
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] backend\.env updated with OFFICE database settings.
) else (
    echo [ERROR] Failed to copy .env.office. Check file paths.
)
timeout /t 3