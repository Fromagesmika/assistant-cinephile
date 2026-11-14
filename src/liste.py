"""Liste « à voir » partagée, et ses règles métier vérifiées par le code (pas par le modèle).

Règles :
- une œuvre n'apparaît qu'une fois (même identifiant TMDB et même type) ;
- on ne retire que ce qui est dans la liste ;
- la liste est limitée à TAILLE_MAX œuvres.
L'existence de l'œuvre sur TMDB est vérifiée par l'agent avant de demander la confirmation.
"""
import json
from pathlib import Path

TAILLE_MAX = 50


class ErreurRegle(Exception):
    """Action refusée par une règle métier ; le message est renvoyé au modèle."""


class ListeAVoir:
    def __init__(self, films=None, chemin=None):
        """`films` : état de départ (tests) ; `chemin` : fichier JSON où la liste est partagée (interface)."""
        self.chemin = Path(chemin) if chemin else None
        if films is None and self.chemin and self.chemin.exists():
            films = json.loads(self.chemin.read_text(encoding="utf-8"))
        self.films = [dict(f) for f in (films or [])]

    def _position(self, tmdb_id, type_oeuvre):
        for i, film in enumerate(self.films):
            if film["tmdb_id"] == tmdb_id and film.get("type", "film") == type_oeuvre:
                return i
        return None

    def contient(self, tmdb_id, type_oeuvre="film"):
        return self._position(tmdb_id, type_oeuvre) is not None

    def verifier_ajout(self, tmdb_id, type_oeuvre="film"):
        if self.contient(tmdb_id, type_oeuvre):
            raise ErreurRegle("Cette œuvre est déjà dans la liste : rien à ajouter.")
        if len(self.films) >= TAILLE_MAX:
            raise ErreurRegle(f"La liste est pleine ({TAILLE_MAX} œuvres) : retirez-en une d'abord.")

    def verifier_retrait(self, tmdb_id, type_oeuvre="film"):
        if not self.contient(tmdb_id, type_oeuvre):
            raise ErreurRegle("Cette œuvre n'est pas dans la liste : rien à retirer.")

    def ajouter(self, fiche):
        self.verifier_ajout(fiche["tmdb_id"], fiche.get("type", "film"))
        self.films.append({k: fiche[k] for k in ("titre", "annee", "tmdb_id", "type") if k in fiche})
        self._enregistrer()

    def retirer(self, tmdb_id, type_oeuvre="film"):
        self.verifier_retrait(tmdb_id, type_oeuvre)
        del self.films[self._position(tmdb_id, type_oeuvre)]
        self._enregistrer()

    def identifiants(self):
        return sorted(f["tmdb_id"] for f in self.films)

    def _enregistrer(self):
        if self.chemin:
            self.chemin.write_text(json.dumps(self.films, ensure_ascii=False, indent=1), encoding="utf-8")
