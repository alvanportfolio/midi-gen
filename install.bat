@echo off
REM ===========================================
REM  PianoRollStudio - Installation Launcher
REM  Launches PowerShell installer window
REM ===========================================

REM Launch PowerShell window directly and close CMD
start "" powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

REM Exit immediately
exit