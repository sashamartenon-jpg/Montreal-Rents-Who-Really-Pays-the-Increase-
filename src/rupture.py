"""
Les données confirment-elles une rupture de tendance en 2019, ou est-ce moi qui la vois ?

1. Test de Chow : une droite unique sur 1992-2025 contre deux droites séparées à l'année c.
2. Recherche de la rupture : le test est calculé pour chaque année candidate de 1997 à 2021 ;
   les données désignent elles-mêmes l'année où la cassure est la plus nette.
3. p-value honnête : chercher la meilleure année gonfle la significativité, et les loyers d'une année
   à l'autre sont autocorrélés. La p-value est donc recalculée par simulation (Monte Carlo) : on simule
   des milliers de séries SANS rupture, avec la même tendance et des résidus AR(1) estimés sur les données,
   et on compte combien produisent un F maximal au moins aussi grand que celui observé.
"""
import numpy as np
from scipy import stats as st

CANDIDATES = np.arange(1997, 2022)   # au moins 5 ans de chaque côté


def _rss(t, Y):
    """Somme des carrés des résidus d'une régression linéaire, pour chaque ligne de Y (vectorisé)."""
    X = np.c_[np.ones_like(t), t - t.mean()]
    beta, *_ = np.linalg.lstsq(X, Y.T, rcond=None)
    return ((Y.T - X @ beta) ** 2).sum(axis=0)


def chow_f(t, Y, c):
    """Statistique F de Chow pour une rupture à l'année c (k = 2 paramètres : constante et pente)."""
    Y = np.atleast_2d(Y)
    n, k = len(t), 2
    before = t < c
    r_one = _rss(t, Y)
    r_two = _rss(t[before], Y[:, before]) + _rss(t[~before], Y[:, ~before])
    return ((r_one - r_two) / k) / (r_two / (n - 2 * k))


def analyse(t, y, n_sim=20000, seed=42):
    t, y = np.asarray(t, float), np.asarray(y, float)
    n = len(t)
    f_by_year = np.array([chow_f(t, y, c)[0] for c in CANDIDATES])
    best = int(CANDIDATES[f_by_year.argmax()])
    f_2019 = float(f_by_year[list(CANDIDATES).index(2019)])
    p_naive = float(st.f.sf(f_2019, 2, n - 4))

    # Hypothèse nulle : une seule tendance, résidus AR(1) (rho estimé sur les résidus, donc prudent)
    slope, intercept = np.polyfit(t, y, 1)
    e = y - (slope * t + intercept)
    rho = float(np.corrcoef(e[:-1], e[1:])[0, 1])
    sigma = float(np.std(e[1:] - rho * e[:-1], ddof=1))
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, sigma, (n_sim, n))
    u = np.empty_like(eps)
    u[:, 0] = eps[:, 0] / np.sqrt(1 - rho ** 2)
    for i in range(1, n):
        u[:, i] = rho * u[:, i - 1] + eps[:, i]
    sims = slope * t + intercept + u
    sup_f = np.max([chow_f(t, sims, c) for c in CANDIDATES], axis=0)
    p_sim = float((sup_f >= f_by_year.max()).mean())
    return {"f_par_annee": dict(zip(CANDIDATES.tolist(), np.round(f_by_year, 1).tolist())),
            "rupture_estimee": best, "f_2019": round(f_2019, 1), "p_naive": p_naive,
            "p_simulee": round(p_sim, 3), "rho": round(rho, 2), "n_sim": n_sim,
            "seuil_5pct_simule": round(float(np.percentile(sup_f, 95)), 1)}
