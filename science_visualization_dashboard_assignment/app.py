from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import analysis as calc

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

# Consistent dashboard design system: deep ink, teal for income, coral for prices.
BG, INK, MUTED = "#F5F7FA", "#182230", "#667085"
TEAL, CORAL, GRID, WHITE = "#147D73", "#E4775B", "#E5EAF0", "#FFFFFF"
FONT = "Inter, Aptos, Segoe UI, sans-serif"
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

st.markdown(f"""
<style>
.stApp {{ background:{BG}; color:{INK}; }}
.block-container {{ max-width:1460px; padding-top:1.35rem; padding-bottom:2.5rem; }}
[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {GRID}; }}
[data-testid="stSidebar"] > div:first-child {{ padding:1.35rem 1.05rem 1rem; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{font-size:1.18rem;letter-spacing:-.03em;}}
[data-testid="stSidebar"] hr {{ margin:.8rem 0; border-color:{GRID}; }}
h1,h2,h3 {{ color:{INK}; letter-spacing:-.035em; }}
h1 {{ font-size:2rem !important; font-weight:730 !important; margin-bottom:.1rem !important; }}
h2 {{ font-size:1.28rem !important; font-weight:680 !important; }}
p,label {{ color:{INK}; }}
.page-kicker {{ color:{TEAL}; font-size:.72rem; font-weight:750; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.35rem; }}
.page-description {{ color:{MUTED}; font-size:.94rem; margin:.15rem 0 1.05rem 0; }}
.filter-panel {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:13px; padding:.75rem 1rem .35rem; margin:.9rem 0 1.15rem; }}
.filter-heading {{ color:{MUTED}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin:0 0 .2rem; }}
[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:12px 15px; min-height:96px; }}
[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-size:.78rem; line-height:1.25; }}
[data-testid="stMetricValue"] {{ color:{INK}; font-size:1.42rem; font-weight:720; }}
div[data-testid="stPlotlyChart"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:13px; padding:5px 8px 2px; }}
[data-testid="stRadio"] > div {{ gap:.55rem; }}
[data-testid="stRadio"] label {{ font-size:.88rem; }}
div[data-testid="stCaptionContainer"] p {{ color:{MUTED}; }}
hr {{ border-color:{GRID}; }}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load():
    return calc.load_data()

df = load()
YEARS = sorted(df.year.unique().tolist())
STATES = sorted(df.state.unique().tolist())
CATEGORIES = sorted(c for c in df.division.unique() if c != "Overall")

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

def short_state(s):
    return {"W.P. Kuala Lumpur":"Kuala Lumpur", "W.P. Putrajaya":"Putrajaya",
            "W.P. Labuan":"Labuan", "Pulau Pinang":"Penang",
            "Negeri Sembilan":"Negeri Sembilan"}.get(s, s)

st.sidebar.markdown("## 📊 Cost of Living")
st.sidebar.caption("MALAYSIA")
st.sidebar.divider()
page = st.sidebar.radio(
    "PAGES",
    ["01  Income vs Price Growth",
     "02  Population, Income & Prices",
     "03  Cost-of-Living Drivers"],
    label_visibility="visible"
)
st.sidebar.divider()
with st.sidebar.expander("About this dashboard"):
    st.write("State-level comparison of household income, population and consumer price indices.")
    st.caption("Data years: " + " · ".join(map(str, YEARS)))

st.markdown('<div class="page-kicker">MALAYSIA · COST OF LIVING</div>', unsafe_allow_html=True)
st.title("Cost of Living Dashboard")

with st.container(border=True):
    st.markdown('<div class="filter-heading">COMPARISON PERIOD</div>', unsafe_allow_html=True)
    fy1, fy2 = st.columns(2)
    with fy1:
        baseline = st.selectbox("Baseline year", YEARS, index=0, key="baseline_year")
    comparison_options = [y for y in YEARS if y != baseline]
    default_comparison = YEARS[-1] if YEARS[-1] != baseline else YEARS[-2]
    with fy2:
        comparison = st.selectbox("Compare with", comparison_options,
                                  index=comparison_options.index(default_comparison),
                                  key="comparison_year")

if page.startswith("01"):
    
    f1, f2 = st.columns([1, 1])
    with f1:
        income_measure_label = st.selectbox("Household income measure", ["Mean income", "Median income"],
                                            help="Choose which income statistic to compare against Overall CPI.")
    with f2:
        selected_states = st.multiselect("States to display", STATES, default=STATES,
                                         help="Select the states you want to compare.")
    measure_col = "income_mean" if income_measure_label == "Mean income" else "income_median"
    growth = calc.growth_comparison(df, baseline, comparison, measure_col)
    if selected_states:
        growth = growth[growth.state.isin(selected_states)]
    if growth.empty:
        st.warning("No matching state data for this selection.")
        st.stop()
    growth = growth.sort_values("gap", ascending=False)

    avg_income_growth = growth["income_growth"].mean()
    avg_price_growth = growth["price_growth"].mean()
    avg_gap = growth["gap"].mean()
    k1, k2, k3 = st.columns(3)
    k1.metric("Average income growth", f"{avg_income_growth:+.1f}%",
              help=f"Average {income_measure_label.lower()} growth across the selected states.")
    k2.metric("Average price growth", f"{avg_price_growth:+.1f}%",
              help="Average Overall CPI growth across the same selected states.")
    k3.metric("Income growth advantage", f"{avg_gap:+.1f} pp",
              help="Average income growth minus average price growth, in percentage points.")

    # Identify states using the income-growth minus price-growth gap.
    most_improved = growth.loc[growth["gap"].idxmax()]
    least_improved = growth.loc[growth["gap"].idxmin()]

    s1, s2 = st.columns(2)
    with s1:
        st.metric(
            "Most improved state",
            short_state(most_improved["state"]),
            delta=f"{most_improved['gap']:+.1f} pp income advantage",
            help="State with the largest difference between income growth and Overall CPI growth."
        )
    with s2:
        st.metric(
            "Least improved state",
            short_state(least_improved["state"]),
            delta=f"{least_improved['gap']:+.1f} pp income advantage",
            delta_color="normal",
            help="State with the smallest difference between income growth and Overall CPI growth. A positive value still means income growth exceeded price growth."
        )

    st.subheader(f"{income_measure_label} vs overall price growth")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=growth.state, x=growth.income_growth, name=income_measure_label,
                         orientation="h", marker_color=TEAL,
                         hovertemplate="<b>%{y}</b><br>" + income_measure_label + " growth: %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(y=growth.state, x=growth.price_growth, name="Overall price growth",
                         orientation="h", marker_color=CORAL,
                         hovertemplate="<b>%{y}</b><br>Overall price growth: %{x:.1f}%<extra></extra>"))
    fig.update_layout(barmode="group", xaxis_title="Growth rate (%)", yaxis_title="",
                      bargap=.22, bargroupgap=.08, legend_title="", height=590)
    fig.update_yaxes(categoryorder="array", categoryarray=growth.state.tolist(), autorange="reversed",
                     tickfont=dict(size=11), title_standoff=14)
    fig.update_xaxes(title="Growth rate (%)", ticksuffix="%", showgrid=True, gridcolor=GRID,
                     zeroline=True, zerolinecolor="#AAB5BF")
    st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)

elif page.startswith("02"):
    year = st.selectbox("Snapshot year", YEARS, index=len(YEARS)-1, key="snapshot_year")
    snap = calc.population_income_snapshot(df, year)
    
    selected_states_2 = st.multiselect("States", STATES, default=STATES, key="obj2_states")
    if selected_states_2:
        snap = snap[snap.state.isin(selected_states_2)]
    if snap.empty:
        st.warning("Select at least one state to display.")
        st.stop()

    snap["state_label"] = snap.state.map(short_state)
    st.subheader(f"Population, household income and price level · {year}")
    fig = px.scatter(
        snap, x="population", y="income_mean", color="cpi",
        color_continuous_scale=["#BFE7E2", "#55AAA1", "#155E59"],
        hover_name="state_label",
        hover_data={"population":":,.0f", "income_mean":"RM {:,.0f}", "cpi":":.1f",
                    "state":False, "state_label":False},
        opacity=.88
    )
    fig.update_traces(marker=dict(size=13, line=dict(color="#FFFFFF", width=1.2)),
                      hovertemplate="<b>%{hovertext}</b><br>Population: %{x:,.0f} thousand persons<br>Mean monthly household income: RM %{y:,.0f}<br>Overall CPI: %{marker.color:.1f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Population (thousand persons)",
        yaxis_title="Mean monthly household income (RM)",
        coloraxis_colorbar=dict(title="Overall CPI", thickness=13, len=.72),
        height=650
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)

else:
    
    view = st.radio("View", ["Spending categories", "States"],
                    horizontal=True,
                    help="Choose whether to rank CPI spending categories or states.")

    if view == "Spending categories":
        rank = calc.category_growth_national(df, baseline, comparison).sort_values("price_growth", ascending=True)
        st.subheader("Which spending categories increased the most?")
        labels = rank.category.tolist()
        values = rank.price_growth.tolist()
        colors = [CORAL if x >= 0 else TEAL for x in values]
        fig = go.Figure(go.Bar(
            x=values, y=labels, orientation="h", marker_color=colors,
            hovertemplate="<b>%{y}</b><br>Average price growth: %{x:.1f}%<extra></extra>"
        ))
        fig.update_layout(xaxis_title="Average price growth (%)", yaxis_title="",
                          showlegend=False, bargap=.25, height=590)
        fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                         ticksuffix="%")
        st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)
    else:
        rank = calc.category_state_growth(df, baseline, comparison, "Overall")
        rank = rank.sort_values("price_growth", ascending=True)
        st.subheader("Overall price growth by state")
        colors = [CORAL if x >= 0 else TEAL for x in rank.price_growth]
        fig = go.Figure(go.Bar(
            x=rank.price_growth, y=rank.state, orientation="h", marker_color=colors,
            hovertemplate="<b>%{y}</b><br>Overall price growth: %{x:.1f}%<extra></extra>"
        ))
        fig.update_layout(xaxis_title="Overall CPI growth (%)", yaxis_title="State",
                          showlegend=False, bargap=.22, height=590)
        fig.update_yaxes(categoryorder="array", categoryarray=rank.state.tolist(), autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                         ticksuffix="%")
        st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)

