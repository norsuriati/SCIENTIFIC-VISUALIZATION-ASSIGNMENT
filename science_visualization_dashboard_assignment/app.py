"""Malaysia: Income, Prices & Population - Cost of Living by State
JIE42403 Scientific Visualisation.  Run:  streamlit run streamlit_app.py
One objective = one page = one chart."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

import analysis as A

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = [[0, "#cde2fb"], [0.25, "#6da7ec"], [0.5, "#2a78d6"], [0.75, "#184f95"], [1, "#0d366b"]]


@st.cache_data
def get_data():
    pop, inc, cpi = A.load()
    m = A.state_metrics(inc, cpi, pop)
    return cpi, m


cpi, M = get_data()
M["label"] = [A.short(s) for s in M.index]


def card(label, value, sub=""):
    st.caption(label)
    st.markdown(f"#### {value}")
    if sub:
        st.caption(sub)


st.sidebar.title("📊 Cost of Living in Malaysia")
page = st.sidebar.radio("Objective", ["Objective 1", "Objective 2", "Objective 3"])
st.sidebar.caption("Data: DOSM household income, CPI (2010 = 100) and population by state, 2012–2024. "
                   "CPI shows how fast prices *rose*, not which state is more expensive.")

# ================================================================== OBJECTIVE 1
if page == "Objective 1":
    gap = M.inc_med_growth - M.cpi_growth
    real = M.real_med_idx
    st.title("Objective 1")
    st.markdown("**To compare income growth and price growth in each state** "
                "*(to identify which states became more affordable and which are falling behind).*")
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Income beat prices", f"{(gap > 0).sum()} of {len(gap)} states")
        with c[1]: card("Average growth", f"+{M.inc_med_growth.mean():.0f}% income", f"vs +{M.cpi_growth.mean():.0f}% prices")
        with c[2]: card("Biggest gain", A.short(real.idxmax()), f"real income ×{real.max()/100:.2f}")
        with c[3]: card("Smallest gain", A.short(real.idxmin()), f"real income ×{real.min()/100:.2f}")
        with c[4]: card("Highest price growth", A.short(M.cpi_growth.idxmax()), f"+{M.cpi_growth.max():.0f}%")

    st.markdown("##### Bar chart: income growth vs price growth, 2012 → 2024")
    d = pd.DataFrame({"inc": M.inc_med_growth, "cpi": M.cpi_growth, "gap": gap}).sort_values("gap")
    names = [A.short(i) for i in d.index]
    f = go.Figure()
    f.add_trace(go.Bar(y=names, x=d.cpi, name="Prices (CPI)", orientation="h", marker_color=ORANGE))
    f.add_trace(go.Bar(y=names, x=d.inc, name="Median household income", orientation="h", marker_color=BLUE))
    f.update_layout(barmode="group", bargap=0.25, height=620, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.05))
    f.update_xaxes(title="% increase 2012 → 2024")
    st.plotly_chart(f)
    st.caption("States are sorted by the gap (income growth minus price growth): smallest gap at the bottom, largest at the top.")

    with st.expander("Interpretation", expanded=True):
        top = gap.sort_values(ascending=False).head(3); low = gap.sort_values().head(3)
        st.markdown(f"""
* **Incomes grew faster than prices in every state.** Median income rose {M.inc_med_growth.min():.0f}–{M.inc_med_growth.max():.0f}%, while prices rose only {M.cpi_growth.min():.0f}–{M.cpi_growth.max():.0f}%. People can afford more than in 2012 everywhere.
* **Biggest winners:** {', '.join(A.short(i) for i in top.index)} (income grew {top.iloc[0]:.0f}, {top.iloc[1]:.0f} and {top.iloc[2]:.0f} points faster than prices).
* **Falling behind:** {', '.join(A.short(i) for i in low.index)}, where income growth beat price growth by only {low.iloc[0]:.0f}–{low.iloc[2]:.0f} points. Putrajaya has the weakest real gain overall: prices rose {M.cpi_growth['W.P. Putrajaya']:.0f}% (highest of all) but income only {M.inc_med_growth['W.P. Putrajaya']:.0f}%.
* **Fast price growth does not always mean less affordable.** Selangor had very high price growth (+{M.cpi_growth['Selangor']:.0f}%) but income doubled (+{M.inc_med_growth['Selangor']:.0f}%).
* **Caution:** low-income states such as Terengganu and Perlis show big gains partly because they started from a low income in 2012.""")

# ================================================================== OBJECTIVE 2
elif page == "Objective 2":
    r1 = stats.spearmanr(M.pop_end, M.inc_med_end); r2 = stats.spearmanr(M.pop_end, M.cpi_growth)
    r3 = stats.spearmanr(M.pop_growth, M.cpi_growth)
    top3 = M.pop_end.nlargest(3)
    st.title("Objective 2")
    st.markdown("**To examine whether states with more people also have higher income and prices** "
                "*(to find where cost-of-living pressure is greatest).*")
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Malaysia population 2024", f"{M.pop_end.sum()/1000:.1f} M")
        with c[1]: card("Top 3 states", f"{top3.sum()/M.pop_end.sum()*100:.0f}% of people", ", ".join(A.short(i) for i in top3.index))
        with c[2]: card("Population vs income", f"ρ = {r1[0]:+.2f}", "no clear link" if abs(r1[0]) < 0.3 else "linked")
        with c[3]: card("Population vs price growth", f"ρ = {r2[0]:+.2f}", "weak link" if abs(r2[0]) < 0.4 else "linked")
        with c[4]: card("Highest price growth", A.short(M.cpi_growth.idxmax()), f"+{M.cpi_growth.max():.0f}%")

    st.markdown("##### Scatter plot: population vs household income, 2024 (colour = price growth since 2012)")
    f = go.Figure(go.Scatter(
        x=M.pop_end, y=M.inc_med_end, mode="markers+text", text=M.label, textposition="top center",
        marker=dict(size=16, color=M.cpi_growth, colorscale=SEQ, showscale=True, colorbar=dict(title="Price<br>growth %"),
                    line=dict(width=1.5, color="white")),
        hovertemplate="<b>%{text}</b><br>Population %{x:,.0f}k<br>Median income RM%{y:,.0f}<extra></extra>"))
    f.update_xaxes(type="log", title="Population 2024 ('000, log scale)")
    f.update_yaxes(title="Median household income 2024 (RM)")
    f.update_layout(height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(f)
    st.caption("Each dot is one state. Darker dot = prices rose more between 2012 and 2024.")

    with st.expander("Interpretation", expanded=True):
        st.markdown(f"""
* **More people does not mean higher income.** The correlation between population and income is ρ = {r1[0]:+.2f} (p = {r1[1]:.2f}), which is no real link. Selangor is the largest state and one of the richest, but Sabah and Perak have many people and low income.
* **Small states can be rich.** KL, Putrajaya and Labuan have few people but high income.
* **Dark dots (fast price growth) sit at the top.** The richest states (Putrajaya, Selangor, KL, Johor, Penang) also had the biggest price rises, so pressure comes more from wealth and urban demand than from head-count. Population size and price growth are only weakly related (ρ = {r2[0]:+.2f}), but states whose population grew faster also saw faster price rises (ρ = {r3[0]:+.2f}).
* **Where pressure is greatest:** Putrajaya (+{M.cpi_growth['W.P. Putrajaya']:.0f}%), Selangor (+{M.cpi_growth['Selangor']:.0f}%) and Johor (+{M.cpi_growth['Johor']:.0f}%). Low-income, low-price-growth states such as Kelantan and Perak face a different problem: low income, not rising prices.
* **Caution:** only 16 states, so these patterns are indications, not proof.""")

# ================================================================== OBJECTIVE 3
else:
    DG = A.division_growth(cpi)
    nat = DG.mean().sort_values(ascending=False)
    ess = DG[A.ESSENTIALS]
    tot = ess.sum(axis=1).sort_values()
    st.title("Objective 3")
    st.markdown("**To identify which spending categories, such as food, housing and transport, push prices up the most** "
                "*(to rank states by overall cost-of-living pressure).*")
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Fastest-rising category", nat.index[0].split(" &")[0], f"+{nat.iloc[0]:.0f}% on average")
        with c[1]: card("Food & Beverages", f"+{nat['Food & Beverages']:.0f}%", "average of 16 states")
        with c[2]: card("Housing & Utilities", f"+{nat['Housing & Utilities']:.0f}%", "average of 16 states")
        with c[3]: card("Highest pressure", A.short(tot.index[-1]), f"food +{ess.loc[tot.index[-1], 'Food & Beverages']:.0f}%")
        with c[4]: card("Lowest pressure", A.short(tot.index[0]), f"food +{ess.loc[tot.index[0], 'Food & Beverages']:.0f}%")

    st.markdown("##### Stacked bar: price rise in food, housing and transport by state, 2012 → 2024")
    names = [A.short(s) for s in tot.index]
    f = go.Figure()
    for k, colr in zip(A.ESSENTIALS, [BLUE, ORANGE, AQUA]):
        f.add_trace(go.Bar(y=names, x=ess.loc[tot.index, k], name=k, orientation="h", marker_color=colr,
                           hovertemplate=k + ": +%{x:.1f}%<extra></extra>"))
    f.update_layout(barmode="stack", bargap=0.25, height=620, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.05))
    f.update_xaxes(title="Price rise (%), the three categories added together")
    st.plotly_chart(f)
    st.caption("States are ranked by the total of the three bars: longest bar = highest cost-of-living pressure from essentials.")

    with st.expander("Interpretation", expanded=True):
        t3 = list(tot.index[::-1][:3]); b3 = list(tot.index[:3])
        st.markdown(f"""
* **Categories that push prices up the most.** Across all states the biggest rises were {nat.index[0]} (+{nat.iloc[0]:.0f}%), {nat.index[1]} (+{nat.iloc[1]:.0f}%) and {nat.index[2]} (+{nat.iloc[2]:.0f}%). Information & Communication and Clothing fell, so not every price went up.
* **Food is the biggest everyday pressure.** Food & Beverages rose +{nat['Food & Beverages']:.0f}% on average, compared with +{nat['Housing & Utilities']:.0f}% for housing and +{nat['Transport'].round(0):.0f}% for transport.
* **Highest pressure:** {', '.join(A.short(i) for i in t3)}. In these states food, housing and transport all rose strongly (food +{ess.loc[t3[0], 'Food & Beverages']:.0f}% in {A.short(t3[0])}).
* **Lowest pressure:** {', '.join(A.short(i) for i in b3)}, where the three essentials rose the least.
* **Caution:** the three bars are simply added together, not weighted by how much households spend on each. The chart shows how fast prices rose, not how expensive each state is.""")

st.caption("Source: Department of Statistics Malaysia (DOSM). JIE42403 Scientific Visualisation.")
