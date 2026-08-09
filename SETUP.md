# Minivers — site de base

Page d'accueil du site reconstruit à partir du mock `index.html`.
La partie boutique sera un projet Django séparé (autre site).

## Lancer avec Docker (recommandé)

```bash
# 1. Copier la config d'exemple et ajuster si besoin
cp .env.example .env

# 2. Build + démarrage
docker compose build
docker compose up
```

L'app sera disponible sur http://localhost:8000 (ou le port choisi via `APP_PORT`).

Commandes utiles :

```bash
docker compose logs -f web       # suivre les logs Django
docker compose exec web bash     # shell dans le conteneur web
docker compose exec web python manage.py createsuperuser
docker compose down              # arrêter (conserve la DB)
docker compose down -v           # arrêter + supprimer le volume de la DB
```

## Lancer sans Docker (développement rapide en SQLite)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Le fallback SQLite s'active automatiquement quand aucune variable `DB_*` n'est définie
(dans ce projet, tant que vous n'avez pas créé de `.env`).

## Structure

```
minivers/                 # package du projet Django (settings, urls, wsgi)
main/                     # app "main" — page d'accueil du site de base
templates/
  base.html               # layout partagé
  main/home.html          # page d'accueil
static/                   # assets statiques (CSS, JS, images)
docker-compose.yml        # stack web + PostgreSQL
Dockerfile                # image de l'app Django
entrypoint.sh             # entrypoint du conteneur (attente DB + migrations)
.env.example              # config par défaut (à copier en .env)
```

## Variables d'environnement

Voir [`.env.example`](.env.example) pour la liste complète. Les principales :

| Variable | Rôle | Défaut |
|---|---|---|
| `APP_PORT` | Port hôte sur lequel l'app est exposée | `8000` |
| `DB_PORT` | Port hôte pour Postgres | `5432` |
| `DB_ENGINE` | `postgres` ou `sqlite` | `postgres` dans Docker, `sqlite` sinon |
| `DB_HOST` | Hôte de la DB (service compose ou IP) | `db` |
| `DJANGO_DEBUG` | Active le mode debug | `true` |
| `DJANGO_ALLOWED_HOSTS` | Hostnames autorisés (CSV) | `*` |
| `DJANGO_SECRET_KEY` | Clé secrète Django | à remplacer en prod |

## Production

```bash
DJANGO_DEBUG=false DJANGO_SECRET_KEY=<long-random> docker compose up --build
```

Le `entrypoint.sh` détecte `DJANGO_DEBUG=false` et lance `collectstatic` automatiquement
avant de démarrer le serveur.
