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
        margin=dict(l=18, r=24, t=52, b=24),
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
st.sidebar.markdown("**Comparison period**")
baseline = st.sidebar.selectbox("Baseline year", YEARS, index=0)
valid_comparisons = [y for y in YEARS if y > baseline]
if not valid_comparisons:
    st.sidebar.warning("Choose an earlier baseline year.")
    st.stop()
comparison = st.sidebar.selectbox("Comparison year", valid_comparisons, index=len(valid_comparisons)-1)
st.sidebar.caption(f"Comparing {baseline} with {comparison}")
with st.sidebar.expander("Data & methodology"):
    st.write("Source: supplied OpenDOSM-derived merged dataset.")
    st.write("Population, mean/median household income and CPI are compared by state and year.")
    st.write("CPI growth is calculated from the Overall CPI index. Category rankings use category CPI index growth.")
    st.caption("Available years: " + ", ".join(map(str, YEARS)))

st.markdown('<div class="kicker">Malaysia · Cost of Living Intelligence</div>', unsafe_allow_html=True)
st.title("Understanding the cost of living")
st.markdown('<div class="subhead">Three focused views. One analytical question per chart.</div>', unsafe_allow_html=True)

if page.startswith("01"):
    growth = calc.growth_comparison(df, baseline, comparison)
    growth = growth.sort_values("gap", ascending=True)
    better = int((growth.gap > 0).sum())
    worse = int((growth.gap < 0).sum())
    avg_real = growth.real_growth.mean()
    st.markdown(f'<div class="objective"><strong>OBJECTIVE 01</strong><br>Compare income growth with price growth in each state to identify where household purchasing power improved or came under pressure.</div>', unsafe_allow_html=True)
    k1,k2,k3 = st.columns(3)
    k1.metric("States where income outpaced prices", f"{better} / {len(growth)}")
    k2.metric("States where prices outpaced income", f"{worse} / {len(growth)}")
    k3.metric("Average real income growth", f"{avg_real:+.1f}%")
    st.subheader("Income growth vs price growth by state")
    st.caption(f"Percentage change from {baseline} to {comparison} · Mean household income compared with Overall CPI")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=growth.state, x=growth.income_growth, name="Mean income growth",
                         orientation="h", marker_color=TEAL,
                         hovertemplate="<b>%{y}</b><br>Income growth: %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(y=growth.state, x=growth.price_growth, name="Overall price growth",
                         orientation="h", marker_color=CORAL,
                         hovertemplate="<b>%{y}</b><br>Price growth: %{x:.1f}%<extra></extra>"))
    fig.update_layout(barmode="group", xaxis_title="Growth (%)", yaxis_title="",
                      bargap=.28, legend_title="")
    fig.update_yaxes(categoryorder="array", categoryarray=growth.state.tolist(), autorange="reversed")
    fig.add_vline(x=0, line_color="#AAB5BF", line_width=1)
    st.plotly_chart(chart_layout(fig, max(520, 32*len(growth)+100)), use_container_width=True, config=PLOT_CONFIG)
    st.markdown('<div class="chart-note">Interpretation: when the teal bar is longer than the coral bar, mean income grew faster than overall prices. This is a purchasing-power indicator, not a direct measure of every household’s affordability.</div>', unsafe_allow_html=True)

elif page.startswith("02"):
    year = st.selectbox("Snapshot year", YEARS, index=len(YEARS)-1, key="snapshot_year")
    snap = calc.population_income_snapshot(df, year)
    st.markdown('<div class="objective"><strong>OBJECTIVE 02</strong><br>Examine whether states with larger populations also have higher household incomes and price levels, to locate possible concentrations of cost-of-living pressure.</div>', unsafe_allow_html=True)
    st.subheader(f"Population, household income and price level · {year}")
    st.caption("Each bubble represents one state. Horizontal position = population; vertical position = mean monthly household income; bubble size = Overall CPI index.")
    snap["state_label"] = snap.state.map(short_state)
    fig = px.scatter(snap, x="population", y="income_mean", size="cpi", color="cpi",
                     color_continuous_scale=["#BFE7E2", TEAL, "#155E59"],
                     hover_name="state_label",
                     hover_data={"population":":,.0f","income_mean":"RM {:,.0f}","cpi":":.1f","state":False,"state_label":False},
                     size_max=48, opacity=.84)
    fig.update_traces(marker=dict(line=dict(color="#FFFFFF", width=1.5)),
                      customdata=snap[["cpi"]].to_numpy(),
                      hovertemplate="<b>%{hovertext}</b><br>Population: %{x:,.0f}<br>Mean monthly income: RM %{y:,.0f}<br>Overall CPI: %{customdata[0]:.1f}<extra></extra>")
    fig.update_layout(xaxis_title="Population (persons, dataset unit)", yaxis_title="Mean monthly household income (RM)",
                      coloraxis_colorbar=dict(title="Overall CPI", thickness=12, len=.72))
    st.plotly_chart(chart_layout(fig, 610), use_container_width=True, config=PLOT_CONFIG)
    st.markdown('<div class="chart-note">Read the chart by looking for states toward the upper-right (larger population and higher mean income), then compare bubble size and colour for the CPI price level. Association does not imply that population causes higher prices.</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="objective"><strong>OBJECTIVE 03</strong><br>Identify which spending categories record the strongest price increases, and compare which states experience the greatest overall cost-of-living pressure.</div>', unsafe_allow_html=True)
    view = st.radio("Ranking view", ["Spending categories", "States"], horizontal=True)
    if view == "Spending categories":
        rank = calc.category_growth_national(df, baseline, comparison)
        rank = rank.sort_values("price_growth", ascending=True)
        st.subheader("Which spending categories increased the most?")
        st.caption(f"Unweighted mean of state-level CPI growth · {baseline} to {comparison}")
        labels = rank.category.tolist()
        values = rank.price_growth.tolist()
        colors = [CORAL if x >= 0 else TEAL for x in values]
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
                               hovertemplate="<b>%{y}</b><br>Average state-level price growth: %{x:.1f}%<extra></extra>"))
        fig.update_layout(xaxis_title="Mean state-level price growth (%)", yaxis_title="", showlegend=False, bargap=.28)
        fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed")
        fig.add_vline(x=0, line_color="#AAB5BF", line_width=1)
        st.plotly_chart(chart_layout(fig, 570), use_container_width=True, config=PLOT_CONFIG)
        st.caption("Categories are ranked using the unweighted mean of available state-level CPI growth rates. This is not an expenditure-weighted contribution to inflation.")
    else:
        category = st.selectbox("Price index to rank", ["Overall"] + CATEGORIES,
                                index=0, format_func=lambda x: "Overall cost of living" if x == "Overall" else x)
        rank = calc.category_state_growth(df, baseline, comparison, category)
        rank = rank.sort_values("price_growth", ascending=True)
        label = "Overall CPI" if category == "Overall" else f"{category} CPI"
        st.subheader(f"Which states face the highest increase? · {label}")
        st.caption(f"State ranking by price index growth · {baseline} to {comparison}")
        colors = [CORAL if x >= 0 else TEAL for x in rank.price_growth]
        fig = go.Figure(go.Bar(x=rank.price_growth, y=rank.state, orientation="h",
                               marker_color=colors,
                               hovertemplate="<b>%{y}</b><br>Price growth: %{x:.1f}%<extra></extra>"))
        fig.update_layout(xaxis_title="Price index growth (%)", yaxis_title="", showlegend=False, bargap=.24)
        fig.update_yaxes(categoryorder="array", categoryarray=rank.state.tolist(), autorange="reversed")
        fig.add_vline(x=0, line_color="#AAB5BF", line_width=1)
        st.plotly_chart(chart_layout(fig, max(520, 32*len(rank)+100)), use_container_width=True, config=PLOT_CONFIG)
        st.caption("This ranks states for the selected CPI index. Growth rates show price change, not the category’s weighted contribution share to total inflation.")

st.divider()
st.caption("Dashboard calculations use the supplied dataset only. Missing state-year/category combinations are not imputed.")
