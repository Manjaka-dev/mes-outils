# -*- coding: utf-8 -*-
"""Tests de l'onglet Temps : chrono, une seule session à la fois, Pomodoro
avec une horloge simulée, sessions manuelles, totaux, export CSV, routes."""
import csv
import datetime
import io
import unittest
from unittest import mock

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # aide.py, quel que soit le lancement

from aide import ConfigTemporaire, ServeurTest

import temps  # noqa: E402


class Horloge:
    """Horloge simulée : avancer(minutes=…, secondes=…)."""

    def __init__(self, depart="2026-03-02T09:00:20"):
        self.t = datetime.datetime.strptime(depart, temps.FORMAT_S)

    def __call__(self):
        return self.t

    def avancer(self, minutes=0, secondes=0):
        self.t += datetime.timedelta(minutes=minutes, seconds=secondes)


class BaseTemps(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigTemporaire({"outils": []})
        self.cfg.__enter__()
        self.horloge = Horloge()
        self.patch = mock.patch.object(temps, "maintenant", self.horloge)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.cfg.__exit__(None, None, None)


class TestChrono(BaseTemps):
    def test_demarrer_arreter(self):
        self.assertEqual(temps.etat(), {"en_cours": False})
        e = temps.demarrer("  Site   vitrine ", "maquette")
        self.assertEqual((e["projet"], e["note"], e["depuis"]), ("Site vitrine", "maquette", "2026-03-02T09:00:20"))
        self.horloge.avancer(minutes=26, secondes=50)          # 09:27:10
        self.assertEqual(temps.etat()["secondes"], 26 * 60 + 50)
        s = temps.arreter()
        self.assertEqual((s["debut"], s["fin"], s["minutes"]), ("2026-03-02T09:00", "2026-03-02T09:27", 27),
                         "durée = heures affichées, à la minute")
        self.assertEqual(temps.etat(), {"en_cours": False})
        self.assertEqual(len(temps.sessions("tout")), 1)

    def test_une_seule_session_a_la_fois(self):
        temps.demarrer("A")
        with self.assertRaisesRegex(ValueError, "tourne déjà sur « A »"):
            temps.demarrer("B")
        with self.assertRaises(ValueError):
            temps.demarrer("")
        temps.arreter()
        with self.assertRaisesRegex(ValueError, "Aucun chrono"):
            temps.arreter()

    def test_moins_d_une_minute_ignoree(self):
        temps.demarrer("A")
        self.horloge.avancer(secondes=30)
        self.assertIsNone(temps.arreter())
        self.assertEqual(temps.sessions("tout"), [])

    def test_survit_au_redemarrage(self):
        temps.demarrer("A", "note")
        # Une autre lecture du fichier (page fermée, Mes outils relancé) retrouve le chrono.
        self.assertTrue(temps._lire()["en_cours"])
        self.horloge.avancer(minutes=5)
        temps.modifier_en_cours(projet="B", note="autre")
        self.assertEqual(temps.arreter(note="fin")["projet"], "B")


class TestPomodoro(BaseTemps):
    def test_alertes(self):
        temps.enregistrer_reglages({"travail": 25, "pause_courte": 5, "pause_longue": 15, "cycles": 2})
        e = temps.demarrer("Projet X", pomodoro=True)
        self.assertEqual((e["pomodoro"]["phase"], e["pomodoro"]["fin_prevue"]), ("travail", "2026-03-02T09:25:20"))
        self.horloge.avancer(minutes=24)
        self.assertEqual(temps.alertes_dues(), [], "rien avant la fin de la période")
        self.horloge.avancer(minutes=1)
        dues = temps.alertes_dues()
        self.assertEqual(len(dues), 1)
        self.assertEqual(dues[0]["titre"], "Pause ! ☕")
        self.assertIn("Projet X", dues[0]["detail"])
        self.assertEqual(temps.etat()["pomodoro"]["phase"], "pause_courte")
        self.assertEqual(temps.alertes_dues(), dues, "toujours due tant qu'elle n'est pas vue")
        self.assertTrue(temps.marquer_alerte(dues[0]["id"]))
        self.assertEqual(temps.alertes_dues(), [], "marquée : plus due")
        self.horloge.avancer(minutes=5)
        dues = temps.alertes_dues()
        self.assertEqual(dues[0]["titre"], "Au travail ! 💪")
        temps.marquer_alerte(dues[0]["id"])
        self.horloge.avancer(minutes=25)
        self.assertEqual(temps.alertes_dues()[0]["titre"], "Grande pause ! 🌿", "pause longue après 2 périodes")
        self.assertEqual(temps.etat()["pomodoro"]["phase"], "pause_longue")

    def test_veille_une_seule_alerte_puis_perimee(self):
        temps.demarrer("A", pomodoro=True)
        self.horloge.avancer(minutes=200)                       # PC en veille
        dues = temps.alertes_dues()
        self.assertEqual(len(dues), 1, "une seule alerte pour plusieurs périodes écoulées")
        temps.modifier_en_cours(pomodoro=False)
        self.horloge.avancer(minutes=61)
        self.assertEqual(temps.alertes_dues(), [], "une alerte de plus d'une heure n'est plus montrée")

    def test_reglages_refuses(self):
        with self.assertRaises(ValueError):
            temps.enregistrer_reglages({"travail": 0})
        with self.assertRaises(ValueError):
            temps.enregistrer_reglages({"cycles": "abc"})
        self.assertEqual(temps.reglages_pomodoro()["travail"], 25)


class TestSessions(BaseTemps):
    def test_manuelles_totaux_periodes(self):
        a = temps.ajouter_session({"projet": "A", "debut": "2026-03-02T08:00", "fin": "2026-03-02T09:30"})
        temps.ajouter_session({"projet": "B", "debut": "2026-03-04T14:00", "fin": "2026-03-04T14:45"})
        temps.ajouter_session({"projet": "A", "debut": "2026-03-10T10:00", "fin": "2026-03-10T10:20"})
        temps.ajouter_session({"projet": "C", "debut": "2026-02-27T10:00", "fin": "2026-02-27T11:00"})
        self.assertEqual(a["minutes"], 90)
        semaine = temps.sessions("semaine", "2026-03-04")
        self.assertEqual(len(semaine), 2, "lundi 2 au dimanche 8 mars")
        self.assertEqual(temps.totaux(temps.sessions("mois", "2026-03-15")),
                         [{"projet": "A", "minutes": 110}, {"projet": "B", "minutes": 45}])
        self.assertEqual(len(temps.sessions("jour", "2026-02-27")), 1)
        m = temps.modifier_session({**a, "fin": "2026-03-02T10:00", "note": "réunion"})
        self.assertEqual((m["minutes"], m["note"]), (120, "réunion"))
        self.assertEqual(temps.supprimer_session(a["id"]), 1)
        self.assertEqual(temps.projets_recents(), ["A", "B", "C"])

    def test_sessions_refusees(self):
        for mauvaise in ({"projet": "A", "debut": "2026-03-02T10:00", "fin": "2026-03-02T09:00"},
                         {"projet": "A", "debut": "2026-03-02T10:00", "fin": "2026-03-04T10:00"},
                         {"projet": "", "debut": "2026-03-02T10:00", "fin": "2026-03-02T11:00"},
                         {"projet": "A", "debut": "hier", "fin": "2026-03-02T11:00"}):
            with self.assertRaises(ValueError):
                temps.ajouter_session(mauvaise)
        with self.assertRaises(ValueError):
            temps.modifier_session({"id": "inconnu", "projet": "A", "debut": "2026-03-02T10:00", "fin": "2026-03-02T11:00"})

    def test_export_csv(self):
        temps.ajouter_session({"projet": "Client; Alpha", "note": "=1+1", "debut": "2026-03-02T08:00", "fin": "2026-03-02T09:30"})
        temps.ajouter_session({"projet": "B", "debut": "2026-03-03T23:30", "fin": "2026-03-04T00:15"})
        r = temps.export_csv("mois", "2026-03-20")
        self.assertEqual(r["nom"], "temps-mois-2026-03.csv")
        self.assertTrue(r["csv"].startswith("﻿"), "BOM UTF-8 pour Excel")
        lignes = list(csv.reader(io.StringIO(r["csv"][1:]), delimiter=";"))
        self.assertEqual(lignes[0], ["Date", "Début", "Fin", "Projet", "Note", "Minutes", "Heures"])
        self.assertEqual(lignes[1], ["02/03/2026", "08:00", "09:30", "Client; Alpha", "'=1+1", "90", "1,50"])
        self.assertEqual(lignes[2][2], "04/03/2026 00:15", "fin un autre jour : avec la date")
        self.assertEqual(lignes[-1], ["Total", "", "", "", "", "135", "2,25"])
        self.assertIn("\r\n", r["csv"])


class TestRoutes(ServeurTest):
    def test_routes(self):
        horloge = Horloge()
        with ConfigTemporaire(), mock.patch.object(temps, "maintenant", horloge):
            statut, r = self.post("/api/temps/demarrer", {"projet": "Site", "pomodoro": True})
            self.assertEqual((statut, r["en_cours"]), (200, True))
            statut, r = self.post("/api/temps/demarrer", {"projet": "Autre"})
            self.assertEqual(statut, 400)
            horloge.avancer(minutes=30)
            statut, r = self.post("/api/temps/alertes", {})
            self.assertEqual(len(r["alertes"]), 1)
            statut, r = self.post("/api/temps/marquer_alerte", {"id": r["alertes"][0]["id"]})
            self.assertEqual(r, {"ok": True})
            statut, r = self.post("/api/temps/arreter", {})
            self.assertEqual((statut, r["session"]["minutes"], r["etat"]), (200, 30, {"en_cours": False}))
            statut, r = self.post("/api/temps/ajouter", {"session": {"projet": "Site", "debut": "2026-03-01T10:00", "fin": "2026-03-01T11:00"}})
            self.assertEqual(statut, 200)
            statut, r = self.post("/api/temps/liste", {"periode": "semaine", "date": "2026-03-02"})
            self.assertEqual((statut, r["total"], r["totaux"], r["debut"], r["fin"]),
                             (200, 30, [{"projet": "Site", "minutes": 30}], "2026-03-02", "2026-03-08"))
            self.assertEqual(r["projets"], ["Site"])
            statut, r = self.post("/api/temps/export", {"periode": "tout"})
            self.assertEqual((statut, r["nom"]), (200, "temps-tout.csv"))
            statut, r = self.post("/api/temps/reglages", {"travail": 50})
            self.assertEqual((statut, r["travail"]), (200, 50))
            statut, r = self.post("/api/temps/liste", {"periode": "année"})
            self.assertEqual(statut, 400)


if __name__ == "__main__":
    unittest.main()
