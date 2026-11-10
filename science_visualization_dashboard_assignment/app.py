"""Malaysia Cost-of-Living Dashboard | JIE42403 Scientific Visualisation."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import analysis as calc

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")
ROOT = Path(__file__).parent
DATA_CANDIDATES = [ROOT / "data" / "merged_dataset.csv", ROOT / "merged_dataset.csv"]
GEO_CANDIDATES = [ROOT / "data" / "geoBoundaries-MYS-ADM1.geojson",
                  ROOT / "geoBoundaries-MYS-ADM1.geojson"]
TEAL, AMBER, INK, MUTED = "#0F766E", "#F59E0B", "#0F172A", "#64748B"
FONT = "Inter, Segoe UI, Arial, sans-serif"
PLOT_CFG = {"displayModeBar": False, "responsive": True}

st.markdown("""<style>
.block-container{padding-top:1.4rem;padding-bottom:2rem;max-width:1500px}
h1{font-size:2rem!important;letter-spacing:-.035em}
[data-testid="stMetric"]{background:#fff;border:1px solid #e2e8f0;padding:13px 15px;border-radius:13px}
[data-testid="stSidebar"]{border-right:1px solid #e2e8f0}
div[data-testid="stPlotlyChart"]{border-radius:12px;overflow:hidden}
.small-note{color:#64748b;font-size:.84rem}
</style>""", unsafe_allow_html=True)

@st.cache_data
def get_data(path):
    return calc.load_data(path)

@st.cache_data
def get_geo(path, states):
    return calc.load_geojson(path, states)

data_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
if data_path is None:
    st.error("Dataset not found. Put merged_dataset.csv in the data/ folder beside app.py.")
    st.stop()
try:
    df = get_data(str(data_path))
except Exception as exc:
    st.error(f"Unable to load dataset: {exc}")
    st.stop()

years = sorted(df.year.unique().tolist())
states = sorted(df.state.dropna().unique().tolist())
if not years or not states:
    st.error("Dataset has no usable year or state records.")
    st.stop()

with st.sidebar:
    st.title("📊 Cost of Living")
    st.caption("Malaysia · State-level analysis")
    page = st.radio("NAVIGATION", ["Overview", "State Comparison", "Price Drivers", "Data Explorer"])
    st.divider()
    default_y0 = years[0]
    default_y1 = years[-1]
    y0 = st.selectbox("Baseline year", years, index=years.index(default_y0))
    later_years = [y for y in years if y > y0]
    if not later_years:
        st.warning("Select an earlier baseline year to compare.")
        st.stop()
    y1 = st.selectbox("Comparison year", later_years, index=len(later_years)-1)
    selected_states = st.multiselect("States", states, default=states)

if not selected_states:
    st.info("Select at least one state from the sidebar.")
    st.stop()

metric = calc.metrics(df, int(y0), int(y1))
metric = metric[metric.state.isin(selected_states)]
pop = calc.population_table(df, int(y1))
pop = pop[pop.state.isin(selected_states)]
period = f"{y0} → {y1}"

def layout_fig(fig, height=430):
    fig.update_layout(height=height, template="plotly_white", font=dict(family=FONT,color=INK),
                      margin=dict(l=15,r=15,t=45,b=15), paper_bgcolor="white",
                      plot_bgcolor="white", legend_title_text="")
    return fig

def money(x):
    return f"RM {x:,.0f}" if pd.notna(x) else "—"

st.title("Malaysia Cost-of-Living Dashboard")
st.caption(f"OpenDOSM indicators · {period} · {len(selected_states)} selected states")
st.markdown(f"""<div style="padding:13px 16px;border-left:4px solid {TEAL};background:#f0fdfa;border-radius:9px;margin:10px 0 18px">
<b>Analytical objective:</b> Examine how changes in consumer prices relate to household income and population across Malaysian states.
</div>""", unsafe_allow_html=True)

if page == "Overview":
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("States analysed", f"{len(metric):,}")
    c2.metric("Average price growth", f"{metric.price_growth.mean():.1f}%" if len(metric) else "—")
    c3.metric("Average income growth", f"{metric.income_growth.mean():.1f}%" if len(metric) else "—")
    c4.metric("Average real income growth", f"{metric.real_growth.mean():.1f}%" if len(metric) else "—")
    left,right = st.columns([1.2,1])
    with left:
        st.subheader("Income growth vs price growth")
        if len(metric):
            fig=go.Figure()
            fig.add_trace(go.Bar(name="Household income",x=metric.state,y=metric.income_growth,marker_color=TEAL))
            fig.add_trace(go.Bar(name="Consumer prices",x=metric.state,y=metric.price_growth,marker_color=AMBER))
            fig.update_layout(barmode="group",yaxis_title="Growth (%)")
            st.plotly_chart(layout_fig(fig,460),use_container_width=True,config=PLOT_CFG)
        else: st.info("No comparable records for selected years and states.")
    with right:
        st.subheader("Population by state")
        if len(pop):
            p=pop.sort_values("population")
            fig=px.bar(p,x="population",y="state",orientation="h",color="population",
                       color_continuous_scale=["#ccfbf1",TEAL],labels={"population":"Population","state":"State"})
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(layout_fig(fig,460),use_container_width=True,config=PLOT_CFG)
        else: st.info("No population data for the selected year.")
    st.subheader("Malaysia state map · price growth")
    geo_path=next((p for p in GEO_CANDIDATES if p.exists()),None)
    if geo_path is None:
        st.warning("GeoJSON boundary file not found. Put geoBoundaries-MYS-ADM1.geojson in data/.")
    elif len(metric):
        try:
            geo=get_geo(str(geo_path),tuple(states))
            map_df=metric.copy()
            map_df["state_key"]=map_df.state.map(calc.norm)
            # Map GeoJSON labels use dashboard_state, matching the dataset's W.P. labels.
            fig=px.choropleth(map_df,geojson=geo,locations="state",featureidkey="properties.dashboard_state",
                color="price_growth",hover_name="state",
                hover_data={"income_growth":":.2f","price_growth":":.2f","real_growth":":.2f","state":False},
                color_continuous_scale=["#d1fae5","#fbbf24","#b91c1c"],
                labels={"price_growth":"Price growth (%)"})
            fig.update_geos(fitbounds="locations",visible=False)
            fig.update_layout(height=570,margin=dict(l=0,r=0,t=15,b=0),font=dict(family=FONT))
            st.plotly_chart(fig,use_container_width=True,config=PLOT_CFG)
        except Exception as exc:
            st.error(f"Map could not be rendered: {exc}")
    st.caption("Interpretation: positive income–price gap means mean household income growth exceeded consumer price growth.")

elif page == "State Comparison":
    st.subheader("State-level income and price performance")
    if len(metric):
        view=metric.sort_values("gap")
        fig=px.bar(view,x="gap",y="state",orientation="h",color="gap",
                   color_continuous_scale=["#b91c1c","#f8fafc",TEAL],
                   labels={"gap":"Income growth minus price growth (percentage points)","state":"State"})
        fig.add_vline(x=0,line_dash="dash",line_color=MUTED)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(layout_fig(fig, max(420,25*len(view))),use_container_width=True,config=PLOT_CFG)
        st.subheader("Detailed comparison")
        show=metric.rename(columns={"income_growth":"Income growth (%)","price_growth":"Price growth (%)",
                                    "real_growth":"Real income growth (%)","gap":"Income-price gap (pp)"})
        st.dataframe(show.round(2),use_container_width=True,hide_index=True)
    else: st.info("No comparable data.")

elif page == "Price Drivers":
    st.subheader("Consumer price growth by expenditure division")
    cat=calc.category_growth(df,int(y0),int(y1))
    cat=cat.loc[cat.index.intersection(selected_states)]
    if not cat.empty:
        cat=cat.rename(columns=calc.SHORT)
        fig=px.imshow(cat,aspect="auto",color_continuous_scale=["#d1fae5","#fbbf24","#b91c1c"],
                      labels=dict(x="Expenditure division",y="State",color="Growth (%)"),
                      text_auto=".1f")
        fig.update_layout(height=max(450,30*len(cat)),xaxis_tickangle=-35)
        st.plotly_chart(layout_fig(fig,max(450,30*len(cat))),use_container_width=True,config=PLOT_CFG)
        st.caption("Values represent percentage change in CPI index between the selected years; they are not price levels.")
    else: st.info("No category records available for this comparison.")

else:
    st.subheader("Dataset explorer")
    division_options=sorted(df.division.unique().tolist())
    chosen_div=st.selectbox("Expenditure division",division_options,
                            index=division_options.index("Overall") if "Overall" in division_options else 0)
    filtered=df[(df.state.isin(selected_states))&(df.year.isin([int(y0),int(y1)]))&(df.division==chosen_div)]
    st.metric("Records shown",f"{len(filtered):,}")
    st.dataframe(filtered.sort_values(["state","year"]),use_container_width=True,hide_index=True)
    st.download_button("Download filtered CSV",filtered.to_csv(index=False).encode("utf-8"),
                       file_name="cost_of_living_filtered.csv",mime="text/csv")
