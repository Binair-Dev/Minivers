from django.shortcuts import render


def home(request):
    return render(request, "main/home.html")


def boutique(request):
    # TODO(boutique): la boutique sortira en projet séparé (URL dédiée).
    # Ce placeholder sert de point d'ancrage pour la future redirection.
    return render(request, "main/boutique.html")
