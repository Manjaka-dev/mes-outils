# -*- coding: utf-8 -*-
"""Tests de l'onglet Extraits : ajout, modification, suppression, recherche,
filtres, compteur d'utilisations et routes."""
import unittest
from unittest import mock

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # aide.py, quel que soit le lancement

from aide import ConfigTemporaire, ServeurTest

import config  # noqa: E402
import extraits  # noqa: E402
import presse_papiers  # noqa: E402


def _exemples():
    a = extraits.enregistrer({"titre": "Lister les fichiers", "langage": "bash", "contenu": "ls -la",
                              "etiquettes": "shell, #fichiers"})
    b = extraits.enregistrer({"titre": "Compter les lignes", "langage": "SQL",
                              "contenu": "SELECT count(*) FROM matable;", "etiquettes": ["base", "Base", "rapide"]})
    c = extraits.enregistrer({"titre": "Démarrer le serveur", "langage": "bash", "contenu": "python -m http.server"})
    return a, b, c


class TestExtraits(unittest.TestCase):
    def test_creer_modifier_supprimer(self):
        with ConfigTemporaire():
            a, b, c = _exemples()
            self.assertEqual(len(extraits.lister()), 3)
            self.assertEqual(a["etiquettes"], ["shell", "fichiers"], "« # » retiré, texte découpé")
            self.assertEqual(b["etiquettes"], ["base", "rapide"], "doublon (casse ignorée) retiré")
            self.assertEqual(a["utilisations"], 0)
            modifie = extraits.enregistrer({**a, "titre": "Lister tout", "contenu": "ls -lah"})
            self.assertEqual((modifie["id"], modifie["titre"]), (a["id"], "Lister tout"))
            self.assertEqual(len(config.lire_donnees("extraits")), 3, "pas de doublon après modification")
            self.assertEqual(extraits.supprimer(a["id"]), 1)
            self.assertEqual(extraits.supprimer(a["id"]), 0)
            self.assertEqual([e["id"] for e in extraits.lister(tri="titre")], [b["id"], c["id"]])

    def test_valeurs_refusees(self):
        with ConfigTemporaire():
            for mauvais in ({"titre": "", "contenu": "x"}, {"titre": "x", "contenu": "  "},
                            {"titre": "x" * 200, "contenu": "x"}, {"id": "inconnu", "titre": "x", "contenu": "y"}):
                with self.assertRaises(ValueError, msg=str(mauvais)[:60]):
                    extraits.enregistrer(mauvais)
            self.assertEqual(extraits.lister(), [], "rien n'est enregistré après un refus")

    def test_recherche_et_filtres(self):
        with ConfigTemporaire():
            a, b, c = _exemples()
            ids = lambda **f: {e["id"] for e in extraits.lister(**f)}  # noqa: E731
            self.assertEqual(ids(recherche="DEMARRER"), {c["id"]}, "casse et accents ignorés")
            self.assertEqual(ids(recherche="count matable"), {b["id"]}, "plein texte, tous les mots")
            self.assertEqual(ids(recherche="count absent"), set())
            self.assertEqual(ids(recherche="rapide"), {b["id"]}, "les étiquettes sont cherchées")
            self.assertEqual(ids(langage="Bash"), {a["id"], c["id"]})
            self.assertEqual(ids(etiquette="shell"), {a["id"]})
            self.assertEqual(ids(langage="bash", recherche="serveur"), {c["id"]})

    def test_compteur_et_tri(self):
        with ConfigTemporaire():
            a, b, c = _exemples()
            for _ in range(3):
                extraits.utiliser(c["id"])
            extraits.utiliser(b["id"])
            self.assertEqual([e["id"] for e in extraits.lister()], [c["id"], b["id"], a["id"]],
                             "les plus utilisés en tête")
            extraits.epingler(a["id"], True)
            self.assertEqual(extraits.lister()[0]["id"], a["id"], "les épinglés passent avant tout")
            self.assertEqual(extraits.lister()[1]["utilisations"], 3)

    def test_copier(self):
        with ConfigTemporaire():
            a, _, _ = _exemples()
            with mock.patch.object(presse_papiers, "ecrire_texte") as ecrire:
                r = extraits.copier(a["id"])
            ecrire.assert_called_once_with("ls -la")
            self.assertEqual(r["utilisations"], 1)
            with self.assertRaises(ValueError):
                extraits.copier("inconnu")


class TestRoutes(ServeurTest):
    def test_routes(self):
        with ConfigTemporaire():
            statut, e = self.post("/api/extraits/enregistrer",
                                  {"extrait": {"titre": "Statut", "langage": "git", "contenu": "git status", "etiquettes": "git"}})
            self.assertEqual(statut, 200)
            statut, r = self.post("/api/extraits/enregistrer", {"extrait": {"titre": "", "contenu": "x"}})
            self.assertEqual((statut, r["erreur"]), (400, "Donnez un titre à l'extrait."))
            with mock.patch.object(presse_papiers, "ecrire_texte") as ecrire:
                statut, r = self.post("/api/extraits/copier", {"id": e["id"]})
            self.assertEqual((statut, r["utilisations"]), (200, 1))
            ecrire.assert_called_once_with("git status")
            statut, r = self.post("/api/extraits/liste", {"recherche": "status"})
            self.assertEqual((statut, r["total"], r["langages"], r["etiquettes"]), (200, 1, ["git"], ["git"]))
            self.assertEqual(len(r["extraits"]), 1)
            statut, r = self.post("/api/extraits/supprimer", {"id": e["id"]})
            self.assertEqual((statut, r["supprimes"]), (200, 1))


if __name__ == "__main__":
    unittest.main()
