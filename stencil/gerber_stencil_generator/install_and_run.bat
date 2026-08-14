@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
if errorlevel 1 goto :python_error
py -3 -m pip install --upgrade pip
if errorlevel 1 goto :install_error
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto :install_error
py -3 stencil_gui.py
exit /b 0
:python_error
echo.
echo Python 3.12 or newer is required.
pause
exit /b 1
:install_error
echo.
echo Installation failed. Check the internet connection and Python installation.
pause
exit /b 1
