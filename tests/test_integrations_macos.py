# -*- coding: utf-8 -*-
"""Vérifications du portage macOS avec des données isolées."""
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest import mock

from aide import ConfigTemporaire


@unittest.skipUnless(sys.platform == "darwin", "Intégrations spécifiques à macOS.")
class TestIntegrationsMac(unittest.TestCase):
    def test_presse_papiers_exclut_le_secret_et_conserve_la_copie_suivante(self):
        import presse_papiers as pp
        import presse_papiers_macos as mac

        planche = mac.NSPasteboard.pasteboardWithUniqueName()
        try:
            with mock.patch.object(mac, "NSPasteboard") as appkit:
                appkit.generalPasteboard.return_value = planche
                source = mac.SourceMac()
                historique = pp.Historique()
                surveillance = pp.Surveillance(historique, source)
                jeton = b"test-effacement"
                mac._ecrire("secret de test", jeton)
                self.assertIsNone(surveillance.sonder())
                self.assertEqual(source.lire(), (None, "exclu"))
                source.ecrire("texte public après la copie")
                mac._effacer(jeton)
                self.assertEqual(surveillance.sonder()["texte"], "texte public après la copie")
                self.assertEqual(len(historique), 1)
                mac._ecrire("autre secret de test", jeton)
                mac._effacer(jeton)
                self.assertIsNone(source.lire()[0])
        finally:
            planche.releaseGlobally()

    def test_ports_arrete_uniquement_le_processus_identifie(self):
        import ports

        programme = ("import socket; "
                     "s=socket.create_server(('127.0.0.1', 0)); "
                     "print(s.getsockname()[1], flush=True); s.accept()")
        p = subprocess.Popen([sys.executable, "-c", programme], stdout=subprocess.PIPE, text=True)
        try:
            port = int(p.stdout.readline())
            self.assertGreater(port, 0)
            ligne = next(e for e in ports.lister_ports(forcer=True) if e["pid"] == p.pid and e["port"] == port)
            self.assertFalse(ligne["protege"])
            with self.assertRaisesRegex(ValueError, "processus ou le port"):
                ports.arreter({**ligne, "cree": "ancienne identité"})
            self.assertIsNone(p.poll())
            self.assertTrue(ports.arreter(ligne)["ok"])
            p.wait(timeout=5)
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
            p.stdout.close()

    def test_ssh_alias_existant_et_hote_connu(self):
        import ssh_cles as ssh

        with ConfigTemporaire() as cfg:
            dossier = Path(cfg.dossier) / "profil ssh"
            dossier.mkdir(mode=0o700)
            cle = dossier / "clé de test"
            subprocess.run([ssh.SSH_KEYGEN, "-q", "-t", "ed25519", "-N", "", "-f", str(cle)],
                           check=True, capture_output=True)
            fichier = dossier / "config"
            initial = ("# >>> Mes outils : serveur-test-archive\n"
                       "Host serveur-test-archive\n    HostName autre.invalid\n"
                       "# <<< Mes outils : serveur-test-archive\n")
            fichier.write_text(initial, encoding="utf-8")
            with mock.patch.multiple(ssh, DOSSIER_SSH=str(dossier), CONFIG_SSH=str(fichier),
                                     FICHIER=str(dossier / "ssh.json")):
                s = ssh.ajouter_existant("Serveur test", "exemple.invalid", 2222, "test", str(cle))
                options = subprocess.run([ssh.SSH, "-F", str(fichier), "-G", s["alias"]],
                                         check=True, capture_output=True, text=True).stdout
                self.assertIn(f"identityfile {cle}", options)
                self.assertIn("stricthostkeychecking true", options)
                self.assertIn("StrictHostKeyChecking=yes", ssh._base_ssh(s))
                with mock.patch.object(ssh, "_executer", return_value=mock.Mock(returncode=0)) as ouvrir:
                    self.assertTrue(ssh.ouvrir_terminal(s["alias"])["ok"])
                    self.assertEqual(ouvrir.call_args.args[0][-1], s["alias"])
                self.assertTrue(ssh.retirer(s["alias"])["ok"])
                self.assertTrue(cle.exists())
                self.assertEqual(fichier.read_text(), initial)

    def test_ssh_annule_la_creation_si_l_hote_est_inconnu(self):
        import ssh_cles as ssh

        with ConfigTemporaire() as cfg, mock.patch.multiple(
                ssh, DOSSIER_SSH=cfg.dossier, CONFIG_SSH=os.path.join(cfg.dossier, "config"),
                FICHIER=os.path.join(cfg.dossier, "ssh.json")):
            executer = ssh._executer

            def executer_test(commande, secret=None):
                if commande[0] == ssh.SSH_KEYGEN:
                    return executer(commande)
                self.assertIn("StrictHostKeyChecking=yes", commande)
                return subprocess.CompletedProcess(commande, 255, "", "Host key verification failed.")

            with mock.patch.object(ssh, "_executer", side_effect=executer_test):
                with self.assertRaisesRegex(ssh.ErreurSSH, "empreinte"):
                    ssh.creer("Hôte inconnu", "exemple.invalid", 22, "test", "secret fictif")
            self.assertEqual(ssh.lister(), [])
            self.assertFalse(list(Path(cfg.dossier).glob("mesoutils_*")))

    def test_docker_macos_simule(self):
        import conteneurs

        processus = mock.Mock(returncode=0, stdout=b"test\n", stderr=b"")
        with mock.patch.object(conteneurs, "chemin_docker", return_value="/opt/homebrew/bin/docker"), \
                mock.patch.object(conteneurs.subprocess, "run", return_value=processus) as executer:
            self.assertEqual(conteneurs._docker("logs", "conteneur-test"), (0, "test\n", ""))
            executer.assert_called_once_with(["/opt/homebrew/bin/docker", "logs", "conteneur-test"],
                                             capture_output=True, timeout=30)
