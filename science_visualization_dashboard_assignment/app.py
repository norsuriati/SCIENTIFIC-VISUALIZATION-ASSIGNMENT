"""Malaysia: Income, Prices & Population - Cost of Living by State
JIE42403 Scientific Visualisation.  Run:  streamlit run streamlit_app.py
One objective = one page = one chart.  Sidebar filters (State, Year) apply to every page."""
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
    return A.load()


pop, inc, cpi = get_data()
ALL = sorted(inc.state.unique())


def card(label, value, sub=""):
    st.caption(label)
    st.markdown(f"#### {value}")
    if sub:
        st.caption(sub)


def height(n, per=34, base=150):
    return int(max(380, per * n + base))


def level(r, strong=0.5, weak=0.25):
    a = abs(r)
    return "a strong" if a >= strong else ("a moderate" if a >= weak else "almost no")


# ------------------------------------------------------------------ sidebar
st.sidebar.title("📊 Cost of Living in Malaysia")
page = st.sidebar.radio("Objective", ["Objective 1", "Objective 2", "Objective 3"])
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
sel = st.sidebar.multiselect("State", ALL, default=ALL, format_func=A.short)
y0, y1 = st.sidebar.select_slider("Year (compare from → to)", options=A.SURVEY_YEARS, value=(A.BASE_YEAR, A.END_YEAR))
st.sidebar.caption("Filters apply to all three objectives. Growth is measured from the first year to the second year. "
                   "CPI shows how fast prices *rose*, not which state is more expensive.")
if not sel:
    st.warning("No state selected: showing all states.")
    sel = ALL
if y0 >= y1:
    st.warning("Choose two different years (the first must be earlier than the second).")
    st.stop()

M = A.metrics(inc, cpi, pop, y0, y1).loc[sel]
n = len(M)
period = f"{y0} → {y1}"
subtitle = f"{n} state{'s' if n > 1 else ''} · {period}"

# ================================================================== OBJECTIVE 1
if page == "Objective 1":
    gap = M.inc_med_growth - M.cpi_growth
    real = M.real_med_idx
    st.title("Objective 1")
    st.markdown("**To compare income growth and price growth in each state** "
                "*(to identify which states became more affordable and which are falling behind).*")
    st.caption(subtitle)
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Income beat prices", f"{(gap > 0).sum()} of {n} states")
        with c[1]: card("Average growth", f"+{M.inc_med_growth.mean():.0f}% income", f"vs +{M.cpi_growth.mean():.0f}% prices")
        with c[2]: card("Biggest real gain", A.short(real.idxmax()), f"real income ×{real.max()/100:.2f}")
        with c[3]: card("Smallest real gain", A.short(real.idxmin()), f"real income ×{real.min()/100:.2f}")
        with c[4]: card("Highest price growth", A.short(M.cpi_growth.idxmax()), f"+{M.cpi_growth.max():.0f}%")

    st.markdown(f"##### Bar chart: income growth vs price growth, {period}")
    d = pd.DataFrame({"inc": M.inc_med_growth, "cpi": M.cpi_growth, "gap": gap}).sort_values("gap")
    names = [A.short(i) for i in d.index]
    f = go.Figure()
    f.add_trace(go.Bar(y=names, x=d.cpi, name="Prices (CPI)", orientation="h", marker_color=ORANGE))
    f.add_trace(go.Bar(y=names, x=d.inc, name="Median household income", orientation="h", marker_color=BLUE))
    f.update_layout(barmode="group", bargap=0.25, height=height(n, 38), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.04))
    f.update_xaxes(title=f"% increase {period}")
    st.plotly_chart(f)
    st.caption("Sorted by the gap (income growth minus price growth): largest gap at the top.")

    with st.expander("Interpretation", expanded=True):
        k = min(3, n)
        top = gap.sort_values(ascending=False).head(k); low = gap.sort_values().head(k)
        w = real.idxmin()
        beat = "every selected state" if (gap > 0).all() else f"{(gap > 0).sum()} of {n} states"
        st.markdown(f"""
* **Income vs prices.** Between {y0} and {y1}, median income grew faster than prices in {beat}. Income rose {M.inc_med_growth.min():.0f}–{M.inc_med_growth.max():.0f}% while prices rose {M.cpi_growth.min():.0f}–{M.cpi_growth.max():.0f}%.
* **Biggest winners:** {', '.join(f"{A.short(i)} (+{v:.0f} pts)" for i, v in top.items())}, where income growth beat price growth by the widest margin.
* **Falling behind:** {', '.join(f"{A.short(i)} ({v:+.0f} pts)" for i, v in low.items())}, where the gap between income and price growth is smallest.
* **Weakest real gain:** {A.short(w)}. Prices rose {M.cpi_growth[w]:.0f}% but median income rose {M.inc_med_growth[w]:.0f}%, so real purchasing power changed by only {real[w]-100:+.0f}%.
* **Caution:** a state that starts with low income can show a big percentage gain; growth does not show how affordable a state is today.""")

# ================================================================== OBJECTIVE 2
elif page == "Objective 2":
    st.title("Objective 2")
    st.markdown("**To examine whether states with more people also have higher income and prices** "
                "*(to find where cost-of-living pressure is greatest).*")
    st.caption(subtitle)
    enough = n >= 5
    if enough:
        r1 = stats.spearmanr(M.pop_end, M.inc_med_end); r2 = stats.spearmanr(M.pop_end, M.cpi_growth)
        r4 = stats.spearmanr(M.inc_med_end, M.cpi_growth)
    top3 = M.pop_end.nlargest(min(3, n))
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card(f"Population {y1}", f"{M.pop_end.sum()/1000:.1f} M", "selected states")
        with c[1]: card("Largest states", f"{top3.sum()/M.pop_end.sum()*100:.0f}% of people", ", ".join(A.short(i) for i in top3.index))
        with c[2]: card("Population vs income", f"ρ = {r1[0]:+.2f}" if enough else "n/a", "needs 5+ states" if not enough else "")
        with c[3]: card("Population vs price growth", f"ρ = {r2[0]:+.2f}" if enough else "n/a", "needs 5+ states" if not enough else "")
        with c[4]: card("Highest price growth", A.short(M.cpi_growth.idxmax()), f"+{M.cpi_growth.max():.0f}%")

    st.markdown(f"##### Scatter plot: population vs household income in {y1} (colour = price growth {period})")
    f = go.Figure(go.Scatter(
        x=M.pop_end, y=M.inc_med_end, mode="markers+text", text=M.label, textposition="top center",
        marker=dict(size=16, color=M.cpi_growth, colorscale=SEQ, showscale=True, colorbar=dict(title="Price<br>growth %"),
                    line=dict(width=1.5, color="white")),
        hovertemplate="<b>%{text}</b><br>Population %{x:,.0f}k<br>Median income RM%{y:,.0f}<extra></extra>"))
    f.update_xaxes(type="log", title=f"Population {y1} ('000, log scale)")
    f.update_yaxes(title=f"Median household income {y1} (RM)")
    f.update_layout(height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(f)
    st.caption("Each dot is one state. Darker dot = prices rose more over the selected period.")

    with st.expander("Interpretation", expanded=True):
        rich = M.inc_med_end.idxmax(); big = M.pop_end.idxmax(); topp = M.cpi_growth.sort_values(ascending=False).head(min(3, n))
        lines = []
        if enough:
            lines.append(f"* **Population and income.** There is {level(r1[0])} link between population size and median income (ρ = {r1[0]:+.2f}, p = {r1[1]:.2f}). {A.short(big)} has the most people ({M.pop_end[big]/1000:.1f} M), while {A.short(rich)} has the highest income (RM{M.inc_med_end[rich]:,.0f}).")
            lines.append(f"* **Population and prices.** There is {level(r2[0])} link between population size and price growth (ρ = {r2[0]:+.2f}). Income level and price growth show {level(r4[0])} link (ρ = {r4[0]:+.2f}, p = {r4[1]:.3f}): " +
                         ("richer states saw faster price rises, so pressure follows wealth and urban demand more than head-count." if r4[0] >= 0.25 else "price rises did not follow income level in this selection."))
        else:
            lines.append(f"* Select at least 5 states to see correlations. {A.short(big)} has the most people ({M.pop_end[big]/1000:.1f} M); {A.short(rich)} has the highest income (RM{M.inc_med_end[rich]:,.0f}).")
        lines.append(f"* **Where pressure is greatest:** {', '.join(f'{A.short(i)} (+{v:.0f}%)' for i, v in topp.items())} had the fastest price growth over {period}.")
        lines.append("* **Caution:** only 16 states at most, so these patterns are indications, not proof; correlation is not causation.")
        st.markdown("\n".join(lines))

# ================================================================== OBJECTIVE 3
else:
    DG = A.division_growth(cpi, y0, y1).loc[sel]
    nat = DG.mean().sort_values(ascending=False)
    ess = DG[A.ESSENTIALS]
    tot = ess.sum(axis=1).sort_values()
    st.title("Objective 3")
    st.markdown("**To identify which spending categories, such as food, housing and transport, push prices up the most** "
                "*(to rank states by overall cost-of-living pressure).*")
    st.caption(subtitle)
    with st.container(border=True):
        st.subheader("Summary box")
        c = st.columns(5)
        with c[0]: card("Fastest-rising category", nat.index[0].split(" &")[0], f"+{nat.iloc[0]:.0f}% on average")
        with c[1]: card("Food & Beverages", f"{nat['Food & Beverages']:+.0f}%", "average of selected states")
        with c[2]: card("Housing & Utilities", f"{nat['Housing & Utilities']:+.0f}%", "average of selected states")
        with c[3]: card("Highest pressure", A.short(tot.index[-1]), f"food {ess.loc[tot.index[-1], 'Food & Beverages']:+.0f}%")
        with c[4]: card("Lowest pressure", A.short(tot.index[0]), f"food {ess.loc[tot.index[0], 'Food & Beverages']:+.0f}%")

    st.markdown(f"##### Stacked bar: price rise in food, housing and transport by state, {period}")
    names = [A.short(s) for s in tot.index]
    f = go.Figure()
    for k, colr in zip(A.ESSENTIALS, [BLUE, ORANGE, AQUA]):
        f.add_trace(go.Bar(y=names, x=ess.loc[tot.index, k], name=k, orientation="h", marker_color=colr,
                           hovertemplate=k + ": %{x:+.1f}%<extra></extra>"))
    f.update_layout(barmode="stack", bargap=0.25, height=height(n, 38), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.04))
    f.update_xaxes(title="Price rise (%), the three categories added together")
    st.plotly_chart(f)
    st.caption("Ranked by the total of the three bars: longest bar = highest cost-of-living pressure from essentials.")

    with st.expander("Interpretation", expanded=True):
        k = min(3, n)
        t3 = list(tot.index[::-1][:k]); b3 = list(tot.index[:k])
        fell = [c_ for c_, v in nat.items() if v < 0]
        st.markdown(f"""
* **Categories that push prices up the most.** Over {period}, the biggest average rises were {nat.index[0]} ({nat.iloc[0]:+.0f}%), {nat.index[1]} ({nat.iloc[1]:+.0f}%) and {nat.index[2]} ({nat.iloc[2]:+.0f}%)."""
                    + (f" {', '.join(fell)} fell, so not every price went up." if fell else "") + f"""
* **Everyday essentials.** Food & Beverages changed {nat['Food & Beverages']:+.0f}% on average, Housing & Utilities {nat['Housing & Utilities']:+.0f}% and Transport {nat['Transport']:+.0f}%.
* **Highest pressure:** {', '.join(A.short(i) for i in t3)}, where the three essentials rose the most (for example food {ess.loc[t3[0], 'Food & Beverages']:+.0f}% in {A.short(t3[0])}).
* **Lowest pressure:** {', '.join(A.short(i) for i in b3)}, where the three essentials rose the least.
* **Caution:** the three bars are simply added together, not weighted by how much households spend on each. The chart shows how fast prices rose, not how expensive each state is.""")

st.caption("Source: Department of Statistics Malaysia (DOSM). JIE42403 Scientific Visualisation.")
