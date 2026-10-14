from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("infos-pratiques/", views.infos_pratiques, name="infos_pratiques"),
]
