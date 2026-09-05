@echo off
echo VELVET VICE - LTX legacy duplicate cleanup
echo Close ComfyUI before continuing.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Cleanup-Legacy-LTX-Installs.ps1"
pause
