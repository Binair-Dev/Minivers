#!/usr/bin/env python3
"""Diff visuel entre les mocks HTML statiques et le rendu Django.

Capture `index.html` et `boutique.html` (servis en statique) puis les pages
Django correspondantes (via runserver ou `DJANGO_LIVE_SERVER_URL`), en
résolutions desktop / tablette / mobile, et produit un rapport HTML + PNG
de comparaison pixel dans `tests/visual/report/`.

Usage :
    python scripts/visual_diff.py                 # capture + diff complet
    python scripts/visual_diff.py --capture-only  # (re)génère les références
    python scripts/visual_diff.py --diff-only     # diff sans re-capturer Django

Les captures de référence vivent dans `tests/visual/reference/` (committées,
ignorées par collectstatic car hors de `static/`).

Dépendances : playwright (+ `playwright install chromium`), Pillow.
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import subprocess
import sys
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageChops

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

BASE_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DIR = BASE_DIR / "tests" / "visual" / "reference"
CURRENT_DIR = BASE_DIR / "tests" / "visual" / "current"
DIFF_DIR = BASE_DIR / "tests" / "visual" / "diff"
REPORT_PATH = BASE_DIR / "tests" / "visual" / "report" / "index.html"

# (nom du mock statique, chemin côté serveur Django)
PAGES = [
    ("index.html", "/"),
    ("boutique.html", "/boutique/"),
]

VIEWPORTS = [
    ("desktop", 1440, 900),
    ("tablet", 768, 1024),
    ("mobile", 390, 844),
]

DIFF_THRESHOLD = 0.0  # en % de pixels différents ; 0 = alerte au moindre pixel


# --------------------------------------------------------------------------- #
# Serveur statique local (sert les mocks HTML à la racine du projet)
# --------------------------------------------------------------------------- #

class _StaticServer:
    """Sert BASE_DIR en HTTP sur un port libre (pour les mocks)."""

    def __init__(self, directory: Path) -> None:
        handler = lambda *a, **kw: SimpleHTTPRequestHandler(  # noqa: E731
            *a, directory=str(directory), **kw
        )
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self._httpd.server_address[1]
        self._thread = None

    def __enter__(self):
        import threading

        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


def start_django_server() -> tuple[subprocess.Popen | None, int | None]:
    """Lance `manage.py runserver` sur un port libre. Retourne (process, port)."""
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    existing = os.environ.get("DJANGO_LIVE_SERVER_URL")
    if existing:
        return None, int(existing.rsplit(":", 1)[1])

    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "manage.py"), "runserver",
         f"127.0.0.1:{port}", "--noreload"],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _wait_for_port(port, timeout=30):
        proc.terminate()
        raise RuntimeError("Le serveur Django n'a pas démarré dans les 30 s.")
    return proc, port


def _wait_for_port(port: int, timeout: float = 15.0) -> bool:
    import socket

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


# --------------------------------------------------------------------------- #
# Captures
# --------------------------------------------------------------------------- #

def capture_all(base_url: str, out_dir: Path, pages: list[tuple[str, str]]) -> None:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, path in pages:
            for vp_name, width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                try:
                    page.goto(f"{base_url}{path}", wait_until="networkidle")
                    # Les Google Fonts / animations peuvent décaler le rendu :
                    # on force le scroll en haut et on laisse les fontes se charger.
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(400)
                    page.screenshot(
                        path=str(out_dir / f"{Path(name).stem}.{vp_name}.png"),
                        full_page=True,
                    )
                finally:
                    page.close()
        browser.close()


# --------------------------------------------------------------------------- #
# Diff pixel
# --------------------------------------------------------------------------- #

def diff_image(ref: Path, cur: Path) -> tuple[float, Image.Image, str]:
    """Retourne (% de pixels différents, image de diff colorisée, note)."""
    a = Image.open(ref).convert("RGB")
    b = Image.open(cur).convert("RGB")
    if a.size != b.size:
        # Tailles différentes => diff maximale. Le plus souvent : la page
        # Django n'existe pas (404) et la capture est une page d'erreur.
        w = max(a.width, b.width)
        h = max(a.height, b.height)
        canvas = Image.new("RGB", (w, h), (255, 0, 255))
        canvas.paste(a, (0, 0))
        return (100.0, canvas,
                "⚠ tailles différentes — la capture Django est probablement "
                "une 404 (page pas encore portée dans les templates)")

    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if bbox is None:
        return 0.0, Image.new("RGB", a.size, (255, 255, 255)), ""

    # Seuil de tolérance : ignorer les micro-écarts (< 12 / 255 par canal)
    gray = diff.convert("L")
    mask = gray.point(lambda v: 255 if v > 12 else 0)

    visual = Image.new("RGB", a.size, (255, 255, 255))
    red = Image.new("RGB", a.size, (255, 0, 0))
    visual.paste(red, mask=mask)

    hist = mask.histogram()
    changed = hist[255]
    pct = 100.0 * changed / (a.width * a.height)
    return pct, visual, ""


# --------------------------------------------------------------------------- #
# Rapport HTML
# --------------------------------------------------------------------------- #

def _img_b64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def build_report(results: list[dict]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    n_ko = sum(1 for r in results if r["pct"] > DIFF_THRESHOLD)
    n_warn = sum(
        1 for r in results if 0 < r["pct"] <= 5.0 and r["pct"] > DIFF_THRESHOLD
    )

    cards = []
    for r in results:
        status = "OK" if r["pct"] <= DIFF_THRESHOLD else "DIFF"
        color = "#1a7f37" if status == "OK" else "#cf222e"
        note_html = (
            f'<p style="color:#9a6700">ℹ {r["note"]}</p>' if r.get("note") else ""
        )
        cards.append(f"""
<details {"open" if status == "DIFF" else ""}>
<summary style="border-left:5px solid {color}">
  <strong>{r['label']}</strong>
  &nbsp;—&nbsp; {r['pct']:.2f} % de pixels différents
  &nbsp;<span style="color:{color}">[{status}]</span>
</summary>
{note_html}
<table><tr>
  <th>Référence (mock)</th><th>Version Django</th><th>Diff</th>
</tr><tr>
  <td><img src="data:image/png;base64,{_img_b64(r['ref'])}"></td>
  <td><img src="data:image/png;base64,{_img_b64(r['cur'])}"></td>
  <td><img src="data:image/png;base64,{_img_b64(r['diff'])}"></td>
</tr></table>
</details>""")

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Rapport de diff visuel — Minivers</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; background: #f6f8fa; }}
h1 {{ font-size: 1.4rem; }}
.summary {{ padding: 1rem; background: #fff; border: 1px solid #d0d7de;
  border-radius: 8px; margin-bottom: 1.5rem; }}
details {{ background: #fff; border: 1px solid #d0d7de; border-radius: 8px;
  margin-bottom: .8rem; }}
summary {{ padding: .8rem; cursor: pointer; }}
table {{ width: 100%; table-layout: fixed; border-collapse: collapse; }}
th, td {{ padding: .4rem; text-align: center; vertical-align: top; }}
img {{ max-width: 100%; border: 1px solid #d0d7de; }}
</style></head><body>
<h1>Rapport de diff visuel — mocks vs Django</h1>
<div class="summary">
  <strong>{len(results)}</strong> comparaisons —
  <strong style="color:#cf222e">{n_ko} en diff</strong>
  (seuil : {DIFF_THRESHOLD} %). Généré le {time.strftime('%Y-%m-%d %H:%M:%S')}.
</div>
{''.join(cards)}
</body></html>"""
    REPORT_PATH.write_text(html, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-only", action="store_true",
                        help="génère uniquement les captures de référence (mocks)")
    parser.add_argument("--diff-only", action="store_true",
                        help="ne re-capture pas la version Django, diff uniquement")
    parser.add_argument("--open", action="store_true",
                        help="ouvre le rapport dans le navigateur")
    args = parser.parse_args()

    print(f"Références : {REFERENCE_DIR}")
    print(f"Rapport    : {REPORT_PATH}")

    # 1. Captures de référence (mocks statiques)
    with _StaticServer(BASE_DIR) as static_srv:
        print(f"Capture des mocks sur http://127.0.0.1:{static_srv.port}/ ...")
        capture_all(f"http://127.0.0.1:{static_srv.port}", REFERENCE_DIR,
                    [(m, "/" + m) for m, _ in PAGES])

    if args.capture_only:
        print("Captures de référence régénérées. (--capture-only : arrêt ici)")
        return 0

    # 2. Captures de la version Django
    if args.diff_only:
        django_url = os.environ.get(
            "DJANGO_LIVE_SERVER_URL", "http://127.0.0.1:8000"
        ).rstrip("/")
        print(f"--diff-only : capture Django ignorée, on suppose {django_url}")
        proc = None
        port = int(django_url.rsplit(":", 1)[1])
    else:
        proc, port = start_django_server()
        print(f"Serveur Django lancé sur le port {port}")

    try:
        if not args.diff_only:
            capture_all(f"http://127.0.0.1:{port}", CURRENT_DIR, PAGES)
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=10)

    # 3. Diff + rapport
    results = []
    for name, _ in PAGES:
        stem = Path(name).stem
        for vp_name, _, _ in VIEWPORTS:
            ref = REFERENCE_DIR / f"{stem}.{vp_name}.png"
            cur = CURRENT_DIR / f"{stem}.{vp_name}.png"
            label = f"{name} [{vp_name}]"
            if not ref.exists() or not cur.exists():
                print(f"  ! {label} : capture manquante ("
                      f"{'ref' if not ref.exists() else 'django'}), ignoré.")
                continue
            pct, diff_img, note = diff_image(ref, cur)
            diff_path = DIFF_DIR / f"{stem}.{vp_name}.diff.png"
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_img.save(diff_path)
            results.append({"label": label, "pct": pct, "ref": ref,
                            "cur": cur, "diff": diff_path, "note": note})
            mark = "OK " if pct <= DIFF_THRESHOLD else "DIFF"
            print(f"  {mark} {label:32s} {pct:6.2f} %"
                  + (f"  {note}" if note else ""))

    build_report(results)

    n_ko = sum(1 for r in results if r["pct"] > DIFF_THRESHOLD)
    print(f"\nRapport généré : {REPORT_PATH}")
    print(f"{len(results)} comparaisons, {n_ko} en diff.")
    if args.open:
        webbrowser.open(REPORT_PATH.as_uri())
    return 1 if n_ko else 0


if __name__ == "__main__":
    sys.exit(main())
