"""Vues du site vitrine Minivers."""

from django.shortcuts import render

from .models import Horaire, Page, Tarif


def home(request):
    return render(request, "main/home.html")


def infos_pratiques(request):
    """Page « Infos pratiques » : horaires d'ouverture et tarifs.

    Toutes les données proviennent des modèles (éditables via l'admin) ;
    une page vide affiche un message propre au lieu de planter.
    """
    horaires = Horaire.objects.all()
    tarifs = Tarif.objects.all()
    page = Page.objects.filter(slug="infos-pratiques", publiee=True).first()

    return render(
        request,
        "main/infos_pratiques.html",
        {
            "page": page,
            "horaires": horaires,
            "tarifs": tarifs,
            "has_horaires": horaires.exists(),
            "has_tarifs": tarifs.exists(),
        },
    )
