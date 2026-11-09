# -*- coding: utf-8 -*-
"""Onglet Presse-papiers : historique des textes copiés, sans dépendance.

- Surveillance : un fil d'arrière-plan regarde toutes les 0,7 s le numéro de
  séquence du presse-papiers Windows (GetClipboardSequenceNumber) ; quand il
  change, le texte (CF_UNICODETEXT) est lu, avec quelques réessais si un
  autre programme tient le presse-papiers.
- Ignorés : les contenus marqués « ExcludeClipboardContentFromMonitorProcessing »
  ou « CanIncludeInClipboardHistory » = 0 (gestionnaires de mots de passe, le
  coffre de Mes outils), les textes vides, le doublon du dernier élément, et
  les textes de plus de 100 000 caractères (ignorés en entier : souvent un
  fichier entier, qui encombrerait la mémoire pour rien).
- Un texte déjà présent plus bas dans l'historique remonte en tête (pas de
  doublon dans la liste).
- Uniquement en mémoire, jamais sur disque (il peut contenir des secrets
  copiés ailleurs) : tout est effacé à la fermeture de Mes outils.
- 50 éléments non épinglés au plus ; les épinglés restent (dans la limite de
  50 épinglés).
- Pause / Reprendre : en mémoire, et réglage persistant
  config.section("presse_papiers")["actif"] (vrai par défaut).

Pour la bulle : demarrer_surveillance(), lister(), recopier(id), supprimer(id),
vider(), pause(bool), epingler(id, bool), etat(). Pour les autres modules :
ecrire_texte(texte).
"""
import ctypes
import datetime
import itertools
import threading
import time
from ctypes import wintypes

import config

LIMITE = 50
MAX_EPINGLES = 50
TAILLE_MAX = 100_000
INTERVALLE = 0.7          # secondes entre deux coups d'œil
APERCU = 600              # caractères envoyés à la page pour l'aperçu
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


# ---------------------------------------------------------------------------
# Le vrai presse-papiers Windows (user32 / kernel32)
# ---------------------------------------------------------------------------
class SourceWindows:
    """Lecture et écriture du presse-papiers Windows par ctypes."""

    def __init__(self):
        u32 = ctypes.WinDLL("user32", use_last_error=True)
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        u32.OpenClipboard.argtypes = [wintypes.HWND]
        u32.OpenClipboard.restype = wintypes.BOOL
        u32.CloseClipboard.restype = wintypes.BOOL
        u32.EmptyClipboard.restype = wintypes.BOOL
        u32.GetClipboardSequenceNumber.restype = wintypes.DWORD
        u32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
        u32.IsClipboardFormatAvailable.restype = wintypes.BOOL
        u32.GetClipboardData.argtypes = [wintypes.UINT]
        u32.GetClipboardData.restype = wintypes.HANDLE
        u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        u32.SetClipboardData.restype = wintypes.HANDLE
        u32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
        u32.RegisterClipboardFormatW.restype = wintypes.UINT
        k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        k32.GlobalAlloc.restype = wintypes.HGLOBAL
        k32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        k32.GlobalFree.restype = wintypes.HGLOBAL
        k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalLock.restype = wintypes.LPVOID
        k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalUnlock.restype = wintypes.BOOL
        k32.GlobalSize.argtypes = [wintypes.HGLOBAL]
        k32.GlobalSize.restype = ctypes.c_size_t
        self.u32, self.k32 = u32, k32
        self.fmt_exclu = u32.RegisterClipboardFormatW("ExcludeClipboardContentFromMonitorProcessing")
        self.fmt_historique = u32.RegisterClipboardFormatW("CanIncludeInClipboardHistory")

    def numero(self):
        return self.u32.GetClipboardSequenceNumber()

    def _ouvrir(self, essais=10):
        for _ in range(essais):
            if self.u32.OpenClipboard(None):
                return True
            time.sleep(0.05)
        return False

    def _dword(self, handle):
        if not handle or self.k32.GlobalSize(handle) < 4:
            return None
        p = self.k32.GlobalLock(handle)
        if not p:
            return None
        try:
            return ctypes.c_uint32.from_address(p).value
        finally:
            self.k32.GlobalUnlock(handle)

    def lire(self):
        """(texte, raison) : texte None si rien à prendre, raison parmi
        « occupe », « exclu », « pas_de_texte », « trop_long »."""
        if not self._ouvrir():
            return None, "occupe"
        try:
            u32 = self.u32
            if self.fmt_exclu and u32.IsClipboardFormatAvailable(self.fmt_exclu):
                return None, "exclu"
            if self.fmt_historique and u32.IsClipboardFormatAvailable(self.fmt_historique):
                if self._dword(u32.GetClipboardData(self.fmt_historique)) == 0:
                    return None, "exclu"
            if not u32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                return None, "pas_de_texte"
            h = u32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return None, "pas_de_texte"
            nb = self.k32.GlobalSize(h) // 2
            if nb > TAILLE_MAX + 1:
                return None, "trop_long"
            p = self.k32.GlobalLock(h)
            if not p:
                return None, "pas_de_texte"
            try:
                texte = ctypes.wstring_at(p, nb)
            finally:
                self.k32.GlobalUnlock(h)
            return texte.split("\0", 1)[0], None
        finally:
            u32.CloseClipboard()

    def ecrire(self, texte):
        """Mettre un texte dans le presse-papiers (copie ordinaire)."""
        if not self._ouvrir(20):
            raise RuntimeError("Le presse-papiers est occupé par un autre programme.")
        try:
            self.u32.EmptyClipboard()
            octets = (str(texte) + "\0").encode("utf-16-le")
            h = self.k32.GlobalAlloc(GMEM_MOVEABLE, len(octets))
            if not h:
                raise RuntimeError("Mémoire insuffisante pour copier ce texte.")
            p = self.k32.GlobalLock(h)
            ctypes.memmove(p, octets, len(octets))
            self.k32.GlobalUnlock(h)
            if not self.u32.SetClipboardData(CF_UNICODETEXT, h):
                self.k32.GlobalFree(h)
                raise RuntimeError("Copie dans le presse-papiers impossible.")
        finally:
            self.u32.CloseClipboard()


# ---------------------------------------------------------------------------
# L'historique (en mémoire)
# ---------------------------------------------------------------------------
def _heure():
    return datetime.datetime.now().isoformat(timespec="seconds")


class Historique:
    """Les textes copiés, le plus récent en tête. Rien n'est écrit sur disque."""

    def __init__(self, limite=LIMITE):
        self.limite = limite
        self._elements = []
        self._verrou = threading.RLock()
        self._compteur = itertools.count(1)

    def ajouter(self, texte, quand=None):
        """Ajoute un texte copié. Renvoie l'élément, ou None s'il est ignoré."""
        if not isinstance(texte, str) or not texte.strip() or len(texte) > TAILLE_MAX:
            return None
        with self._verrou:
            if self._elements and self._elements[0]["texte"] == texte:
                return None
            existant = next((e for e in self._elements if e["texte"] == texte), None)
            if existant:
                self._elements.remove(existant)
                existant["quand"] = quand or _heure()
                self._elements.insert(0, existant)
                return dict(existant)
            element = {"id": next(self._compteur), "texte": texte, "quand": quand or _heure(), "epingle": False}
            self._elements.insert(0, element)
            self._rogner()
            return dict(element)

    def _rogner(self):
        libres = [e for e in self._elements if not e["epingle"]]
        for e in libres[self.limite:]:
            self._elements.remove(e)

    def lister(self, recherche=""):
        mots = str(recherche or "").lower().split()
        with self._verrou:
            return [dict(e) for e in self._elements
                    if all(m in e["texte"].lower() for m in mots)]

    def trouver(self, identifiant):
        with self._verrou:
            return next((e for e in self._elements if e["id"] == identifiant), None)

    def remonter(self, identifiant):
        """Passer un élément en tête (il vient d'être recopié)."""
        with self._verrou:
            e = self.trouver(identifiant)
            if e is None:
                raise ValueError("Élément introuvable (déjà effacé ?).")
            self._elements.remove(e)
            e["quand"] = _heure()
            self._elements.insert(0, e)
            return dict(e)

    def supprimer(self, identifiant):
        with self._verrou:
            avant = len(self._elements)
            self._elements = [e for e in self._elements if e["id"] != identifiant]
            return avant - len(self._elements)

    def vider(self, garder_epingles=True):
        with self._verrou:
            avant = len(self._elements)
            self._elements = [e for e in self._elements if garder_epingles and e["epingle"]]
            return avant - len(self._elements)

    def epingler(self, identifiant, valeur=True):
        with self._verrou:
            e = self.trouver(identifiant)
            if e is None:
                raise ValueError("Élément introuvable (déjà effacé ?).")
            if valeur and not e["epingle"] and sum(x["epingle"] for x in self._elements) >= MAX_EPINGLES:
                raise ValueError("50 éléments épinglés au plus : désépinglez-en un d'abord.")
            e["epingle"] = bool(valeur)
            if not valeur:
                self._rogner()
            return dict(e)

    def __len__(self):
        return len(self._elements)


# ---------------------------------------------------------------------------
# La surveillance
# ---------------------------------------------------------------------------
class Surveillance:
    """Regarde le presse-papiers à intervalle régulier et remplit l'historique.

    source : objet avec numero(), lire() → (texte, raison) et ecrire(texte)
    (SourceWindows, ou une fausse source dans les tests)."""

    def __init__(self, historique, source, intervalle=INTERVALLE):
        self.historique = historique
        self.source = source
        self.intervalle = intervalle
        self.actif = True
        self._dernier = None
        self._fil = None
        self._arret = threading.Event()
        self._verrou = threading.Lock()

    def sonder(self):
        """Un coup d'œil. Renvoie l'élément ajouté, ou None."""
        numero = self.source.numero()
        if numero == self._dernier:
            return None
        if not self.actif:
            self._dernier = numero      # copié pendant la pause : jamais pris
            return None
        texte, raison = self.source.lire()
        if raison == "occupe":
            return None                 # on réessaiera au prochain coup d'œil
        self._dernier = numero
        if texte is None:
            return None
        return self.historique.ajouter(texte)

    def oublier_contenu_actuel(self):
        """Le contenu actuel ne sera pas pris (départ, reprise après pause)."""
        self._dernier = self.source.numero()

    def en_marche(self):
        return self._fil is not None and self._fil.is_alive()

    def demarrer(self):
        with self._verrou:
            if self.en_marche():
                return False
            self._arret.clear()
            self.oublier_contenu_actuel()
            self._fil = threading.Thread(target=self._boucle, name="presse-papiers", daemon=True)
            self._fil.start()
            return True

    def arreter(self):
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=3)

    def _boucle(self):
        while not self._arret.is_set():
            try:
                self.sonder()
            except Exception:  # noqa: BLE001 — la surveillance ne doit jamais mourir
                pass
            self._arret.wait(self.intervalle)


# ---------------------------------------------------------------------------
# Le module : un historique et une surveillance pour toute l'appli
# ---------------------------------------------------------------------------
_historique = Historique()
_surveillance = None
_verrou_module = threading.Lock()


def _la_surveillance():
    global _surveillance
    with _verrou_module:
        if _surveillance is None:
            _surveillance = Surveillance(_historique, SourceWindows())
        return _surveillance


def actif_par_reglage():
    return config.section("presse_papiers").get("actif", True) is not False


def demarrer_surveillance():
    """Lancer la surveillance (sans effet si elle tourne déjà). Renvoie etat()."""
    s = _la_surveillance()
    if not s.en_marche():
        s.actif = actif_par_reglage()
        s.demarrer()
    return etat()


def etat():
    s = _surveillance
    return {"actif": bool(s.actif) if s else actif_par_reglage(),
            "surveille": bool(s and s.en_marche()),
            "nombre": len(_la_surveillance().historique),
            "limite": LIMITE}


def lister(recherche=""):
    """Les éléments, le plus récent en tête : [{id, texte, quand, epingle}]."""
    return _la_surveillance().historique.lister(recherche)


def recopier(identifiant):
    """Remettre un élément dans le presse-papiers ; il passe en tête."""
    s = _la_surveillance()
    e = s.historique.remonter(identifiant)
    s.source.ecrire(e["texte"])
    return e


def supprimer(identifiant):
    return _la_surveillance().historique.supprimer(identifiant)


def vider(garder_epingles=True):
    """« Tout effacer » : les épinglés sont gardés, sauf garder_epingles=False."""
    return _la_surveillance().historique.vider(garder_epingles)


def epingler(identifiant, valeur=True):
    return _la_surveillance().historique.epingler(identifiant, valeur)


def pause(valeur=True):
    """pause(True) : plus rien n'est pris ; pause(False) : reprise. Le choix
    est gardé dans les réglages."""
    s = _la_surveillance()
    s.actif = not valeur
    if s.actif:
        s.oublier_contenu_actuel()
    config.modifier_section("presse_papiers", actif=s.actif)
    return etat()


def ecrire_texte(texte):
    """Copie ordinaire d'un texte (utilisée aussi par l'onglet Extraits)."""
    _la_surveillance().source.ecrire(texte)


# ---------------------------------------------------------------------------
# Routes de la page
# ---------------------------------------------------------------------------
def _pour_page(e):
    texte = e["texte"]
    return {"id": e["id"], "apercu": texte[:APERCU], "longueur": len(texte),
            "lignes": texte.count("\n") + 1, "quand": e["quand"], "epingle": e["epingle"]}


def _route_liste(d):
    demarrer_surveillance()     # sans la bulle (tableau de bord seul), la page la lance
    return {**etat(), "elements": [_pour_page(e) for e in lister(d.get("recherche") or "")]}


def _identifiant(d):
    try:
        return int(d.get("id"))
    except (TypeError, ValueError):
        raise ValueError("Élément introuvable (déjà effacé ?).") from None


ROUTES = {
    "liste": _route_liste,
    "recopier": lambda d: _pour_page(recopier(_identifiant(d))),
    "supprimer": lambda d: {"supprimes": supprimer(_identifiant(d))},
    "vider": lambda d: {"supprimes": vider(not d.get("tout"))},
    "epingler": lambda d: _pour_page(epingler(_identifiant(d), bool(d.get("epingle", True)))),
    "pause": lambda d: pause(bool(d.get("pause", True))),
    "etat": lambda d: etat(),
}
