"""Recherche hybride avec reranking : candidats BM25 + dense, puis reclassement par un cross-encoder.

BM25 et la fusion sont écrits sans framework ; le cross-encoder est un petit modèle ouvert.

Pourquoi : au niveau 2, l'agent reformule les questions en mots-clés,
souvent sans accents (« Cleo de 5 a 7 »). La recherche dense y est sensible ; BM25, qui compare
des mots normalisés (minuscules, sans accents), ne l'est pas. La fusion garde le meilleur des deux.

- BM25 : score classique de Robertson (k1 = 1,5 ; b = 0,75) sur un index inversé.
- RRF : score = somme sur les deux classements de 1 / (60 + rang). Pas de poids à régler,
  et les deux échelles de scores (cosinus et BM25) n'ont pas besoin d'être comparables.
- Reranking (configuration retenue) : l'union des 20 meilleurs candidats de chaque recherche
  est relue par un cross-encoder multilingue, qui lit la question et l'extrait ensemble.
  La fusion RRF seule dégradait les questions bien formulées (voir results/choix_hybride.md) ;
  le cross-encoder garde ce que trouvent les deux recherches sans cet inconvénient.
"""
import math
from collections import Counter, defaultdict

import numpy as np

from src.metrics import normaliser
from src.rag import index_principal, vecteur_requete

K1, B = 1.5, 0.75
K_RRF = 60
CANDIDATS = 50  # profondeur de chaque classement avant fusion RRF
CANDIDATS_RERANK = 20  # profondeur de chaque classement avant reranking
MODELE_RERANK = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"  # multilingue, entraîné sur mMARCO
_reranker = None

# Mots trop fréquents pour aider à distinguer un passage (après normalisation, sans accents).
MOTS_VIDES = set("""
le la les l un une des de du d et ou en au aux a à est sont ete etait qui que quoi qu quel quelle quels
quelles ce cet cette ces se sa son ses il elle ils elles on pour par sur dans avec sans ne pas plus
y t comment combien pourquoi quand ou dont lui leur leurs film films serie series
""".split())


def mots(texte):
    return [m for m in normaliser(texte).split() if len(m) > 1 and m not in MOTS_VIDES]


class BM25:
    def __init__(self, textes):
        self.longueurs = np.array([0] * len(textes), dtype=np.float32)
        self.postings = defaultdict(list)  # mot -> [(passage, fréquence)]
        for i, texte in enumerate(textes):
            compte = Counter(mots(texte))
            self.longueurs[i] = sum(compte.values())
            for mot, frequence in compte.items():
                self.postings[mot].append((i, frequence))
        self.moyenne = float(self.longueurs.mean())
        n = len(textes)
        self.idf = {m: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for m, p in self.postings.items()}

    def scores(self, requete):
        scores = np.zeros(len(self.longueurs), dtype=np.float32)
        for mot in set(mots(requete)):
            for i, frequence in self.postings.get(mot, ()):
                norme = K1 * (1 - B + B * self.longueurs[i] / self.moyenne)
                scores[i] += self.idf[mot] * frequence * (K1 + 1) / (frequence + norme)
        return scores


class IndexHybride:
    def __init__(self):
        self.dense = index_principal()
        self.passages = self.dense.passages
        self.bm25 = BM25([p["texte"] for p in self.passages])

    def classements(self, requete, profondeur=CANDIDATS):
        dense = self.dense.vecteurs @ vecteur_requete(requete, self.dense.modele)
        lexical = self.bm25.scores(requete)
        return (np.argsort(-dense, kind="stable")[:profondeur], np.argsort(-lexical, kind="stable")[:profondeur])

    def rechercher(self, requete, k=5, mode="hybride_rerank"):
        """mode : « hybride_rerank » (retenu), « dense_rerank », « hybride » (RRF), « dense » ou « bm25 »."""
        if mode.endswith("_rerank"):
            dense, lexical = self.classements(requete, CANDIDATS_RERANK)
            candidats = [int(i) for i in dense]
            if mode == "hybride_rerank":
                candidats = list(dict.fromkeys(candidats + [int(i) for i in lexical]))
            scores = reranker().predict([(requete, self.passages[i]["texte"]) for i in candidats])
            ordre = np.argsort(-scores, kind="stable")[:k]
            return [{**self.passages[candidats[j]], "score": round(float(scores[j]), 4)} for j in ordre]
        dense, lexical = self.classements(requete)
        if mode == "dense":
            ordre = list(dense)
        elif mode == "bm25":
            ordre = list(lexical)
        else:
            fusion = defaultdict(float)
            for classement in (dense, lexical):
                for rang, i in enumerate(classement, start=1):
                    fusion[int(i)] += 1 / (K_RRF + rang)
            ordre = sorted(fusion, key=lambda i: (-fusion[i], i))
        return [{**self.passages[int(i)], "score": None} for i in ordre[:k]]


def reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder  # import tardif : torch est long à charger

        _reranker = CrossEncoder(MODELE_RERANK, device="cpu")
    return _reranker


_index = None


def index_hybride():
    global _index
    if _index is None:
        _index = IndexHybride()
    return _index
