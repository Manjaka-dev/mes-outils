# -*- coding: utf-8 -*-
"""Réglages et fichiers de données de « Mes outils », partagés par tous les
modules.

- outils.json : les réglages personnels (prénom, langue, tuiles, dossiers de
  projets…), créé depuis outils.exemple.json au premier lancement, jamais
  envoyé sur GitHub ;
- donnees\\<nom>.json : les données de chaque module (écriture sûre, copie
  .bak de la version précédente).

Les tests remplacent FICHIER_OUTILS et DONNEES par des chemins temporaires.
"""
import json
import os
import shutil
import threading

VERSION = "1.2.0"
DEPOT = "https://github.com/rarianaAina/mes-outils"
ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
FICHIER_OUTILS = os.path.join(RACINE, "outils.json")
FICHIER_EXEMPLE = os.path.join(RACINE, "outils.exemple.json")
DONNEES = os.path.join(RACINE, "donnees")
LANGUES = ("fr", "en")
THEMES = ("auto", "clair", "sombre")

_verrou = threading.RLock()


# ---------------------------------------------------------------------------
# outils.json
# ---------------------------------------------------------------------------
def lire():
    """Le contenu d'outils.json (copié depuis l'exemple s'il n'existe pas)."""
    with _verrou:
        if not os.path.exists(FICHIER_OUTILS) and os.path.exists(FICHIER_EXEMPLE):
            shutil.copyfile(FICHIER_EXEMPLE, FICHIER_OUTILS)
        try:
            with open(FICHIER_OUTILS, encoding="utf-8-sig") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"outils": []}


def ecrire(contenu):
    with _verrou:
        contenu = {k: v for k, v in contenu.items() if k != "bulle"}
        tmp = FICHIER_OUTILS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(contenu, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, FICHIER_OUTILS)


def modifier(**valeurs):
    """Change quelques clés d'outils.json sans toucher au reste."""
    with _verrou:
        contenu = lire()
        contenu.update(valeurs)
        ecrire(contenu)
        return contenu


def section(nom):
    """Une section d'outils.json (dictionnaire vide si absente)."""
    valeur = lire().get(nom)
    return valeur if isinstance(valeur, dict) else {}


def modifier_section(nom, **valeurs):
    with _verrou:
        contenu = lire()
        sec = contenu.get(nom) if isinstance(contenu.get(nom), dict) else {}
        sec.update(valeurs)
        contenu[nom] = sec
        ecrire(contenu)
        return sec


def langue():
    valeur = lire().get("langue") or "fr"
    return valeur if valeur in LANGUES else "fr"


def theme():
    valeur = lire().get("theme") or "auto"
    return valeur if valeur in THEMES else "auto"


def dossiers_projets():
    """Les dossiers où chercher les projets (GitHub, Projets, État Git).
    Ancien emplacement : github > dossiers."""
    contenu = lire()
    dossiers = contenu.get("dossiers_projets")
    if dossiers is None:
        dossiers = (contenu.get("github") or {}).get("dossiers") or []
    return [d for d in dossiers if isinstance(d, str) and d.strip()]


def enregistrer_dossiers_projets(dossiers):
    nouveaux = []
    for chemin in dossiers or []:
        chemin = os.path.normpath(str(chemin).strip().strip('"'))
        if not os.path.isdir(chemin):
            raise ValueError(f"Dossier introuvable : {chemin}")
        if chemin not in nouveaux:
            nouveaux.append(chemin)
    with _verrou:
        contenu = lire()
        contenu["dossiers_projets"] = nouveaux
        if isinstance(contenu.get("github"), dict):
            contenu["github"].pop("dossiers", None)
        ecrire(contenu)
    return nouveaux


# ---------------------------------------------------------------------------
# donnees\<nom>.json
# ---------------------------------------------------------------------------
def chemin_donnees(nom):
    return os.path.join(DONNEES, nom + ".json")


def lire_donnees(nom, defaut=None):
    """Le contenu de donnees\\<nom>.json, ou « defaut » s'il n'existe pas."""
    with _verrou:
        try:
            with open(chemin_donnees(nom), encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return [] if defaut is None else defaut


def ecrire_donnees(nom, valeur):
    """Écriture sûre : fichier temporaire puis remplacement, copie .bak."""
    with _verrou:
        os.makedirs(DONNEES, exist_ok=True)
        chemin = chemin_donnees(nom)
        if os.path.exists(chemin):
            shutil.copyfile(chemin, chemin + ".bak")
        tmp = chemin + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(valeur, f, ensure_ascii=False, indent=1)
        os.replace(tmp, chemin)
