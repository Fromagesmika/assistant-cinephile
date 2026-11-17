@echo off
rem Lance l'interface de l'assistant cinéphile (http://localhost:8501)
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    echo Environnement introuvable : lancez d'abord
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Lancement du site, il s'ouvre dans le navigateur
echo Pour l'arreter : fermez cette fenetre ou faites Ctrl+C
".venv\Scripts\streamlit.exe" run app.py
pause
