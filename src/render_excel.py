"""
Captures des feuilles Excel pour le site (docs/assets/excel/*.png), via LibreOffice.

Excel ne trace pas les points NA() d'un graphique ; LibreOffice peut les tracer à zéro. Pour que la capture
montre ce qu'Excel affiche, le script calcule d'abord le classeur, puis vide dans une copie de rendu les cellules
« feuilles » des séries de graphiques (aucune formule n'en dépend) dont la valeur est #N/A.
Exécution : python src/render_excel.py   (nécessite LibreOffice et pdftoppm)
"""
import subprocess
import tempfile
from pathlib import Path

from openpyxl import load_workbook
from PIL import Image, ImageChops

import os
ROOT = Path(__file__).resolve().parents[1]
LANG = os.environ.get("XL_LANG", "fr")
SRC = ROOT / "docs" / "assets" / ("modele_loyers_montreal.xlsx" if LANG == "fr" else "montreal_rents_workbook.xlsx")
OUT = ROOT / "docs" / "assets" / "excel" / ("" if LANG == "fr" else "en")
OUT.mkdir(parents=True, exist_ok=True)
SHEETS = ({"Accueil": "accueil", "Tableau de bord": "tableau-de-bord", "Carte provinces": "carte-provinces",
           "Carte villes": "carte-villes", "Scénarios": "scenarios", "Simulateur": "simulateur"}
          if LANG == "fr" else
          {"Home": "accueil", "Dashboard": "tableau-de-bord", "Province map": "carte-provinces",
           "City map": "carte-villes", "Scenarios": "scenarios", "Simulator": "simulateur"})
HOME = "Accueil" if LANG == "fr" else "Home"
# dans la feuille Calculs, toute cellule #N/A est une « feuille » : seuls les graphiques la lisent


def soffice(fmt, src, outdir):
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", fmt, "--outdir", str(outdir), str(src)],
                   check=True, capture_output=True, timeout=300)


tmp = Path(tempfile.mkdtemp())
soffice("xlsx", SRC, tmp)                      # copie calculée (valeurs en cache)
values = load_workbook(tmp / SRC.name, data_only=True)
wb = load_workbook(SRC)
blanked = 0
ws, wv = wb["Calculs"], values["Calculs"]
for row in ws.iter_rows(min_row=4):
    for c in row:
        if isinstance(c.value, str) and c.value.startswith("=") and wv[c.coordinate].value == "#N/A":
            c.value = None
            blanked += 1
for ws in wb.worksheets:
    ws.sheet_state = "visible" if ws.title in SHEETS else "hidden"
    if ws.title not in SHEETS and ws.print_area:
        ws.print_area = None     # LibreOffice exporte toute zone d'impression, même sur une feuille masquée
    ws.sheet_view.tabSelected = ws.title == HOME
wb.active = 0
wb.save(tmp / "rendu.xlsx")
soffice("pdf", tmp / "rendu.xlsx", tmp)
subprocess.run(["pdftoppm", "-r", "150", "-png", str(tmp / "rendu.pdf"), str(tmp / "p")], check=True)
pages = sorted(tmp.glob("p-*.png"))
assert len(pages) == len(SHEETS), f"{len(pages)} pages pour {len(SHEETS)} feuilles : une zone d'impression déborde"
for old in OUT.glob("*.png"):
    old.unlink()
for src, slug in zip(pages, SHEETS.values()):
    im = Image.open(src).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if bbox:
        pad = 16
        im = im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))
    im.save(OUT / f"{slug}.png", optimize=True)
print(f"{blanked} cellules NA vidées pour le rendu · {len(pages)} captures :", ", ".join(sorted(p.name for p in OUT.glob('*.png'))))
