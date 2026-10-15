@echo off
title VidyaMarksPro - Switch to Home Mode
echo Switching to Home configuration (Password Authenticated)...
copy /y "backend\.env.home" "backend\.env" >nul
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] backend\.env updated with HOME database settings.
) else (
    echo [ERROR] Failed to copy .env.home. Check file paths.
)
timeout /t 3