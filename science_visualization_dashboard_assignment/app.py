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
.kpi {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:13px 16px; box-sizing:border-box; }}
.kpi-label {{ color:{MUTED}; font-size:.8rem; font-weight:650; line-height:1.25; }}
.kpi-value {{ color:{INK}; font-size:1.4rem; font-weight:740; line-height:1.2; margin:.2rem 0 .15rem; overflow-wrap:anywhere; }}
.kpi-sub {{ color:{MUTED}; font-size:.82rem; line-height:1.3; }}
.kpi-delta {{ font-size:.86rem; font-weight:680; line-height:1.3; margin-top:.2rem; }}
.legend-row {{ display:flex; gap:1.3rem; align-items:center; flex-wrap:wrap; font-size:.8rem; color:{MUTED}; margin:.1rem 0 .55rem; }}
.lg-item {{ display:inline-flex; align-items:center; gap:.4rem; }}
.lg-sw {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
.lg-grad {{ width:96px; height:10px; border-radius:5px; background:linear-gradient(90deg,#FDE6D6,#F8A670,{PRICE_ORANGE},#B23A00); display:inline-block; }}
.scale {{ width:340px; max-width:100%; margin:.1rem 0 .7rem; }}
.scale-title {{ font-size:.78rem; font-weight:650; color:{MUTED}; margin-bottom:.3rem; }}
.scale-bar {{ height:12px; border-radius:6px; background:linear-gradient(90deg,#FDE6D6,#F8A670,{PRICE_ORANGE},#B23A00); }}
.scale-labels {{ display:flex; justify-content:space-between; font-size:.78rem; color:{MUTED}; margin-top:.3rem; }}
.lg-dash {{ width:20px; border-top:2px dashed {INK}; display:inline-block; }}
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


TONES = {"income": INCOME_BLUE, "price": PRICE_ORANGE, "down": TEAL, "neutral": MUTED}


def delta(change, prev, tone):
    """('▲ +4.2% vs 2022', colour tone). A fall always uses the teal tone."""
    return f"{'▲' if change >= 0 else '▼'} {change:+.1f}% vs {prev}", ("down" if change < 0 else tone)


def cards(items, heading):
    """Summary boxes. Each item is (label, big value, detail line or None, change text, tone)."""
    st.markdown(f'<div class="filter-heading">{html.escape(heading)}</div>', unsafe_allow_html=True)
    for col, (label, value, detail, change, tone) in zip(st.columns(len(items)), items):
        extra = f'<div class="kpi-sub">{html.escape(detail)}</div>' if detail else ""
        col.markdown(
            f'<div class="kpi" style="min-height:118px">'
            f'<div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(str(value))}</div>{extra}'
            f'<div class="kpi-delta" style="color:{TONES[tone]}">{html.escape(change)}</div></div>',
            unsafe_allow_html=True,
        )


def legend_row(*items):
    """A small key above a chart. Items are ready-made HTML snippets."""
    st.markdown('<div class="legend-row">' + "".join(f'<span class="lg-item">{i}</span>' for i in items) + "</div>",
                unsafe_allow_html=True)


def scale_legend(title, low, mid, high):
    """Colour key: a gradient bar with three words underneath."""
    st.markdown(
        f'<div class="scale"><div class="scale-title">{html.escape(title)}</div><div class="scale-bar"></div>'
        f'<div class="scale-labels"><span>{html.escape(low)}</span><span>{html.escape(mid)}</span>'
        f'<span>{html.escape(high)}</span></div></div>', unsafe_allow_html=True)


def swatch(color, text):
    return f'<span class="lg-sw" style="background:{color}"></span>{text}'


def income_picker():
    return st.selectbox("Income measure", ["Mean income", "Median income"], key="income_measure")


# ------------------------------------------------------------------ sidebar
st.sidebar.markdown("## 📊 Cost of Living")
st.sidebar.caption("MALAYSIA")
st.sidebar.divider()
page = st.sidebar.radio(
    "PAGES",
    ["01  Income vs Price Growth", "02  Population, Income & Prices", "03  Cost-of-Living Drivers"],
)
st.sidebar.divider()
# One year choice for the whole dashboard. Growth (pages 01 and 03) is always measured from the first survey year.
baseline = YEARS[0]
st.sidebar.markdown("### YEAR")
comparison = st.sidebar.selectbox("Select year", YEARS[1:], index=len(YEARS[1:]) - 1, key="year_select")
if page.startswith("02"):
    st.sidebar.caption(f"Shows every state in {comparison}.")
else:
    st.sidebar.caption(f"Shows change from {baseline} (first survey year) to {comparison}.")
prev = max(y for y in YEARS if y < comparison)  # the survey year before the one selected
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
    f1, f2 = st.columns(2)
    with f1:
        income_label = income_picker()
    with f2:
        selected_states = st.multiselect("Highlight state", STATES, default=[],
                                         help="Highlight one or more states. Leave empty to show all. "
                                              "The summary boxes follow your selection.")
    measure_col = "income_mean" if income_label == "Mean income" else "income_median"

    growth_all = calc.growth_comparison(df, baseline, comparison, measure_col).sort_values("gap", ascending=False)
    step = calc.growth_comparison(df, prev, comparison, measure_col)  # latest step: previous survey year to selected year
    if selected_states:
        step = step[step.state.isin(selected_states)]
    if growth_all.empty or step.empty:
        st.warning("No data available for this selection.")
        st.stop()

    inc_up, inc_low = step.loc[step.income_growth.idxmax()], step.loc[step.income_growth.idxmin()]
    pr_up = step.loc[step.price_growth.idxmax()]
    low_label = "Income fell most" if inc_low.income_growth < 0 else "Income rose least"
    cards([
        ("Income rose most" if inc_up.income_growth >= 0 else "Income fell least", short_state(inc_up.state), None, *delta(inc_up.income_growth, prev, "income")),
        (low_label, short_state(inc_low.state), None, *delta(inc_low.income_growth, prev, "income")),
        ("Prices rose most" if pr_up.price_growth >= 0 else "Prices fell least", short_state(pr_up.state), None, *delta(pr_up.price_growth, prev, "price")),
    ], f"LATEST CHANGE · {prev} TO {comparison}")

    chart = growth_all.copy()
    chart["label"] = chart.state.map(short_state)
    picked = set(selected_states)
    inc_colors = [INCOME_BLUE if (not picked or s in picked) else MUTED_BLUE for s in chart.state]
    price_colors = [PRICE_ORANGE if (not picked or s in picked) else MUTED_ORANGE for s in chart.state]
    hover_extra = chart[["real_growth", "gap"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=chart.label, x=chart.income_growth, orientation="h", name=f"{income_label} growth",
        marker_color=inc_colors, text=[f"{v:.0f}%" for v in chart.income_growth],
        textposition="outside", cliponaxis=False, customdata=hover_extra,
        hovertemplate="<b>%{y}</b><br>Change " + f"{baseline} to {comparison}" + "<br>Income growth: %{x:.1f}%<br>Real income growth: %{customdata[0]:+.1f}%"
                      "<br>Income–price gap: %{customdata[1]:+.1f} pp<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=chart.label, x=chart.price_growth, orientation="h", name="Price (CPI) growth",
        marker_color=price_colors, text=[f"{v:.0f}%" for v in chart.price_growth],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Change " + f"{baseline} to {comparison}" + "<br>Price growth: %{x:.1f}%<extra></extra>",
    ))
    hi = max(float(chart.income_growth.max()), float(chart.price_growth.max()), 0)
    lo = min(float(chart.income_growth.min()), float(chart.price_growth.min()), 0)
    height = max(590, 34 * len(chart) + 120)
    fig = chart_layout(fig, height)
    fig.update_layout(barmode="group", bargap=.25, bargroupgap=.08, legend_title="",
                      yaxis_title="", xaxis_title=f"Growth since {baseline} (%)", margin=dict(l=28, r=65, t=55, b=45))
    fig.update_yaxes(categoryorder="array", categoryarray=chart.label.tolist(), autorange="reversed",
                     tickfont=dict(size=11))
    fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                     range=[min(0, lo * 1.12), hi * 1.16 if hi > 0 else 1])
    st.subheader(f"Income and price growth by state · {baseline} to {comparison}")
    show(fig)

# =================================================================== PAGE 2
elif page.startswith("02"):
    objective_banner(2, "Population, Income & Prices",
                     "Examine whether states with more people also have higher income and prices, "
                     "to find where cost-of-living pressure is greatest.")
    f1, f2 = st.columns(2)
    with f1:
        income_label = income_picker()
    with f2:
        selected_states = st.multiselect("Highlight state", STATES, default=[], key="obj2_states",
                                         help="Highlight one or more states. Leave empty to show all.")
    measure_col = "income_mean" if income_label == "Mean income" else "income_median"

    snap = calc.population_income_snapshot(df, comparison)
    before = calc.population_income_snapshot(df, prev).set_index("state")
    if snap.empty:
        st.warning("No data available for this year.")
        st.stop()
    snap["label"] = snap.state.map(short_state)
    top_pop = snap.sort_values("population", ascending=False).iloc[0]
    top_inc = snap.sort_values(measure_col, ascending=False).iloc[0]
    top_cpi = snap.sort_values("cpi", ascending=False).iloc[0]

    def change(row, col):
        return (row[col] / before.loc[row.state, col] - 1) * 100 if row.state in before.index else 0.0

    cards([
        ("Highest income", short_state(top_inc.state), f"RM {top_inc[measure_col]:,.0f} per month",
         *delta(change(top_inc, measure_col), prev, "income")),
        ("Largest population", short_state(top_pop.state), f"{top_pop.population / 1000:.1f} million people",
         *delta(change(top_pop, "population"), prev, "neutral")),
        ("Highest prices", short_state(top_cpi.state), f"CPI {top_cpi.cpi:.1f} (2010 = 100)",
         *delta(change(top_cpi, "cpi"), prev, "price")),
    ], f"{comparison} · CHANGE SINCE {prev}")

    picked = set(selected_states)
    focus = [(not picked) or s in picked for s in snap.state]
    order = {s: i for i, s in enumerate(snap.sort_values("population").state)}  # alternate label sides to limit overlap
    positions = ["top center" if order[s] % 2 == 0 else "bottom center" for s in snap.state]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=snap.population, y=snap[measure_col], mode="markers+text", text=snap.label,
        textposition=positions, textfont=dict(size=10, color=INK),
        marker=dict(size=16, color=snap.cpi, colorscale=["#FDE6D6", "#F8A670", PRICE_ORANGE, "#B23A00"],
                    opacity=[0.95 if f else 0.3 for f in focus], showscale=False,
                    line=dict(color=[INK if (picked and f) else WHITE for f in focus], width=1.6)),
        customdata=snap[["cpi"]],
        hovertemplate="<b>%{text}</b><br>Population: %{x:,.0f} thousand persons<br>"
                      + income_label + ": RM %{y:,.0f} per month<br>Overall CPI: %{customdata[0]:.1f}<extra></extra>",
    ))
    pmin, pmax = float(snap.population.min()), float(snap.population.max())
    ticks = [t for t in (100, 250, 500, 1000, 2500, 5000) if pmin * 0.7 <= t <= pmax * 1.4]
    ymin, ymax = float(snap[measure_col].min()), float(snap[measure_col].max())
    fig.update_xaxes(type="log", title="Population (log scale): more people →", showgrid=True, gridcolor=GRID,
                     tickvals=ticks, ticktext=[f"{t / 1000:g}M" for t in ticks],
                     range=[math.log10(pmin * 0.7), math.log10(pmax * 1.4)])
    fig.update_yaxes(title="Monthly household income (RM)", tickformat=",", showgrid=True,
                     gridcolor=GRID, range=[ymin * 0.8, ymax * 1.1])
    fig.update_layout(showlegend=False)
    st.subheader(f"Population, {income_label.lower()} and prices by state · {comparison}")
    scale_legend("Dot colour = how much prices rose since 2010", "Smaller rise", "Moderate", "Bigger rise")
    show(chart_layout(fig, 620))

# =================================================================== PAGE 3
else:
    objective_banner(3, "Cost-of-Living Drivers",
                     "Identify which spending categories, such as food, housing and transport, push prices up the most, "
                     "and rank states by overall cost-of-living pressure.")
    tbl = calc.category_growth_table(df, baseline, comparison)
    step = calc.category_growth_table(df, prev, comparison)  # latest step: previous survey year to selected year
    if tbl.empty or step.empty:
        st.warning("No data available for this year.")
        st.stop()
    cat_avg = tbl.drop(columns=calc.OVERALL).mean().sort_values(ascending=False)
    step_cat = step.drop(columns=calc.OVERALL).mean().sort_values(ascending=False)
    state_list = list(tbl.index)
    ALL = "All states (average)"
    key_to_state = {calc.norm(s): s for s in state_list}

    top_state = step[calc.OVERALL].idxmax()
    low_cat, low_val = step_cat.index[-1], float(step_cat.iloc[-1])
    cards([
        ("State with the biggest price rise" if step.loc[top_state, calc.OVERALL] >= 0 else "State where prices fell least", short_state(top_state), None,
         *delta(float(step.loc[top_state, calc.OVERALL]), prev, "price")),
        ("Fastest-rising category" if step_cat.iloc[0] >= 0 else "Smallest fall in prices", step_cat.index[0], "Average of all states",
         *delta(float(step_cat.iloc[0]), prev, "price")),
        ("Prices fell most in" if low_val < 0 else "Slowest-rising category", low_cat, "Average of all states",
         *delta(low_val, prev, "price")),
    ], f"LATEST CHANGE · {prev} TO {comparison}")

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
    scale_legend(f"Map colour = how much prices rose since {baseline}", "Smaller rise", "Moderate", "Bigger rise")
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
        use_tiles = hasattr(go, "Choroplethmap")
        Choro = go.Choroplethmap if use_tiles else go.Choropleth
        common = dict(geojson=gj, featureidkey="properties.state_key")
        fig_map = go.Figure(Choro(
            locations=[calc.norm(s) for s in state_list], z=tbl[calc.OVERALL].values,
            text=[short_state(s) for s in state_list],
            colorscale=["#FDE6D6", "#F8A670", PRICE_ORANGE, "#B23A00"], showscale=False,
            marker_line_color="white", marker_line_width=1,
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
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
        show_clickable(fig_map, "map3", _on_map_click)
        if no_shape:
            st.caption("Not on the map file: " + ", ".join(short_state(s) for s in no_shape)
                       + ". Choose them from the menu below.")

    st.selectbox(
        "Selected state (click the map, or choose here)", [ALL] + state_list, key="p3_state",
        format_func=lambda s: s if s == ALL else short_state(s),
        help="Listed from the highest to the lowest overall price rise. "
             "Small areas such as Kuala Lumpur, Putrajaya and Labuan are easier to pick here.",
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
    fig.add_vline(x=overall, line_dash="dash", line_color=INK)
    fig.update_yaxes(categoryorder="array", categoryarray=vals.index.tolist(), autorange="reversed",
                     automargin=True)
    fig.update_xaxes(title=f"Price growth since {baseline} (%)", ticksuffix="%", showgrid=True,
                     gridcolor=GRID, zeroline=True, zerolinecolor="#8793A1",
                     range=[min(0, float(vals.min())) - 8, float(vals.max()) * 1.15 + 6])
    fig = chart_layout(fig, 560)
    fig.update_layout(showlegend=False, bargap=.28, margin=dict(l=28, r=40, t=20, b=50))
    st.subheader(f"Spending categories driving prices · {label}")
    legend_row(swatch(PRICE_ORANGE, "Prices rose"), swatch(TEAL, "Prices fell"),
               f'<span class="lg-dash"></span>Overall price rise ({overall:+.0f}%)')
    show(fig)

st.divider()
st.caption("Source: OpenDOSM — Population, Household Income and Consumer Price Index by state. "
           "JIE42403 Scientific Visualisation.")
