# -*- coding: utf-8 -*-
"""Tests de l'onglet « Ports » : lecture de netstat et tasklist (sorties
simulées), refus des arrêts dangereux, arrêt réel d'un petit programme
lancé par le test, et routes HTTP."""
import os
import socket
import subprocess
import sys
import time
import unittest
from unittest import mock

from aide import ServeurTest

import ports  # noqa: E402

NETSTAT = """
Connexions actives

  Proto  Adresse locale         Adresse distante       État
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       1260
  TCP    0.0.0.0:3000           0.0.0.0:0              LISTENING       5100
  TCP    127.0.0.1:5432         0.0.0.0:0              LISTENING       6200
  TCP    127.0.0.1:5432         0.0.0.0:0              LISTENING       6200
  TCP    127.0.0.1:50123        127.0.0.1:5432         ESTABLISHED     5100
  TCP    192.168.1.20:49800     93.184.216.34:443      TIME_WAIT       0
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING       4
  TCP    0.0.0.0:7000           0.0.0.0:0              ABHÖREN         7100
  TCP    [::]:3000              [::]:0                 LISTENING       5100
  TCP    [::1]:8069             [::]:0                 LISTENING       7200
  TCP    [fe80::1%12]:9999      [::]:0                 LISTENING       7200
  UDP    0.0.0.0:5353           *:*                                    8100
  UDP    [::]:5353              *:*                                    8100
"""

TASKLIST = (
    '"System Idle Process","0","Services","0","8 Ko"\r\n'
    '"System","4","Services","0","136 Ko"\r\n'
    '"svchost.exe","1260","Services","0","18\xa0280 Ko"\r\n'
    '"node.exe","5100","Console","1","95 432 K"\r\n'
    '"postgres.exe","6200","Services","0","12 000 Ko"\r\n'
    '"python.exe","7200","Console","1","64 000 Ko"\r\n'
    '"java.exe","7100","Console","1","N/A"\r\n'
    '"chrome.exe","8100","Console","1","210 000 Ko"\r\n'
)


class TestLecture(unittest.TestCase):
    def test_netstat_tcp(self):
        e = ports.lire_netstat(NETSTAT)
        cles = [(x["adresse"], x["port"], x["pid"]) for x in e]
        self.assertIn(("0.0.0.0", 3000, 5100), cles)
        self.assertIn(("::", 3000, 5100), cles, "IPv6 sans crochets")
        self.assertIn(("::1", 8069, 7200), cles)
        self.assertIn(("fe80::1", 9999, 7200), cles, "l'indice d'interface %12 est retiré")
        self.assertIn(("0.0.0.0", 7000, 7100), cles, "état dans une autre langue : reconnu par l'adresse distante")
        self.assertEqual(cles.count(("127.0.0.1", 5432, 6200)), 1, "doublon retiré")
        self.assertNotIn(50123, [x["port"] for x in e], "connexion établie ignorée")
        self.assertNotIn(49800, [x["port"] for x in e], "TIME_WAIT ignoré")
        self.assertFalse([x for x in e if x["proto"] == "UDP"], "UDP seulement sur demande")

    def test_netstat_udp(self):
        udp = [x for x in ports.lire_netstat(NETSTAT, udp=True) if x["proto"] == "UDP"]
        self.assertEqual([(x["adresse"], x["port"], x["pid"]) for x in udp], [("0.0.0.0", 5353, 8100), ("::", 5353, 8100)])

    def test_tasklist(self):
        p = ports.lire_tasklist(TASKLIST)
        self.assertEqual(p[1260], {"nom": "svchost.exe", "memoire_ko": 18280}, "espace insécable dans le nombre")
        self.assertEqual(p[5100]["memoire_ko"], 95432)
        self.assertIsNone(p[7100]["memoire_ko"])
        self.assertEqual(ports.lire_tasklist("Erreur : rien\r\n"), {})

    def test_commandes(self):
        self.assertEqual(ports.lire_commandes('{"ProcessId":5,"CommandLine":"node app.js"}'), {5: "node app.js"})
        self.assertEqual(ports.lire_commandes('[{"ProcessId":5,"CommandLine":null},{"ProcessId":6,"CommandLine":"x"}]'),
                         {5: "", 6: "x"})
        self.assertEqual(ports.lire_commandes(""), {})
        self.assertEqual(ports.lire_commandes("pas du json"), {})

    def test_separer_adresse(self):
        self.assertEqual(ports.separer_adresse("[::1]:5432"), ("::1", 5432))
        self.assertEqual(ports.separer_adresse("*:*"), ("*", None))
        self.assertEqual(ports.separer_adresse("rien"), (None, None))


class TestListe(unittest.TestCase):
    def setUp(self):
        ports.oublier_cache()
        ports._commandes.clear()

    def tearDown(self):
        ports.oublier_cache()
        ports._commandes.clear()

    def _simuler(self):
        def executer(commande, delai=15):
            return NETSTAT if commande[0] == "netstat" else TASKLIST
        return [mock.patch.object(ports, "_executer", side_effect=executer),
                mock.patch.object(ports, "commandes", return_value={5100: "node server.js", 7200: "python -m http.server"}),
                mock.patch.object(ports, "nos_pids", return_value={7200, 1})]

    def test_liste_enrichie(self):
        patchs = self._simuler()
        for p in patchs:
            p.start()
        try:
            liste = ports.lister_ports(forcer=True)
            appels_netstat = ports._executer.call_count
            ports.lister_ports()
            self.assertEqual(ports._executer.call_count, appels_netstat, "deuxième lecture servie par le cache")
        finally:
            for p in patchs:
                p.stop()
        par_port = {(x["port"], x["adresse"]): x for x in liste}
        node = par_port[(3000, "0.0.0.0")]
        self.assertEqual((node["nom"], node["memoire_ko"], node["commande"]), ("node.exe", 95432, "node server.js"))
        self.assertEqual(node["dev"], "Node / React")
        self.assertTrue(node["web"])
        self.assertFalse(node["protege"])
        self.assertFalse(par_port[(5432, "127.0.0.1")]["web"], "PostgreSQL n'est pas une page web")
        self.assertEqual(par_port[(5432, "127.0.0.1")]["dev"], "PostgreSQL")
        self.assertTrue(par_port[(135, "0.0.0.0")]["protege"], "svchost est protégé")
        self.assertTrue(par_port[(445, "0.0.0.0")]["protege"], "PID 4 est protégé")
        self.assertEqual(par_port[(445, "0.0.0.0")]["nom"], "System")
        self.assertTrue(par_port[(8069, "::1")]["soi"], "le processus de Mes outils est signalé")
        self.assertEqual([x["port"] for x in liste], sorted(x["port"] for x in liste), "liste triée par port")

    def test_qui_ecoute(self):
        patchs = self._simuler()
        for p in patchs:
            p.start()
        try:
            r = ports.qui_ecoute(3000)
            self.assertEqual((r["pid"], r["nom"]), (5100, "node.exe"))
            self.assertIsNone(ports.qui_ecoute(3999))
            self.assertIsNone(ports.qui_ecoute("abc"))
        finally:
            for p in patchs:
                p.stop()


class TestArretRefuse(unittest.TestCase):
    def _refus(self, pid, nom, actuel, motif, arbre=False):
        with mock.patch.object(ports, "processus_pid", return_value=actuel), \
                mock.patch.object(ports.subprocess, "run") as run, \
                self.assertRaisesRegex(ValueError, motif):
            ports.arreter({"pid": pid, "nom": nom, "arbre": arbre})
        run.assert_not_called()

    def test_pid_systeme(self):
        self._refus(0, "System Idle Process", {"nom": "System Idle Process"}, "système")
        self._refus(4, "System", {"nom": "System"}, "système")

    def test_programmes_proteges(self):
        for nom in ("svchost.exe", "csrss.exe", "lsass.exe", "explorer.exe", "MsMpEng.exe", "winlogon.exe", "dwm.exe"):
            self._refus(4321, nom, {"nom": nom}, "système")

    def test_mes_outils_lui_meme(self):
        self._refus(os.getpid(), "python.exe", {"nom": "python.exe"}, "Mes outils")
        self._refus(os.getppid(), "python.exe", {"nom": "python.exe"}, "Mes outils")

    def test_pid_reutilise(self):
        self._refus(4321, "node.exe", {"nom": "notepad.exe"}, "autre programme")
        self._refus(4321, "", {"nom": "node.exe"}, "autre programme")

    def test_processus_disparu(self):
        self._refus(4321, "node.exe", None, "n'existe plus")

    def test_arbre_qui_contient_mes_outils(self):
        with mock.patch.object(ports, "ancetres", return_value={os.getpid(), 4321}):
            self._refus(4321, "cmd.exe", {"nom": "cmd.exe"}, "arbre", arbre=True)

    def test_pid_invalide(self):
        for pid in (None, "abc", -3):
            with self.assertRaisesRegex(ValueError, "invalide"):
                ports.arreter({"pid": pid, "nom": "x"})

    def test_commande_taskkill(self):
        ok = subprocess.CompletedProcess([], 0, b"", b"")
        with mock.patch.object(ports, "processus_pid", return_value={"nom": "node.exe"}), \
                mock.patch.object(ports, "ancetres", return_value=set()), \
                mock.patch.object(ports.subprocess, "run", return_value=ok) as run:
            r = ports.arreter({"pid": 4321, "nom": "NODE.EXE", "arbre": True})
        self.assertEqual(r["nom"], "node.exe")
        self.assertEqual(run.call_args[0][0], ["taskkill", "/PID", "4321", "/F", "/T"])

    def test_ancetres_reels(self):
        chaine = ports.ancetres(os.getpid())
        self.assertIn(os.getpid(), chaine)
        self.assertIn(os.getppid(), chaine, "le parent fait partie des ancêtres")


class TestArretReel(unittest.TestCase):
    """Un petit serveur Python lancé par le test, trouvé dans la liste puis arrêté."""

    def test_arret_d_un_programme_de_test(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        code = ("import socket,time\n"
                f"s=socket.socket();s.bind(('127.0.0.1',{port}));s.listen()\n"
                "time.sleep(120)\n")
        prog = subprocess.Popen([sys.executable, "-c", code], creationflags=ports.SANS_FENETRE)
        try:
            entree = None
            for _ in range(50):
                entree = next((e for e in ports.lister_ports(forcer=True) if e["port"] == port), None)
                if entree:
                    break
                time.sleep(0.1)
            self.assertIsNotNone(entree, "le port du programme de test apparaît dans la liste")
            self.assertTrue(entree["nom"].lower().startswith("python"), entree["nom"])
            self.assertEqual(entree["adresse"], "127.0.0.1")
            self.assertEqual(ports.qui_ecoute(port)["pid"], entree["pid"])
            ports.arreter({"pid": entree["pid"], "nom": entree["nom"]})
            for _ in range(50):
                if not any(e["port"] == port for e in ports.lister_ports(forcer=True)):
                    break
                time.sleep(0.1)
            self.assertFalse(any(e["port"] == port for e in ports.lister_ports(forcer=True)),
                             "le port a disparu après l'arrêt")
            prog.wait(timeout=10)
        finally:
            if prog.poll() is None:
                subprocess.run(["taskkill", "/PID", str(prog.pid), "/F", "/T"], capture_output=True,
                               creationflags=ports.SANS_FENETRE)


class TestRoutes(ServeurTest):
    def test_liste(self):
        t0 = time.monotonic()
        statut, r = self.post("/api/ports/liste", {"forcer": True})
        self.assertEqual(statut, 200)
        self.assertLess(time.monotonic() - t0, 8, "la liste reste rapide")
        self.assertTrue(any(e["soi"] for e in r["ports"]), "le serveur de test se voit lui-même")
        statut, r = self.post("/api/ports/liste", {"udp": True})
        self.assertEqual((statut, r["udp"]), (200, True))

    def test_arret_refuse(self):
        statut, r = self.post("/api/ports/arreter", {"pid": 4, "nom": "System"})
        self.assertEqual(statut, 400)
        self.assertIn("système", r["erreur"])
        statut, r = self.post("/api/ports/arreter", {"pid": os.getpid(), "nom": "python.exe"})
        self.assertEqual(statut, 400)
        self.assertIn("Mes outils", r["erreur"])

    def test_chercher_et_ouvrir(self):
        with mock.patch.object(ports, "qui_ecoute", return_value=None):
            statut, r = self.post("/api/ports/chercher", {"port": 3999})
        self.assertEqual((statut, r["resultat"]), (200, None))
        self.assertEqual(self.post("/api/ports/chercher", {"port": 70000})[0], 400)
        with mock.patch.object(ports.webbrowser, "open") as ouvrir:
            statut, _ = self.post("/api/ports/ouvrir", {"port": 5173})
        self.assertEqual(statut, 200)
        ouvrir.assert_called_once_with("http://localhost:5173/")
        with mock.patch.object(ports.webbrowser, "open") as ouvrir:
            self.assertEqual(self.post("/api/ports/ouvrir", {"port": "x"})[0], 400)
        ouvrir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
