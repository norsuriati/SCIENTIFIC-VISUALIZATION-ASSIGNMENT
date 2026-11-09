"""Shared analysis layer (pandas/numpy only) used by the Streamlit app and the PDF report.
Data: DOSM household income, state CPI (2010=100) and state population."""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
BASE_YEAR, END_YEAR = 2012, 2024            # first/last household-income survey year that also has CPI
SURVEY_YEARS = [2012, 2014, 2016, 2019, 2020, 2022, 2024]
ESSENTIALS = ["Food & Beverages", "Housing & Utilities", "Transport"]

REGION = {  # for colouring only
    "Johor": "South", "Melaka": "South", "Negeri Sembilan": "South",
    "Kedah": "North", "Perlis": "North", "Pulau Pinang": "North", "Perak": "North",
    "Kelantan": "East Coast", "Terengganu": "East Coast", "Pahang": "East Coast",
    "Selangor": "Klang Valley", "W.P. Kuala Lumpur": "Klang Valley", "W.P. Putrajaya": "Klang Valley",
    "Sabah": "East Malaysia", "Sarawak": "East Malaysia", "W.P. Labuan": "East Malaysia",
}
SHORT = {"W.P. Kuala Lumpur": "KL", "W.P. Putrajaya": "Putrajaya", "W.P. Labuan": "Labuan",
         "Pulau Pinang": "Penang", "Negeri Sembilan": "N. Sembilan"}
# approximate state capital / centroid coordinates (lat, lon) for the geospatial bubble map
COORDS = {
    "Johor": (1.85, 103.3), "Kedah": (6.1, 100.6), "Kelantan": (5.3, 102.0), "Melaka": (2.2, 102.25),
    "Negeri Sembilan": (2.75, 102.25), "Pahang": (3.9, 102.6), "Perak": (4.6, 101.1), "Perlis": (6.45, 100.2),
    "Pulau Pinang": (5.4, 100.35), "Sabah": (5.4, 116.7), "Sarawak": (2.5, 113.5), "Selangor": (3.35, 101.5),
    "Terengganu": (4.9, 103.0), "W.P. Kuala Lumpur": (3.14, 101.69), "W.P. Labuan": (5.28, 115.24),
    "W.P. Putrajaya": (2.93, 101.69),
}

def short(s): return SHORT.get(s, s)

def load():
    pop = pd.read_csv(DATA / "population_state_slim.csv", parse_dates=["date"])
    pop = pop[(pop.sex == "both") & (pop.ethnicity == "overall")].copy()
    pop["year"] = pop.date.dt.year
    inc = pd.read_csv(DATA / "hh_income_state.csv", parse_dates=["date"])
    inc["year"] = inc.date.dt.year
    cpi = pd.read_csv(DATA / "cpi_2d_state_mapped.csv", parse_dates=["date"])
    cpi["year"] = cpi.date.dt.year
    return pop, inc, cpi

def pop_total(pop):
    t = pop[pop.age == "overall"][["state", "year", "population"]].rename(columns={"population": "pop_k"})
    return t

def age_groups(pop, year):
    """Broad age bands (non-overlapping, uses 5-year groups only; 70-74 .. 80-84 + 85+)."""
    g = pop[(pop.year == year) & (~pop.age.isin(["overall", "70+", "80+"]))].copy()
    def band(a):
        if a in ("0-4", "5-9", "10-14"): return "0-14"
        if a in ("65-69", "70-74", "75-79", "80-84", "85+"): return "65+"
        return "15-64"
    g["band"] = g.age.map(band)
    out = g.groupby(["state", "band"]).population.sum().unstack()
    out["dep_ratio"] = (out["0-14"] + out["65+"]) / out["15-64"] * 100
    return out

def cpi_annual(cpi, division="Overall"):
    d = cpi[cpi.division == division]
    return d.groupby(["state", "year"])["index"].mean().unstack()

def income_panel(inc, cpi):
    """Long panel state x survey year: nominal & real income (base year 2012 prices), CPI rebased 2012=100."""
    ca = cpi_annual(cpi).loc[:, SURVEY_YEARS]
    rebased = ca.div(ca[BASE_YEAR], axis=0) * 100
    rows = []
    for st, g in inc.groupby("state"):
        g = g.set_index("year")
        for y in SURVEY_YEARS:
            if y in g.index and not np.isnan(rebased.loc[st, y]):
                if BASE_YEAR not in g.index: continue
                rows.append(dict(state=st, year=y, mean=g.loc[y, "income_mean"], median=g.loc[y, "income_median"],
                                 cpi=rebased.loc[st, y],
                                 mean_idx=g.loc[y, "income_mean"] / g.loc[BASE_YEAR, "income_mean"] * 100,
                                 median_idx=g.loc[y, "income_median"] / g.loc[BASE_YEAR, "income_median"] * 100))
    p = pd.DataFrame(rows)
    p["real_median_idx"] = p.median_idx / p.cpi * 100
    p["real_mean_idx"] = p.mean_idx / p.cpi * 100
    p["real_median"] = p["median"] / (p.cpi / 100)      # RM at 2012 prices
    return p

def state_metrics(inc, cpi, pop):
    p = income_panel(inc, cpi)
    a, b = p[p.year == BASE_YEAR].set_index("state"), p[p.year == END_YEAR].set_index("state")
    m = pd.DataFrame(index=b.index)
    n = END_YEAR - BASE_YEAR
    m["inc_med_base"], m["inc_med_end"] = a["median"], b["median"]
    m["inc_mean_base"], m["inc_mean_end"] = a["mean"], b["mean"]
    m["inc_med_growth"] = (b["median"] / a["median"] - 1) * 100
    m["inc_mean_growth"] = (b["mean"] / a["mean"] - 1) * 100
    m["cpi_growth"] = (b["cpi"] / 100 - 1) * 100
    m["gap_pp"] = m.inc_med_growth - m.cpi_growth
    m["real_med_idx"] = b["real_median_idx"]
    m["real_med_cagr"] = ((b["real_median_idx"] / 100) ** (1 / n) - 1) * 100
    m["inc_med_cagr"] = ((b["median"] / a["median"]) ** (1 / n) - 1) * 100
    m["cpi_cagr"] = ((b["cpi"] / 100) ** (1 / n) - 1) * 100
    m["mean_median_ratio"] = b["mean"] / b["median"]
    pt = pop_total(pop).pivot(index="state", columns="year", values="pop_k")
    m["pop_end"], m["pop_base"] = pt[END_YEAR], pt[BASE_YEAR]
    m["pop_growth"] = (m.pop_end / m.pop_base - 1) * 100
    m["pop_share"] = m.pop_end / m.pop_end.sum() * 100
    ag = age_groups(pop, END_YEAR)
    m["dep_ratio"] = ag["dep_ratio"]
    # essentials & per-division growth (annual avg 2012 -> 2024)
    for d in ESSENTIALS:
        ca = cpi_annual(cpi, d)
        m[f"cpi_{d}"] = (ca[END_YEAR] / ca[BASE_YEAR] - 1) * 100
    m["essentials_growth"] = m[[f"cpi_{d}" for d in ESSENTIALS]].mean(axis=1)
    m["region"] = [REGION[s] for s in m.index]
    return m

def division_growth(cpi, y0=BASE_YEAR, y1=END_YEAR):
    """state x division cumulative % change between annual-average CPI of y0 and y1."""
    d = cpi[cpi.division != "Overall"]
    a = d.groupby(["state", "division", "year"])["index"].mean().unstack()
    return ((a[y1] / a[y0] - 1) * 100).unstack()

def pressure_index(m, w=None):
    """Composite Cost-of-Living Pressure Index (0-100, higher = more pressure). Rank-scaled components."""
    w = w or {"Price growth": 1, "Real-income shortfall": 1, "Low income level": 1, "Population growth": 1}
    def mm(s):  # percentile-rank scaling 0-100: robust to outliers (Putrajaya, Perlis, Terengganu)
        return (s.rank(method="average") - 1) / (len(s) - 1) * 100
    comp = pd.DataFrame({
        "Price growth": mm(m.cpi_growth),
        "Real-income shortfall": mm(-m.real_med_idx),
        "Low income level": mm(-m.inc_med_end),
        "Population growth": mm(m.pop_growth),
    })
    ws = pd.Series(w).reindex(comp.columns).fillna(0)
    ws = ws / ws.sum()
    contrib = comp * ws
    idx = contrib.sum(axis=1)
    return comp, contrib, idx

def monthly_overall(cpi):
    return cpi[cpi.division == "Overall"].pivot(index="date", columns="state", values="index")

def yoy(cpi):
    return monthly_overall(cpi).pct_change(12) * 100

def corr_table(m):
    from scipy import stats
    pairs = [("pop_end", "inc_med_end", "Population (2024) vs median income (2024)"),
             ("pop_end", "cpi_growth", "Population (2024) vs price growth 2012-24"),
             ("pop_growth", "cpi_growth", "Population growth vs price growth"),
             ("pop_end", "real_med_idx", "Population vs real median income index"),
             ("inc_med_end", "cpi_growth", "Median income (2024) vs price growth")]
    out = []
    for x, y, lab in pairs:
        r, pr = stats.pearsonr(m[x], m[y]); rho, ps = stats.spearmanr(m[x], m[y])
        lr, lp = stats.pearsonr(np.log(m[x]) if x.startswith("pop_end") else m[x], m[y])
        out.append(dict(pair=lab, pearson=r, p_pearson=pr, spearman=rho, p_spearman=ps))
    return pd.DataFrame(out)
