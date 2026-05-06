import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from urllib.parse import urlparse

st.set_page_config(page_title="BIASSENTINEL | V2.0", layout="wide", initial_sidebar_state="expanded")

# ── THEME: IMAGE_69A7AC.PNG MATCH ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@300;400;700&display=swap');
:root { --bg: #080808; --panel: #0d0d0d; --red: #a01a1a; --cream: #e0e0d1; --muted: #444444; }
.main, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid #1e1e1e; }
html, body, p, div, span, li { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }
.section-header { display: flex; align-items: center; gap: 15px; margin: 2rem 0 1rem; }
.section-header span { font-size: 0.65rem; color: var(--red); letter-spacing: 4px; text-transform: uppercase; }
.section-header div { flex: 1; height: 1px; background: #1e1e1e; }
.stat-card { background: #0f0f0f; border-top: 2px solid var(--red); padding: 20px; }
.stat-label { font-size: 0.55rem; color: var(--muted); letter-spacing: 3px; text-transform: uppercase; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 2.2rem; color: white; margin-top: 5px; }
.badge-negative { border: 1px solid var(--red); color: var(--red); font-size: 0.55rem; padding: 2px 8px; background: #a01a1a10; }
.badge-neutral { border: 1px solid var(--muted); color: var(--muted); font-size: 0.55rem; padding: 2px 8px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 0.6rem; color: var(--red); letter-spacing: 3px; padding: 15px 10px; border-bottom: 1px solid #1e1e1e; }
td { padding: 15px 10px; border-bottom: 1px solid #121212; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace("www.", "").upper()
    except: return "UNKNOWN"

# ── NAVIGATION ───────────────────────────────────────────────────────────────
if "target" not in st.session_state: st.session_state.target = "India"
if "tab" not in st.session_state: st.session_state.tab = "dashboard"

with st.sidebar:
    st.markdown("<h2 style='color:var(--red); text-align:center;'>BIASSENTINEL</h2>", unsafe_allow_html=True)
    if st.button("📊 DASHBOARD"): st.session_state.tab = "dashboard"; st.rerun()
    if st.button("⚔️ COMPARE"): st.session_state.tab = "compare"; st.rerun()
    st.markdown("---")
    # Dynamic Country List from DB
    try:
        conn = get_db_connection()
        countries = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist()
        conn.close()
    except: countries = ["India", "USA", "Russia"]
    
    st.session_state.target = st.selectbox("SELECT TARGET", sorted(countries) if countries else ["India"])

# ── MASTHEAD ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 30px;'>
    <div>
        <h1 style='margin:0; font-size:2.8rem;'>BIAS<span style='color:var(--red);'>SENTINEL</span></h1>
        <p style='font-size:0.6rem; color:var(--muted); letter-spacing:5px; margin-top:5px;'>GLOBAL MEDIA INTELLIGENCE ENGINE &nbsp; | &nbsp; V2.0</p>
    </div>
    <div style='border: 1px solid var(--red); padding: 8px 25px;'>
        <div style='font-size: 0.5rem; color: var(--red); letter-spacing: 3px;'>TARGET:</div>
        <div style='font-size: 1.1rem; color: white; letter-spacing: 4px;'>{st.session_state.target.upper()}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── DASHBOARD VIEW ──────────────────────────────────────────────────────────
if st.session_state.tab == "dashboard":
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{st.session_state.target}%",))
    reports = pd.read_sql("SELECT report_reason FROM bias_reports", conn)
    conn.close()

    if df.empty:
        st.error("No signals for this region. Run fix_db.py to upload global data.")
    else:
        # Stat Grid
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='stat-card'><div class='stat-label'>TOTAL ARTICLES</div><div class='stat-value'>{len(df):,}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='stat-card'><div class='stat-label'>AVG SENTIMENT</div><div class='stat-value'>{df['sentiment_score'].mean():.2f}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='stat-card'><div class='stat-label'>SOURCES</div><div class='stat-value'>{df['source_url'].nunique()}</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='stat-card'><div class='stat-label'>FLAGGED BIAS</div><div class='stat-value'>{len(reports)}</div></div>", unsafe_allow_html=True)

        # Media Landscape Table
        st.markdown("<div class='section-header'><span>MEDIA LANDSCAPE</span><div></div></div>", unsafe_allow_html=True)
        sort_order = st.selectbox("EDITORIAL PRIORITY", ["Negative Bias First", "Positive Bias First"])
        
        df_grouped = df.groupby("actor_name")["sentiment_score"].agg(["mean", "count"]).reset_index()
        df_grouped["REPORTS"] = df_grouped["actor_name"].apply(lambda x: reports['report_reason'].str.contains(x, case=False).sum() if not reports.empty else 0)
        df_grouped = df_grouped.sort_values("mean", ascending=("Negative" in sort_order)).head(10)

        rows = ""
        for _, row in df_grouped.iterrows():
            analysis = "Systemic Negative" if row['mean'] < -2 else "Neutral"
            badge = "badge-negative" if row['mean'] < -2 else "badge-neutral"
            rows += f"<tr><td>{row['actor_name']}</td><td><span class='{badge}'>{analysis}</span></td><td style='color:var(--red)'>{row['mean']:+.2f}</td><td>{row['REPORTS']}</td></tr>"

        st.markdown(f"<table><tr><th>CHANNEL</th><th>ANALYSIS</th><th>SCORE</th><th>REPORTS</th></tr>{rows}</table>", unsafe_allow_html=True)

# ── REFRESH DATABASE CHECK ──────────────────────────────────────────────────
# (The SQL check logic mentioned in your prompt is now handled by the scripts)
