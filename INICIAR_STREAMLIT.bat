@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
)
if not exist ".venv\Scripts\python.exe" (
  echo ERRO: Python nao encontrado. Instale Python 3.10+ e tente novamente.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERRO ao instalar dependencias.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
