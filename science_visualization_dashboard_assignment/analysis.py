"""Pure-pandas calculations for the dashboard (no Streamlit here, so they are easy to test)."""
import json
import re

import pandas as pd

OVERALL = "Overall"

# Short labels so the heatmap columns stay readable
SHORT = {
    "Food & Beverages": "Food & Drink",
    "Alcoholic Beverages & Tobacco": "Alcohol & Tobacco",
    "Clothing & Footwear": "Clothing",
    "Housing & Utilities": "Housing & Utilities",
    "Furnishings & Household Maintenance": "Furnishings",
    "Health": "Health",
    "Transport": "Transport",
    "Information & Communication": "Info & Comms",
    "Recreation, Sport & Culture": "Recreation",
    "Education Services": "Education",
    "Restaurants & Accommodation": "Restaurants & Hotels",
    "Insurance & Financial Services": "Insurance & Finance",
    "Personal Care & Miscellaneous": "Personal Care",
}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


def state_year(df: pd.DataFrame) -> pd.DataFrame:
    """One row per state-year with population, income and overall CPI."""
    base = df.drop_duplicates(["state", "year"])[
        ["state", "year", "population", "income_mean", "income_median"]
    ]
    cpi = df[df["division"] == OVERALL][["state", "year", "index"]].rename(columns={"index": "cpi"})
    return base.merge(cpi, on=["state", "year"])


def growth_table(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """Income growth vs price growth between two years (all in %)."""
    sy = state_year(df)
    a = sy[sy["year"] == y0].set_index("state")
    b = sy[sy["year"] == y1].set_index("state")
    out = pd.DataFrame(
        {
            "income_growth": (b["income_mean"] / a["income_mean"] - 1) * 100,
            "price_growth": (b["cpi"] / a["cpi"] - 1) * 100,
        }
    )
    # Real income growth: how much income grew AFTER removing price increases
    out["real_growth"] = ((1 + out["income_growth"] / 100) / (1 + out["price_growth"] / 100) - 1) * 100
    out["gap"] = out["income_growth"] - out["price_growth"]
    return out.dropna().reset_index()


def population_table(df: pd.DataFrame, year: int) -> pd.DataFrame:
    sy = state_year(df)
    return sy[sy["year"] == year].reset_index(drop=True)


def category_growth(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """Price growth (%) per state and spending category between two years.
    Rows = states, columns = categories (plus 'Overall'), sorted by overall pressure."""
    a = df[df["year"] == y0].set_index(["state", "division"])["index"]
    b = df[df["year"] == y1].set_index(["state", "division"])["index"]
    g = ((b / a - 1) * 100).unstack("division")
    g = g.sort_values(OVERALL, ascending=False)
    cols = [OVERALL] + [c for c in g.columns if c != OVERALL]
    return g[cols]


# ------------------------------------------------------------------ map helpers
ALIASES = {
    "penang": "pulau pinang",
    "malacca": "melaka",
    "trengganu": "terengganu",
    "johore": "johor",
    "n sembilan": "negeri sembilan",
}


def norm(name) -> str:
    """Normalise a state name so 'W.P. Kuala Lumpur', 'Wilayah Persekutuan Kuala Lumpur'
    and 'Kuala Lumpur' all become 'kuala lumpur'."""
    s = str(name).lower()
    s = re.sub(r"federal territory of|wilayah persekutuan|w\.p\.|\bwp\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIASES.get(s, s)


def _round_coords(obj, nd=3):
    """Round coordinates (about 100 m) so the map file is lighter to send to the browser."""
    if isinstance(obj, (list, tuple)):
        return [_round_coords(x, nd) for x in obj]
    return round(obj, nd) if isinstance(obj, float) else obj


def _ring_area(ring) -> float:
    """Signed area of a ring in lon/lat (positive = counter-clockwise)."""
    return sum((x1 * y2 - x2 * y1) for (x1, y1, *_), (x2, y2, *_) in zip(ring, ring[1:] + ring[:1])) / 2


def _rewind_polygon(poly):
    """Plotly (d3) needs outer rings clockwise and holes counter-clockwise.
    Many GeoJSON files use the opposite order, which makes a state fill the whole map."""
    out = []
    for i, ring in enumerate(poly):
        ccw = _ring_area(ring) > 0
        if (i == 0 and ccw) or (i > 0 and not ccw):
            ring = ring[::-1]
        out.append(ring)
    return out


def _rewind_geometry(geom):
    if geom["type"] == "Polygon":
        geom["coordinates"] = _rewind_polygon(geom["coordinates"])
    elif geom["type"] == "MultiPolygon":
        geom["coordinates"] = [_rewind_polygon(p) for p in geom["coordinates"]]


def load_geojson(path: str, state_names):
    """Read a Malaysia states GeoJSON. Finds which property holds the state name, and adds a
    'state_key' property (normalised name) to every feature.
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
        raise ValueError("Could not match the GeoJSON property names to Malaysian state names.")
    for f in feats:
        f["properties"]["state_key"] = norm(f["properties"].get(best) or "")
        if f.get("geometry"):
            f["geometry"]["coordinates"] = _round_coords(f["geometry"]["coordinates"])
            _rewind_geometry(f["geometry"])
    drawn = {f["properties"]["state_key"] for f in feats}
    return gj, [s for s in state_names if norm(s) not in drawn]
