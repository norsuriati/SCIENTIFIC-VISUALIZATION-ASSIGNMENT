from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
[data-testid="stSidebar"] [data-testid="stRadio"] > label {{ font-size:.78rem; color:{MUTED}; font-weight:650; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label {{ font-size:.82rem; color:{MUTED}; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {{ min-height:2.55rem; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ font-size:.72rem; line-height:1.35; }}
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


def save_income_measure():
    st.session_state["shared_income_measure"] = st.session_state["income_measure_widget"]

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
st.sidebar.markdown("### TIME PERIOD")
view_mode = st.sidebar.radio(
    "Period",
    ["Compare years", "Single year"],
    key="global_view_mode",
    label_visibility="collapsed"
)

if view_mode == "Compare years":
    baseline = st.sidebar.selectbox(
        "From year", YEARS, index=0, key="baseline_year"
    )
    comparison_options = [y for y in YEARS if y != baseline]
    default_comparison = YEARS[-1] if YEARS[-1] != baseline else YEARS[-2]
    comparison = st.sidebar.selectbox(
        "To year", comparison_options,
        index=comparison_options.index(default_comparison),
        key="comparison_year"
    )
    selected_year = comparison
else:
    selected_year = st.sidebar.selectbox(
        "Year", YEARS, index=len(YEARS)-1, key="single_year"
    )
    baseline = comparison = selected_year

st.sidebar.caption(
    "Population, income and prices uses the selected year. "
    "When comparing years, it uses the To year."
)
st.markdown('<div class="page-kicker">MALAYSIA · COST OF LIVING</div>', unsafe_allow_html=True)
st.title("Cost of Living Dashboard")

if page.startswith("01"):
    st.markdown('<div class="filter-heading">ANALYSIS FILTERS</div>', unsafe_allow_html=True)
    f1, f2 = st.columns([1, 1])
    with f1:
        if "income_measure_widget" not in st.session_state:
            st.session_state["income_measure_widget"] = st.session_state.get(
                "shared_income_measure", "Mean income"
            )
        income_measure_label = st.selectbox(
            "Income measure", ["Mean income", "Median income"],
            key="income_measure_widget", on_change=save_income_measure
        )
        st.session_state["shared_income_measure"] = income_measure_label
    with f2:
        selected_states = st.multiselect(
            "State", STATES, default=[], help="Leave empty to show all states."
        )

    measure_col = "income_mean" if income_measure_label == "Mean income" else "income_median"

    if view_mode == "Compare years":
        # Keep every state in the chart. The selected state(s) are highlighted;
        # all other states remain visible in grey for context.
        growth_all = calc.growth_comparison(df, baseline, comparison, measure_col)
        growth_all = growth_all.sort_values("gap", ascending=False)

        # Summary cards and best/worst state insights follow the selected state filter.
        growth = growth_all[growth_all.state.isin(selected_states)] if selected_states else growth_all.copy()
        if growth.empty:
            st.warning("No data available for this selection.")
            st.stop()

        avg_income_growth = growth["income_growth"].mean()
        avg_price_growth = growth["price_growth"].mean()
        avg_gap = growth["gap"].mean()

        k1, k2, k3 = st.columns(3)
        k1.metric("Average income growth", f"{avg_income_growth:+.1f}%")
        k2.metric("Average price growth", f"{avg_price_growth:+.1f}%")
        k3.metric("Income–price gap", f"{avg_gap:+.1f} pp",
                  help="Income growth minus price growth, in percentage points.")

        most_improved = growth.loc[growth["gap"].idxmax()]
        least_improved = growth.loc[growth["gap"].idxmin()]
        s1, s2 = st.columns(2)
        s1.metric("Highest income–price gap", short_state(most_improved["state"]),
                  delta=f"{most_improved['gap']:+.1f} pp")
        s2.metric("Lowest income–price gap", short_state(least_improved["state"]),
                  delta=f"{least_improved['gap']:+.1f} pp")

        income_name = f"{income_measure_label} household income"
        st.subheader(f"Income and price growth by state")
        chart_growth = growth_all.sort_values("income_growth", ascending=False).copy()
        chart_growth["state_label"] = chart_growth.state.map(short_state)

        # Match the reference: paired horizontal bars, clear category colours,
        # and percentage labels at the end of each bar.
        income_blue = "#2864E8"
        price_orange = "#F05A0A"
        selected_set = set(selected_states)
        if selected_states:
            income_colors = [
                income_blue if state in selected_set else "#D9DEE5"
                for state in chart_growth.state
            ]
            price_colors = [
                price_orange if state in selected_set else "#E5E7EB"
                for state in chart_growth.state
            ]
        else:
            income_colors = [income_blue] * len(chart_growth)
            price_colors = [price_orange] * len(chart_growth)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=chart_growth.state_label,
            x=chart_growth.income_growth,
            name=income_name,
            orientation="h",
            marker_color=income_colors,
            text=[f"{v:.0f}%" for v in chart_growth.income_growth],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>" + income_name
                          + ": %{x:.1f}%<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            y=chart_growth.state_label,
            x=chart_growth.price_growth,
            name="Prices (CPI)",
            orientation="h",
            marker_color=price_colors,
            text=[f"{v:.0f}%" for v in chart_growth.price_growth],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Prices (CPI): %{x:.1f}%<extra></extra>"
        ))
        max_value = max(
            float(chart_growth.income_growth.max()),
            float(chart_growth.price_growth.max()),
            0
        )
        min_value = min(
            float(chart_growth.income_growth.min()),
            float(chart_growth.price_growth.min()),
            0
        )
        fig.update_layout(
            barmode="group",
            yaxis_title="",
            xaxis_title="Growth (%)",
            bargap=.25,
            bargroupgap=.08,
            legend_title="",
            height=max(590, 34 * len(chart_growth) + 120),
            margin=dict(l=28, r=65, t=55, b=45)
        )
        fig.update_yaxes(
            categoryorder="array",
            categoryarray=chart_growth.state_label.tolist(),
            autorange="reversed",
            tickfont=dict(size=11)
        )
        fig.update_xaxes(
            ticksuffix="%",
            showgrid=True,
            gridcolor=GRID,
            zeroline=True,
            zerolinecolor="#AAB5BF",
            range=[min(0, min_value * 1.12), max_value * 1.16 if max_value > 0 else 1]
        )
        st.plotly_chart(
            chart_layout(fig, max(590, 34 * len(chart_growth) + 120)),
            use_container_width=True,
            config=PLOT_CONFIG
        )

    else:
        snap_all = calc.population_income_snapshot(df, selected_year)
        snap = snap_all[snap_all.state.isin(selected_states)] if selected_states else snap_all.copy()
        if snap.empty:
            st.warning("No data available for this selection.")
            st.stop()

        income_avg = snap[measure_col].mean()
        cpi_avg = snap["cpi"].mean()
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Average {income_measure_label.lower()}",
                  f"RM {income_avg:,.0f}")
        k2.metric("Average Overall CPI", f"{cpi_avg:.1f}")
        k3.metric("States selected", f"{len(snap)}")

        st.subheader(f"{income_measure_label} and Overall CPI by state · {selected_year}")
        chart_data = snap_all.copy()
        chart_data["state_label"] = chart_data.state.map(short_state)
        # Keep every state visible. Selected state(s) use the main colour;
        # the remaining states stay muted for geographic context.
        selected_set = set(selected_states)
        bar_colors = [
            TEAL if (not selected_states or state in selected_set) else "#D9DEE5"
            for state in chart_data.state
        ]

        # Paired horizontal bars. Income and CPI use independent scales
        # because they are measured in different units.
        chart_data = snap_all.copy()
        chart_data["state_label"] = chart_data.state.map(short_state)
        chart_data = chart_data.sort_values("state_label").reset_index(drop=True)

        selected_set = set(selected_states)
        income_blue, cpi_orange = "#2864E8", "#F05A0A"
        income_colors = [
            income_blue if (not selected_states or state in selected_set) else "#D9DEE5"
            for state in chart_data.state
        ]
        cpi_colors = [
            cpi_orange if (not selected_states or state in selected_set) else "#E5E7EB"
            for state in chart_data.state
        ]

        positions = list(range(len(chart_data)))
        income_y = [p - 0.20 for p in positions]
        cpi_y = [p + 0.20 for p in positions]
        chart_height = max(610, 48 * len(chart_data) + 165)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data[measure_col], y=income_y, xaxis="x",
            orientation="h", width=0.30, marker_color=income_colors,
            name=f"{income_measure_label} household income",
            text=[f"RM {v:,.0f}" for v in chart_data[measure_col]],
            textposition="outside", cliponaxis=False,
            customdata=chart_data.state_label,
            hovertemplate="<b>%{customdata}</b><br>" + income_measure_label
                          + ": RM %{x:,.0f} per month<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            x=chart_data["cpi"], y=cpi_y, xaxis="x2",
            orientation="h", width=0.30, marker_color=cpi_colors,
            name="Overall CPI",
            text=[f"{v:.1f}" for v in chart_data["cpi"]],
            textposition="outside", cliponaxis=False,
            customdata=chart_data.state_label,
            hovertemplate="<b>%{customdata}</b><br>Overall CPI: %{x:.1f}<extra></extra>"
        ))

        fig.update_layout(
            template="plotly_white",
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            font=dict(family=FONT, color=INK, size=12),
            height=chart_height,
            margin=dict(l=105, r=100, t=155, b=95),
            barmode="overlay",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.22,
                xanchor="left", x=0,
                bgcolor="rgba(255,255,255,0)"
            ),
            hoverlabel=dict(bgcolor="#17212B", font_color=WHITE, font_size=12),
            xaxis=dict(
                title=dict(text=f"{income_measure_label} household income (RM/month)", standoff=18),
                domain=[0, 1],
                range=[0, float(chart_data[measure_col].max()) * 1.20],
                showgrid=True, gridcolor=GRID, zeroline=False,
                side="bottom", tickprefix="RM ", automargin=True
            ),
            xaxis2=dict(
                title=dict(text="Overall CPI index", standoff=8),
                overlaying="x", anchor="y", side="top", position=1,
                range=[0, float(chart_data["cpi"].max()) * 1.20],
                showgrid=False, zeroline=False, tickformat=".1f",
                automargin=True
            ),
            yaxis=dict(
                tickmode="array",
                tickvals=positions,
                ticktext=chart_data.state_label.tolist(),
                range=[len(chart_data) - 0.5, -0.5],
                showgrid=False, zeroline=False, title="",
                automargin=True
            )
        )
        st.plotly_chart(
            chart_layout(fig, chart_height),
            use_container_width=True,
            config=PLOT_CONFIG
        )

elif page.startswith("02"):
    year = selected_year
    income_measure_label = st.session_state.get("shared_income_measure", "Mean income")
    measure_col = "income_mean" if income_measure_label == "Mean income" else "income_median"
    snap = calc.population_income_snapshot(df, year)
    
    st.markdown('<div class="filter-heading">ANALYSIS FILTERS</div>', unsafe_allow_html=True)
    selected_states_2 = st.multiselect(
        "State", STATES, default=[], key="obj2_states",
        help="Leave empty to show all states."
    )
    if selected_states_2:
        snap = snap[snap.state.isin(selected_states_2)]
    if snap.empty:
        st.warning("Select at least one state to display.")
        st.stop()

    snap["state_label"] = snap.state.map(short_state)
    st.subheader(f"Population, {income_measure_label.lower()} and prices · {year}")
    fig = px.scatter(
        snap, x="population", y=measure_col, color="cpi",
        color_continuous_scale=["#BFE7E2", "#55AAA1", "#155E59"],
        hover_name="state_label",
        hover_data={"population":":,.0f", measure_col:"RM {:,.0f}", "cpi":":.1f",
                    "state":False, "state_label":False},
        opacity=.88
    )
    fig.update_traces(marker=dict(size=13, line=dict(color="#FFFFFF", width=1.2)),
                      hovertemplate="<b>%{hovertext}</b><br>Population: %{x:,.0f} thousand persons<br>" + income_measure_label + " monthly household income: RM %{y:,.0f}<br>Overall CPI: %{marker.color:.1f}<extra></extra>")
    fig.update_layout(
        xaxis_title="Population (thousand persons)",
        yaxis_title=f"{income_measure_label} monthly household income (RM)",
        coloraxis_colorbar=dict(title="Overall CPI", thickness=13, len=.72),
        height=650
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)

else:
    # Objective 3: two clear views — national overview or one selected state.
    st.markdown('<div class="filter-heading">ANALYSIS FILTERS</div>', unsafe_allow_html=True)
    obj3_view = st.radio(
        "Area",
        ["Overall Malaysia", "By State"],
        horizontal=True,
        key="obj3_view"
    )

    if obj3_view == "Overall Malaysia":
        if view_mode == "Compare years":
            rank = calc.category_growth_national(df, baseline, comparison)
            value_col = "price_growth"
            chart_title = "Price growth by spending category"
            axis_title = "Price growth (%)"
            hover_label = "Price growth"
        else:
            selected = df[(df.year == selected_year) & (df.division != "Overall")]
            rank = (selected.groupby("division", as_index=False)["index"]
                    .mean().rename(columns={"division": "category", "index": "cpi_index"}))
            value_col = "cpi_index"
            chart_title = f"Price index by spending category · {selected_year}"
            axis_title = "CPI index"
            hover_label = "CPI index"

        rank = rank.sort_values(value_col, ascending=False).reset_index(drop=True)
        labels = rank.category.tolist()
        values = rank[value_col].tolist()

        # Lollipop chart: thin stems and clear dots make category ranking lighter.
        fig = go.Figure()
        for label, value in zip(labels, values):
            fig.add_trace(go.Scatter(
                x=[0, value], y=[label, label],
                mode="lines", line=dict(color="#D8E0E7", width=2),
                hoverinfo="skip", showlegend=False
            ))
        marker_colors = [TEAL if value >= 0 else CORAL for value in values]
        fig.add_trace(go.Scatter(
            x=values, y=labels, mode="markers",
            marker=dict(size=13, color=marker_colors, line=dict(color=WHITE, width=1.5)),
            name=hover_label,
            customdata=labels,
            hovertemplate="<b>%{customdata}</b><br>" + hover_label + ": %{x:.1f}"
                           + ("%" if view_mode == "Compare years" else "") + "<extra></extra>"
        ))
        fig.update_layout(
            xaxis_title=axis_title, yaxis_title="", showlegend=False,
            height=590
        )
        fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True,
                         zerolinecolor="#8793A1", zerolinewidth=1.4,
                         ticksuffix="%" if view_mode == "Compare years" else "")
        st.subheader(chart_title)
        st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)

    else:
        selected_state = st.selectbox(
            "State", STATES, index=STATES.index("Kelantan") if "Kelantan" in STATES else 0,
            key="obj3_selected_state"
        )

        if view_mode == "Compare years":
            rows = []
            for category in CATEGORIES:
                category_data = calc.category_state_growth(df, baseline, comparison, category)
                match = category_data[category_data.state.eq(selected_state)]
                if not match.empty:
                    rows.append({
                        "category": category,
                        "price_growth": float(match.iloc[0]["price_growth"])
                    })
            rank = pd.DataFrame(rows)
            value_col = "price_growth"
            chart_title = f"Price growth by category · {short_state(selected_state)}"
            axis_title = "Price growth (%)"
            hover_label = "Price growth"
        else:
            selected = df[
                (df.year == selected_year) &
                (df.state == selected_state) &
                (df.division != "Overall")
            ][["division", "index"]].copy()
            rank = selected.rename(columns={"division": "category", "index": "cpi_index"})
            value_col = "cpi_index"
            chart_title = f"Price index by category · {short_state(selected_state)}"
            axis_title = "CPI index"
            hover_label = "CPI index"

        if rank.empty:
            st.warning("No category data is available for this state and period.")
            st.stop()

        rank = rank.sort_values(value_col, ascending=False).reset_index(drop=True)
        labels = rank.category.tolist()
        values = rank[value_col].tolist()
        state_bar_colors = [TEAL if value >= 0 else CORAL for value in values]
        fig = go.Figure(go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=state_bar_colors, line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>" + hover_label + ": %{x:.1f}"
                           + ("%" if view_mode == "Compare years" else "") + "<extra></extra>"
        ))
        fig.update_layout(
            xaxis_title=axis_title, yaxis_title="", showlegend=False,
            bargap=.28, height=590
        )
        fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=True,
                         zerolinecolor="#8793A1", zerolinewidth=1.4,
                         ticksuffix="%" if view_mode == "Compare years" else "")
        st.subheader(chart_title)
        st.plotly_chart(chart_layout(fig, 590), use_container_width=True, config=PLOT_CONFIG)
