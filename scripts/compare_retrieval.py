"""Compare embeddings et tailles de découpage sur la recherche seule, sans appel au LLM.

On change un seul réglage à la fois : d'abord le modèle à taille fixe, puis la taille avec
le meilleur modèle. Les questions viennent de tests.jsonl (cas `document`).
Deux niveaux de réussite sont mesurés :
- page   : un passage de la bonne page est dans le top k ;
- fait   : un passage de la bonne page contenant le fait attendu est dans le top k.

Lancement : python scripts/compare_retrieval.py
Produit   : results/choix_retrieval.md
"""
import json
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
from src.metrics import rang_pertinent  # noqa: E402
from src.rag import Index, chemin_index, tous_les_passages  # noqa: E402

K = 5
TAILLE_REFERENCE = 800


def mesurer(modele, taille, tests):
    chevauchement = taille // 8
    nombre = len(tous_les_passages(taille, chevauchement))
    deja_calcule = chemin_index(modele, taille, chevauchement).exists()
    debut = time.perf_counter()
    index = Index(modele, taille, chevauchement)
    duree = time.perf_counter() - debut

    rangs_page, rangs_fait, scores_doc, scores_abs = [], [], [], []
    for cas in tests:
        trouves = index.rechercher(cas["question"], k=K)
        if cas["type"] == "document":
            rangs_page.append(rang_pertinent(trouves, cas, avec_fait=False))
            rangs_fait.append(rang_pertinent(trouves, cas, avec_fait=True))
            scores_doc.append(trouves[0]["score"])
        elif cas["type"] == "absent":
            scores_abs.append(trouves[0]["score"])

    def recall(rangs):
        return sum(r is not None for r in rangs) / len(rangs)

    def mrr(rangs):
        return sum(1 / r for r in rangs if r) / len(rangs)

    ligne = {
        "modele": modele, "taille": taille, "passages": nombre,
        "duree": None if deja_calcule else round(duree),
        "recall_page": recall(rangs_page), "recall_fait": recall(rangs_fait),
        "mrr_fait": mrr(rangs_fait),
        "score_doc_min": min(scores_doc), "score_doc_moyen": sum(scores_doc) / len(scores_doc),
        "score_abs_max": max(scores_abs), "score_abs_moyen": sum(scores_abs) / len(scores_abs),
        "rates": [c["id"] for c, r in zip((t for t in tests if t["type"] == "document"), rangs_fait) if r is None],
    }
    print(ligne, flush=True)
    return ligne


def main():
    with open(RACINE / "tests.jsonl", encoding="utf-8") as f:
        tests = [json.loads(l) for l in f if l.strip()]

    lignes = [mesurer(m, TAILLE_REFERENCE, tests) for m in ("e5", "minilm")]
    meilleur = max(lignes, key=lambda l: (l["recall_fait"], l["mrr_fait"]))["modele"]
    lignes += [mesurer(meilleur, t, tests) for t in (400, 1500)]

    texte = [
        f"# Choix du découpage et des embeddings (top {K}, {sum(t['type'] == 'document' for t in tests)} questions)",
        "",
        "| Modèle | Taille | Passages | Encodage (s) | Recall@5 page | Recall@5 fait | MRR fait | Score haut min (document) | Score haut max (absent) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for l in lignes:
        duree = "déjà calculé" if l["duree"] is None else l["duree"]
        texte.append(
            f"| {l['modele']} | {l['taille']} | {l['passages']} | {duree} | {l['recall_page']:.0%} "
            f"| {l['recall_fait']:.0%} | {l['mrr_fait']:.3f} | {l['score_doc_min']:.3f} | {l['score_abs_max']:.3f} |"
        )
    texte += ["", "Questions dont le fait n'est pas retrouvé :", ""]
    texte += [f"- {l['modele']} / {l['taille']} : {', '.join(l['rates']) or 'aucune'}" for l in lignes]
    (RACINE / "results" / "choix_retrieval.md").write_text("\n".join(texte) + "\n", encoding="utf-8")
    print("\n".join(texte))


if __name__ == "__main__":
    main()
