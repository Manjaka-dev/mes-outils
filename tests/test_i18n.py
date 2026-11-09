# -*- coding: utf-8 -*-
"""Tests des dictionnaires de traduction (outil/web/*.js) : le dictionnaire
est commun à toute la page, une même phrase ne doit donc pas recevoir deux
traductions différentes, et les {variables} doivent se retrouver dans la
traduction."""
import os
import re
import shutil
import subprocess
import unittest

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outil", "web")
FICHIERS = ["i18n.js", "mails.js", "notes.js", "agenda.js", "motsdepasse.js", "ssh.js"]
BLOC = re.compile(r"I18N\.ajouter\(\{(.*?)\}\);", re.S)
PAIRE = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"')


def paires(nom):
    with open(os.path.join(WEB, nom), encoding="utf-8") as f:
        texte = f.read()
    for bloc in BLOC.findall(texte):
        # Commentaires « // … » en fin de ligne retirés.
        bloc = re.sub(r"^\s*//.*$", "", bloc, flags=re.M)
        yield from PAIRE.findall(bloc)


class TestDictionnaires(unittest.TestCase):
    def test_chaque_fichier_a_un_dictionnaire(self):
        for nom in FICHIERS:
            self.assertTrue(list(paires(nom)), f"{nom} : aucun I18N.ajouter trouvé")

    def test_pas_de_traductions_contradictoires(self):
        vues = {}
        for nom in FICHIERS:
            for cle, valeur in paires(nom):
                if cle in vues and vues[cle][1] != valeur:
                    self.fail(f"« {cle} » traduit « {vues[cle][1]} » dans {vues[cle][0]} et « {valeur} » dans {nom}")
                vues[cle] = (nom, valeur)

    def test_variables_conservees(self):
        for nom in FICHIERS:
            for cle, valeur in paires(nom):
                self.assertEqual(set(re.findall(r"\{(\w+)\}", cle)), set(re.findall(r"\{(\w+)\}", valeur)),
                                 f"{nom} : variables différentes entre « {cle} » et « {valeur} »")

    @unittest.skipUnless(shutil.which("node"), "node absent")
    def test_syntaxe_js(self):
        for nom in FICHIERS:
            r = subprocess.run(["node", "--check", os.path.join(WEB, nom)], capture_output=True, text=True,
                               timeout=30, creationflags=0x08000000)
            self.assertEqual(r.returncode, 0, f"{nom} : {r.stderr}")


if __name__ == "__main__":
    unittest.main()
