"""Niveau 0 : LLM seul, avec un prompt soigné, sans documents ni outils.

C'est la référence à battre. Le modèle répond avec ce qu'il a appris à l'entraînement.
"""
import json

from src.llm import MODELE, discuter

PROMPT_SYSTEME = """Tu es un assistant cinéphile francophone. Tu réponds aux questions sur les films et les séries.

Règles :
- Réponds uniquement à partir de ce que tu sais avec certitude. N'invente jamais de fait.
- Si tu ne connais pas la réponse ou si tu n'es pas sûr, ne devine pas : utilise le statut "abstention".
- Si la demande est trop vague pour y répondre (par exemple un titre qui désigne plusieurs œuvres, ou aucun film précisé), utilise le statut "precision" et pose une question.
- Si la demande n'a aucun rapport avec le cinéma ou les séries, utilise le statut "refus".
- Sinon, utilise le statut "reponse" et réponds en une à trois phrases.

Réponds uniquement avec un objet JSON de cette forme :
{"statut": "reponse" | "abstention" | "precision" | "refus", "texte": "ta réponse en français"}"""


def lire_sortie(texte_brut):
    """Lit le JSON renvoyé par le modèle.

    Si le JSON est invalide, on garde le texte et on le compte comme une réponse classique :
    un modèle mal formaté ne doit pas être récompensé par une abstention automatique.
    Certains modèles entourent le JSON de ```json ... ``` : on retire ces marques avant de lire.
    """
    try:
        nettoye = texte_brut.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        donnees = json.loads(nettoye)
        statut = donnees.get("statut", "reponse")
        if statut not in {"reponse", "abstention", "precision", "refus"}:
            statut = "reponse"
        return statut, str(donnees.get("texte", ""))
    except (json.JSONDecodeError, AttributeError):
        return "reponse", texte_brut


def repondre(question, essai=0):
    """Renvoie la réponse et sa trace. Tous les niveaux auront cette même forme de sortie."""
    messages = [
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": question},
    ]
    sortie = discuter(messages, format_json=True, essai=essai)
    statut, texte = lire_sortie(sortie["texte"])
    return {
        "niveau": 0,
        "statut": statut,
        "texte": texte,
        "sources": [],  # le niveau 0 ne cite rien : il n'a aucun document
        "etapes": [{"type": "llm", "modele": sortie.get("modele", MODELE)}],
        "tokens": sortie["tokens_total"],
        "latence": sortie["latence"],
    }
