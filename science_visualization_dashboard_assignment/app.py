from pathlib import Path
import html
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analysis as calc

st.set_page_config(page_title="Malaysia Cost of Living", page_icon="📊", layout="wide")

# Consistent design system: income = blue, prices = orange, falling prices = teal.
BG, INK, MUTED = "#F5F7FA", "#182230", "#667085"
TEAL, GRID, WHITE = "#147D73", "#E5EAF0", "#FFFFFF"
INCOME_BLUE, PRICE_ORANGE = "#2864E8", "#F05A0A"
MUTED_BLUE, MUTED_ORANGE = "#D9DEE5", "#E5E7EB"
FONT = "Inter, Aptos, Segoe UI, sans-serif"
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}
MAP_VERSION = "4"  # change this number to force the map file to be read again

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
.objective-card {{ background:#FFFFFF; border:1px solid {GRID}; border-left:5px solid {TEAL}; border-radius:12px;
                   padding:.8rem 1.1rem; margin:.5rem 0 1.1rem; }}
.objective-label {{ color:{TEAL}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; }}
.objective-text {{ color:{INK}; font-size:1.02rem; margin-top:.15rem; }}
.filter-heading {{ color:{MUTED}; font-size:.7rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin:0 0 .2rem; }}
.kpi {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:13px 16px; box-sizing:border-box; }}
.kpi-header {{ display:flex; align-items:center; justify-content:space-between; gap:.5rem; margin-bottom:.35rem; }}
.kpi-label {{ color:{MUTED}; font-size:.8rem; font-weight:650; line-height:1.25; }}
.kpi-period {{ display:inline-flex; align-items:center; gap:.25rem; flex:0 0 auto; padding:.2rem .5rem; border-radius:999px; background:#F2F4F7; color:{MUTED}; font-size:.66rem; font-weight:750; letter-spacing:.035em; white-space:nowrap; }}
.kpi-value {{ color:{INK}; font-size:1.4rem; font-weight:740; line-height:1.2; margin:.2rem 0 .15rem; overflow-wrap:anywhere; }}
.kpi-sub {{ color:{MUTED}; font-size:.82rem; line-height:1.3; }}
.kpi-row {{ display:flex; align-items:baseline; gap:.6rem; padding:.28rem 0; border-top:1px solid {GRID}; }}
.kpi-tag {{ flex:0 0 3.9rem; color:{MUTED}; font-size:.72rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
.kpi-name {{ flex:1; color:{INK}; font-size:1.02rem; font-weight:720; line-height:1.25; }}
.kpi-name small {{ display:block; color:{MUTED}; font-size:.78rem; font-weight:500; }}
.kpi-chg {{ flex:0 0 auto; font-size:.9rem; font-weight:700; white-space:nowrap; }}
.kpi-foot {{ color:{MUTED}; font-size:.72rem; margin-top:.3rem; }}
.kpi-delta {{ font-size:.86rem; font-weight:680; line-height:1.3; margin-top:.2rem; }}
.legend-row {{ display:flex; gap:1.3rem; align-items:center; flex-wrap:wrap; font-size:.8rem; color:{MUTED}; margin:.1rem 0 .55rem; }}
.lg-item {{ display:inline-flex; align-items:center; gap:.4rem; }}
.lg-sw {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
.lg-grad {{ width:96px; height:10px; border-radius:5px; background:linear-gradient(90deg,#FDE6D6,#F8A670,{PRICE_ORANGE},#B23A00); display:inline-block; }}
.scale {{ width:340px; max-width:100%; margin:.1rem auto .7rem; }}
.scale-bar {{ height:12px; border-radius:6px; background:linear-gradient(90deg,#FDE6D6,#F8A670,{PRICE_ORANGE},#B23A00); }}
.scale-labels {{ display:flex; justify-content:space-between; font-size:.78rem; color:{MUTED}; margin-top:.3rem; }}
.lg-dash {{ width:20px; border-top:2px dashed {INK}; display:inline-block; }}
[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:12px; padding:12px 15px; min-height:96px; }}
[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-size:.78rem; line-height:1.25; }}
[data-testid="stMetricValue"] {{ color:{INK}; font-size:1.42rem; font-weight:720; }}
div[data-testid="stPlotlyChart"] {{ background:#FFFFFF; border:1px solid {GRID}; border-radius:13px; padding:0; overflow:hidden; }}
[data-testid="stRadio"] > div {{ gap:.55rem; }}
[data-testid="stRadio"] label {{ font-size:.88rem; }}
div[data-testid="stCaptionContainer"] p {{ color:{MUTED}; }}
hr {{ border-color:{GRID}; }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    return calc.load_data()


@st.cache_data
def get_geojson(path, state_names, version):
    return calc.load_geojson(path, list(state_names))


def find_geojson():
    here = Path(__file__).parent
    options = [here / "data" / "malaysia_states.geojson", here / "malaysia_states.geojson"]
    options += sorted(here.glob("*.geojson")) + sorted((here / "data").glob("*.geojson"))
    return next((p for p in options if p.exists()), None)


df = load()
YEARS = sorted(df.year.unique().tolist())
