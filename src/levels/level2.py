"""Niveau 2 : agent outillé. Boucle écrite sans framework.

- 7 outils décrits par un schéma JSON, classés par effet : 5 en lecture, 2 en écriture.
- Boucle bornée : au plus MAX_APPELS_LLM appels au modèle et MAX_TOKENS tokens par requête.
- Les erreurs d'outils (arguments invalides, œuvre introuvable, règle métier) sont renvoyées
  au modèle comme résultat d'outil, pour qu'il puisse se corriger.
- Toute écriture dans la liste est d'abord vérifiée par le code (règles métier, existence sur
  TMDB), puis attend la confirmation de l'utilisateur : la session se met en pause et ne
  reprend qu'avec sa décision. L'interface et l'évaluation passent par ce même mécanisme.
"""
import json
import re
import time

from src import tmdb
from src.levels.level0 import lire_json, lire_sortie
from src.liste import ErreurRegle, ListeAVoir
from src.llm import MODELE, discuter
from src.rag import index_principal

MAX_APPELS_LLM = 8
MAX_TOKENS = 40_000
K = 5

PROMPT_SYSTEME = """Tu es un assistant cinéphile francophone. Tu réponds aux questions sur les films et les séries, et tu gères la liste « à voir » partagée de l'utilisateur. Tu disposes d'outils.

Répondre à une question :
- Commence par rechercher_documents (pages Wikipédia). Si les extraits ne suffisent pas, utilise rechercher_oeuvre et details_oeuvre (base TMDB).
- Réponds uniquement à partir des résultats des outils, même si tu crois connaître la réponse. Chaque phrase de ta réponse se termine par la référence [n] du résultat qui la justifie, par exemple [3].
- Si les outils ne donnent pas la réponse, utilise le statut "abstention".
- Si le titre désigne plusieurs œuvres différentes et que la question ne précise pas laquelle, ou si aucune œuvre n'est nommée, utilise le statut "precision" et pose une question.
- Si la demande n'a aucun rapport avec le cinéma ou les séries, utilise le statut "refus" sans appeler d'outil.

Modifier la liste :
- Identifie chaque œuvre avec rechercher_oeuvre pour obtenir son tmdb_id. N'invente jamais un identifiant.
- Consulte la liste avec lire_liste avant de retirer quelque chose.
- Si l'œuvre demandée est introuvable, ne modifie rien et dis-le.
- Chaque ajout ou retrait est soumis à la confirmation de l'utilisateur. Si une action est refusée, ne la propose pas de nouveau.

Quand tu as terminé, n'appelle plus d'outil et réponds uniquement avec un objet JSON de cette forme :
{"statut": "reponse" | "abstention" | "precision" | "refus", "texte": "ta réponse en français", "sources": [références utilisées]}"""


def _outil(nom, description, proprietes, requis):
    return {"type": "function", "function": {
        "name": nom, "description": description,
        "parameters": {"type": "object", "properties": proprietes, "required": requis},
    }}


_TYPE = {"type": "string", "enum": ["film", "serie"], "description": "film (par défaut) ou serie"}
_ID = {"type": "integer", "description": "identifiant TMDB obtenu avec rechercher_oeuvre"}

OUTILS = [
    _outil("rechercher_documents", "Cherche les 5 extraits de pages Wikipédia les plus proches d'une requête.",
           {"requete": {"type": "string", "description": "la question ou les mots-clés à chercher"}}, ["requete"]),
    _outil("rechercher_oeuvre", "Cherche un film ou une série par son titre dans TMDB. Renvoie au plus 5 œuvres avec tmdb_id et année.",
           {"titre": {"type": "string"}, "type": _TYPE, "annee": {"type": "integer", "description": "année de sortie, si connue"}}, ["titre"]),
    _outil("details_oeuvre", "Fiche TMDB d'une œuvre : année, durée, réalisation ou création, genres, acteurs, et pour un film son budget et ses recettes mondiales au box-office (en dollars).",
           {"tmdb_id": _ID, "type": _TYPE}, ["tmdb_id"]),
    _outil("recommander_oeuvres", "Œuvres recommandées par TMDB à partir d'une œuvre, avec un filtre facultatif sur les années.",
           {"tmdb_id": _ID, "type": _TYPE, "annee_min": {"type": "integer"}, "annee_max": {"type": "integer"}}, ["tmdb_id"]),
    _outil("lire_liste", "Renvoie le contenu actuel de la liste « à voir ».", {}, []),
    _outil("ajouter_a_la_liste", "Ajoute une œuvre à la liste « à voir ». Action soumise à la confirmation de l'utilisateur.",
           {"tmdb_id": _ID, "type": _TYPE}, ["tmdb_id"]),
    _outil("retirer_de_la_liste", "Retire une œuvre de la liste « à voir ». Action soumise à la confirmation de l'utilisateur.",
           {"tmdb_id": _ID, "type": _TYPE}, ["tmdb_id"]),
]
SCHEMAS = {o["function"]["name"]: o["function"]["parameters"] for o in OUTILS}
EFFETS = {
    "rechercher_documents": "lecture", "rechercher_oeuvre": "lecture", "details_oeuvre": "lecture",
    "recommander_oeuvres": "lecture", "lire_liste": "lecture",
    "ajouter_a_la_liste": "ecriture", "retirer_de_la_liste": "ecriture",
}


class ErreurArguments(Exception):
    pass


def valider_arguments(nom, texte_arguments):
    """Contrôle les arguments d'un appel d'outil contre son schéma JSON (types, requis, valeurs permises)."""
    if nom not in SCHEMAS:
        raise ErreurArguments(f"Outil inconnu : {nom}. Outils disponibles : {', '.join(SCHEMAS)}.")
    try:
        arguments = json.loads(texte_arguments or "{}")
    except json.JSONDecodeError:
        raise ErreurArguments("Arguments illisibles : ce n'est pas un objet JSON.")
    if not isinstance(arguments, dict):
        raise ErreurArguments("Les arguments doivent former un objet JSON.")
    schema = SCHEMAS[nom]
    for cle in schema["required"]:
        if cle not in arguments:
            raise ErreurArguments(f"Argument obligatoire manquant : {cle}.")
    propres = {}
    for cle, valeur in arguments.items():
        if cle not in schema["properties"]:
            raise ErreurArguments(f"Argument inconnu : {cle}.")
        attendu = schema["properties"][cle]
        if attendu["type"] == "integer":
            # Les modèles écrivent parfois 27205.0 ou "27205" : on accepte s'il s'agit bien d'un entier.
            if isinstance(valeur, float) and valeur.is_integer():
                valeur = int(valeur)
            elif isinstance(valeur, str) and valeur.strip().isdigit():
                valeur = int(valeur)
            if not isinstance(valeur, int) or isinstance(valeur, bool):
                raise ErreurArguments(f"{cle} doit être un entier.")
        elif attendu["type"] == "string" and not isinstance(valeur, str):
            raise ErreurArguments(f"{cle} doit être une chaîne de caractères.")
        if "enum" in attendu and valeur not in attendu["enum"]:
            raise ErreurArguments(f"{cle} doit valoir {' ou '.join(attendu['enum'])}.")
        propres[cle] = valeur
    return propres


class Session:
    """Une requête traitée par l'agent. Elle peut s'arrêter pour attendre une confirmation."""

    def __init__(self, question, liste=None, essai=0):
        self.liste = liste if liste is not None else ListeAVoir()
        self.essai = essai
        self.messages = [{"role": "system", "content": PROMPT_SYSTEME}, {"role": "user", "content": question}]
        self.preuves = []            # résultats citables, numérotés [1], [2]… dans l'ordre d'arrivée
        self.passages_recherche = []  # extraits de la première recherche documentaire (Recall@5, MRR)
        self.etapes = []
        self.tokens = 0
        self.latence = 0.0
        self.appels_llm = 0
        self.file = []               # appels d'outils demandés par le modèle, pas encore traités
        self.attente = None          # écriture en attente de confirmation
        self.ecriture_demandee = False
        self.fin = None

    # --- Boucle -------------------------------------------------------------------------

    def avancer(self, decision=None):
        """Fait progresser la session jusqu'à la réponse finale ou jusqu'à la prochaine confirmation."""
        if self.attente is not None:
            if decision is None:
                raise ValueError("Une action attend une confirmation : passez decision=True ou False.")
            self._appliquer_decision(bool(decision))
        while self.fin is None and self.attente is None:
            if self.file:
                self._traiter_appel(self.file.pop(0))
            else:
                self._tour_llm()
        return self

    def _tour_llm(self):
        if self.appels_llm >= MAX_APPELS_LLM or self.tokens >= MAX_TOKENS:
            limite = f"{MAX_APPELS_LLM} appels au modèle" if self.appels_llm >= MAX_APPELS_LLM else f"{MAX_TOKENS} tokens"
            self.etapes.append({"type": "limite", "detail": limite})
            self._terminer("abstention", f"Je m'arrête : la limite de {limite} est atteinte.", [])
            return
        sortie = discuter(self.messages, essai=self.essai, outils=OUTILS)
        self.appels_llm += 1
        self.tokens += sortie["tokens_total"]
        self.latence += sortie["latence"]
        message = sortie["message"]
        self.messages.append(message)  # renvoyé tel quel, avec la signature de Gemini
        appels = message.get("tool_calls") or []
        self.etapes.append({
            "type": "llm", "appel": self.appels_llm, "modele": sortie.get("modele", MODELE),
            "tokens": sortie["tokens_total"], "latence": round(sortie["latence"], 3),
            "outils_demandes": [a["function"]["name"] for a in appels],
        })
        if appels:
            self.file.extend(appels)
        else:
            self._conclure(sortie["texte"])

    def _traiter_appel(self, appel):
        nom = appel["function"]["name"]
        debut = time.perf_counter()
        etape = {"type": "outil", "nom": nom, "effet": EFFETS.get(nom, "inconnu"), "arguments": appel["function"].get("arguments")}
        try:
            arguments = valider_arguments(nom, appel["function"].get("arguments"))
            etape["arguments"] = arguments
            if EFFETS[nom] == "ecriture":
                self.ecriture_demandee = True
                action = self._preparer_ecriture(nom, arguments)
                # Règles respectées : on n'écrit rien, on attend la décision de l'utilisateur.
                etape["resultat"] = "en attente de confirmation"
                self.etapes.append(etape)
                self.attente = {"appel": appel, "action": action}
                return
            resultat, duree_externe = self._executer_lecture(nom, arguments)
        except (ErreurArguments, ErreurRegle, tmdb.ErreurTMDB) as erreur:
            resultat, duree_externe = {"erreur": str(erreur)}, 0.0
        except Exception as erreur:  # panne d'un outil : le modèle doit le savoir, la boucle continue
            resultat, duree_externe = {"erreur": f"L'outil a échoué : {erreur}"}, 0.0
        duree = duree_externe + (time.perf_counter() - debut)
        self.latence += duree
        etape.update({"resultat": _resume(resultat), "duree": round(duree, 3)})
        self.etapes.append(etape)
        self._repondre_outil(appel, resultat)

    def _repondre_outil(self, appel, resultat):
        self.messages.append({"role": "tool", "tool_call_id": appel["id"], "content": json.dumps(resultat, ensure_ascii=False)})

    # --- Outils en lecture ----------------------------------------------------------------

    def _citer(self, source, texte):
        self.preuves.append({"doc_id": source, "texte": texte})
        return len(self.preuves)

    def _executer_lecture(self, nom, a):
        """Exécute un outil sans effet. Renvoie (résultat pour le modèle, durée d'un appel externe)."""
        type_oeuvre = a.get("type", "film")
        if nom == "rechercher_documents":
            passages = index_principal().rechercher(a["requete"], k=K)
            if not self.passages_recherche:
                self.passages_recherche = passages
            return {"extraits": [
                {"ref": self._citer(p["doc_id"], p["texte"]), "page": p["doc_id"], "texte": p["texte"]} for p in passages
            ]}, 0.0
        if nom == "rechercher_oeuvre":
            resultats, duree = tmdb.rechercher(a["titre"], type_oeuvre, a.get("annee"))
            if not resultats:
                return {"resultats": [], "message": "Aucune œuvre trouvée sur TMDB pour ce titre."}, duree
            return {"resultats": [{"ref": self._citer(f"TMDB:{r['tmdb_id']}", _texte_fiche(r)), **r} for r in resultats]}, duree
        if nom == "details_oeuvre":
            fiche, duree = tmdb.details(a["tmdb_id"], type_oeuvre)
            return {"ref": self._citer(f"TMDB:{fiche['tmdb_id']}", _texte_fiche(fiche)), **fiche}, duree
        if nom == "recommander_oeuvres":
            resultats, duree = tmdb.recommandations(a["tmdb_id"], type_oeuvre, a.get("annee_min"), a.get("annee_max"))
            return {"resultats": [{"ref": self._citer(f"TMDB:{r['tmdb_id']}", _texte_fiche(r)), **r} for r in resultats]}, duree
        if nom == "lire_liste":
            return {"liste": self.liste.films, "nombre": len(self.liste.films)}, 0.0
        raise ErreurArguments(f"Outil inconnu : {nom}.")

    # --- Outils en écriture ---------------------------------------------------------------

    def _preparer_ecriture(self, nom, a):
        """Vérifie tout ce qui peut l'être par le code avant de déranger l'utilisateur."""
        type_oeuvre = a.get("type", "film")
        if nom == "ajouter_a_la_liste":
            self.liste.verifier_ajout(a["tmdb_id"], type_oeuvre)
            fiche, _ = tmdb.details(a["tmdb_id"], type_oeuvre)  # l'œuvre doit exister : pas d'identifiant inventé
            return {"type": "ajouter", "fiche": fiche, "tmdb_id": fiche["tmdb_id"],
                    "texte": f"Ajouter « {fiche['titre']} » ({fiche['annee']}) à la liste à voir ?"}
        self.liste.verifier_retrait(a["tmdb_id"], type_oeuvre)
        film = next(f for f in self.liste.films if f["tmdb_id"] == a["tmdb_id"] and f.get("type", "film") == type_oeuvre)
        return {"type": "retirer", "tmdb_id": a["tmdb_id"], "type_oeuvre": type_oeuvre,
                "texte": f"Retirer « {film['titre']} » ({film.get('annee')}) de la liste à voir ?"}

    def _appliquer_decision(self, accepte):
        appel, action = self.attente["appel"], self.attente["action"]
        self.attente = None
        self.etapes.append({"type": "confirmation", "action": action["texte"], "decision": "acceptée" if accepte else "refusée"})
        if not accepte:
            self._repondre_outil(appel, {"ok": False, "erreur": "L'utilisateur a refusé cette action. Ne la propose pas de nouveau."})
            return
        try:
            if action["type"] == "ajouter":
                self.liste.ajouter(action["fiche"])
            else:
                self.liste.retirer(action["tmdb_id"], action["type_oeuvre"])
            # Message explicite : avec un simple {"ok": true}, le modèle redemandait parfois
            # l'accord de l'utilisateur alors que l'action était déjà faite.
            resultat = {"ok": True, "message": "L'utilisateur a confirmé : l'action est faite. Ne redemande pas son accord.",
                        "liste": self.liste.films}
        except ErreurRegle as erreur:  # la liste partagée a pu changer pendant l'attente
            resultat = {"ok": False, "erreur": str(erreur)}
        self.etapes.append({"type": "ecriture", "action": action["type"], "tmdb_id": action["tmdb_id"], "ok": resultat["ok"]})
        self._repondre_outil(appel, resultat)

    # --- Fin -----------------------------------------------------------------------------

    def _conclure(self, texte_brut):
        statut, texte = lire_sortie(texte_brut)
        donnees = lire_json(texte_brut)
        numeros = {int(n) for groupe in re.findall(r"\[([\d\s,]+)\]", texte) for n in re.findall(r"\d+", groupe)}
        sources = donnees.get("sources", []) if isinstance(donnees, dict) else []
        if isinstance(sources, list):
            numeros |= {int(n) for n in sources if str(n).isdigit()}
        numeros = sorted(n for n in numeros if 1 <= n <= len(self.preuves))
        # Même règle qu'au niveau 1 : une réponse factuelle sans citation valide n'est pas donnée.
        # Elle ne s'applique pas au compte rendu d'une modification de la liste.
        if statut == "reponse" and not numeros and not self.ecriture_demandee:
            self.etapes.append({"type": "regle", "detail": "citation manquante"})
            statut, texte = "abstention", "Je ne peux pas répondre : aucune source ne justifie une réponse."
        self._terminer(statut, texte, numeros if statut == "reponse" else [])

    def _terminer(self, statut, texte, numeros):
        self.fin = {"statut": statut, "texte": texte, "sources": sorted({self.preuves[n - 1]["doc_id"] for n in numeros})}

    def sortie(self):
        return {
            "niveau": 2,
            **self.fin,
            "passages": self.preuves,  # tout ce que le modèle a vu et pouvait citer (pour le juge)
            "passages_recherche": self.passages_recherche,
            "liste_finale": self.liste.films,
            "etapes": self.etapes,
            "appels_llm": self.appels_llm,
            "tokens": self.tokens,
            "latence": self.latence,
        }


def _texte_fiche(fiche):
    """Version texte d'un résultat TMDB, telle que le juge de fidélité la lira."""
    champs = {k: v for k, v in fiche.items() if v not in (None, [], "")}
    return "TMDB — " + " ; ".join(f"{k} : {', '.join(map(str, v)) if isinstance(v, list) else v}" for k, v in champs.items())


def _resume(resultat, limite=400):
    texte = json.dumps(resultat, ensure_ascii=False)
    return texte if len(texte) <= limite else texte[:limite] + "…"


def refuser_tout(action):
    return False


def repondre(question, essai=0, liste=None, confirmer=refuser_tout):
    """Traite une requête de bout en bout. `confirmer(action)` joue le rôle de l'utilisateur.

    Par défaut, toute écriture est refusée : une question simple ne doit jamais modifier la liste.
    """
    session = Session(question, liste, essai).avancer()
    while session.attente is not None:
        session.avancer(confirmer(session.attente["action"]))
    return session.sortie()
