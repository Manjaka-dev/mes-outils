# -*- coding: utf-8 -*-
"""Tests de l'historique du presse-papiers.

- Logique de l'historique avec une fausse source (doublons, limite de 50,
  épinglés, pause) ;
- lecture Windows avec de faux user32 / kernel32 (contenus marqués exclus) ;
- deux essais sur le vrai presse-papiers : un texte copié est capté, un mot
  de passe copié par le coffre ne l'est pas. Le contenu d'avant est remis
  ensuite.
"""
import ctypes
import time
import unittest
import uuid
from ctypes import wintypes
from unittest import mock

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # aide.py, quel que soit le lancement

from aide import ConfigTemporaire, ServeurTest

import config  # noqa: E402
import presse_papiers as pp  # noqa: E402
from presse_papiers import Historique, SourceWindows, Surveillance  # noqa: E402


class FausseSource:
    """Un presse-papiers imaginaire : copier() change le numéro de séquence."""

    def __init__(self):
        self.n = 1
        self.contenu = (None, "pas_de_texte")
        self.occupe = False

    def numero(self):
        return self.n

    def copier(self, texte, raison=None):
        self.n += 1
        self.contenu = (None, raison) if raison else (texte, None)

    def lire(self):
        return (None, "occupe") if self.occupe else self.contenu

    def ecrire(self, texte):
        self.copier(texte)


def surveillance():
    s = Surveillance(Historique(), FausseSource())
    s.oublier_contenu_actuel()
    return s


def textes(s):
    return [e["texte"] for e in s.historique.lister()]


class TestHistorique(unittest.TestCase):
    def test_textes_captes_et_doublons(self):
        s = surveillance()
        self.assertIsNone(s.sonder(), "rien de nouveau")
        for t in ("un", "deux", "deux", "   ", "", "un"):
            s.source.copier(t)
            s.sonder()
        self.assertEqual(textes(s), ["un", "deux"],
                         "vides et doublon du dernier ignorés ; un texte déjà présent remonte en tête")

    def test_limite_et_epingles(self):
        s = surveillance()
        s.source.copier("garde-moi")
        s.sonder()
        s.historique.epingler(s.historique.lister()[0]["id"], True)
        for i in range(70):
            s.source.copier(f"texte {i}")
            s.sonder()
        liste = s.historique.lister()
        self.assertEqual(len(liste), 51, "50 éléments non épinglés + l'épinglé")
        self.assertIn("garde-moi", textes(s), "l'épinglé n'est jamais retiré par la limite")
        self.assertEqual(liste[0]["texte"], "texte 69")
        self.assertNotIn("texte 19", textes(s), "les plus anciens partent")
        self.assertEqual(s.historique.vider(), 50)
        self.assertEqual(textes(s), ["garde-moi"], "« Tout effacer » garde les épinglés")
        self.assertEqual(s.historique.vider(garder_epingles=False), 1)

    def test_pause(self):
        s = surveillance()
        s.actif = False
        s.source.copier("pendant la pause")
        s.sonder()
        s.actif = True
        s.sonder()
        self.assertEqual(textes(s), [], "un texte copié pendant la pause n'est jamais pris")
        s.source.copier("après")
        s.sonder()
        self.assertEqual(textes(s), ["après"])

    def test_exclus_trop_long_et_occupe(self):
        s = surveillance()
        s.source.copier(None, "exclu")
        s.sonder()
        s.historique.ajouter("x" * (pp.TAILLE_MAX + 1))
        self.assertEqual(textes(s), [], "contenu exclu et texte trop long ignorés")
        s.source.occupe = True
        s.source.copier("plus tard")
        s.sonder()
        self.assertEqual(textes(s), [])
        s.source.occupe = False
        s.sonder()
        self.assertEqual(textes(s), ["plus tard"], "presse-papiers occupé : réessayé au coup d'œil suivant")

    def test_fil_demarre_une_seule_fois(self):
        s = Surveillance(Historique(), FausseSource(), intervalle=0.01)
        try:
            self.assertTrue(s.demarrer())
            self.assertFalse(s.demarrer(), "idempotent")
            s.source.copier("par le fil")
            for _ in range(200):
                if len(s.historique):
                    break
                time.sleep(0.01)
            self.assertEqual(textes(s), ["par le fil"])
        finally:
            s.arreter()


# ---------------------------------------------------------------------------
# Lecture Windows simulée : faux user32 et kernel32
# ---------------------------------------------------------------------------
class FauxUser32:
    def __init__(self, formats, ouvrable=True):
        self.formats = formats          # {format: octets}
        self.ouvrable = ouvrable
        self.fermetures = 0

    def OpenClipboard(self, _hwnd):
        return self.ouvrable

    def CloseClipboard(self):
        self.fermetures += 1
        return True

    def IsClipboardFormatAvailable(self, fmt):
        return fmt in self.formats

    def GetClipboardData(self, fmt):
        return fmt if fmt in self.formats else None


class FauxKernel32:
    def __init__(self, user32):
        self.user32 = user32
        self.tampons = {}

    def GlobalSize(self, h):
        return len(self.user32.formats[h])

    def GlobalLock(self, h):
        tampon = ctypes.create_string_buffer(self.user32.formats[h], len(self.user32.formats[h]))
        self.tampons[h] = tampon
        return ctypes.addressof(tampon)

    def GlobalUnlock(self, h):
        return True


EXCLU, HISTORIQUE = 0xC101, 0xC102


def fausse_source(formats, ouvrable=True):
    src = object.__new__(SourceWindows)
    src.u32 = FauxUser32(formats, ouvrable)
    src.k32 = FauxKernel32(src.u32)
    src.fmt_exclu, src.fmt_historique = EXCLU, HISTORIQUE
    return src


def texte_windows(t):
    return (t + "\0").encode("utf-16-le")


class TestLectureWindows(unittest.TestCase):
    def test_texte_lu(self):
        src = fausse_source({pp.CF_UNICODETEXT: texte_windows("Bonjour é😀")})
        self.assertEqual(src.lire(), ("Bonjour é😀", None))
        self.assertEqual(src.u32.fermetures, 1, "le presse-papiers est toujours refermé")

    def test_contenus_exclus(self):
        texte = {pp.CF_UNICODETEXT: texte_windows("secret")}
        self.assertEqual(fausse_source({**texte, EXCLU: b"\0\0\0\0"}).lire(), (None, "exclu"))
        self.assertEqual(fausse_source({**texte, HISTORIQUE: b"\0\0\0\0"}).lire(), (None, "exclu"))
        self.assertEqual(fausse_source({**texte, HISTORIQUE: b"\1\0\0\0"}).lire(), ("secret", None),
                         "CanIncludeInClipboardHistory = 1 : accepté")

    def test_autres_cas(self):
        self.assertEqual(fausse_source({}).lire(), (None, "pas_de_texte"))
        long = {pp.CF_UNICODETEXT: texte_windows("x" * (pp.TAILLE_MAX + 5))}
        self.assertEqual(fausse_source(long).lire(), (None, "trop_long"))
        with mock.patch.object(pp.time, "sleep"):
            self.assertEqual(fausse_source({}, ouvrable=False).lire(), (None, "occupe"))


# ---------------------------------------------------------------------------
# Le vrai presse-papiers (contenu sauvegardé puis remis)
# ---------------------------------------------------------------------------
FORMATS_NON_COPIABLES = {2, 3, 9, 14, 0x80, 0x82, 0x83, 0x8E}   # bitmaps, métafichiers, palette…


def sauver_presse_papiers(src):
    """Copie de tous les formats « mémoire » du presse-papiers."""
    u32, k32 = src.u32, src.k32
    u32.EnumClipboardFormats.argtypes = [wintypes.UINT]
    u32.EnumClipboardFormats.restype = wintypes.UINT
    if not src._ouvrir(40):
        raise unittest.SkipTest("presse-papiers occupé")
    sauvegarde = []
    try:
        fmt = 0
        while True:
            fmt = u32.EnumClipboardFormats(fmt)
            if not fmt:
                break
            if fmt in FORMATS_NON_COPIABLES or 0x200 <= fmt <= 0x3FF:
                continue
            h = u32.GetClipboardData(fmt)
            if not h:
                continue
            taille = k32.GlobalSize(h)
            p = k32.GlobalLock(h)
            if not p:
                continue
            try:
                sauvegarde.append((fmt, ctypes.string_at(p, taille)))
            finally:
                k32.GlobalUnlock(h)
    finally:
        u32.CloseClipboard()
    return sauvegarde


def remettre_presse_papiers(src, sauvegarde):
    u32, k32 = src.u32, src.k32
    if not src._ouvrir(40):
        return
    try:
        u32.EmptyClipboard()
        for fmt, octets in sauvegarde:
            h = k32.GlobalAlloc(pp.GMEM_MOVEABLE, max(1, len(octets)))
            p = k32.GlobalLock(h)
            ctypes.memmove(p, octets, len(octets))
            k32.GlobalUnlock(h)
            if not u32.SetClipboardData(fmt, h):
                k32.GlobalFree(h)
    finally:
        u32.CloseClipboard()


class TestVraiPressePapiers(unittest.TestCase):
    def setUp(self):
        self.src = SourceWindows()
        self.sauvegarde = sauver_presse_papiers(self.src)
        self.surv = Surveillance(Historique(), self.src)
        self.surv.oublier_contenu_actuel()

    def tearDown(self):
        remettre_presse_papiers(self.src, self.sauvegarde)

    def sonder_jusqu_a_changement(self, numero_avant):
        for _ in range(40):
            if self.src.numero() != numero_avant and self.surv._dernier == self.src.numero():
                return
            self.surv.sonder()
            time.sleep(0.05)

    def test_texte_copie_capte(self):
        texte = "Mes outils : essai " + uuid.uuid4().hex
        avant = self.src.numero()
        self.src.ecrire(texte)
        self.sonder_jusqu_a_changement(avant)
        self.assertEqual([e["texte"] for e in self.surv.historique.lister()], [texte])

    def test_copie_du_coffre_ignoree(self):
        import coffre
        texte = "Mes outils : faux secret " + uuid.uuid4().hex
        avant = self.src.numero()
        coffre.copier_presse_papiers(texte)
        self.sonder_jusqu_a_changement(avant)
        self.assertNotEqual(self.src.numero(), avant, "le presse-papiers a bien changé")
        self.assertEqual(self.src.lire(), (None, "exclu"))
        self.assertEqual(self.surv.historique.lister(), [], "un mot de passe du coffre n'entre pas dans l'historique")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
class TestRoutes(ServeurTest):
    def test_routes(self):
        hist = Historique()
        surv = Surveillance(hist, FausseSource(), intervalle=0.01)
        with ConfigTemporaire() as cfg, mock.patch.object(pp, "_historique", hist), \
                mock.patch.object(pp, "_surveillance", surv):
            try:
                statut, r = self.post("/api/presse_papiers/liste", {})
                self.assertEqual((statut, r["surveille"], r["actif"], r["elements"]), (200, True, True, []))
                hist.ajouter("premier\nligne 2")
                hist.ajouter("second")
                statut, r = self.post("/api/presse_papiers/liste", {"recherche": "PREM"})
                self.assertEqual([e["apercu"] for e in r["elements"]], ["premier\nligne 2"])
                self.assertEqual(r["elements"][0]["lignes"], 2)
                premier = r["elements"][0]["id"]
                statut, r = self.post("/api/presse_papiers/recopier", {"id": premier})
                self.assertEqual(statut, 200)
                self.assertEqual(surv.source.contenu, ("premier\nligne 2", None), "remis dans le presse-papiers")
                time.sleep(0.05)
                self.assertEqual([e["texte"] for e in hist.lister()], ["premier\nligne 2", "second"],
                                 "recopié : en tête, sans doublon")
                statut, r = self.post("/api/presse_papiers/epingler", {"id": premier, "epingle": True})
                self.assertEqual((statut, r["epingle"]), (200, True))
                statut, r = self.post("/api/presse_papiers/pause", {"pause": True})
                self.assertEqual((statut, r["actif"]), (200, False))
                self.assertEqual(cfg.lire()["presse_papiers"], {"actif": False}, "réglage gardé")
                statut, r = self.post("/api/presse_papiers/vider", {})
                self.assertEqual((statut, r["supprimes"]), (200, 1))
                statut, r = self.post("/api/presse_papiers/supprimer", {"id": premier})
                self.assertEqual((statut, r["supprimes"]), (200, 1))
                statut, r = self.post("/api/presse_papiers/supprimer", {"id": "x"})
                self.assertEqual(statut, 400)
                self.post("/api/presse_papiers/pause", {"pause": False})
                self.assertTrue(config.section("presse_papiers")["actif"])
            finally:
                surv.arreter()


if __name__ == "__main__":
    unittest.main()
