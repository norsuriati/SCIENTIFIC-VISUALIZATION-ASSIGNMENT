from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import analysis as calc

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

# Calm editorial dashboard styling: neutral canvas, restrained teal/coral accents.
BG, INK, MUTED = "#F6F8FA", "#17212B", "#667482"
TEAL, CORAL, GOLD, GRID = "#168C83", "#E2765B", "#D7A441", "#E8EDF1"
FONT = "Inter, Aptos, Segoe UI, sans-serif"
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

st.markdown(f"""
<style>
.stApp {{ background:{BG}; color:{INK}; }}
.block-container {{ max-width:1480px; padding-top:2.0rem; padding-bottom:3rem; }}
[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid {GRID}; }}
[data-testid="stSidebar"] > div:first-child {{ padding-top:1.5rem; }}
h1,h2,h3 {{ color:{INK}; letter-spacing:-.035em; }}
h1 {{ font-size:2.15rem !important; font-weight:720 !important; }}
h2 {{ font-size:1.32rem !important; font-weight:680 !important; }}
p, label {{ color:{INK}; }}
.kicker {{ color:{TEAL}; font-size:.76rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }}
.subhead {{ color:{MUTED}; font-size:1rem; margin-top:-.25rem; }}
.objective {{ background:#FFFFFF; border:1px solid {GRID}; border-left:4px solid {TEAL};
  padding:1rem 1.15rem; border-radius:12px; margin:.8rem 0 1rem 0; color:{INK}; }}
.objective strong {{ color:{TEAL}; }}
.chart-note {{ color:{MUTED}; font-size:.88rem; margin-top:-.35rem; }}
[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:13px; padding:13px 16px; }}
[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-size:.82rem; }}
[data-testid="stMetricValue"] {{ color:{INK}; font-size:1.55rem; font-weight:700; }}
div[data-testid="stPlotlyChart"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:14px; padding:8px; }}
.stSelectbox, .stMultiSelect {{ background:#FFFFFF; }}
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
st.sidebar.caption("MALAYSIA · STATE-LEVEL ANALYSIS")
st.sidebar.divider()
page = st.sidebar.radio("DASHBOARD", [
    "01  Income vs Price Growth",
    "02  Population, Income & Prices",
    "03  Cost-of-Living Drivers",
], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("**Year comparison**")
st.sidebar.caption("Choose two years available in the dataset.")
baseline = st.sidebar.selectbox("Baseline year (Year A)", YEARS, index=0, key="baseline_year")
comparison_options = [y for y in YEARS if y != baseline]
default_comparison = YEARS.index(YEARS[-1]) if YEARS[-1] != baseline else len(YEARS) - 2
comparison = st.sidebar.selectbox(
    "Comparison year (Year B)", comparison_options,
    index=comparison_options.index(YEARS[default_comparison]),
    key="comparison_year"
)
st.sidebar.caption(f"Selected comparison: {baseline} → {comparison}")
with st.sidebar.expander("Available dataset years"):
    st.write(", ".join(map(str, YEARS)))
with st.sidebar.expander("Data & methodology"):
    st.write("Source: supplied OpenDOSM-derived merged dataset.")
    st.write("Population, mean/median household income and CPI are compared by state and year.")
    st.write("CPI growth is calculated from the Overall CPI index. Category rankings use category CPI index growth.")
    st.caption("Available years: " + ", ".join(map(str, YEARS)))

st.markdown('<div class="kicker">Malaysia · Cost of Living Intelligence</div>', unsafe_allow_html=True)
st.title("Understanding the cost of living")
st.markdown('<div class="subhead">Three focused views. One analytical question per chart.</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="objective" style="display:flex;justify-content:space-between;align-items:center;gap:12px;'
    f'padding:.7rem 1rem;margin:.8rem 0 1rem 0;">'
    f'<span><strong>ACTIVE COMPARISON PERIOD</strong><br>{baseline} <span style="color:{MUTED}">compared with</span> {comparison}</span>'
    f'<span style="color:{MUTED};font-size:.85rem;">Only years available in the dataset are selectable</span></div>',
    unsafe_allow_html=True
)

if page.startswith("01"):
    st.markdown('<div class="objective"><strong>OBJECTIVE 01</strong><br>Compare household income growth with overall price growth in each state to see whether income is keeping pace with the cost of living.</div>', unsafe_allow_html=True)

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
    growth = growth.sort_values("gap", ascending=True)

    better = int((growth.gap > 0).sum())
    worse = int((growth.gap < 0).sum())
    avg_real = growth.real_growth.mean()
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Income outpaced prices", f"{better} of {len(growth)} states")
        st.caption("Income growth % is higher than Overall CPI growth %.")
    with k2:
        st.metric("Prices outpaced income", f"{worse} of {len(growth)} states")
        st.caption("Overall CPI growth % is higher than income growth %.")
    with k3:
        st.metric("Average real income growth", f"{avg_real:+.1f}%")
        st.caption("Average income growth after adjusting for CPI growth.")

    st.subheader(f"{income_measure_label} growth vs overall price growth")
    st.caption(f"Year A: {baseline}  →  Year B: {comparison} · Percentage change (%)")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=growth.state, x=growth.income_growth, name=income_measure_label,
                         orientation="h", marker_color=TEAL,
                         hovertemplate="<b>%{y}</b><br>" + income_measure_label + " growth: %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(y=growth.state, x=growth.price_growth, name="Overall price growth",
                         orientation="h", marker_color=CORAL,
                         hovertemplate="<b>%{y}</b><br>Overall price growth: %{x:.1f}%<extra></extra>"))
    fig.update_layout(barmode="group", xaxis_title="Growth rate (%)", yaxis_title="State",
                      bargap=.22, bargroupgap=.08, legend_title="", height=650)
    fig.update_yaxes(categoryorder="array", categoryarray=growth.state.tolist(), autorange="reversed",
                     tickfont=dict(size=11), title_standoff=14)
    fig.update_xaxes(title="Growth rate (%)", ticksuffix="%", showgrid=True, gridcolor=GRID,
                     zeroline=True, zerolinecolor="#AAB5BF")
    st.plotly_chart(chart_layout(fig, 650), use_container_width=True, config=PLOT_CONFIG)
    st.markdown('<div class="chart-note">Teal = selected household income growth. Coral = overall CPI growth. If income growth is higher than price growth, purchasing power improved on average. Switch between Mean and Median to compare the two income measures separately.</div>', unsafe_allow_html=True)

elif page.startswith("02"):
    year = st.selectbox("Snapshot year", YEARS, index=len(YEARS)-1, key="snapshot_year")
    snap = calc.population_income_snapshot(df, year)
    st.markdown('<div class="objective"><strong>OBJECTIVE 02</strong><br>Examine whether states with larger populations also have higher household incomes and price levels. Each point represents one state.</div>', unsafe_allow_html=True)

    selected_states_2 = st.multiselect("States to display", STATES, default=STATES, key="obj2_states")
    if selected_states_2:
        snap = snap[snap.state.isin(selected_states_2)]
    if snap.empty:
        st.warning("Select at least one state to display.")
        st.stop()

    snap["state_label"] = snap.state.map(short_state)
    st.subheader(f"Population, household income and price level · {year}")
    st.info(f"This page shows a single-year snapshot for **{year}**. Change the Snapshot year filter to view another available year; the comparison period above applies to Objectives 1 and 3.")
    st.caption("Population is on the horizontal axis, mean monthly household income on the vertical axis, and Overall CPI is shown by point colour. Points are equal-sized for easier reading.")
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
    st.plotly_chart(chart_layout(fig, 650), use_container_width=True, config=PLOT_CONFIG)
    st.markdown('<div class="chart-note">Look toward the upper-right for states with both larger populations and higher mean incomes. Darker points indicate a higher Overall CPI. Hover over a point to read the state and its values. Association does not imply causation.</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="objective"><strong>OBJECTIVE 03</strong><br>Find which spending categories recorded the largest price increases, and identify which states experienced the highest overall price growth.</div>', unsafe_allow_html=True)

    view = st.radio(
        "Choose what to rank",
        ["Spending categories", "States by overall price growth"],
        horizontal=True,
        help="Spending categories ranks the CPI categories. States ranks each state using Overall CPI only."
    )

    if view == "Spending categories":
        rank = calc.category_growth_national(df, baseline, comparison).sort_values("price_growth", ascending=True)
        st.subheader("Which spending categories increased the most?")
        st.caption(f"Average state-level CPI growth · Year A: {baseline} → Year B: {comparison}")
        labels = rank.category.tolist()
        values = rank.price_growth.tolist()
        colors = [CORAL if x >= 0 else TEAL for x in values]
        fig = go.Figure(go.Bar(
            x=values, y=labels, orientation="h", marker_color=colors,
            hovertemplate="<b>%{y}</b><br>Average price growth: %{x:.1f}%<extra></extra>"
        ))
        fig.update_layout(xaxis_title="Average price growth (%)", yaxis_title="Spending category",
                          showlegend=False, bargap=.25, height=650)
        fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                         ticksuffix="%")
        st.plotly_chart(chart_layout(fig, 650), use_container_width=True, config=PLOT_CONFIG)
        st.caption("This view compares the 13 spending categories. It does not rank states. Values are the unweighted average of available state-level CPI growth rates, not weighted contributions to inflation.")
    else:
        rank = calc.category_state_growth(df, baseline, comparison, "Overall")
        rank = rank.sort_values("price_growth", ascending=True)
        st.subheader("Which states had the highest overall price growth?")
        st.caption(f"Overall CPI growth by state · Year A: {baseline} → Year B: {comparison}")
        colors = [CORAL if x >= 0 else TEAL for x in rank.price_growth]
        fig = go.Figure(go.Bar(
            x=rank.price_growth, y=rank.state, orientation="h", marker_color=colors,
            hovertemplate="<b>%{y}</b><br>Overall price growth: %{x:.1f}%<extra></extra>"
        ))
        fig.update_layout(xaxis_title="Overall CPI growth (%)", yaxis_title="State",
                          showlegend=False, bargap=.22, height=650)
        fig.update_yaxes(categoryorder="array", categoryarray=rank.state.tolist(), autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#AAB5BF",
                         ticksuffix="%")
        st.plotly_chart(chart_layout(fig, 650), use_container_width=True, config=PLOT_CONFIG)
        st.caption("This view ranks states using Overall CPI only. It is a broad measure of overall price growth, not a measure of household income or expenditure.")

st.divider()
st.caption("Dashboard calculations use the supplied dataset only. Missing state-year/category combinations are not imputed.")
