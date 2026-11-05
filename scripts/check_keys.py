"""Vérifie que les clés du fichier .env fonctionnent, sans jamais les afficher.

Lancement : python scripts/check_keys.py
"""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
tout_va_bien = True


def rapport(nom, ok, detail):
    global tout_va_bien
    tout_va_bien = tout_va_bien and ok
    print(f"[{'OK' if ok else 'ERREUR'}] {nom} : {detail}")


cle_gemini = os.getenv("GEMINI_API_KEY")
if not cle_gemini:
    rapport("Gemini", False, "clé vide dans .env")
else:
    # Requête de liste des modèles : elle vérifie la clé sans consommer de tokens.
    r = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/openai/models",
        headers={"Authorization": f"Bearer {cle_gemini}"},
        timeout=30,
    )
    rapport("Gemini", r.status_code == 200, f"code HTTP {r.status_code}")
    if r.status_code == 200:
        modele = os.getenv("CHAT_MODEL") or "gemini-3.5-flash-lite"
        disponibles = [m["id"].removeprefix("models/") for m in r.json()["data"]]
        rapport("Modèle", modele in disponibles, modele)

cle_tmdb = os.getenv("TMDB_API_KEY")
if not cle_tmdb:
    rapport("TMDB", False, "clé vide dans .env")
else:
    r = requests.get(
        "https://api.themoviedb.org/3/configuration",
        params={"api_key": cle_tmdb},
        timeout=30,
    )
    rapport("TMDB", r.status_code == 200, f"code HTTP {r.status_code}")

sys.exit(0 if tout_va_bien else 1)
