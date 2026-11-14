"""Appel au LLM (API Gemini, format compatible OpenAI), avec cache disque et mesure des coûts.

Trois rôles, utilisés par tous les niveaux :
- envoyer les messages au modèle et récupérer la réponse ;
- mesurer tokens et latence (colonnes du tableau du sujet) ;
- garder chaque réponse dans cache/ : relancer eval.py redonne les mêmes chiffres,
  sans clé d'API et sans consommer de quota.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_CACHE = RACINE / "cache"
URL_API = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MAX_ESSAIS = 8

load_dotenv(RACINE / ".env")
MODELE = os.getenv("CHAT_MODEL") or "gemini-3.5-flash-lite"
INTERVALLE_MIN = float(os.getenv("LLM_MIN_INTERVAL") or 6)

_dernier_appel = 0.0  # instant du dernier appel réel, pour respecter le débit de l'offre gratuite


def _cle_cache(messages, format_json, essai, outils=None):
    """Empreinte de la requête : mêmes entrées = même fichier de cache.

    `essai` distingue les répétitions d'un même cas (utile pour pass^3, où il faut
    3 réponses indépendantes et non 3 fois la même réponse relue dans le cache).
    """
    requete = {"modele": MODELE, "messages": messages, "json": format_json, "essai": essai}
    if outils:  # ajouté seulement s'il y a des outils : les clés des niveaux 0 et 1 ne changent pas
        requete["outils"] = outils
    contenu = json.dumps(
        requete,
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


def _appeler_api(messages, format_json, outils=None):
    """Appel HTTP réel. Sur 429 ou erreur serveur, on attend de plus en plus longtemps."""
    global _dernier_appel

    cle = os.getenv("GEMINI_API_KEY")
    if not cle:
        raise RuntimeError("GEMINI_API_KEY est vide : collez votre clé dans le fichier .env")

    corps = {"model": MODELE, "messages": messages, "temperature": 0}
    if format_json:
        corps["response_format"] = {"type": "json_object"}
    if outils:
        corps["tools"] = outils

    for essai in range(MAX_ESSAIS):
        attente = INTERVALLE_MIN - (time.monotonic() - _dernier_appel)
        if attente > 0:
            time.sleep(attente)
        _dernier_appel = time.monotonic()

        debut = time.perf_counter()
        reponse = requests.post(
            URL_API,
            headers={"Authorization": f"Bearer {cle}"},
            json=corps,
            timeout=120,
        )
        latence = time.perf_counter() - debut

        if reponse.status_code == 429 or reponse.status_code >= 500:
            derniere_erreur = f"code HTTP {reponse.status_code} : {reponse.text[:300]}"
            pause = min(60, 2 ** (essai + 1))
            print(f"    API : code {reponse.status_code}, nouvel essai dans {pause} s", flush=True)
            time.sleep(pause)
            continue
        reponse.raise_for_status()

        donnees = reponse.json()
        message = donnees["choices"][0]["message"]
        return {
            "texte": message.get("content") or "",
            # Message brut, renvoyé tel quel au tour suivant : avec des outils, Gemini exige
            # de retrouver ses appels d'outils et leur signature (thought_signature).
            "message": message,
            "tokens_entree": donnees["usage"]["prompt_tokens"],
            "tokens_sortie": donnees["usage"]["completion_tokens"],
            # Le total peut aussi compter les tokens de raisonnement interne du modèle :
            # c'est lui qu'on retient comme coût, pour ne pas le sous-estimer.
            "tokens_total": donnees["usage"]["total_tokens"],
            "latence": latence,
            "modele": donnees.get("model", MODELE),
        }
    # Les réponses déjà obtenues restent dans le cache : si le quota du jour est épuisé,
    # il suffira de relancer eval.py plus tard pour continuer là où on s'est arrêté.
    raise RuntimeError(f"API Gemini indisponible après {MAX_ESSAIS} essais ; {derniere_erreur}")


def discuter(messages, format_json=False, essai=0, outils=None):
    """Renvoie la réponse du modèle : depuis le cache si elle existe, sinon depuis l'API.

    La latence stockée est celle de l'appel d'origine, donc le tableau de résultats ne
    change pas quand on relit le cache.
    """
    chemin = DOSSIER_CACHE / f"{_cle_cache(messages, format_json, essai, outils)}.json"
    if chemin.exists():
        return json.loads(chemin.read_text(encoding="utf-8"))

    resultat = _appeler_api(messages, format_json, outils)
    DOSSIER_CACHE.mkdir(exist_ok=True)
    chemin.write_text(json.dumps(resultat, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultat
