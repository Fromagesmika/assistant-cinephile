"""Découpage du corpus, index de vecteurs et recherche dense.

La recherche est écrite à la main avec numpy : les vecteurs sont normalisés, donc la
similarité cosinus est un simple produit scalaire. Pour 156 pages, pas besoin de base vectorielle.
"""
import hashlib
import json
import re
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_INDEX = RACINE / "data" / "index"
DOSSIER_REQUETES = RACINE / "cache" / "requetes"

# Les modèles e5 attendent ces préfixes pour distinguer une question d'un passage.
MODELES = {
    "e5": {"nom": "intfloat/multilingual-e5-small", "requete": "query: ", "passage": "passage: "},
    "minilm": {"nom": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "requete": "", "passage": ""},
}

# Configuration retenue d'après scripts/compare_retrieval.py (voir results/choix_retrieval.md).
CONFIG = {"modele": "e5", "taille": 800, "chevauchement": 100}

SECTIONS_IGNOREES = {"notes et références", "références", "voir aussi", "liens externes", "bibliographie", "annexes"}
_modeles_charges = {}


def charger_corpus():
    with open(RACINE / "data" / "corpus.jsonl", encoding="utf-8") as f:
        return [json.loads(ligne) for ligne in f]


def _unites(texte, taille):
    """Découpe une page en (section, ligne) ; une ligne trop longue est coupée en phrases."""
    section = ""
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if not ligne:
            continue
        titre = re.fullmatch(r"=+\s*(.*?)\s*=+", ligne)
        if titre:
            section = titre.group(1)
            continue
        if section.lower() in SECTIONS_IGNOREES:
            continue
        if len(ligne) <= taille:
            yield section, ligne
        else:
            for phrase in re.split(r"(?<=[.!?…])\s+", ligne):
                yield section, phrase


def decouper(document, taille, chevauchement):
    """Regroupe les lignes d'une page en passages d'environ `taille` caractères.

    Chaque passage commence par le titre de l'œuvre et la section : sans cela, une phrase comme
    « Musique : Hans Zimmer » ne dirait pas de quel film elle parle, et serait introuvable.
    Le chevauchement répète la fin du passage précédent pour ne pas couper une idée en deux.
    """
    passages, courant, longueur, section_courante = [], [], 0, ""

    def emettre():
        corps = "\n".join(courant)
        entete = document["doc_id"] + (f" — {section_courante}" if section_courante else "")
        passages.append({
            "passage_id": f"{document['doc_id']}#{len(passages)}",
            "doc_id": document["doc_id"],
            "url": document["url"],
            "texte": f"{entete}\n{corps}",
        })

    for section, unite in _unites(document["texte"], taille):
        changement = bool(courant) and section != section_courante
        if courant and (changement or longueur + len(unite) > taille):
            emettre()
            # On garde la fin du passage comme début du suivant, sauf si la section change.
            reprise, cumul = [], 0
            if not changement:
                for precedent in reversed(courant):
                    if cumul + len(precedent) > chevauchement:
                        break
                    reprise.insert(0, precedent)
                    cumul += len(precedent)
            courant, longueur = reprise, cumul
        courant.append(unite)
        longueur += len(unite)
        section_courante = section
    if courant:
        emettre()
    return passages


def tous_les_passages(taille, chevauchement):
    return [p for doc in charger_corpus() for p in decouper(doc, taille, chevauchement)]


def _modele(cle):
    # Import tardif : relire le cache ne charge ni torch ni le modèle, ce qui est bien plus rapide.
    if cle not in _modeles_charges:
        from sentence_transformers import SentenceTransformer

        _modeles_charges[cle] = SentenceTransformer(MODELES[cle]["nom"], device="cpu")
    return _modeles_charges[cle]


def encoder(textes, cle, genre, afficher=False):
    """Transforme des textes en vecteurs normalisés. `genre` vaut « requete » ou « passage »."""
    prefixe = MODELES[cle][genre]
    return _modele(cle).encode(
        [prefixe + t for t in textes],
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=afficher,
        convert_to_numpy=True,
    ).astype(np.float32)


def chemin_index(modele, taille, chevauchement):
    return DOSSIER_INDEX / f"{modele}_{taille}_{chevauchement}.npy"


def vecteurs_index(modele, taille, chevauchement, passages):
    """Lit les vecteurs enregistrés, ou les calcule une fois pour toutes."""
    chemin = chemin_index(modele, taille, chevauchement)
    if chemin.exists():
        vecteurs = np.load(chemin)
        if len(vecteurs) == len(passages):
            return vecteurs
    vecteurs = encoder([p["texte"] for p in passages], modele, "passage", afficher=True)
    DOSSIER_INDEX.mkdir(parents=True, exist_ok=True)
    np.save(chemin, vecteurs)
    return vecteurs


def vecteur_requete(question, modele):
    """Vecteur d'une question, gardé sur disque : les résultats sont identiques d'une machine à l'autre."""
    chemin = DOSSIER_REQUETES / f"{modele}.json"
    memoire = json.loads(chemin.read_text(encoding="utf-8")) if chemin.exists() else {}
    cle = hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    if cle not in memoire:
        memoire[cle] = encoder([question], modele, "requete")[0].tolist()
        DOSSIER_REQUETES.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(memoire), encoding="utf-8")
    return np.array(memoire[cle], dtype=np.float32)


class Index:
    def __init__(self, modele, taille, chevauchement):
        self.modele = modele
        self.passages = tous_les_passages(taille, chevauchement)
        self.vecteurs = vecteurs_index(modele, taille, chevauchement, self.passages)

    def rechercher(self, question, k=5):
        """Renvoie les k passages les plus proches, du plus similaire au moins similaire."""
        scores = self.vecteurs @ vecteur_requete(question, self.modele)
        meilleurs = np.argsort(-scores, kind="stable")[:k]
        return [{**self.passages[i], "score": round(float(scores[i]), 4)} for i in meilleurs]


_index_principal = None


def index_principal():
    """L'index de la configuration retenue, chargé une seule fois."""
    global _index_principal
    if _index_principal is None:
        _index_principal = Index(CONFIG["modele"], CONFIG["taille"], CONFIG["chevauchement"])
    return _index_principal
