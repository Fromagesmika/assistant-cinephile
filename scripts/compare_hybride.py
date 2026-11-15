"""Mesure hors ligne de la recherche hybride, avant de l'intégrer au niveau 3.

Deux jeux de requêtes pour les 28 cas `document` :
- la question d'origine (ce que reçoit le niveau 1) ;
- la première requête que l'agent du niveau 2 a réellement écrite (lue dans traces/niveau2.jsonl).
Le second jeu est celui qui compte : c'est là que le niveau 2 perd du Recall@5.

Résultat : results/choix_hybride.md
Lancement : python scripts/compare_hybride.py
"""
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src.hybride import index_hybride  # noqa: E402
from src.metrics import moyenne, rang_pertinent  # noqa: E402

MODES = ["dense", "bm25", "hybride", "dense_rerank", "hybride_rerank"]


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    cas = [c for c in lire(RACINE / "tests.jsonl") if c["type"] == "document"]
    traces = {t["id"]: t for t in lire(RACINE / "traces" / "niveau2.jsonl")}
    requetes_agent = {}
    for c in cas:
        etapes = traces.get(c["id"], {}).get("etapes", [])
        premiere = next((e["arguments"]["requete"] for e in etapes
                         if e.get("nom") == "rechercher_documents" and isinstance(e.get("arguments"), dict)), None)
        if premiere:
            requetes_agent[c["id"]] = premiere

    index = index_hybride()
    jeux = {
        "Questions d'origine": {c["id"]: c["question"] for c in cas},
        "Requêtes écrites par l'agent (niveau 2)": requetes_agent,
    }
    texte = ["# Recherche hybride et reranking : mesure hors ligne", "",
             "Recall@5 : le fait attendu est dans un des 5 extraits. MRR : moyenne de 1 / rang.",
             "dense : e5 seul (niveaux 1 et 2). bm25 : mots seuls. hybride : fusion RRF des deux.",
             "dense_rerank / hybride_rerank : 20 meilleurs candidats dense (et BM25), reclassés par le cross-encoder.",
             "Configuration retenue pour le niveau 3 : hybride_rerank.", ""]
    for nom, requetes in jeux.items():
        texte += [f"## {nom} ({len(requetes)} requêtes)", "", "| Recherche | Recall@5 | MRR | Échecs |", "|---|---|---|---|"]
        for mode in MODES:
            rangs = {}
            for c in cas:
                if c["id"] in requetes:
                    passages = index.rechercher(requetes[c["id"]], k=5, mode=mode)
                    rangs[c["id"]] = rang_pertinent(passages, c, avec_fait=True)
            recall = moyenne(r is not None for r in rangs.values())
            mrr = moyenne(1 / r if r else 0 for r in rangs.values())
            echecs = ", ".join(i for i, r in rangs.items() if r is None) or "aucun"
            texte.append(f"| {mode} | {recall:.0%} | {mrr:.3f} | {echecs} |")
        texte.append("")
    texte += ["Requêtes de l'agent, pour mémoire :", ""] + [f"- {i} : {q}" for i, q in requetes_agent.items()]
    (RACINE / "results" / "choix_hybride.md").write_text("\n".join(texte) + "\n", encoding="utf-8")
    print("\n".join(texte))


if __name__ == "__main__":
    main()
