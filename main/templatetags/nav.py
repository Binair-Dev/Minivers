"""Tag de navigation : rend la nav commune depuis un seul endroit.

Inclus dans les templates via::

    {% load nav %}
    {% nav %}

Contrairement à un context processor, ce tag ne demande aucune modification
de ``settings.py`` : les items vivent dans ``NAV_ITEMS`` ci-dessous, et les
liens utilisent les routes existantes de ``main.urls``.
"""

from django import template

register = template.Library()

# Éléments de la nav principale, dans l'ordre d'affichage.
# ``anchor`` : ancre locale (page d'accueil uniquement) ; ``url_name`` :
# route nommée de l'app ``main`` ; les deux renseignés => lien interne vers
# la page d'accueil + ancre (ex. tarifs depuis une autre page).
NAV_ITEMS = [
    {"label": "Comment ça marche", "anchor": "comment"},
    {"label": "Parc", "anchor": "activites"},
    {"label": "Tarifs", "anchor": "tarifs"},
    {"label": "Anniversaires", "anchor": "anniversaires"},
    {"label": "Agenda", "anchor": "evenements"},
    # TODO(boutique): la boutique sortira en projet séparé — remplacer ce
    # placeholder par l'URL du site boutique quand il existera.
    {"label": "Boutique", "url_name": "main:boutique"},
    {"label": "Infos pratiques", "url_name": "main:infos_pratiques"},
    {"label": "Contact", "anchor": "contact"},
]


@register.inclusion_tag("main/_nav.html", takes_context=True)
def nav(context, active=None):
    """Rend la nav principale.

    ``active`` : label optionnel de l'item à marquer comme page courante
    (les ancres locales ne gardent leur sens que sur la page d'accueil).
    """
    request = context.get("request")
    items = []
    for item in NAV_ITEMS:
        if item.get("url_name"):
            href = f"#{item['anchor']}" if item.get("anchor") else "#"
            if request is not None:
                href = _reverse_or_anchor(item["url_name"], item.get("anchor"))
        else:
            href = f"#{item['anchor']}"
        items.append({"label": item["label"], "href": href, "active": item["label"] == active})
    return {"items": items}


def _reverse_or_anchor(url_name, anchor):
    """URL de la route si elle existe, sinon ancre locale (dégradation douce)."""
    from django.urls import reverse, NoReverseMatch

    try:
        url = reverse(url_name)
    except NoReverseMatch:
        return f"#{anchor}" if anchor else "#"
    return f"{url}#{anchor}" if anchor else url
