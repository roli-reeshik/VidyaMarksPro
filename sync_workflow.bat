@echo off
title VidyaMarksPro - Master Sync & Environment Manager
cls

:MENU
echo ================================================================
echo         VidyaMarksPro :: Master Environment & Sync Manager
echo ================================================================
echo Repository: https://github.com/roli-reeshik/VidyaMarksPro
echo.
echo Please select your current workflow stage:
echo [1] Starting at Home   (Pull Git updates + Set Home Env + Import DB)
echo [2] Leaving Home       (Export DB + Commit & Push Git updates)
echo [3] Starting Office    (Pull Git updates + Set Office Env + Import DB)
echo [4] Leaving Office     (Export DB + Commit & Push Git updates)
echo [5] Exit
echo ================================================================
set /p CHOICE="Enter your choice (1-5): "

if "%CHOICE%"=="1" goto START_HOME
if "%CHOICE%"=="2" goto LEAVE_HOME
if "%CHOICE%"=="3" goto START_OFFICE
if "%CHOICE%"=="4" goto LEAVE_OFFICE
if "%CHOICE%"=="5" exit /b
echo.
echo [ERROR] Invalid choice, please try again.
pause
cls
goto MENU

:: ================================================================
:: OPTION 1: STARTING AT HOME
:: ================================================================
:START_HOME
cls
echo ================================================================
echo [STAGE: STARTING AT HOME]
echo ================================================================

echo 1. Pulling latest code from GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Git pull had issues. Check network or merge conflicts.
) else (
    echo [SUCCESS] Git code is up-to-date!
)
echo.

echo 2. Setting environment configuration to HOME (.env.home)...
if exist "backend\.env.home" (
    copy /y "backend\.env.home" "backend\.env" >nul
    echo [SUCCESS] backend\.env configured for Home PC!
) else (
    echo [WARNING] backend\.env.home not found!
)
echo.

echo 3. Checking for latest database snapshot to import...
if exist "db_backups\latest_examination_data.dump" (
    echo Importing latest database snapshot into local PostgreSQL...
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

    set PGPASSWORD=%CURRENT_PG_PASSWORD%
    psql -U %CURRENT_PG_USER% -h localhost -p 5432 -c "CREATE DATABASE %CURRENT_PG_DB%;" 2>nul
    pg_restore -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% --clean --if-exists -v "db_backups\latest_examination_data.dump" 2>nul
    echo [SUCCESS] Home PostgreSQL database is ready!
) else (
    echo [INFO] No DB dump file found in db_backups\. Skipping DB restore.
)

echo.
echo ================================================================
echo [READY] Setup complete. You can now run start.bat!
echo ================================================================
pause
goto MENU

:: ================================================================
:: OPTION 2: LEAVING HOME
:: ================================================================
:LEAVE_HOME
cls
echo ================================================================
echo [STAGE: LEAVING HOME]
echo ================================================================

echo 1. Exporting local PostgreSQL database snapshot...
if not exist "db_backups" mkdir "db_backups"

for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

set PGPASSWORD=%CURRENT_PG_PASSWORD%
pg_dump -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% -F c -b -v -f "db_backups\latest_examination_data.dump" 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] DB snapshot saved to db_backups\latest_examination_data.dump
) else (
    echo [WARNING] Database export skipped or failed.
)
echo.

echo 2. Pushing code changes to GitHub...
set /p COMMIT_MSG="Enter commit summary (or press Enter for default): "
set CURRENT_TIME=%TIME: =0%
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Home sync: %DATE% %CURRENT_TIME%

git add .
git commit -m "%COMMIT_MSG%"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Code pushed to https://github.com/roli-reeshik/VidyaMarksPro!
) else (
    echo [ERROR] Git push failed. Please verify your connection.
)

echo.
echo ================================================================
echo [READY] All updates saved. You can now safely disconnect the drive!
echo ================================================================
pause
goto MENU

:: ================================================================
:: OPTION 3: STARTING OFFICE
:: ================================================================
:START_OFFICE
cls
echo ================================================================
echo [STAGE: STARTING AT OFFICE]
echo ================================================================

echo 1. Pulling latest code from GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Git pull had issues. Check network or merge conflicts.
) else (
    echo [SUCCESS] Git code is up-to-date!
)
echo.

echo 2. Setting environment configuration to OFFICE (.env.office)...
if exist "backend\.env.office" (
    copy /y "backend\.env.office" "backend\.env" >nul
    echo [SUCCESS] backend\.env configured for Office PC (No password)!
) else (
    echo [WARNING] backend\.env.office not found!
)
echo.

echo 3. Checking for latest database snapshot to import...
if exist "db_backups\latest_examination_data.dump" (
    echo Importing latest database snapshot into local PostgreSQL...
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
    for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

    set PGPASSWORD=%CURRENT_PG_PASSWORD%
    psql -U %CURRENT_PG_USER% -h localhost -p 5432 -c "CREATE DATABASE %CURRENT_PG_DB%;" 2>nul
    pg_restore -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% --clean --if-exists -v "db_backups\latest_examination_data.dump" 2>nul
    echo [SUCCESS] Office PostgreSQL database is synchronized!
) else (
    echo [INFO] No DB dump file found in db_backups\. Skipping DB restore.
)

echo.
echo ================================================================
echo [READY] Setup complete. You can now run start.bat!
echo ================================================================
pause
goto MENU

:: ================================================================
:: OPTION 4: LEAVING OFFICE
:: ================================================================
:LEAVE_OFFICE
cls
echo ================================================================
echo [STAGE: LEAVING OFFICE]
echo ================================================================

echo 1. Exporting local PostgreSQL database snapshot...
if not exist "db_backups" mkdir "db_backups"

for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_PASSWORD',''))"') do set CURRENT_PG_PASSWORD=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_USER','postgres'))"') do set CURRENT_PG_USER=%%i
for /f "tokens=*" %%i in ('python -c "import os; from dotenv import load_dotenv; load_dotenv('backend/.env'); print(os.getenv('DB_NAME','vidya_examination_db'))"') do set CURRENT_PG_DB=%%i

set PGPASSWORD=%CURRENT_PG_PASSWORD%
pg_dump -U %CURRENT_PG_USER% -h localhost -p 5432 -d %CURRENT_PG_DB% -F c -b -v -f "db_backups\latest_examination_data.dump" 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] DB snapshot saved to db_backups\latest_examination_data.dump
) else (
    echo [WARNING] Database export skipped or failed.
)
echo.

echo 2. Pushing code changes to GitHub...
set /p COMMIT_MSG="Enter commit summary (or press Enter for default): "
set CURRENT_TIME=%TIME: =0%
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Office sync: %DATE% %CURRENT_TIME%

git add .
git commit -m "%COMMIT_MSG%"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Code pushed to https://github.com/roli-reeshik/VidyaMarksPro!
) else (
    echo [ERROR] Git push failed. Please verify your connection.
)

echo.
echo ================================================================
echo [READY] All updates saved. You can now safely disconnect the drive!
echo ================================================================
pause
goto MENU