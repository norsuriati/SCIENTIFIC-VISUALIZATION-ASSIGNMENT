"""Malaysia: Income, Prices & Population - Cost-of-Living Pressure by State
JIE42403 Scientific Visualisation.  Run:  streamlit run streamlit_app.py
Libraries: streamlit, plotly, pandas, numpy, scipy (+ analysis.py for all calculations)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

import analysis as A

st.set_page_config(page_title="Malaysia Cost-of-Living Pressure", page_icon="📊", layout="wide")

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SEQ = [[0, "#cde2fb"], [0.25, "#6da7ec"], [0.5, "#2a78d6"], [0.75, "#184f95"], [1, "#0d366b"]]
DIV = [[0, "#2a78d6"], [0.5, "#e9e8e4"], [1, "#eb6834"]]          # blue - grey - orange


@st.cache_data
def get_data():
    pop, inc, cpi = A.load()
    m = A.state_metrics(inc, cpi, pop)
    return pop, inc, cpi, m, A.income_panel(inc, cpi)


pop, inc, cpi, M, P = get_data()
M["label"] = [A.short(s) for s in M.index]


def style(fig, h=400, **kw):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2), **kw)
    return fig


def card(label, value, sub=""):
    st.caption(label)
    st.markdown(f"#### {value}")
    if sub:
        st.caption(sub)


def bubble_map(color, title, size=None):
    """Geospatial bubble map: one bubble per state."""
    sz = np.sqrt(size) * 1.1 + 4 if size is not None else 22
    f = go.Figure(go.Scattergeo(
        lat=[A.COORDS[s][0] for s in M.index], lon=[A.COORDS[s][1] for s in M.index], text=M.label,
        marker=dict(size=sz, color=color, colorscale=SEQ, showscale=True, colorbar=dict(title=title),
                    line=dict(width=1, color="white"), opacity=0.9),
        customdata=np.c_[M.pop_end, M.inc_med_end, M.cpi_growth, M.real_med_idx],
        hovertemplate="<b>%{text}</b><br>Population %{customdata[0]:,.0f}k<br>Median income RM%{customdata[1]:,.0f}"
                      "<br>Price growth %{customdata[2]:.1f}%<br>Real income index %{customdata[3]:.0f}<extra></extra>"))
    f.update_geos(fitbounds="locations", showcountries=True, showland=True, landcolor="#e9e8e4",
                  countrycolor="#9a9992", showocean=True, oceancolor="#dbe9f9", resolution=50)
    return f


# ------------------------------------------------------------------ sidebar
st.sidebar.title("📊 Cost of Living in Malaysia")
page = st.sidebar.radio("Objective", ["1 · Income vs Prices", "2 · Population & Cost of Living", "3 · Pressure Drivers & Index"])
measure = st.sidebar.radio("Income measure", ["Median", "Mean"], help="Median is less distorted by high earners.")
st.sidebar.caption(f"**Data:** DOSM household income, state CPI (2010=100), state population. Income and CPI are compared over "
                   f"{A.BASE_YEAR}–{A.END_YEAR} ({', '.join(map(str, A.SURVEY_YEARS))}); CPI = annual average of the survey year.")
st.sidebar.caption("⚠️ CPI is an index (2010 = 100 in every state): it shows how fast prices *rose*, not which state is *more expensive* in RM.")

col = "median" if measure == "Median" else "mean"
inc_growth = M["inc_med_growth"] if col == "median" else M["inc_mean_growth"]
real_idx = P.pivot(index="state", columns="year", values=f"real_{col}_idx")
real_end = real_idx[A.END_YEAR]
gap = inc_growth - M["cpi_growth"]

# ================================================================== PAGE 1
if page.startswith("1"):
    st.title("Objective 1 · Income vs Prices")
    st.markdown("**To compare income growth and price growth in each state** "
                "*(to identify which states became more affordable and which are falling behind).*")
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("States where income beat prices", f"{(gap > 0).sum()} / {len(gap)}")
        with c[1]: card(f"Avg {col} income growth", f"{inc_growth.mean():.0f}%", f"vs prices +{M.cpi_growth.mean():.0f}%")
        with c[2]: card("Best real gain", A.short(real_end.idxmax()), f"real income ×{real_end.max()/100:.2f}")
        with c[3]: card("Weakest real gain", A.short(real_end.idxmin()), f"real income ×{real_end.min()/100:.2f}")
        with c[4]: card("Highest price growth", A.short(M.cpi_growth.idxmax()), f"+{M.cpi_growth.max():.0f}%")

    v1, v2 = st.columns(2)
    with v1:
        st.markdown("##### ① Line chart: income vs prices over time (2012 = 100)")
        s = st.selectbox("State", list(M.index), index=list(M.index).index("Selangor"), format_func=A.short)
        g = P[P.state == s]
        f = go.Figure()
        f.add_trace(go.Scatter(x=g.year, y=g[f"{col}_idx"], name=f"{measure} income", mode="lines+markers",
                               line=dict(color=BLUE, width=2), marker=dict(size=8)))
        f.add_trace(go.Scatter(x=g.year, y=g.cpi, name="Consumer prices (CPI)", mode="lines+markers",
                               line=dict(color=ORANGE, width=2), marker=dict(size=8)))
        f.add_hline(y=100, line_dash="dot", line_color="grey")
        f.update_yaxes(title="Index (2012 = 100)")
        f.update_xaxes(title="Survey year", dtick=2)
        st.plotly_chart(style(f, 420, hovermode="x unified"))
    with v2:
        st.markdown("##### ② Bar chart: growth 2012→2024 by state")
        d = pd.DataFrame({"inc": inc_growth, "cpi": M.cpi_growth, "gap": gap}).sort_values("gap")
        names = [A.short(i) for i in d.index]
        f = go.Figure()
        f.add_trace(go.Bar(y=names, x=d.cpi, name="Prices (CPI)", orientation="h", marker_color=ORANGE))
        f.add_trace(go.Bar(y=names, x=d.inc, name=f"{measure} income", orientation="h", marker_color=BLUE))
        f.update_layout(barmode="group", bargap=0.25)
        f.update_xaxes(title="% change 2012→2024")
        st.plotly_chart(style(f, 520))
    st.markdown("##### ③ Map: real-income index 2024 (income growth after removing price rises; 100 = no change)")
    st.plotly_chart(style(bubble_map(real_end.reindex(M.index), "Real income<br>index"), 460))
    with st.expander("Interpretation / Discussion", expanded=True):
        hi, lo = real_end.idxmax(), real_end.idxmin()
        st.markdown(f"""
* **Incomes outran prices everywhere (②).** Every state's {col} income grew faster than its prices, so real purchasing power rose by
  {real_end.min()-100:.0f}% to {real_end.max()-100:.0f}%. Strongest: **{A.short(hi)}** (×{real_end.max()/100:.2f}); weakest: **{A.short(lo)}** (×{real_end.min()/100:.2f}).
* **Fast inflation does not automatically mean poor affordability (①, ②).** Selangor and Putrajaya had the highest price growth (+{M.cpi_growth['Selangor']:.0f}%, +{M.cpi_growth['W.P. Putrajaya']:.0f}%),
  yet Selangor's real income still rose ×{real_end['Selangor']/100:.2f}; Putrajaya is the exception (×{real_end['W.P. Putrajaya']/100:.2f}) because its income grew modestly.
* **Who is falling behind (③).** The palest bubbles (Putrajaya, Negeri Sembilan, Labuan, Pahang) gained least; Terengganu and Perlis gained most. The 2020 dip (COVID-19) is visible in ① — real income fell about 10% in most states before recovering by 2022–2024.
* **Caveat.** Low-base states (Terengganu, Perlis) show big percentage gains partly because their 2012 income was low, and growth says nothing about the *level* of affordability. Rankings are sensitive to the base year (rank correlation 0.58 between 2012 and 2014 bases), though the extremes hold.""")

# ================================================================== PAGE 2
elif page.startswith("2"):
    st.title("Objective 2 · Population and Cost of Living")
    st.markdown("**To examine whether states with more people also have higher income and prices** "
                "*(to find where cost-of-living pressure is greatest).*")
    ymap = {"Median household income 2024 (RM)": "inc_med_end", "Price growth 2012→2024 (%)": "cpi_growth",
            "Real median income index 2024": "real_med_idx", "Population growth 2012→2024 (%)": "pop_growth"}
    ylab = st.selectbox("Compare population size (2024) with…", list(ymap))
    yv = ymap[ylab]
    rho, prho = stats.spearmanr(M.pop_end, M[yv])
    top3 = M.pop_end.nlargest(3)
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Population 2024", f"{M.pop_end.sum()/1000:.1f} M", f"+{(M.pop_end.sum()/M.pop_base.sum()-1)*100:.0f}% since 2012")
        with c[1]: card("Top-3 share", f"{top3.sum()/M.pop_end.sum()*100:.0f}%", ", ".join(A.short(i) for i in top3.index))
        with c[2]: card("Correlation ρ (selected)", f"{rho:+.2f}", f"p = {prho:.2f}")
        with c[3]: card("Fastest-growing", A.short(M.pop_growth.idxmax()), f"+{M.pop_growth.max():.0f}%")
        with c[4]: card("Highest dependency ratio", A.short(M.dep_ratio.idxmax()), f"{M.dep_ratio.max():.0f} per 100 workers")

    v1, v2 = st.columns(2)
    with v1:
        st.markdown("##### ① Scatter plot: population size vs selected indicator")
        x = np.log10(M.pop_end)
        b = np.polyfit(x, M[yv], 1)
        xs = np.linspace(x.min(), x.max(), 50)
        f = go.Figure()
        f.add_trace(go.Scatter(x=M.pop_end, y=M[yv], mode="markers+text", text=M.label, textposition="top center", name="State",
                               marker=dict(size=13, color=M.cpi_growth, colorscale=SEQ, showscale=True,
                                           colorbar=dict(title="Price<br>growth %"), line=dict(width=1.5, color="white")),
                               hovertemplate="%{text}<br>Pop %{x:,.0f}k<br>" + ylab + " %{y:,.1f}<extra></extra>"))
        f.add_trace(go.Scatter(x=10 ** xs, y=np.polyval(b, xs), mode="lines", line=dict(color=ORANGE, dash="dash"), name="Trend"))
        f.update_xaxes(type="log", title="Population 2024 ('000, log scale)")
        f.update_yaxes(title=ylab)
        st.plotly_chart(style(f, 460))
    with v2:
        st.markdown("##### ② Bar chart: population growth vs price growth 2012→2024")
        d = M.sort_values("pop_growth")
        names = list(d.label)
        f = go.Figure()
        f.add_trace(go.Bar(y=names, x=d.cpi_growth, name="Price growth %", orientation="h", marker_color=ORANGE))
        f.add_trace(go.Bar(y=names, x=d.pop_growth, name="Population growth %", orientation="h", marker_color=BLUE))
        f.update_layout(barmode="group", bargap=0.25)
        f.update_xaxes(title="% change 2012→2024")
        st.plotly_chart(style(f, 560))
    st.markdown("##### ③ Map: bubble = population 2024, colour = price growth 2012→2024")
    st.plotly_chart(style(bubble_map(M.cpi_growth, "Price<br>growth %", size=M.pop_end), 480))
    with st.expander("Interpretation / Discussion", expanded=True):
        r1 = stats.spearmanr(M.pop_end, M.inc_med_end); r2 = stats.spearmanr(M.pop_end, M.cpi_growth)
        r3 = stats.spearmanr(M.pop_growth, M.cpi_growth); r4 = stats.spearmanr(M.inc_med_end, M.cpi_growth)
        st.markdown(f"""
* **More people does not mean higher income or prices (①, ③).** Population size is essentially unrelated to median income
  (ρ = {r1[0]:+.2f}, p = {r1[1]:.2f}) and only weakly to price growth (ρ = {r2[0]:+.2f}, p = {r2[1]:.2f}). Sabah and Perak are populous but have low incomes, whereas
  KL, Putrajaya and Labuan are small yet among the richest.
* **What does move together (①, ②).** Richer states saw faster price rises (income level vs price growth ρ = {r4[0]:+.2f}, p = {r4[1]:.3f}), and states whose population grew faster also saw faster price growth
  (ρ = {r3[0]:+.2f}, p = {r3[1]:.2f}). This points to urban demand and wage levels, rather than head-count, as the source of price pressure.
* **Where pressure is greatest (③).** The Klang Valley (Selangor holds ≈{M.pop_share['Selangor']:.0f}% of Malaysians) combines large or fast-growing populations with high price growth: Putrajaya +{M.cpi_growth['W.P. Putrajaya']:.0f}%, Selangor +{M.cpi_growth['Selangor']:.0f}%,
  then Johor +{M.cpi_growth['Johor']:.0f}%, Penang +{M.cpi_growth['Pulau Pinang']:.0f}% and KL +{M.cpi_growth['W.P. Kuala Lumpur']:.0f}%. Kelantan and Terengganu have the highest dependency ratios (≈{M.dep_ratio['Kelantan']:.0f} and {M.dep_ratio['Terengganu']:.0f} dependants per 100 workers).
* **Caveat.** n = 16 states, so only the income–price link is clearly significant; Putrajaya (population recorded from 2010) is an outlier; correlation is not causation.""")

# ================================================================== PAGE 3
else:
    st.title("Objective 3 · Pressure Drivers & Index")
    st.markdown("**To identify which spending categories, such as food, housing and transport, push prices up the most** "
                "*(to rank states by overall cost-of-living pressure).*")
    y0, y1 = st.select_slider("Period for category price change (annual-average CPI)", options=list(range(2010, 2026)), value=(2012, 2024))
    DG = A.division_growth(cpi, y0, y1)
    nat = DG.mean().sort_values()
    st.sidebar.markdown("**Pressure-index weights**")
    w = {k: st.sidebar.slider(k, 0, 5, 1) for k in ["Price growth", "Real-income shortfall", "Low income level", "Population growth"]}
    if sum(w.values()) == 0:
        st.sidebar.warning("All weights are 0 — using equal weights.")
        w = {k: 1 for k in w}
    comp, contrib, idx = A.pressure_index(M, w)
    idx = idx.sort_values(ascending=False)
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Highest pressure", A.short(idx.index[0]), f"index {idx.iloc[0]:.0f}/100")
        with c[1]: card("Lowest pressure", A.short(idx.index[-1]), f"index {idx.iloc[-1]:.0f}/100")
        with c[2]: card("Fastest-rising category", nat.index[-1].split(" &")[0], f"avg +{nat.iloc[-1]:.0f}% ({y0}→{y1})")
        with c[3]: card("Food & Beverages", f"+{nat['Food & Beverages']:.0f}%", f"Housing +{nat['Housing & Utilities']:.0f}%")
        with c[4]: card("Latest inflation (Sep 2026)", f"{A.yoy(cpi).iloc[-1].mean():.1f}% YoY", "average of 16 states")

    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f"##### ① Bar chart: average price change by category, {y0}→{y1}")
        f = go.Figure(go.Bar(y=list(nat.index), x=nat.values, orientation="h",
                             marker_color=[ORANGE if v >= 0 else BLUE for v in nat.values],
                             hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>"))
        f.update_xaxes(title="% change (average of 16 states)")
        st.plotly_chart(style(f, 500))
    with v2:
        st.markdown("##### ② Stacked bar: Cost-of-Living Pressure Index (0–100)")
        f = go.Figure()
        for k, colr in zip(contrib.columns, [BLUE, ORANGE, AQUA, YELLOW]):
            f.add_trace(go.Bar(y=[A.short(s) for s in idx.index], x=contrib.loc[idx.index, k], name=k, orientation="h",
                               marker_color=colr, hovertemplate=k + ": %{x:.1f}<extra></extra>"))
        f.update_layout(barmode="stack", bargap=0.25)
        f.update_yaxes(autorange="reversed")
        f.update_xaxes(title="Index (higher = more pressure)")
        st.plotly_chart(style(f, 500))
    st.markdown(f"##### ③ Heatmap: price change by category and state, {y0}→{y1} (%)")
    order = DG.loc[:, DG.mean().sort_values(ascending=False).index]
    f = go.Figure(go.Heatmap(z=order.values, x=list(order.columns), y=[A.short(s) for s in order.index], colorscale=DIV, zmid=0,
                             text=np.round(order.values, 0), texttemplate="%{text:.0f}", colorbar=dict(title="% chg"),
                             hovertemplate="%{y} · %{x}<br>%{z:.1f}%<extra></extra>"))
    f.update_xaxes(tickangle=-35)
    f.update_yaxes(autorange="reversed")
    st.plotly_chart(style(f, 520))
    with st.expander("Interpretation / Discussion", expanded=True):
        fo = DG["Food & Beverages"].sort_values()
        top = nat.index[::-1]
        st.markdown(f"""
* **A few categories drive most of the rise (①).** On average the biggest increases were **{top[0]}** (+{nat[top[0]]:.0f}%), **{top[1]}** (+{nat[top[1]]:.0f}%) and **{top[2]}** (+{nat[top[2]]:.0f}%) ({y0}→{y1}),
  while categories such as Information & Communication and Clothing & Footwear fell (default 2012→2024 window) — consumers gained there.
* **Food pressure differs by state (③).** Food & Beverages rose from +{fo.iloc[0]:.0f}% in {A.short(fo.index[0])} to +{fo.iloc[-1]:.0f}% in {A.short(fo.index[-1])}; essentials rose most in the Klang Valley (Putrajaya, Selangor) and in Penang and Johor.
* **The index ranks states (②).** At current weights **{A.short(idx.index[0])}**, **{A.short(idx.index[1])}** and **{A.short(idx.index[2])}** face the highest pressure and **{A.short(idx.index[-1])}** the lowest. The coloured stacks show *why*: Putrajaya is driven by population growth and a weak real-income gain, Kelantan by low income level.
  Move the sidebar sliders to test sensitivity — Terengganu stays at or near the bottom and Putrajaya / Negeri Sembilan near the top under most weightings, but the middle ranks reshuffle.
* **Caveat.** The index is relative (rank-based) across 16 states, not an absolute poverty measure, and it uses price *growth*, not price levels.""")

st.caption("Sources: Department of Statistics Malaysia (DOSM) – household income, CPI by state, population by state. JIE42403 Scientific Visualisation assignment.")
