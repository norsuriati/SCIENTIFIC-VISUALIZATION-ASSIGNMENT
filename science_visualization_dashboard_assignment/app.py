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

    st.markdown(f'<div class="sec">Income vs price growth, bubble size = population {y1}</div>'
                f'<div class="note">One bubble per state. Further right = higher median income in {y1}; '
                f'higher up = prices rose more over {period}; bigger bubble = more people. Colour = region.</div>',
                unsafe_allow_html=True)
    REG_COL = {"Klang Valley": BLUE, "South": ORANGE, "North": TEAL, "East Coast": "#7c3aed", "East Malaysia": "#64748b"}
    sizeref = 2.0 * M.pop_end.max() / (62 ** 2)
    f = go.Figure()
    for reg, colr in REG_COL.items():
        g = M[[A.REGION[i] == reg for i in M.index]].sort_values("inc_med_end")
        if g.empty:
            continue
        f.add_trace(go.Scatter(
            x=g.inc_med_end, y=g.cpi_growth, mode="markers+text", name=reg, text=g.label,
            textposition=["top center" if i % 2 == 0 else "bottom center" for i in range(len(g))],
            textfont=dict(size=12, color=INK),
            marker=dict(size=g.pop_end, sizemode="area", sizeref=sizeref, sizemin=7, color=colr, opacity=0.78,
                        line=dict(width=1.5, color="white")),
            customdata=np.stack([g.pop_end, g.inc_med_growth], axis=-1),
            hovertemplate="<b>%{text}</b><br>Median income RM%{x:,.0f}<br>Price growth +%{y:.1f}%"
                          "<br>Population %{customdata[0]:,.0f}k<extra></extra>"))
    style(f, 620, legend=dict(orientation="h", y=1.07, x=0, title_text=""))
    f.update_xaxes(title=f"Median household income {y1} (RM)", tickprefix="RM", tickformat=",", automargin=True)
    f.update_yaxes(title=f"Price growth {period} (%)", ticksuffix="%", automargin=True)
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

    st.markdown(f'<div class="sec">Price rise in food, housing and transport, by state, {period}</div>'
                '<div class="note">Each block is one state inside one category. Bigger block = bigger price rise. '
                'A category with more area pushes prices up more overall.</div>', unsafe_allow_html=True)
    ids, labels, parents, values, texts, colors = [], [], [], [], [], []
    for cat, colr in zip(A.ESSENTIALS, [BLUE, ORANGE, TEAL]):
        v = ess[cat].clip(lower=0.01)
        ids.append(cat); labels.append(f"<b>{cat}</b>"); parents.append(""); values.append(float(v.sum()))
        texts.append(f"avg {ess[cat].mean():+.0f}%"); colors.append(colr)
        for st_, val in ess[cat].sort_values(ascending=False).items():
            ids.append(f"{cat}/{st_}"); labels.append(A.short(st_)); parents.append(cat)
            values.append(float(max(val, 0.01))); texts.append(f"{val:+.0f}%"); colors.append(colr)
    f = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, text=texts, branchvalues="total",
        textinfo="label+text", textfont=dict(size=14, color="white"),
        marker=dict(colors=colors, line=dict(width=2, color="white")),
        tiling=dict(pad=4), sort=False, root_color="white",
        hovertemplate="<b>%{label}</b><br>Price rise %{text}<extra></extra>"))
    style(f, 640, showlegend=False)
    f.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    show(f)
    if (ess < 0).any().any():
        st.caption("Some prices fell in this period. A fall cannot be drawn as area, so it shows as a tiny block "
                   "with its real % in the label. Choose a longer year range for a clearer picture.")


st.caption("Source: Department of Statistics Malaysia (DOSM) · JIE42403 Scientific Visualisation")
