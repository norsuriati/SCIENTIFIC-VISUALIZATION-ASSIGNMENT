"""Malaysia: Income, Prices & Population - Cost of Living by State
JIE42403 Scientific Visualisation.   Run:  streamlit run app.py
One objective = one page = one chart.  Sidebar filters (State, Year range) apply to every page."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

import analysis as A

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

# ------------------------------------------------------------------ design tokens
INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
BLUE, ORANGE, TEAL = "#2563eb", "#ea580c", "#0d9488"
GOOD, BAD = "#047857", "#b91c1c"
SEQ = [[0, "#dbeafe"], [0.5, "#3b82f6"], [1, "#1e3a8a"]]
FONT = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

st.markdown(f"""
<style>
.block-container {{padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px;}}
h1 {{font-size: 1.9rem !important; font-weight: 700 !important; letter-spacing: -0.02em; margin-bottom: .1rem;}}
.tag {{display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
       color:{BLUE}; background:#eff6ff; padding:.2rem .6rem; border-radius:999px; margin-bottom:.5rem;}}
.goal {{color:{MUTED}; font-size:1rem; margin:.2rem 0 .3rem 0; line-height:1.5;}}
.scope {{color:{MUTED}; font-size:.85rem; margin-bottom:1.1rem;}}
.kpi {{background:#fff; border:1px solid {GRID}; border-radius:12px; padding:.9rem 1rem; height:100%;
       box-shadow:0 1px 2px rgba(16,24,40,.04);}}
.kpi .l {{font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:{MUTED};}}
.kpi .v {{font-size:1.5rem; font-weight:700; color:{INK}; line-height:1.25; margin:.15rem 0;}}
.kpi .s {{font-size:.8rem; color:{MUTED};}}
.sec {{font-size:1.05rem; font-weight:650; color:{INK}; margin:1.4rem 0 .1rem 0;}}
.note {{font-size:.82rem; color:{MUTED}; margin-top:-.3rem;}}
section[data-testid="stSidebar"] {{border-right:1px solid {GRID};}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def get_data():
    return A.load()


pop, inc, cpi = get_data()
ALL = sorted(inc.state.unique())
YEARS = [y for y in A.SURVEY_YEARS if y in set(inc.year)]


def metrics(y0, y1):
    med = inc.pivot(index="state", columns="year", values="income_median")
    ca = A.cpi_annual(cpi).reindex(med.index)
    pt = A.pop_total(pop).pivot(index="state", columns="year", values="pop_k").reindex(med.index)
    m = pd.DataFrame(index=med.index)
    m["inc_med_growth"] = (med[y1] / med[y0] - 1) * 100
    m["cpi_growth"] = (ca[y1] / ca[y0] - 1) * 100
    m["gap"] = m.inc_med_growth - m.cpi_growth
    m["real_chg"] = ((med[y1] / med[y0]) / (ca[y1] / ca[y0]) - 1) * 100   # % change in purchasing power
    m["inc_med_end"] = med[y1]
    m["pop_end"] = pt[y1]
    m["pop_growth"] = (pt[y1] / pt[y0] - 1) * 100
    m["label"] = [A.short(x) for x in m.index]
    return m


# ------------------------------------------------------------------ helpers
def kpi(col, label, value, sub=""):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
                 f'<div class="s">{sub}&nbsp;</div></div>', unsafe_allow_html=True)


def show(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:                                  # older Streamlit
        st.plotly_chart(fig, use_container_width=True)


def style(fig, h, **kw):
    fig.update_layout(height=h, template="plotly_white", font=dict(family=FONT, size=13, color=INK),
                      margin=dict(l=10, r=20, t=40, b=10), paper_bgcolor="white", plot_bgcolor="white",
                      hoverlabel=dict(font_size=13), **kw)
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def row_h(n, per=34, base=140):
    return int(max(360, per * n + base))


def header(tag, goal, purpose, scope):
    st.markdown(f'<span class="tag">{tag}</span>', unsafe_allow_html=True)
    st.markdown(f"# {goal}")
    st.markdown(f'<div class="goal">{purpose}</div><div class="scope">{scope}</div>', unsafe_allow_html=True)


def strength(r):
    a = abs(r)
    return "strong" if a >= 0.5 else ("moderate" if a >= 0.25 else "weak")


def names(idx):
    return ", ".join(A.short(i) for i in idx)


# ------------------------------------------------------------------ sidebar
st.sidebar.markdown("## 📊 Cost of Living")
st.sidebar.caption("Malaysia · by state")
page = st.sidebar.radio("Objective", ["1 · Income vs prices", "2 · Population & pressure", "3 · Spending categories"])
st.sidebar.markdown("---")
st.sidebar.markdown("**Filters**")
sel = st.sidebar.multiselect("States", ALL, default=ALL, format_func=A.short)
y0, y1 = st.sidebar.select_slider("Year range", options=YEARS, value=(YEARS[0], YEARS[-1]))
st.sidebar.caption("Years are DOSM household-income survey years. Prices use the annual-average CPI.")

if not sel:
    st.sidebar.info("No state selected, so all states are shown.")
    sel = ALL
if y0 == y1:
    st.info("Start and end year are the same. Move the **Year range** slider so the two ends differ.")
    st.stop()

M = metrics(y0, y1).loc[sel]
n = len(M)
period = f"{y0} → {y1}"
scope = f"{n} state{'s' if n > 1 else ''} · {period}"

# ================================================================== OBJECTIVE 1
if page.startswith("1"):
    header("Objective 1", "Income growth vs price growth",
           "To compare income growth and price growth in each state, and identify which states became "
           "more affordable and which are falling behind.", scope)

    gap, real = M.gap, M.real_chg
    c = st.columns(4)
    kpi(c[0], "Income beat prices", f"{(gap > 0).sum()} of {n}", "states with real income gain")
    kpi(c[1], "Average growth", f"+{M.inc_med_growth.mean():.0f}%", f"income, vs +{M.cpi_growth.mean():.0f}% prices")
    kpi(c[2], "Biggest real gain", A.short(real.idxmax()), f"purchasing power {real.max():+.0f}%")
    kpi(c[3], "Smallest real gain", A.short(real.idxmin()), f"purchasing power {real.min():+.0f}%")

    st.markdown(f'<div class="sec">Median household income growth vs price growth, {period}</div>'
                '<div class="note">States sorted by the gap (income growth minus price growth). '
                'Top = most affordable gain, bottom = falling behind.</div>', unsafe_allow_html=True)
    d = M.assign(gap=gap).sort_values("gap")
    f = go.Figure()
    f.add_trace(go.Bar(y=d.label, x=d.cpi_growth, name="Prices (CPI)", orientation="h", marker_color=ORANGE,
                       text=[f"{v:.0f}%" for v in d.cpi_growth], textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}<br>Prices +%{x:.1f}%<extra></extra>"))
    f.add_trace(go.Bar(y=d.label, x=d.inc_med_growth, name="Median household income", orientation="h", marker_color=BLUE,
                       text=[f"{v:.0f}%" for v in d.inc_med_growth], textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}<br>Income +%{x:.1f}%<extra></extra>"))
    style(f, row_h(n, 40), barmode="group", bargap=0.3, bargroupgap=0.05,
          legend=dict(orientation="h", y=1.06, x=0))
    f.update_xaxes(title=f"% increase, {period}", ticksuffix="%")
    show(f)


# ================================================================== OBJECTIVE 2
elif page.startswith("2"):
    header("Objective 2", "Population, income and prices",
           "To examine whether states with more people also have higher income and prices, "
           "and find where cost-of-living pressure is greatest.", scope)

    enough = n >= 5
    if enough:
        r1 = stats.spearmanr(M.pop_end, M.inc_med_end)
        r2 = stats.spearmanr(M.pop_end, M.cpi_growth)
    top3 = M.pop_end.nlargest(min(3, n))
    c = st.columns(4)
    kpi(c[0], f"Population {y1}", f"{M.pop_end.sum() / 1000:.1f} M", "selected states")
    kpi(c[1], "Largest states", f"{top3.sum() / M.pop_end.sum() * 100:.0f}% of people", names(top3.index))
    kpi(c[2], "Population vs income", f"ρ = {r1[0]:+.2f}" if enough else "n/a",
        f"{strength(r1[0])} link" if enough else "needs 5+ states")
    kpi(c[3], "Population vs price growth", f"ρ = {r2[0]:+.2f}" if enough else "n/a",
        f"{strength(r2[0])} link" if enough else "needs 5+ states")

    st.markdown(f'<div class="sec">Population vs median household income, {y1}</div>'
                f'<div class="note">One dot per state. Darker dot = prices rose more over {period}. '
                'Population is on a log scale because a few states are far larger than the rest.</div>',
                unsafe_allow_html=True)
    f = go.Figure(go.Scatter(
        x=M.pop_end, y=M.inc_med_end, mode="markers+text", text=M.label, textposition="top center",
        textfont=dict(size=12, color=INK),
        marker=dict(size=18, color=M.cpi_growth, colorscale=SEQ, showscale=True,
                    colorbar=dict(title="Price<br>growth %", thickness=14, len=0.8),
                    line=dict(width=1.5, color="white")),
        customdata=M.cpi_growth,
        hovertemplate="<b>%{text}</b><br>Population %{x:,.0f}k<br>Median income RM%{y:,.0f}"
                      "<br>Price growth +%{customdata:.1f}%<extra></extra>"))
    style(f, 600, showlegend=False)
    f.update_xaxes(type="log", title=f"Population {y1} ('000, log scale)")
    f.update_yaxes(title=f"Median household income {y1} (RM)", tickprefix="RM")
    show(f)


# ================================================================== OBJECTIVE 3
else:
    header("Objective 3", "Which spending categories push prices up",
           "To identify which spending categories, such as food, housing and transport, push prices up "
           "the most, and rank states by overall cost-of-living pressure.", scope)

    DG = A.division_growth(cpi, y0, y1).loc[sel]
    nat = DG.mean().sort_values(ascending=False)
    ess = DG[A.ESSENTIALS]
    tot = ess.sum(axis=1).sort_values()

    c = st.columns(4)
    kpi(c[0], "Fastest-rising category", nat.index[0].split(" &")[0], f"+{nat.iloc[0]:.0f}% on average")
    kpi(c[1], "Food & Beverages", f"{nat['Food & Beverages']:+.0f}%", "average of selected states")
    kpi(c[2], "Highest pressure", A.short(tot.index[-1]), f"essentials +{tot.iloc[-1]:.0f}% combined")
    kpi(c[3], "Lowest pressure", A.short(tot.index[0]), f"essentials +{tot.iloc[0]:.0f}% combined")

    st.markdown(f'<div class="sec">Price rise in food, housing and transport by state, {period}</div>'
                '<div class="note">States ranked by the three bars added together: '
                'longest bar = highest cost-of-living pressure from essentials.</div>', unsafe_allow_html=True)
    lab = [A.short(s) for s in tot.index]
    f = go.Figure()
    for k_, colr in zip(A.ESSENTIALS, [BLUE, ORANGE, TEAL]):
        f.add_trace(go.Bar(y=lab, x=ess.loc[tot.index, k_], name=k_, orientation="h", marker_color=colr,
                           hovertemplate=k_ + ": %{x:+.1f}%<extra>%{y}</extra>"))
    f.add_trace(go.Scatter(y=lab, x=tot.values, mode="text", text=[f"{v:.0f}%" for v in tot.values],
                           textposition="middle right", showlegend=False, hoverinfo="skip",
                           textfont=dict(size=12, color=INK)))
    style(f, row_h(n, 38), barmode="stack", bargap=0.3, legend=dict(orientation="h", y=1.06, x=0))
    f.update_xaxes(title="Price rise (%), the three categories added together", ticksuffix="%",
                   range=[min(0, tot.min() * 1.1), tot.max() * 1.12])
    show(f)


st.caption("Source: Department of Statistics Malaysia (DOSM) · JIE42403 Scientific Visualisation")
