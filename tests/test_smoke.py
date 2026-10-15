"""Tests de non-régression (fumée) sur les vues du site vitrine.

Vérifie que chaque page publique répond 200 avec le contenu attendu,
que le contenu éditorial venant des fixtures est bien rendu, et que les
URLs inconnues renvoient proprement 404.
"""

from django.test import TestCase

from main.models import Horaire, NewsItem, Page, Tarif


class SmokeTestsBase(TestCase):
    """Base commune : charge la fixture de démo avant chaque test."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command

        call_command("loaddata", "demo", verbosity=0)


class HomeSmokeTests(SmokeTestsBase):
    """Page d'accueil."""

    def test_home_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_home_uses_home_template(self):
        response = self.client.get("/")
        self.assertTemplateUsed(response, "main/home.html")

    def test_home_contains_hero_and_nav(self):
        response = self.client.get("/")
        self.assertContains(response, "Bienvenue au Minivers")
        self.assertContains(response, "<nav")

    def test_home_shows_latest_news_from_models(self):
        response = self.client.get("/")
        self.assertContains(response, "Ouverture de la saison printanière")

    def test_home_falls_back_to_mock_without_news(self):
        NewsItem.objects.all().delete()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Journee Super Heros")


class BoutiqueSmokeTests(SmokeTestsBase):
    """Page boutique (placeholder en attendant le projet dédié)."""

    def test_boutique_returns_200(self):
        response = self.client.get("/boutique/")
        self.assertEqual(response.status_code, 200)

    def test_boutique_uses_boutique_template(self):
        response = self.client.get("/boutique/")
        self.assertTemplateUsed(response, "main/boutique.html")

    def test_boutique_contains_catalog(self):
        response = self.client.get("/boutique/")
        self.assertContains(response, "Notre <span>Boutique</span>")


class InfosPratiquesSmokeTests(SmokeTestsBase):
    """Page « Infos pratiques » (horaires + tarifs depuis les modèles)."""

    def test_infos_pratiques_returns_200(self):
        response = self.client.get("/infos-pratiques/")
        self.assertEqual(response.status_code, 200)

    def test_infos_pratiques_uses_template(self):
        response = self.client.get("/infos-pratiques/")
        self.assertTemplateUsed(response, "main/infos_pratiques.html")

    def test_infos_pratiques_shows_horaires_and_tarifs(self):
        response = self.client.get("/infos-pratiques/")
        self.assertContains(response, "Lundi")
        self.assertContains(response, "Enfant (3-12 ans)")

    def test_infos_pratiques_empty_is_clean(self):
        Horaire.objects.all().delete()
        Tarif.objects.all().delete()
        response = self.client.get("/infos-pratiques/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La grille tarifaire n'est pas encore disponible")

    def test_infos_pratiques_shows_editorial_page(self):
        response = self.client.get("/infos-pratiques/")
        # Contenu éditorial de la Page « infos-pratiques » (fixture).
        self.assertContains(response, "Retrouvez ici les horaires, les tarifs")


class ActualitesSmokeTests(SmokeTestsBase):
    """Liste et détail des actualités (pagination, 404, cas vide)."""

    def test_news_list_returns_200(self):
        response = self.client.get("/actualites/")
        self.assertEqual(response.status_code, 200)

    def test_news_list_uses_template(self):
        response = self.client.get("/actualites/")
        self.assertTemplateUsed(response, "main/news/news_list.html")

    def test_news_list_contains_fixture_items(self):
        response = self.client.get("/actualites/")
        self.assertContains(response, "Nuit du parc")
        self.assertContains(response, "Ouverture de la saison printanière")

    def test_news_list_empty_is_clean(self):
        NewsItem.objects.all().delete()
        response = self.client.get("/actualites/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucune actualité")

    def test_news_list_pagination(self):
        # La fixture contient 2 actualités (1 page) : on en crée 6 de plus
        # pour forcer une 2e page (6 par page).
        for i in range(6):
            NewsItem.objects.create(
                titre=f"Actualité de remplissage {i}",
                date="2026-01-01",
                contenu="x",
            )
        response = self.client.get("/actualites/?page=2")
        self.assertEqual(response.status_code, 200)

    def test_news_list_pagination_out_of_range_is_clean(self):
        response = self.client.get("/actualites/?page=99")
        self.assertEqual(response.status_code, 200)

    def test_news_detail_returns_200_with_slug(self):
        news = NewsItem.objects.get(titre="Nuit du parc")
        response = self.client.get(f"/actualites/{news.pk}-nuit-du-parc/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuit du parc")

    def test_news_detail_ignores_cosmetic_slug(self):
        news = NewsItem.objects.get(titre="Nuit du parc")
        response = self.client.get(f"/actualites/{news.pk}-autre-slug/")
        self.assertEqual(response.status_code, 200)

    def test_news_detail_unknown_pk_returns_404(self):
        response = self.client.get("/actualites/9999-slug-inconnu/")
        self.assertEqual(response.status_code, 404)


class UnknownPageTests(TestCase):
    """Toute page inconnue renvoie 404 (pas de crash 500)."""

    def test_unknown_page_returns_404(self):
        response = self.client.get("/cette-page-nexiste-pas/")
        self.assertEqual(response.status_code, 404)
