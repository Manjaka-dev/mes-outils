# -*- coding: utf-8 -*-
"""Tests de l'onglet « Testeur d'API » (requetes.py).

Un petit serveur HTTP local, lancé par les tests, joue le rôle de l'API :
aucun appel vers Internet.
"""
import gzip
import json
import os
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Lancement possible par « -m unittest tests.test_requetes » comme par « discover -s tests ».
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aide import ConfigTemporaire, ServeurTest  # noqa: E402

import config  # noqa: E402
import requetes  # noqa: E402

JETON = "jeton-de-test-123"


class FausseApi(BaseHTTPRequestHandler):
    """Répond selon le chemin ; renvoie en JSON ce qu'elle a reçu."""

    def log_message(self, *args):
        pass

    def _envoyer(self, code, corps=b"", type_contenu="application/json", entetes=()):
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        for k, v in entetes:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(corps)
            except ConnectionError:
                pass  # le client a abandonné (test du délai dépassé)

    def _traiter(self):
        longueur = int(self.headers.get("Content-Length") or 0)
        recu = self.rfile.read(longueur) if longueur else b""
        chemin = self.path
        if chemin.startswith("/echo"):
            corps = json.dumps({"methode": self.command, "chemin": chemin,
                                "entetes": {k.lower(): v for k, v in self.headers.items()},
                                "corps": recu.decode("utf-8")}).encode("utf-8")
            return self._envoyer(200, corps, "application/json; charset=utf-8", [("X-Essai", "oui")])
        if chemin == "/redirection":
            return self._envoyer(302, b"", "text/plain", [("Location", "/echo?apres=1")])
        if chemin == "/vers-ftp":
            return self._envoyer(302, b"", "text/plain", [("Location", "ftp://exemple.invalid/x")])
        if chemin == "/lent":
            time.sleep(3)
            return self._envoyer(200, b"{}")
        if chemin == "/binaire":
            return self._envoyer(200, bytes(range(256)) * 4, "application/octet-stream")
        if chemin == "/gros":
            return self._envoyer(200, b"a" * (requetes.LIMITE_CORPS + 1000), "text/plain")
        if chemin == "/gzip":
            return self._envoyer(200, gzip.compress(b'{"ok": true}'), "application/json", [("Content-Encoding", "gzip")])
        if chemin == "/texte":
            return self._envoyer(200, "Bonjour, ça va ?".encode("latin-1"), "text/plain; charset=iso-8859-1")
        if chemin == "/erreur":
            return self._envoyer(404, b'{"erreur": "absent"}')
        return self._envoyer(500, b"inconnu", "text/plain")

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _traiter


class AvecFausseApi(ServeurTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = ThreadingHTTPServer(("127.0.0.1", 0), FausseApi)
        cls.api.daemon_threads = True
        threading.Thread(target=cls.api.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.api.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.api.shutdown()
        cls.api.server_close()
        super().tearDownClass()

    def setUp(self):
        self.cfg = ConfigTemporaire()
        self.cfg.__enter__()

    def tearDown(self):
        self.cfg.__exit__(None, None, None)

    def requete(self, url, **autres):
        r = {"methode": "GET", "url": url, "params": [], "entetes": [], "corps": {"type": "aucun"},
             "auth": {"type": "aucune"}, "options": {}}
        r.update(autres)
        return r

    def envoyer(self, url, **autres):
        return requetes.envoyer({"requete": self.requete(url, **autres)})["reponse"]


class TestEnvoi(AvecFausseApi):
    def test_get_json_parametres_et_entetes(self):
        rep = self.envoyer(self.base + "/echo?x=1",
                           params=[{"cle": "q", "valeur": "é t", "actif": True}, {"cle": "off", "valeur": "1", "actif": False}],
                           entetes=[{"cle": "X-Demo", "valeur": "42", "actif": True}])
        self.assertEqual(rep["statut"], 200)
        self.assertEqual(rep["type"], "json", "une réponse JSON est reconnue")
        recu = json.loads(rep["corps"])
        self.assertEqual(recu["chemin"], "/echo?x=1&q=%C3%A9+t", "paramètres ajoutés, ligne désactivée ignorée")
        self.assertEqual(recu["entetes"]["x-demo"], "42")
        self.assertIn(["X-Essai", "oui"], [list(e) for e in rep["entetes"]])
        self.assertIn("\n  ", rep["corps"], "le JSON est mis en forme")
        self.assertGreater(rep["duree_ms"], 0)

    def test_post_json_et_formulaire(self):
        rep = self.envoyer(self.base + "/echo", methode="POST", corps={"type": "json", "texte": '{"a": 1}'})
        recu = json.loads(rep["corps"])
        self.assertEqual((recu["methode"], recu["corps"]), ("POST", '{"a": 1}'))
        self.assertTrue(recu["entetes"]["content-type"].startswith("application/json"))
        rep = self.envoyer(self.base + "/echo", methode="PUT", corps={"type": "formulaire", "champs": [
            {"cle": "nom", "valeur": "a b&c", "actif": True}, {"cle": "x", "valeur": "y", "actif": False}]})
        recu = json.loads(rep["corps"])
        self.assertEqual((recu["methode"], recu["corps"]), ("PUT", "nom=a+b%26c"))
        self.assertEqual(recu["entetes"]["content-type"], "application/x-www-form-urlencoded")

    def test_authentification(self):
        rep = self.envoyer(self.base + "/echo", auth={"type": "bearer", "jeton": JETON})
        self.assertEqual(json.loads(rep["corps"])["entetes"]["authorization"], "Bearer " + JETON)
        rep = self.envoyer(self.base + "/echo", auth={"type": "basic", "utilisateur": "u", "mot_de_passe": "p"})
        self.assertEqual(json.loads(rep["corps"])["entetes"]["authorization"], "Basic dTpw")

    def test_redirection_suivie_ou_non(self):
        rep = self.envoyer(self.base + "/redirection")
        self.assertEqual((rep["statut"], rep["redirections"]), (200, 1))
        self.assertTrue(rep["url_finale"].endswith("/echo?apres=1"))
        rep = self.envoyer(self.base + "/redirection", options={"redirections": False})
        self.assertEqual(rep["statut"], 302, "sans suivi, la 302 est rendue telle quelle")
        self.assertIn("/echo?apres=1", dict(rep["entetes"])["Location"])
        rep = self.envoyer(self.base + "/vers-ftp")
        self.assertEqual(rep["statut"], 302, "jamais de redirection vers autre chose que http(s)")

    def test_erreur_http_est_une_reponse(self):
        rep = self.envoyer(self.base + "/erreur")
        self.assertEqual((rep["statut"], rep["type"]), (404, "json"))

    def test_delai_depasse(self):
        with self.assertRaisesRegex(requetes.ErreurRequete, "délai dépassé"):
            self.envoyer(self.base + "/lent", options={"timeout": 1})

    def test_binaire_gros_gzip_charset(self):
        rep = self.envoyer(self.base + "/binaire")
        self.assertEqual((rep["type"], rep["taille"], rep["corps"]), ("binaire", 1024, ""))
        rep = self.envoyer(self.base + "/gros")
        self.assertTrue(rep["tronque"])
        self.assertEqual(len(rep["corps"]), requetes.LIMITE_CORPS, "corps coupé à 5 Mo")
        self.assertEqual(rep["taille"], requetes.LIMITE_CORPS + 1000, "taille réelle annoncée par le serveur")
        rep = self.envoyer(self.base + "/gzip")
        self.assertEqual(json.loads(rep["corps"]), {"ok": True}, "réponse gzip décompressée")
        rep = self.envoyer(self.base + "/texte")
        self.assertEqual((rep["type"], rep["corps"]), ("texte", "Bonjour, ça va ?"))

    def test_head_et_options(self):
        rep = self.envoyer(self.base + "/echo", methode="HEAD")
        self.assertEqual((rep["statut"], rep["type"]), (200, "vide"))
        rep = self.envoyer(self.base + "/echo", methode="OPTIONS")
        self.assertEqual(json.loads(rep["corps"])["methode"], "OPTIONS")

    def test_connexion_refusee(self):
        with self.assertRaisesRegex(requetes.ErreurRequete, "refusée|Échec"):
            self.envoyer("http://127.0.0.1:1/", options={"timeout": 3})

    def test_variables(self):
        requetes.enregistrer_variables({"variables": {"base_url": self.base, "cle": "v1"}})
        rep = self.envoyer("{{base_url}}/echo", entetes=[{"cle": "X-Cle", "valeur": "{{ cle }}", "actif": True}])
        self.assertEqual(json.loads(rep["corps"])["entetes"]["x-cle"], "v1")
        self.assertEqual(requetes.etat()["historique"][0]["requete"]["url"], "{{base_url}}/echo",
                         "l'historique garde la variable, pas sa valeur")
        with self.assertRaisesRegex(requetes.ErreurRequete, "Variable inconnue"):
            self.envoyer("{{inconnue}}/x")
        with self.assertRaisesRegex(requetes.ErreurRequete, "invalide"):
            requetes.enregistrer_variables({"variables": {"a b": "x"}})


class TestRefus(unittest.TestCase):
    def test_schemas_refuses(self):
        for url in ("file:///C:/Windows/win.ini", "ftp://exemple.invalid/", "javascript:alert(1)", "exemple.invalid/x", "http://"):
            with self.subTest(url=url), ConfigTemporaire(), self.assertRaises(requetes.ErreurRequete):
                requetes.envoyer({"requete": {"methode": "GET", "url": url}})

    def test_valeurs_refusees(self):
        cas = [{"methode": "TRACE", "url": "http://127.0.0.1/"},
               {"url": "http://127.0.0.1/", "entetes": [{"cle": "X-A", "valeur": "a\r\nb"}]},
               {"url": "http://127.0.0.1/", "entetes": [{"cle": "Mauvais nom", "valeur": "a"}]},
               {"url": "http://127.0.0.1/", "auth": {"type": "bearer", "jeton": requetes.MASQUE}}]
        for r in cas:
            with self.subTest(r=r), ConfigTemporaire(), self.assertRaises(requetes.ErreurRequete):
                requetes.envoyer({"requete": r})


class TestSecrets(AvecFausseApi):
    def test_historique_sans_secret_et_limite(self):
        for i in range(requetes.MAX_HISTORIQUE + 5):
            requetes.envoyer({"requete": self.requete(
                self.base + f"/echo?n={i}&api_key=cle-secrete",
                entetes=[{"cle": "Authorization", "valeur": "Bearer " + JETON, "actif": True},
                         {"cle": "X-Normal", "valeur": "visible", "actif": True}],
                auth={"type": "basic", "utilisateur": "moi", "mot_de_passe": "mdp-secret"},
                methode="POST", corps={"type": "json", "texte": '{"login": "a", "password": "mdp-corps"}'})})
        hist = requetes.etat()["historique"]
        self.assertEqual(len(hist), requetes.MAX_HISTORIQUE, "historique limité à 50")
        self.assertIn("n=54", hist[0]["requete"]["url"], "la plus récente en premier")
        with open(config.chemin_donnees("requetes"), encoding="utf-8") as f:
            brut = f.read()
        for secret in (JETON, "mdp-secret", "cle-secrete", "mdp-corps"):
            self.assertNotIn(secret, brut, f"secret écrit sur le disque : {secret}")
        r = hist[0]["requete"]
        self.assertEqual(r["entetes"][0]["valeur"], requetes.MASQUE, "Authorization masqué")
        self.assertEqual(r["entetes"][1]["valeur"], "visible", "les autres en-têtes restent")
        self.assertEqual((r["auth"]["type"], r["auth"]["mot_de_passe"]), ("basic", requetes.MASQUE))
        self.assertEqual(json.loads(r["corps"]["texte"])["login"], "a")

    def test_requete_masquee_refusee_au_renvoi(self):
        requetes.envoyer({"requete": self.requete(self.base + "/echo", auth={"type": "bearer", "jeton": JETON})})
        ancienne = requetes.etat()["historique"][0]["requete"]
        with self.assertRaisesRegex(requetes.ErreurRequete, "masquée"):
            requetes.envoyer({"requete": ancienne})

    def test_requetes_enregistrees(self):
        r = self.requete(self.base + "/echo", auth={"type": "bearer", "jeton": JETON},
                         entetes=[{"cle": "Cookie", "valeur": "sid=abc", "actif": True}])
        e = requetes.enregistrer({"nom": "Écho", "collection": "Démo", "requete": r})["enregistree"]
        self.assertEqual((e["nom"], e["collection"]), ("Écho", "Démo"))
        self.assertEqual(e["requete"]["auth"], {"type": "bearer", "jeton": "", "utilisateur": "", "mot_de_passe": ""},
                         "l'authentification n'est pas enregistrée")
        self.assertEqual(e["requete"]["entetes"][0]["valeur"], requetes.MASQUE)
        requetes.enregistrer({"id": e["id"], "nom": "Écho 2", "collection": "", "requete": r})
        liste = requetes.etat()["enregistrees"]
        self.assertEqual([x["nom"] for x in liste], ["Écho 2"], "même id : mise à jour, pas de doublon")
        with self.assertRaisesRegex(requetes.ErreurRequete, "nom"):
            requetes.enregistrer({"nom": " ", "requete": r})
        requetes.supprimer({"id": e["id"]})
        self.assertEqual(requetes.etat()["enregistrees"], [])
        with self.assertRaises(requetes.ErreurRequete):
            requetes.supprimer({"id": e["id"]})

    def test_curl(self):
        r = self.requete("https://exemple.invalid/a b", methode="POST", corps={"type": "json", "texte": "{\"t\": \"l'été\"}"},
                         auth={"type": "bearer", "jeton": JETON}, options={"ignorer_tls": True, "timeout": 5})
        commande = requetes.curl({"requete": r})["commande"]
        self.assertTrue(commande.startswith("curl 'https://exemple.invalid/a b'"), commande)
        self.assertIn("-H 'Authorization: Bearer " + JETON + "'", commande, "le cURL copié garde l'authentification")
        self.assertIn("--data-raw '{\"t\": \"l'\"'\"'été\"}'", commande, "apostrophe échappée pour bash")
        self.assertIn(" -k", commande)
        self.assertNotIn("-X POST", commande, "POST implicite avec --data-raw")


class TestRoutes(AvecFausseApi):
    def test_routes_par_le_serveur(self):
        statut, r = self.post("/api/requetes/etat", {})
        self.assertEqual((statut, r["historique"], r["enregistrees"]), (200, [], []))
        statut, r = self.post("/api/requetes/envoyer", {"requete": self.requete(self.base + "/echo")})
        self.assertEqual((statut, r["reponse"]["statut"], len(r["historique"])), (200, 200, 1))
        statut, r = self.post("/api/requetes/envoyer", {"requete": self.requete("file:///C:/x")})
        self.assertEqual(statut, 400)
        self.assertIn("http://", r["erreur"])
        statut, r = self.post("/api/requetes/historique/vider", {})
        self.assertEqual((statut, r["historique"]), (200, []))
        statut, _ = self.post("/api/requetes/envoyer", {"requete": self.requete(self.base + "/echo")}, entete=False)
        self.assertEqual(statut, 403, "sans l'en-tête X-Mes-Outils, rien ne part")


if __name__ == "__main__":
    unittest.main()
