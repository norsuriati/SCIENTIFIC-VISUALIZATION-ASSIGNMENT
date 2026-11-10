"""Data preparation and calculations for the Malaysia Cost of Living dashboard."""
import json
import math
import re
from pathlib import Path

import pandas as pd

OVERALL = "Overall"


# ------------------------------------------------------------------ data
def load_data(path=None):
    if path is None:
        path = Path(__file__).parent / "data" / "merged_dataset.csv"
    df = pd.read_csv(path)
    required = {"state", "year", "population", "income_mean", "income_median", "division", "index"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    for col in ["year", "population", "income_mean", "income_median", "index"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["state", "year", "division", "index"])
    df["year"] = df["year"].astype(int)
    return df


def state_year(df):
    """Return one record per state/year with population, income and overall CPI."""
    core = (df.sort_values("division")
              .drop_duplicates(["state", "year"])[
                  ["state", "year", "population", "income_mean", "income_median"]
              ])
    overall = (df[df["division"].eq(OVERALL)][["state", "year", "index"]]
               .rename(columns={"index": "cpi"}))
    return core.merge(overall, on=["state", "year"], how="inner")


# ------------------------------------------------------------------ objective 1
def growth_comparison(df, baseline, comparison, income_measure="income_mean"):
    """Compare selected household income measure growth with Overall CPI growth."""
    if income_measure not in {"income_mean", "income_median"}:
        raise ValueError("income_measure must be 'income_mean' or 'income_median'")
    sy = state_year(df)
    a = sy[sy.year.eq(baseline)].set_index("state")
    b = sy[sy.year.eq(comparison)].set_index("state")
    common = a.index.intersection(b.index)
    out = pd.DataFrame(index=common)
    out["income_growth"] = (b.loc[common, income_measure] / a.loc[common, income_measure] - 1) * 100
    out["price_growth"] = (b.loc[common, "cpi"] / a.loc[common, "cpi"] - 1) * 100
    out["real_growth"] = ((1 + out["income_growth"] / 100) /
                          (1 + out["price_growth"] / 100) - 1) * 100
    out["gap"] = out["income_growth"] - out["price_growth"]
    return out.replace([float("inf"), -float("inf")], pd.NA).dropna().reset_index()


# ------------------------------------------------------------------ objective 2
def population_income_snapshot(df, year):
    return state_year(df).query("year == @year").dropna(
        subset=["population", "income_mean", "cpi"]
    ).copy()


def rank_corr(a, b):
    """Spearman rank correlation (no SciPy needed)."""
    return float(pd.Series(a).rank().corr(pd.Series(b).rank()))


# ------------------------------------------------------------------ objective 3
def category_state_growth(df, baseline, comparison, category):
    part = df[df["division"].eq(category)]
    a = part[part.year.eq(baseline)].set_index("state")["index"]
    b = part[part.year.eq(comparison)].set_index("state")["index"]
    common = a.index.intersection(b.index)
    out = pd.DataFrame({"state": common,
                        "price_growth": (b.loc[common] / a.loc[common] - 1).values * 100})
    return out.dropna().sort_values("price_growth", ascending=False).reset_index(drop=True)


def category_growth_national(df, baseline, comparison):
    """Unweighted mean of state-level category CPI growth; descriptive, not expenditure-weighted."""
    categories = [c for c in df["division"].dropna().unique() if c != OVERALL]
    rows = []
    for category in categories:
        a = df[(df.year == baseline) & (df.division == category)].set_index("state")["index"]
        b = df[(df.year == comparison) & (df.division == category)].set_index("state")["index"]
        common = a.index.intersection(b.index)
        growth = (b.loc[common] / a.loc[common] - 1) * 100
        rows.append({"category": category, "price_growth": growth.mean()})
    return pd.DataFrame(rows).sort_values("price_growth", ascending=False).reset_index(drop=True)


def category_growth_table(df, baseline, comparison):
    """Price growth (%) with states as rows and categories as columns (plus 'Overall').
    Rows are sorted by overall price growth, so row 1 = highest cost-of-living pressure."""
    a = df[df.year.eq(baseline)].set_index(["state", "division"])["index"]
    b = df[df.year.eq(comparison)].set_index(["state", "division"])["index"]
    g = ((b / a - 1) * 100).unstack("division").dropna(subset=[OVERALL])
    g = g.sort_values(OVERALL, ascending=False)
    return g[[OVERALL] + [c for c in g.columns if c != OVERALL]]


# ------------------------------------------------------------------ map helpers
ALIASES = {
    "penang": "pulau pinang",
    "malacca": "melaka",
    "trengganu": "terengganu",
    "johore": "johor",
    "n sembilan": "negeri sembilan",
}


def norm(name):
    """'W.P. Kuala Lumpur', 'Wilayah Persekutuan Kuala Lumpur' and 'Kuala Lumpur' all become 'kuala lumpur'."""
    s = str(name).lower()
    s = re.sub(r"federal territory of|wilayah persekutuan|w\.p\.|\bwp\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIASES.get(s, s)


def _simplify_ring(ring, tol=0.004):
    """Douglas-Peucker: keep the shape but drop most points (tol in degrees, about 400 m)."""
    n = len(ring)
    if n <= 8:
        return ring
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[j][0], ring[j][1]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        far, far_d = -1, -1.0
        for k in range(i + 1, j):
            x, y = ring[k][0], ring[k][1]
            d = math.hypot(x - x1, y - y1) if length == 0 else abs(dy * (x - x1) - dx * (y - y1)) / length
            if d > far_d:
                far, far_d = k, d
        if far_d > tol:
            keep[far] = True
            stack += [(i, far), (far, j)]
    out = [p for p, k in zip(ring, keep) if k]
    return out if len(out) >= 4 else ring


def _ring_area(ring):
    """Signed area in lon/lat (positive = counter-clockwise)."""
    return sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1])) / 2


def _prepare_polygon(poly):
    """Simplify, round, and give outer rings clockwise / holes counter-clockwise order."""
    out = []
    for i, ring in enumerate(poly):
        ring = [[round(p[0], 3), round(p[1], 3)] for p in _simplify_ring(ring)]
        ccw = _ring_area(ring) > 0
        if (i == 0 and ccw) or (i > 0 and not ccw):
            ring = ring[::-1]
        out.append(ring)
    return out


def load_geojson(path, state_names):
    """Read a Malaysia states GeoJSON (for example geoBoundaries ADM1).
    Finds which property holds the state name, adds a 'state_key' property, makes the file light.
    Returns (geojson, states_without_a_shape)."""
    with open(path, encoding="utf-8") as fh:
        gj = json.load(fh)
    feats = gj["features"]
    wanted = {norm(s) for s in state_names}
    keys = {k for f in feats for k, v in (f.get("properties") or {}).items() if isinstance(v, str)}
    best, best_n = None, 0
    for k in keys:
        n = len({norm((f.get("properties") or {}).get(k) or "") for f in feats} & wanted)
        if n > best_n:
            best, best_n = k, n
    if best is None or best_n < 5:
        raise ValueError("Could not match the GeoJSON names to Malaysian state names.")
    slim = []
    for f in feats:
        geom = f.get("geometry")
        if not geom:
            continue
        key = norm((f.get("properties") or {}).get(best) or "")
        if geom["type"] == "Polygon":
            coords = _prepare_polygon(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            coords = [_prepare_polygon(p) for p in geom["coordinates"]]
        else:
            continue
        slim.append({"type": "Feature", "properties": {"state_key": key},
                     "geometry": {"type": geom["type"], "coordinates": coords}})
    out = {"type": "FeatureCollection", "features": slim, "state_property": best}
    drawn = {f["properties"]["state_key"] for f in slim}
    return out, [s for s in state_names if norm(s) not in drawn]


def _points(coords):
    if coords and isinstance(coords[0], (int, float)):
        yield coords[0], coords[1]
    else:
        for c in coords:
            yield from _points(c)


def geo_view(gj, width_px=900, height_px=460):
    """Map centre and zoom that fit all shapes."""
    pts = [p for f in gj["features"] for p in _points(f["geometry"]["coordinates"])]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    lon_span, lat_span = max(lons) - min(lons), max(lats) - min(lats)
    z_lon = math.log2(0.9 * width_px * 360 / (512 * max(lon_span, 0.1)))
    z_lat = math.log2(0.9 * height_px * 360 / (512 * max(lat_span, 0.1)))
    return {"lat": (min(lats) + max(lats)) / 2, "lon": (min(lons) + max(lons)) / 2}, min(z_lon, z_lat)
