"""
Outils géographiques du projet : projection conique conforme de Lambert (paramètres de Statistique Canada),
fonds de carte et cartes de référence (matplotlib) pour le classeur Excel et le site.
"""
from pathlib import Path
import json
import numpy as np
from matplotlib.path import Path as MPath

ROOT = Path(__file__).resolve().parents[1]
GEOJSON = ROOT / "data" / "ref" / "canada_provinces.geojson"

# Lambert conique conforme, parallèles 49° et 77°, méridien central -91,87° (projection de Statistique Canada)
_P1, _P2, _P0, _L0 = np.radians([49.0, 77.0, 63.390675, -91.866667])
_N = np.log(np.cos(_P1) / np.cos(_P2)) / np.log(np.tan(np.pi / 4 + _P2 / 2) / np.tan(np.pi / 4 + _P1 / 2))
_F = np.cos(_P1) * np.tan(np.pi / 4 + _P1 / 2) ** _N / _N
_RHO0 = _F / np.tan(np.pi / 4 + _P0 / 2) ** _N


def proj(lon, lat):
    lon, lat = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    rho = _F / np.tan(np.pi / 4 + lat / 2) ** _N
    return rho * np.sin(_N * (lon - _L0)), _RHO0 - rho * np.cos(_N * (lon - _L0))


def load_rings():
    """Anneaux extérieurs projetés : liste de (code province, tableau N×2)."""
    g = json.loads(GEOJSON.read_text(encoding="utf-8"))
    rings = []
    for f in g["features"]:
        for poly in f["geometry"]["coordinates"]:
            r = np.asarray(poly[0])
            x, y = proj(r[:, 0], r[:, 1])
            rings.append((f["properties"]["code"], np.c_[x, y]))
    return rings


def _rdp(pts, eps):
    """Simplification de Ramer-Douglas-Peucker (version itérative)."""
    n = len(pts)
    if n < 3:
        return pts
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i0, i1 = stack.pop()
        if i1 - i0 < 2:
            continue
        a, b = pts[i0], pts[i1]
        seg = pts[i0 + 1:i1]
        ab = b - a
        nrm = np.hypot(*ab)
        d = (np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / nrm) if nrm else np.hypot(*(seg - a).T)
        k = int(np.argmax(d))
        if d[k] > eps:
            m = i0 + 1 + k
            keep[m] = True
            stack += [(i0, m), (m, i1)]
    return pts[keep]


def outlines(bbox, eps):
    """Contours simplifiés des anneaux qui touchent la zone bbox = (lon0, lat0, lon1, lat1)."""
    lon0, lat0, lon1, lat1 = bbox
    corners = np.array(proj([lon0, lon1, lon0, lon1, (lon0 + lon1) / 2, (lon0 + lon1) / 2],
                            [lat0, lat0, lat1, lat1, lat0, lat1])).T
    bx0, by0 = corners.min(0)
    bx1, by1 = corners.max(0)
    out = []
    for code, ring in load_rings():
        rx0, ry0 = ring.min(0)
        rx1, ry1 = ring.max(0)
        if rx1 < bx0 or rx0 > bx1 or ry1 < by0 or ry0 > by1:
            continue
        s = _rdp(ring, eps)
        if len(s) >= 4:
            out.append((code, s))
    return out, (bx0, by0, bx1, by1)


# ---------------------------------------------------------------- rendus matplotlib (fonds de carte et cartes de référence)
def _patches(ax, bbox_proj=None, fill="#cfe6ec", edge="#ffffff", lw=0.6, colors=None, zorder=1):
    from matplotlib.patches import Polygon
    for code, ring in load_rings():
        if bbox_proj is not None:
            rx0, ry0 = ring.min(0)
            rx1, ry1 = ring.max(0)
            if rx1 < bbox_proj[0] or rx0 > bbox_proj[2] or ry1 < bbox_proj[1] or ry0 > bbox_proj[3]:
                continue
        fc = (colors or {}).get(code, fill)
        ax.add_patch(Polygon(ring, closed=True, facecolor=fc, edgecolor=edge, linewidth=lw, zorder=zorder))


def basemap(bbox, out, width_px=1400, fill="#cfe6ec", edge="#ffffff", background="none"):
    """Fond de carte rogné exactement sur bbox (lon0, lat0, lon1, lat1) : sert de fond à un graphique Excel en nuage de points.
    Renvoie la boîte projetée (bx0, by0, bx1, by1) et la taille de l'image en pixels."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _, (bx0, by0, bx1, by1) = outlines(bbox, 1e9)  # même boîte projetée que les contours
    ratio = (by1 - by0) / (bx1 - bx0)
    w_in = width_px / 100
    fig = plt.figure(figsize=(w_in, w_in * ratio), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(bx0, bx1)
    ax.set_ylim(by0, by1)
    ax.axis("off")
    _patches(ax, (bx0, by0, bx1, by1), fill=fill, edge=edge)
    fig.savefig(out, dpi=100, transparent=(background == "none"), facecolor=background if background != "none" else "none")
    plt.close(fig)
    return (bx0, by0, bx1, by1), (width_px, int(round(width_px * ratio)))


def choropleth(values, out, title, subtitle, labels, fmt=lambda v: f"{v:+.1f} %", width_px=1600, na=("YT", "NT", "NU"),
               ramp=("#dff1f6", "#9fd3e0", "#4fb0c8", "#1d7f9b", "#0b4f66"), selected=None, sel_color="#d83995"):
    """Carte choroplèthe des provinces (valeurs = {code: nombre}) : image de référence intégrée au classeur et au site."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    from matplotlib.cm import ScalarMappable
    bbox = (-141.5, 41.5, -52.3, 70.5)
    _, (bx0, by0, bx1, by1) = outlines(bbox, 1e9)
    by1 = by0 + (by1 - by0) * 0.92  # moins d'Arctique
    cmap = LinearSegmentedColormap.from_list("teal", ramp)
    vals = [v for k, v in values.items() if k not in na]
    norm = Normalize(min(vals), max(vals))
    colors = {k: ("#e3e8ec" if k in na else cmap(norm(v))) for k, v in values.items()}
    for k in na:
        colors[k] = "#e3e8ec"
    if selected:
        colors[selected] = sel_color
    ratio = (by1 - by0) / (bx1 - bx0)
    fig = plt.figure(figsize=(width_px / 100, width_px / 100 * ratio + 1.3), dpi=100)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.84])
    ax.set_xlim(bx0, bx1)
    ax.set_ylim(by0, by1)
    ax.axis("off")
    _patches(ax, None, colors=colors, edge="#ffffff", lw=0.8)
    for code, pos in labels.items():
        (lon, lat), target = (pos[0], pos[1]) if isinstance(pos[0], tuple) else (pos, None)
        x, y = proj(lon, lat)
        dark = target is None and (code == selected or (code not in na and norm(values[code]) > 0.6))
        kw = dict(ha="center", va="center", fontsize=10.5, fontweight="bold", color="#ffffff" if dark else "#0f1b26", zorder=5,
                  bbox=dict(boxstyle="round,pad=0.25", fc=(0, 0, 0, 0.18) if dark else (1, 1, 1, 0.85), ec="none"))
        if target is None:
            ax.text(x, y, f"{code}\n{fmt(values[code])}", **kw)
        else:
            tx, ty = proj(*target)
            ax.annotate(f"{code}\n{fmt(values[code])}", xy=(tx, ty), xytext=(x, y), arrowprops=dict(arrowstyle="-", color="#607286", lw=0.8), **kw)
    fig.text(0.02, 0.955, title, fontsize=17, fontweight="bold", color="#0f1b26", va="top")
    fig.text(0.02, 0.905, subtitle, fontsize=10.5, color="#607286", va="top")
    cax = fig.add_axes([0.70, 0.90, 0.27, 0.025])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.ax.tick_params(labelsize=8.5, colors="#44546a", length=2)
    cb.outline.set_visible(False)
    cb.set_ticks([min(vals), max(vals)])
    cb.set_ticklabels([fmt(min(vals)), fmt(max(vals))])
    fig.savefig(out, dpi=100, facecolor="#ffffff")
    plt.close(fig)
    return out
