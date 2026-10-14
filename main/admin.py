"""Administration Django des modèles vitrine de Minivers."""

from django.contrib import admin

from .models import Horaire, NewsItem, Page, Tarif


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("titre", "slug", "publiee")
    list_filter = ("publiee",)
    search_fields = ("titre", "slug", "contenu")
    prepopulated_fields = {"slug": ("titre",)}


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("titre", "date")
    list_filter = ("date",)
    search_fields = ("titre", "contenu")
    date_hierarchy = "date"


@admin.register(Horaire)
class HoraireAdmin(admin.ModelAdmin):
    list_display = ("jour", "ouverture", "fermeture", "fermeture_exceptionnelle")
    list_editable = ("ouverture", "fermeture", "fermeture_exceptionnelle")


@admin.register(Tarif)
class TarifAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "ordre")
    list_editable = ("prix", "ordre")
    search_fields = ("nom", "description")
