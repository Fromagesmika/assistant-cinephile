"""Juge LLM de fidélité : la réponse ne dit-elle rien de plus que les passages fournis ?

Les règles de metrics.py vérifient qu'un fait attendu est présent, mais pas qu'il n'y a pas
d'invention à côté. Le juge couvre ce second point. Sa fiabilité se mesure contre vos
annotations humaines (scripts/calibrer_juge.py) : ne pas changer ce prompt après la calibration.
"""
from src.levels.level0 import lire_json
from src.levels.level1 import construire_contexte
from src.llm import discuter

PROMPT_JUGE = """Tu évalues la fidélité d'une réponse à ses sources. On te donne des extraits, une question et une réponse.

La réponse est fidèle si chacune de ses affirmations est explicitement soutenue par les extraits. Elle n'est pas fidèle si elle contient au moins un détail absent des extraits ou contredit par eux, même si ce détail est vrai dans la réalité.
Ne juge ni le style ni les numéros de citation.

Réponds uniquement avec un objet JSON de cette forme :
{"fidele": true ou false, "detail": "l'affirmation non soutenue, ou une chaîne vide"}"""


def juger(question, reponse, passages):
    """Renvoie (fidele, detail, tokens). Un verdict illisible compte comme non fidèle."""
    contenu = f"{construire_contexte(passages)}\n\nQuestion : {question}\n\nRéponse à évaluer : {reponse}"
    sortie = discuter(
        [{"role": "system", "content": PROMPT_JUGE}, {"role": "user", "content": contenu}],
        format_json=True,
    )
    donnees = lire_json(sortie["texte"]) or {}
    return donnees.get("fidele") is True, str(donnees.get("detail", "")), sortie["tokens_total"]
