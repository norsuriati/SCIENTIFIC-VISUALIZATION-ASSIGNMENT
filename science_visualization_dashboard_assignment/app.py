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
ORSEQ = [[0, "#fbbf77"], [0.5, "#ea580c"], [1, "#7c2d12"]]
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
ALLCATS = sorted(d for d in cpi.division.unique() if d != "Overall")   # the 13 CPI divisions


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


def cat_short(c):
    return c.split(" &")[0].split(",")[0]


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

cats, focus = ALLCATS, "None"
if page.startswith("3"):
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Category filters**")
    cats = st.sidebar.multiselect("Spending categories (13)", ALLCATS, default=ALLCATS, format_func=cat_short)
    if not cats:
        st.sidebar.info("No category selected, so all 13 are shown.")
        cats = ALLCATS
    focus = st.sidebar.selectbox("Highlight a state", ["None"] + list(sel),
                                 format_func=lambda x: x if x == "None" else A.short(x))

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

    st.markdown(f'<div class="sec">Population by state and region, {y1}</div>'
                '<div class="note">Tile size = population (more people = bigger tile). Tile colour = the measure you choose below. '
                'If big tiles are also dark, larger states have higher income or faster price rises. '
                'Region totals are population-weighted averages.</div>', unsafe_allow_html=True)
    basis = st.radio("Colour tiles by", [f"Median income {y1}", f"Price growth {period}"], horizontal=True)
    col = "inc_med_end" if basis.startswith("Median") else "cpi_growth"
    ids, labels, parents, values, colors, texts, cd = [], [], [], [], [], [], []
    M2 = M.assign(region=[A.REGION[i] for i in M.index])
    for reg, g in M2.groupby("region"):
        w = g.pop_end
        ids.append(reg); labels.append(reg); parents.append(""); values.append(float(w.sum()))
        colors.append(float(np.average(g[col], weights=w))); texts.append(f"{w.sum() / 1000:.1f} M people")
        cd.append([float(w.sum() / 1000), float(np.average(g.inc_med_end, weights=w)), float(np.average(g.cpi_growth, weights=w))])
        for s_, r in g.sort_values("pop_end", ascending=False).iterrows():
            ids.append(f"{reg}/{s_}"); labels.append(r.label); parents.append(reg); values.append(float(r.pop_end))
            colors.append(float(r[col]))
            texts.append(f"{r.pop_end / 1000:.1f} M · RM{r.inc_med_end:,.0f} · +{r.cpi_growth:.0f}%")
            cd.append([float(r.pop_end / 1000), float(r.inc_med_end), float(r.cpi_growth)])
    is_inc = col == "inc_med_end"
    f = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, text=texts, customdata=cd, branchvalues="total",
        textinfo="label+text", textfont=dict(size=13),
        marker=dict(colors=colors, colorscale=SEQ if is_inc else ORSEQ, cmin=float(M[col].min()), cmax=float(M[col].max()),
                    showscale=True, line=dict(width=2, color="white"),
                    colorbar=dict(title="Median<br>income (RM)" if is_inc else "Price<br>growth (%)", thickness=14, len=0.8)),
        tiling=dict(pad=4), sort=False, root_color="white",
        hovertemplate="<b>%{label}</b><br>Population %{customdata[0]:.2f} M<br>Median income RM%{customdata[1]:,.0f}"
                      "<br>Price growth +%{customdata[2]:.1f}%<extra></extra>"))
    style(f, 620, showlegend=False)
    f.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    show(f)


# ================================================================== OBJECTIVE 3
else:
    header("Objective 3", "Which spending categories push prices up",
           "To identify which spending categories, such as food, housing and transport, push prices up "
           "the most, and rank states by overall cost-of-living pressure.", scope)

    DG = A.division_growth(cpi, y0, y1).loc[sel][cats]          # state x selected categories (% rise)
    nat = DG.mean().sort_values(ascending=False)                 # category average across states
    pressure = DG.mean(axis=1)                                   # state overall pressure = average rise across categories

    c = st.columns(4)
    kpi(c[0], "Fastest-rising category", cat_short(nat.index[0]), f"{nat.iloc[0]:+.0f}% on average")
    kpi(c[1], "Slowest category", cat_short(nat.index[-1]), f"{nat.iloc[-1]:+.0f}% on average")
    kpi(c[2], "Highest pressure", A.short(pressure.idxmax()), f"{pressure.max():+.0f}% avg over {len(cats)} categories")
    kpi(c[3], "Lowest pressure", A.short(pressure.idxmin()), f"{pressure.min():+.0f}% avg over {len(cats)} categories")

    st.markdown(f'<div class="sec">Price rise by spending category, {period}</div>'
                '<div class="note">Each row is a category, ranked by its average rise (top = fastest). Each dot is a state; '
                'darker dot = that state has higher overall pressure (average rise across the selected categories). '
                'Diamond = category average. Use the sidebar to pick categories or highlight a state.</div>',
                unsafe_allow_html=True)
    order = list(nat.index[::-1])                                # bottom -> top
    ypos = {c_: i for i, c_ in enumerate(order)}
    xs, ys, cols, cd = [], [], [], []
    for i, s_ in enumerate(DG.index):
        jit = ((i % 5) - 2) * 0.08                               # small vertical spread so dots do not hide each other
        for c_ in order:
            xs.append(float(DG.loc[s_, c_])); ys.append(ypos[c_] + jit)
            cols.append(float(pressure[s_])); cd.append([A.short(s_), c_, float(pressure[s_])])
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", showlegend=False, customdata=cd,
        marker=dict(size=10, color=cols, colorscale=ORSEQ, cmin=float(pressure.min()), cmax=float(pressure.max()),
                    showscale=True, opacity=0.9, line=dict(width=0.5, color="white"),
                    colorbar=dict(title="Overall<br>pressure %", thickness=14, len=0.8)),
        hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>Price rise %{x:+.1f}%"
                      "<br>State overall %{customdata[2]:+.1f}%<extra></extra>"))
    f.add_trace(go.Scatter(
        x=[float(nat[c_]) for c_ in order], y=list(range(len(order))), mode="markers", name="Category average",
        marker=dict(symbol="diamond", size=14, color=INK, line=dict(width=1.5, color="white")),
        hovertemplate="Average %{x:+.1f}%<extra></extra>"))
    if focus != "None" and focus in DG.index:
        f.add_trace(go.Scatter(
            x=[float(DG.loc[focus, c_]) for c_ in order], y=list(range(len(order))), mode="markers+text",
            name=A.short(focus), text=[f"{DG.loc[focus, c_]:+.0f}%" for c_ in order], textposition="middle right",
            textfont=dict(size=12, color=INK),
            marker=dict(size=16, color="rgba(0,0,0,0)", line=dict(width=2.5, color=INK)),
            hovertemplate=A.short(focus) + ": %{x:+.1f}%<extra></extra>"))
    style(f, int(max(440, 42 * len(order) + 170)), legend=dict(orientation="h", y=1.06, x=0))
    f.add_vline(x=0, line_dash="dot", line_color=MUTED, line_width=1)
    f.update_xaxes(title=f"Price rise {period} (%)", ticksuffix="%")
    f.update_yaxes(tickvals=list(range(len(order))), ticktext=order, range=[-0.7, len(order) - 0.3], automargin=True)
    show(f)


st.caption("Source: Department of Statistics Malaysia (DOSM) · JIE42403 Scientific Visualisation")
