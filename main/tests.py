"""Tests des critères de fin de la tâche t6 (models minimaux + admin).

Vérifie : migrations appliquées, fixture de démo chargeable, les 4 modèles
enregistrés dans l'admin, et objets créables/modifiables via l'admin.
"""

import json
from pathlib import Path

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import TestCase

from main.admin import HoraireAdmin, NewsItemAdmin, PageAdmin, TarifAdmin
from main.models import Horaire, NewsItem, Page, Tarif

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "demo.json"


class RegistrationTests(TestCase):
    def test_all_models_registered_in_admin(self):
        for model in (Page, NewsItem, Horaire, Tarif):
            self.assertIn(model, admin.site._registry)
            self.assertIsInstance(admin.site._registry[model], (PageAdmin, NewsItemAdmin, HoraireAdmin, TarifAdmin))

    def test_fixture_file_exists_and_is_valid_json(self):
        self.assertTrue(FIXTURE.exists(), f"fixture manquante : {FIXTURE}")
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        models = {entry["model"] for entry in data}
        self.assertLessEqual({"main.page", "main.newsitem", "main.horaire", "main.tarif"}, models)


class ModelBehaviourTests(TestCase):
    def test_fixture_loads(self):
        from django.core.management import call_command
        call_command("loaddata", "demo", verbosity=0)
        self.assertEqual(Page.objects.count(), 2)
        self.assertEqual(NewsItem.objects.count(), 2)
        self.assertEqual(Horaire.objects.count(), 7)
        self.assertEqual(Tarif.objects.count(), 3)

    def test_page_str_and_slug_unique(self):
        page = Page.objects.create(slug="test", titre="Test", contenu="x", publiee=True)
        self.assertEqual(str(page), "Test")
        doublon = Page(slug="test", titre="Doublon", contenu="x")
        with self.assertRaises(ValidationError):
            doublon.full_clean()

    def test_horaire_jour_unique_and_choices(self):
        Horaire.objects.create(jour="Lundi", ouverture="10:00", fermeture="18:00")
        doublon = Horaire(jour="Lundi")
        with self.assertRaises(ValidationError):
            doublon.full_clean()
        h = Horaire.objects.get(jour="Lundi")
        self.assertEqual(str(h), "Lundi")

    def test_tarif_ordre_and_negative_price_rejected(self):
        Tarif.objects.create(nom="A", prix="5.00", ordre=2)
        Tarif.objects.create(nom="B", prix="3.00", ordre=1)
        self.assertEqual(list(Tarif.objects.all()), list(Tarif.objects.order_by("ordre", "nom")))
        tarif = Tarif(nom="C", prix="-1.00")
        with self.assertRaises(Exception):
            tarif.full_clean()

    def test_newsitem_image_optional(self):
        item = NewsItem.objects.create(titre="Test", date="2026-01-01", contenu="x")
        self.assertFalse(item.image)


class AdminAccessTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "x")
        self.client.force_login(self.admin)

    def test_changelists_render(self):
        Page.objects.create(slug="p1", titre="P1", contenu="x")
        Horaire.objects.create(jour="Lundi")
        Tarif.objects.create(nom="T", prix="5.00")
        for url in (
            "/admin/main/page/",
            "/admin/main/newsitem/",
            "/admin/main/horaire/",
            "/admin/main/tarif/",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_add_and_edit_via_admin(self):
        # Création d'une Page via le formulaire d'admin
        response = self.client.post(
            "/admin/main/page/add/",
            {"slug": "contact", "titre": "Contact", "contenu": "Écrivez-nous.", "publiee": "on"},
        )
        self.assertRedirects(response, "/admin/main/page/")
        page = Page.objects.get(slug="contact")
        self.assertTrue(page.publiee)

        # Modification via le formulaire d'admin
        response = self.client.post(
            f"/admin/main/page/{page.pk}/change/",
            {"slug": "contact", "titre": "Contact (maj)", "contenu": "Écrivez-nous.", "publiee": "on"},
        )
        self.assertRedirects(response, "/admin/main/page/")
        page.refresh_from_db()
        self.assertEqual(page.titre, "Contact (maj)")

        # Création d'un Tarif via l'admin
        response = self.client.post(
            "/admin/main/tarif/add/",
            {"nom": "Groupe", "description": "", "prix": "7.50", "ordre": "1"},
        )
        self.assertRedirects(response, "/admin/main/tarif/")
        self.assertTrue(Tarif.objects.filter(nom="Groupe", prix="7.50").exists())
