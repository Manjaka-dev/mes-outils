# -*- coding: utf-8 -*-
"""Tests du socle : routes automatiques des modules, liste des onglets,
Réglages et installation (raccourcis créés dans un dossier temporaire)."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from aide import ConfigTemporaire, ServeurTest

import config  # noqa: E402
import installation  # noqa: E402
import reglages  # noqa: E402


class TestSocle(ServeurTest):
    def test_onglets_listes(self):
        with ConfigTemporaire({"langue": "en", "onglets_masques": ["ssh"]}):
            statut, r = self.get("/api/onglets")
        self.assertEqual(statut, 200)
        self.assertIn("reglages.js", r["fichiers"])
        self.assertNotIn("i18n.js", r["fichiers"], "i18n.js est chargé à part, en premier")
        self.assertEqual((r["langue"], r["masques"]), ("en", ["ssh"]))

    def test_module_inconnu_ou_invalide(self):
        for chemin in ("/api/reglages/n_existe_pas", "/api/..%2Fhub/x", "/api/Hub/x", "/api/existe_pas_du_tout/x"):
            statut, _ = self.post(chemin, {})
            self.assertEqual(statut, 404, chemin)

    def test_module_sans_entete_refuse(self):
        statut, _ = self.post("/api/reglages/lire", {}, entete=False)
        self.assertEqual(statut, 403)

    def test_lire_et_enregistrer(self):
        with ConfigTemporaire({"prenom": "Aina", "outils": []}) as cfg:
            statut, r = self.post("/api/reglages/lire", {})
            self.assertEqual((statut, r["prenom"], r["langue"]), (200, "Aina", "fr"))
            statut, r = self.post("/api/reglages/enregistrer",
                                  {"prenom": "  Rado ", "langue": "en", "onglets_masques": ["ssh", "accueil", "reglages"]})
            self.assertEqual(statut, 200)
            contenu = cfg.lire()
        self.assertEqual(contenu["prenom"], "Rado")
        self.assertEqual(contenu["langue"], "en")
        self.assertEqual(contenu["onglets_masques"], ["ssh"], "Accueil et Réglages ne se masquent pas")
        self.assertEqual(contenu["outils"], [], "le reste d'outils.json est conservé")

    def test_valeurs_refusees(self):
        with ConfigTemporaire() as cfg:
            statut, r = self.post("/api/reglages/enregistrer", {"langue": "de"})
            self.assertEqual(statut, 400)
            statut, _ = self.post("/api/reglages/enregistrer", {"onglets_masques": ["<script>"]})
            self.assertEqual(statut, 400)
            self.assertNotIn("langue", cfg.lire(), "rien n'est enregistré après un refus")

    def test_dossiers_projets(self):
        with ConfigTemporaire() as cfg:
            statut, r = self.post("/api/reglages/dossiers", {"dossiers": [cfg.dossier]})
            self.assertEqual((statut, r["dossiers_projets"]), (200, [cfg.dossier]))
            statut, _ = self.post("/api/reglages/dossiers", {"dossiers": [r"Z:\n-existe-pas"]})
            self.assertEqual(statut, 400)
            self.assertEqual(config.dossiers_projets(), [cfg.dossier])

    def test_mise_a_jour_sans_git_refusee(self):
        dossier = tempfile.mkdtemp()
        try:
            with mock.patch.object(config, "RACINE", dossier), self.assertRaisesRegex(ValueError, "git clone"):
                reglages.mise_a_jour()
        finally:
            shutil.rmtree(dossier, ignore_errors=True)


class TestDonnees(unittest.TestCase):
    def test_ecriture_sure_avec_copie(self):
        with ConfigTemporaire():
            self.assertEqual(config.lire_donnees("essai"), [])
            self.assertEqual(config.lire_donnees("essai", {}), {})
            config.ecrire_donnees("essai", [1])
            config.ecrire_donnees("essai", [1, 2])
            self.assertEqual(config.lire_donnees("essai"), [1, 2])
            self.assertTrue(os.path.exists(config.chemin_donnees("essai") + ".bak"))

    def test_premier_lancement_depuis_l_exemple(self):
        with ConfigTemporaire() as cfg:
            os.remove(cfg.fichier)
            exemple = os.path.join(cfg.dossier, "exemple.json")
            with open(exemple, "w", encoding="utf-8") as f:
                f.write('{"prenom": "", "outils": [{"id": "x"}]}')
            with mock.patch.object(config, "FICHIER_EXEMPLE", exemple):
                self.assertEqual(config.lire()["outils"], [{"id": "x"}])
            self.assertTrue(os.path.exists(cfg.fichier))


class TestInstallation(unittest.TestCase):
    def test_dependances_presentes(self):
        self.assertEqual(installation.verifier(), [], "lancer les tests avec le Python de Mes outils")

    def test_raccourci_cree_puis_retire(self):
        dossier = tempfile.mkdtemp()
        try:
            with mock.patch.object(installation, "dossier_special", return_value=dossier):
                self.assertEqual(installation.etat(), {"bureau": False, "demarrage": False})
                chemin = installation.creer_raccourci("bureau")
                self.assertTrue(os.path.isfile(chemin))
                self.assertEqual(installation.etat()["bureau"], True)
                installation.supprimer_raccourci("bureau")
                self.assertFalse(os.path.exists(chemin))
        finally:
            shutil.rmtree(dossier, ignore_errors=True)

    def test_vrais_dossiers_windows(self):
        for genre in ("bureau", "demarrage"):
            self.assertTrue(os.path.isdir(installation.dossier_special(genre)), genre)


if __name__ == "__main__":
    unittest.main()
