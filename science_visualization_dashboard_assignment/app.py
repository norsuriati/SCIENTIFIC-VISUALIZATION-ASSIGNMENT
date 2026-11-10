"""Malaysia Cost-of-Living Dashboard (JIE42403 Scientific Visualisation)
Data: OpenDOSM (Population, Household Income, Consumer Price Index) merged by state and year.
Run:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import analysis as calc
except ImportError:  # the file may be called analysis.py
    import analysis as calc

# ---------------------------------------------------------------- setup
st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

TEAL, AMBER, INK, MUTED = "#0F766E", "#F59E0B", "#0F172A", "#64748B"
FONT = "Inter, Segoe UI, Arial, sans-serif"
PLOT_CFG = {"displayModeBar": False}

STATE_SHORT = {
    "W.P. Kuala Lumpur": "KL",
    "W.P. Putrajaya": "Putrajaya",
    "W.P. Labuan": "Labuan",
    "Pulau Pinang": "Penang",
    "Negeri Sembilan": "N. Sembilan",
}


def short_state(s: str) -> str:
    return STATE_SHORT.get(s, s)


st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1440px;}
      h1 {font-size: 2rem !important; letter-spacing: -0.035em; margin-bottom: .2rem;}
      h2, h3 {letter-spacing: -0.02em;}
      .objective {background: linear-gradient(110deg,#ECFDF5,#F8FAFC); border: 1px solid #D1FAE5;
                  border-left: 4px solid #0F766E; padding: .9rem 1.1rem;
                  border-radius: 12px; font-size: 1rem; color: #0F172A; margin: .6rem 0 1.2rem 0;}
      .objective b {color: #0F766E;}
      [data-testid="stMetric"] {background:#FFFFFF; border:1px solid #E2E8F0; padding:14px 16px;
                  border-radius:14px; box-shadow:0 2px 8px rgba(15,23,42,.035);}
      [data-testid="stMetricLabel"] p {font-size: .82rem; color: #64748B;}
      [data-testid="stMetricValue"] {font-size: 1.55rem; font-weight:650;}
      [data-testid="stSidebar"] {border-right:1px solid #E2E8F0;}
      .small {color: #64748B; font-size: .85rem;}
      div[data-testid="stPlotlyChart"] {border-radius: 14px; overflow:hidden;}
      div[data-testid="stExpander"] {border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data() -> pd.DataFrame:
    here = Path(__file__).parent
    path = next((p for p in (here / "data" / "merged_dataset.csv", here / "merged_dataset.csv") if p.exists()), None)
    if path is None:
        st.error("merged_dataset.csv not found. Put it in the data folder next to app.py.")
        st.stop()
    return calc.load_data(str(path))


df = get_data()
YEARS = sorted(df["year"].unique().tolist())


@st.cache_data(show_spinner=False)
def get_geojson(path: str, state_names: tuple):
    return calc.load_geojson(path, list(state_names))


def find_geojson():
    """Find boundary files regardless of capitalization or a slightly different filename."""
    here = Path(__file__).parent
    candidates = []
    for folder in (here / "data", here):
        if folder.exists():
            candidates.extend(folder.glob("*.geojson"))
            candidates.extend(folder.glob("*.json"))
    # Prefer an explicitly named Malaysia states file, then geoBoundaries ADM1.
    candidates = list(dict.fromkeys(candidates))
    candidates.sort(key=lambda p: (
        0 if "malaysia" in p.name.lower() and "state" in p.name.lower() else
        1 if "mys" in p.name.lower() and "adm1" in p.name.lower() else 2,
        p.name.lower()
    ))
    return next((p for p in candidates if p.is_file() and p.stat().st_size > 1000), None)

