@echo off
cd /d "%~dp0"
py -3 stencil_gui.py
if errorlevel 1 pause
