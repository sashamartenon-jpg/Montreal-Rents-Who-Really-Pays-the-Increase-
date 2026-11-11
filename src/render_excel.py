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
from openpyxl.utils import range_boundaries
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
CALC = "Calculs" if LANG == "fr" else "Calculations"
DPI = 400                      # rendu large, puis réduction : le texte reste net sur un écran Retina et dans la vue agrandie
MAX_W, MAX_H = 2400, 2200      # la page affiche une capture sur 1 024 px au plus : 2 400 px couvrent un écran 2x
# dans la feuille Calculs, toute cellule #N/A est une « feuille » : seuls les graphiques la lisent


def soffice(fmt, src, outdir):
    # la langue du système fixe l'affichage des nombres : « 1 346 $ » et « +27,2 % » pour le classeur français
    loc = "fr_CA.UTF-8" if LANG == "fr" else "en_US.UTF-8"
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", fmt, "--outdir", str(outdir), str(src)],
                   check=True, capture_output=True, timeout=300, env={**os.environ, "LANG": loc, "LC_ALL": loc})


tmp = Path(tempfile.mkdtemp())
soffice("xlsx", SRC, tmp)                      # copie calculée (valeurs en cache)
values = load_workbook(tmp / SRC.name, data_only=True)
wb = load_workbook(SRC)
blanked = 0
ws, wv = wb[CALC], values[CALC]
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
    ws.page_margins.top = ws.page_margins.bottom = ws.page_margins.left = ws.page_margins.right = 0.2
    ws.page_margins.header = ws.page_margins.footer = 0     # la feuille occupe toute la page : meilleure définition
    if ws.title in SHEETS and ws.print_area:
        # LibreOffice arrête la page à la dernière ligne qui porte un contenu : une note fusionnée sur deux lignes
        # perdait sa seconde ligne. Une espace en colonne A, au bas de la dernière fusion (copie de rendu seulement).
        bas = range_boundaries(ws.print_area.split("!")[-1].replace("$", ""))[3]
        fin = max((m.max_row for m in ws.merged_cells.ranges if m.max_row <= bas), default=0)
        if fin and ws.cell(row=fin, column=1).value is None:
            ws.cell(row=fin, column=1).value = " "
wb.active = 0
wb.save(tmp / "rendu.xlsx")
soffice("pdf", tmp / "rendu.xlsx", tmp)
subprocess.run(["pdftoppm", "-r", str(DPI), "-png", str(tmp / "rendu.pdf"), str(tmp / "p")], check=True)
pages = sorted(tmp.glob("p-*.png"))
assert len(pages) == len(SHEETS), f"{len(pages)} pages pour {len(SHEETS)} feuilles : une zone d'impression déborde"
for old in OUT.glob("*.png"):
    old.unlink()
for src, slug in zip(pages, SHEETS.values()):
    im = Image.open(src).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if bbox:
        pad = round(16 * DPI / 150)
        im = im.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad)))
    k = min(MAX_W / im.width, MAX_H / im.height, 1)
    if k < 1:
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    # palette de 256 couleurs sans tramage : écart moyen inférieur à 0,2 niveau sur 255, fichier trois fois plus léger
    im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(OUT / f"{slug}.png", optimize=True)
print(f"{blanked} cellules NA vidées pour le rendu · {len(pages)} captures :", ", ".join(sorted(p.name for p in OUT.glob('*.png'))))
