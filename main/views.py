"""Vues du site vitrine Minivers."""

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from .models import Horaire, NewsItem, Page, Tarif

# Nombre d'actualités affichées sur la page d'accueil.
NB_ACTUALITES_HOME = 3


def home(request):
    """Accueil : dernière section alimentée par les actualités (modèles).

    Si aucune actualité n'existe (base vide), le mock statique est conservé
    afin que la page ne soit jamais vide.
    """
    dernieres_actualites = NewsItem.objects.all()[:NB_ACTUALITES_HOME]

    return render(
        request,
        "main/home.html",
        {"dernieres_actualites": dernieres_actualites},
    )


def boutique(request):
    # TODO(boutique): la boutique sortira en projet séparé (URL dédiée).
    # Ce placeholder sert de point d'ancrage pour la future redirection.
    return render(request, "main/boutique.html")


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


# === NEWS (t8) ===
NEWS_PAR_PAGE = 6


def news_list(request):
    """Liste des actualités, triées par date décroissante, 6 par page.

    Une liste vide (ou une page hors limites) affiche un message propre.
    """
    items = NewsItem.objects.order_by("-date")
    paginator = Paginator(items, NEWS_PAR_PAGE)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "main/news/news_list.html",
        {"page_obj": page, "paginator": paginator},
    )


def news_detail(request, pk, slug):
    """Détail d'une actualité par identifiant + slug dérivé du titre.

    Le slug est purement cosmétique : seule la clé primaire sert à la
    résolution, ce qui garde les liens stables si le titre est corrigé.
    """
    news = get_object_or_404(NewsItem, pk=pk)
    return render(request, "main/news/news_detail.html", {"news": news})
