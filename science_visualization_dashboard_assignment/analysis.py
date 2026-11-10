"""Pure-pandas calculations for Malaysia Cost of Living dashboard."""
import json
import re
from pathlib import Path

import pandas as pd

OVERALL = "Overall"

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

ALIASES = {
    "penang": "pulau pinang", "pinang": "pulau pinang",
    "malacca": "melaka", "trengganu": "terengganu",
    "johore": "johor", "n sembilan": "negeri sembilan",
    "kuala lumpur": "kuala lumpur", "labuan": "labuan",
    "putrajaya": "putrajaya",
}

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"state", "year", "population", "income_mean", "income_median", "division", "index"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["index"] = pd.to_numeric(df["index"], errors="coerce")
    for c in ["population", "income_mean", "income_median"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["state", "year", "division", "index"]).copy()
    df["year"] = df["year"].astype(int)
    df["state"] = df["state"].astype(str).str.strip()
    df["division"] = df["division"].astype(str).str.strip()
    return df

def state_year(df: pd.DataFrame) -> pd.DataFrame:
    base = df.drop_duplicates(["state", "year"])[
        ["state", "year", "population", "income_mean", "income_median"]]
    cpi = df[df["division"].str.casefold() == OVERALL.casefold()][
        ["state", "year", "index"]].rename(columns={"index": "cpi"})
    return base.merge(cpi, on=["state", "year"], how="inner")

def growth_table(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    sy = state_year(df)
    a, b = sy[sy.year == y0].set_index("state"), sy[sy.year == y1].set_index("state")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    out = pd.DataFrame(index=common)
    out["income_growth"] = (b.income_mean / a.income_mean - 1) * 100
    out["price_growth"] = (b.cpi / a.cpi - 1) * 100
    out["real_growth"] = ((1 + out.income_growth / 100) / (1 + out.price_growth / 100) - 1) * 100
    out["gap"] = out.income_growth - out.price_growth
    return out.replace([float("inf"), -float("inf")], pd.NA).dropna().reset_index(names="state")

def population_table(df: pd.DataFrame, year: int) -> pd.DataFrame:
    return state_year(df).query("year == @year").reset_index(drop=True)

def category_growth(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    d = df[df["division"] != OVERALL]
    a = d[d.year == y0].set_index(["state", "division"])["index"]
    b = d[d.year == y1].set_index(["state", "division"])["index"]
    g = ((b / a - 1) * 100).unstack("division")
    if OVERALL in df["division"].unique():
        overall = growth_table(df, y0, y1).set_index("state")["price_growth"]
        g[OVERALL] = overall
    if OVERALL in g.columns:
        g = g.sort_values(OVERALL, ascending=False)
        g = g[[OVERALL] + [c for c in g.columns if c != OVERALL]]
    return g

def norm(name) -> str:
    s = str(name or "").strip().lower().replace("&", " and ")
    s = re.sub(r"federal territory of|wilayah persekutuan|w\\.p\\.|\\bwp\\b", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return ALIASES.get(s, s)

def load_geojson(path: str, state_names=None):
    """Load ADM1 GeoJSON and normalize its feature labels to dataset state names."""
    with open(path, "r", encoding="utf-8") as f:
        geo = json.load(f)
    if not isinstance(geo.get("features"), list):
        raise ValueError("GeoJSON does not contain a features array.")
    lookup = {norm(s): s for s in (state_names or [])}
    # geoBoundaries names Kuala Lumpur / Labuan / Putrajaya without W.P. prefix.
    for feature in geo["features"]:
        props = feature.setdefault("properties", {})
        raw = props.get("shapeName") or props.get("NAME_1") or props.get("name")
        key = norm(raw)
        if key in lookup:
            props["dashboard_state"] = lookup[key]
        elif key in {"kuala lumpur", "labuan", "putrajaya"}:
            candidate = "W.P. " + key.title()
            props["dashboard_state"] = candidate if candidate in (state_names or []) else raw
        else:
            props["dashboard_state"] = raw
    return geo

def metrics(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    """Compatibility alias for the app's metrics call."""
    return growth_table(df, y0, y1)
