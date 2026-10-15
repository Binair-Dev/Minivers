# CI locale — Minivers : tests Django + diff visuel (mocks vs rendu Django).
#
# Usage :
#   just test                          # suite Django complète
#   just visual-check                  # diff visuel en mode check
#   just check                         # test + visual-check (CI locale)
#
# SQLite ne fonctionne pas sur /mnt/hdde (CIFS verrouille SQLite) : la base
# utilisée par manage.py / visual_diff.py doit vivre sur disque local.
# Passe le chemin via la variable DB_NAME (ou MINIVERS_DB_NAME une fois pour
# toutes dans ton shell : export MINIVERS_DB_NAME=/chemin/local/minivers.db).

set export := true

python := env_var_or_default("PYTHON", "python3")
_db    := env_var_or_default("MINIVERS_DB_NAME", "")
db     := if _db == "" { env("DB_NAME", "") } else { _db }

# export DB_NAME seulement si un chemin est connu (sinon laisser l'env tel quel)
[private]
@_db-env:
    @:

default: check

# Lance la suite Django complète.
@test:
    #!/usr/bin/env bash
    if [ -n "{{ db }}" ]; then export DB_NAME="{{ db }}"; fi
    if [ -z "$DB_NAME" ] && [ ! -w . ]; then \
        echo "ATTENTION : DB_NAME non défini — SQLite sera créé dans le dossier courant." \
           ; echo "Si ce dossier est sur CIFS (/mnt/...), définis MINIVERS_DB_NAME=/chemin/local.db." ; fi
    {{ python }} manage.py test

# Diff visuel complet (capture mocks + Django, diff pixel, rapport).
@visual-check:
    #!/usr/bin/env bash
    if [ -n "{{ db }}" ]; then export DB_NAME="{{ db }}"; fi
    {{ python }} scripts/visual_diff.py

# Diff visuel puis ouvre le rapport HTML.
@visual-report:
    #!/usr/bin/env bash
    if [ -n "{{ db }}" ]; then export DB_NAME="{{ db }}"; fi
    {{ python }} scripts/visual_diff.py --open

# CI locale : tests + diff visuel.
# IMPORTANT : la DB doit avoir migrations + fixture (sinon la home Django lève
# une 500 « no such table » capturée comme diff 100 %). Bootstrap :
#   just bootstrap
check: test visual-check

# Prépare une DB locale (migrations + fixtures de démo) pour le diff visuel.
@bootstrap:
    #!/usr/bin/env bash
    if [ -n "{{ db }}" ]; then export DB_NAME="{{ db }}"; fi
    if [ -z "$DB_NAME" ]; then echo "ERREUR : définis MINIVERS_DB_NAME=/chemin/local.db (SQLite interdit sur CIFS)." >&2; exit 1; fi
    {{ python }} manage.py migrate --noinput
    {{ python }} manage.py loaddata demo

# Supprime les artefacts visuels générés.
clean:
    rm -rf tests/visual/current tests/visual/diff tests/visual/report
