"""
Cartes géographiques du projet (docs/assets/maps/*.png), dessinées en Python à partir des contours Natural Earth.

- provinces_<indicateur>.png : carte choroplèthe des 10 provinces (IPC du loyer)
- provinces_annuel.png       : six petites cartes, hausse annuelle 2020 à 2025 sur une échelle commune
- villes.png                 : les régions métropolitaines où loyer demandé et loyer payé sont publiés

Projection conique conforme de Lambert (paramètres de Statistique Canada), palette du projet.
Les mêmes images sont insérées dans le classeur Excel et affichées sur le site.
Exécution : python src/maps.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Polygon
import numpy as np

import geo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "maps"
OUT.mkdir(parents=True, exist_ok=True)
CARTE = json.loads((ROOT / "docs" / "data" / "carte.json").read_text(encoding="utf-8"))

plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
SKY, PINK, NAVY, INK, GREY, NA = "#0593C6", "#D83995", "#04557A", "#0F1B26", "#A5B3C1", "#E3E8EC"
CMAP = LinearSegmentedColormap.from_list("sky", ["#E0F2FA", "#7CC6E5", "#0593C6", "#04557A"])
LABELS = {"BC": (-124.5, 54.6), "AB": (-115.2, 55.2), "SK": (-107.5, 56.0), "MB": (-96.0, 54.0), "ON": (-86.0, 50.2),
          "QC": (-72.5, 52.5), "NL": (-62.5, 53.6), "NB": (-66.4, 46.6), "NS": (-62.8, 45.0), "PE": (-63.2, 46.4)}
OFFSET = {"NB": (-4.5, -4.0), "NS": (5.0, -3.2), "PE": (5.5, 2.0)}   # étiquettes des Maritimes repoussées en mer
RINGS = geo.load_rings()
PROV = {p["code"]: p for p in CARTE["provinces"]}


def draw_provinces(ax, values, vmin, vmax, labels=True, label_fmt="{:+.1f} %", highlight=None, fontsize=8):
    norm = Normalize(vmin, vmax)
    for code, ring in RINGS:
        v = values.get(code)
        if code == highlight:
            fc = PINK
        elif v is None:
            fc = NA
        else:
            fc = CMAP(norm(v))
        ax.add_patch(Polygon(ring, closed=True, facecolor=fc, edgecolor="white", linewidth=0.45, zorder=2))
    if labels:
        for code, (lon, lat) in LABELS.items():
            if code not in values:
                continue
            x, y = geo.proj(lon, lat)
            dx, dy = OFFSET.get(code, (0, 0))
            x2, y2 = x + dx / 100, y + dy / 100
            if (dx, dy) != (0, 0):
                ax.plot([x, x2], [y, y2], color=INK, linewidth=0.6, zorder=3)
            ax.text(x2, y2, f"{code} {label_fmt.format(values[code])}", ha="center", va="center", fontsize=fontsize, color=INK,
                    fontweight="bold", zorder=4, bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.9))
    ax.set_xlim(-0.62, 0.52)
    ax.set_ylim(-0.39, 0.24)
    ax.set_aspect("equal")
    ax.axis("off")


def colorbar(fig, ax, vmin, vmax, label):
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=Normalize(vmin, vmax))
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.01, aspect=35, shrink=0.55)
    cb.set_label(label, fontsize=8, color=INK)
    cb.ax.tick_params(labelsize=7, colors=INK, length=2)
    cb.outline.set_visible(False)
    cb.ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.1f} %")


def province_map(key, title, subtitle, fname, highlight="QC"):
    vals = {c: p[key] for c, p in PROV.items() if c != "CA"}
    vmin, vmax = min(vals.values()), max(vals.values())
    fig, ax = plt.subplots(figsize=(8.6, 5.9), dpi=180)
    fig.patch.set_alpha(0)
    draw_provinces(ax, vals, vmin, vmax, highlight=highlight)
    ax.set_title(title + "\n", loc="left", fontsize=12, fontweight="bold", color=INK, pad=2)
    ax.text(0, 1.01, subtitle, transform=ax.transAxes, fontsize=8.5, color="#44546A", va="bottom")
    colorbar(fig, ax, vmin, vmax, "IPC du loyer · province en rose : Québec")
    ax.text(0.99, 0.0, "Contours : Natural Earth · Projection conique conforme de Lambert · Statistique Canada 18-10-0005-01",
            transform=ax.transAxes, fontsize=6, color="#607286", ha="right", va="bottom")
    fig.savefig(OUT / fname, bbox_inches="tight", pad_inches=0.1, transparent=True)
    plt.close(fig)


def annual_small_multiples():
    years = list(range(2020, 2026))
    annual = {y: {c: round((p["serie_loyer"][y - 2019] / p["serie_loyer"][y - 2020] - 1) * 100, 1) for c, p in PROV.items() if c != "CA"}
              for y in years}
    allv = [v for d in annual.values() for v in d.values()]
    vmin, vmax = min(allv), max(allv)
    fig, axes = plt.subplots(2, 3, figsize=(12.6, 5.6), dpi=170)
    fig.patch.set_alpha(0)
    fig.subplots_adjust(hspace=0.02, wspace=0.02, top=0.9, bottom=0.08)
    for ax, y in zip(axes.ravel(), years):
        d = annual[y]
        top = max(d, key=d.get)
        draw_provinces(ax, d, vmin, vmax, labels=False)
        for code, (lon, lat) in LABELS.items():
            x, y_ = geo.proj(lon, lat)
            dx, dy = OFFSET.get(code, (0, 0))
            ax.text(x + dx / 100, y_ + dy / 100, code, ha="center", va="center", fontsize=5.5, color=INK, zorder=4)
        ax.set_title(f"{y} · en tête : {PROV[top]['nom']} ({d[top]:+.1f} %)", loc="left", fontsize=9, fontweight="bold", color=INK, pad=2)
    fig.suptitle("Hausse annuelle de l'IPC du loyer, par province, 2020 à 2025 (échelle commune)", x=0.01, ha="left", fontsize=12,
                 fontweight="bold", color=INK)
    colorbar(fig, axes.ravel().tolist(), vmin, vmax, "Hausse sur un an")
    fig.savefig(OUT / "provinces_annuel.png", bbox_inches="tight", pad_inches=0.1, transparent=True)
    plt.close(fig)
    return annual


def city_map():
    villes = [v for v in CARTE["villes"] if v.get("paye") and v.get("demande")]
    vals = [v["ecart_pct"] for v in villes]
    vmin, vmax = min(vals), max(vals)
    norm = Normalize(vmin, vmax)
    fig, (ax_w, ax_e) = plt.subplots(1, 2, figsize=(13, 5.6), dpi=170, gridspec_kw={"width_ratios": [1, 1.2]})
    fig.patch.set_alpha(0)
    boxes = {ax_w: (-125.6, 48.0, -95.6, 57.5), ax_e: (-84.2, 41.8, -59.6, 50.6)}
    XY = {7: (9, 9), 8: (-9, -14), 11: (9, -13), 27: (9, 4), 20: (-9, 9), 21: (-9, -12), 9: (9, 7), 16: (-9, 9), 19: (9, -4)}
    HA = {8: "right", 20: "right", 21: "right", 16: "right"}
    for ax, bb in boxes.items():
        for code, ring in RINGS:
            ax.add_patch(Polygon(ring, closed=True, facecolor="#EEF5F9", edgecolor="#B9C7D1", linewidth=0.5, zorder=1))
        corners = np.array(geo.proj([bb[0], bb[2], bb[0], bb[2], (bb[0] + bb[2]) / 2, (bb[0] + bb[2]) / 2],
                                    [bb[1], bb[1], bb[3], bb[3], bb[1], bb[3]])).T
        ax.set_xlim(corners[:, 0].min(), corners[:, 0].max())
        ax.set_ylim(corners[:, 1].min(), corners[:, 1].max())
        ax.set_aspect("equal")
        ax.axis("off")
        for v in sorted(villes, key=lambda z: z["ecart_pct"]):
            x, y = geo.proj(v["lon"], v["lat"])
            if not (ax.get_xlim()[0] < x < ax.get_xlim()[1] and ax.get_ylim()[0] < y < ax.get_ylim()[1]):
                continue
            mtl = v["id"] == 7
            ax.scatter([x], [y], s=60 + 10 * (v["ecart_pct"] - vmin), color=PINK if mtl else CMAP(norm(v["ecart_pct"])),
                       edgecolor="white", linewidth=1.2, zorder=3)
            short = v["nom"].split(" (")[0].replace(" - Cambridge - Waterloo", "")
            ax.annotate(f"{short}  {v['ecart_pct']:+.0f} %", (x, y), xytext=XY.get(v["id"], (8, 4)), textcoords="offset points", fontsize=7.5,
                        ha=HA.get(v["id"], "left"), color=PINK if mtl else INK, fontweight="bold" if mtl else "normal", zorder=4,
                        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85))
    ax_w.set_title("Ouest", loc="left", fontsize=10, fontweight="bold", color=INK)
    ax_e.set_title("Est", loc="left", fontsize=10, fontweight="bold", color=INK)
    last = CARTE["periodes"][-1]
    fig.suptitle(f"Loyer demandé par rapport au loyer payé, appartements de 2 chambres, {last} · {len(villes)} régions où les deux sont publiés",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
    cb = fig.colorbar(sm, ax=[ax_w, ax_e], orientation="horizontal", fraction=0.03, pad=0.02, aspect=40, shrink=0.45)
    cb.set_label("Écart demandé / payé · Montréal en rose", fontsize=8, color=INK)
    cb.ax.tick_params(labelsize=7, colors=INK, length=2)
    cb.outline.set_visible(False)
    cb.ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f} %")
    fig.savefig(OUT / "villes.png", bbox_inches="tight", pad_inches=0.1, transparent=True)
    plt.close(fig)
    return villes


if __name__ == "__main__":
    for f in OUT.glob("*.png"):
        f.unlink()
    province_map("hausse_loyer_2025", "Hausse des loyers en 2025, par province", "Indice des prix du loyer, 2025 contre 2024 · le Québec est premier",
                 "provinces_2025.png")
    province_map("hausse_loyer", "Hausse des loyers de 2019 à 2025, par province", "Indice des prix du loyer, 2025 contre 2019 · le Québec est 4e",
                 "provinces_2019_2025.png")
    province_map("hausse_reelle", "Hausse réelle des loyers de 2019 à 2025, par province",
                 "IPC du loyer rapporté à l'IPC d'ensemble · ce que les loyers ont gagné sur l'inflation", "provinces_reelle.png")
    annual_small_multiples()
    v = city_map()
    print("cartes :", ", ".join(sorted(p.name for p in OUT.glob("*.png"))), f"· {len(v)} régions sur la carte des villes")
