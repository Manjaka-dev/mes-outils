# -*- coding: utf-8 -*-
"""Notes et agenda de « Mes outils », enregistrés sur ce PC.

Deux fichiers JSON dans le dossier « donnees » : notes.json et agenda.json.
Écriture sûre (fichier temporaire puis remplacement) et sauvegarde du fichier
précédent (.bak) à chaque enregistrement.
"""
import datetime
import json
import os
import shutil
import threading
import uuid

import config  # noqa: E402

DOSSIER = config.DONNEES
_verrou = threading.RLock()


def _chemin(nom):
    return os.path.join(DOSSIER, nom + ".json")


def _lire(nom):
    try:
        with open(_chemin(nom), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _ecrire(nom, elements):
    os.makedirs(DOSSIER, exist_ok=True)
    chemin = _chemin(nom)
    if os.path.exists(chemin):
        shutil.copyfile(chemin, chemin + ".bak")
    tmp = chemin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=1)
    os.replace(tmp, chemin)


def maintenant():
    return datetime.datetime.now().replace(second=0, microsecond=0)


def _iso(d):
    return d.strftime("%Y-%m-%dT%H:%M")


def _date(texte):
    try:
        return datetime.datetime.strptime(texte[:16], "%Y-%m-%dT%H:%M") if texte else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Opérations communes
# ---------------------------------------------------------------------------
def lister(nom):
    with _verrou:
        return _lire(nom)


def enregistrer(nom, element):
    """Créer ou mettre à jour un élément (note ou rendez-vous). Renvoie l'élément."""
    with _verrou:
        elements = _lire(nom)
        element = dict(element)
        element["modifie"] = _iso(maintenant())
        if not element.get("id"):
            element["id"] = uuid.uuid4().hex[:12]
            element["cree"] = element["modifie"]
            elements.append(element)
        else:
            for i, existant in enumerate(elements):
                if existant["id"] == element["id"]:
                    # Un rappel déplacé doit pouvoir sonner à nouveau.
                    if _cle_rappel(nom, existant) != _cle_rappel(nom, element):
                        element["rappel_fait"] = False
                    elements[i] = {**existant, **element}
                    element = elements[i]
                    break
            else:
                elements.append(element)
        _ecrire(nom, elements)
        return element


def supprimer(nom, identifiant):
    with _verrou:
        elements = _lire(nom)
        restants = [e for e in elements if e["id"] != identifiant]
        if len(restants) != len(elements):
            _ecrire(nom, restants)
        return len(elements) - len(restants)


# ---------------------------------------------------------------------------
# Rappels
# ---------------------------------------------------------------------------
def _cle_rappel(nom, e):
    if nom == "notes":
        return e.get("rappel")
    return (e.get("debut"), e.get("rappel_minutes"))


def _heure_rappel(nom, e):
    if nom == "notes":
        return _date(e.get("rappel"))
    debut = _date(e.get("debut"))
    minutes = e.get("rappel_minutes")
    if debut is None or minutes in (None, ""):
        return None
    return debut - datetime.timedelta(minutes=int(minutes))


def rappels_dus():
    """Les rappels arrivés à échéance et pas encore signalés, notes et agenda.

    Un rappel vieux de plus de deux jours (PC éteint pendant les vacances) est
    marqué comme signalé sans sonner : il n'a plus rien d'utile à dire.
    """
    dus = []
    a_l_heure = maintenant()
    with _verrou:
        for nom in ("notes", "agenda"):
            elements = _lire(nom)
            change = False
            for e in elements:
                if e.get("rappel_fait"):
                    continue
                heure = _heure_rappel(nom, e)
                if heure is None or heure > a_l_heure:
                    continue
                if a_l_heure - heure > datetime.timedelta(days=2):
                    e["rappel_fait"] = True
                    change = True
                    continue
                dus.append({
                    "genre": nom,
                    "id": e["id"],
                    "titre": e.get("titre") or ("Note" if nom == "notes" else "Rendez-vous"),
                    "detail": _detail_rappel(nom, e),
                })
            if change:
                _ecrire(nom, elements)
    return dus


def _detail_rappel(nom, e):
    if nom == "notes":
        texte = (e.get("texte") or "").strip()
        if not texte and e.get("elements"):
            restants = [x["texte"] for x in e["elements"] if not x.get("fait")]
            texte = " · ".join(restants[:3])
        return texte[:140]
    debut = _date(e.get("debut"))
    quand = "toute la journée" if e.get("journee") else (debut.strftime("à %H:%M") if debut else "")
    lieu = f" · {e['lieu']}" if e.get("lieu") else ""
    return f"Aujourd'hui {quand}{lieu}" if debut and debut.date() == a_jour() else (
        (debut.strftime("Le %d/%m %H:%M") if debut else "") + lieu)


def a_jour():
    return datetime.date.today()


def marquer_rappel(genre, identifiant, reporter_minutes=None):
    """Rappel vu (OK) ou reporté de quelques minutes (« Plus tard »)."""
    with _verrou:
        elements = _lire(genre)
        for e in elements:
            if e["id"] != identifiant:
                continue
            if reporter_minutes:
                plus_tard = maintenant() + datetime.timedelta(minutes=reporter_minutes)
                if genre == "notes":
                    e["rappel"] = _iso(plus_tard)
                else:
                    debut = _date(e.get("debut"))
                    if debut:
                        e["rappel_minutes"] = int((debut - plus_tard).total_seconds() // 60)
                e["rappel_fait"] = False
            else:
                e["rappel_fait"] = True
            _ecrire(genre, elements)
            return True
    return False
