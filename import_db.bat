@echo off
title VidyaMarksPro - Import Database to Current PC
echo ================================================================
echo   Importing Latest Database Snapshot into Local PostgreSQL...
echo ================================================================

if not exist "db_backups\latest_examination_data.dump" (
    echo [ERROR] Backup file db_backups\latest_examination_data.dump not found!
    pause
    exit /b
)

for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

set PGPASSWORD=%CURRENT_PG_PASSWORD%

REM Create database if it does not exist yet on this machine
psql -U %CURRENT_PG_USER% -h localhost -p 5432 -c "CREATE DATABASE %CURRENT_PG_DB%;" 2>nul

REM Restore all tables, constraints, marks, and audit logs
pg_restore -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% --clean --if-exists -v "db_backups\latest_examination_data.dump"

echo.
echo ================================================================
echo [FINISHED] Local PostgreSQL database is now up-to-date!
echo ================================================================
pause