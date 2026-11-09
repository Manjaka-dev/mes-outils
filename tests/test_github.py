# -*- coding: utf-8 -*-
"""Tests de l'onglet GitHub (github.py), sans toucher au vrai compte GitHub :
les appels à l'API sont simulés, git travaille sur des dépôts temporaires.

Lancer depuis la racine du projet :  python -m unittest discover -s tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from http.server import ThreadingHTTPServer
from unittest import mock
import http.client

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outil"))
import coffre_windows  # noqa: E402
import github  # noqa: E402

PROFIL_API = {"login": "testeur", "name": "Testeur", "avatar_url": "https://exemple/a.png", "id": 42}


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


class FauxCoffre:
    """Remplace le coffre de Windows le temps d'un test."""

    def __init__(self, valeur=None):
        self.valeurs = {github.CIBLE_COFFRE: valeur} if valeur else {}

    def __enter__(self):
        self.patchs = [
            mock.patch.object(coffre_windows, "lire", side_effect=lambda c: self.valeurs.get(c)),
            mock.patch.object(coffre_windows, "ecrire", side_effect=lambda c, u, s: self.valeurs.__setitem__(c, s) or True),
            mock.patch.object(coffre_windows, "supprimer", side_effect=lambda c: self.valeurs.pop(c, None)),
        ]
        for p in self.patchs:
            p.start()
        github._cache["profil"] = None
        return self

    def __exit__(self, *exc):
        for p in self.patchs:
            p.stop()
        github._cache["profil"] = None


class TestAdresses(unittest.TestCase):
    def test_adresses_github_reconnues(self):
        self.assertEqual(github.depot_github("https://github.com/Moi/Projet.git"), "moi/projet")
        self.assertEqual(github.depot_github("git@github.com:moi/projet"), "moi/projet")
        self.assertEqual(github.depot_github("https://github.com/moi/mes-outils/"), "moi/mes-outils")
        self.assertIsNone(github.depot_github("https://gitlab.com/moi/projet.git"), "GitLab n'est pas GitHub")
        self.assertIsNone(github.depot_github(None))

    def test_nom_suggere(self):
        self.assertEqual(github.nom_suggere(r"C:\x\Mes outils"), "mes-outils")
        self.assertEqual(github.nom_suggere(r"C:\x\Projet été 2026\\"), "projet-t-2026")


class TestDepotsLocaux(unittest.TestCase):
    def setUp(self):
        self.racine = tempfile.mkdtemp()
        for nom, url in (("caisse", "https://github.com/moi/caisse.git"), ("autre", "https://gitlab.com/x/y.git")):
            chemin = os.path.join(self.racine, nom)
            os.makedirs(chemin)
            git("init", "-q", cwd=chemin)
            git("remote", "add", "origin", url, cwd=chemin)
        os.makedirs(os.path.join(self.racine, "pas-git"))

    def tearDown(self):
        shutil.rmtree(self.racine, ignore_errors=True)

    def test_retrouve_les_depots_github_du_dossier(self):
        trouves = github.depots_locaux([self.racine, r"Z:\n-existe-pas"])
        self.assertEqual(trouves, {"moi/caisse": os.path.join(self.racine, "caisse")},
                         "seul le dépôt GitHub doit être trouvé, le dossier absent ignoré")


class TestConnexion(unittest.TestCase):
    def setUp(self):
        github._attente.update(code=None)

    def test_sans_client_id(self):
        with self.assertRaises(github.ErreurGitHub):
            github.connexion_debut("")

    def test_parcours_complet(self):
        reponses = {
            github.URL_CODE: (200, {"device_code": "dc", "user_code": "ABCD-1234", "interval": 5,
                                    "verification_uri": "https://github.com/login/device", "expires_in": 900}),
        }
        jetons = iter([(200, {"error": "authorization_pending"}), (200, {"error": "slow_down", "interval": 10}),
                       (200, {"access_token": "gho_test", "token_type": "bearer"})])

        def faux_requete(methode, url, jeton=None, donnees=None, formulaire=None, delai=20):
            if url == github.URL_JETON:
                self.assertEqual(formulaire["device_code"], "dc")
                return next(jetons)
            if url == github.API + "/user":
                self.assertEqual(jeton, "gho_test")
                return 200, PROFIL_API
            return reponses[url]

        with FauxCoffre() as coffre, mock.patch.object(github, "_requete", side_effect=faux_requete), \
                mock.patch.object(github.webbrowser, "open") as ouvrir, mock.patch.object(github.time, "time") as horloge:
            horloge.return_value = 1000.0
            r = github.connexion_debut("client123")
            self.assertEqual(r["code"], "ABCD-1234")
            ouvrir.assert_called_once_with("https://github.com/login/device")
            self.assertEqual(github.connexion_suite()["etat"], "attente", "trop tôt : GitHub ne doit pas être appelé")
            horloge.return_value = 1006.0
            self.assertEqual(github.connexion_suite()["etat"], "attente")  # authorization_pending
            horloge.return_value = 1012.0
            self.assertEqual(github.connexion_suite()["etat"], "attente")  # slow_down → intervalle 10 s
            horloge.return_value = 1015.0
            self.assertEqual(github.connexion_suite()["etat"], "attente", "slow_down doit espacer les appels")
            horloge.return_value = 1023.0
            r = github.connexion_suite()
            self.assertEqual(r["etat"], "connecte")
            self.assertEqual(r["login"], "testeur")
            self.assertEqual(coffre.valeurs[github.CIBLE_COFFRE], "gho_test", "le jeton doit aller dans le coffre")
            self.assertEqual(github.connexion_suite()["etat"], "aucune")

    def test_code_expire_et_refus(self):
        with FauxCoffre(), mock.patch.object(github, "_requete", return_value=(200, {"error": "access_denied"})), \
                mock.patch.object(github.time, "time", return_value=5000.0):
            github._attente.update(code="dc", client_id="c", intervalle=5, prochain=0, expire=9999)
            self.assertEqual(github.connexion_suite()["etat"], "refuse")
            github._attente.update(code="dc", client_id="c", intervalle=5, prochain=0, expire=10)
            self.assertEqual(github.connexion_suite()["etat"], "expire")

    def test_device_flow_desactive(self):
        with mock.patch.object(github, "_requete", return_value=(400, {"error": "device_flow_disabled"})):
            with self.assertRaisesRegex(github.ErreurGitHub, "Device Flow"):
                github.connexion_debut("client123")

    def test_jeton_retire_chez_github(self):
        with FauxCoffre("gho_vieux") as coffre, mock.patch.object(github, "_requete", return_value=(401, {"message": "Bad credentials"})):
            with self.assertRaisesRegex(github.ErreurGitHub, "reconnectez"):
                github.etat()
            self.assertNotIn(github.CIBLE_COFFRE, coffre.valeurs, "un jeton refusé doit être retiré du coffre")


class TestListe(unittest.TestCase):
    def test_pagination_et_depots_locaux(self):
        page1 = [{"name": f"d{i}", "full_name": f"testeur/d{i}", "html_url": f"https://github.com/testeur/d{i}",
                  "private": i % 2 == 0, "pushed_at": f"2026-01-{(i % 28) + 1:02d}T00:00:00Z"} for i in range(100)]
        page2 = [{"name": "Caisse", "full_name": "testeur/Caisse", "html_url": "https://github.com/testeur/Caisse",
                  "private": True, "pushed_at": "2026-11-01T00:00:00Z", "language": "TypeScript"}]
        appels = []

        def faux_appel(methode, chemin, donnees=None):
            appels.append(chemin)
            return page1 if "page=1&" in chemin else page2

        with mock.patch.object(github, "_appel", side_effect=faux_appel), \
                mock.patch.object(github, "depots_locaux", return_value={"testeur/caisse": r"F:\Projets\caisse"}):
            r = github.lister_depots([r"F:\Projets"])
        self.assertEqual(len(appels), 2, "deux pages : 100 dépôts puis 1")
        self.assertEqual(len(r["depots"]), 101)
        self.assertEqual(r["depots"][0]["nom"], "Caisse", "le plus récent en premier")
        self.assertEqual(r["depots"][0]["local"], r"F:\Projets\caisse", "repéré sur ce PC malgré les majuscules")
        self.assertIsNone(r["depots"][1]["local"])


class TestEnvoi(unittest.TestCase):
    """Création d'un dépôt à partir d'un dossier : le « GitHub » est ici un
    dépôt nu local, pour vérifier les vraies commandes git."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.projet = os.path.join(self.tmp, "Mon Projet")
        os.makedirs(os.path.join(self.projet, "src"))
        os.makedirs(os.path.join(self.projet, "node_modules"))
        for chemin, contenu in (("src/app.py", "print('ok')\n"), (".gitignore", "secret.txt\nnode_modules/\n"),
                                ("secret.txt", "ne pas envoyer"), (".env", "CLE=123"), (".env.example", "CLE="),
                                ("node_modules/x.js", "x")):
            with open(os.path.join(self.projet, chemin.replace("/", os.sep)), "w", encoding="utf-8") as f:
                f.write(contenu)
        self.distant = os.path.join(self.tmp, "distant.git")
        git("init", "-q", "--bare", self.distant, cwd=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_apercu_ne_modifie_rien_et_signale_les_risques(self):
        a = github.apercu(self.projet)
        self.assertFalse(os.path.exists(os.path.join(self.projet, ".git")), "l'aperçu ne doit rien créer")
        self.assertEqual(a["nombre"], 4, ".gitignore, .env, .env.example et src/app.py")
        self.assertEqual(a["sensibles"], [".env"], ".env signalé, .env.example non")
        self.assertEqual(a["nom_suggere"], "mon-projet")
        self.assertFalse(a["existant"])

    def test_fichier_trop_gros_refuse(self):
        with mock.patch.object(github, "TAILLE_MAX", 5):
            a = github.apercu(self.projet)
            self.assertIn("src/app.py", a["trop_gros"])
            with FauxCoffre("gho_test"), self.assertRaisesRegex(github.ErreurGitHub, "100 Mo"):
                github.creer_et_envoyer(self.projet, "mon-projet")

    def test_creer_et_envoyer(self):
        os.remove(os.path.join(self.projet, ".env"))
        cree = {}

        def faux_requete(methode, url, jeton=None, donnees=None, formulaire=None, delai=20):
            if url == github.API + "/user":
                return 200, PROFIL_API
            if url == github.API + "/user/repos" and methode == "POST":
                cree.update(donnees)
                return 201, {"html_url": "https://github.com/testeur/mon-projet", "full_name": "testeur/mon-projet",
                             "clone_url": self.distant}
            raise AssertionError(url)

        # Sans identité git : l'adresse « noreply » de GitHub doit être utilisée.
        env = {k: v for k, v in os.environ.items()}
        env.update(GIT_CONFIG_GLOBAL=os.path.join(self.tmp, "vide.gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        with FauxCoffre("gho_test"), mock.patch.object(github, "_requete", side_effect=faux_requete), \
                mock.patch.dict(os.environ, env, clear=True):
            r = github.creer_et_envoyer(self.projet, "mon-projet", "Un test", prive=True)
        self.assertEqual(cree, {"name": "mon-projet", "description": "Un test", "private": True, "auto_init": False})
        self.assertEqual(r["nombre"], 3)
        envoyes = sorted(git("ls-tree", "-r", "--name-only", "main", cwd=self.distant).split())
        self.assertEqual(envoyes, [".env.example", ".gitignore", "src/app.py"], "secret.txt et node_modules exclus")
        auteur = git("log", "-1", "--format=%an <%ae>", "main", cwd=self.distant).strip()
        self.assertEqual(auteur, "testeur <42+testeur@users.noreply.github.com>")
        self.assertEqual(git("remote", "get-url", "origin", cwd=self.projet).strip(), self.distant)
        with open(os.path.join(self.projet, ".git", "config"), encoding="utf-8") as f:
            config = f.read()
        self.assertNotIn("gho_test", config, "le jeton ne doit jamais être écrit dans .git/config")
        # Un second envoi du même dossier est refusé (déjà relié).
        with FauxCoffre("gho_test"), self.assertRaisesRegex(github.ErreurGitHub, "déjà relié"):
            github.creer_et_envoyer(self.projet, "mon-projet")

    def test_nom_invalide(self):
        with self.assertRaisesRegex(github.ErreurGitHub, "invalide"):
            github.creer_et_envoyer(self.projet, "mon projet/../x")

    def test_jeton_passe_par_l_environnement(self):
        with FauxCoffre("gho_test"):
            github._cache["profil"] = {"login": "testeur", "id": 42}
            env = github._env_git(True)
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.https://github.com/.extraheader")
        self.assertTrue(env["GIT_CONFIG_VALUE_0"].startswith("AUTHORIZATION: basic "))
        self.assertEqual(env["GIT_CONFIG_VALUE_1"], "", "le gestionnaire d'identifiants doit être écarté")


class TestCoffreWindows(unittest.TestCase):
    def test_aller_retour(self):
        cible = f"MesOutils:test:{uuid.uuid4()}"
        try:
            self.assertTrue(coffre_windows.ecrire(cible, "testeur", "secret-é-123"))
            self.assertEqual(coffre_windows.lire(cible), "secret-é-123")
        finally:
            coffre_windows.supprimer(cible)
        self.assertIsNone(coffre_windows.lire(cible))


class TestRoutes(unittest.TestCase):
    """Les routes /api/github/* du serveur local."""

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

    def post(self, chemin, donnees, entete=True):
        c = http.client.HTTPConnection("127.0.0.1", self.serveur.server_address[1], timeout=10)
        entetes = {"Host": f"127.0.0.1:{self.hub.PORT}", "Content-Type": "application/json"}
        if entete:
            entetes["X-Mes-Outils"] = "1"
        c.request("POST", chemin, body=json.dumps(donnees), headers=entetes)
        try:
            r = c.getresponse()
            return r.status, json.loads(r.read() or b"{}")
        finally:
            c.close()

    def test_etat_deconnecte(self):
        with FauxCoffre(), mock.patch.object(self.hub, "lire_outils", return_value={"github": {"dossiers": ["X"]}}):
            statut, r = self.post("/api/github/etat", {})
        self.assertEqual((statut, r), (200, {"connecte": False, "dossiers": ["X"]}))

    def test_ordre_sans_entete_refuse(self):
        statut, _ = self.post("/api/github/deconnexion", {}, entete=False)
        self.assertEqual(statut, 403, "une page d'un autre site ne doit pas pouvoir donner d'ordre")

    def test_erreur_github_renvoyee_en_400(self):
        with mock.patch.object(self.hub, "lire_outils", return_value={"github": {}}), \
                mock.patch.object(github, "CLIENT_ID", ""):
            statut, r = self.post("/api/github/connexion/debut", {})
        self.assertEqual(statut, 400)
        self.assertIn("client_id", r["erreur"])

    def test_dossier_inexistant_refuse(self):
        with mock.patch.object(self.hub, "lire_outils", return_value={"github": {}}), \
                mock.patch.object(self.hub, "ecrire_outils") as ecrire:
            statut, r = self.post("/api/github/dossiers", {"dossiers": [r"Z:\n-existe-pas"]})
        self.assertEqual(statut, 400)
        ecrire.assert_not_called()


if __name__ == "__main__":
    unittest.main()
