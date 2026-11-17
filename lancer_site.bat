@echo off
rem Lance l'interface de l'assistant cinephile (http://localhost:8501)
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    echo Environnement introuvable, lancez d'abord :
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

rem Streamlit demande un email facultatif au premier lancement : on y repond une fois pour toutes
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo Lancement du site, il s'ouvre dans le navigateur
echo Pour l'arreter : fermez cette fenetre
".venv\Scripts\streamlit.exe" run app.py
pause
