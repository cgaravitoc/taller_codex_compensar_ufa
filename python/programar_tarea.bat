@echo off
setlocal
rem Registra SOLO al ejecutar este archivo sin --dry-run. No requiere contrasenas.
rem Modo InteractiveToken: se ejecuta cuando el usuario tiene sesion iniciada.
if /I "%~1"=="--dry-run" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0programar_tarea.ps1" -DryRun
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0programar_tarea.ps1"
)
exit /b %errorlevel%
