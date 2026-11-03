@echo off
REM =====================================================================
REM  Downloader Bot - one-click build of the Windows Setup.exe
REM  Requirements: Python 3.10+, NSIS 3.x (makensis on PATH)
REM  Output: dist\DownloaderBot.exe  and  DownloaderBot-Setup-1.0.0.exe
REM =====================================================================
setlocal enabledelayedexpansion

echo ============================================
echo   Downloader Bot - Setup.exe builder
echo ============================================

REM --- prerequisites ---------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install Python 3.10+ first.
    pause & exit /b 1
)
where makensis >nul 2>&1
if errorlevel 1 (
    echo [ERROR] NSIS (makensis) not found on PATH.
    echo         Download NSIS 3.x from https://nsis.sourceforge.io and re-run.
    pause & exit /b 1
)

REM --- venv + deps -----------------------------------------------------------
if not exist ".venv-build" (
    echo [1/4] Creating virtualenv...
    python -m venv .venv-build
)
call ".venv-build\Scripts\activate.bat"

echo [2/4] Installing dependencies...
pip install --upgrade pip >nul
pip install -r requirements.txt -r requirements-gui.txt pyinstaller

REM --- build the frozen app ---------------------------------------------------
echo [3/4] Building frozen executable with PyInstaller...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
pyinstaller --clean --noconfirm build\downloader-bot.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller failed.
    pause & exit /b 1
)

REM --- build the Setup.exe installer ----------------------------------------
echo [4/4] Building Setup.exe with NSIS...
cd /d "%~dp0"
makensis build\installer.nsi
if errorlevel 1 (
    echo [ERROR] NSIS failed.
    pause & exit /b 1
)

echo.
echo ============================================
echo   DONE - Setup.exe built:
echo   %CD%\DownloaderBot-Setup-1.0.0.exe
echo ============================================
pause
