@echo off
chcp 65001 >nul
title EURO_GOALS PRO+ — Local Control Panel v3.1
color 0B
setlocal enabledelayedexpansion

set VERSION=9.9.6
set APPNAME=EURO_GOALS PRO+
set LOGDIR=logs
set LOGFILE=%LOGDIR%\local_run_%DATE:~0,10%.log
set PYTHON_ENV=venv\Scripts\activate
set ENV_MODE=LOCAL

:: ==========================================================
:: EURO_GOALS PRO+ — Local Control Panel v3.1 (Live Status + ENV Toggle)
:: ==========================================================
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

:MENU
cls
echo ==========================================================
echo       %APPNAME% — Control Panel  [v%VERSION%]
echo ==========================================================
echo   Current Environment : %ENV_MODE%
echo ----------------------------------------------------------
:: === Check if uvicorn is running ===
set STATUS=🔴 STOPPED
for /f "tokens=1" %%a in ('tasklist /FI "IMAGENAME eq uvicorn.exe" /NH ^| find /I "uvicorn.exe"') do (
    if "%%a"=="uvicorn.exe" set STATUS=🟢 RUNNING
)
echo   Server Status       : %STATUS%
echo   Active Directory    : %cd%
echo   Log File            : %LOGFILE%
echo ==========================================================
echo   1. 🚀  Start Local Server
echo   2. 🛑  Stop Server
echo   3. 📜  View Latest Logs
echo   4. 🌐  Open in Browser
echo   5. 🧠  Check Python Environment
echo   6. ⬆️  Update Version Info
echo   7. 🔁  Refresh Status
echo   8. ❌  Exit
echo   9. 🌍  Switch Environment (Local / Render)
echo ==========================================================
echo.
set /p choice="Select an option (1-9): "

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto VIEW
if "%choice%"=="4" goto OPEN
if "%choice%"=="5" goto CHECK
if "%choice%"=="6" goto UPDATE
if "%choice%"=="7" goto MENU
if "%choice%"=="8" goto END
if "%choice%"=="9" goto TOGGLE
goto MENU

:START
cls
echo ==========================================================
echo  [STARTING SERVER] %APPNAME% v%VERSION% (%ENV_MODE%)
echo ==========================================================
if not exist "venv\Scripts\activate" (
    echo [!] Virtual environment not found, creating...
    python -m venv venv
)
call %PYTHON_ENV%
echo [✓] Virtual environment activated.
echo [i] Checking dependencies...
pip show fastapi >nul 2>&1 || pip install fastapi
pip show uvicorn >nul 2>&1 || pip install uvicorn
pip show jinja2 >nul 2>&1 || pip install jinja2
pip show python-dotenv >nul 2>&1 || pip install python-dotenv
echo ----------------------------------------------------------
echo [✓] Dependencies verified.
echo [i] Starting server and writing logs to %LOGFILE% ...
if "%ENV_MODE%"=="LOCAL" (
    start /MIN cmd /c "uvicorn main:app --reload > %LOGFILE% 2>&1"
    start http://127.0.0.1:8000
) else (
    echo [Render Mode] External environment active — skipping local launch.
)
pause
goto MENU

:STOP
cls
echo ==========================================================
echo  [STOPPING SERVER]
echo ==========================================================
taskkill /f /im uvicorn.exe >nul 2>&1
echo [✓] Uvicorn server stopped.
pause
goto MENU

:VIEW
cls
echo ==========================================================
echo  [VIEW LOG FILE]
echo ==========================================================
if exist "%LOGFILE%" (
    start notepad "%LOGFILE%"
) else (
    echo [x] Log file not found.
)
pause
goto MENU

:OPEN
cls
echo ==========================================================
echo  [OPEN IN BROWSER]
echo ==========================================================
if "%ENV_MODE%"=="LOCAL" (
    start http://127.0.0.1:8000
) else (
    start https://eurogoals-proplus.onrender.com
)
echo [✓] Browser opened.
pause
goto MENU

:CHECK
cls
echo ==========================================================
echo  [ENVIRONMENT STATUS]
echo ==========================================================
if exist "venv\Scripts\activate" (
    echo [✓] Virtual environment exists.
) else (
    echo [x] Virtual environment missing.
)
where python
pip list | findstr fastapi
pip list | findstr uvicorn
pause
goto MENU

:UPDATE
cls
echo ==========================================================
echo  [UPDATE VERSION INFO]
echo ==========================================================
set /p NEWVER="Enter new version (e.g. 9.9.7): "
if not "%NEWVER%"=="" (
    set VERSION=%NEWVER%
    echo [✓] Version updated to v%VERSION%.
)
pause
goto MENU

:TOGGLE
if "%ENV_MODE%"=="LOCAL" (
    set ENV_MODE=RENDER
) else (
    set ENV_MODE=LOCAL
)
echo [✓] Environment switched to %ENV_MODE%.
timeout /t 1 >nul
goto MENU

:END
cls
echo ==========================================================
echo  [EURO_GOALS] Session Ended
echo ==========================================================
echo Bye Pierros 👋 — Control Panel Closed.
timeout /t 2 >nul
exit
