"""Évaluation : un seul protocole (tests.jsonl) pour tous les niveaux.

Lancement : python eval.py
Produit   : results/niveauN.jsonl (résultats bruts), traces/niveauN.jsonl (traces),
            results/tableau.md (le tableau attendu dans le rapport).

Les réponses déjà obtenues sont relues dans cache/ : la commande reproduit le tableau
sans clé d'API tant que tests.jsonl et les prompts n'ont pas changé.
"""
import argparse
import json
from pathlib import Path

from src.levels import level0
from src.metrics import (
    abstention_correcte,
    moyenne,
    precision_ou_refus_correct,
    reponse_exacte,
)
from src.traces import ecrire_trace, vider_traces

RACINE = Path(__file__).resolve().parent
NIVEAUX = {0: level0}  # on ajoutera 1, 2 et 3 ici au fil des semaines
# Le niveau 0 n'a pas d'outils : les tâches en plusieurs étapes ne s'appliquent pas à lui.
TYPES_PAR_NIVEAU = {0: {"document", "absent", "ambigu"}}


def charger_tests():
    with open(RACINE / "tests.jsonl", encoding="utf-8") as f:
        return [json.loads(ligne) for ligne in f if ligne.strip()]


def noter(sortie, cas):
    """Renvoie le critère évalué pour ce type de cas et s'il est réussi."""
    if cas["type"] == "document":
        return "exactitude", reponse_exacte(sortie, cas)
    if cas["type"] == "absent":
        return "abstention", abstention_correcte(sortie)
    if cas["type"] == "ambigu":
        return "precision_refus", precision_ou_refus_correct(sortie, cas)
    raise ValueError(f"Type de cas non géré : {cas['type']}")


def evaluer_niveau(numero, tests):
    module = NIVEAUX[numero]
    vider_traces(numero)
    lignes = []
    for cas in tests:
        if cas["type"] not in TYPES_PAR_NIVEAU[numero]:
            continue
        sortie = module.repondre(cas["question"])
        critere, reussi = noter(sortie, cas)
        lignes.append({
            "id": cas["id"],
            "type": cas["type"],
            "strate": cas.get("strate"),
            "critere": critere,
            "reussi": reussi,
            "question": cas["question"],
            "statut": sortie["statut"],
            "reponse": sortie["texte"],
            "sources": sortie["sources"],
            "tokens": sortie["tokens"],
            "latence": round(sortie["latence"], 3),
        })
        ecrire_trace(numero, {"id": cas["id"], **sortie})
        print(f"  [{'ok' if reussi else 'KO'}] {cas['id']} ({sortie['tokens']} tokens)")

    (RACINE / "results").mkdir(exist_ok=True)
    with open(RACINE / "results" / f"niveau{numero}.jsonl", "w", encoding="utf-8") as f:
        for ligne in lignes:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    return lignes


def taux(lignes, critere, strate=None):
    """Part de réussite pour un critère, éventuellement limitée à une strate."""
    valeurs = [
        l["reussi"] for l in lignes
        if l["critere"] == critere and (strate is None or l["strate"] == strate)
    ]
    return moyenne(valeurs)


def pourcent(valeur):
    return "—" if valeur is None else f"{valeur:.0%}"


def tableau(resultats):
    """Le tableau du sujet, plus le détail de l'exactitude par strate de films."""
    titres = {0: "0 · LLM seul", 1: "1 · RAG", 2: "2 · Agent", 3: "3 · Extension"}
    sortie = [
        "| Niveau | Recall@5 | Exactitude | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for numero, lignes in sorted(resultats.items()):
        tokens = moyenne(l["tokens"] for l in lignes)
        latence = moyenne(l["latence"] for l in lignes)
        sortie.append(
            f"| {titres[numero]} | — | {pourcent(taux(lignes, 'exactitude'))} "
            f"| {pourcent(taux(lignes, 'abstention'))} "
            f"| {pourcent(taux(lignes, 'precision_refus'))} | — | — "
            f"| {tokens:.0f} | {latence:.2f} |"
        )
    sortie += [
        "",
        "Exactitude par strate :",
        "",
        "| Niveau | Populaire | Peu connu | Récent |",
        "|---|---|---|---|",
    ]
    for numero, lignes in sorted(resultats.items()):
        cellules = [pourcent(taux(lignes, "exactitude", s)) for s in ("populaire", "peu_connu", "recent")]
        sortie.append(f"| {titres[numero]} | " + " | ".join(cellules) + " |")
    return "\n".join(sortie) + "\n"


def main():
    analyseur = argparse.ArgumentParser(description="Évalue les niveaux sur tests.jsonl")
    analyseur.add_argument("--niveaux", type=int, nargs="+", default=sorted(NIVEAUX))
    arguments = analyseur.parse_args()

    tests = charger_tests()
    resultats = {}
    for numero in arguments.niveaux:
        print(f"Niveau {numero}")
        resultats[numero] = evaluer_niveau(numero, tests)

    texte = tableau(resultats)
    (RACINE / "results" / "tableau.md").write_text(texte, encoding="utf-8")
    print("\n" + texte)


if __name__ == "__main__":
    main()
