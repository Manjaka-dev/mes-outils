# -*- coding: utf-8 -*-
"""Tests de la bulle (sans l'afficher) : langue du menu, modules facultatifs,
textes courts du menu, coffre partagé."""
import unittest

from aide import ConfigTemporaire

import bulle  # noqa: E402
import coffre  # noqa: E402
import hub  # noqa: E402


class TestBulle(unittest.TestCase):
    def test_langue_du_menu(self):
        with ConfigTemporaire({"langue": "fr"}):
            self.assertEqual(bulle.tr("Projets"), "Projets")
        with ConfigTemporaire({"langue": "en"}):
            self.assertEqual(bulle.tr("Projets"), "Projects")
            self.assertEqual(bulle.tr("Arrêter {nom} ?", nom="x"), "Stop x?")
            self.assertEqual(bulle.tr("Texte inconnu"), "Texte inconnu", "un texte sans traduction reste tel quel")

    def test_modules_facultatifs(self):
        self.assertIsNone(bulle.module("module_qui_n_existe_pas"), "un module absent ne doit pas faire planter la bulle")
        for nom in ("projets", "temps", "extraits", "presse_papiers", "github"):
            self.assertIsNotNone(bulle.module(nom), nom)

    def test_fonctions_attendues_par_la_bulle(self):
        """La bulle appelle ces fonctions : elles doivent exister."""
        attendues = {"projets": ["serveurs", "action_commande"], "temps": ["etat", "arreter", "alertes_dues", "marquer_alerte"],
                     "extraits": ["lister", "copier"], "presse_papiers": ["demarrer_surveillance", "lister", "recopier"],
                     "github": ["echecs_ci"]}
        for nom, fonctions in attendues.items():
            m = bulle.module(nom)
            for f in fonctions:
                self.assertTrue(callable(getattr(m, f, None)), f"{nom}.{f}")

    def test_texte_court_pour_le_menu(self):
        self.assertEqual(bulle.Bulle.court("a\nb   c"), "a b c")
        self.assertEqual(len(bulle.Bulle.court("x" * 200)), 48)

    def test_coffre_partage(self):
        self.assertIs(hub.le_coffre(), coffre.partage(), "un seul coffre pour tous les onglets")


if __name__ == "__main__":
    unittest.main()
