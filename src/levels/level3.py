"""Niveau 3 : extension « RAG avancé », mesurée contre le niveau 2.

Défaut observé au niveau 2 : l'agent reformule les questions en mots-clés, souvent sans accents,
et la recherche dense retrouve moins bien les extraits (Recall@5 de 93 % au niveau 1, 71 % au
niveau 2). Correction : la recherche documentaire de l'agent devient hybride (BM25 + dense) avec
reranking par un cross-encoder (src/hybride.py ; choix justifié dans results/choix_hybride.md).

Tout le reste est identique au niveau 2 (prompt, outils, boucle, règles, confirmations) :
la différence mesurée entre les deux niveaux vient donc de la recherche seule.
"""
from src.hybride import index_hybride
from src.levels import level2


class Session(level2.Session):
    niveau = 3

    @staticmethod
    def rechercher_passages(requete, k):
        return index_hybride().rechercher(requete, k=k, mode="hybride_rerank")


def repondre(question, essai=0, liste=None, confirmer=level2.refuser_tout):
    return level2.repondre(question, essai=essai, liste=liste, confirmer=confirmer, classe=Session)
