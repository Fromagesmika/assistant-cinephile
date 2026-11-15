"""Génère tests.jsonl : le protocole commun à tous les niveaux.

Le jeu de test est écrit ici, en Python, pour rester lisible et éviter les erreurs de JSON.
Après toute modification : python scripts/build_tests.py puis python scripts/check_tests.py

Quatre types de cas, comme dans le sujet :
- document : la réponse est dans le corpus. `attendu` liste les faits à retrouver ;
- absent   : la réponse n'existe ni dans le corpus ni sur TMDB, le système doit s'abstenir ;
- tache    : plusieurs étapes ; l'état final de la liste est vérifié par du code ;
- ambigu   : le système doit demander une précision ou refuser.

Les titres inventés des cas `absent` ont été cherchés sur TMDB : aucun résultat.
"""
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


# Identifiants relevés sur TMDB ; les années sont aussi celles de TMDB.
TMDB_ID = {
    "Alien": 348,
    "Casablanca": 289,
    "Fight Club": 550,
    "Grave": 393519,
    "Inception": 27205,
    "Interstellar": 157336,
    "Joker": 475557,
    "La Haine": 406,
    "Memories of Murder": 11423,
    "Mickey 17": 696506,
    "Oppenheimer": 872585,
    "Seven": 807,
    "Titane": 630240,
    "Titanic": 597,
}


def doc(strate, question, attendu, source):
    return {"type": "document", "strate": strate, "question": question, "attendu": attendu, "sources": [source]}


def absent(question, termes_absents):
    return {"type": "absent", "question": question, "termes_absents": termes_absents}


def ambigu(question, comportement):
    return {"type": "ambigu", "question": question, "comportement": comportement}


def tache(question, initial, final, confirmations=None):
    """`confirmations` indique ce que répond l'utilisateur simulé, par type d'action."""
    return {
        "type": "tache",
        "question": question,
        # L'identifiant TMDB identifie le film sans ambiguïté : c'est lui que le code comparera.
        "etat_initial": [{"titre": t, "annee": a, "tmdb_id": TMDB_ID[t]} for t, a in initial],
        "etat_final": [{"titre": t, "annee": a, "tmdb_id": TMDB_ID[t]} for t, a in final],
        "confirmations": confirmations or {"ajouter": "accepter", "retirer": "accepter"},
    }


DOCUMENTS = [
    # Films et séries très connus : le LLM seul peut souvent répondre de mémoire.
    doc("populaire", "Qui a composé la musique du film Inception de Christopher Nolan ?", [["Hans Zimmer"]], "Inception"),
    doc("populaire", "Qui est le directeur de la photographie d'Inception ?", [["Wally Pfister"]], "Inception"),
    doc("populaire", "Quelle est la durée du film Parasite de Bong Joon-ho, sorti en 2019 ?", [["132", "2 h 12", "2h12"]], "Parasite (film, 2019)"),
    doc("populaire", "Dans quelle ville allemande une partie du Fabuleux Destin d'Amélie Poulain a-t-elle été tournée en studio ?", [["Cologne"]], "Le Fabuleux Destin d'Amélie Poulain"),
    doc("populaire", "Quel groupe est crédité pour la musique du film La Haine de Mathieu Kassovitz ?", [["Assassin"]], "La Haine"),
    doc("populaire", "Dans Le Dîner de cons, quel footballeur a inspiré le prénom de Juste Leblanc ?", [["Just Fontaine"]], "Le Dîner de cons (film)"),
    doc("populaire", "Combien d'épisodes compte la série Kaamelott ?", [["458"]], "Kaamelott"),
    doc("populaire", "Quel était le budget par épisode de la série Breaking Bad ?", [["3,2 millions"]], "Breaking Bad"),
    # Œuvres moins connues : le LLM seul devrait être moins fiable.
    doc("peu_connu", "Qui a composé la musique du film Le Samouraï de Jean-Pierre Melville ?", [["François de Roubaix"]], "Le Samouraï"),
    doc("peu_connu", "Quel romancier est l'auteur du livre adapté dans Le Salaire de la peur de Clouzot ?", [["Georges Arnaud"]], "Le Salaire de la peur"),
    doc("peu_connu", "À quelle date se déroule l'action de Cléo de 5 à 7 d'Agnès Varda ?", [["21 juin 1961"]], "Cléo de 5 à 7"),
    doc("peu_connu", "Quelle récompense le film Divines de Houda Benyamina a-t-il reçue au festival de Cannes 2016 ?", [["Caméra d'or"]], "Divines"),
    doc("peu_connu", "Dans Mon oncle de Jacques Tati, que fabrique l'usine dirigée par Monsieur Arpel ?", [["tuyaux"]], "Mon oncle"),
    doc("peu_connu", "En quelle année Mon oncle de Jacques Tati a-t-il reçu l'Oscar du meilleur film en langue étrangère ?", [["1959"]], "Mon oncle"),
    doc("peu_connu", "Combien d'épisodes compte la série Le Bureau des légendes ?", [["cinquante", "50"]], "Le Bureau des légendes"),
    doc("peu_connu", "Qui a écrit et réalisé le film d'animation La Tortue rouge ?", [["Michael Dudok de Wit"]], "La Tortue rouge"),
    # Œuvres sorties depuis 2024 : le LLM seul ne les connaît pas forcément.
    doc("recent", "Quel est le budget du film d'animation Flow de Gints Zilbalodis ?", [["3,5 millions"]], "Flow (film, 2024)"),
    doc("recent", "Quelle récompense Un simple accident de Jafar Panahi a-t-il remportée au festival de Cannes 2025 ?", [["Palme d'or"]], "Un simple accident"),
    doc("recent", "Qui a composé la musique du film Sirāt d'Óliver Laxe ?", [["Kangding Ray"]], "Sirāt"),
    doc("recent", "Quel est le budget du film Un p'tit truc en plus d'Artus ?", [["6 100 000", "6,1 millions"]], "Un p'tit truc en plus"),
    doc("recent", "Quel écrivain est l'auteur du roman adapté dans L'Amour ouf de Gilles Lellouche ?", [["Neville Thompson"]], "L'Amour ouf"),
    doc("recent", "Qui a reçu le prix d'interprétation féminine à Cannes 2025 pour La Petite Dernière ?", [["Nadia Melliti"]], "La Petite Dernière (film)"),
    doc("recent", "Qui a composé la musique de Valeur sentimentale de Joachim Trier ?", [["Hania Rani"]], "Valeur sentimentale"),
    doc("recent", "Quelle particularité de mise en scène ont tous les épisodes de la mini-série Adolescence ?", [["plan séquence"]], "Adolescence (mini-série)"),
    doc("recent", "De quel roman de Thomas Pynchon est librement adapté Une bataille après l'autre ?", [["Vineland"]], "Une bataille après l'autre"),
    # Box-office (ajout de la semaine 3) : chiffres de fréquentation tirés des sections « Box-office ».
    doc("populaire", "Combien d'entrées Le Fabuleux Destin d'Amélie Poulain a-t-il réalisées en France ?", [["8 636 041"]], "Le Fabuleux Destin d'Amélie Poulain"),
    doc("peu_connu", "Combien d'entrées Le Salaire de la peur de Clouzot a-t-il réalisées en France ?", [["6 944 306"]], "Le Salaire de la peur"),
    doc("recent", "Combien d'entrées Un p'tit truc en plus d'Artus a-t-il réalisées le jour de sa sortie ?", [["279 635"]], "Un p'tit truc en plus"),
]

ABSENTS = [
    # Œuvres inventées : la seule bonne réponse est de ne pas répondre.
    absent("Qui a réalisé le film Les Horloges de Valparaíso, sorti en 2019 ?", ["Horloges de Valparaíso"]),
    absent("Quelle est la durée du film Le Dernier Phare de Kerlouan ?", ["Dernier Phare de Kerlouan"]),
    absent("Combien de saisons compte la série Brume sur Tromsø ?", ["Brume sur Tromsø"]),
    # Œuvres réelles, mais détail qu'aucune source ne donne.
    absent("Quelle pointure de chaussures Christopher Nolan portait-il pendant le tournage d'Inception ?", ["pointure"]),
    absent("Combien de tasses de café ont été bues pendant le tournage de Mon oncle de Jacques Tati ?", ["tasses de café"]),
    absent("Quelle était la couleur de la voiture du monteur de Whiplash pendant le montage ?", ["voiture du monteur"]),
]

TACHES = [
    tache("Entre Memories of Murder et Parasite, ajoute à la liste à voir le plus ancien des deux films de Bong Joon-ho.",
          [], [("Memories of Murder", 2003)]),
    tache("Retire Titanic de la liste à voir et mets Interstellar à la place.",
          [("Titanic", 1997)], [("Interstellar", 2014)]),
    tache("Ajoute Grave et Titane, les deux films de Julia Ducournau, à la liste à voir.",
          [], [("Grave", 2017), ("Titane", 2021)]),
    tache("Trouve qui a réalisé Parasite (2019), puis ajoute à la liste à voir son film Mickey 17.",
          [], [("Mickey 17", 2025)]),
    tache("Retire tous les films de la liste à voir.",
          [("La Haine", 1995), ("Seven", 1995)], []),
    tache("Remplace tous les films de la liste sortis avant 2000 par Oppenheimer.",
          [("Casablanca", 1943), ("Alien", 1979), ("Joker", 2019)], [("Joker", 2019), ("Oppenheimer", 2023)]),
    # Règles métier et confirmation : ici, le bon résultat est que la liste change peu ou pas.
    tache("Ajoute Inception à la liste à voir.",  # doublon : la règle métier doit l'empêcher
          [("Inception", 2010)], [("Inception", 2010)]),
    tache("Ajoute le film Les Horloges de Valparaíso à la liste à voir.",  # film inexistant
          [("La Haine", 1995)], [("La Haine", 1995)]),
    tache("Ajoute Drive My Car à la liste à voir.",  # l'utilisateur refuse : rien ne doit changer
          [("La Haine", 1995)], [("La Haine", 1995)], {"ajouter": "refuser", "retirer": "refuser"}),
    tache("Ajoute Fight Club à la liste à voir et retire Seven.",  # ajout accepté, retrait refusé
          [("Seven", 1995)], [("Seven", 1995), ("Fight Club", 1999)], {"ajouter": "accepter", "retirer": "refuser"}),
    # Box-office (ajout de la semaine 3) : recettes mondiales TMDB, 839 M$ contre 747 M$.
    tache("Entre Inception et Interstellar, ajoute à la liste à voir celui qui a fait les plus grosses recettes au box-office mondial.",
          [], [("Inception", 2010)]),
]

AMBIGUS = [
    ambigu("Qui a réalisé Nosferatu ?", "precision"),  # 1922 ou 2024
    ambigu("Qui joue dans Frankenstein ?", "precision"),  # plusieurs adaptations
    ambigu("Il dure combien de temps, ce film ?", "precision"),  # aucun film nommé
    ambigu("Et la suite, elle sort quand ?", "precision"),  # aucune œuvre nommée
    ambigu("Quelle est la capitale de l'Australie ?", "refus"),
    ambigu("Écris-moi une recette de crêpes.", "refus"),
]


def main():
    familles = [("doc", DOCUMENTS), ("abs", ABSENTS), ("task", TACHES), ("amb", AMBIGUS)]
    with open(RACINE / "tests.jsonl", "w", encoding="utf-8") as f:
        for prefixe, cas_famille in familles:
            for i, cas in enumerate(cas_famille, start=1):
                f.write(json.dumps({"id": f"{prefixe}-{i:02d}", **cas}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
