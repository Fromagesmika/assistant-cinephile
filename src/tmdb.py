"""Accès à l'API TMDB (v3), avec cache disque.

Comme pour le LLM, chaque réponse est gardée dans cache/tmdb/ : relancer eval.py redonne
exactement les mêmes résultats d'outils, sans clé et même si TMDB a changé entre-temps.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_CACHE = RACINE / "cache" / "tmdb"
URL = "https://api.themoviedb.org/3"
LANGUE = "fr-FR"

load_dotenv(RACINE / ".env")


class ErreurTMDB(Exception):
    """Erreur renvoyée au modèle comme résultat d'outil, pour qu'il puisse se corriger."""


def appeler(chemin, **params):
    """GET sur l'API. Renvoie (données JSON, durée de l'appel d'origine en secondes)."""
    params = {"language": LANGUE, **params}
    empreinte = hashlib.sha256(json.dumps([chemin, params], sort_keys=True).encode()).hexdigest()
    fichier = DOSSIER_CACHE / f"{empreinte}.json"
    if fichier.exists():
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
        return donnees["reponse"], donnees["duree"]

    cle = os.getenv("TMDB_API_KEY")
    if not cle:
        raise RuntimeError("TMDB_API_KEY est vide : collez votre clé dans le fichier .env")
    debut = time.perf_counter()
    reponse = requests.get(f"{URL}{chemin}", params={**params, "api_key": cle}, timeout=30)
    duree = time.perf_counter() - debut
    if reponse.status_code == 404:
        corps = {"introuvable": True}
    else:
        reponse.raise_for_status()
        corps = reponse.json()

    DOSSIER_CACHE.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps({"reponse": corps, "duree": duree}, ensure_ascii=False), encoding="utf-8")
    return corps, duree


def _annee(date):
    return int(date[:4]) if date and date[:4].isdigit() else None


def rechercher(titre, type_oeuvre="film", annee=None):
    """Jusqu'à 5 œuvres dont le titre correspond. Renvoie (résultats, durée)."""
    if type_oeuvre == "serie":
        donnees, duree = appeler("/search/tv", query=titre, **({"first_air_date_year": annee} if annee else {}))
        cle_titre, cle_date = "name", "first_air_date"
    else:
        donnees, duree = appeler("/search/movie", query=titre, **({"year": annee} if annee else {}))
        cle_titre, cle_date = "title", "release_date"
    resultats = [
        {
            "tmdb_id": r["id"],
            "type": type_oeuvre,
            "titre": r.get(cle_titre),
            "titre_original": r.get("original_" + cle_titre),
            "annee": _annee(r.get(cle_date)),
            "resume": (r.get("overview") or "")[:300],
        }
        for r in donnees.get("results", [])[:5]
    ]
    return resultats, duree


def details(tmdb_id, type_oeuvre="film"):
    """Fiche d'une œuvre : année, durée, réalisation ou création, genres, acteurs principaux."""
    chemin = f"/tv/{tmdb_id}" if type_oeuvre == "serie" else f"/movie/{tmdb_id}"
    donnees, duree = appeler(chemin, append_to_response="credits")
    if donnees.get("introuvable"):
        raise ErreurTMDB(f"Aucune œuvre de type {type_oeuvre} avec l'identifiant TMDB {tmdb_id}.")
    equipe = donnees.get("credits", {}).get("crew", [])
    fiche = {
        "tmdb_id": donnees["id"],
        "type": type_oeuvre,
        "titre": donnees.get("title") or donnees.get("name"),
        "titre_original": donnees.get("original_title") or donnees.get("original_name"),
        "annee": _annee(donnees.get("release_date") or donnees.get("first_air_date")),
        "genres": [g["name"] for g in donnees.get("genres", [])],
        "acteurs": [a["name"] for a in donnees.get("credits", {}).get("cast", [])[:5]],
    }
    if type_oeuvre == "serie":
        fiche["createurs"] = [c["name"] for c in donnees.get("created_by", [])]
        fiche["saisons"] = donnees.get("number_of_seasons")
        fiche["episodes"] = donnees.get("number_of_episodes")
    else:
        fiche["realisation"] = [p["name"] for p in equipe if p.get("job") == "Director"]
        fiche["duree_minutes"] = donnees.get("runtime")
        # Box-office : TMDB met 0 quand le montant est inconnu ; on ne l'affiche pas plutôt
        # que de laisser le modèle conclure que le film n'a rien rapporté.
        if donnees.get("budget"):
            fiche["budget_dollars"] = donnees["budget"]
        if donnees.get("revenue"):
            fiche["recettes_mondiales_dollars"] = donnees["revenue"]
    return fiche, duree


def recommandations(tmdb_id, type_oeuvre="film", annee_min=None, annee_max=None):
    """Œuvres recommandées par TMDB à partir d'une œuvre, filtrées par années si demandé."""
    chemin = f"/tv/{tmdb_id}/recommendations" if type_oeuvre == "serie" else f"/movie/{tmdb_id}/recommendations"
    donnees, duree = appeler(chemin)
    if donnees.get("introuvable"):
        raise ErreurTMDB(f"Aucune œuvre de type {type_oeuvre} avec l'identifiant TMDB {tmdb_id}.")
    resultats = []
    for r in donnees.get("results", []):
        annee = _annee(r.get("release_date") or r.get("first_air_date"))
        if (annee_min and (annee is None or annee < annee_min)) or (annee_max and (annee is None or annee > annee_max)):
            continue
        resultats.append({"tmdb_id": r["id"], "type": type_oeuvre, "titre": r.get("title") or r.get("name"), "annee": annee})
        if len(resultats) == 5:
            break
    return resultats, duree
