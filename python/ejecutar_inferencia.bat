@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Falta .venv. Revise guia\index.html.
  exit /b 1
)
if not exist "logs" mkdir "logs"
".venv\Scripts\python.exe" "python\inferencia.py" --desde 2026-06-16 >> "logs\tarea.log" 2>&1
exit /b %errorlevel%
