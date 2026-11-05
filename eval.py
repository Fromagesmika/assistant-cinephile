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

from src.juge import juger
from src.levels import level0, level1
from src.metrics import (
    abstention_correcte,
    moyenne,
    precision_ou_refus_correct,
    rang_pertinent,
    reponse_exacte,
    source_citee,
)
from src.traces import ecrire_trace, vider_traces

RACINE = Path(__file__).resolve().parent
NIVEAUX = {0: level0, 1: level1}  # on ajoutera 2 et 3 ici au fil des semaines
# Les niveaux 0 et 1 n'ont pas d'outils : les tâches en plusieurs étapes ne les concernent pas.
TYPES_PAR_NIVEAU = {0: {"document", "absent", "ambigu"}, 1: {"document", "absent", "ambigu"}}


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


def mesures_rag(sortie, cas):
    """Mesures propres aux niveaux qui consultent des documents (cas `document` seulement)."""
    if cas["type"] != "document" or "passages" not in sortie:
        return {}
    mesures = {
        "rang": rang_pertinent(sortie["passages"], cas, avec_fait=True),
        "rang_page": rang_pertinent(sortie["passages"], cas, avec_fait=False),
    }
    if sortie["statut"] == "reponse":
        fidele, detail, tokens_juge = juger(cas["question"], sortie["texte"], sortie["passages"])
        mesures.update({
            "source_citee": source_citee(sortie, cas),
            "fidele": fidele,
            "detail_juge": detail,
            "tokens_juge": tokens_juge,  # coût de l'évaluation, pas du système : hors tableau
        })
    return mesures


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
            **mesures_rag(sortie, cas),
        })
        ecrire_trace(numero, {"id": cas["id"], **sortie})
        print(f"  [{'ok' if reussi else 'KO'}] {cas['id']} ({sortie['tokens']} tokens)", flush=True)

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


def recall_et_mrr(lignes):
    """Recall@5 : le fait attendu est dans un des 5 passages. MRR : moyenne de 1/rang."""
    rangs = [l["rang"] for l in lignes if "rang" in l]
    if not rangs:
        return None, None
    return moyenne(r is not None for r in rangs), moyenne(1 / r if r else 0 for r in rangs)


def tableau(resultats):
    """Le tableau du sujet, plus le détail de l'exactitude par strate de films."""
    titres = {0: "0 · LLM seul", 1: "1 · RAG", 2: "2 · Agent", 3: "3 · Extension"}
    sortie = [
        "| Niveau | Recall@5 | MRR | Exactitude | Source citée | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for numero, lignes in sorted(resultats.items()):
        recall, mrr = recall_et_mrr(lignes)
        citees = [l["source_citee"] for l in lignes if "source_citee" in l]
        fideles = [l["fidele"] for l in lignes if "fidele" in l]
        sortie.append(
            f"| {titres[numero]} | {pourcent(recall)} | {'—' if mrr is None else f'{mrr:.3f}'} "
            f"| {pourcent(taux(lignes, 'exactitude'))} | {pourcent(moyenne(citees))} | {pourcent(moyenne(fideles))} "
            f"| {pourcent(taux(lignes, 'abstention'))} | {pourcent(taux(lignes, 'precision_refus'))} | — | — "
            f"| {moyenne(l['tokens'] for l in lignes):.0f} | {moyenne(l['latence'] for l in lignes):.2f} |"
        )
    sortie += [
        "",
        "Source citée et fidélité portent sur les réponses données aux cas `document`. "
        "La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).",
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
        print(f"Niveau {numero}", flush=True)
        resultats[numero] = evaluer_niveau(numero, tests)

    texte = tableau(resultats)
    (RACINE / "results" / "tableau.md").write_text(texte, encoding="utf-8")
    print("\n" + texte)


if __name__ == "__main__":
    main()
