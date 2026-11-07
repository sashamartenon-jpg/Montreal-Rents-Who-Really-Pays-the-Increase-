"""
Classeur Excel du projet : docs/assets/modele_loyers_montreal.xlsx

Question : à Montréal, qui paie vraiment la hausse des loyers ?

Feuilles visibles
  Accueil           la question, la réponse en 4 chiffres recalculés, navigation
  Tableau de bord   période et type de logement au choix : 4 indicateurs, 4 graphiques
  Carte provinces   carte du Canada (graphique Excel) : indicateur et année au choix, classement, fiche
  Carte villes      16 régions métropolitaines : loyer demandé contre loyer payé, ville au choix
  Scénarios         trois hypothèses jusqu'en 2030 et délai de rattrapage (NPM)
  Simulateur        un loyer comparé au marché
  Données           6 tableaux sources (onglets gris)
Feuille masquée : Calculs (séries des graphiques ; les NA() n'y servent qu'à masquer des points de graphique).

Règles : aucune macro, aucune valeur collée dans les feuilles d'analyse, aucune cellule vide ni erreur visible.
Les cartes sont des graphiques Excel (nuages de points) : contours projetés en Lambert par src/geo.py.
Exécution : python src/build_excel.py
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.series import SeriesLabel, StrRef
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText, Text
from openpyxl.chart.title import Title
from openpyxl.comments import Comment
from openpyxl.drawing.line import LineProperties
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties, RegularTextRun
from openpyxl.formatting.rule import DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.path.insert(0, str(Path(__file__).parent))
import geo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "docs" / "assets" / "modele_loyers_montreal.xlsx"
OUT.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ version anglaise
# XL_LANG=en : mêmes feuilles, mêmes formules ; textes, onglets, titres de graphiques,
# formats monétaires et chaînes à l'intérieur des formules traduits via src/xl_en.py.
# La traduction passe par un seul point : l'écriture des cellules (openpyxl Cell.value).
import os
import re as _re
LANG = os.environ.get("XL_LANG", "fr")
if LANG == "en":
    OUT = ROOT / "docs" / "assets" / "modele_loyers_montreal_en.xlsx"
    from xl_en import FORMATS as _FM, SHEETS as _SH, STRINGS as _ST
    _SHEET_PATTERNS = []
    for _fr, _en in _SH.items():
        _rep = f"'{_en}'!" if (" " in _en or "-" in _en) else f"{_en}!"
        _SHEET_PATTERNS.append((_re.compile(r"'" + _re.escape(_fr) + r"'!"), _rep))
        if " " not in _fr and "'" not in _fr:
            _SHEET_PATTERNS.append((_re.compile(r"(?<![A-Za-z0-9_'])" + _re.escape(_fr) + r"!"), _rep))

    def tr(t):
        return _ST.get(t, t)

    def tr_sheets(f):
        for rx, rep in _SHEET_PATTERNS:
            f = rx.sub(rep, f)
        return f

    def tr_formula(f):
        f = tr_sheets(f)
        return _re.sub(r'"([^"]*)"', lambda m: '"' + _ST.get(m.group(1), m.group(1)) + '"', f)

    def tr_fmt(fmt):
        return _FM.get(fmt, fmt)

    def tr_sheetname(t):
        return _SH.get(t, t)

    from openpyxl.cell.cell import Cell as _Cell
    _cell_fset = _Cell.value.fset

    def _tr_set(self, v):
        if isinstance(v, str):
            v = tr_formula(v) if v.startswith("=") else _ST.get(v, v)
        _cell_fset(self, v)
    _Cell.value = property(_Cell.value.fget, _tr_set)
else:
    tr = tr_sheets = tr_formula = tr_fmt = tr_sheetname = lambda x: x
    _ST = {}

# ------------------------------------------------------------------ palette du site
BLUE, BLUE_D, BLUE_L, NAVY = "2F86D6", "1F5FA8", "E8F2FC", "163E73"
PINK, PINK_D, PINK_L, CORAL, VIOLET = "E0457B", "B8285E", "FDEAF1", "F2876B", "7B6CD9"
CANVAS, LINE, WHITE = "F4F7FB", "D5DFEA", "FFFFFF"
INK, INK2, INK3, GREY = "13233A", "44546A", "5B6B82", "A9B6C6"
CLASS_COLORS = ["CFE6FA", "9CCBF2", "5FA8E6", "2F86D6", "1F5FA8"]   # quintiles, du plus bas au plus haut
TYPE_COLORS = ["C98500", BLUE, PINK, VIOLET]                         # studio, 1 ch., 2 ch., 3 ch.
FONT = "Arial"
MONEY = '#,##0 "$"' if LANG == "fr" else '"$"#,##0'
MONEY_S = '+#,##0 "$";-#,##0 "$";0 "$"' if LANG == "fr" else '+"$"#,##0;-"$"#,##0;"$"0' 
PCT = "0.0%"
PCT_S = "+0.0%;-0.0%;0.0%"


def F(size=10, bold=False, color=INK, italic=False, underline=None):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic, underline=underline)


def fill(c):
    return PatternFill("solid", fgColor=c)


thin = Side(style="thin", color=LINE)
BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center", indent=1)
INPUT_FONT = F(10, True, "0000FF")

wb = Workbook()


def sheet(title, tab=BLUE):
    ws = wb.create_sheet(tr_sheetname(title))
    ws.sheet_properties.tabColor = tab
    return ws


def name(n, ref):
    wb.defined_names[n] = DefinedName(n, attr_text=tr_sheets(ref))


def banner(ws, title, subtitle, last_col, nav=True):
    """Bandeau bleu, filet rose et corail : même en-tête sur chaque feuille."""
    ws.sheet_view.showGridLines = False
    for r_, h_ in ((1, 34), (2, 20), (3, 5)):
        ws.row_dimensions[r_].height = h_
        for c_ in range(1, last_col + 1):
            ws.cell(row=r_, column=c_).fill = fill(BLUE_D if r_ < 3 else (PINK if c_ <= last_col * 0.6 else CORAL))
    ws.cell(row=1, column=2, value=title).font = F(16, True, "FFFFFF")
    ws.cell(row=2, column=2, value=subtitle).font = F(9, False, "DCEBFA")
    for r_ in (1, 2):
        ws.cell(row=r_, column=2).alignment = Alignment(vertical="center")
    if nav:
        c = ws.cell(row=1, column=last_col, value='=HYPERLINK("#\'Accueil\'!A1","← Accueil")')
        c.font = F(9, True, "FFFFFF", underline="single")
        c.alignment = Alignment(horizontal="right", vertical="center")


def canvas(ws, r0, r1, c0, c1, color=CANVAS):
    for r_ in range(r0, r1 + 1):
        for c_ in range(c0, c1 + 1):
            ws.cell(row=r_, column=c_).fill = fill(color)


def card(ws, r0, c0, r1, c1, accent=BLUE):
    for r_ in range(r0, r1 + 1):
        for c_ in range(c0, c1 + 1):
            cell = ws.cell(row=r_, column=c_)
            cell.fill = fill(WHITE)
            top = Side(style="thick", color=accent) if r_ == r0 else None
            cell.border = Border(top=top, bottom=thin if r_ == r1 else None, left=thin if c_ == c0 else None,
                                 right=thin if c_ == c1 else None)


def label(ws, cell, text, color=INK3):
    ws[cell] = text.upper()
    ws[cell].font = F(8, True, color)


def note(ws, cell, text):
    ws[cell] = text
    ws[cell].font = F(9, color=INK3, italic=True)


def header_row(ws, row, col, labels):
    for i, h in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=h)
        c.font, c.fill, c.border, c.alignment = F(9, True, BLUE_D), fill(BLUE_L), BOX, CENTER


def merge(ws, rng, value=None, font=None, align=None, fill_color=None, border=None):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    if value is not None:
        c.value = value
    if font:
        c.font = font
    c.alignment = align or LEFT
    if fill_color or border:
        for row in ws[rng]:
            for cell in row:
                if fill_color:
                    cell.fill = fill(fill_color)
                if border:
                    cell.border = border
    return c


def selector(ws, rng, value, nm, fmt="General"):
    c = merge(ws, rng, value, INPUT_FONT, CENTER, "FFF6C2", BOX)
    c.number_format = fmt
    first = rng.split(":")[0]
    col = "".join(ch for ch in first if ch.isalpha())
    row = "".join(ch for ch in first if ch.isdigit())
    name(nm, f"'{ws.title}'!${col}${row}")


def validation(ws, cell, **kw):
    for k_ in ("formula1", "error", "errorTitle", "prompt"):
        if isinstance(kw.get(k_), str):
            kw[k_] = tr_formula(kw[k_]) if kw[k_].startswith(("=", '"')) else tr(kw[k_])
    dv = DataValidation(showErrorMessage=True, **kw)
    ws.add_data_validation(dv)
    dv.add(cell)


def chart_title(text, size=1100):
    text = tr(text)
    cp = CharacterProperties(sz=size, b=True, solidFill=INK)
    para = Paragraph(pPr=ParagraphProperties(defRPr=cp), r=[RegularTextRun(rPr=cp, t=text)])
    return Title(tx=Text(rich=RichText(p=[para])), overlay=False)


def style_chart(ch, title, yfmt=None, legend=True, w=13.4, h=8.2):
    ch.title = chart_title(title)
    ch.style = 2
    ch.height, ch.width = h, w
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E6EEF3"))
    if yfmt:
        ch.y_axis.number_format = tr_fmt(yfmt)
    if legend:
        ch.legend.position = "t"   # en bas, Excel superpose légende et étiquettes d'axe
    else:
        ch.legend = None


def color_series(s, color, line=True, width=28575):
    if line:
        s.graphicalProperties.line.solidFill = color
        s.graphicalProperties.line.width = width
        s.smooth = False
        s.marker.symbol = "none"
    else:
        s.graphicalProperties.solidFill = color
        s.graphicalProperties.line.solidFill = color


def value_labels(sr, fmt=None, series_name=False, pos=None, size=None, bold=False, color=None):
    sr.dLbls = DataLabelList()
    sr.dLbls.showVal = not series_name
    sr.dLbls.showSerName = series_name
    sr.dLbls.showCatName = sr.dLbls.showLegendKey = sr.dLbls.showPercent = False
    if fmt:
        sr.dLbls.numFmt = fmt
    if pos:
        sr.dLbls.position = pos
    if size or color:
        cp = CharacterProperties(sz=size or 900, b=bold, solidFill=color or INK)
        sr.dLbls.txPr = RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=cp), endParaRPr=cp)])


def pct_text(ref):
    """Pourcentage signé en texte ; FIXED suit le séparateur décimal de l'Excel de l'utilisateur."""
    return f'IF(({ref})>=0,"+","")&FIXED(({ref})*100,1)&" %"'


def as_table(ws, ref, tname):
    t = Table(displayName=tname, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(t)


# ================================================================== données
rents = pd.read_csv(CLEAN / "fait_loyers_montreal.csv")
units = pd.read_csv(CLEAN / "dim_unit.csv")
cities = pd.read_csv(CLEAN / "fait_loyers_2ch_rmr.csv")
geos = pd.read_csv(CLEAN / "dim_geo.csv")
cpi = pd.read_csv(CLEAN / "ipc_montreal.csv")
schl = pd.read_csv(CLEAN / "schl_roulement.csv")
ipcp = pd.read_csv(CLEAN / "fait_ipc_provinces.csv")
trim = pd.read_csv(CLEAN / "fait_loyer_trimestriel.csv", dtype={"cote": str})
rmr = pd.read_csv(CLEAN / "dim_rmr.csv")
rents = rents.merge(units[["unit_id", "label_fr"]], on="unit_id")
cities = cities.merge(geos[["geo_id", "label_fr"]], on="geo_id")
TYPES = ["Studio", "1 chambre", "2 chambres", "3 chambres"]
YEARS = list(range(1992, 2026))
CITY_LABELS = list(geos.label_fr)
QNUM = {"01": 1, "04": 2, "07": 3, "10": 4}
QLAB = lambda p: f"{p[:4]} T{QNUM[p[5:]]}"
PERIODS = sorted(trim.periode.unique())
LAST_Q = QLAB(PERIODS[-1])

# Régions retenues : loyer demandé ET loyer payé publiés à chacun des trimestres gardés (aucune cellule vide).
w = trim.pivot_table(index="geo_id", columns=["estimation", "periode"], values="loyer")
KEEP_P = [p for p in PERIODS if w[("A", PERIODS[-1])].notna().any()]
complete = lambda ps: w[[(e, p) for e in "AP" for p in ps]].notna().all(axis=1)
KEEP_P = PERIODS if complete(PERIODS).sum() >= complete(PERIODS[1:]).sum() else PERIODS[1:]
ids = sorted(complete(KEEP_P)[complete(KEEP_P)].index)
if LANG == "en":
    # chaînes construites avec le trimestre courant et le nombre de régions
    Q_EN = "Q" + LAST_Q[-1] + " " + LAST_Q[:4]
    _ST.update({
        LAST_Q: LAST_Q,
        f"Annonce moins loyer payé, {LAST_Q}": f"Asking minus rent paid, {Q_EN}",
        f"ANNONCE MOINS LOYER PAYÉ, {LAST_Q}": f"ASKING MINUS RENT PAID, {Q_EN}",
        f"Appartements de 2 chambres, {LAST_Q} · loyer demandé dans les annonces contre loyer payé par les locataires en place · {len(ids)} régions":
            f"Two-bedroom apartments, {Q_EN} · asking rent in listings vs rent paid by sitting tenants · {len(ids)} metro areas",
        f"Les {len(ids)} régions où les deux loyers sont publiés pour {LAST_Q}.":
            f"The {len(ids)} metro areas where both rents are published for {Q_EN}.",
        f"Dernières données : enquête SCHL d'octobre 2025, loyers demandés et payés de {LAST_Q}, IPC annuel 2025.":
            f"Latest data: October 2025 CMHC survey, asking and paid rents for {Q_EN}, 2025 annual CPI.",
        f"• Dernières données : enquête SCHL d'octobre 2025, loyers demandés et payés de {LAST_Q}, IPC annuel 2025.":
            f"• Latest data: October 2025 CMHC survey, asking and paid rents for {Q_EN}, 2025 annual CPI.",
        f"Les {len(ids)} régions où l'on connaît le loyer demandé et le loyer payé. Choisis une ville.":
            f"The {len(ids)} metro areas where both the asking and the paid rent are known. Pick a city.",
        f"Marché 2025 : loyer moyen SCHL par type (RECHERCHEX à deux critères). Gain de relocation : loyer demandé à Montréal au {LAST_Q} moins le loyer actuel, pour les 2 chambres.":
            f"Market 2025: CMHC average rent by type (two-criteria XLOOKUP). Re-let gain: Montreal asking rent in {Q_EN} minus the current rent, for two-bedrooms.",
    })
reg = rmr[rmr.geo_id.isin(ids)].reset_index(drop=True)
MTL_ID = int(rmr.loc[rmr.nom == "Montréal", "geo_id"].iloc[0])
assert MTL_ID in ids
tq = trim[trim.geo_id.isin(ids) & trim.periode.isin(KEEP_P)].merge(rmr[["geo_id", "nom"]], on="geo_id")
assert tq.loyer.notna().all()
tq = tq.assign(trimestre=tq.periode.map(QLAB), est=tq.estimation.map({"A": "Demandé", "P": "Payé"}),
               fiab=np.where(tq.cote.fillna("") == "E", "À utiliser avec prudence", "Normale"))
QS = [QLAB(p) for p in KEEP_P]
PROV = ipcp[ipcp.code != "CA"][["code", "province"]].drop_duplicates().sort_values("province").values.tolist()


def data_sheet(title, tname, df, headers, fmts, names, source, widths):
    ws = sheet(title, GREY)
    banner(ws, title, source, len(headers) + 1)
    header_row(ws, 5, 2, headers)
    for i, row in enumerate(df.itertuples(index=False)):
        for j, v in enumerate(row):
            assert not (v is None or (isinstance(v, float) and np.isnan(v))), f"cellule vide dans {title}"
            c = ws.cell(row=6 + i, column=2 + j, value=v.item() if hasattr(v, "item") else v)
            c.font, c.number_format = F(10, color="0000FF"), fmts[j]
    last = 5 + len(df)
    as_table(ws, f"B5:{CL(1 + len(headers))}{last}", tname)
    for j, nm in enumerate(names):
        if nm:
            name(nm, f"'{title}'!${CL(2 + j)}$6:${CL(2 + j)}${last}")
    ws.row_dimensions[5].height = 30
    ws.column_dimensions["A"].width = 2
    for j, w_ in enumerate(widths):
        ws.column_dimensions[CL(2 + j)].width = w_
    ws.freeze_panes = "B6"
    return ws, last


# ------------------------------------------------------------------ tableaux sources
order = {u: i for i, u in enumerate(["studio", "1ch", "2ch", "3ch"])}
rd = rents.assign(o=rents.unit_id.map(order)).sort_values(["o", "year"])
data_sheet("Loyers Montréal", "tbl_loyers", rd[["year", "label_fr", "loyer_nominal"]].astype({"loyer_nominal": int}),
           ["Année", "Type de logement", "Loyer moyen ($/mois)"], ["0", "@", MONEY], ["Loyers_Annee", "Loyers_Type", "Loyers_Montant"],
           "Statistique Canada 34-10-0133-01 · loyers moyens SCHL, immeubles de 3 logements et plus, octobre", [9, 16, 20])
pv = cities.pivot(index="year", columns="label_fr", values="loyer_nominal")[CITY_LABELS].reset_index()
vws, lastv = data_sheet("Grandes villes", "tbl_villes", pv.astype(int), ["Année"] + CITY_LABELS, ["0"] + [MONEY] * 6,
                        ["Villes_Annees"], "Statistique Canada 34-10-0133-01 · loyer moyen d'un 2 chambres, octobre",
                        [9] + [15] * 6)
name("Villes_Loyers", f"'Grandes villes'!$C$6:$H${lastv}")
name("Villes_Noms", "'Grandes villes'!$C$5:$H$5")
data_sheet("IPC Montréal", "tbl_ipc", cpi[["year", "ipc_2002_100"]], ["Année", "IPC d'ensemble (2002 = 100)"], ["0", "0.0"],
           ["IPC_Annee", "IPC_Valeur"], "Statistique Canada 18-10-0005-01 · moyenne annuelle", [9, 24])
data_sheet("IPC provinces", "tbl_ipc_provinces", ipcp[["annee", "code", "province", "ipc_loyer", "ipc_ensemble"]],
           ["Année", "Code", "Province", "IPC du loyer", "IPC d'ensemble"], ["0", "@", "@", "0.0", "0.0"],
           ["IPCP_Annee", "IPCP_Code", None, "IPCP_Loyer", "IPCP_Ens"],
           "Statistique Canada 18-10-0005-01 · 2002 = 100 · le loyer suit les mêmes logements d'une année à l'autre", [8, 7, 26, 13, 14])
data_sheet("Loyers trimestriels", "tbl_trimestriel", tq[["trimestre", "geo_id", "nom", "est", "loyer", "fiab"]],
           ["Trimestre", "ID", "Région métropolitaine", "Estimation", "Loyer ($)", "Fiabilité"], ["@", "0", "@", "@", MONEY, "@"],
           ["T_Periode", "T_ID", None, "T_Est", "T_Loyer", None],
           f"Statistique Canada 46-10-0092-01 · 2 chambres · les {len(ids)} régions où loyer demandé et payé sont publiés", [10, 6, 40, 11, 11, 22])
data_sheet("SCHL", "tbl_schl", schl[["year", "indicateur", "valeur", "unite"]], ["Année", "Indicateur", "Valeur", "Unité"],
           ["0", "@", "0.0", "@"], ["SCHL_Annee", "SCHL_Indic", "SCHL_Valeur", None],
           "SCHL, Rapport sur le marché locatif 2025 · logements reloués, hausses à échantillon constant", [8, 36, 10, 10])

# ================================================================== Calculs (masquée)
k = sheet("Calculs", GREY)
banner(k, "Calculs", "Séries des graphiques et des cartes · les NA() masquent un point de graphique, aucune autre feuille ne les lit", 40, nav=False)
col_w = {}


def kset(cell, v, fmt=None):
    k[cell] = v
    if fmt:
        k[cell].number_format = fmt


# --- A. Tableau de bord (lignes 5-38)
header_row(k, 4, 1, ["Année", "Loyer (type choisi)", "IPC", "Loyer réel", "Période choisie"] + TYPES)
for i, yr in enumerate(YEARS):
    r = 5 + i
    kset(f"A{r}", yr)
    kset(f"B{r}", f"=SUMIFS(Loyers_Montant,Loyers_Annee,A{r},Loyers_Type,TypeLog)", MONEY)
    kset(f"C{r}", f"=INDEX(IPC_Valeur,MATCH(A{r},IPC_Annee,0))", "0.0")
    kset(f"D{r}", f"=B{r}*INDEX(IPC_Valeur,MATCH(Fin,IPC_Annee,0))/C{r}", MONEY)
    kset(f"E{r}", f"=IF(AND(A{r}>=Debut,A{r}<=Fin),D{r},NA())", MONEY)
    for j, t in enumerate(TYPES):
        kset(f"{CL(6 + j)}{r}", f'=SUMIFS(Loyers_Montant,Loyers_Annee,A{r},Loyers_Type,"{t}")', MONEY)
LASTK = 5 + len(YEARS) - 1
rc = LASTK + 3
header_row(k, rc, 1, ["Ville", "Loyer début", "Loyer fin", "Hausse", "Rang", "Ville (triée)", "Hausse (triée)"])
for j, city in enumerate(CITY_LABELS):
    r = rc + 1 + j
    kset(f"A{r}", city)
    kset(f"B{r}", f"=INDEX(Villes_Loyers,MATCH(Debut,Villes_Annees,0),MATCH(A{r},Villes_Noms,0))", MONEY)
    kset(f"C{r}", f"=INDEX(Villes_Loyers,MATCH(Fin,Villes_Annees,0),MATCH(A{r},Villes_Noms,0))", MONEY)
    kset(f"D{r}", f"=C{r}/B{r}-1+ROW()/1E9", PCT)
    kset(f"E{r}", f"=RANK(D{r},$D${rc + 1}:$D${rc + 6},0)")
    kset(f"F{r}", f"=INDEX($A${rc + 1}:$A${rc + 6},MATCH({j + 1},$E${rc + 1}:$E${rc + 6},0))")
    kset(f"G{r}", f"=INDEX($D${rc + 1}:$D${rc + 6},MATCH({j + 1},$E${rc + 1}:$E${rc + 6},0))", PCT)
C_FIRST, C_LAST = rc + 1, rc + 6
rr = C_LAST + 3
header_row(k, rr, 1, ["Année", "Tous les locataires", "Logements reloués (SCHL)"])
for i, yr in enumerate(range(2022, 2026)):
    r = rr + 1 + i
    kset(f"A{r}", str(yr))
    kset(f"B{r}", f'=SUMIFS(Loyers_Montant,Loyers_Annee,{yr},Loyers_Type,"2 chambres")', MONEY)
    kset(f"C{r}", f'=SUMIFS(SCHL_Valeur,SCHL_Annee,{yr},SCHL_Indic,"loyer_moyen_reloues_2ch")', MONEY)
R_FIRST, R_LAST = rr + 1, rr + 4

# --- B. Scénarios (séries du graphique)
S0 = R_LAST + 3
header_row(k, S0, 1, ["Année", "Historique", "A · Tendance longue", "B · Locataires en place", "C · Rythme récent"])
for i, yr in enumerate(range(2015, 2031)):
    r = S0 + 1 + i
    kset(f"A{r}", str(yr))
    kset(f"B{r}", f'=IF({yr}<=2025,SUMIFS(Loyers_Montant,Loyers_Annee,{yr},Loyers_Type,"2 chambres"),NA())', MONEY)
    for j_, col in enumerate("CDE"):
        kset(f"{col}{r}", f"=IF({yr}>=2025,Scen_Base*(1+INDEX(Scen_Taux,{j_ + 1}))^({yr}-2025),NA())", MONEY)
S_FIRST, S_LAST = S0 + 1, S0 + 16

# --- C. Carte des provinces
IND_PROV = ["Hausse des loyers sur un an", "Hausse des loyers depuis 2019", "Hausse réelle depuis 2019 (après inflation)"]
IND_VILLE = ["Écart entre loyer demandé et loyer payé (%)", "Écart entre loyer demandé et loyer payé ($)", "Loyer demandé ($)"]
L0 = S_LAST + 3
for i, t in enumerate(IND_PROV):
    kset(f"A{L0 + i}", t)
for i, t in enumerate(IND_VILLE):
    kset(f"C{L0 + i}", t)
name("ListeIndProv", f"Calculs!$A${L0}:$A${L0 + 2}")
name("ListeIndVille", f"Calculs!$C${L0}:$C${L0 + 2}")

CAN_BB = (-141.0, 41.7, -52.6, 70.0)
can_out, CB = geo.outlines(CAN_BB, 0.004)
EAST_BB, WEST_BB = (-84.2, 41.8, -59.6, 49.9), (-125.6, 48.0, -95.6, 54.6)
east_out, EB = geo.outlines(EAST_BB, 0.0011)
west_out, WB = geo.outlines(WEST_BB, 0.0014)
SCALE, OFF = 1000.0, 1000.0           # coordonnées ≥ 1000 : un point nul tombe hors des axes
sx = lambda x, b: round(float((x - b[0]) * SCALE + OFF), 2)
sy = lambda y, b: round(float((y - b[1]) * SCALE + OFF), 2)
# position du symbole et décalage de l'étiquette (unités projetées × 1000)
PROV_PT = {"BC": (-124.2, 54.2, 0, -32), "AB": (-114.6, 54.6, 0, -32), "SK": (-106.0, 54.2, 0, -32), "MB": (-97.6, 55.2, 0, -32),
           "ON": (-86.0, 50.2, 0, -32), "QC": (-72.0, 51.6, 0, -32), "NL": (-61.0, 53.4, 0, -32), "NB": (-66.3, 46.6, -58, -6),
           "NS": (-63.0, 45.1, 52, -22), "PE": (-63.2, 46.4, 44, 26)}
P0 = L0 + 6
hdr = ["Code", "Province", "x", "y", "Loyer (année)", "Loyer (année - 1)", "Loyer 2019", "Ensemble (année)", "Ensemble 2019",
       "Sur un an", "Depuis 2019", "Réelle", "Valeur", "Tri", "Rang", "Classe", "Étiquette", "x étiquette", "y étiquette"] + \
      [f"y classe {c}" for c in range(1, 6)] + ["y choisie", "Rang trié", "Province triée", "Valeur triée", "Hausse 2025", "Rang 2025"]
header_row(k, P0 - 1, 1, hdr)
PL = P0 + len(PROV) - 1
for i, (code, pname) in enumerate(PROV + [["CA", "Canada"]]):
    r = P0 + i
    kset(f"A{r}", code)
    kset(f"B{r}", pname)
    LP = lambda yr: f"SUMIFS(IPCP_Loyer,IPCP_Annee,{yr},IPCP_Code,$A{r})"
    EP = lambda yr: f"SUMIFS(IPCP_Ens,IPCP_Annee,{yr},IPCP_Code,$A{r})"
    kset(f"E{r}", f"={LP('AnneeCarte')}", "0.0")
    kset(f"F{r}", f"={LP('AnneeCarte-1')}", "0.0")
    kset(f"G{r}", f"={LP(2019)}", "0.0")
    kset(f"H{r}", f"={EP('AnneeCarte')}", "0.0")
    kset(f"I{r}", f"={EP(2019)}", "0.0")
    kset(f"J{r}", f"=E{r}/F{r}-1", PCT_S)
    kset(f"K{r}", f"=E{r}/G{r}-1", PCT_S)
    kset(f"L{r}", f"=(E{r}/G{r})/(H{r}/I{r})-1", PCT_S)
    kset(f"M{r}", f"=CHOOSE(MATCH(IndCarte,ListeIndProv,0),J{r},K{r},L{r})", PCT_S)
    kset(f"AC{r}", f"={LP(2025)}/{LP(2024)}-1", PCT_S)
    name(f"V_{code}", f"Calculs!$M${r}")
    if code == "CA":
        continue
    lon, lat, dx, dy = PROV_PT[code]
    x_, y_ = geo.proj(lon, lat)
    kset(f"C{r}", sx(x_, CB))
    kset(f"D{r}", sy(y_, CB))
    kset(f"N{r}", f"=M{r}+ROW()/1E9")
    kset(f"O{r}", f"=RANK(N{r},$N${P0}:$N${PL},0)")
    kset(f"P{r}", f"=MATCH(M{r},Seuils_Prov,1)")
    kset(f"Q{r}", f'=A{r}&" "&{pct_text(f"M{r}")}')
    kset(f"R{r}", f"=C{r}+{dx}")
    kset(f"S{r}", f"=D{r}+{dy}")
    for c_ in range(1, 6):
        kset(f"{CL(19 + c_)}{r}", f'=IF(AND(P{r}={c_},A{r}<>ProvSelCode),D{r},NA())')
    kset(f"Y{r}", f'=IF(A{r}=ProvSelCode,D{r},NA())')
    kset(f"Z{r}", i + 1)
    kset(f"AA{r}", f"=INDEX($B${P0}:$B${PL},MATCH(Z{r},$O${P0}:$O${PL},0))")
    kset(f"AB{r}", f"=INDEX($M${P0}:$M${PL},MATCH(Z{r},$O${P0}:$O${PL},0))", PCT_S)
    kset(f"AD{r}", f"=RANK(AC{r},$AC${P0}:$AC${PL},0)")
name("ProvNoms", f"Calculs!$B${P0}:$B${PL}")
name("ProvCodes", f"Calculs!$A${P0}:$A${PL}")
name("ProvValeurs", f"Calculs!$M${P0}:$M${PL}")
name("ProvRangs", f"Calculs!$O${P0}:$O${PL}")
QC_R = P0 + [c for c, _ in PROV].index("QC")
name("QC_Hausse_2025", f"Calculs!$AC${QC_R}")
name("QC_Rang_2025", f"Calculs!$AD${QC_R}")
SP = PL + 3
kset(f"A{SP}", "Seuils (quintiles)")
for i, p in enumerate([0, 0.2, 0.4, 0.6, 0.8]):
    kset(f"B{SP + i}", f"=PERCENTILE(ProvValeurs,{p})", PCT_S)
    kset(f"C{SP + i}", f'={pct_text(f"B{SP + i}")}')
name("Seuils_Prov", f"Calculs!$B${SP}:$B${SP + 4}")
kset(f"E{SP}", "Code choisi")
kset(f"F{SP}", "=INDEX(ProvCodes,MATCH(ProvSel,ProvNoms,0))")
name("ProvSelCode", f"Calculs!$F${SP}")
# IPC du loyer de la province choisie, base 2019 = 100
IP0 = SP + 7
header_row(k, IP0, 1, ["Année", "Province choisie", "Canada"])
for i, yr in enumerate(range(2019, 2026)):
    r = IP0 + 1 + i
    kset(f"A{r}", str(yr))
    kset(f"B{r}", f"=SUMIFS(IPCP_Loyer,IPCP_Annee,{yr},IPCP_Code,ProvSelCode)/SUMIFS(IPCP_Loyer,IPCP_Annee,2019,IPCP_Code,ProvSelCode)*100", "0.0")
    kset(f"C{r}", f'=SUMIFS(IPCP_Loyer,IPCP_Annee,{yr},IPCP_Code,"CA")/SUMIFS(IPCP_Loyer,IPCP_Annee,2019,IPCP_Code,"CA")*100', "0.0")
IP_FIRST, IP_LAST = IP0 + 1, IP0 + 7

# --- D. Carte des villes
V0 = IP_LAST + 4
vh = ["ID", "Région", "x est", "y est", "x ouest", "y ouest", "Demandé", "Payé", "Écart $", "Écart %", "Valeur", "Classe", "Tri", "Rang"] + \
     [f"y est c{c}" for c in range(1, 6)] + [f"y ouest c{c}" for c in range(1, 6)]
header_row(k, V0 - 1, 1, vh)
VL = V0 + len(reg) - 1
q_ = lambda est, r: f'SUMIFS(T_Loyer,T_ID,$A{r},T_Est,"{est}",T_Periode,"{LAST_Q}")'
for i, row in enumerate(reg.itertuples(index=False)):
    r = V0 + i
    x_, y_ = geo.proj(row.lon, row.lat)
    kset(f"A{r}", int(row.geo_id))
    kset(f"B{r}", row.nom)
    kset(f"C{r}", sx(x_, EB)); kset(f"D{r}", sy(y_, EB)); kset(f"E{r}", sx(x_, WB)); kset(f"F{r}", sy(y_, WB))
    kset(f"G{r}", f"={q_('Demandé', r)}", MONEY)
    kset(f"H{r}", f"={q_('Payé', r)}", MONEY)
    kset(f"I{r}", f"=G{r}-H{r}", MONEY_S)
    kset(f"J{r}", f"=G{r}/H{r}-1", PCT_S)
    kset(f"K{r}", f"=CHOOSE(MATCH(IndVilles,ListeIndVille,0),J{r},I{r},G{r})")
    kset(f"L{r}", f"=MATCH(K{r},Seuils_Ville,1)")
    kset(f"M{r}", f"=K{r}+ROW()/1E9")
    kset(f"N{r}", f"=RANK(M{r},$M${V0}:$M${VL},0)")
    for c_ in range(1, 6):
        kset(f"{CL(14 + c_)}{r}", f"=IF(AND(L{r}={c_},A{r}<>VilleSelID),D{r},NA())")
        kset(f"{CL(19 + c_)}{r}", f"=IF(AND(L{r}={c_},A{r}<>VilleSelID),F{r},NA())")
name("V_Noms", f"Calculs!$B${V0}:$B${VL}")
name("V_Valeurs", f"Calculs!$K${V0}:$K${VL}")
name("V_Rangs", f"Calculs!$N${V0}:$N${VL}")
SV = VL + 3
kset(f"A{SV}", "Seuils (quintiles)")
for i, p in enumerate([0, 0.2, 0.4, 0.6, 0.8]):
    kset(f"B{SV + i}", f"=PERCENTILE(V_Valeurs,{p})")
    kset(f"C{SV + i}", f'=IF(VillePct,{pct_text(f"B{SV + i}")},FIXED(B{SV + i},0)&" $")')
name("Seuils_Ville", f"Calculs!$B${SV}:$B${SV + 4}")
kset(f"E{SV}", "Ville choisie"); kset(f"F{SV}", "=MATCH(VilleSel,V_Noms,0)")
kset(f"E{SV + 1}", "ID"); kset(f"F{SV + 1}", f"=INDEX($A${V0}:$A${VL},F{SV})")
for j, (lab_, col_) in enumerate([("x est", "C"), ("y est", "D"), ("x ouest", "E"), ("y ouest", "F")]):
    kset(f"E{SV + 2 + j}", lab_); kset(f"F{SV + 2 + j}", f"=INDEX(${col_}${V0}:${col_}${VL},$F${SV})")
kset(f"G{SV}", "=VilleSel")
kset(f"H{SV}", "=MATCH(IndVilles,ListeIndVille,0)=1")
name("VilleSelRow", f"Calculs!$F${SV}")
name("VilleSelID", f"Calculs!$F${SV + 1}")
name("VillePct", f"Calculs!$H${SV}")
T0 = SV + 8
header_row(k, T0 - 1, 1, ["Rang", "Région", "Valeur", "Valeur (texte)"])
for i in range(10):
    r = T0 + i
    kset(f"A{r}", i + 1)
    kset(f"B{r}", f"=INDEX(V_Noms,MATCH({i + 1},V_Rangs,0))")
    kset(f"C{r}", f"=INDEX(V_Valeurs,MATCH({i + 1},V_Rangs,0))")
    kset(f"D{r}", f'=IF(VillePct,{pct_text(f"C{r}")},FIXED(C{r},0)&" $")')
Q0 = T0 + 12
header_row(k, Q0, 1, ["Trimestre", "Loyer demandé", "Loyer payé"])
for i, q in enumerate(QS):
    r = Q0 + 1 + i
    kset(f"A{r}", q)
    kset(f"B{r}", f'=SUMIFS(T_Loyer,T_ID,VilleSelID,T_Est,"Demandé",T_Periode,"{q}")', MONEY)
    kset(f"C{r}", f'=SUMIFS(T_Loyer,T_ID,VilleSelID,T_Est,"Payé",T_Periode,"{q}")', MONEY)
QS0, QS1 = Q0 + 1, Q0 + len(QS)

# --- E. Contours (une série par carte, anneaux séparés par une ligne vide)
O_COL = 36
outline_last = {}
for lab_, outs, B_, c0 in (("Canada", can_out, CB, O_COL), ("Est", east_out, EB, O_COL + 3), ("Ouest", west_out, WB, O_COL + 6)):
    k.cell(row=4, column=c0, value=f"Contours {lab_}").font = F(9, True)
    r_ = 5
    for _, ring in outs:
        for x_, y_ in ring:
            k.cell(row=r_, column=c0, value=sx(x_, B_))
            k.cell(row=r_, column=c0 + 1, value=sy(y_, B_))
            r_ += 1
        r_ += 1
    outline_last[c0] = r_ - 2
k.conditional_formatting.add(f"A4:AJ{max(VL, QS1) + 2}", FormulaRule(formula=["ISNA(A4)"], font=F(9, color="C9CED6")))
for c_ in range(1, 45):
    k.column_dimensions[CL(c_)].width = 12
k.column_dimensions["B"].width = 34


def map_chart(title, bbox, w, outline_col, x_ref, class_cols, sel, extra=()):
    """Carte = graphique en nuage de points : contours, 5 classes de couleur, sélection en rose, étiquettes."""
    ch = ScatterChart()
    ch.title = chart_title(title, 1100)
    ch.style = 2
    ch.scatterStyle = "lineMarker"
    ch.legend = None
    ratio = (bbox[3] - bbox[1]) / (bbox[2] - bbox[0])
    ch.width, ch.height = w, w * 0.96 * ratio / 0.86
    ch.plot_area.layout = Layout(manualLayout=ManualLayout(layoutTarget="inner", xMode="edge", yMode="edge", x=0.02, y=0.11, w=0.96, h=0.86))
    o = Series(Reference(k, min_col=outline_col + 1, min_row=5, max_row=outline_last[outline_col]),
               Reference(k, min_col=outline_col, min_row=5, max_row=outline_last[outline_col]), title="Contours")
    o.marker.symbol = "none"
    o.graphicalProperties.line.solidFill = "9FB2C8"
    o.graphicalProperties.line.width = 9525
    ch.series.append(o)
    for c_, (ycol, size) in enumerate(class_cols):
        s_ = Series(Reference(k, min_col=ycol, min_row=x_ref[1], max_row=x_ref[2]),
                    Reference(k, min_col=x_ref[0], min_row=x_ref[1], max_row=x_ref[2]), title=f"Classe {c_ + 1}")
        s_.marker.symbol, s_.marker.size = "circle", size
        s_.marker.graphicalProperties = GraphicalProperties(solidFill=CLASS_COLORS[c_])
        s_.marker.graphicalProperties.line.solidFill = "FFFFFF"
        s_.graphicalProperties.line.noFill = True
        ch.series.append(s_)
    ycol, xcell, name_ref, size = sel
    s_ = Series(Reference(k, min_col=ycol[0], min_row=ycol[1], max_row=ycol[2]),
                Reference(k, min_col=xcell[0], min_row=xcell[1], max_row=xcell[2]))
    if name_ref:
        s_.tx = SeriesLabel(strRef=StrRef(name_ref))
        value_labels(s_, series_name=True, pos="r", size=1000, bold=True, color=PINK_D)
    s_.marker.symbol, s_.marker.size = "circle", size
    s_.marker.graphicalProperties = GraphicalProperties(solidFill=PINK)
    s_.marker.graphicalProperties.line.solidFill = "FFFFFF"
    s_.graphicalProperties.line.noFill = True
    ch.series.append(s_)
    for s_ in extra:
        ch.series.append(s_)
    for s_ in ch.series:
        s_.smooth = False
    ch.display_blanks = "gap"
    x0, y0, x1, y1 = bbox
    ch.x_axis.scaling.min, ch.x_axis.scaling.max = OFF, OFF + (x1 - x0) * SCALE
    ch.y_axis.scaling.min, ch.y_axis.scaling.max = OFF, OFF + (y1 - y0) * SCALE
    ch.x_axis.delete = ch.y_axis.delete = True
    ch.x_axis.majorGridlines = ch.y_axis.majorGridlines = None
    ch.plot_area.graphicalProperties = GraphicalProperties(solidFill="FFFFFF")
    return ch


# ================================================================== Tableau de bord
d = sheet("Tableau de bord", BLUE_D)
d.sheet_view.zoomScale = 90
banner(d, "Tableau de bord : loyers à Montréal, 1992-2025", "Modifie les cases jaunes : les 4 indicateurs et les 4 graphiques se recalculent", 14)
d.column_dimensions["A"].width = 2
for c_ in range(2, 15):
    d.column_dimensions[CL(c_)].width = 11.5
canvas(d, 4, 50, 1, 14)
for lab_rng, lab, in_rng, val, nm in [("B5:C5", "Année de début", "D5:E5", 2019, "Debut"), ("F5:G5", "Année de fin", "H5:I5", 2025, "Fin"),
                                      ("J5:K5", "Logement", "L5:M5", "2 chambres", "TypeLog")]:
    merge(d, lab_rng, lab, F(10, True, INK2), RIGHT)
    selector(d, in_rng, val, nm)
d.row_dimensions[5].height = 22
validation(d, "D5", type="whole", operator="between", formula1="1992", formula2="2024", error="Choisis une année entre 1992 et 2024.")
validation(d, "H5", type="whole", operator="between", formula1="1993", formula2="2025", error="Choisis une année entre 1993 et 2025.")
validation(d, "L5", type="list", formula1='"Studio,1 chambre,2 chambres,3 chambres"')
d["B6"] = '=IF(Debut>=Fin,"L\'année de début doit précéder l\'année de fin.","")'
d["B6"].font = F(9, True, "B42323")
LOY = lambda yr: f"SUMIFS(Loyers_Montant,Loyers_Annee,{yr},Loyers_Type,TypeLog)"
IPCV = lambda yr: f"INDEX(IPC_Valeur,MATCH({yr},IPC_Annee,0))"
cards = [
    ("B", "D", "Loyer moyen, année de fin", f"={LOY('Fin')}", MONEY, BLUE, '=TypeLog&", octobre "&Fin', None, None),
    ("E", "G", "Hausse réelle (après inflation)", f"=({LOY('Fin')}/{LOY('Debut')})/({IPCV('Fin')}/{IPCV('Debut')})-1", PCT_S, PINK,
     "Hausse nominale", f"={LOY('Fin')}/{LOY('Debut')}-1", PCT_S),
    ("H", "J", "Rythme annuel réel", "=IFERROR((1+E9)^(1/(Fin-Debut))-1,0)", PCT_S, PINK, '="Croissance composée sur "&(Fin-Debut)&" ans"', None, None),
    ("K", "M", "Prime de relocation 2025 (2 ch.)",
     '=SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"loyer_moyen_reloues_2ch")-SUMIFS(Loyers_Montant,Loyers_Annee,2025,Loyers_Type,"2 chambres")',
     MONEY_S, CORAL, "Loyer d'un 2 ch. reloué", '=SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"loyer_moyen_reloues_2ch")', MONEY),
]
for c1, c2, lab, f, fmt, accent, sub, sub_f, sub_fmt in cards:
    card(d, 8, ord(c1) - 64, 11, ord(c2) - 64, accent)
    merge(d, f"{c1}8:{c2}8", lab.upper(), F(8, True, INK3))
    merge(d, f"{c1}9:{c2}10", f, F(24, True, PINK_D if accent != BLUE else BLUE_D))
    d[f"{c1}9"].number_format = fmt
    if sub_f:
        merge(d, f"{c1}11:{chr(ord(c1) + 1)}11", sub, F(9, color=INK2))
        d[f"{c2}11"] = sub_f
        d[f"{c2}11"].font, d[f"{c2}11"].number_format, d[f"{c2}11"].alignment = F(9, True, INK2), sub_fmt, RIGHT
    else:
        merge(d, f"{c1}11:{c2}11", sub, F(9, color=INK2))
d.row_dimensions[8].height = 20
d.row_dimensions[11].height = 18
c1_ = LineChart()
style_chart(c1_, "Loyer réel du type choisi (en couleur : période choisie)", yfmt='#,##0 "$"', legend=False)
c1_.add_data(Reference(k, min_col=4, max_col=5, min_row=4, max_row=LASTK), titles_from_data=True)
c1_.set_categories(Reference(k, min_col=1, min_row=5, max_row=LASTK))
color_series(c1_.series[0], "C9D3DF", width=19050)
color_series(c1_.series[1], BLUE, width=38100)
c1_.display_blanks = "gap"
d.add_chart(c1_, "B13")
c2_ = BarChart()
c2_.type = "bar"
style_chart(c2_, "Hausse du 2 chambres sur la période choisie", yfmt="0%", legend=False)
c2_.add_data(Reference(k, min_col=7, min_row=C_FIRST, max_row=C_LAST), titles_from_data=False)
c2_.set_categories(Reference(k, min_col=6, min_row=C_FIRST, max_row=C_LAST))
color_series(c2_.series[0], BLUE, line=False)
value_labels(c2_.series[0], "0%")
c2_.x_axis.scaling.orientation = "maxMin"
c2_.gapWidth = 50
d.add_chart(c2_, "H13")
c3_ = LineChart()
style_chart(c3_, "Loyer par type de logement (dollars courants)", yfmt='#,##0 "$"')
c3_.add_data(Reference(k, min_col=6, max_col=9, min_row=4, max_row=LASTK), titles_from_data=True)
c3_.set_categories(Reference(k, min_col=1, min_row=5, max_row=LASTK))
for s_, col in zip(c3_.series, TYPE_COLORS):
    color_series(s_, col, width=25400)
d.add_chart(c3_, "B31")
c4_ = BarChart()
style_chart(c4_, "2 chambres : tous les locataires et logements reloués", yfmt='#,##0 "$"')
c4_.add_data(Reference(k, min_col=2, max_col=3, min_row=rr, max_row=R_LAST), titles_from_data=True)
c4_.set_categories(Reference(k, min_col=1, min_row=R_FIRST, max_row=R_LAST))
color_series(c4_.series[0], BLUE, line=False)
color_series(c4_.series[1], PINK, line=False)
for s_ in c4_.series:
    value_labels(s_)
c4_.gapWidth = 60
c4_.overlap = -10
d.add_chart(c4_, "H31")
note(d, "B49", "Sources : Statistique Canada 34-10-0133-01, 18-10-0005-01 ; SCHL, Rapport sur le marché locatif 2025.")
d.freeze_panes = "A7"

# ================================================================== Carte provinces
cp = sheet("Carte provinces", BLUE)
cp.sheet_view.zoomScale = 85
banner(cp, "Carte du Canada : où les loyers montent-ils le plus vite ?",
       "Indice des prix du loyer par province · choisis l'indicateur, l'année et la province (cases jaunes)", 16)
cp.column_dimensions["A"].width = 2
for c_ in range(2, 11):
    cp.column_dimensions[CL(c_)].width = 10.5
for c_, w_ in zip(range(11, 17), [9, 27, 12, 12, 14, 3]):
    cp.column_dimensions[CL(c_)].width = w_
canvas(cp, 4, 52, 1, 16)
cp.row_dimensions[5].height = cp.row_dimensions[6].height = 24
merge(cp, "B5:C5", "Indicateur", F(10, True, INK2), RIGHT)
selector(cp, "D5:G5", IND_PROV[0], "IndCarte")
merge(cp, "B6:C6", "Année", F(10, True, INK2), RIGHT)
selector(cp, "D6:E6", 2025, "AnneeCarte", "0")
merge(cp, "H5:H5", "Province", F(10, True, INK2), RIGHT)
selector(cp, "I5:J5", "Québec", "ProvSel")
validation(cp, "D5", type="list", formula1="ListeIndProv")
validation(cp, "D6", type="whole", operator="between", formula1="2020", formula2="2025", error="Choisis une année entre 2020 et 2025.")
validation(cp, "I5", type="list", formula1="ProvNoms")
merge(cp, "F6:J6", '="Hausse de "&(AnneeCarte-1)&" à "&AnneeCarte&" pour l\'indicateur sur un an"', F(9, color=INK3, italic=True))
labels = []
for i, (code, _) in enumerate(PROV):
    r = P0 + i
    s_ = Series(Reference(k, min_col=19, min_row=r, max_row=r), Reference(k, min_col=18, min_row=r, max_row=r))
    s_.tx = SeriesLabel(strRef=StrRef(f"Calculs!$Q${r}"))
    s_.marker.symbol = "none"
    s_.graphicalProperties.line.noFill = True
    value_labels(s_, series_name=True, pos="ctr", size=900, bold=True, color=INK)
    labels.append(s_)
cp.add_chart(map_chart("Canada · une bulle par province, couleur selon la valeur (rose : province choisie)", CB, 18.6, O_COL,
                       (3, P0, PL), [(20 + c_, 12 + 3 * c_) for c_ in range(5)], ((25, P0, PL), (3, P0, PL), None, 26), labels), "B8")
label(cp, "L8", "Classement des provinces")
for j, h_ in enumerate(["Province", "Valeur", "Rang", "Écart au Canada"]):
    c = cp.cell(row=9, column=12 + j, value=h_)
    c.font, c.fill, c.border, c.alignment = F(9, True, BLUE_D), fill(BLUE_L), BOX, CENTER
for i in range(len(PROV)):
    r_ = 10 + i
    cp[f"L{r_}"] = f"=Calculs!AA{P0 + i}"
    cp[f"M{r_}"] = f"=Calculs!AB{P0 + i}"
    cp[f"N{r_}"] = i + 1
    cp[f"O{r_}"] = f"=(M{r_}-V_CA)*100"
    cp[f"M{r_}"].number_format, cp[f"O{r_}"].number_format = PCT_S, '+0.0" pts";-0.0" pts";0.0" pts"'
    for j_ in range(4):
        c = cp.cell(row=r_, column=12 + j_)
        c.fill, c.border, c.font = fill(WHITE), BOX, F(10)
        c.alignment = LEFT if j_ == 0 else Alignment(horizontal="center", vertical="center")
CR1 = 10 + len(PROV) - 1
cp[f"L{CR1 + 1}"], cp[f"M{CR1 + 1}"] = "Canada (référence)", "=V_CA"
cp[f"L{CR1 + 1}"].font = cp[f"M{CR1 + 1}"].font = F(10, True, INK2)
cp[f"M{CR1 + 1}"].number_format, cp[f"M{CR1 + 1}"].alignment = PCT_S, Alignment(horizontal="center")
cp.conditional_formatting.add(f"L10:O{CR1}", FormulaRule(formula=["$L10=ProvSel"], fill=fill(PINK_L), font=F(10, True, PINK_D)))
cp.conditional_formatting.add(f"M10:M{CR1}", DataBarRule(start_type="num", start_value=0, end_type="max", color="9CCBF2"))
RC = CR1 + 3
label(cp, f"L{RC}", "Province choisie", PINK_D)
card(cp, RC + 1, 12, RC + 7, 15, PINK)
merge(cp, f"L{RC + 1}:O{RC + 1}", "=ProvSel", F(14, True, INK))
cp.row_dimensions[RC + 1].height = 22
for i, (lab_, f_, fmt) in enumerate([
        ("Valeur de l'indicateur", "=INDEX(ProvValeurs,MATCH(ProvSel,ProvNoms,0))", PCT_S),
        ("Rang sur 10 provinces", "=INDEX(ProvRangs,MATCH(ProvSel,ProvNoms,0))", "0"),
        ('="Hausse sur un an ("&AnneeCarte&")"', f"=INDEX(Calculs!$J${P0}:$J${PL},MATCH(ProvSel,ProvNoms,0))", PCT_S),
        ('="Hausse 2019 → "&AnneeCarte', f"=INDEX(Calculs!$K${P0}:$K${PL},MATCH(ProvSel,ProvNoms,0))", PCT_S),
        ('="Hausse réelle 2019 → "&AnneeCarte', f"=INDEX(Calculs!$L${P0}:$L${PL},MATCH(ProvSel,ProvNoms,0))", PCT_S)]):
    r_ = RC + 2 + i
    merge(cp, f"L{r_}:M{r_}", lab_, F(10, color=INK2))
    merge(cp, f"N{r_}:O{r_}", f_, F(11, True, INK), RIGHT)
    cp[f"N{r_}"].number_format = fmt
chp = LineChart()
style_chart(chp, "IPC du loyer, base 2019 = 100", w=13, h=6.5)
chp.add_data(Reference(k, min_col=2, max_col=3, min_row=IP0, max_row=IP_LAST), titles_from_data=True)
chp.set_categories(Reference(k, min_col=1, min_row=IP_FIRST, max_row=IP_LAST))
color_series(chp.series[0], PINK, width=31750)
color_series(chp.series[1], GREY, width=19050)
chp.y_axis.scaling.min = 90
cp.add_chart(chp, f"L{RC + 9}")
label(cp, "B31", "Légende : quintiles de l'indicateur (une couleur = 2 provinces)")
for i in range(5):
    c = cp.cell(row=32, column=2 + 2 * i)
    c.fill = fill(CLASS_COLORS[i])
    cp.cell(row=32, column=3 + 2 * i, value=f"=\"≥ \"&Calculs!C{SP + i}").font = F(9, color=INK2)
note(cp, "B34", "Contours : Natural Earth (domaine public), projection conique conforme de Lambert (paramètres de Statistique Canada), "
                "calculée par src/geo.py. Territoires : pas d'IPC provincial publié.")
cp.freeze_panes = "A7"

# ================================================================== Carte villes
cv = sheet("Carte villes", BLUE)
cv.sheet_view.zoomScale = 85
banner(cv, "Carte des villes : combien coûte un déménagement ?",
       f"Appartements de 2 chambres, {LAST_Q} · loyer demandé dans les annonces contre loyer payé par les locataires en place · {len(ids)} régions", 16)
cv.column_dimensions["A"].width = 2
for c_ in range(2, 11):
    cv.column_dimensions[CL(c_)].width = 10
for c_, w_ in zip(range(11, 17), [4, 34, 12, 12, 7, 3]):
    cv.column_dimensions[CL(c_)].width = w_
canvas(cv, 4, 60, 1, 16)
cv.row_dimensions[5].height = cv.row_dimensions[6].height = 24
merge(cv, "B5:C5", "Indicateur", F(10, True, INK2), RIGHT)
selector(cv, "D5:H5", IND_VILLE[0], "IndVilles")
merge(cv, "B6:C6", "Ville", F(10, True, INK2), RIGHT)
selector(cv, "D6:H6", "Montréal", "VilleSel")
validation(cv, "D5", type="list", formula1="ListeIndVille")
validation(cv, "D6", type="list", formula1="V_Noms")
SEL_ROWS = (SV + 2, SV + 3, SV + 4, SV + 5)
cv.add_chart(map_chart("Québec, Ontario et Maritimes", EB, 17.4, O_COL + 3, (3, V0, VL), [(15 + c_, 7 + 2 * c_) for c_ in range(5)],
                       ((6, SEL_ROWS[1], SEL_ROWS[1]), (6, SEL_ROWS[0], SEL_ROWS[0]), f"Calculs!$G${SV}", 17)), "B8")
cv.add_chart(map_chart("Prairies et Colombie-Britannique", WB, 17.4, O_COL + 6, (5, V0, VL), [(20 + c_, 7 + 2 * c_) for c_ in range(5)],
                       ((6, SEL_ROWS[3], SEL_ROWS[3]), (6, SEL_ROWS[2], SEL_ROWS[2]), f"Calculs!$G${SV}", 17)), "B35")
label(cv, "L8", "Ville choisie", PINK_D)
card(cv, 9, 12, 15, 15, PINK)
merge(cv, "L9:O9", "=VilleSel", F(14, True, INK))
cv.row_dimensions[9].height = 22
for i, (lab_, col_, fmt) in enumerate([("Loyer demandé (annonces)", "G", MONEY), ("Loyer payé (locataires en place)", "H", MONEY),
                                       ("Écart par mois", "I", MONEY_S), ("Écart en %", "J", PCT_S)]):
    r_ = 10 + i
    merge(cv, f"L{r_}:M{r_}", lab_, F(10, color=INK2))
    merge(cv, f"N{r_}:O{r_}", f"=INDEX(Calculs!${col_}${V0}:${col_}${VL},VilleSelRow)", F(11, True, INK), RIGHT)
    cv[f"N{r_}"].number_format = fmt
merge(cv, "L14:M14", "Rang pour l'indicateur", F(10, color=INK2))
merge(cv, "N14:O14", f'=INDEX(V_Rangs,VilleSelRow)&" sur {len(ids)}"', F(11, True, INK), RIGHT)
merge(cv, "L15:O15", f"Les {len(ids)} régions où les deux loyers sont publiés pour {LAST_Q}.", F(8, color=INK3, italic=True))
label(cv, "L17", "Légende : quintiles de l'indicateur")
for i in range(5):
    cv[f"L{18 + i}"] = f"=\"Classe {i + 1} : à partir de \"&Calculs!C{SV + i}"
    cv[f"L{18 + i}"].font = F(9, color=INK2)
    cv[f"M{18 + i}"].fill = fill(CLASS_COLORS[i])
label(cv, "L24", "Les 10 premières régions")
for j, h_ in enumerate(["Région", "Valeur", "", "Rang"]):
    c = cv.cell(row=25, column=12 + j, value=h_)
    c.font, c.fill, c.border, c.alignment = F(9, True, BLUE_D), fill(BLUE_L), BOX, CENTER
for i in range(10):
    r_ = 26 + i
    cv[f"L{r_}"] = f"=Calculs!B{T0 + i}"
    cv[f"M{r_}"] = f"=Calculs!D{T0 + i}"
    cv[f"N{r_}"] = f"=Calculs!C{T0 + i}"
    cv[f"O{r_}"] = i + 1
    for j in range(4):
        c = cv.cell(row=r_, column=12 + j)
        c.fill, c.border, c.font = fill(WHITE), BOX, F(10)
        c.alignment = LEFT if j == 0 else Alignment(horizontal="center", vertical="center")
cv.conditional_formatting.add("N26:N35", DataBarRule(start_type="min", end_type="max", color="9CCBF2", showValue=False))
cv.conditional_formatting.add("L26:O35", FormulaRule(formula=["$L26=VilleSel"], fill=fill(PINK_L), font=F(10, True, PINK_D)))
label(cv, "L51", "Repères du marché (calculés sur le tableau source)")
MXF = lambda fn: f'=_xlfn.{fn}(T_Loyer,T_Est,"Demandé",T_Periode,"{LAST_Q}")'
for i, (lab_, fn) in enumerate([("Loyer demandé le plus élevé", "MAXIFS"), ("Loyer demandé le plus bas", "MINIFS")]):
    r_ = 52 + i
    merge(cv, f"L{r_}:M{r_}", lab_, F(10, color=INK2))
    cv[f"N{r_}"] = MXF(fn)
    cv[f"N{r_}"].number_format, cv[f"N{r_}"].font, cv[f"N{r_}"].alignment = MONEY, F(11, True, INK), RIGHT
    cv[f"O{r_}"] = f"=INDEX(V_Noms,MATCH(N{r_},Calculs!$G${V0}:$G${VL},0))"
    cv[f"O{r_}"].font, cv[f"O{r_}"].alignment = F(9, color=INK3), LEFT
chq = LineChart()
style_chart(chq, "Ville choisie : loyer demandé et loyer payé", yfmt='#,##0 "$"', w=13, h=7)
chq.add_data(Reference(k, min_col=2, max_col=3, min_row=Q0, max_row=QS1), titles_from_data=True)
chq.set_categories(Reference(k, min_col=1, min_row=QS0, max_row=QS1))
color_series(chq.series[0], PINK, width=31750)
color_series(chq.series[1], BLUE, width=31750)
for s_ in chq.series:
    s_.marker.symbol, s_.marker.size = "circle", 6
cv.add_chart(chq, "L38")
note(cv, "B58", "Positions : projection conique conforme de Lambert (src/geo.py). Contours : Natural Earth. "
                "Estimations expérimentales de Statistique Canada (46-10-0092-01).")
cv.freeze_panes = "A7"

# ================================================================== Scénarios
sc = sheet("Scénarios", PINK)
banner(sc, "Scénarios : quand le loyer moyen rattrapera-t-il les annonces ?",
       "Loyer moyen d'un 2 chambres à Montréal · trois hypothèses tirées des données · des scénarios pour raisonner, pas une prévision", 21)
sc.column_dimensions["A"].width = 2
canvas(sc, 4, 40, 1, 21)
label(sc, "B5", "Point de départ")
sc["B6"], sc["E6"] = "Loyer moyen 2025, tous les locataires", '=SUMIFS(Loyers_Montant,Loyers_Annee,2025,Loyers_Type,"2 chambres")'
sc["B7"], sc["E7"] = f"Loyer demandé dans les annonces, {LAST_Q}", f'=SUMIFS(T_Loyer,T_ID,{MTL_ID},T_Est,"Demandé",T_Periode,"{LAST_Q}")'
for c_ in ("E6", "E7"):
    sc[c_].number_format, sc[c_].font = MONEY, F(11, True, "008000")
name("Scen_Base", "'Scénarios'!$E$6")
label(sc, "B9", "Hypothèses de croissance annuelle")
header_row(sc, 10, 2, ["Scénario", "", "Source du taux", "Taux tiré des données", "Ajustement (points)", "Taux retenu", "Rattrape les annonces en"])
sc.merge_cells("B10:C10")
scen = [
    ("A · Tendance longue", "Croissance annuelle composée 1992-2019",
     '=(SUMIFS(Loyers_Montant,Loyers_Annee,2019,Loyers_Type,"2 chambres")/SUMIFS(Loyers_Montant,Loyers_Annee,1992,Loyers_Type,"2 chambres"))^(1/27)-1'),
    ("B · Locataires en place", "Hausse 2025 des loyers non reloués (SCHL)",
     '=SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"hausse_loyer_non_reloues_2ch")/100'),
    ("C · Rythme récent", "Croissance annuelle composée 2019-2025",
     '=(SUMIFS(Loyers_Montant,Loyers_Annee,2025,Loyers_Type,"2 chambres")/SUMIFS(Loyers_Montant,Loyers_Annee,2019,Loyers_Type,"2 chambres"))^(1/6)-1'),
]
for i, (lab_, src_, f_) in enumerate(scen):
    r = 11 + i
    merge(sc, f"B{r}:C{r}", lab_, F(10, True), fill_color=WHITE, border=BOX)
    sc[f"D{r}"], sc[f"E{r}"] = src_, f_
    sc[f"D{r}"].font = F(9, color=INK2)
    sc[f"F{r}"] = 0
    sc[f"F{r}"].font, sc[f"F{r}"].fill, sc[f"F{r}"].border, sc[f"F{r}"].number_format = INPUT_FONT, fill("FFF6C2"), BOX, PCT_S
    sc[f"F{r}"].alignment = Alignment(horizontal="center")
    sc[f"G{r}"] = f"=E{r}+F{r}"
    sc[f"H{r}"] = f'=IF(G{r}<=0,"jamais",ROUNDUP(NPER(G{r},0,-$E$6,$E$7),0)&" ans ("&(2025+ROUNDUP(NPER(G{r},0,-$E$6,$E$7),0))&")")'
    sc[f"E{r}"].number_format = sc[f"G{r}"].number_format = PCT
    sc[f"H{r}"].alignment = RIGHT
    for col in "DEGH":
        sc[f"{col}{r}"].fill, sc[f"{col}{r}"].border = fill(WHITE), BOX
name("Scen_Taux", "'Scénarios'!$G$11:$G$13")
sc.conditional_formatting.add("G11:G13", DataBarRule(start_type="num", start_value=0, end_type="max", color="9CCBF2"))
note(sc, "B15", "« Rattrape les annonces » : années pour que le loyer moyen atteigne le loyer affiché aujourd'hui (fonction NPM).")
header_row(sc, 17, 2, ["Année", "Loyer moyen"])
for i, yr in enumerate(range(2015, 2026)):
    r = 18 + i
    sc[f"B{r}"], sc[f"C{r}"] = str(yr), f'=SUMIFS(Loyers_Montant,Loyers_Annee,{yr},Loyers_Type,"2 chambres")'
    sc[f"C{r}"].number_format = MONEY
header_row(sc, 17, 5, ["Année", "A · Tendance", "B · En place", "C · Récent"])
for i, yr in enumerate(range(2026, 2031)):
    r = 18 + i
    sc[f"E{r}"] = str(yr)
    for j_, col in enumerate("FGH"):
        sc[f"{col}{r}"] = f"=$E$6*(1+$G${11 + j_})^({yr}-2025)"
        sc[f"{col}{r}"].number_format = MONEY
for rng in ("B18:C28", "E18:H22"):
    for row in sc[rng]:
        for c in row:
            c.fill, c.border = fill(WHITE), BOX
            c.alignment = Alignment(horizontal="center")
chs_ = LineChart()
style_chart(chs_, "Loyer moyen d'un 2 chambres : historique et scénarios jusqu'en 2030", yfmt='#,##0 "$"', w=17, h=9.5)
chs_.add_data(Reference(k, min_col=2, max_col=5, min_row=S0, max_row=S_LAST), titles_from_data=True)
chs_.set_categories(Reference(k, min_col=1, min_row=S_FIRST, max_row=S_LAST))
for s_, col, w_ in zip(chs_.series, [BLUE, GREY, CORAL, PINK], [38100, 22225, 22225, 22225]):
    color_series(s_, col, width=w_)
for s_ in chs_.series[1:]:
    s_.graphicalProperties.line.dashStyle = "dash"
chs_.display_blanks = "gap"
sc.add_chart(chs_, "J5")
sc.row_dimensions[10].height = sc.row_dimensions[17].height = 30
for col, w_ in zip("BCDEFGH", [10, 18, 38, 18, 16, 12, 24]):
    sc.column_dimensions[col].width = w_

# ================================================================== Simulateur
s = sheet("Simulateur", BLUE)
banner(s, "Simulateur : ton loyer face au marché montréalais", "Modifie uniquement les cellules jaunes ; tout le reste se recalcule, y compris le graphique", 9)
s.column_dimensions["A"].width = 2
s.column_dimensions["B"].width = 48
s.column_dimensions["C"].width = 22
s.column_dimensions["D"].width = 52
label(s, "B4", "Entrées")
for r, lab_, val, fmt, nt in [(5, "Loyer mensuel actuel ($)", 1250, MONEY, "Exemple : 1 250 $. Remplace par ton loyer."),
                              (6, "Type de logement", "2 chambres", "@", "Liste déroulante."),
                              (7, "Année de début du bail", 2019, "0", "Entre 1992 et 2025."),
                              (8, "Revenu annuel brut du ménage ($)", 60000, MONEY, "Mets 0 pour ne pas calculer le taux d'effort.")]:
    s[f"B{r}"] = lab_
    s[f"C{r}"] = val
    s[f"C{r}"].font, s[f"C{r}"].fill, s[f"C{r}"].border, s[f"C{r}"].number_format = INPUT_FONT, fill("FFF6C2"), BOX, fmt
    s[f"C{r}"].alignment = RIGHT
    note(s, f"D{r}", nt)
validation(s, "C6", type="list", formula1='"Studio,1 chambre,2 chambres,3 chambres"')
validation(s, "C7", type="whole", operator="between", formula1="1992", formula2="2025", error="Choisis une année entre 1992 et 2025.")
label(s, "B10", "Résultats (données d'octobre 2025)")
res = [
    (11, "Loyer moyen SCHL, ce type, 2025", "=SUMIFS(Loyers_Montant,Loyers_Annee,2025,Loyers_Type,$C$6)", MONEY),
    (12, "Écart entre ton loyer et cette moyenne", "=C5-C11", MONEY_S),
    (13, "Écart en %", "=C5/C11-1", PCT_S),
    (14, "Hausse du loyer moyen depuis le début du bail", "=C11/SUMIFS(Loyers_Montant,Loyers_Annee,$C$7,Loyers_Type,$C$6)-1", PCT_S),
    (15, "Inflation (IPC Montréal) sur la même période", "=INDEX(IPC_Valeur,MATCH(2025,IPC_Annee,0))/INDEX(IPC_Valeur,MATCH($C$7,IPC_Annee,0))-1", PCT_S),
    (16, "Hausse réelle du loyer moyen (au-delà de l'inflation)", "=(1+C14)/(1+C15)-1", PCT_S),
    (17, "Taux d'effort (loyer × 12 / revenu)", '=IF(C8>0,C5*12/C8,"Non calculé")', PCT),
    (18, "Statut d'abordabilité (seuil SCHL : 30 % du revenu)", '=_xlfn.IFS(C8<=0,"Non calculé",C5*12/C8<=0.3,"Sous le seuil",TRUE,"Au-dessus du seuil")', "@"),
    (19, "Loyer moyen d'un 2 chambres reloué en 2025 (SCHL)", '=SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"loyer_moyen_reloues_2ch")', MONEY),
    (20, "Ce que coûterait un déménagement (2 ch. reloué − ton loyer)", "=C19-C5", MONEY_S),
]
for r, lab_, f_, fmt in res:
    s[f"B{r}"] = lab_
    s[f"C{r}"] = f_
    s[f"C{r}"].number_format, s[f"C{r}"].border, s[f"C{r}"].font, s[f"C{r}"].alignment = fmt, BOX, F(10, True), RIGHT
s["C19"].comment = Comment(tr("SCHL, Rapport sur le marché locatif 2025, figure 1. Publié pour les 2 chambres seulement."), "Projet Loyers Montréal")
s.conditional_formatting.add("C18", FormulaRule(formula=[tr_formula('C18="Sous le seuil"')], fill=fill("DFF5E1"), font=F(10, True, "0A7A0A")))
s.conditional_formatting.add("C18", FormulaRule(formula=[tr_formula('C18="Au-dessus du seuil"')], fill=fill("FBE3E3"), font=F(10, True, "B42323")))
label(s, "F4", "Comparaison")
for i, (lab_, f_) in enumerate([("Ton loyer", "=C5"), ("Moyenne, tous locataires", "=C11"), ("2 ch. reloué (SCHL)", "=C19")]):
    s[f"F{5 + i}"], s[f"G{5 + i}"] = lab_, f_
    s[f"G{5 + i}"].number_format = MONEY
s.column_dimensions["F"].width, s.column_dimensions["G"].width = 24, 12
chs = BarChart()
chs.type = "bar"
style_chart(chs, "Ton loyer comparé au marché (2025)", yfmt='#,##0 "$"', legend=False, w=12.5, h=6.5)
chs.add_data(Reference(s, min_col=7, min_row=5, max_row=7), titles_from_data=False)
chs.set_categories(Reference(s, min_col=6, min_row=5, max_row=7))
color_series(chs.series[0], BLUE, line=False)
value_labels(chs.series[0])
chs.gapWidth = 60
s.add_chart(chs, "F9")
for i, t in enumerate(["• Moyenne de la région métropolitaine, immeubles de 3 logements et plus, tous âges et tous quartiers.",
                       "• La moyenne inclut les locataires de longue date : un logement à louer coûte en général plus cher.",
                       "• Le logement social et les condos loués ne sont pas couverts par l'enquête."]):
    s[f"B{22 + i}"], s[f"B{22 + i}"].font = t, F(9, color=INK3)


# ================================================================== Excel 365 : portefeuille (RECHERCHEX, LET, FILTRE, TRIER, UNIQUE)
# Seule feuille qui demande Excel 2021 ou 365. Les formules à résultat multiple sont figées sur
# un bloc de cellules (formules matricielles {…}) : le fichier s'ouvre sans réparation ; dans
# Excel 365, retirer les accolades rend la propagation automatique.
x = sheet("Excel 365", "1A6B3C")
banner(x, "Excel 365 : un portefeuille de logements lu avec les fonctions dynamiques",
       "RECHERCHEX, LET, FILTRE, TRIER, UNIQUE · cases jaunes modifiables · requiert Excel 2021 ou Microsoft 365", 11)
x.column_dimensions["A"].width = 2
for c_, w_ in zip("BCDEFGHIJK", [15, 13, 13, 11, 13, 15, 13, 20, 16, 2]):
    x.column_dimensions[c_].width = w_
canvas(x, 4, 44, 1, 11)
label(x, "B5", "Portefeuille fictif d'une agence · même liste que l'exemple du programme Python")
PORTF = [("Plateau-101", "2 chambres", 1150, 2017), ("Plateau-102", "2 chambres", 1420, 2021), ("Villeray-201", "1 chambre", 980, 2019),
         ("Villeray-202", "2 chambres", 1890, 2025), ("Rosemont-301", "Studio", 760, 2015), ("Rosemont-302", "2 chambres", 1510, 2023),
         ("HoMa-401", "1 chambre", 1245, 2024), ("HoMa-402", "3 chambres", 2150, 2024)]
header_row(x, 6, 2, ["Logement", "Type", "Loyer actuel ($)", "Début du bail", "Marché 2025 ($)", "Hausse du marché depuis le bail",
                     "Écart au marché", "Position", "Gain de relocation ($/mois)"])
x.row_dimensions[6].height = 42
R0, R1 = 7, 7 + len(PORTF) - 1
XL = lambda crit_year, typ: f"_xlfn.XLOOKUP(1,(Loyers_Annee={crit_year})*(Loyers_Type={typ}),Loyers_Montant)"
_LETN = {"debut": "start", "marche_bail": "market_at_lease", "sous": "below", "gains": "gains"}
def af(ref, f):
    """Formule matricielle traduite (chaînes entre guillemets et noms LET en anglais dans la version EN)."""
    f = tr_formula(f)
    if LANG == "en":
        for a_, b_ in _LETN.items():
            f = _re.sub(r"\b" + a_ + r"\b", b_, f)
    return ArrayFormula(ref, f)
for i, (lg, typ, loyer, bail) in enumerate(PORTF):
    r = R0 + i
    for col, v, fmt in (("B", lg, "@"), ("C", typ, "@"), ("D", loyer, MONEY), ("E", bail, "0")):
        c = x[f"{col}{r}"]
        c.value, c.font, c.fill, c.border, c.number_format, c.alignment = v, INPUT_FONT, fill("FFF6C2"), BOX, fmt, CENTER
    x[f"F{r}"] = af(f"F{r}", f"={XL(2025, f'C{r}')}")
    x[f"G{r}"] = af(f"G{r}", f"=_xlfn.LET(debut,E{r},marche_bail,{XL('debut', f'C{r}')},F{r}/marche_bail-1)")
    x[f"H{r}"] = f"=D{r}/F{r}-1"
    x[f"I{r}"] = f'=_xlfn.IFS(H{r}<-0.05,"Sous le marché",H{r}>0.05,"Au-dessus du marché",TRUE,"Dans le marché")'
    x[f"J{r}"] = f'=IF(C{r}="2 chambres",SUMIFS(T_Loyer,T_ID,{MTL_ID},T_Est,"Demandé",T_Periode,"{LAST_Q}")-D{r},"—")'
    for col, fmt in (("F", MONEY), ("G", PCT_S), ("H", PCT_S), ("I", "@"), ("J", MONEY_S)):
        c = x[f"{col}{r}"]
        c.font, c.fill, c.border, c.number_format, c.alignment = F(10), fill(WHITE), BOX, fmt, CENTER
    validation(x, f"C{r}", type="list", formula1='"' + ",".join(TYPES) + '"', error="Choisis un type dans la liste.", errorTitle="Type de logement")
    validation(x, f"E{r}", type="whole", operator="between", formula1="1992", formula2="2025", error="Année entre 1992 et 2025.", errorTitle="Début du bail")
note(x, f"B{R1 + 1}", f"Marché 2025 : loyer moyen SCHL par type (RECHERCHEX à deux critères). Gain de relocation : loyer demandé à Montréal au {LAST_Q} moins le loyer actuel, pour les 2 chambres.")

RB = R1 + 3   # bloc dynamique
label(x, f"B{RB}", "Lecture dynamique du portefeuille")
card(x, RB + 1, 2, RB + 12, 5, "1A6B3C")
merge(x, f"B{RB + 1}:E{RB + 1}", "Logements sous le marché, du plus grand écart au plus petit (TRIER + FILTRE)", F(10, True, INK))
header_row(x, RB + 2, 2, ["Logement", "Type", "Loyer actuel ($)", "Écart au marché"])
S0, S1 = RB + 3, RB + 10
x[f"B{S0}"] = af(f"B{S0}:E{S1}",
    f'=IFERROR(_xlfn._xlws.SORT(_xlfn._xlws.FILTER(CHOOSE({{1,2,3,4}},B{R0}:B{R1},C{R0}:C{R1},D{R0}:D{R1},H{R0}:H{R1}),H{R0}:H{R1}<-0.05),4,1),"")')
for r in range(S0, S1 + 1):
    for col, fmt in (("B", "@"), ("C", "@"), ("D", MONEY), ("E", PCT_S)):
        c = x[f"{col}{r}"]
        c.font, c.number_format, c.alignment, c.border = F(10), fmt, CENTER, Border(bottom=Side(style="hair", color=LINE))

card(x, RB + 1, 7, RB + 12, 10, PINK)
merge(x, f"G{RB + 1}:J{RB + 1}", "Indicateurs du portefeuille (LET + FILTRE, UNIQUE)", F(10, True, INK))
kp = [
    ("Logements sous le marché (écart < −5 %)", f"=_xlfn.LET(sous,_xlfn._xlws.FILTER(H{R0}:H{R1},H{R0}:H{R1}<-0.05),IFERROR(ROWS(sous),0))", "0"),
    ("Revenu annuel libéré si les 2 chambres sous le marché étaient reloués au prix des annonces",
     f'=_xlfn.LET(gains,_xlfn._xlws.FILTER(J{R0}:J{R1},(C{R0}:C{R1}="2 chambres")*(H{R0}:H{R1}<-0.05)),IFERROR(SUM(gains)*12,0))', MONEY),
    ("Écart moyen au marché, tout le portefeuille", f"=AVERAGE(H{R0}:H{R1})", PCT_S),
]
for i, (lab_, f_, fmt) in enumerate(kp):
    r = RB + 2 + i * 2
    merge(x, f"G{r}:I{r + 1}", lab_, F(9, color=INK2))
    x[f"J{r}"] = af(f"J{r}", f_) if "FILTER" in f_ else f_
    x.merge_cells(f"J{r}:J{r + 1}")
    x[f"J{r}"].font, x[f"J{r}"].number_format, x[f"J{r}"].alignment = F(16, True, PINK_D if i < 2 else BLUE_D), fmt, CENTER
U0 = RB + 8
header_row(x, U0, 7, ["Types présents (UNIQUE)", "Logements", "Écart moyen", ""])
x[f"G{U0 + 1}"] = af(f"G{U0 + 1}:G{U0 + 4}", f'=IFERROR(INDEX(_xlfn.UNIQUE(C{R0}:C{R1}),ROW()-{U0}),"")')
for r in range(U0 + 1, U0 + 5):
    x[f"H{r}"] = f'=IF(G{r}="","",COUNTIF(C${R0}:C${R1},G{r}))'
    x[f"I{r}"] = f'=IF(G{r}="","",AVERAGEIFS(H${R0}:H${R1},C${R0}:C${R1},G{r}))'
    for col, fmt in (("G", "@"), ("H", "0"), ("I", PCT_S)):
        x[f"{col}{r}"].font, x[f"{col}{r}"].number_format, x[f"{col}{r}"].alignment = F(10), fmt, CENTER

RF = RB + 14
label(x, f"B{RF}", "Les fonctions de cette feuille")
header_row(x, RF + 1, 2, ["Fonction", "Ce qu'elle fait ici", "", "", "", "", "", "Où"])
x.merge_cells(f"C{RF + 1}:H{RF + 1}")
FN365 = [
    ("RECHERCHEX", "Lit le loyer du marché pour un type ET une année : un seul appel, deux critères, sans colonne d'aide ni INDEX/EQUIV.", "Colonnes F et G"),
    ("LET", "Nomme les étapes d'un calcul (debut, marche_bail, sous, gains) : la formule se lit comme une phrase.", "Colonne G, indicateurs"),
    ("FILTRE + TRIER", "Extrait les logements sous le marché et les classe par écart, sans RANG ni colonnes intermédiaires.", "Bloc de gauche"),
    ("UNIQUE", "Liste les types présents dans le portefeuille ; NB.SI et MOYENNE.SI.ENS complètent par type.", "Bloc de droite"),
    ("SI.CONDITIONS", "Position du loyer face au marché en une formule lisible.", "Colonne I"),
]
for i, (fn, desc, ou) in enumerate(FN365):
    r = RF + 2 + i
    x[f"B{r}"], x[f"B{r}"].font = fn, F(10, True)
    merge(x, f"C{r}:H{r}", desc, F(10, color=INK2))
    x[f"I{r}"], x[f"I{r}"].font = ou, F(9, color=INK3)
    for col in "BCDEFGHI":
        x[f"{col}{r}"].fill = fill(WHITE)
        x[f"{col}{r}"].border = Border(bottom=Side(style="thin", color=LINE))
    x.row_dimensions[r].height = 28
note(x, f"B{RF + 8}", "Dans une version d'Excel antérieure à 2021, seule cette feuille affiche #NOM? ; toutes les autres s'ouvrent normalement.")
note(x, f"B{RF + 9}", "Les blocs à résultat multiple sont figés sur 8 lignes (formules matricielles {…}) pour s'ouvrir sans réparation ; dans Excel 365, retire les accolades : la formule se propage seule.")
x.freeze_panes = "A7"

# ================================================================== Mode d'emploi
me = sheet("Mode d'emploi", VIOLET)
banner(me, "Mode d'emploi : les fonctions du classeur, de la plus simple à la plus avancée",
       "Chaque formule est visible : clique sur une cellule pour la lire. Aucune macro, aucun code caché.", 10)
me.column_dimensions["A"].width = 2
for c_, w_ in zip("BCDEFGHIJ", [24, 16, 60, 34, 2, 2, 2, 2, 2]):
    me.column_dimensions[c_].width = w_
canvas(me, 4, 46, 1, 10)
label(me, "B5", "Les fonctions, par niveau")
FN = [
    ("Simple", "SOMME.SI.ENS", "Lit un loyer dans les tableaux sources selon plusieurs critères (année, type, trimestre…). La fonction la plus utilisée du classeur.", "Partout · ex. Tableau de bord"),
    ("Simple", "MAX.SI.ENS / MIN.SI.ENS", "Le loyer demandé le plus élevé et le plus bas parmi les 16 régions, sans trier le tableau.", "Carte villes, repères du marché"),
    ("Simple", "SI.CONDITIONS", "Le statut d'abordabilité en une seule formule lisible, au lieu de SI imbriqués.", "Simulateur"),
    ("Simple", "LIEN_HYPERTEXTE", "Les boutons de navigation entre les feuilles.", "Accueil, bandeaux"),
    ("Intermédiaire", "INDEX + EQUIV", "Retrouve une valeur par sa position : la fiche de la ville choisie, le tri des classements.", "Cartes, Tableau de bord"),
    ("Intermédiaire", "RANG + INDEX/EQUIV", "Trie les villes par hausse sans macro : RANG classe, INDEX/EQUIV reconstruit la liste triée.", "Calculs (alimente les graphiques)"),
    ("Intermédiaire", "CENTILE", "Découpe les valeurs en quintiles : les 5 classes de couleur des cartes.", "Calculs, légendes des cartes"),
    ("Intermédiaire", "CHOISIR + EQUIV", "Bascule les cartes d'un indicateur à l'autre à partir d'une liste déroulante.", "Calculs"),
    ("Avancée", "NPM (NPER)", "Le nombre d'années pour que le loyer moyen rattrape le prix des annonces, pour chaque scénario.", "Scénarios"),
    ("Avancée", "NA() dans les séries", "Un point NA() n'est pas tracé : les classes de couleur des cartes et les périodes des courbes.", "Calculs (feuille masquée)"),
    ("Avancée", "Graphique en nuage de points", "Les deux cartes : les contours projetés sont une série de lignes, chaque ville ou province une série de points.", "Carte provinces, Carte villes"),
    ("Excel 365", "RECHERCHEX à deux critères", "Le loyer du marché pour un type et une année, en un seul appel.", "Excel 365"),
    ("Excel 365", "LET", "Des étapes nommées dans la formule : lisible et plus rapide à vérifier.", "Excel 365"),
    ("Excel 365", "FILTRE + TRIER + UNIQUE", "Extraire, classer et dédoublonner un portefeuille sans colonnes intermédiaires.", "Excel 365"),
]
header_row(me, 6, 2, ["Niveau", "Fonction ou outil", "Ce qu'elle fait ici", "Où la voir"])
for i, (niv, fn, desc, ou) in enumerate(FN):
    r = 7 + i
    me[f"B{r}"] = niv
    me[f"B{r}"].font = F(9, True, {"Simple": "1A6B3C", "Intermédiaire": BLUE_D, "Avancée": PINK_D, "Excel 365": VIOLET}[niv])
    me[f"C{r}"] = fn
    me[f"C{r}"].font = F(10, True)
    me[f"D{r}"] = desc
    me[f"E{r}"] = ou
    me[f"E{r}"].font = F(9, color=INK3)
    for col in "BCDE":
        me[f"{col}{r}"].fill = fill(WHITE)
        me[f"{col}{r}"].border = Border(bottom=Side(style="thin", color=LINE))
        me[f"{col}{r}"].alignment = Alignment(vertical="center", wrap_text=True, indent=1)
    me.row_dimensions[r].height = 30
R_ME = 7 + len(FN) + 1
label(me, f"B{R_ME}", "Et les fonctions d'Excel 365 ?")
for i, t in enumerate([
    "Toutes les feuilles d'analyse n'utilisent que des fonctions disponibles depuis Excel 2019, pour s'ouvrir partout sans erreur.",
    "La feuille « Excel 365 » montre les fonctions dynamiques (RECHERCHEX, LET, FILTRE, TRIER, UNIQUE) sur un portefeuille de logements ;",
    "elle demande Excel 2021 ou Microsoft 365, et c'est la seule.",
]):
    me[f"B{R_ME + 1 + i}"], me[f"B{R_ME + 1 + i}"].font = t, F(10, color=INK2)
R_EX = R_ME + 5
label(me, f"B{R_EX}", "Trois exercices pour prendre le classeur en main")
for i, t in enumerate([
    "1.  Tableau de bord : mets la période 1992-2019, puis 2019-2025. Compare les deux rythmes annuels réels (+0,5 % contre +4,1 %).",
    "2.  Carte provinces : année 2024. Quelle province mène ? (Réponse : l'Alberta.) Repasse à 2025 : le Québec prend la tête.",
    "3.  Simulateur : entre ton propre loyer et ton année de bail, puis lis l'écart avec le marché et ton taux d'effort.",
]):
    me[f"B{R_EX + 1 + i}"], me[f"B{R_EX + 1 + i}"].font = t, F(10, color=INK2)
R_CV = R_EX + 5
label(me, f"B{R_CV}", "Conventions")
for i, t in enumerate([
    "Cases jaunes : entrées modifiables (protégées par une validation des données). Texte bleu : données sources. Vert : valeur lue ailleurs. Noir : calcul.",
    "La feuille « Calculs » (masquée : clic droit sur un onglet → Afficher) contient les séries des graphiques ; ses NA() sont volontaires.",
    "Chaque bandeau de feuille cite sa source. Les données brutes sont dans les six derniers onglets, en tableaux Excel nommés.",
]):
    me[f"B{R_CV + 1 + i}"], me[f"B{R_CV + 1 + i}"].font = t, F(10, color=INK2)

# ================================================================== Accueil
a = sheet("Accueil", PINK)
a.sheet_view.zoomScale = 90
banner(a, "À Montréal, qui paie vraiment la hausse des loyers ?", "Classeur d'analyse · Projet « Loyers à Montréal, 1992-2026 »", 14, nav=False)
a.row_dimensions[1].height = 44
a["B1"].font = F(20, True, "FFFFFF")
a.column_dimensions["A"].width = 2
for c_ in range(2, 15):
    a.column_dimensions[CL(c_)].width = 11.5
canvas(a, 4, 42, 1, 14)
merge(a, "B5:M5", "Réponse courte : ceux qui déménagent. Les quatre chiffres ci-dessous sont recalculés par les formules du classeur.",
      F(11, True, INK))
REAL = lambda y0, y1: (f'(SUMIFS(Loyers_Montant,Loyers_Annee,{y1},Loyers_Type,"2 chambres")/'
                       f'SUMIFS(Loyers_Montant,Loyers_Annee,{y0},Loyers_Type,"2 chambres"))'
                       f'/(INDEX(IPC_Valeur,MATCH({y1},IPC_Annee,0))/INDEX(IPC_Valeur,MATCH({y0},IPC_Annee,0)))-1')
kpis = [
    ("B", "D", f"Annonce moins loyer payé, {LAST_Q}",
     f'=SUMIFS(T_Loyer,T_ID,{MTL_ID},T_Est,"Demandé",T_Periode,"{LAST_Q}")-SUMIFS(T_Loyer,T_ID,{MTL_ID},T_Est,"Payé",T_Periode,"{LAST_Q}")',
     MONEY_S, PINK, "Par mois, 2 chambres à Montréal"),
    ("E", "G", "Hausse 2025 : reloués / en place",
     '=SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"hausse_loyer_reloues_2ch")/100', PCT_S, CORAL,
     '="contre "&FIXED(SUMIFS(SCHL_Valeur,SCHL_Annee,2025,SCHL_Indic,"hausse_loyer_non_reloues_2ch"),1)&" % pour les locataires en place"'),
    ("H", "J", "Hausse réelle d'un 2 ch., 2019-2025", f"={REAL(2019, 2025)}", PCT_S, BLUE,
     f'="Après inflation. De 1992 à 2019 : "&{pct_text(REAL(1992, 2019))}'),
    ("K", "M", "Loyer au Québec en 2025 (IPC)", "=QC_Hausse_2025", PCT_S, BLUE, '="Rang "&QC_Rang_2025&" sur 10 provinces"'),
]
for c1, c2, lab_, f_, fmt, acc, sub in kpis:
    card(a, 7, ord(c1) - 64, 10, ord(c2) - 64, acc)
    merge(a, f"{c1}7:{c2}7", lab_.upper(), F(8, True, INK3))
    merge(a, f"{c1}8:{c2}9", f_, F(26, True, BLUE_D if acc == BLUE else PINK_D))
    a[f"{c1}8"].number_format = fmt
    merge(a, f"{c1}10:{c2}10", sub, F(9, color=INK2))
a.row_dimensions[7].height = 20
a.row_dimensions[10].height = 18
merge(a, "B13:M13", "Explorer le classeur", F(12, True, INK))
nav_items = [
    ("Tableau de bord", "Choisis une période et un type de logement : indicateurs et graphiques se recalculent."),
    ("Carte provinces", "La carte du Canada : hausse des loyers par province, par année, avec classement."),
    ("Carte villes", f"Les {len(ids)} régions où l'on connaît le loyer demandé et le loyer payé. Choisis une ville."),
    ("Scénarios", "Trois hypothèses jusqu'en 2030 et le délai pour que le loyer moyen rattrape les annonces."),
    ("Simulateur", "Compare un loyer à la moyenne du marché et au prix d'un logement reloué."),
    ("Excel 365", "Un portefeuille de logements lu avec RECHERCHEX, LET, FILTRE, TRIER et UNIQUE (Excel 2021 ou 365)."),
    ("Mode d'emploi", "Chaque fonction du classeur, de la plus simple à la plus avancée, et trois exercices."),
]
for i, (tgt, desc) in enumerate(nav_items):
    r_ = 15 + i * 2
    merge(a, f"B{r_}:D{r_}", f'=HYPERLINK("#\'{tgt}\'!A1","{tgt}")', F(11, True, "FFFFFF"), CENTER, BLUE)
    merge(a, f"E{r_}:M{r_}", desc, F(10, color=INK2))
    a.row_dimensions[r_].height = 24
merge(a, "B30:M30", "Méthode", F(12, True, INK))
for i, t in enumerate([
    "Sources : Statistique Canada (34-10-0133-01, 18-10-0005-01, 46-10-0092-01) et SCHL, Rapport sur le marché locatif 2025.",
    f"Dernières données : enquête SCHL d'octobre 2025, loyers demandés et payés de {LAST_Q}, IPC annuel 2025.",
    "Chaque chiffre est recalculé ici par formules et vérifié contre le pipeline Python et les requêtes SQL du projet.",
    "Cases jaunes : entrées. Texte bleu : donnée source. Vert : valeur lue dans une autre feuille. Noir : calcul. Aucune macro.",
    "Classeur généré par un script Python (openpyxl) écrit avec l'aide d'un assistant d'IA ; questions, sources et vérifications par l'auteur du projet.",
]):
    merge(a, f"B{31 + i}:M{31 + i}", "• " + t, F(9, color=INK2))

# ================================================================== ordre, impression, enregistrement
wb.remove(wb["Sheet"])
ORDER = ["Accueil", "Tableau de bord", "Carte provinces", "Carte villes", "Scénarios", "Simulateur", "Excel 365", "Mode d'emploi",
         "Loyers Montréal", "Grandes villes", "IPC Montréal", "IPC provinces", "Loyers trimestriels", "SCHL", "Calculs"]
ORDER = [tr_sheetname(nm) for nm in ORDER]
assert sorted(ORDER) == sorted(wb.sheetnames), set(ORDER) ^ set(wb.sheetnames)
wb._sheets = [wb[nm] for nm in ORDER]
k.sheet_state = "hidden"
wb.active = 0
for ws_ in wb.worksheets:
    ws_.sheet_view.tabSelected = ws_.title == tr_sheetname("Accueil")
    ws_.page_setup.orientation = "landscape"
    ws_.page_setup.paperSize = ws_.PAPERSIZE_A4
    ws_.sheet_properties.pageSetUpPr.fitToPage = True
    ws_.page_setup.fitToWidth = 1
    ws_.page_setup.fitToHeight = 0
    ws_.print_options.horizontalCentered = True
    ws_.page_margins.left = ws_.page_margins.right = 0.3
for ws_, area in ((a, "A1:N36"), (me, f"A1:K{R_CV + 5}"), (x, f"A1:L{RF + 10}"), (d, "A1:N50"), (cp, "A1:P52"), (cv, "A1:P59"), (sc, "A1:U34"), (s, "A1:I25")):
    ws_.print_area = area
    ws_.page_setup.fitToHeight = 1
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
n_f = sum(1 for ws_ in wb.worksheets for row in ws_.iter_rows() for c in row if (isinstance(c.value, str) and c.value.startswith("=")) or isinstance(c.value, ArrayFormula))
print(f"enregistré : {OUT.relative_to(ROOT)} · {len(wb.worksheets)} feuilles · {n_f} formules · {len(ids)} régions · trimestres {QS[0]} à {QS[-1]}")
