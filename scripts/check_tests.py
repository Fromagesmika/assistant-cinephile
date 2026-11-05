"""Contrôle le jeu de test avant toute évaluation.

Vérifie les minimums du sujet (40 cas et leur répartition) et surtout que chaque réponse
attendue se trouve bien dans le document source indiqué. Sans ce contrôle, une erreur dans
tests.jsonl passerait pour une erreur du modèle.

Lancement : python scripts/check_tests.py
"""
import collections
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src.metrics import contient  # noqa: E402

MINIMUMS = {"document": 20, "absent": 5, "tache": 10, "ambigu": 5}

with open(RACINE / "tests.jsonl", encoding="utf-8") as f:
    tests = [json.loads(l) for l in f if l.strip()]
with open(RACINE / "data" / "corpus.jsonl", encoding="utf-8") as f:
    corpus = {d["doc_id"]: d for d in map(json.loads, f)}

erreurs = []
if len({c["id"] for c in tests}) != len(tests):
    erreurs.append("identifiants en double")

nombre = collections.Counter(c["type"] for c in tests)
for type_cas, minimum in MINIMUMS.items():
    if nombre[type_cas] < minimum:
        erreurs.append(f"{type_cas} : {nombre[type_cas]} cas, minimum {minimum}")

for cas in tests:
    if cas["type"] == "document":
        documents = [corpus.get(s) for s in cas["sources"]]
        if None in documents:
            erreurs.append(f"{cas['id']} : source absente du corpus {cas['sources']}")
            continue
        for groupe in cas["attendu"]:
            if not any(contient(d["texte"], v) for d in documents for v in groupe):
                erreurs.append(f"{cas['id']} : {groupe} introuvable dans {cas['sources']}")
    if cas["type"] == "absent":
        # Le film ou le fait visé ne doit apparaître nulle part dans le corpus.
        for terme in cas["termes_absents"]:
            trouves = [d["doc_id"] for d in corpus.values() if contient(d["texte"], terme)]
            if trouves:
                erreurs.append(f"{cas['id']} : « {terme} » présent dans {trouves[:3]}")

print(f"{len(tests)} cas : {dict(nombre)}")
print("Par strate :", dict(collections.Counter(c.get("strate") for c in tests if c["type"] == "document")))
for e in erreurs:
    print("ERREUR", e)
print("Jeu de test valide" if not erreurs else f"{len(erreurs)} erreur(s)")
sys.exit(1 if erreurs else 0)
