"""Trace de chaque exécution, en JSONL (une ligne JSON par exécution).

Le sujet demande : étapes, outils, arguments, tokens, durée. Au niveau 0, il n'y a qu'une
étape et aucun outil ; le format reste le même pour pouvoir comparer tous les niveaux.
"""
import json
from pathlib import Path

DOSSIER_TRACES = Path(__file__).resolve().parent.parent / "traces"


def ecrire_trace(niveau, trace):
    DOSSIER_TRACES.mkdir(exist_ok=True)
    with open(DOSSIER_TRACES / f"niveau{niveau}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False) + "\n")


def vider_traces(niveau):
    """Repart d'un fichier vide, pour que les traces correspondent à la dernière évaluation."""
    (DOSSIER_TRACES / f"niveau{niveau}.jsonl").unlink(missing_ok=True)
