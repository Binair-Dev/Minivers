"""Modèles minimaux du site Minivers.

Volontairement restreint au contenu vitrine : pages éditoriales,
actualités, horaires d'ouverture et tarifs. Aucun modèle e-commerce
ni utilisateur custom (voir consignes projet).
"""

from django.core.validators import MinValueValidator
from django.db import models


class Page(models.Model):
    """Page éditoriale statique identifiée par son slug (ex. « a-propos »)."""

    slug = models.SlugField("slug", max_length=100, unique=True)
    titre = models.CharField("titre", max_length=200)
    contenu = models.TextField("contenu")
    publiee = models.BooleanField("publiée", default=False)

    class Meta:
        verbose_name = "page"
        verbose_name_plural = "pages"
        ordering = ["titre"]

    def __str__(self) -> str:
        return self.titre


class NewsItem(models.Model):
    """Actualité affichée sur le site."""

    titre = models.CharField("titre", max_length=200)
    date = models.DateField("date")
    contenu = models.TextField("contenu")
    image = models.ImageField(
        "image",
        upload_to="news/%Y/%m/",
        blank=True,
        null=True,
        help_text="Image optionnelle illustrant l'actualité.",
    )

    class Meta:
        verbose_name = "actualité"
        verbose_name_plural = "actualités"
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.titre} ({self.date:%d/%m/%Y})"


class Horaire(models.Model):
    """Horaires d'ouverture pour un jour de la semaine.

    Les champs ``ouverture``/``fermeture`` peuvent rester vides pour un jour
    fermé habituellement. ``fermeture_exceptionnelle`` signale une fermeture
    annuelle (congé annuel, travaux…) qui prime sur les horaires ordinaires.
    """

    Jour = models.TextChoices("Jour", "Lundi Mardi Mercredi Jeudi Vendredi Samedi Dimanche")

    jour = models.CharField("jour", max_length=20, choices=Jour.choices, unique=True)
    ouverture = models.TimeField("ouverture", null=True, blank=True)
    fermeture = models.TimeField("fermeture", null=True, blank=True)
    fermeture_exceptionnelle = models.BooleanField(
        "fermeture exceptionnelle",
        default=False,
        help_text="Fermeture annuelle ou temporaire : le lieu est fermé ce jour.",
    )

    class Meta:
        verbose_name = "horaire"
        verbose_name_plural = "horaires"
        ordering = ["jour"]

    def __str__(self) -> str:
        return self.get_jour_display()


class Tarif(models.Model):
    """Tarif d'entrée affiché sur le site."""

    nom = models.CharField("nom", max_length=100)
    description = models.TextField("description", blank=True)
    prix = models.DecimalField(
        "prix",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    ordre = models.PositiveIntegerField(
        "ordre d'affichage",
        default=0,
        help_text="Les tarifs sont triés par ordre croissant.",
    )

    class Meta:
        verbose_name = "tarif"
        verbose_name_plural = "tarifs"
        ordering = ["ordre", "nom"]

    def __str__(self) -> str:
        return f"{self.nom} — {self.prix} €"
