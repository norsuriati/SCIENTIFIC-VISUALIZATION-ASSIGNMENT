"""Pure-pandas calculations for the dashboard (no Streamlit here, so they are easy to test)."""
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
