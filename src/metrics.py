"""Notation d'un cas de test, écrite sans framework.

Chaque fonction est volontairement simple : elle reçoit la sortie d'un niveau et un cas de
tests.jsonl, puis renvoie vrai ou faux. Les règles reposent sur des faits attendus ; le juge
LLM calibré sur 20 cas (pour la fidélité aux sources) arrivera avec le niveau 1.
"""
import re
import unicodedata


def normaliser(texte):
    """Minuscules, sans accents, ponctuation réduite : « Émile-Zola » devient « emile zola »."""
    texte = unicodedata.normalize("NFKD", texte.lower())
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return texte.strip()


def contient(texte, expression):
    """Vrai si l'expression apparaît comme suite de mots entiers (« 12 » ne valide pas « 120 »)."""
    return f" {normaliser(expression)} " in f" {normaliser(texte)} "


def reponse_exacte(sortie, cas):
    """Le statut doit être « reponse », et chaque groupe de faits attendus doit être présent.

    `attendu` est une liste de groupes ; dans un groupe, une seule variante suffit.
    Exemple : [["Bong Joon-ho", "Bong Joon ho"]] accepte les deux graphies.
    """
    if sortie["statut"] != "reponse":
        return False
    return all(any(contient(sortie["texte"], v) for v in groupe) for groupe in cas["attendu"])


def source_citee(sortie, cas):
    """Au moins une source attendue figure parmi les sources citées (à partir du niveau 1)."""
    return bool(set(sortie["sources"]) & set(cas["sources"]))


def abstention_correcte(sortie):
    return sortie["statut"] == "abstention"


def precision_ou_refus_correct(sortie, cas):
    """Vérifie le comportement attendu pour un cas ambigu (« precision ») ou hors sujet (« refus »)."""
    return sortie["statut"] == cas["comportement"]


def moyenne(valeurs):
    """Moyenne d'une liste ; None si elle est vide (affiché « — » dans le tableau)."""
    valeurs = list(valeurs)
    return sum(valeurs) / len(valeurs) if valeurs else None
