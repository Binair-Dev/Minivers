# SETUP — Minivers

Ce guide permet à un contributeur externe de faire tourner le site en
développement local (SQLite, sans Docker) et en production (Docker
Compose + PostgreSQL + gunicorn), en suivant uniquement ce document.

> Prérequis commun : **git**. Pour le dev local : **Python 3.12** (le
> couple Django 4.2 + Python ≥ 3.13 casse les inclusion tags ; l'image
> Docker est déjà en 3.12). Pour la prod : **Docker + docker compose**.

---

## 1. Développement local (SQLite)

```bash
git clone <url-du-dépôt> minivers && cd minivers

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optionnel : jeu de données de démo (pages, actualités, horaires, tarifs)
python manage.py migrate
python manage.py loaddata demo

python manage.py runserver
```

Le site est sur http://localhost:8000 — la base est un fichier SQLite
(`db.sqlite3`, créé automatiquement, git-ignoré).

Notes :

- **Aucun `.env` n'est nécessaire en dev.** Sans fichier `.env` ni
  variable `DB_*`, Django utilise SQLite et `DEBUG=true`. Le runserver
  sert les statics sans collectstatic : passez `DJANGO_WHITENOISE=false`
  (ou ne collectez pas) pour rester dans ce mode simple — voir
  `.env.example`.
- **Attention si le dépôt est cloné sur un montage CIFS** (ex.
  `/mnt/...`) : SQLite y est verrouillé. Mettez la base ailleurs :
  ```bash
  export DB_NAME=/home/moi/minivers.db   # chemin sur disque local
  ```
- Créer un compte admin (édition du contenu sur `/admin/`) :
  ```bash
  python manage.py createsuperuser
  ```
  Sans fixture ni superuser, le site reste fonctionnel : les pages
  affichent un contenu de repli propre.

### Tests

```bash
python manage.py test
```

### Diff visuel (non-régression rendu)

Compare le rendu Django aux mocks HTML statiques (`index.html`,
`boutique.html`) sur desktop/tablette/mobile et produit un rapport dans
`tests/visual/report/index.html`. Nécessite Playwright + Pillow
(dépendances de dev, hors `requirements.txt`) :

```bash
pip install playwright pillow && playwright install chromium
```

Sur CIFS, la base doit être locale avant tout :

```bash
export MINIVERS_DB_NAME=/home/moi/minivers.db   # ou DB_NAME
just bootstrap        # migrations + fixture démo sur cette base
just visual-check     # capture + diff pixel
just check            # tests Django + diff visuel
```

---

## 2. Production (Docker Compose)

La stack : service `web` (gunicorn derrière WhiteNoise) + service `db`
(PostgreSQL 16, volume nommé `pg_data`). Au démarrage du conteneur,
`entrypoint.sh` attend la base, applique les migrations et lance
`collectstatic` automatiquement.

```bash
cp .env.example .env
```

Éditez `.env` — **deux valeurs à changer absolument en prod** :

```ini
DJANGO_SECRET_KEY=<long-aléatoire>   # python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_DEBUG=false
```

Puis :

```bash
docker compose up --build -d
docker compose logs -f web        # suivi du premier boot (migrations, collectstatic)
```

Le site répond sur http://localhost:8000 (port réglable via `APP_PORT`
dans `.env`). Vérification rapide :

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/            # 200
docker compose exec web python manage.py check --deploy                    # audit prod
```

Créer le compte admin :

```bash
docker compose exec web python manage.py createsuperuser
```

Commandes utiles :

```bash
docker compose logs -f web                                    # logs gunicorn
docker compose exec web bash                                  # shell dans le conteneur
docker compose restart web                                    # après édition de .env
docker compose down                                           # arrêt (données conservées)
docker compose down -v                                        # arrêt + suppression des volumes (⚠ données perdues)
```

Chargement du contenu de démo en prod (optionnel) :

```bash
docker compose exec web python manage.py loaddata demo
```

### Sauvegardes / persistance

- Les données vivent dans le volume `pg_data` : elles survivent à
  `down`/`up` et au remplacement du conteneur.
- Les médias uploadés (images d'actualités) vont dans le volume
  `media_data` ; les statics sont collectés au boot dans le conteneur.
- Sauvegarde : `docker compose exec db pg_dump -U minivers minivers > backup.sql`
  Restauration : `cat backup.sql | docker compose exec -T db psql -U minivers minivers`

### Notes de sécurité prod

- `DEBUG=false` active les cookies `Secure` : l'admin exige **HTTPS**
  (derrière un reverse proxy qui termine le TLS ; voir
  `SECURE_PROXY_SSL_HEADER` dans `settings.py`).
- Postgres est exposé sur l'hôte via `DB_HOST_PORT` pour psql/GUI —
  supprimez le bloc `ports` du service `db` dans `docker-compose.yml`
  si vous n'en avez pas besoin.
- Seul `.env.example` est versionné ; `.env` est git-ignoré, ne le
  commitez jamais.

---

## 3. Variables d'environnement

Liste complète commentée dans [`.env.example`](.env.example). Les principales :

| Variable | Rôle | Défaut |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django | à remplacer en prod |
| `DJANGO_DEBUG` | Mode debug | `false` (sauf en dev local sans `.env` : `true`) |
| `DJANGO_ALLOWED_HOSTS` | Hostnames servis (CSV) | `*` (mettez votre domaine en prod) |
| `DJANGO_WHITENOISE` | `false` en dev sans collectstatic | `true` |
| `APP_PORT` | Port hôte de l'app | `8000` |
| `GUNICORN_WORKERS` | Workers gunicorn (règle : 2×CPU+1) | `3` |
| `DB_ENGINE` | `postgres` ou `sqlite` | `postgres` dans Docker, `sqlite` sinon |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Identifiants Postgres | `minivers` / `minivers` / `minivers` |
| `DB_HOST` / `DB_PORT` | Cible **de l'app** (réseau compose) | `db` / `5432` |
| `DB_HOST_PORT` | Port Postgres exposé **sur l'hôte** (psql/GUI) | `5432` |

⚠ `DB_PORT` (app → db, toujours 5432 dans le réseau compose) et
`DB_HOST_PORT` (hôte → db, libre) sont deux choses différentes.

---

## 4. Résolution de problèmes

| Symptôme | Cause probable | Solution |
|---|---|---|
| `sqlite3.OperationalError: unable to open database file` ou blocage | Dépôt sur CIFS (`/mnt/...`) | `export DB_NAME=/chemin/local.db` |
| Crash `Context.__copy__` / inclusion tags en local | Python ≥ 3.13 avec Django 4.2 | utiliser Python 3.12 (ou Docker) |
| 500 sur `/` juste après `loaddata` sans `migrate` | base non migrée | `python manage.py migrate` (ou `just bootstrap`) |
| Statics 404 en mode prod local | collectstatic non passé | `python manage.py collectstatic` (automatique dans le conteneur) |
| Admin inaccessible en HTTP avec `DEBUG=false` | cookies `Secure` | passer en HTTPS derrière un reverse proxy |
| Port 8000/5432 déjà pris | autre service sur l'hôte | changer `APP_PORT` / `DB_HOST_PORT` dans `.env` |
| Diff visuel 100 % partout | base vide ou non migrée avant capture | `just bootstrap` puis `just visual-check` |
