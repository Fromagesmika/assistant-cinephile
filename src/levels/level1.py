"""Niveau 1 : RAG. Le modèle répond uniquement à partir des passages retrouvés et les cite.

Déroulé : rechercher 5 passages, les numéroter, demander au modèle une réponse citée, puis
contrôler par le code que chaque réponse s'appuie sur au moins un passage réellement fourni.
"""
import re

from src.levels.level0 import lire_json, lire_sortie
from src.llm import MODELE, discuter
from src.rag import index_principal

K = 5

PROMPT_SYSTEME = """Tu es un assistant cinéphile francophone. Tu réponds à partir des extraits fournis, et uniquement à partir d'eux, même si tu crois connaître la réponse.

Règles :
- Dans le champ "texte", chaque phrase se termine par le numéro de l'extrait qui la justifie. Exemple : "La musique est composée par Hans Zimmer [2]. Le film dure 148 minutes [4]." Une phrase sans numéro est interdite.
- Ne donne aucun détail absent des extraits.
- Si les extraits ne contiennent pas la réponse, utilise le statut "abstention".
- Si le titre demandé désigne plusieurs œuvres présentes dans les extraits et que la question ne précise pas laquelle, ou si aucune œuvre n'est nommée, utilise le statut "precision" et pose une question.
- Si la demande n'a aucun rapport avec le cinéma ou les séries, utilise le statut "refus".
- Sinon, utilise le statut "reponse" et réponds en une à trois phrases.

Réponds uniquement avec un objet JSON de cette forme :
{"statut": "reponse" | "abstention" | "precision" | "refus", "texte": "ta réponse en français, avec ses citations", "sources": [numéros des extraits utilisés]}"""


def construire_contexte(passages):
    return "\n\n".join(f"Extrait [{i}] : {p['texte']}" for i, p in enumerate(passages, start=1))


def numeros_cites(texte, donnees, nombre_passages):
    """Numéros cités dans le texte ou la liste `sources`, sans ceux qui ne correspondent à aucun extrait."""
    # Une citation peut regrouper plusieurs extraits : [1] ou [1, 4].
    numeros = {int(n) for groupe in re.findall(r"\[([\d\s,]+)\]", texte) for n in re.findall(r"\d+", groupe)}
    sources = donnees.get("sources", []) if isinstance(donnees, dict) else []
    if isinstance(sources, list):
        # Le modèle écrit parfois les numéros comme du texte : ["1"] au lieu de [1].
        numeros |= {int(n) for n in sources if str(n).isdigit()}
    return sorted(n for n in numeros if 1 <= n <= nombre_passages)


def repondre(question, essai=0):
    passages = index_principal().rechercher(question, k=K)
    messages = [
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": f"{construire_contexte(passages)}\n\nQuestion : {question}"},
    ]
    sortie = discuter(messages, format_json=True, essai=essai)
    statut, texte = lire_sortie(sortie["texte"])
    numeros = numeros_cites(texte, lire_json(sortie["texte"]), len(passages))

    # Règle vérifiée par le code : pas de citation valide, pas de réponse.
    citation_manquante = statut == "reponse" and not numeros
    if citation_manquante:
        statut = "abstention"
        texte = "Je ne peux pas répondre : aucune source ne justifie une réponse."

    cites = [passages[n - 1] for n in numeros] if statut == "reponse" else []
    return {
        "niveau": 1,
        "statut": statut,
        "texte": texte,
        "sources": sorted({p["doc_id"] for p in cites}),
        "passages": passages,
        "etapes": [
            {"type": "recherche", "k": K, "resultats": [(p["passage_id"], p["score"]) for p in passages]},
            {"type": "llm", "modele": sortie.get("modele", MODELE), "citation_manquante": citation_manquante},
        ],
        "tokens": sortie["tokens_total"],
        "latence": sortie["latence"],
    }
