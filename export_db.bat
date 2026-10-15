@echo off
title VidyaMarksPro - Export Database to Hard Drive
echo ================================================================
echo   Exporting Local PostgreSQL Database to External Drive...
echo ================================================================

if not exist "db_backups" mkdir "db_backups"

REM Use python to read the active DB settings from backend\.env
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

set PGPASSWORD=%CURRENT_PG_PASSWORD%

pg_dump -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% -F c -b -v -f "db_backups\latest_examination_data.dump"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo [SUCCESS] Database exported to:
    echo   E:\Examination\VidyaMarksPro\db_backups\latest_examination_data.dump
    echo ================================================================
) else (
    echo.
    echo [ERROR] pg_dump failed! Make sure PostgreSQL bin directory is in your PATH.
)
pause