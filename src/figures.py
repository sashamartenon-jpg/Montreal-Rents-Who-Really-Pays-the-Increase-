"""
Analyses statistiques et figures (matplotlib) pour la page « Python » du site.

1. Rupture de tendance en 2019 : régression linéaire du loyer réel avant et après 2019.
2. Décomposition de la hausse de 2025 : logements constants (SCHL) + effet de composition.
3. Loyer demandé contre loyer payé dans les régions métropolitaines (dernier trimestre).
4. Inoccupation et hausse des loyers : corrélation, avec et sans 2025.

Sorties : docs/assets/python/*.png et stats.json  ·  Exécution : python src/figures.py (après pipeline.py)
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rupture
from matplotlib.ticker import FuncFormatter

import os
ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "docs" / "assets" / "python"
OUT.mkdir(parents=True, exist_ok=True)
LANG = os.environ.get("FIG_LANG", "fr")
SUF = "" if LANG == "fr" else "_en"
L = lambda f, e: f if LANG == "fr" else e
for old in OUT.glob("*.png"):   # on ne supprime que les captures de la langue en cours
    is_en = old.stem.endswith("_en")
    if (LANG == "en") == is_en:
        old.unlink()

SKY, PINK, PINK_INK, GREY, INK, INK3 = "#2f86d6", "#e0457b", "#b8285e", "#a9b6c6", "#13233a", "#5b6b82"
CORAL = "#f2876b"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#d6e2ea", "axes.labelcolor": INK3,
    "xtick.color": INK3, "ytick.color": INK3, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6eef3", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.facecolor": "#ffffff", "axes.facecolor": "#ffffff",
})
fr = (lambda x, d=1: f"{x:.{d}f}".replace(".", ",")) if LANG == "fr" else (lambda x, d=1: f"{x:.{d}f}")
dollars = FuncFormatter((lambda v, _: f"{v:,.0f} $".replace(",", " ")) if LANG == "fr" else (lambda v, _: f"${v:,.0f}"))

rents = pd.read_csv(CLEAN / "fait_loyers_montreal.csv")
vac = pd.read_csv(CLEAN / "fait_inoccupation.csv")
schl = pd.read_csv(CLEAN / "schl_roulement.csv").set_index(["indicateur", "year"]).valeur
trim = pd.read_csv(CLEAN / "fait_loyer_trimestriel.csv")
rmr = pd.read_csv(CLEAN / "dim_rmr.csv")
two = rents[rents.unit_id == "2ch"].set_index("year")
stats = {}

# 1. Rupture de tendance : deux régressions linéaires sur le loyer réel -------------------------
real = two.loyer_reel_2025
pre, post = real.loc[1992:2019], real.loc[2019:2025]
b_pre, a_pre = np.polyfit(pre.index, pre.values, 1)
b_post, a_post = np.polyfit(post.index, post.values, 1)
r2 = lambda s, b, a: 1 - float(((s.values - (b * s.index.values + a)) ** 2).sum()) / float(((s.values - s.values.mean()) ** 2).sum())
stats.update(pente_avant=round(b_pre, 1), pente_apres=round(b_post, 1), ratio_pentes=round(b_post / b_pre, 1),
             r2_avant=round(r2(pre, b_pre, a_pre), 2), r2_apres=round(r2(post, b_post, a_post), 2))
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.axvspan(2019, 2025.4, color=PINK, alpha=0.08, lw=0)
ax.plot(real.index, real.values, color=SKY, lw=2.4, zorder=3)
for s_, b_, a_, col, pos, ha in [(pre, b_pre, a_pre, INK3, (2004, 1095), "center"), (post, b_post, a_post, PINK_INK, (2018.6, 1290), "right")]:
    x = np.array([s_.index.min(), s_.index.max()])
    ax.plot(x, b_ * x + a_, ls="--", lw=1.4, color=col, zorder=2)
    lab_pente = f"{'+' if b_ > 0 else ''}{fr(b_, 1)} $ par an" if LANG == "fr" else f"{'+' if b_ > 0 else ''}${fr(b_, 1)} per year"
    ax.annotate(f"{lab_pente}\n{s_.index.min()}-{s_.index.max()}", xy=pos, ha=ha,
                color=col, fontsize=10.5, fontweight="bold")
ax.yaxis.set_major_formatter(dollars)
ax.set_ylim(800, 1420)
ax.set_title(L("Loyer réel d'un 2 chambres à Montréal (dollars de 2025) et tendance linéaire par période",
              "Real two-bedroom rent in Montreal (2025 dollars) and linear trend by period"), loc="left", fontsize=11, color=INK)
fig.savefig(OUT / f"rupture_2019{SUF}.png")
plt.close(fig)

# 1 bis. La rupture est-elle réelle ? Test de Chow, recherche de l'année, p-value simulée --------
rup = rupture.analyse(real.index.values, real.values)
stats.update(chow_f_2019=rup["f_2019"], chow_p_naive=rup["p_naive"], chow_p_simulee=rup["p_simulee"],
             chow_rupture=rup["rupture_estimee"], chow_rho=rup["rho"], chow_n_sim=rup["n_sim"], chow_seuil=rup["seuil_5pct_simule"],
             chow_f_par_annee=rup["f_par_annee"])
fig, ax = plt.subplots(figsize=(8, 3.4))
yrs, fs = list(rup["f_par_annee"]), list(rup["f_par_annee"].values())
ax.bar(yrs, fs, color=[PINK if y_ == rup["rupture_estimee"] else "#b9d7f2" for y_ in yrs], width=0.75, zorder=3)
ax.axhline(rup["seuil_5pct_simule"], color=INK3, lw=1.2, ls="--", zorder=4)
ax.annotate(L(f"seuil à 5 % (simulé, résidus autocorrélés) : F = {fr(rup['seuil_5pct_simule'], 1)}",
            f"5% threshold (simulated, autocorrelated residuals): F = {fr(rup['seuil_5pct_simule'], 1)}"), xy=(1997, rup["seuil_5pct_simule"] + 1.2),
            color=INK3, fontsize=9)
ax.annotate(f"{rup['rupture_estimee']} : F = {fr(rup['f_2019'], 1)}", xy=(rup["rupture_estimee"], max(fs) + 1), ha="center", color=PINK_INK,
            fontsize=10, fontweight="bold")
ax.set_ylim(0, max(fs) * 1.18)
ax.set_title(L("Test de Chow pour chaque année de rupture possible (loyer réel, 2 chambres)",
              "Chow test for each candidate break year (real rent, two-bedroom)"), loc="left", fontsize=11, color=INK)
ax.set_ylabel(L("Statistique F", "F statistic"))
fig.savefig(OUT / f"test_chow{SUF}.png")
plt.close(fig)

# 2. Décomposition de la hausse de 2025 ---------------------------------------------------------
brute = float(two.var_annuelle_pct[2025])
meme = float(schl["hausse_loyer_meme_echantillon_2ch", 2025])
compo = round(brute - meme, 1)
stats.update(hausse_brute_2025=brute, hausse_meme_echantillon_2025=meme, effet_composition_2025=compo,
             part_composition=round(compo / brute * 100))
fig, ax = plt.subplots(figsize=(6.6, 3.4))
labels = [L("Mêmes logements\n(SCHL)", "Same units\n(CMHC)"), L("Composition du parc\n(déduite)", "Housing mix\n(inferred)"), L("Moyenne brute\n(StatCan)", "Raw average\n(StatCan)")]
bottoms, heights, colors = [0, meme, 0], [meme, compo, brute], [SKY, PINK, INK]
ax.bar(labels, heights, bottom=bottoms, color=colors, width=0.55, zorder=3)
for i, (b_, h_) in enumerate(zip(bottoms, heights)):
    pc = " %" if LANG == "fr" else "%"
    ax.text(i, b_ + h_ + 0.3, f"+{fr(h_)} pts" if i == 1 else f"+{fr(h_)}{pc}", ha="center", fontsize=10.5, fontweight="bold",
            color=PINK_INK if i == 1 else INK)
ax.plot([0.275, 0.725], [meme, meme], color=INK3, lw=0.8, ls=":")
ax.plot([1.275, 1.725], [brute, brute], color=INK3, lw=0.8, ls=":")
ax.set_ylim(0, 17)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %" if LANG == "fr" else f"{v:.0f}%"))
ax.set_title(L("Hausse du loyer moyen d'un 2 chambres en 2025, Montréal",
              "Increase in the average two-bedroom rent in 2025, Montreal"), loc="left", fontsize=11, color=INK)
fig.savefig(OUT / f"decomposition_2025{SUF}.png")
plt.close(fig)

# 3. Loyer demandé contre loyer payé ------------------------------------------------------------
last = trim.periode.max()
t = trim[(trim.periode == last)].pivot_table(index="geo_id", columns="estimation", values="loyer").dropna()
t = t.join(rmr.set_index("geo_id")[["nom"]])
above = int((t.A > t.P).sum())
stats.update(n_rmr_paye=len(t), n_demande_superieur=above, periode=last)
fig, ax = plt.subplots(figsize=(6.4, 4.2))
lim = [800, 3200]
ax.plot(lim, lim, color=GREY, lw=1, ls="--", zorder=1)
ax.text(2350, 2240, L("demandé = payé", "asking = paid"), color=INK3, fontsize=8.5, rotation=38, ha="center", va="top")
mtl = t.index == 7
ax.scatter(t.P[~mtl], t.A[~mtl], s=40, color=SKY, edgecolor="white", linewidth=0.8, zorder=3)
ax.scatter(t.P[mtl], t.A[mtl], s=80, color=PINK, edgecolor="white", linewidth=1, zorder=4)
short = lambda n: n.split(" (")[0].replace(" - Cambridge - Waterloo", "")
for gid, r_ in t.iterrows():
    if gid in (7, 27, 41, 2, 32, 30, 16, 9, 11):
        ax.annotate(short(r_.nom), (r_.P, r_.A), xytext=(6, -3 if gid != 16 else 5), textcoords="offset points", fontsize=8.5,
                    color=PINK_INK if gid == 7 else INK3, fontweight="bold" if gid == 7 else "normal")
ax.xaxis.set_major_formatter(dollars); ax.yaxis.set_major_formatter(dollars)
ax.set_xlim(800, 2850); ax.set_ylim(1100, 3200)
ax.set_xlabel(L("Loyer payé par les locataires en place", "Rent paid by sitting tenants")); ax.set_ylabel(L("Loyer demandé dans les annonces", "Asking rent in listings"))
q = {"01": "T1", "04": "T2", "07": "T3", "10": "T4"}[last[5:]]
ax.set_title(L(f"Appartements de 2 chambres, {last[:4]} {q} ({len(t)} régions)",
              f"Two-bedroom apartments, Q{q[1]} {last[:4]} ({len(t)} metro areas)"), loc="left", fontsize=11, color=INK)
fig.savefig(OUT / f"demande_vs_paye{SUF}.png")
plt.close(fig)

# 4. Inoccupation et hausse de loyer ------------------------------------------------------------
m = (vac[vac.geo_id == "Montreal"].set_index("year").taux_inoccupation_pct.rename("inocc")
     .to_frame().join(two.var_annuelle_pct.rename("hausse")).dropna())
r = m.inocc.corr(m.hausse)
slope, intercept = np.polyfit(m.inocc, m.hausse, 1)
r_wo = m.drop(2025).inocc.corr(m.drop(2025).hausse)
stats.update(correlation=round(r, 2), correlation_sans_2025=round(r_wo, 2), n=len(m), pente=round(slope, 2))
fig, ax = plt.subplots(figsize=(6.4, 4))
ax.scatter(m.inocc, m.hausse, s=36, color=SKY, alpha=0.9, edgecolor="white", linewidth=0.8, zorder=3)
xs = np.linspace(m.inocc.min(), m.inocc.max(), 50)
ax.plot(xs, slope * xs + intercept, color=GREY, lw=1.5, zorder=2)
for y in (2001, 2016, 2022, 2025):
    ax.annotate(str(y), (m.inocc[y], m.hausse[y]), xytext=(6, 4), textcoords="offset points",
                fontsize=9, color=PINK_INK if y == 2025 else INK3, fontweight="bold" if y == 2025 else "normal")
ax.scatter([m.inocc[2025]], [m.hausse[2025]], s=64, color=PINK, zorder=4, edgecolor="white")
ax.set_xlabel(L("Taux d'inoccupation (%)", "Vacancy rate (%)"))
ax.set_ylabel(L("Hausse annuelle du loyer (%)", "Annual rent increase (%)"))
ax.set_title(L(f"Inoccupation et hausse de loyer, 1998-2025 (r = {fr(r, 2)})",
              f"Vacancy and rent increases, 1998-2025 (r = {fr(r, 2)})"), loc="left", fontsize=11, color=INK)
fig.savefig(OUT / f"inoccupation_hausse{SUF}.png")
plt.close(fig)

stats = {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in stats.items()}
stats["chow_f_par_annee"] = {str(k_): v_ for k_, v_ in stats["chow_f_par_annee"].items()}
(OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")
print(stats)
