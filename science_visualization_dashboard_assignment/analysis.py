"""Data preparation and calculations for the Malaysia Cost of Living dashboard."""
from pathlib import Path
import pandas as pd

OVERALL = "Overall"

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

def growth_comparison(df, baseline, comparison):
    sy = state_year(df)
    a = sy[sy.year.eq(baseline)].set_index("state")
    b = sy[sy.year.eq(comparison)].set_index("state")
    common = a.index.intersection(b.index)
    out = pd.DataFrame(index=common)
    out["income_growth"] = (b.loc[common, "income_mean"] / a.loc[common, "income_mean"] - 1) * 100
    out["price_growth"] = (b.loc[common, "cpi"] / a.loc[common, "cpi"] - 1) * 100
    out["real_growth"] = ((1 + out["income_growth"] / 100) /
                          (1 + out["price_growth"] / 100) - 1) * 100
    out["gap"] = out["income_growth"] - out["price_growth"]
    return out.replace([float("inf"), -float("inf")], pd.NA).dropna().reset_index()

def population_income_snapshot(df, year):
    return state_year(df).query("year == @year").dropna(
        subset=["population", "income_mean", "cpi"]
    ).copy()

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
