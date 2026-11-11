# -*- coding: utf-8 -*-
"""Onglet Extraits : bouts de code et commandes favoris.

Chaque extrait : titre, langage (une étiquette libre : « bash », « sql »…),
contenu, étiquettes, épinglé, nombre d'utilisations. Fichier
donnees\\extraits.json. Routes POST /api/extraits/<action>.

Pour la bulle : lister() (épinglés puis les plus utilisés en tête) et
copier(identifiant) (met le contenu dans le presse-papiers et compte
l'utilisation).
"""
import subprocess
import threading
import time
import unicodedata
import uuid

import config

NOM = "extraits"
MAX_TITRE = 120
MAX_LANGAGE = 30
MAX_ETIQUETTES = 10
MAX_ETIQUETTE = 30
MAX_CONTENU = 100_000
TRIS = ("usage", "titre", "recent")

_verrou = threading.RLock()


def _maintenant():
    return time.strftime("%Y-%m-%dT%H:%M")


def _sans_accents(texte):
    """Minuscules sans accents, pour une recherche tolérante."""
    texte = unicodedata.normalize("NFD", str(texte or "").lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")


def _tous():
    elements = config.lire_donnees(NOM, [])
    return elements if isinstance(elements, list) else []


def _etiquettes(valeur):
    """Liste d'étiquettes propre : depuis une liste ou un texte « a, b, #c »,
    sans doublon (casse ignorée), au plus 10."""
    if isinstance(valeur, str):
        valeur = valeur.replace(";", ",").split(",")
    propres, vues = [], set()
    for e in valeur or []:
        e = str(e).strip().lstrip("#").strip()[:MAX_ETIQUETTE]
        if e and e.lower() not in vues:
            vues.add(e.lower())
            propres.append(e)
    return propres[:MAX_ETIQUETTES]


def _cle_tri(tri):
    if tri == "titre":
        return lambda e: (not e.get("epingle"), _sans_accents(e.get("titre")))
    if tri == "recent":
        return lambda e: (not e.get("epingle"), _inverse(e.get("modifie") or ""))
    # « usage » : épinglés, puis les plus utilisés, puis les derniers utilisés.
    return lambda e: (not e.get("epingle"), -int(e.get("utilisations") or 0),
                      _inverse(e.get("dernier_usage") or ""), _sans_accents(e.get("titre")))


def _inverse(texte):
    """Clé de tri décroissante pour une date ISO (texte)."""
    return [-ord(c) for c in texte]


def lister(recherche="", langage="", etiquette="", tri="usage"):
    """Les extraits filtrés et triés (épinglés toujours en tête).

    recherche : tous les mots doivent se trouver dans le titre, le contenu,
    le langage ou les étiquettes (casse et accents ignorés)."""
    mots = _sans_accents(recherche).split()
    langage = _sans_accents(langage).strip()
    etiquette = _sans_accents(etiquette).strip()
    with _verrou:
        elements = _tous()
    resultat = []
    for e in elements:
        if langage and _sans_accents(e.get("langage")) != langage:
            continue
        if etiquette and etiquette not in [_sans_accents(x) for x in e.get("etiquettes") or []]:
            continue
        if mots:
            botte = _sans_accents(" ".join([e.get("titre") or "", e.get("contenu") or "", e.get("langage") or "",
                                            " ".join(e.get("etiquettes") or [])]))
            if not all(m in botte for m in mots):
                continue
        resultat.append(dict(e))
    resultat.sort(key=_cle_tri(tri if tri in TRIS else "usage"))
    return resultat


def enregistrer(extrait):
    """Créer (sans id) ou modifier (avec id) un extrait. Renvoie l'extrait."""
    if not isinstance(extrait, dict):
        raise ValueError("Extrait invalide.")
    titre = str(extrait.get("titre") or "").strip()
    contenu = str(extrait.get("contenu") or "")
    if not titre:
        raise ValueError("Donnez un titre à l'extrait.")
    if not contenu.strip():
        raise ValueError("L'extrait est vide.")
    if len(titre) > MAX_TITRE:
        raise ValueError("Titre trop long (120 caractères au plus).")
    if len(contenu) > MAX_CONTENU:
        raise ValueError("Extrait trop long (100 000 caractères au plus).")
    propre = {
        "titre": titre,
        "langage": str(extrait.get("langage") or "").strip()[:MAX_LANGAGE],
        "contenu": contenu,
        "etiquettes": _etiquettes(extrait.get("etiquettes")),
        "epingle": bool(extrait.get("epingle")),
        "modifie": _maintenant(),
    }
    with _verrou:
        elements = _tous()
        identifiant = extrait.get("id")
        if identifiant:
            existant = next((e for e in elements if e.get("id") == identifiant), None)
            if existant is None:
                raise ValueError("Extrait introuvable.")
            existant.update(propre)
            resultat = existant
        else:
            resultat = {"id": uuid.uuid4().hex[:12], **propre, "utilisations": 0,
                        "dernier_usage": "", "cree": propre["modifie"]}
            elements.append(resultat)
        config.ecrire_donnees(NOM, elements)
        return dict(resultat)


def supprimer(identifiant):
    """Supprimer un extrait. Renvoie le nombre d'extraits supprimés (0 ou 1)."""
    with _verrou:
        elements = _tous()
        restants = [e for e in elements if e.get("id") != identifiant]
        if len(restants) != len(elements):
            config.ecrire_donnees(NOM, restants)
        return len(elements) - len(restants)


def epingler(identifiant, valeur=True):
    with _verrou:
        elements = _tous()
        e = next((x for x in elements if x.get("id") == identifiant), None)
        if e is None:
            raise ValueError("Extrait introuvable.")
        e["epingle"] = bool(valeur)
        config.ecrire_donnees(NOM, elements)
        return dict(e)


def utiliser(identifiant):
    """Compter une utilisation (copie). Renvoie l'extrait."""
    with _verrou:
        elements = _tous()
        e = next((x for x in elements if x.get("id") == identifiant), None)
        if e is None:
            raise ValueError("Extrait introuvable.")
        e["utilisations"] = int(e.get("utilisations") or 0) + 1
        e["dernier_usage"] = _maintenant()
        config.ecrire_donnees(NOM, elements)
        return dict(e)


def copier(identifiant):
    """Mettre le contenu de l'extrait dans le presse-papiers et compter
    l'utilisation. Renvoie l'extrait."""
    with _verrou:
        e = next((x for x in _tous() if x.get("id") == identifiant), None)
    if e is None:
        raise ValueError("Extrait introuvable.")
    if config.MACOS:
        try:
            subprocess.run(["/usr/bin/pbcopy"], input=e["contenu"].encode("utf-8"),
                           capture_output=True, timeout=5, check=True)
        except (OSError, subprocess.SubprocessError):
            raise ValueError("Impossible de copier cet extrait dans le presse-papiers.") from None
    else:
        import presse_papiers  # ici : ce module touche à user32
        presse_papiers.ecrire_texte(e["contenu"])
    return utiliser(identifiant)


# ---------------------------------------------------------------------------
# Routes de la page
# ---------------------------------------------------------------------------
def _route_liste(d):
    tous = lister()
    filtres = lister(d.get("recherche") or "", d.get("langage") or "", d.get("etiquette") or "", d.get("tri") or "usage")
    langages = sorted({e["langage"] for e in tous if e.get("langage")}, key=_sans_accents)
    etiquettes = sorted({x for e in tous for x in e.get("etiquettes") or []}, key=_sans_accents)
    return {"extraits": filtres, "total": len(tous), "langages": langages, "etiquettes": etiquettes}


ROUTES = {
    "liste": _route_liste,
    "enregistrer": lambda d: enregistrer(d.get("extrait") or {}),
    "supprimer": lambda d: {"supprimes": supprimer(d.get("id"))},
    "epingler": lambda d: epingler(d.get("id"), d.get("epingle", True)),
    "utiliser": lambda d: utiliser(d.get("id")),
    "copier": lambda d: copier(d.get("id")),
}
