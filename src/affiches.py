"""Affiches TMDB, stockées dans data/affiches/ (pour l'interface uniquement).

Une affiche absente est téléchargée à la première demande, puis relue sur le disque.
Les fiches TMDB consultées ici passent par le cache de src/tmdb.py.
"""
from pathlib import Path

import requests

from src import tmdb

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "data" / "affiches"
URL_IMAGES = "https://image.tmdb.org/t/p/w342"


def chemin_local(tmdb_id, type_oeuvre="film"):
    return DOSSIER / f"{type_oeuvre}_{tmdb_id}.jpg"


def telecharger(tmdb_id, type_oeuvre="film"):
    """Renvoie le chemin de l'affiche sur le disque, ou None si TMDB n'en a pas."""
    chemin = chemin_local(tmdb_id, type_oeuvre)
    if chemin.exists():
        return chemin
    fiche, _ = tmdb.appeler(f"/tv/{tmdb_id}" if type_oeuvre == "serie" else f"/movie/{tmdb_id}")
    poster = fiche.get("poster_path")
    if not poster:
        return None
    reponse = requests.get(URL_IMAGES + poster, timeout=30)
    if reponse.status_code != 200:
        return None
    DOSSIER.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(reponse.content)
    return chemin


def affiche(tmdb_id, type_oeuvre="film"):
    """Comme telecharger, mais sans jamais lever d'erreur : l'interface doit s'afficher même hors ligne."""
    try:
        return telecharger(tmdb_id, type_oeuvre)
    except Exception:
        chemin = chemin_local(tmdb_id, type_oeuvre)
        return chemin if chemin.exists() else None
