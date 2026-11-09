# -*- coding: utf-8 -*-
"""Aides communes aux tests de « Mes outils ».

- ConfigTemporaire : outils.json et dossier donnees temporaires (les vrais
  fichiers de l'utilisateur ne sont jamais touchés) ;
- ServeurTest : le serveur du tableau de bord sur un port libre, avec
  post() et get() qui posent les bons en-têtes.

Utilisation :
    from aide import ConfigTemporaire, ServeurTest

    class TestX(ServeurTest):
        def test_y(self):
            with ConfigTemporaire({"prenom": "Test"}) as cfg:
                statut, r = self.post("/api/module/action", {...})
"""
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest import mock

OUTIL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outil")
if OUTIL not in sys.path:
    sys.path.insert(0, OUTIL)

import config  # noqa: E402


class ConfigTemporaire:
    """Remplace outils.json et le dossier donnees par des copies temporaires."""

    def __init__(self, contenu=None):
        self.contenu = {"outils": []} if contenu is None else contenu

    def __enter__(self):
        self.dossier = tempfile.mkdtemp(prefix="mes-outils-test-")
        self.fichier = os.path.join(self.dossier, "outils.json")
        self.donnees = os.path.join(self.dossier, "donnees")
        with open(self.fichier, "w", encoding="utf-8") as f:
            json.dump(self.contenu, f, ensure_ascii=False)
        self.patchs = [mock.patch.object(config, "FICHIER_OUTILS", self.fichier),
                       mock.patch.object(config, "DONNEES", self.donnees),
                       mock.patch.object(config, "FICHIER_EXEMPLE", os.path.join(self.dossier, "absent.json"))]
        for p in self.patchs:
            p.start()
        return self

    def lire(self):
        with open(self.fichier, encoding="utf-8") as f:
            return json.load(f)

    def __exit__(self, *exc):
        for p in self.patchs:
            p.stop()
        shutil.rmtree(self.dossier, ignore_errors=True)


class ServeurTest(unittest.TestCase):
    """Le serveur du tableau de bord sur un port libre, le temps des tests."""

    @classmethod
    def setUpClass(cls):
        import hub
        cls.hub = hub
        cls.serveur = ThreadingHTTPServer(("127.0.0.1", 0), hub.Gestionnaire)
        threading.Thread(target=cls.serveur.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def _requete(self, methode, chemin, donnees=None, entete=True):
        c = http.client.HTTPConnection("127.0.0.1", self.serveur.server_address[1], timeout=20)
        entetes = {"Host": f"127.0.0.1:{self.hub.PORT}", "Content-Type": "application/json"}
        if entete:
            entetes["X-Mes-Outils"] = "1"
        corps = json.dumps(donnees) if donnees is not None else None
        c.request(methode, chemin, body=corps, headers=entetes)
        try:
            r = c.getresponse()
            brut = r.read()
            try:
                return r.status, json.loads(brut or b"{}")
            except ValueError:
                return r.status, brut
        finally:
            c.close()

    def post(self, chemin, donnees=None, entete=True):
        return self._requete("POST", chemin, donnees if donnees is not None else {}, entete)

    def get(self, chemin, entete=True):
        return self._requete("GET", chemin, None, entete)
