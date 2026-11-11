from pathlib import Path
import html
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analysis as calc

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

# Consistent design system: income = blue, prices = orange, falling prices = teal.
BG, INK, MUTED = "#F5F7FA", "#182230", "#667085"
TEAL, GRID, WHITE = "#147D73", "#E5EAF0", "#FFFFFF"
INCOME_BLUE, PRICE_ORANGE = "#2864E8", "#F05A0A"
MUTED_BLUE, MUTED_ORANGE = "#D9DEE5", "#E5E7EB"
FONT = "Inter, Aptos, Segoe UI, sans-serif"
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}
MAP_VERSION = "4"  # change this number to force the map file to be read again

st.markdown(f"""
<style>
.stApp {{ background:{BG}; color:{INK}; }}
.block-container {{ max-width:1460px; padding-top:1.35rem; padding-bottom:2.5rem; }}
[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {GRID}; }}
[data-testid="stSidebar"] > div:first-child {{ padding:1.35rem 1.05rem 1rem; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{font-size:1.18rem;letter-spacing:-.03em;}}
[data-testid="stSidebar"] hr {{ margin:.8rem 0; border-color:{GRID}; }}
[data-testid="stSidebar"] [data-testid="stRadio"] > label {{ font-size:.78rem; color:{MUTED}; font-weight:650; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label {{ font-size:.82rem; color:{MUTED}; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {{ min-height:2.55rem; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ font-size:.72rem; line-height:1.35; }}
h1,h2,h3 {{ color:{INK}; letter-spacing:-.035em; }}
h1 {{ font-size:2rem !important; font-weight:730 !important; margin-bottom:.1rem !important; }}
h2 {{ font-size:1.28rem !important; font-weight:680 !important; }}
p,label {{ color:{INK}; }}
.page-kicker {{ color:{TEAL}; font-size:.72rem; font-weight:750; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.35rem; }}
.objective-card {{ background:#FFFFFF; border:1px solid {GRID}; border-left:5px solid {TEAL}; border-radius:12px;
                   padding:.8rem 1.1rem; margin:.5rem 0 1.1rem; }}
.objective-label {{ color:{TEAL}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; }}
.objective-text {{ color:{INK}; font-size:1.02rem; margin-top:.15rem; }}
.filter-heading {{ color:{MUTED}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin:0 0 .2rem; }}
.kpi {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:13px 16px; min-height:152px; box-sizing:border-box; }}
.kpi-label {{ color:{MUTED}; font-size:.8rem; font-weight:650; line-height:1.25; }}
.kpi-value {{ color:{INK}; font-size:1.4rem; font-weight:740; line-height:1.2; margin:.2rem 0 .15rem; overflow-wrap:anywhere; }}
.kpi-sub {{ color:{MUTED}; font-size:.8rem; line-height:1.3; }}
[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:12px 15px; min-height:96px; }}
[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-size:.78rem; line-height:1.25; }}
[data-testid="stMetricValue"] {{ color:{INK}; font-size:1.42rem; font-weight:720; }}
div[data-testid="stPlotlyChart"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:13px; padding:0; overflow:hidden; }}
[data-testid="stRadio"] > div {{ gap:.55rem; }}
[data-testid="stRadio"] label {{ font-size:.88rem; }}
div[data-testid="stCaptionContainer"] p {{ color:{MUTED}; }}
hr {{ border-color:{GRID}; }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    return calc.load_data()


@st.cache_data
def get_geojson(path, state_names, version):
    return calc.load_geojson(path, list(state_names))


def find_geojson():
    here = Path(__file__).parent
    options = [here / "data" / "malaysia_states.geojson", here / "malaysia_states.geojson"]
    options += sorted(here.glob("*.geojson")) + sorted((here / "data").glob("*.geojson"))
    return next((p for p in options if p.exists()), None)


df = load()
YEARS = sorted(df.year.unique().tolist())
STATES = sorted(df.state.unique().tolist())


# ------------------------------------------------------------------ helpers
STATE_SHORT = {"W.P. Kuala Lumpur": "Kuala Lumpur", "W.P. Putrajaya": "Putrajaya",
               "W.P. Labuan": "Labuan", "Pulau Pinang": "Penang", "Negeri Sembilan": "Negeri Sembilan"}


def short_state(s):
    return STATE_SHORT.get(s, s)


def names(series, n=3):
    return ", ".join(short_state(s) for s in list(series)[:n])


def strength(r):
    a = abs(r)
    return "almost no" if a < 0.2 else "a weak" if a < 0.4 else "a moderate" if a < 0.6 else "a strong"


def show(fig):
    """Draw a Plotly chart full width (works on old and new Streamlit versions)."""
    try:
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


def show_clickable(fig, key, on_click):
    """Plotly chart where clicking a region calls on_click (plain chart on old Streamlit)."""
    for kwargs in ({"width": "stretch"}, {"use_container_width": True}):
        try:
            st.plotly_chart(fig, key=key, on_select=on_click, selection_mode="points",
                            config=PLOT_CONFIG, **kwargs)
            return
        except Exception:
            continue
    show(fig)


def chart_layout(fig, height=560):
    fig.update_layout(
        template="plotly_white", height=height, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family=FONT, color=INK, size=12),
        margin=dict(l=28, r=28, t=48, b=54),
        hoverlabel=dict(bgcolor="#17212B", font_color="#FFFFFF", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


def objective_banner(num, title, text):
    st.markdown(
        f'<div class="objective-card"><div class="objective-label">Objective {num} · {title}</div>'
        f'<div class="objective-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def cards(items):
    """Summary boxes. Each item is (label, big value, one plain-language line, tooltip)."""
    for col, (label, value, sub, hint) in zip(st.columns(len(items)), items):
        col.markdown(
            f'<div class="kpi" title="{html.escape(hint, quote=True)}">'
            f'<div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(str(value))}</div>'
            f'<div class="kpi-sub">{html.escape(sub)}</div></div>',
            unsafe_allow_html=True,
        )


def link_text(r):
    """Plain words for a correlation value."""
    a = abs(r)
    if a < 0.2:
        return "No clear link"
    word = "Weak" if a < 0.4 else "Moderate" if a < 0.6 else "Strong"
    return f"{word} {'positive' if r > 0 else 'negative'} link"


def gap_phrase(gap):
    return (f"Income grew {gap:.0f} points more than prices" if gap >= 0
            else f"Income fell {abs(gap):.0f} points behind prices")


def interpretation(bullets, note=None):
    with st.container(border=True):
        st.markdown("**Interpretation**")
        st.markdown("\n".join(f"- {b}" for b in bullets))
        if note:
            st.caption(note)


def income_picker():
    return st.selectbox("Income measure", ["Mean income", "Median income"], key="income_measure")


def top_list(frame, value_col, fmt, n=3):
    return ", ".join(f"**{short_state(r.state)}** ({fmt.format(getattr(r, value_col))})" for r in frame.head(n).itertuples())


# ------------------------------------------------------------------ sidebar
st.sidebar.markdown("## 📊 Cost of Living")
st.sidebar.caption("MALAYSIA")
st.sidebar.divider()
page = st.sidebar.radio(
    "PAGES",
    ["01  Income vs Price Growth", "02  Population, Income & Prices", "03  Cost-of-Living Drivers"],
)
st.sidebar.divider()
st.sidebar.markdown("### TIME PERIOD")
baseline = st.sidebar.selectbox("From year", YEARS[:-1], index=0, key="baseline_year")
to_options = [y for y in YEARS if y > baseline]  # the To year is always after the From year
if st.session_state.get("comparison_year") not in to_options:
    st.session_state.pop("comparison_year", None)
comparison = st.sidebar.selectbox("To year", to_options, index=len(to_options) - 1, key="comparison_year")
st.sidebar.caption(
    f"Growth is measured from {baseline} to {comparison}. "
    f"Page 02 shows the snapshot for {comparison}."
)
st.sidebar.divider()
with st.sidebar.expander("About the data"):
    st.markdown(
        """
**Source:** OpenDOSM (Department of Statistics Malaysia): Population, Household Income and Consumer Price Index by state.

**How it was prepared**
- Joined by state and year (16 states, survey years only)
- Monthly CPI averaged into yearly values (2010 = 100)
- Population is in thousands persons

**Limits**
- Income is nominal, not adjusted for inflation
- Category growth is an unweighted average, not budget-weighted
        """
    )

st.markdown('<div class="page-kicker">MALAYSIA · COST OF LIVING</div>', unsafe_allow_html=True)
st.title("Cost of Living Dashboard")

# =================================================================== PAGE 1
if page.startswith("01"):
    objective_banner(1, "Income vs Price Growth",
                     "Compare income growth and price growth in each state, "
                     "to see which states became more affordable and which are falling behind.")
    st.markdown('<div class="filter-heading">ANALYSIS FILTERS</div>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        income_label = income_picker()
    with f2:
        selected_states = st.multiselect("State", STATES, default=[],
                                         help="Highlight one or more states. Leave empty to show all. "
                                              "The summary boxes follow your selection.")
    measure_col = "income_mean" if income_label == "Mean income" else "income_median"

    growth_all = calc.growth_comparison(df, baseline, comparison, measure_col).sort_values("gap", ascending=False)
    growth = growth_all[growth_all.state.isin(selected_states)] if selected_states else growth_all
    if growth.empty:
        st.warning("No data available for this selection.")
        st.stop()

    avg_inc, avg_price, avg_gap = growth.income_growth.mean(), growth.price_growth.mean(), growth.gap.mean()
    n_beat = int((growth.gap > 0).sum())
    best, worst = growth.iloc[0], growth.iloc[-1]

    cards([
        ("Average income growth", f"{avg_inc:+.1f}%", f"{income_label} of households, {baseline} to {comparison}",
         "How much household income grew on average across the states."),
        ("Average price growth", f"{avg_price:+.1f}%", "Change in prices (Consumer Price Index)",
         "Growth in the overall Consumer Price Index (CPI)."),
        ("Income growth minus price growth", f"{avg_gap:+.1f} points",
         "Above zero = income grew faster than prices",
         "Income growth minus price growth, in percentage points."),
    ])
    cards([
        ("Highest gap (best off)", short_state(best.state), gap_phrase(best.gap),
         "The state where income grew furthest ahead of prices."),
        ("Lowest gap (most behind)", short_state(worst.state), gap_phrase(worst.gap),
         "The state where income grew least compared with prices."),
        ("States where income beat prices", f"{n_beat} of {len(growth)}",
         "Households there gained purchasing power" if n_beat else "No state gained purchasing power",
         "A positive gap means purchasing power improved."),
    ])

    chart = growth_all.copy()
    chart["label"] = chart.state.map(short_state)
    picked = set(selected_states)
    inc_colors = [INCOME_BLUE if (not picked or s in picked) else MUTED_BLUE for s in chart.state]
    price_colors = [PRICE_ORANGE if (not picked or s in picked) else MUTED_ORANGE for s in chart.state]
    hover_extra = chart[["real_growth", "gap"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=chart.label, x=chart.income_growth, orientation="h", name=f"{income_label} growth ({baseline}–{comparison})",
        marker_color=inc_colors, text=[f"{v:.0f}%" for v in chart.income_growth],
        textposition="outside", cliponaxis=False, customdata=hover_extra,
        hovertemplate="<b>%{y}</b><br>Change " + f"{baseline} to {comparison}" + "<br>Income growth: %{x:.1f}%<br>Real income growth: %{customdata[0]:+.1f}%"
                      "<br>Income–price gap: %{customdata[1]:+.1f} pp<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=chart.label, x=chart.price_growth, orientation="h", name=f"Price (CPI) growth ({baseline}–{comparison})",
        marker_color=price_colors, text=[f"{v:.0f}%" for v in chart.price_growth],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Change " + f"{baseline} to {comparison}" + "<br>Price growth: %{x:.1f}%<extra></extra>",
    ))
    hi = max(float(chart.income_growth.max()), float(chart.price_growth.max()), 0)
    lo = min(float(chart.income_growth.min()), float(chart.price_growth.min()), 0)
    height = max(590, 34 * len(chart) + 120)
    fig = chart_layout(fig, height)
    fig.update_layout(barmode="group", bargap=.25, bargroupgap=.08, legend_title="",
                      yaxis_title="", xaxis_title=f"Change from {baseline} to {comparison} (%)", margin=dict(l=28, r=65, t=55, b=45))
    fig.update_yaxes(categoryorder="array", categoryarray=chart.label.tolist(), autorange="reversed",
                     tickfont=dict(size=11))
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                     range=[min(0, lo * 1.12), hi * 1.16 if hi > 0 else 1])
    st.subheader(f"Income and price growth by state · {baseline} to {comparison}")
    st.caption(f"Each bar shows how much it grew between {baseline} and {comparison}. "
               "States are ranked by the income–price gap, the most affordable at the top.")
    show(fig)

    ratio = (f" Income grew about {avg_inc / avg_price:.1f} times as fast as prices."
             if avg_price > 0 and avg_inc > 0 else "")
    n_list = min(3, max(1, len(growth) // 2))
    all_beat = n_beat == len(growth)
    interpretation([
        f"From {baseline} to {comparison}, {income_label.lower()} changed by **{avg_inc:+.0f}%** on average while prices "
        f"changed by **{avg_price:+.0f}%**.{ratio}",
        f"Income grew faster than prices in **{n_beat} of {len(growth)}** states"
        + (", so purchasing power improved everywhere." if all_beat
           else f", so in {len(growth) - n_beat} states households lost purchasing power."),
        (f"The most affordable states are {top_list(growth, 'gap', '{:+.0f} pp', n_list)}. "
         f"The states falling behind are {top_list(growth.iloc[::-1], 'gap', '{:+.0f} pp', n_list)}.")
        if all_beat else
        (f"The largest income–price gaps are in {top_list(growth, 'gap', '{:+.0f} pp', n_list)}. "
         f"The smallest are in {top_list(growth.iloc[::-1], 'gap', '{:+.0f} pp', n_list)}."),
        "A small or negative gap means income did not keep up with prices, so households have less room to absorb price rises.",
    ], note="Income is nominal (not adjusted for inflation). The gap is a simple approximation of real income growth; "
            "hover over a bar to see the exact real growth.")

# =================================================================== PAGE 2
elif page.startswith("02"):
    objective_banner(2, "Population, Income & Prices",
                     "Examine whether states with more people also have higher income and prices, "
                     "to find where cost-of-living pressure is greatest.")
    st.markdown('<div class="filter-heading">ANALYSIS FILTERS</div>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1:
        income_label = income_picker()
    with f2:
        selected_states = st.multiselect("State", STATES, default=[], key="obj2_states",
                                         help="Highlight one or more states. Leave empty to show all.")
    measure_col = "income_mean" if income_label == "Mean income" else "income_median"

    snap = calc.population_income_snapshot(df, comparison)
    if snap.empty:
        st.warning("No data available for this year.")
        st.stop()
    snap["label"] = snap.state.map(short_state)
    r_inc = calc.rank_corr(snap.population, snap[measure_col])
    r_cpi = calc.rank_corr(snap.population, snap.cpi)
    r_ic = calc.rank_corr(snap[measure_col], snap.cpi)
    top_pop = snap.sort_values("population", ascending=False)
    top_inc = snap.sort_values(measure_col, ascending=False)

    top_cpi = snap.sort_values("cpi", ascending=False)
    q = snap[(snap.cpi >= snap.cpi.median()) & (snap[measure_col] < snap[measure_col].median())].sort_values("cpi", ascending=False)
    if q.empty:
        pressure = ("None", "No state has high prices with below-average income")
    else:
        others = [short_state(s) for s in q.state.iloc[1:3]]
        pressure = (short_state(q.state.iloc[0]),
                    "High prices, lower income" + (f" (also {', '.join(others)})" if others else ""))

    cards([
        ("Highest income", short_state(top_inc.iloc[0].state), f"RM {top_inc.iloc[0][measure_col]:,.0f} per month",
         f"{income_label} household income in {comparison}."),
        ("Largest population", short_state(top_pop.iloc[0].state), f"{top_pop.iloc[0].population / 1000:.1f} million people",
         f"The state with the most people in {comparison}."),
        ("Highest prices", short_state(top_cpi.iloc[0].state), f"Prices {top_cpi.iloc[0].cpi - 100:.0f}% higher than in 2010",
         "Based on the Overall Consumer Price Index (2010 = 100)."),
        ("Most pressure on households", pressure[0], pressure[1],
         "States where prices are above the median but income is below the median."),
    ])

    picked = set(selected_states)
    focus = [(not picked) or s in picked for s in snap.state]
    fig = go.Figure(go.Scatter(
        x=snap.population, y=snap[measure_col], mode="markers+text", text=snap.label,
        textposition="top center", textfont=dict(size=10, color=INK),
        marker=dict(size=15, color=snap.cpi, colorscale=["#FDE6D6", "#F8A670", PRICE_ORANGE, "#B23A00"],
                    opacity=[0.95 if f else 0.3 for f in focus],
                    line=dict(color=[INK if (picked and f) else WHITE for f in focus], width=1.6),
                    colorbar=dict(title=f"Overall CPI<br>{comparison}<br>(2010 = 100)", thickness=13, len=.72)),
        customdata=snap[["cpi"]],
        hovertemplate="<b>%{text}</b><br>Population: %{x:,.0f} thousand persons<br>"
                      + income_label + ": RM %{y:,.0f} per month<br>Overall CPI: %{customdata[0]:.1f}<extra></extra>",
    ))
    pmin, pmax = float(snap.population.min()), float(snap.population.max())
    ticks = [t for t in (100, 250, 500, 1000, 2500, 5000) if pmin * 0.7 <= t <= pmax * 1.4]
    fig.update_xaxes(type="log", title=f"Population in {comparison} (log scale)", showgrid=True, gridcolor=GRID,
                     tickvals=ticks, ticktext=[f"{t / 1000:g}M" for t in ticks],
                     range=[math.log10(pmin * 0.7), math.log10(pmax * 1.4)])
    fig.update_yaxes(title=f"{income_label} monthly income in {comparison} (RM)", tickformat=",", showgrid=True,
                     gridcolor=GRID, rangemode="tozero")
    fig.update_layout(showlegend=False)
    st.subheader(f"Population, {income_label.lower()} and prices by state · {comparison}")
    st.caption("Each dot is a state. Darker orange = higher prices. Hover for exact values.")
    show(chart_layout(fig, 620))

    pop_range = top_inc.head(3).population
    interpretation([
        f"Population size has **{strength(r_inc)} link** with income (r = {r_inc:+.2f}) and **{strength(r_cpi)} link** "
        f"with prices (r = {r_cpi:+.2f}). "
        + ("Having more people does not make a state richer or more expensive." if max(abs(r_inc), abs(r_cpi)) < 0.4
           else "States with more people tend to differ in income and prices."),
        f"Income and prices are {'**closely linked**' if r_ic >= 0.6 else '**moderately linked**' if r_ic >= 0.4 else 'only loosely linked'} "
        f"(r = {r_ic:+.2f}): the highest-income states ({names(top_inc.state, 3)}) are also among the most expensive.",
        f"Those three states have very different populations, from {pop_range.min() / 1000:.1f} to {pop_range.max() / 1000:.1f} million. "
        "Their income is explained by their economy, not by their headcount.",
        "Pressure is greatest where prices are high but income is below the median: "
        + (f"**{names(q.state, 3)}**." if not q.empty else "no state falls in this group."),
    ], note="r is the Spearman rank correlation across the states (-1 to +1). Correlation shows a link, not a cause.")

# =================================================================== PAGE 3
else:
    objective_banner(3, "Cost-of-Living Drivers",
                     "Identify which spending categories, such as food, housing and transport, push prices up the most, "
                     "and rank states by overall cost-of-living pressure.")
    tbl = calc.category_growth_table(df, baseline, comparison)
    if tbl.empty:
        st.warning("No data available for this period.")
        st.stop()
    cat_avg = tbl.drop(columns=calc.OVERALL).mean().sort_values(ascending=False)
    state_list = list(tbl.index)
    rank = {s: i for i, s in enumerate(state_list, 1)}
    ALL = "All states (average)"
    key_to_state = {calc.norm(s): s for s in state_list}

    cards([
        ("Highest price rise (state)", short_state(state_list[0]), f"Overall prices up {tbl[calc.OVERALL].iloc[0]:.0f}%",
         "The state with the largest overall price growth."),
        ("Lowest price rise (state)", short_state(state_list[-1]), f"Overall prices up {tbl[calc.OVERALL].iloc[-1]:.0f}%",
         "The state with the smallest overall price growth."),
        ("Fastest-rising category", cat_avg.index[0], f"Prices up {cat_avg.iloc[0]:.0f}% on average",
         "Average of the 16 states, not weighted by spending."),
        ("Slowest-rising category", cat_avg.index[-1],
         (f"Prices fell {abs(cat_avg.iloc[-1]):.0f}% on average" if cat_avg.iloc[-1] < -0.5
          else f"Prices up only {cat_avg.iloc[-1]:.0f}% on average"),
         "Average of the 16 states, not weighted by spending."),
    ])

    def _on_map_click():
        """Clicking a state on the map selects it; the menu and the bar chart follow."""
        try:
            points = st.session_state["map3"]["selection"]["points"]
        except Exception:
            return
        for p in points:
            name = key_to_state.get(p.get("location"))
            if name is None and p.get("curve_number", 0) == 0 and p.get("point_index") is not None:
                name = state_list[p["point_index"]]
            if name:
                st.session_state["p3_state"] = name
                return

    if st.session_state.get("p3_state") not in [ALL] + state_list:
        st.session_state["p3_state"] = ALL

    # ---------- map of overall price pressure (click a state)
    st.subheader(f"Overall price growth by state · {baseline} to {comparison}")
    geo_path = find_geojson()
    gj, no_shape = None, []
    if geo_path is not None:
        try:
            gj, no_shape = get_geojson(str(geo_path), tuple(state_list), MAP_VERSION)
        except Exception as err:
            st.warning(f"Map file could not be read: {err}")
    if gj is None:
        st.info("Map file not found. Put a Malaysia states GeoJSON file (for example geoBoundaries-MYS-ADM1.geojson) "
                "in the same folder as app.py. You can still choose a state with the menu below.")
    else:
        use_tiles = st.session_state.get("map_mode", "Tile-free map") == "Tile-free map" and hasattr(go, "Choroplethmap")
        Choro = go.Choroplethmap if use_tiles else go.Choropleth
        common = dict(geojson=gj, featureidkey="properties.state_key")
        fig_map = go.Figure(Choro(
            locations=[calc.norm(s) for s in state_list], z=tbl[calc.OVERALL].values,
            text=[short_state(s) for s in state_list], colorscale="Oranges",
            marker_line_color="white", marker_line_width=1,
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
            colorbar=dict(title=f"Price growth<br>{baseline}–{comparison}<br>(%)", thickness=12, len=0.8),
            hovertemplate="<b>%{text}</b><br>Overall prices: %{z:+.0f}%<extra></extra>", **common,
        ))
        chosen = st.session_state["p3_state"]
        if chosen != ALL:  # dark outline around the chosen state
            fig_map.add_trace(Choro(
                locations=[calc.norm(chosen)], z=[0], showscale=False, hoverinfo="skip",
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                marker_line_color=INK, marker_line_width=3, **common,
            ))
        if use_tiles:
            center, zoom = calc.geo_view(gj)
            fig_map.update_layout(map=dict(style="white-bg", center=center, zoom=zoom))
        else:
            fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
        fig_map.update_layout(height=460, margin=dict(l=0, r=0, t=0, b=0), clickmode="event+select",
                              paper_bgcolor="#FFFFFF", font=dict(family=FONT, size=12, color=INK))
        st.caption("Click a state to see its spending categories below. Darker orange = prices rose more.")
        show_clickable(fig_map, "map3", _on_map_click)
        with st.expander("Map check"):
            st.write(f"File: {geo_path.name} · name field: {gj.get('state_property')} · "
                     f"{len(state_list) - len(no_shape)} of {len(state_list)} states matched · version {MAP_VERSION}")
            st.radio("Drawing mode (change this if the map looks wrong)", ["Tile-free map", "Classic geo map"],
                     key="map_mode", horizontal=True)
        if no_shape:
            st.caption("Not on the map file: " + ", ".join(short_state(s) for s in no_shape)
                       + ". Choose them from the menu below.")

    sel_col, rank_col = st.columns([1.4, 1])
    with sel_col:
        st.selectbox(
            "Selected state (click the map, or choose here)", [ALL] + state_list, key="p3_state",
            format_func=lambda s: s if s == ALL else f"{rank[s]}. {short_state(s)}  (overall {tbl.loc[s, calc.OVERALL]:+.0f}%)",
            help="States are ranked 1 = highest cost-of-living pressure (largest overall price growth). "
                 "Small areas such as Kuala Lumpur, Putrajaya and Labuan are easier to pick here.",
        )
    with rank_col:
        with st.expander("State ranking by overall price growth"):
            st.dataframe(
                pd.DataFrame({"Rank": range(1, len(state_list) + 1),
                              "State": [short_state(s) for s in state_list],
                              "Overall price growth": [f"{v:+.1f}%" for v in tbl[calc.OVERALL]]}),
                hide_index=True,
            )

    choice = st.session_state["p3_state"]
    if choice == ALL:
        vals, overall, label = cat_avg, float(tbl[calc.OVERALL].mean()), "all states (average)"
    else:
        vals = tbl.loc[choice].drop(calc.OVERALL).dropna().sort_values(ascending=False)
        overall, label = float(tbl.loc[choice, calc.OVERALL]), short_state(choice)

    # ---------- bar chart: which categories pushed prices up
    fig = go.Figure(go.Bar(
        y=vals.index.tolist(), x=vals.values, orientation="h",
        marker_color=[PRICE_ORANGE if v >= 0 else TEAL for v in vals.values],
        text=[f"{v:+.0f}%" for v in vals.values], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Price growth: %{x:+.1f}%<extra></extra>",
    ))
    fig.add_vline(x=overall, line_dash="dash", line_color=INK,
                  annotation_text=f"Overall {overall:+.0f}%", annotation_position="top right")
    fig.update_yaxes(categoryorder="array", categoryarray=vals.index.tolist(), autorange="reversed",
                     automargin=True)
    fig.update_xaxes(title=f"Price growth {baseline} to {comparison} (%)", ticksuffix="%", showgrid=True,
                     gridcolor=GRID, zeroline=True, zerolinecolor="#8793A1",
                     range=[min(0, float(vals.min())) - 8, float(vals.max()) * 1.15 + 6])
    fig = chart_layout(fig, 560)
    fig.update_layout(showlegend=False, bargap=.28, margin=dict(l=28, r=40, t=60, b=50))
    st.subheader(f"Spending categories driving prices · {label}")
    st.caption("Orange = prices rose, teal = prices fell. Bars past the dashed line rose faster than overall prices.")
    show(fig)

    top3 = ", ".join(f"**{k}** ({v:+.0f}%)" for k, v in cat_avg.head(3).items())
    low = cat_avg.index[-1]
    bullets = [
        f"Across states, the fastest-rising categories from {baseline} to {comparison} are {top3}.",
        (f"**{low}** changed {cat_avg.iloc[-1]:+.0f}%, so not every price is going up."
         if cat_avg.iloc[-1] < -0.5 else f"**{low}** changed the least ({cat_avg.iloc[-1]:+.0f}%)."),
        f"Ranking by overall price growth: highest pressure in {', '.join(f'**{short_state(s)}** ({tbl.loc[s, calc.OVERALL]:+.0f}%)' for s in state_list[:3])}; "
        f"lowest in {', '.join(f'**{short_state(s)}** ({tbl.loc[s, calc.OVERALL]:+.0f}%)' for s in state_list[::-1][:3])}.",
    ]
    if choice != ALL:
        bullets.append(f"In **{label}**, **{vals.index[0]}** rose the most ({vals.iloc[0]:+.0f}%) against overall prices of {overall:+.0f}%.")
    else:
        bullets.append("Click a state on the map to see which categories pushed its prices up.")
    interpretation(bullets, note="Category growth is a price change, not a share of household spending. "
                                 "The all-states figure is an unweighted average of the 16 states.")

st.divider()
st.caption("Source: OpenDOSM — Population, Household Income and Consumer Price Index by state. "
           "JIE42403 Scientific Visualisation.")
