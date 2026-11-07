"""Rend l'image d'aperçu des liens (docs/assets/og-image-v2.png, 1200 × 630) depuis src/og.html.

Le nom de fichier porte une version : les réseaux sociaux (LinkedIn, WhatsApp, Facebook)
gardent l'ancienne image en cache pour une même adresse. Changer le nom force un nouveau
téléchargement partout. Si l'image change à nouveau, incrémenter OUT et le og:image du modèle.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "og.html"
OUT = ROOT / "docs" / "assets" / "og-image-v2.png"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    p.goto(SRC.as_uri())
    p.wait_for_timeout(400)
    p.screenshot(path=str(OUT))
    b.close()

# compression sans perte : les réseaux rechargent l'image à chaque aperçu
from PIL import Image
im = Image.open(OUT).convert("RGB")
im.save(OUT, optimize=True)
print(f"image d'aperçu : {OUT.relative_to(ROOT)} · {OUT.stat().st_size // 1024} Ko")
