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
from dashboard_data import Y0, Y1

st.set_page_config(
    page_title="Malaysia States Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BLUE, ORANGE, GREY, RED, GREEN = "#2a6fdb", "#f08a24", "#9aa5b1", "#d1495b", "#2e9e6b"

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


# ======================================================================== PAGE 1
def page_population():
    pop = load_pop()
    wide = an.population_wide(pop)

    header(
        "Page 1 · Population growth across Malaysian states",
        "Analyse how the population of each Malaysian state grew (or shrank) between 2017 and 2023 "
        "using annual population estimates, and identify which states drive national growth.",
    )

    y0, y1 = st.slider("Study period", Y0, Y1, (Y0, Y1), help="Applies to the summary box and all three charts.")
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

    # ---- Visual 1: treemap
    st.subheader("1 · Who lives where, and who is growing?")
    share = wide[y1] / wide[y1].sum() * 100
    tm = pd.DataFrame({
        "tile": [f"{st_}<br>{c:+.1f}% / yr" for st_, c in cagr.items()],
        "Population ('000)": wide[y1].values,
        "CAGR (%)": cagr.values,
    })
    fig = px.treemap(
        tm, path=[px.Constant("Malaysia"), "tile"], values="Population ('000)", color="CAGR (%)",
        color_continuous_scale="RdYlGn", range_color=[-3, 3],
        title=f"Tile size = population in {y1}; colour = annual growth rate {y0}–{y1}",
    )
    fig.update_traces(texttemplate="<b>%{label}</b><br>%{value:,.0f}k", textfont_size=13,
                      root_color="#f3f6fb")
    fig.update_layout(coloraxis_colorbar=dict(title="CAGR % / yr", thickness=14))
    show(fig, 500)
    big3 = share.nlargest(3)
    neg = cagr[cagr < 0]
    interpretation(
        f"The bigger the tile, the more people live in the state in {y1}. The three largest states — "
        f"{', '.join(f'**{k}** ({v:.0f}%)' for k, v in big3.items())} — hold **{big3.sum():.0f}%** of Malaysia's population. "
        "Green tiles are growing and red tiles are shrinking. "
        + (f"{len(neg)} state(s) are shrinking over this period, the largest being **{wide.loc[neg.index, y1].idxmax()}** "
           f"({neg[wide.loc[neg.index, y1].idxmax()]:+.2f}% a year). " if len(neg) else "No state shrinks over this period. ")
        + "Size and growth are not the same thing: the biggest tiles are not always the greenest."
    )

    # ---- Visual 2: year-on-year growth, grouped bars
    st.subheader("2 · Year-on-year growth by state")
    sg = st.multiselect("States to compare", list(wide.index),
                        default=wide[y1].nlargest(6).index.tolist(), key="p1_states")
    gy = growth.loc[:, [c for c in growth.columns if y0 < c <= y1]]
    if sg:
        gl = gy.loc[sg].stack().rename("growth").reset_index()
        gl.columns = ["state", "year", "growth"]
        fig = px.bar(
            gl, x="year", y="growth", color="state", barmode="group",
            labels={"growth": "Growth vs previous year (%)", "year": "Year", "state": "State"},
            title="Annual population growth (%) for the selected states",
        )
        fig.update_xaxes(dtick=1)
        fig.add_hline(y=0, line_color="#333", line_width=1)
        if crosses_2020:
            fig.add_vline(x=2020, line_dash="dot", line_color=GREY, layer="below",
                          annotation_text="2020 series break", annotation_position="top left")
        show(fig, 470)
    else:
        st.info("Select at least one state.")
    ex = gy.drop(columns=[2020], errors="ignore").stack()
    ex_state, ex_year = ex.idxmax()
    last_pos = int((gy[y1] > 0).sum())
    txt = (
        f"Each cluster is one year and each coloured bar is one state, so you can read how growth changes from year "
        f"to year. Excluding 2020, the typical year-on-year change across all states has a median absolute size of "
        f"**{ex.abs().median():.1f}%**, and the largest single gain is **{ex_state} in {ex_year}** ({ex.max():+.1f}%)"
    )
    txt += ", consistent with a new administrative city still filling up. " if ex_state == "W.P. Putrajaya" else ". "
    if crosses_2020:
        txt += (
            "The 2020 cluster contains very large bars in both directions (up and down): that is the re-basing "
            "artefact, not migration, so judge trends from the other years. "
        )
    txt += f"In {y1}, **{last_pos} of {len(gy)}** states grew, showing how broad-based the latest growth is."
    interpretation(txt)

    # ---- Visual 3: diverging bar of growth rate
    st.subheader("3 · Annual growth rate by state")
    cs = cagr.sort_values()
    fig = go.Figure(
        go.Bar(
            x=cs.values, y=list(cs.index), orientation="h",
            marker_color=[GREEN if v >= 0 else RED for v in cs.values],
            text=[f"{v:+.2f}%" for v in cs.values], textposition="outside",
            hovertemplate="%{y}<br>CAGR: %{x:+.2f}% per year<extra></extra>",
        )
    )
    fig.add_vline(x=nat_cagr, line_dash="dash", line_color="#333",
                  annotation_text=f"Malaysia {nat_cagr:+.2f}%", annotation_position="top")
    fig.update_xaxes(range=[min(cs.min(), 0) - 0.9, cs.max() + 0.9], title="Compound annual growth rate (% per year)")
    fig.update_yaxes(categoryorder="array", categoryarray=list(cs.index))
    fig.update_layout(title=f"Population growth rate {y0}–{y1}: green = growing, red = shrinking", showlegend=False)
    show(fig, 560)
    above = int((cagr > nat_cagr).sum())
    interpretation(
        f"States are ranked by compound annual growth rate; the dashed line is the national rate "
        f"({nat_cagr:+.2f}%). The fastest growers are {ranked(cagr, 3, '{:+.2f}%')}, while growth is weakest in "
        f"{ranked(cagr, 3, '{:+.2f}%', ascending=True)}. Only **{above} of {len(cagr)}** states grow faster than "
        "the national average, so growth is concentrated in a minority of states. Treat strongly negative values with "
        "care — if the period spans 2020 they may reflect the series break rather than real decline "
        "(compare against the 2020–2023 period)."
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

    # ---- Visual 3: change between survey years
    st.subheader("3 · How much did income change between survey years?")
    c1, c2 = st.columns(2)
    yf = c1.selectbox("From survey year", years[:-1], index=0)
    to_opts = [y for y in years if y > yf]
    yt = c2.selectbox("To survey year", to_opts, index=len(to_opts) - 1)
    w_mean = inc.pivot(index="state", columns="year", values="income_mean")
    ch_med = (w_med[yt] / w_med[yf] - 1) * 100
    ch_mean = (w_mean[yt] / w_mean[yf] - 1) * 100
    order3 = ch_med.sort_values().index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(y=order3, x=ch_med[order3], orientation="h", name="Median", marker_color=BLUE,
                         text=[f"{v:+.0f}%" for v in ch_med[order3]], textposition="outside",
                         hovertemplate="%{y}<br>Median change: %{x:+.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(y=order3, x=ch_mean[order3], orientation="h", name="Mean", marker_color=ORANGE,
                         text=[f"{v:+.0f}%" for v in ch_mean[order3]], textposition="outside",
                         hovertemplate="%{y}<br>Mean change: %{x:+.1f}%<extra></extra>"))
    lo3, hi3 = min(ch_med.min(), ch_mean.min(), 0), max(ch_med.max(), ch_mean.max(), 0)
    fig.update_xaxes(range=[lo3 - 4, hi3 + 5], title=f"Change in household income, {yf} → {yt} (%)")
    fig.update_yaxes(categoryorder="array", categoryarray=order3)
    fig.update_layout(barmode="group", title=f"Percentage change in median and mean income, {yf} → {yt}",
                      legend=dict(orientation="h", y=1.07, x=0))
    show(fig, 700)
    n_mean_faster = int((ch_mean > ch_med).sum())
    interpretation(
        f"Each state has two bars: the % change in its **median** (blue) and **mean** (orange) income from {yf} to {yt}. "
        f"On average the median changed **{ch_med.mean():+.1f}%** and the mean **{ch_mean.mean():+.1f}%**. "
        f"The median moved most in {ranked(ch_med, 3, '{:+.1f}%')} and least in "
        f"{ranked(ch_med, 3, '{:+.1f}%', ascending=True)}. In **{n_mean_faster} of {len(ch_med)}** states the mean "
        f"changed by *more* (or fell by less) than the median, meaning higher earners did relatively better than the "
        "typical household (widening skew); where the orange bar is shorter, the typical household fared relatively better."
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
    states = c1.multiselect("States (stacked chart)", pop_states, default=totals.nlargest(5).index.tolist())
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

    # ---- Visual 1: stacked columns
    st.subheader("1 · Marriages per year: who contributes?")
    chg20 = (cnt[2020] / cnt[2019] - 1) * 100
    up20 = chg20[chg20 > 0].index.tolist()
    nat_sel = cnt.sum()
    if states:
        parts = cnt.loc[states].stack().rename("value").reset_index()
        rest = (nat_sel - cnt.loc[states].sum()).rename("value").reset_index()
        rest["state"] = "Other states"
        sb = pd.concat([parts[["state", "year", "value"]], rest[["state", "year", "value"]]])
        palette = px.colors.qualitative.Set2
        cmap = {s_: palette[i % len(palette)] for i, s_ in enumerate(states)}
        cmap["Other states"] = "#c9ced6"
        fig = px.bar(
            sb, x="year", y="value", color="state", color_discrete_map=cmap,
            category_orders={"state": states + ["Other states"]},
            labels={"value": "Number of marriages", "year": "Year", "state": "State"},
            title=f"Annual marriages ({sex_label.lower()} records): selected states stacked on top of all other states",
        )
        fig.add_trace(go.Scatter(x=list(nat_sel.index), y=list(nat_sel.values), mode="text",
                                 text=[f"{v / 1000:.0f}k" for v in nat_sel.values], textposition="top center",
                                 showlegend=False, hoverinfo="skip", textfont=dict(size=13)))
        fig.update_layout(barmode="stack")
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(range=[0, float(nat_sel.max()) * 1.12])
        show(fig, 470)
        share_sel = cnt.loc[states, Y1].sum() / nat_sel[Y1] * 100
        sel_txt = f"The selected states account for **{share_sel:.0f}%** of all marriages in {Y1}. "
    else:
        st.info("Select at least one state.")
        sel_txt = ""
    interpretation(
        f"The total height of each column is the national count (labelled on top). Nationally marriages were stable at "
        f"~{nat[[2017, 2018, 2019]].mean() / 1000:.0f}k a year until 2019, fell **{abs(an.pct_change(nat[2020], nat[2019])):.1f}%** "
        f"in 2020 when gatherings were restricted, then rebounded to a peak of **{nat[peak_year]:,.0f} in {peak_year}** "
        f"(postponed weddings) before falling to {nat[Y1]:,.0f} in {Y1} — **{abs(an.pct_change(nat[Y1], nat[2019])):.1f}%** "
        "below 2019, i.e. the rebound did not become a new normal. " + sel_txt
        + "The dip was not uniform: "
        + (f"{len(up20)} state(s) recorded *more* marriages in 2020 than 2019 "
           f"({', '.join(up20[:4])}{'…' if len(up20) > 4 else ''}), "
           if up20 else "every state recorded fewer marriages in 2020, ")
        + f"while {chg20.idxmin()} fell the most ({chg20.min():+.1f}%)."
    )

    # ---- Visual 2: ranked bar chart
    st.subheader("2 · State ranking")
    c1, c2 = st.columns([2, 2])
    yr = c1.select_slider("Year", options=list(range(Y0, Y1 + 1)), value=Y1)
    measure = c2.radio("Measure", ["Marriage rate (per 1,000)", "Number of marriages"], horizontal=True)
    rate_y = sel[sel.year == yr].set_index("state")["rate"].dropna()
    cnt_y = cnt[yr]
    if measure.startswith("Marriage rate"):
        ser, fmt, unit = rate_y, "{:.1f}", "per 1,000"
    else:
        ser, fmt, unit = cnt_y, "{:,.0f}", "marriages"
    ser = ser.sort_values()
    avg = ser.mean()
    fig = go.Figure(
        go.Bar(
            x=ser.values, y=list(ser.index), orientation="h",
            marker_color=[ORANGE if v >= avg else BLUE for v in ser.values],
            text=[fmt.format(v) for v in ser.values], textposition="outside",
            hovertemplate="%{y}<br>%{x:,.1f} " + unit + "<extra></extra>",
        )
    )
    fig.add_vline(x=avg, line_dash="dash", line_color="#333",
                  annotation_text=f"Average of states: {fmt.format(avg)}", annotation_position="top")
    fig.update_xaxes(range=[0, float(ser.max()) * 1.15], title=measure)
    fig.update_yaxes(categoryorder="array", categoryarray=list(ser.index))
    fig.update_layout(title=f"{measure}, {yr} — orange = at or above average, blue = below", showlegend=False)
    show(fig, 560)
    both_idx = rate_y.index.intersection(cnt_y.index)
    rho = rate_y[both_idx].corr(cnt_y[both_idx], method="spearman")
    n_above = int((ser >= avg).sum())
    interpretation(
        f"In {yr} the highest values are {ranked(ser, 3, fmt)} and the lowest are {ranked(ser, 3, fmt, ascending=True)} "
        f"({unit}). **{n_above} of {len(ser)}** states are at or above the average of states ({fmt.format(avg)}). "
        f"Switch the measure to see why both matter: the rank correlation between rate and count is "
        f"**{rho:.2f}** in {yr} ({'weak' if abs(rho) < 0.4 else 'moderate' if abs(rho) < 0.7 else 'strong'}), so the "
        "*count* ranking (driven by state size) differs from the *rate* ranking. "
        "Rates are the fairer way to compare states of different size."
    )

    # ---- Visual 3: marriage rate by year (grouped bars)
    st.subheader("3 · Marriage rate over the years")
    rate_p = sel.pivot(index="state", columns="year", values="rate")
    avg_y = rate_p.mean()
    if states:
        palette = px.colors.qualitative.Set2
        cmap = {s_: palette[i % len(palette)] for i, s_ in enumerate(states)}
        rt = sel[sel.state.isin(states)].dropna(subset=["rate"])
        fig = px.bar(
            rt, x="year", y="rate", color="state", barmode="group", color_discrete_map=cmap,
            category_orders={"state": states},
            labels={"rate": "Marriage rate (per 1,000)", "year": "Year", "state": "State"},
            title=f"Marriage rate per year ({sex_label.lower()} records); diamonds = average of all 16 states",
        )
        fig.add_trace(go.Scatter(x=list(avg_y.index), y=list(avg_y.values), mode="markers", name="Average of all states",
                                 marker=dict(symbol="diamond", size=12, color="black"),
                                 hovertemplate="Average of states, %{x}: %{y:.1f}<extra></extra>"))
        fig.update_xaxes(dtick=1)
        show(fig, 470)
    else:
        st.info("Select at least one state.")
    d_rate = (rate_p[Y1] - rate_p[2019]).dropna()
    interpretation(
        f"Each cluster is one year; each bar is a state's marriage rate per 1,000, and the black diamond is the "
        f"average of all states. The average rate was **{avg_y[2019]:.1f}** in 2019, **{avg_y[2020]:.1f}** in 2020, "
        f"**{avg_y[2021]:.1f}** in 2021 and **{avg_y[Y1]:.1f}** in {Y1}. Compared with 2019, the rate in {Y1} is lower in "
        f"**{int((d_rate < 0).sum())} of {len(d_rate)}** states; the largest fall is in **{d_rate.idxmin()}** "
        f"({d_rate.min():+.1f} points) and the smallest change in **{d_rate.abs().idxmin()}** ({d_rate[d_rate.abs().idxmin()]:+.1f}). "
        "Unlike the counts in Visual 1, rates adjust for population size, so they show whether marriage is becoming "
        "more or less common rather than simply whether more people live in the state."
    )

    with st.expander("Data-quality check: female vs male marriage rate (shows the flagged anomaly)"):
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
            "Colour code: green/red = growth/decline; blue/orange = comparison groups."
        )

PAGES[choice]()
