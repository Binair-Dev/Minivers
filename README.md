# Minivers — parc indoor enfants & boutique de jeux

Site vitrine éditorial du **Minivers**, parc de loisirs indoor pour les
enfants de 0 à 12 ans : accueil, univers du parc, tarifs, anniversaires,
agenda des événements, infos pratiques (horaires, tarifs d'entrée) et un
aperçu de la boutique de jeux.

La **boutique en ligne elle-même est hors périmètre** : la page
`/boutique/` est un placeholder qui deviendra un lien sortant vers un
projet séparé. Le site n'a **pas de comptes utilisateurs** — la seule
interface d'administration est l'admin Django, réservé à l'équipe.

## Stack

| Couche | Choix |
|---|---|
| Backend | Django 4.2 (Python 3.12 en production) |
| Base de données | PostgreSQL 16 en prod (Docker) / SQLite en dev local |
| Serveur d'appli | gunicorn (prod) / runserver (dev) |
| Fichiers statiques | WhiteNoise (noms hashés + compression, `Cache-Control: immutable`) |
| Déploiement | Docker Compose : services `web` (gunicorn) + `db` (Postgres, volume nommé) |
| Édition de contenu | Admin Django : pages éditoriales, actualités, horaires, tarifs |

## Structure du dépôt

```
minivers/                 # package Django : settings 12-factor, urls, wsgi/asgi
main/                     # app principale
  models.py               #   Page, NewsItem (actualités), Horaire, Tarif
  admin.py                #   admin Django de ces 4 modèles
  views.py, urls.py       #   /  /boutique/  /infos-pratiques/
  templatetags/nav.py     #   nav principale partagée (tag {% nav %})
  fixtures/demo.json      #   jeu de données de démonstration
  migrations/             #   migrations
templates/                # base.html (layout partagé) + templates main/
static/                   # css/ js/ img/ (assets du site)
scripts/visual_diff.py    # diff visuel mocks HTML ↔ rendu Django (dev)
tests/                    # tests smoke + captures de référence du diff visuel
docker-compose.yml        # stack de production : web (gunicorn) + db (Postgres)
Dockerfile                # image multi-stage (venv builder + runtime slim)
entrypoint.sh             # boot conteneur : attente DB, migrations, collectstatic
.env.example              # modèle de configuration (à copier en .env)
justfile                  # commandes locales : just test / visual-check / check
index.html, boutique.html # mocks HTML statiques d'origine (référence du diff visuel)
sketches/                 # esquisses de design et variants des mocks
```

## Pages publiques

| URL | Contenu |
|---|---|
| `/` | Accueil : hero, univers du parc, tarifs, événements (depuis les actualités), contact |
| `/boutique/` | Aperçu catalogue (placeholder — boutique en projet séparé) |
| `/infos-pratiques/` | Horaires d'ouverture et tarifs d'entrée, éditables via l'admin |
| `/actualites/` et `/actualites/<pk>-<slug>/` | Liste paginée + détail des actualités |
| `/admin/` | Admin Django (contenu éditorial) |

Les pages se remplissent depuis l'admin : si la base est vide, elles
restent propres (message « aucun contenu » ou repli sur le contenu du
mock d'origine pour la section Événements de l'accueil).

## Démarrage

Voir **[SETUP.md](SETUP.md)** — il contient tout ce qu'il faut pour
cloner, lancer en développement local (SQLite) et déployer en
production (Docker Compose), y compris les commandes de test.

## Périmètre v1 (rappels projet)

- Site éditorial vitrine : pages, actualités, horaires, tarifs via admin.
- Boutique : **lien sortant vers un projet séparé**, pas de panier ici.
- Aucun compte utilisateur public, pas d'e-commerce.
- Diff visuel mock ↔ Django (`just visual-check`) pour garantir zéro
  régression de rendu.
