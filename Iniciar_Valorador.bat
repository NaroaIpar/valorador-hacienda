@echo off
echo ==========================================
echo   Iniciando el Valorador de Vehiculos...
echo   Por favor, espera unos segundos.
echo ==========================================

REM Entramos en la carpeta donde está este archivo
cd /d "%~dp0"

REM Activamos tu entorno virtual (asumiendo que se llama .venv)
call .venv\Scripts\activate

REM Arrancamos la aplicación web
streamlit run app.py