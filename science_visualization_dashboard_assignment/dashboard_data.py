"""Data loading and analysis helpers (pure pandas, no Streamlit/Plotly).

Keeping the calculations here makes them easy to test and keeps app.py focused on layout.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
Y0, Y1 = 2017, 2023  # study window

# Approximate state centroids for the bubble maps (no GeoJSON/API token required)
COORDS = {
    "Johor": (1.95, 103.35),
    "Kedah": (6.10, 100.55),
    "Kelantan": (5.40, 102.05),
    "Melaka": (2.20, 102.25),
    "Negeri Sembilan": (2.75, 102.25),
    "Pahang": (3.80, 102.60),
    "Perak": (4.60, 101.10),
    "Perlis": (6.45, 100.20),
    "Pulau Pinang": (5.38, 100.30),
    "Sabah": (5.40, 116.80),
    "Sarawak": (2.50, 113.50),
    "Selangor": (3.40, 101.45),
    "Terengganu": (4.85, 103.00),
    "W.P. Kuala Lumpur": (3.14, 101.69),
    "W.P. Labuan": (5.28, 115.24),
    "W.P. Putrajaya": (2.93, 101.70),
}


def _with_year(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    return df


# ------------------------------------------------------------------ population
def load_population() -> pd.DataFrame:
    """Total population by state-year (thousands), both sexes, all ages, all ethnicities."""
    df = _with_year(pd.read_csv(DATA / "population_state.csv"))
    df = df[(df.sex == "both") & (df.age == "overall") & (df.ethnicity == "overall")]
    df = df[df.year.between(Y0, Y1)]
    return df[["state", "year", "population"]].sort_values(["state", "year"]).reset_index(drop=True)


def population_wide(pop: pd.DataFrame) -> pd.DataFrame:
    return pop.pivot(index="state", columns="year", values="population")


def annual_growth_pct(wide: pd.DataFrame) -> pd.DataFrame:
    """Year-on-year % change (first year dropped)."""
    return (wide.pct_change(axis=1) * 100).drop(columns=wide.columns[0])


def cagr_pct(wide: pd.DataFrame, y0: int, y1: int) -> pd.Series:
    return ((wide[y1] / wide[y0]) ** (1 / (y1 - y0)) - 1) * 100


# ---------------------------------------------------------------------- income
def load_income() -> pd.DataFrame:
    """Household income (RM/month) for survey years inside the study window."""
    df = _with_year(pd.read_csv(DATA / "hh_income_state.csv"))
    df = df[df.year.between(Y0, Y1)].copy()
    df["gap"] = df.income_mean - df.income_median
    df["ratio"] = df.income_mean / df.income_median
    return df.sort_values(["state", "year"]).reset_index(drop=True)


# ------------------------------------------------------------------- marriages
def load_marriages(tol: float = 0.20) -> pd.DataFrame:
    """Marriages 2017-2023 with a suspected-anomaly flag on the published rate.

    The rate is count / base population, so count / rate should vary smoothly across
    years. A value that departs from the average of its neighbouring years by more
    than ``tol`` is flagged (e.g. Perak male 2023 = 30.8 while the count fell).
    """
    df = _with_year(pd.read_csv(DATA / "marriages_state.csv"))
    df = df[df.year.between(Y0, Y1)].sort_values(["state", "sex", "year"]).copy()
    df["base"] = df["abs"] / df["rate"]
    g = df.groupby(["state", "sex"])["base"]
    prev, nxt = g.shift(1), g.shift(-1)
    neighbour = pd.concat([prev, nxt], axis=1).mean(axis=1)
    df["dev"] = df["base"] / neighbour - 1
    df["anomaly"] = df["dev"].abs() > tol
    return df.reset_index(drop=True)


def marriages_by_state_year(m: pd.DataFrame, sex: str = "both", rate_clean: bool = True) -> pd.DataFrame:
    """One row per state-year with `count` and `rate`.

    sex='both' averages the bride and groom records (national totals are identical for the
    two sexes; state totals differ slightly because spouses can register in different states).
    """
    d = m.copy()
    if rate_clean:
        d.loc[d.anomaly, "rate"] = np.nan
    if sex != "both":
        d = d[d.sex == sex]
    out = d.groupby(["state", "year"], as_index=False).agg(count=("abs", "mean"), rate=("rate", "mean"))
    return out


def pct_change(new: float, old: float) -> float:
    return (new / old - 1) * 100
