"""Malaysia Cost-of-Living Dashboard (JIE42403 Scientific Visualisation)
Data: OpenDOSM (Population, Household Income, Consumer Price Index) merged by state and year.
Run:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import calc

# ---------------------------------------------------------------- setup
st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

TEAL, AMBER, INK, MUTED = "#0F766E", "#F59E0B", "#0F172A", "#64748B"
FONT = "Inter, Segoe UI, Arial, sans-serif"
PLOT_CFG = {"displayModeBar": False}

STATE_SHORT = {
    "W.P. Kuala Lumpur": "KL",
    "W.P. Putrajaya": "Putrajaya",
    "W.P. Labuan": "Labuan",
    "Pulau Pinang": "Penang",
    "Negeri Sembilan": "N. Sembilan",
}


def short_state(s: str) -> str:
    return STATE_SHORT.get(s, s)


st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1250px;}
      h1 {font-size: 1.9rem !important; margin-bottom: 0.2rem;}
      .objective {background: #E6F4F1; border-left: 5px solid #0F766E; padding: 0.9rem 1.1rem;
                  border-radius: 8px; font-size: 1.05rem; color: #0F172A; margin: 0.6rem 0 1.2rem 0;}
      .objective b {color: #0F766E;}
      [data-testid="stMetricLabel"] p {font-size: 0.85rem; color: #64748B;}
      [data-testid="stMetricValue"] {font-size: 1.6rem;}
      .small {color: #64748B; font-size: 0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data() -> pd.DataFrame:
    return calc.load_data(str(Path(__file__).parent / "merged_dataset.csv"))


df = get_data()
YEARS = sorted(df["year"].unique().tolist())


def show(fig: go.Figure) -> None:
    """Draw a Plotly chart full-width (works on old and new Streamlit versions)."""
    try:
        st.plotly_chart(fig, width="stretch", config=PLOT_CFG)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)


def style(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        template="plotly_white",
        font=dict(family=FONT, size=13, color=INK),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_size=13),
    )
    return fig


def metric_row(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        with col.container(border=True):
            st.metric(label, value, help=help_text)


def period_picker(key: str):
    y0, y1 = st.select_slider(
        "Period to compare (survey years)",
        options=YEARS,
        value=(YEARS[0], YEARS[-1]),
        key=key,
    )
    if y0 == y1:
        st.info("Please choose two different years to compare.")
        st.stop()
    return y0, y1


def strength(r: float) -> str:
    a = abs(r)
    return "almost no" if a < 0.2 else "a weak" if a < 0.4 else "a moderate" if a < 0.6 else "a strong"


def names(series, n=3):
    return ", ".join(short_state(s) for s in list(series)[:n])


# ---------------------------------------------------------------- sidebar
st.sidebar.title("📊 Cost of Living")
st.sidebar.caption("Malaysia · by state · 2012–2024")
page = st.sidebar.radio(
    "Choose an objective",
    ["1 · Income vs Prices", "2 · Population & Prices", "3 · What Drives Prices"],
    label_visibility="collapsed",
)
st.sidebar.divider()
with st.sidebar.expander("About the data"):
    st.markdown(
        """
        **Source:** OpenDOSM (Department of Statistics Malaysia)
        - Population by state
        - Household income by state (mean, median)
        - Consumer Price Index (CPI) by state and category

        **How it was prepared**
        - Joined by *state* and *year* (16 states, 7 survey years)
        - Monthly CPI averaged into yearly values
        - CPI base: 2010 = 100
        - Population is in thousands
        """
    )

st.title("Can Malaysians keep up with the cost of living?")

# ---------------------------------------------------------------- page 1
if page.startswith("1"):
    st.markdown(
        '<div class="objective"><b>Objective 1.</b> Compare income growth and price growth in each state, '
        "to see which states became more affordable and which are falling behind.</div>",
        unsafe_allow_html=True,
    )
    y0, y1 = period_picker("p1")
    g = calc.growth_table(df, y0, y1).sort_values("real_growth", ascending=False)
    best, worst = g.iloc[0], g.iloc[-1]

    metric_row(
        [
            ("Average income growth", f"+{g.income_growth.mean():.0f}%", "Average of all 16 states, mean household income."),
            ("Average price growth", f"+{g.price_growth.mean():.0f}%", "Average rise in overall CPI."),
            ("Most affordable gain", short_state(best.state), f"Real income change of {best.real_growth:+.0f}% after prices."),
            ("Falling behind", short_state(worst.state), f"Real income change of only {worst.real_growth:+.0f}% after prices."),
        ]
    )

    states = [short_state(s) for s in g.state]
    fig = go.Figure()
    fig.add_bar(y=states, x=g.income_growth, name="Income growth", orientation="h",
                marker_color=TEAL, text=[f"+{v:.0f}%" for v in g.income_growth], textposition="outside")
    fig.add_bar(y=states, x=g.price_growth, name="Price growth", orientation="h",
                marker_color=AMBER, text=[f"+{v:.0f}%" for v in g.price_growth], textposition="outside")
    fig.update_layout(barmode="group", bargap=0.25)
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title=f"Growth from {y0} to {y1} (%)", range=[0, g.income_growth.max() * 1.15])
    st.subheader(f"Income growth vs price growth, {y0}–{y1}")
    st.caption("States are ranked by real income growth (income growth after removing price rises). Best at the top.")
    show(style(fig, 640))

    n_pos = int((g.real_growth > 0).sum())
    outcome = (
        "so households became better off in real terms."
        if n_pos == len(g)
        else f"so in {len(g) - n_pos} {'state' if len(g) - n_pos == 1 else 'states'} households lost purchasing power."
    )
    with st.container(border=True):
        st.markdown("**What the chart shows**")
        st.markdown(
            f"- Between {y0} and {y1}, income changed by **{g.income_growth.mean():+.0f}%** on average while prices changed by "
            f"**{g.price_growth.mean():+.0f}%**. Income grew faster than prices in **{n_pos} of {len(g)}** states, {outcome}\n"
            f"- The strongest real income change is in **{names(g.state, 3)}** ({g.real_growth.iloc[:3].min():+.0f}% to "
            f"{g.real_growth.iloc[0]:+.0f}%).\n"
            f"- The weakest are **{names(g.state[::-1], 3)}**. **{short_state(worst.state)}** is furthest behind, with real income "
            f"changing by only {worst.real_growth:+.0f}%."
        )

# ---------------------------------------------------------------- page 2
elif page.startswith("2"):
    st.markdown(
        '<div class="objective"><b>Objective 2.</b> Examine whether states with more people also have higher '
        "income and prices, to find where cost-of-living pressure is greatest.</div>",
        unsafe_allow_html=True,
    )
    year = st.select_slider("Year", options=YEARS, value=YEARS[-1], key="p2")
    t = calc.population_table(df, year)
    r_inc = t["population"].corr(t["income_mean"], method="spearman")
    r_cpi = t["population"].corr(t["cpi"], method="spearman")
    r_ic = t["income_mean"].corr(t["cpi"], method="spearman")
    top_inc = t.sort_values("income_mean", ascending=False)
    top_pop = t.sort_values("population", ascending=False)

    metric_row(
        [
            ("Most populous state", short_state(top_pop.iloc[0].state), f"{top_pop.iloc[0].population / 1000:.1f} million people."),
            ("Highest income", short_state(top_inc.iloc[0].state), f"RM {top_inc.iloc[0].income_mean:,.0f} mean monthly household income."),
            ("Population vs income", f"r = {r_inc:+.2f}", "Rank correlation. 0 = no link, 1 = perfect link."),
            ("Income vs prices", f"r = {r_ic:+.2f}", "Rank correlation. Higher-income states tend to have higher prices."),
        ]
    )

    fig = go.Figure(
        go.Scatter(
            x=t.population, y=t.income_mean, mode="markers+text",
            text=[short_state(s) for s in t.state], textposition="top center", textfont=dict(size=11, color=INK),
            marker=dict(size=17, color=t.cpi, colorscale="YlOrRd", line=dict(color="white", width=1.5),
                        colorbar=dict(title="Price level<br>(CPI, 2010=100)", thickness=14)),
            customdata=t[["cpi"]],
            hovertemplate="<b>%{text}</b><br>Population: %{x:,.0f}k<br>Income: RM %{y:,.0f}<br>CPI: %{customdata[0]:.1f}<extra></extra>",
        )
    )
    fig.update_xaxes(
        type="log", title="Population (log scale)",
        tickvals=[100, 250, 500, 1000, 2500, 5000], ticktext=["0.1M", "0.25M", "0.5M", "1M", "2.5M", "5M"],
    )
    fig.update_yaxes(title="Mean monthly household income (RM)", tickformat=",", rangemode="tozero")
    st.subheader(f"Population, income and prices by state, {year}")
    st.caption("Each dot is a state. Darker colour = higher prices.")
    show(style(fig, 600))

    with st.container(border=True):
        st.markdown("**What the chart shows**")
        st.markdown(
            f"- Population size has **{strength(r_inc)} link** with income (r = {r_inc:+.2f}) and "
            f"**{strength(r_cpi)} link** with prices (r = {r_cpi:+.2f}). "
            + ("Having more people does not make a state richer or costlier.\n" if max(abs(r_inc), abs(r_cpi)) < 0.4
               else "States with more people tend to differ in income and prices.\n")
            + f"- Income and prices {'**move together**' if r_ic > 0.4 else 'are only loosely linked'} (r = {r_ic:+.2f}): the highest-income states "
            f"(**{names(top_inc.state, 3)}**) have prices of {top_inc.cpi.iloc[:3].min():.0f}–{top_inc.cpi.iloc[:3].max():.0f} on the CPI scale, "
            f"compared with {t.cpi.median():.0f} for the typical state.\n"
            f"- Pressure is greatest where prices are high but income is not: look for dark dots that sit low on the chart. "
            f"Compare the most populous states (**{names(top_pop.state, 3)}**) to see that size alone does not set income."
        )

# ---------------------------------------------------------------- page 3
else:
    st.markdown(
        '<div class="objective"><b>Objective 3.</b> Identify which spending categories, such as food, housing '
        "and transport, push prices up the most, to rank states by overall cost-of-living pressure.</div>",
        unsafe_allow_html=True,
    )
    y0, y1 = period_picker("p3")
    c = calc.category_growth(df, y0, y1)
    cats = c.drop(columns=calc.OVERALL).mean().sort_values(ascending=False)
    top_cat, low_cat = cats.index[0], cats.index[-1]
    food = cats.get("Food & Beverages", float("nan"))

    metric_row(
        [
            ("Highest pressure state", short_state(c.index[0]), f"Overall prices up {c[calc.OVERALL].iloc[0]:.0f}%."),
            ("Lowest pressure state", short_state(c.index[-1]), f"Overall prices up {c[calc.OVERALL].iloc[-1]:.0f}%."),
            ("Fastest-rising category", calc.SHORT[top_cat], f"Up {cats.iloc[0]:.0f}% on average across states."),
            ("Slowest category", calc.SHORT[low_cat], f"Changed {cats.iloc[-1]:+.0f}% on average across states."),
        ]
    )

    z = c.values
    zmax = float(abs(z).max())
    xlabels = ["Overall"] + [calc.SHORT[x] for x in c.columns[1:]]
    ylabels = [short_state(s) for s in c.index]
    fig = go.Figure(
        go.Heatmap(
            z=z, x=xlabels, y=ylabels, zmin=-zmax, zmax=zmax, colorscale="RdBu_r", xgap=2, ygap=2,
            colorbar=dict(title="Price growth (%)", thickness=14),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:+.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        annotations=[
            dict(x=xlabels[j], y=ylabels[i], text=f"{z[i][j]:.0f}", showarrow=False, font=dict(
                size=11, color="white" if abs(z[i][j]) > 0.55 * zmax else INK))
            for i in range(z.shape[0]) for j in range(z.shape[1])
        ]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top", tickangle=-35)
    fig.add_shape(type="line", xref="x", yref="paper", x0=0.5, x1=0.5, y0=0, y1=1, line=dict(color=INK, width=2))
    st.subheader(f"Price growth by state and spending category, {y0}–{y1}")
    st.caption("Numbers are % price growth. States are ranked by overall pressure, highest at the top. "
               "Red = prices rose, blue = prices fell.")
    fig = style(fig, 700)
    fig.update_layout(margin=dict(l=10, r=10, t=110, b=10))
    show(fig)

    with st.container(border=True):
        st.markdown("**What the chart shows**")
        st.markdown(
            f"- Across states, the fastest-rising categories are **{calc.SHORT[cats.index[0]]}** ({cats.iloc[0]:+.0f}%), "
            f"**{calc.SHORT[cats.index[1]]}** ({cats.iloc[1]:+.0f}%) and **{calc.SHORT[cats.index[2]]}** ({cats.iloc[2]:+.0f}%).\n"
            + (f"- **Food & Drink**, an everyday essential, changed {food:+.0f}% on average.\n"
               if "Food & Beverages" not in cats.index[:3] else "")
            + (f"- **{calc.SHORT[low_cat]}** changed {cats.iloc[-1]:+.0f}%, so not every price is going up.\n"
               if cats.iloc[-1] < -0.5 else f"- **{calc.SHORT[low_cat]}** changed the least ({cats.iloc[-1]:+.0f}%).\n")
            + f""
            f"- Overall pressure is highest in **{names(c.index, 3)}** and lowest in **{names(c.index[::-1], 3)}**."
        )
        st.caption("These are price changes per category. The chart does not show how much of a household budget each category takes.")

st.divider()
st.caption("Source: OpenDOSM — Population, Household Income and Consumer Price Index by state. JIE42403 Scientific Visualisation.")
