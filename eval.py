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
from src.levels import level0, level1, level2
from src.liste import ListeAVoir
from src.metrics import (
    abstention_correcte,
    chaque_phrase_citee,
    moyenne,
    precision_ou_refus_correct,
    rang_pertinent,
    reponse_exacte,
    source_citee,
)
from src.traces import ecrire_trace, vider_traces

RACINE = Path(__file__).resolve().parent
NIVEAUX = {0: level0, 1: level1, 2: level2}  # le niveau 3 s'ajoutera ici
# Les niveaux 0 et 1 n'ont pas d'outils : les tâches en plusieurs étapes ne les concernent pas.
TYPES_PAR_NIVEAU = {
    0: {"document", "absent", "ambigu"},
    1: {"document", "absent", "ambigu"},
    2: {"document", "absent", "ambigu", "tache"},
}
ESSAIS_TACHE = 3  # pass^3 : une tâche n'est réussie que si ses 3 essais indépendants réussissent


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
    # Recall@5 et MRR portent sur les 5 extraits d'une recherche. L'agent peut en lancer
    # plusieurs (ou aucune) : on retient la première, et l'absence de recherche compte comme un échec.
    recherche = sortie.get("passages_recherche", sortie["passages"])
    mesures = {
        "rang": rang_pertinent(recherche, cas, avec_fait=True),
        "rang_page": rang_pertinent(recherche, cas, avec_fait=False),
    }
    if sortie["statut"] == "reponse":
        fidele, detail, tokens_juge = juger(cas["question"], sortie["texte"], sortie["passages"])
        mesures.update({
            "source_citee": source_citee(sortie, cas),
            "phrases_citees": chaque_phrase_citee(sortie["texte"]),
            "fidele": fidele,
            "detail_juge": detail,
            "tokens_juge": tokens_juge,  # coût de l'évaluation, pas du système : hors tableau
        })
    return mesures


def etat_final_correct(liste, cas):
    """Tâche réussie si la liste contient exactement les œuvres attendues (vérifié par le code)."""
    return liste.identifiants() == sorted(f["tmdb_id"] for f in cas["etat_final"])


def evaluer_tache(numero, module, cas):
    """Lance ESSAIS_TACHE essais indépendants, chacun sur une liste remise à l'état initial.

    L'utilisateur est simulé : il accepte ou refuse chaque type d'action comme le prévoit le cas.
    """
    essais = []
    for essai in range(ESSAIS_TACHE):
        liste = ListeAVoir(cas["etat_initial"])
        confirmer = lambda action: cas["confirmations"][action["type"]] == "accepter"
        sortie = module.repondre(cas["question"], essai=essai, liste=liste, confirmer=confirmer)
        essais.append((sortie, etat_final_correct(liste, cas)))
        ecrire_trace(numero, {"id": f"{cas['id']}#{essai}", **sortie})
    sorties = [s for s, _ in essais]
    succes = [ok for _, ok in essais]
    print(f"  [{'ok' if all(succes) else 'KO'}] {cas['id']} essais {''.join('1' if ok else '0' for ok in succes)} "
          f"({moyenne(s['tokens'] for s in sorties):.0f} tokens)", flush=True)
    return {
        "id": cas["id"],
        "type": cas["type"],
        "strate": None,
        "critere": "tache",
        "reussi": all(succes),
        "succes_essais": succes,
        "question": cas["question"],
        "statut": sorties[0]["statut"],
        "reponse": sorties[0]["texte"],
        "sources": sorties[0]["sources"],
        "listes_finales": [s["liste_finale"] for s in sorties],
        "tokens": moyenne(s["tokens"] for s in sorties),
        "latence": round(moyenne(s["latence"] for s in sorties), 3),
    }


def evaluer_niveau(numero, tests):
    module = NIVEAUX[numero]
    vider_traces(numero)
    lignes = []
    for cas in tests:
        if cas["type"] not in TYPES_PAR_NIVEAU[numero]:
            continue
        if cas["type"] == "tache":
            lignes.append(evaluer_tache(numero, module, cas))
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
        "| Niveau | Recall@5 | MRR | Exactitude | Source citée | Phrases citées | Fidélité | Abstention | Précision/refus | Succès tâches | pass^3 | Tokens / requête | Latence (s) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for numero, lignes in sorted(resultats.items()):
        recall, mrr = recall_et_mrr(lignes)
        citees = [l["source_citee"] for l in lignes if "source_citee" in l]
        phrases = [l["phrases_citees"] for l in lignes if "phrases_citees" in l]
        fideles = [l["fidele"] for l in lignes if "fidele" in l]
        sortie.append(
            f"| {titres[numero]} | {pourcent(recall)} | {'—' if mrr is None else f'{mrr:.3f}'} "
            f"| {pourcent(taux(lignes, 'exactitude'))} | {pourcent(moyenne(citees))} | {pourcent(moyenne(phrases))} "
            f"| {pourcent(moyenne(fideles))} "
            f"| {pourcent(taux(lignes, 'abstention'))} | {pourcent(taux(lignes, 'precision_refus'))} "
            f"| {pourcent(moyenne(ok for l in lignes for ok in l.get('succes_essais', [])))} "
            f"| {pourcent(taux(lignes, 'tache'))} "
            f"| {moyenne(l['tokens'] for l in lignes):.0f} | {moyenne(l['latence'] for l in lignes):.2f} |"
        )
    nombre_taches = max((sum(l["critere"] == "tache" for l in lignes) for lignes in resultats.values()), default=0)
    sortie += [
        "",
        "Source citée, phrases citées et fidélité portent sur les réponses données aux cas `document`. "
        "La fidélité vient du juge LLM (voir results/calibration_juge.md pour sa fiabilité).",
        f"Succès tâches : part des {ESSAIS_TACHE} × {nombre_taches} essais dont l'état final de la liste est correct ; "
        f"pass^3 : part des tâches réussies aux {ESSAIS_TACHE} essais.",
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
