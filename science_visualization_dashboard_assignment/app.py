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
.block-container {{ max-width:1460px; padding-top:.35rem; padding-bottom:2.5rem; }}
[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {GRID}; }}
[data-testid="stSidebar"] > div:first-child {{ padding:1.35rem 1.05rem 1rem; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{font-size:1.32rem;letter-spacing:-.035em;font-weight:760;margin-bottom:.15rem;color:{INK};}}
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
                   padding:.8rem 1.1rem; margin:.15rem 0 1.1rem; }}
.objective-label {{ color:{TEAL}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; }}
.objective-text {{ color:{INK}; font-size:1.02rem; margin-top:.15rem; }}
.filter-heading {{ color:{MUTED}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin:0 0 .2rem; }}
.kpi {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:13px 16px; box-sizing:border-box; }}
.kpi.equal-height {{ height:258px; display:flex; flex-direction:column; }}
.kpi.equal-height .kpi-row {{ flex:1 1 0; align-items:flex-start; }}
.kpi.equal-height .kpi-name {{ min-width:0; overflow-wrap:anywhere; }}

.kpi-header {{ display:flex; align-items:center; justify-content:space-between; gap:.5rem; margin-bottom:.35rem; }}
.kpi-label {{ color:{MUTED}; font-size:.8rem; font-weight:650; line-height:1.25; }}
.kpi-period {{ display:inline-flex; align-items:center; gap:.25rem; flex:0 0 auto; padding:.2rem .5rem; border-radius:999px; background:#F2F4F7; color:{MUTED}; font-size:.66rem; font-weight:750; letter-spacing:.035em; white-space:nowrap; }}
.kpi-value {{ color:{INK}; font-size:1.4rem; font-weight:740; line-height:1.2; margin:.2rem 0 .15rem; overflow-wrap:anywhere; }}
.kpi-sub {{ color:{MUTED}; font-size:.82rem; line-height:1.3; }}
.kpi-row {{ display:flex; align-items:baseline; gap:.6rem; padding:.28rem 0; border-top:1px solid {GRID}; }}
.kpi-tag {{ flex:0 0 3.9rem; color:{MUTED}; font-size:.72rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.kpi-name {{ flex:1; color:{INK}; font-size:1.02rem; font-weight:720; line-height:1.25; }}
.kpi-name small {{ display:block; color:{MUTED}; font-size:.78rem; font-weight:500; }}
.kpi-chg {{ flex:0 0 auto; font-size:.9rem; font-weight:700; white-space:nowrap; }}
.kpi-foot {{ color:{MUTED}; font-size:.72rem; margin-top:.3rem; }}
.kpi-delta {{ font-size:.86rem; font-weight:680; line-height:1.3; margin-top:.2rem; }}
.legend-row {{ display:flex; gap:1.3rem; align-items:center; flex-wrap:wrap; font-size:.8rem; color:{MUTED}; margin:.1rem 0 .55rem; }}
.lg-item {{ display:inline-flex; align-items:center; gap:.4rem; }}
.lg-sw {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
.lg-grad {{ width:96px; height:10px; border-radius:5px; background:linear-gradient(90deg,#FDE6D6,#F8A670,{PRICE_ORANGE},#B23A00); display:inline-block; }}
.scale {{ width:340px; max-width:100%; margin:.1rem auto .7rem; }}
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


def chg(change, tone="price"):
    """('▲ +4.2%', tone). A fall always uses the teal tone."""
    return f"{'▲' if change >= 0 else '▼'} {change:+.1f}%", ("down" if change < 0 else tone)


def cards(items, equal_height=False):
    """Summary cards. The comparison period is shown as a compact header badge.
    A row is (name, detail or None, change text, tone)."""
    def row(tag, r):
        name, detail, change, tone = r
        small = f"<small>{html.escape(detail)}</small>" if detail else ""
        return (f'<div class="kpi-row"><span class="kpi-tag">{tag}</span>'
                f'<span class="kpi-name">{html.escape(name)}{small}</span>'
                f'<span class="kpi-chg" style="color:{TONES[tone]}">{html.escape(change)}</span></div>')
    for col, (title, hi, lo, foot) in zip(st.columns(len(items)), items):
        period_text = str(foot).replace("Change ", "").replace("change ", "").split(",")[0]
        period = html.escape(period_text)
        col.markdown(
            f'<div class="kpi{" equal-height" if equal_height else ""}"><div class="kpi-header">'
            f'<span class="kpi-label">{html.escape(title)}</span>'
            f'<span class="kpi-period">{period.upper()}</span></div>'
            f'{row("Highest", hi)}{row("Lowest", lo)}</div>',
            unsafe_allow_html=True,
        )


def legend_row(*items):
    """A small key above a chart. Items are ready-made HTML snippets."""
    st.markdown('<div class="legend-row">' + "".join(f'<span class="lg-item">{i}</span>' for i in items) + "</div>",
                unsafe_allow_html=True)


def scale_legend(low, mid, high):
    """Colour key: a centred gradient bar with three words underneath."""
    st.markdown(
        f'<div class="scale"><div class="scale-bar"></div>'
        f'<div class="scale-labels"><span>{html.escape(low)}</span><span>{html.escape(mid)}</span>'
        f'<span>{html.escape(high)}</span></div></div>', unsafe_allow_html=True)


def source_note():
    st.caption("Source: OpenDOSM")


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
# One shared year filter for all objectives, populated directly from the dataset.
baseline = YEARS[0]
st.sidebar.markdown("### YEAR")
comparison = st.sidebar.selectbox(
    "Select year",
    YEARS,
    index=len(YEARS) - 1,
    key="year_select",
)
prev = max((y for y in YEARS if y < comparison), default=None)
if comparison == baseline:
    st.sidebar.caption(
        f"{baseline} is the baseline year. Objective 1 and 3 growth comparisons "
        "start from the next available survey year."
    )
else:
    st.sidebar.caption(
        f"Available years follow the dataset: {', '.join(map(str, YEARS))}. "
        f"Growth in Objectives 1 and 3 is measured from {baseline}."
    )

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

    if comparison == baseline:
        st.info(
            f"{baseline} is the baseline year. Select a later year to view income "
            "and price growth compared with the baseline."
        )
        st.stop()

    growth_all = calc.growth_comparison(df, baseline, comparison, measure_col).sort_values("gap", ascending=False)
    step = calc.growth_comparison(df, prev, comparison, measure_col)  # latest step: previous survey year to selected year
    if selected_states:
        step = step[step.state.isin(selected_states)]
    if growth_all.empty or step.empty:
        st.warning("No data available for this selection.")
        st.stop()

    def end_rows(col, tone):
        hi, lo = step.loc[step[col].idxmax()], step.loc[step[col].idxmin()]
        return ((short_state(hi.state), None, *chg(hi[col], tone)), (short_state(lo.state), None, *chg(lo[col], tone)))

    cards([
        ("Income", *end_rows("income_growth", "income"), f"Change vs {prev}"),
        ("Prices", *end_rows("price_growth", "price"), f"Change vs {prev}"),
    ])

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
    source_note()

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
    before = (calc.population_income_snapshot(df, prev).set_index("state")
              if prev is not None else pd.DataFrame())
    if snap.empty:
        st.warning("No data available for this year.")
        st.stop()
    snap["label"] = snap.state.map(short_state)
    top_pop = snap.sort_values("population", ascending=False).iloc[0]
    top_inc = snap.sort_values(measure_col, ascending=False).iloc[0]
    top_cpi = snap.sort_values("cpi", ascending=False).iloc[0]

    def change(row, col):
        if prev is None or row.state not in before.index:
            return None
        return (row[col] / before.loc[row.state, col] - 1) * 100

    def end_rows(col, tone, detail):
        ordered = snap.sort_values(col, ascending=False)
        hi, lo = ordered.iloc[0], ordered.iloc[-1]

        def change_display(row):
            value = change(row, col)
            return ("—", "neutral") if value is None else chg(value, tone)

        hi_change, hi_tone = change_display(hi)
        lo_change, lo_tone = change_display(lo)
        return ((short_state(hi.state), detail(hi[col]), hi_change, hi_tone),
                (short_state(lo.state), detail(lo[col]), lo_change, lo_tone))

    period_label = "Baseline year" if prev is None else f"Change vs {prev}"
    cards([
        ("Income", *end_rows(measure_col, "income", lambda v: f"RM {v:,.0f} per month"), period_label),
        ("Population", *end_rows("population", "neutral", lambda v: f"{v / 1000:.2f} million people"), period_label),
        ("Prices", *end_rows("cpi", "price", lambda v: f"CPI Index {v:.1f}"), period_label),
    ], equal_height=True)

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
    fig.update_xaxes(type="log", title="Population (million)", showgrid=True, gridcolor=GRID,
                     tickvals=ticks, ticktext=[f"{t / 1000:g}" for t in ticks],
                     range=[math.log10(pmin * 0.7), math.log10(pmax * 1.4)])
    fig.update_yaxes(title="Monthly household income (RM)", tickformat=",", showgrid=True,
                     gridcolor=GRID, range=[ymin * 0.8, ymax * 1.1])
    fig.update_layout(showlegend=False)
    st.subheader(f"Population, {income_label.lower()} and prices by state · {comparison}")
    scale_legend("Small increase", "Medium", "Big increase")
    show(chart_layout(fig, 620))
    source_note()

# =================================================================== PAGE 3
else:
    objective_banner(3, "Cost-of-Living Drivers",
                     "Identify which spending categories, such as food, housing and transport, push prices up the most, "
                     "and rank states by overall cost-of-living pressure.")
    if comparison == baseline:
        st.info(
            f"{baseline} is the baseline year. Select a later year to view "
            "overall price growth and spending-category changes."
        )
        st.stop()

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

    st_sorted = step[calc.OVERALL].sort_values(ascending=False)
    cards([
        ("State prices (overall)",
         (short_state(st_sorted.index[0]), None, *chg(float(st_sorted.iloc[0]))),
         (short_state(st_sorted.index[-1]), None, *chg(float(st_sorted.iloc[-1]))),
         f"Change vs {prev}"),
        ("Spending category prices",
         (step_cat.index[0], None, *chg(float(step_cat.iloc[0]))),
         (step_cat.index[-1], None, *chg(float(step_cat.iloc[-1]))),
         f"Change vs {prev}, average of all states"),
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
    scale_legend("Small increase", "Medium", "Big increase")
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
        source_note()
        if no_shape:
            st.caption("Not on the map file: " + ", ".join(short_state(s) for s in no_shape)
                       + ". Choose them from the menu below.")

    st.selectbox(
        "Selected state (click the map, or choose here)", [ALL] + state_list, key="p3_state",
        format_func=lambda s: s if s == ALL else short_state(s),
        help="Listed from the biggest to the smallest overall price increase. "
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
    legend_row(swatch(PRICE_ORANGE, "Prices increased"), swatch(TEAL, "Prices decreased"),
               f'<span class="lg-dash"></span>Overall change ({overall:+.0f}%)')
    show(fig)
    source_note()
