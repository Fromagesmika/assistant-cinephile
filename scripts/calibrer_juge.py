"""Calibration du juge de fidélité sur 20 cas annotés à la main, comme le demande le sujet.

Trois étapes, à lancer dans l'ordre :
  python scripts/calibrer_juge.py preparer   choisit les 20 cas (fichier data/calibration.jsonl)
  python scripts/calibrer_juge.py annoter    vous montre chaque cas ; vous répondez o ou n
  python scripts/calibrer_juge.py mesurer    compare le juge à vos réponses

L'annotation se fait à l'aveugle : le verdict du juge n'est calculé qu'à l'étape « mesurer ».
Les réponses du niveau 0 sont incluses car elles contiennent de vraies erreurs : avec seulement
des réponses fidèles, on ne saurait pas si le juge sait en détecter une.
"""
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

CAS = RACINE / "data" / "calibration.jsonl"
ANNOTATIONS = RACINE / "data" / "annotations.jsonl"
NB_NIVEAU0 = 10
NB_NIVEAU1 = 10


def lire_jsonl(chemin):
    if not chemin.exists():
        return []
    with open(chemin, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def preparer():
    """Prend les réponses données aux cas `document`, de façon déterministe, sans regarder le juge."""
    passages = {t["id"]: t["passages"] for t in lire_jsonl(RACINE / "traces" / "niveau1.jsonl")}
    selection = []
    for niveau, nombre in ((0, NB_NIVEAU0), (1, NB_NIVEAU1)):
        lignes = [l for l in lire_jsonl(RACINE / "results" / f"niveau{niveau}.jsonl")
                  if l["type"] == "document" and l["statut"] == "reponse"]
        # On répartit la sélection sur toute la liste pour couvrir les trois strates.
        pas = max(1, len(lignes) / nombre)
        for i in range(min(nombre, len(lignes))):
            ligne = lignes[int(i * pas)]
            selection.append({
                "cle": f"n{niveau}-{ligne['id']}",
                "question": ligne["question"],
                "reponse": ligne["reponse"],
                "passages": [{"doc_id": p["doc_id"], "texte": p["texte"]} for p in passages[ligne["id"]]],
            })
    with open(CAS, "w", encoding="utf-8") as f:
        for cas in selection:
            f.write(json.dumps(cas, ensure_ascii=False) + "\n")
    print(f"{len(selection)} cas préparés dans {CAS.name}")


def annoter():
    """Affiche les cas pas encore annotés. On peut s'arrêter avec q et reprendre plus tard."""
    deja = {a["cle"] for a in lire_jsonl(ANNOTATIONS)}
    restants = [c for c in lire_jsonl(CAS) if c["cle"] not in deja]
    print("Une réponse est fidèle si TOUT ce qu'elle affirme est écrit dans les extraits.")
    print("Un détail absent des extraits la rend non fidèle, même s'il est vrai dans la réalité.\n")
    for numero, cas in enumerate(restants, start=1):
        print("=" * 70, f"\nCas {numero}/{len(restants)}\nQUESTION : {cas['question']}\n")
        for i, passage in enumerate(cas["passages"], start=1):
            print(f"--- Extrait {i}\n{passage['texte']}\n")
        print(f"RÉPONSE À ÉVALUER : {cas['reponse']}\n")
        choix = ""
        while choix not in {"o", "n", "q"}:
            choix = input("Fidèle aux extraits ? (o = oui, n = non, q = quitter) ").strip().lower()
        if choix == "q":
            return
        with open(ANNOTATIONS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"cle": cas["cle"], "fidele": choix == "o"}, ensure_ascii=False) + "\n")
    print("Annotation terminée.")


def mesurer():
    from src.juge import juger

    humain = {a["cle"]: a["fidele"] for a in lire_jsonl(ANNOTATIONS)}
    vp = vn = fp = fn = 0  # « positif » = le juge déclare la réponse fidèle
    desaccords = []
    for cas in lire_jsonl(CAS):
        if cas["cle"] not in humain:
            continue
        verdict, detail, _ = juger(cas["question"], cas["reponse"], cas["passages"])
        attendu = humain[cas["cle"]]
        vp += verdict and attendu
        vn += not verdict and not attendu
        fp += verdict and not attendu
        fn += not verdict and attendu
        if verdict != attendu:
            desaccords.append(f"- {cas['cle']} : humain {'fidèle' if attendu else 'non fidèle'}, juge {'fidèle' if verdict else 'non fidèle'}. {detail}")

    total = vp + vn + fp + fn
    if total == 0:
        raise SystemExit("Aucune annotation : lancez d'abord l'étape « annoter ».")
    texte = [
        f"# Calibration du juge de fidélité ({total} cas annotés)", "",
        f"- Accord avec l'annotation humaine : {(vp + vn) / total:.0%}",
        f"- Réponses non fidèles selon l'humain : {vn + fp}, dont repérées par le juge : {vn}",
        f"- Réponses fidèles selon l'humain : {vp + fn}, dont reconnues par le juge : {vp}",
        "", "Désaccords :", "", *(desaccords or ["- aucun"]),
    ]
    (RACINE / "results" / "calibration_juge.md").write_text("\n".join(texte) + "\n", encoding="utf-8")
    print("\n".join(texte))


if __name__ == "__main__":
    etapes = {"preparer": preparer, "annoter": annoter, "mesurer": mesurer}
    if len(sys.argv) != 2 or sys.argv[1] not in etapes:
        raise SystemExit("Usage : python scripts/calibrer_juge.py preparer|annoter|mesurer")
    etapes[sys.argv[1]]()
