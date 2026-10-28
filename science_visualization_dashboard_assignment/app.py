"""Malaysia states dashboard: population, household income and marriages (2017-2023).

JIE42403 Scientific Visualisation - three pages, one objective each:
    1. Population growth by state
    2. Mean vs median household income by state
    3. Marriage trends by state
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import dashboard_data as an
from dashboard_data import COORDS, Y0, Y1

st.set_page_config(
    page_title="Malaysia States Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BLUE, ORANGE, GREY, RED = "#2a6fdb", "#f08a24", "#9aa5b1", "#d1495b"

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; max-width: 1250px;}
    .kpi {border: 1px solid rgba(128,128,128,.28); border-left: 5px solid #2a6fdb;
          border-radius: 10px; padding: .7rem .9rem; height: 100%;
          background: rgba(42,111,219,.05);}
    .kpi .l {font-size: .78rem; opacity: .7; text-transform: uppercase; letter-spacing: .04em;}
    .kpi .v {font-size: 1.55rem; font-weight: 700; line-height: 1.25;}
    .kpi .s {font-size: .8rem; opacity: .75;}
    .obj {border-left: 4px solid #f08a24; padding: .6rem .9rem; margin: .2rem 0 1rem 0;
          background: rgba(240,138,36,.08); border-radius: 0 8px 8px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ helpers
@st.cache_data
def load_pop():
    return an.load_population()


@st.cache_data
def load_inc():
    return an.load_income()


@st.cache_data
def load_mar():
    return an.load_marriages()


def show(fig, height=None):
    """Render a Plotly figure full-width (works across Streamlit versions)."""
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(size=13),
    )
    if height:
        fig.update_layout(height=height)
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # older Streamlit
        st.plotly_chart(fig, use_container_width=True)


def header(title, objective):
    st.title(title)
    st.markdown(f'<div class="obj"><b>Objective.</b> {objective}</div>', unsafe_allow_html=True)


def kpis(items):
    """Summary box: list of (label, value, sub-text)."""
    cols = st.columns(len(items))
    for col, (label, value, sub) in zip(cols, items):
        col.markdown(
            f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
            f'<div class="s">{sub}</div></div>',
            unsafe_allow_html=True,
        )
    st.write("")


def interpretation(text):
    with st.container(border=True):
        st.markdown("**Interpretation**")
        st.markdown(text)


def ranked(s, n=3, fmt="{:.2f}", ascending=False):
    s = s.sort_values(ascending=ascending).head(n)
    return ", ".join(f"**{k}** ({fmt.format(v)})" for k, v in s.items())


def add_coords(df, col="state"):
    df = df.copy()
    df["lat"] = df[col].map(lambda s: COORDS[s][0])
    df["lon"] = df[col].map(lambda s: COORDS[s][1])
    return df


def bubble_map(df, color, size, color_label, scale, hover, range_color=None, midpoint=None):
    fig = px.scatter_map(
        df,
        lat="lat",
        lon="lon",
        color=color,
        size=size,
        size_max=46,
        hover_name="state",
        hover_data=hover,
        color_continuous_scale=scale,
        range_color=range_color,
        color_continuous_midpoint=midpoint,
        labels={color: color_label},
        center=dict(lat=4.3, lon=108.8),
        zoom=4.4,
        map_style="carto-positron",
        opacity=0.85,
    )
    fig.update_layout(coloraxis_colorbar=dict(title=color_label, thickness=14))
    return fig


# ======================================================================== PAGE 1
def page_population():
    pop = load_pop()
    wide = an.population_wide(pop)

    header(
        "Page 1 · Population growth across Malaysian states",
        "Analyse how the population of each Malaysian state grew (or shrank) between 2017 and 2023 "
        "using annual population estimates, and identify which states drive national growth.",
    )

    y0, y1 = st.slider("Study period", Y0, Y1, (Y0, Y1), help="Applies to the summary box, line chart and map.")
    if y0 >= y1:
        st.warning("Choose a period of at least two years.")
        return

    growth = an.annual_growth_pct(wide)
    cagr = an.cagr_pct(wide, y0, y1)
    gain = wide[y1] - wide[y0]
    nat = wide.sum()
    nat_cagr = ((nat[y1] / nat[y0]) ** (1 / (y1 - y0)) - 1) * 100

    # ---- Summary box
    kpis(
        [
            (f"Malaysia population, {y1}", f"{nat[y1] / 1000:.1f} M", f"{nat[y0] / 1000:.1f} M in {y0}"),
            ("National growth (CAGR)", f"{nat_cagr:+.2f}% / yr", f"{y0}–{y1}"),
            ("Fastest-growing state", cagr.idxmax(), f"{cagr.max():+.2f}% / yr"),
            ("Weakest growth", cagr.idxmin(), f"{cagr.min():+.2f}% / yr"),
            ("Largest absolute gain", gain.idxmax(), f"{gain.max():+,.0f} thousand people"),
        ]
    )

    g20 = growth[2020] if 2020 in growth.columns else None
    crosses_2020 = y0 < 2020 <= y1
    if crosses_2020:
        st.info(
            f"**Data note.** Between 2019 and 2020 the published series jumps in both directions "
            f"(from {g20.idxmin()} {g20.min():+.1f}% to {g20.idxmax()} {g20.max():+.1f}% in a single year). "
            "Swings of this size are not plausible demographic flows and most likely reflect the series being "
            "re-based to the 2020 Census. Growth rates that cross 2020 therefore mix real growth with this "
            "re-basing; set the study period to 2017–2019 or 2020–2023 for a like-for-like comparison."
        )

    # ---- Visual 1: line plot
    st.subheader("1 · Population trajectories")
    c1, c2 = st.columns([3, 1.4])
    default = wide[y1].nlargest(6).index.tolist()
    states = c1.multiselect("States to display", list(wide.index), default=default)
    mode = c2.radio("Scale", [f"Index ({y0} = 100)", "Population ('000)"], horizontal=False)
    if states:
        d = pop[pop.state.isin(states) & pop.year.between(y0, y1)].copy()
        if mode.startswith("Index"):
            base = d[d.year == y0].set_index("state")["population"]
            d["value"] = d["population"] / d["state"].map(base) * 100
            ylab = f"Population index ({y0} = 100)"
        else:
            d["value"] = d["population"]
            ylab = "Population ('000)"
        fig = px.line(
            d, x="year", y="value", color="state", markers=True,
            labels={"value": ylab, "year": "Year", "state": "State"},
            title="Population by state over time",
        )
        fig.update_xaxes(dtick=1)
        if crosses_2020:
            fig.add_vline(x=2020, line_dash="dot", line_color=GREY,
                          annotation_text="2020 series break", annotation_position="top left")
        show(fig, 430)
    else:
        st.info("Select at least one state.")
    interpretation(
        f"The indexed lines remove differences in size so growth *speed* can be compared directly. "
        f"Nationally the population moved from **{nat[y0] / 1000:.1f} M to {nat[y1] / 1000:.1f} M** "
        f"({nat_cagr:+.2f}% a year). In absolute terms **{gain.idxmax()}** adds the most people "
        f"({gain.max():,.0f} thousand), while **{gain.idxmin()}** changes the least or loses people "
        f"({gain.min():+,.0f} thousand). Lines that move in near-parallel before 2020 show steady, "
        "natural-increase-driven growth; the vertical jump at 2020 is the series break described above, "
        "not a one-year migration wave."
    )

    # ---- Visual 2: heatmap of annual growth
    st.subheader("2 · Year-on-year growth heatmap")
    gy = growth.loc[:, [c for c in growth.columns if y0 < c <= y1]]
    order = cagr.sort_values(ascending=False).index
    z = gy.loc[order]
    fig = go.Figure(
        go.Heatmap(
            z=z.values, x=[str(c) for c in z.columns], y=list(z.index),
            colorscale="RdBu", zmid=0, zmin=-8, zmax=8,
            text=np.round(z.values, 1), texttemplate="%{text}",
            hovertemplate="%{y}, %{x}<br>Growth: %{z:+.2f}%<extra></extra>",
            colorbar=dict(title="% YoY", thickness=14),
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Annual population growth (%), states ranked by CAGR (colour clipped at ±8%)")
    show(fig, 520)
    ex = gy.drop(columns=[2020], errors="ignore").stack()
    ex_state, ex_year = ex.idxmax()
    last_pos = int((gy[y1] > 0).sum())
    txt = (
        f"Blue cells are growth years and red cells are contractions; the number in each cell is the exact "
        f"percentage. Excluding 2020, the typical year-on-year change has a median absolute size of "
        f"**{ex.abs().median():.1f}%**. The largest single gain is **{ex_state} in {ex_year}** ({ex.max():+.1f}%)"
    )
    if ex_state == "W.P. Putrajaya":
        txt += ", consistent with a new administrative city still filling up. "
    else:
        txt += ". "
    if crosses_2020:
        txt += (
            "The 2020 column is the re-basing artefact: it is negative where the earlier series was higher than the "
            "re-based one and positive where it was lower, so it should not be read as migration. "
        )
    txt += f"In {y1}, **{last_pos} of {len(gy)}** states grew, showing how broad-based the latest growth is."
    interpretation(txt)

    # ---- Visual 3: geospatial bubble map
    st.subheader("3 · Where is growth happening?")
    mp = add_coords(pd.DataFrame({"state": cagr.index, "CAGR (%)": cagr.values, "Population ('000)": wide[y1].values}))
    mp = mp.sort_values("Population ('000)", ascending=False)
    fig = bubble_map(
        mp, "CAGR (%)", "Population ('000)", "CAGR (% / yr)", "RdBu",
        {"lat": False, "lon": False, "CAGR (%)": ":.2f", "Population ('000)": ":,.0f"},
        range_color=[-3, 3], midpoint=0,
    )
    fig.update_layout(title=f"Population growth rate {y0}–{y1} (bubble size = {y1} population)")
    show(fig, 560)
    interpretation(
        f"Bubble size shows how many people live in each state in {y1}; colour shows the annual growth rate. "
        f"The fastest growers are {ranked(cagr, 3, '{:+.2f}%')}, while growth is weakest in "
        f"{ranked(cagr, 3, '{:+.2f}%', ascending=True)}. Populous states can combine large bubbles "
        "with positive growth, but growth is not simply a function of size: some large states show weak or negative "
        "rates. Treat strongly negative values with care — if the period spans 2020 they may reflect "
        "the series break rather than real decline (compare against the 2020–2023 period)."
    )

    with st.container(border=True):
        st.markdown("**Page takeaway**")
        st.markdown(
            f"Population growth is concentrated in a few states: **{gain.idxmax()}** alone contributes "
            f"{gain.max() / gain.clip(lower=0).sum() * 100:.0f}% of all positive state-level gains. "
            f"The highest growth *rates* belong to {', '.join(cagr.nlargest(2).index)}, which are small, "
            "whereas the highest *counts* come from large states, so rate and volume must be read together."
        )


# ======================================================================== PAGE 2
def page_income():
    inc = load_inc()
    pop = load_pop()
    years = sorted(inc.year.unique())

    header(
        "Page 2 · Household income: mean vs median",
        f"Compare mean and median monthly household income across Malaysian states for the survey years available "
        f"in 2017–2023 ({', '.join(map(str, years))}), and judge how skewed each state's income distribution is.",
    )
    st.caption(
        f"The household income survey is not annual: only **{', '.join(map(str, years))}** fall inside the "
        "study window, so 2017, 2018, 2021 and 2023 are not available."
    )

    year = st.radio("Survey year", years, index=len(years) - 1, horizontal=True)
    d = inc[inc.year == year].set_index("state")
    w_med = inc.pivot(index="state", columns="year", values="income_median")
    chg = (w_med[years[-1]] / w_med[years[0]] - 1) * 100

    # ---- Summary box
    kpis(
        [
            ("Highest median income", d.income_median.idxmax(), f"RM {d.income_median.max():,.0f} / month"),
            ("Lowest median income", d.income_median.idxmin(), f"RM {d.income_median.min():,.0f} / month"),
            ("Top ÷ bottom state", f"{d.income_median.max() / d.income_median.min():.2f}×", f"median income, {year}"),
            ("Average mean ÷ median", f"{d.ratio.mean():.2f}×", "mean is above median in every state"),
            (f"Median change {years[0]}→{years[-1]}", f"{chg.mean():+.1f}%", f"average of states; range {chg.min():+.0f}% to {chg.max():+.0f}%"),
        ]
    )

    # ---- Visual 1: dumbbell
    st.subheader("1 · Mean vs median by state")
    order = d.sort_values("income_median").index.tolist()
    xs, ys = [], []
    for s in order:
        xs += [d.loc[s, "income_median"], d.loc[s, "income_mean"], None]
        ys += [s, s, None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#c9ced6", width=4),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=d.loc[order, "income_median"], y=order, mode="markers", name="Median",
                             marker=dict(size=12, color=BLUE),
                             hovertemplate="%{y}<br>Median: RM %{x:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=d.loc[order, "income_mean"], y=order, mode="markers", name="Mean",
                             marker=dict(size=12, color=ORANGE, symbol="diamond"),
                             hovertemplate="%{y}<br>Mean: RM %{x:,.0f}<extra></extra>"))
    fig.update_layout(
        title=f"Monthly household income, {year}: the grey bar is the mean–median gap",
        xaxis_title="Household income (RM / month)",
        yaxis=dict(categoryorder="array", categoryarray=order),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    show(fig, 560)
    gap_pct = (d.ratio - 1) * 100
    interpretation(
        f"In {year} the highest median income is in **{d.income_median.idxmax()}** "
        f"(RM {d.income_median.max():,.0f}) and the lowest in **{d.income_median.idxmin()}** "
        f"(RM {d.income_median.min():,.0f}), a **{d.income_median.max() / d.income_median.min():.1f}×** spread. "
        f"The mean exceeds the median in every state — by {gap_pct.min():.0f}% to {gap_pct.max():.0f}% — "
        "which is the signature of a right-skewed distribution: a minority of high-income households pulls the "
        f"average above what the typical household earns. The widest relative gap is in **{d.ratio.idxmax()}** "
        f"(mean = {d.ratio.max():.2f}× median), the narrowest in **{d.ratio.idxmin()}** ({d.ratio.min():.2f}×); "
        "the median is the fairer measure of the 'typical' household."
    )

    # ---- Visual 2: scatter mean vs median, all survey years
    st.subheader("2 · Mean–median relationship across survey years")
    s_df = inc.assign(Year=inc.year.astype(str))
    fig = px.scatter(
        s_df, x="income_median", y="income_mean", color="Year", hover_name="state",
        category_orders={"Year": [str(y) for y in years]},
        color_discrete_sequence=[GREY, RED, BLUE],
        labels={"income_median": "Median household income (RM / month)",
                "income_mean": "Mean household income (RM / month)"},
        title="Each point is one state in one survey year",
    )
    fig.update_traces(marker=dict(size=10, opacity=0.85))
    x_lo, x_hi = s_df.income_median.min() * 0.9, s_df.income_median.max() * 1.05
    y_lo, y_hi = s_df.income_mean.min() * 0.9, s_df.income_mean.max() * 1.08
    for k in (1.2, 1.4):
        fig.add_trace(go.Scatter(x=[x_lo, x_hi], y=[k * x_lo, k * x_hi], mode="lines",
                                 line=dict(color="#aab", dash="dash", width=1), showlegend=False, hoverinfo="skip"))
        xl = min(x_hi, y_hi / k) * 0.97
        fig.add_trace(go.Scatter(x=[xl], y=[k * xl], mode="text", text=[f"mean = {k}× median"],
                                 textposition="top left", showlegend=False, hoverinfo="skip",
                                 textfont=dict(size=11, color="#667")))
    sel = s_df[s_df.year == year]
    fig.add_trace(go.Scatter(x=sel.income_median, y=sel.income_mean, mode="text", text=sel.state,
                             textposition="top center", textfont=dict(size=10),
                             showlegend=False, hoverinfo="skip"))
    fig.update_xaxes(range=[x_lo, x_hi])
    fig.update_yaxes(range=[y_lo, y_hi])
    show(fig, 520)
    y_first, y_last = years[0], years[-1]
    y_mid = 2020 if 2020 in years else years[1]
    med = inc.pivot(index="state", columns="year", values="income_median")
    r = inc.pivot(index="state", columns="year", values="ratio")
    fall = ((med[y_mid] / med[y_first] - 1) * 100).mean()
    in_band = ((inc.ratio >= 1.19) & (inc.ratio <= 1.41)).mean()
    above = int((med[y_last] > med[y_first]).sum())
    interpretation(
        f"The points fall almost on a straight line, so mean and median move together: {in_band:.0%} of the "
        f"state-year points sit between the dashed 1.2× and 1.4× guide lines, so the degree of skew is "
        f"surprisingly uniform across states. The {y_mid} cloud (red) lies to the lower-left of {y_first} (grey): "
        f"the median fell by about **{abs(fall):.0f}%** on average in the pandemic year. By {y_last} (blue) the median is "
        f"back above its {y_first} level in **{above} of {len(med)}** states. The average mean ÷ median ratio rises "
        f"from {r[y_first].mean():.2f} to {r[y_mid].mean():.2f} in {y_mid} and falls back to {r[y_last].mean():.2f} in "
        f"{y_last}: the mean fell by less than the median in {y_mid}, which suggests the pandemic cut the incomes of "
        "typical households more than those of top earners. Labels show the states for the selected survey year."
    )

    # ---- Visual 3: geospatial
    st.subheader("3 · Geography of household income")
    metric_opts = {"Median income (RM)": "income_median", "Mean income (RM)": "income_mean",
                   "Mean − median gap (RM)": "gap"}
    metric_label = st.selectbox("Map colour", list(metric_opts), index=0)
    col = metric_opts[metric_label]
    mp = d.reset_index()[["state", col]].merge(
        pop[pop.year == year][["state", "population"]].rename(columns={"population": "Population ('000)"}),
        on="state",
    )
    mp = add_coords(mp).sort_values("Population ('000)", ascending=False)
    fig = bubble_map(
        mp, col, "Population ('000)", metric_label, "YlGnBu",
        {"lat": False, "lon": False, col: ":,.0f", "Population ('000)": ":,.0f"},
    )
    fig.update_layout(title=f"{metric_label}, {year} (bubble size = state population)")
    show(fig, 560)
    top3 = d.income_median.nlargest(3).index
    klang = set(top3) == {"W.P. Kuala Lumpur", "W.P. Putrajaya", "Selangor"}
    interpretation(
        f"Darker bubbles mark higher values. In {year} the highest-income states are "
        f"{ranked(d.income_median, 3, 'RM {:,.0f}')}"
        + (" — the contiguous Klang Valley core around the capital" if klang else "")
        + f", while the lowest are {ranked(d.income_median, 3, 'RM {:,.0f}', ascending=True)}. "
        f"The mean–median gap in ringgit is strongly correlated with median income "
        f"(r = {np.corrcoef(d.income_median, d.gap)[0, 1]:.2f} in {year}): the absolute gap grows with affluence even "
        "though the *relative* skew (Visual 2) is similar across states. Bubble size adds context: the largest bubbles "
        "show where most households live, so the national picture is weighted towards those states."
    )

    with st.container(border=True):
        st.markdown("**Page takeaway**")
        st.markdown(
            f"Median income is a more representative statistic than the mean — the mean overstates the typical "
            f"household by about {gap_pct.mean():.0f}% on average. Income fell sharply in 2020, "
            f"then recovered to above 2019 levels in most states by {years[-1]}, with the strongest rise "
            f"in **{chg.idxmax()}** ({chg.max():+.0f}%) and the weakest in **{chg.idxmin()}** ({chg.min():+.0f}%)."
        )


# ======================================================================== PAGE 3
def page_marriages():
    m = load_mar()
    pop_states = sorted(m.state.unique())
    header(
        "Page 3 · Marriage trends across Malaysian states",
        "Examine how the annual number of marriages and the marriage rate evolved in each state from 2017 to 2023, "
        "including the effect of the 2020 pandemic restrictions and the rebound afterwards.",
    )

    c1, c2, c3 = st.columns([3, 1.6, 1.6])
    totals = m.groupby("state")["abs"].sum()
    states = c1.multiselect("States (line chart)", pop_states, default=totals.nlargest(5).index.tolist())
    sex_label = c2.radio("Record basis", ["Both (average)", "Female", "Male"],
                         help="Each marriage has one female and one male record; state counts differ slightly "
                              "because spouses may register in different states.")
    clean = c3.checkbox("Exclude suspected anomalous rates", value=True,
                        help="Removes published rates whose implied population base jumps by more than 20% versus "
                             "neighbouring years (see Visual 3).")
    sex = {"Both (average)": "both", "Female": "female", "Male": "male"}[sex_label]

    both = an.marriages_by_state_year(m, "both", clean)
    sel = an.marriages_by_state_year(m, sex, clean)
    cnt = sel.pivot(index="state", columns="year", values="count")
    nat = both.groupby("year")["count"].sum()
    rate_avg = both.groupby("state")["rate"].mean()
    n_anom = int(m.anomaly.sum())

    # ---- Summary box
    peak_year = nat.idxmax()
    kpis(
        [
            (f"Marriages in {Y1}", f"{nat[Y1]:,.0f}", f"{an.pct_change(nat[Y1], nat[2019]):+.1f}% vs 2019"),
            ("2020 pandemic dip", f"{an.pct_change(nat[2020], nat[2019]):+.1f}%", f"{nat[2020]:,.0f} vs {nat[2019]:,.0f} in 2019"),
            ("Peak year", f"{peak_year}", f"{nat[peak_year]:,.0f} marriages (rebound)"),
            ("Highest avg. rate", rate_avg.idxmax(), f"{rate_avg.max():.1f} per 1,000"),
            ("Lowest avg. rate", rate_avg.idxmin(), f"{rate_avg.min():.1f} per 1,000"),
        ]
    )

    # ---- Visual 1: line plot
    st.subheader("1 · Marriages over time")
    view = st.radio("Show", ["Number of marriages", "Index (2019 = 100)"], horizontal=True)
    if states:
        long = cnt.loc[states].stack().rename("value").reset_index()
        if view.startswith("Index"):
            long["value"] = long["value"] / long["state"].map(cnt[2019]) * 100
            ylab = "Marriages, index (2019 = 100)"
        else:
            ylab = "Number of marriages"
        fig = px.line(long, x="year", y="value", color="state", markers=True,
                      labels={"value": ylab, "year": "Year", "state": "State"},
                      title=f"Annual marriages by state ({sex_label.lower()} records)")
        if view.startswith("Index"):
            nat_sex = cnt.sum()
            fig.add_trace(go.Scatter(x=nat_sex.index, y=nat_sex.values / nat_sex[2019] * 100,
                                     mode="lines+markers", name="Malaysia (total)",
                                     line=dict(color="black", dash="dash", width=3)))
            fig.add_hline(y=100, line_dash="dot", line_color=GREY)
        fig.update_xaxes(dtick=1)
        fig.add_vline(x=2020, line_dash="dot", line_color=GREY,
                      annotation_text="2020 restrictions", annotation_position="top left")
        show(fig, 430)
    else:
        st.info("Select at least one state.")
    chg20 = (cnt[2020] / cnt[2019] - 1) * 100
    up20 = chg20[chg20 > 0].index.tolist()
    interpretation(
        f"Nationally marriages were stable at ~{nat[[2017, 2018, 2019]].mean() / 1000:.0f}k a year until 2019, "
        f"fell **{abs(an.pct_change(nat[2020], nat[2019])):.1f}%** in 2020 when gatherings were restricted, "
        f"then rebounded to a peak of **{nat[peak_year]:,.0f} in {peak_year}** (postponed weddings) before falling "
        f"again to {nat[Y1]:,.0f} in {Y1} — **{abs(an.pct_change(nat[Y1], nat[2019])):.1f}%** below 2019, i.e. the "
        "rebound did not become a new normal. The dip was not uniform: "
        + (f"{len(up20)} state(s) actually recorded *more* marriages in 2020 than 2019 "
           f"({', '.join(up20[:4])}{'…' if len(up20) > 4 else ''}), "
           if up20 else "every state recorded fewer marriages in 2020, ")
        + f"while {chg20.idxmin()} fell the most ({chg20.min():+.1f}%). The index view makes these differences visible "
        "regardless of state size."
    )

    # ---- Visual 2: heatmap
    st.subheader("2 · State × year heatmap")
    hm_opts = ["Marriage rate (per 1,000)", "Number of marriages", "Change in marriages vs 2019 (%)"]
    hm = st.selectbox("Heatmap metric", hm_opts)
    if hm == hm_opts[0]:
        z = sel.pivot(index="state", columns="year", values="rate")
        cs, fmt, zmid, cb = "YlOrRd", ".1f", None, "per 1,000"
    elif hm == hm_opts[1]:
        z = cnt
        cs, fmt, zmid, cb = "YlGnBu", ",.0f", None, "marriages"
    else:
        z = (cnt.div(cnt[2019], axis=0) - 1) * 100
        cs, fmt, zmid, cb = "RdBu", ".0f", 0, "% vs 2019"
    z = z.loc[z.mean(axis=1).sort_values(ascending=False).index]
    kw = dict(zmid=zmid, zmin=-25, zmax=25) if zmid == 0 else {}
    fig = go.Figure(
        go.Heatmap(
            z=z.values, x=[str(c) for c in z.columns], y=list(z.index), colorscale=cs,
            text=z.values, texttemplate="%{text:" + fmt + "}",
            hovertemplate="%{y}, %{x}<br>%{z:" + fmt + "}<extra></extra>",
            colorbar=dict(title=cb, thickness=14), **kw,
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title=f"{hm} ({sex_label.lower()} records), states ordered high → low")
    show(fig, 540)
    ra = rate_avg
    interpretation(
        f"Rows are ordered from highest to lowest average value. On the **rate** view the highest-rate states are "
        f"{ranked(ra, 3, '{:.1f}')}, and the lowest are {ranked(ra, 3, '{:.1f}', ascending=True)} per 1,000. "
        f"Rates and counts tell different stories: {cnt[2023].idxmax()} leads on *counts* because it is large, whereas "
        "the states with the highest *rates* are not necessarily the biggest. In the 'change vs 2019' view "
        f"{int((chg20 < 0).sum())} of {len(chg20)} states are red (below 2019) in 2020, while "
        f"{int((cnt[2021] > cnt[2019]).sum())} of {len(cnt)} are blue (above 2019) in 2021 (the rebound)"
        + (f"; {', '.join(up20[:3])} already recorded increases in 2020." if up20 else ".")
    )

    # ---- Visual 3: scatter female vs male rate
    st.subheader("3 · Female vs male marriage rate")
    p = m.pivot_table(index=["state", "year"], columns="sex", values="rate").reset_index()
    flagged = set(zip(m.loc[m.anomaly, "state"], m.loc[m.anomaly, "year"]))
    p["flag"] = [(s_, y_) in flagged for s_, y_ in zip(p.state, p.year)]
    p["Year"] = p["year"].astype(str)
    ok, bad = p[~p.flag], p[p.flag]
    fig = px.scatter(ok, x="female", y="male", color="Year", hover_name="state",
                     color_discrete_sequence=px.colors.sequential.Viridis,
                     labels={"female": "Female marriage rate (per 1,000)", "male": "Male marriage rate (per 1,000)"},
                     title="Each point is one state in one year (dashed line: equal rates)")
    fig.update_traces(marker=dict(size=9, opacity=0.8))
    lo, hi = float(np.nanmin(p[["female", "male"]].values)) - 1, float(np.nanmax(p[["female", "male"]].values)) + 1
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color=GREY, dash="dash"),
                             showlegend=False, hoverinfo="skip"))
    if len(bad):
        fig.add_trace(go.Scatter(x=bad.female, y=bad.male, mode="markers+text", name="Suspected anomaly",
                                 text=[f"{s} {y}" for s, y in zip(bad.state, bad.year)], textposition="bottom right",
                                 marker=dict(symbol="x", size=14, color=RED, line=dict(width=2, color=RED)),
                                 hovertemplate="%{text}<br>F %{x} / M %{y}<extra></extra>"))
    show(fig, 520)
    diff = (p[~p.flag].female - p[~p.flag].male).groupby(p[~p.flag].state).mean()
    bad_txt = ""
    if len(bad):
        b = m[m.anomaly].iloc[0]
        bad_txt = (f" The red cross marks **{b.state} {b.sex} {b.year}**: its published rate ({b.rate}) is inconsistent "
                   f"with its count ({b['abs']:,}) — the implied population base differs by {abs(b.dev) * 100:.0f}% from "
                   "neighbouring years, most likely a recording error, so it is excluded from averages by default.")
    interpretation(
        "Points close to the dashed 45° line mean brides and grooms marry at similar rates, as expected because "
        "each marriage has one of each. Systematic departures reveal registration and demographic effects: "
        f"states where the **female** rate is higher than the male rate are {ranked(diff, 3, '{:+.1f}')}; "
        f"states where the **male** rate is higher are {ranked(diff, 3, '{:+.1f}', ascending=True)}. "
        "A possible explanation (not testable with this data) is that spouses register in different states, so "
        "migration hubs record more male than female marriages." + bad_txt
    )

    with st.container(border=True):
        st.markdown("**Page takeaway**")
        st.markdown(
            f"Marriage is highly sensitive to external shocks: a {abs(an.pct_change(nat[2020], nat[2019])):.0f}% fall in 2020 "
            f"was followed by a rebound to {nat[peak_year]:,.0f} ({peak_year}), then a decline to "
            f"{nat[Y1]:,.0f} by {Y1}. Rate-based and count-based rankings differ, so both should be used "
            f"when comparing states. {n_anom} published rate value(s) were flagged as suspect."
        )


# ======================================================================== MAIN
PAGES = {
    "1 · Population growth": page_population,
    "2 · Household income": page_income,
    "3 · Marriage trends": page_marriages,
}

with st.sidebar:
    st.header("📊 Malaysia States")
    st.caption("JIE42403 Scientific Visualisation")
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.divider()
    with st.expander("About the data"):
        st.markdown(
            "- **Population** – annual estimates by state ('000), 2017–2023\n"
            "- **Household income** – mean & median RM/month; survey years 2019, 2020, 2022 fall in the window\n"
            "- **Marriages** – annual counts and rates by state and sex, 2017–2023\n\n"
            "Source: Department of Statistics Malaysia (DOSM) open data, via data.gov.my.\n\n"
            "Heatmaps use diverging colours centred on zero for growth/change and sequential colours for levels."
        )

PAGES[choice]()
