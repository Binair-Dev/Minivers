from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("infos-pratiques/", views.infos_pratiques, name="infos_pratiques"),
    # === NEWS (t8) ===
    path("actualites/", views.news_list, name="news_list"),
    path("actualites/<int:pk>-<slug:slug>/", views.news_detail, name="news_detail"),
]
