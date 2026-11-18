@echo off
rem Lance l'interface de l'assistant cinephile (http://localhost:8501)
rem Au premier lancement, installe l'environnement Python (quelques minutes)
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python est introuvable. Installez Python 3.12 depuis https://www.python.org
        echo en cochant "Add python.exe to PATH", puis relancez ce fichier
        pause
        exit /b 1
    )
    echo Premier lancement : installation de l'environnement, quelques minutes...
    if not exist ".venv\Scripts\python.exe" python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo L'installation a echoue, voir les messages ci-dessus
        pause
        exit /b 1
    )
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Fichier .env cree : collez-y vos cles Gemini et TMDB pour poser de nouvelles questions
    echo Sans cle, les questions deja en cache fonctionnent
)

rem Streamlit demande un email facultatif au premier lancement : on y repond une fois pour toutes
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo Lancement du site, il s'ouvre dans le navigateur
echo Pour l'arreter : fermez cette fenetre
".venv\Scripts\python.exe" -m streamlit run app.py
pause
