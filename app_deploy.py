import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
from urllib.parse import urlparse

st.set_page_config(page_title="BIASSENTINEL | V2.0", layout="wide", initial_sidebar_state="expanded")

# ── THEME (Command Center Design) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@300;400;700&display=swap');
:root { --bg: #080808; --panel: #0d0d0d; --red: #a01a1a; --cream: #e0e0d1; --muted: #444444; --border: #1e1e1e; }
.main, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid var(--border); }
html, body, p, div, span, li { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }
.section-header { display: flex; align-items: center; gap: 15px; margin: 2rem 0 1rem; }
.section-header span { font-size: 0.65rem; color: var(--red); letter-spacing: 4px; text-transform: uppercase; }
.section-header div { flex: 1; height: 1px; background: var(--border); }
.stat-card { background: #0f0f0f; border-top: 2px solid var(--red); padding: 20px; }
.stat-label { font-size: 0.55rem; color: var(--muted); letter-spacing: 3px; text-transform: uppercase; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 2.2rem; color: white; margin-top: 5px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 0.6rem; color: var(--red); letter-spacing: 3px; padding: 15px 10px; border-bottom: 1px solid var(--border); }
td { padding: 15px 10px; border-bottom: 1px solid #121212; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ── DATABASE HELPERS ────────────────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

# ── NAVIGATION & DATA ──────────────────────────────────────────────────────
if "tab" not in st.session_state: st.session_state.tab = "dashboard"

# Fetch Global Countries List with SAFE FALLBACK
try:
    conn = get_db_connection()
    all_countries = sorted(pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist())
    conn.close()
except:
    all_countries = []

# If DB is empty, provide a list so the app doesn't crash (image_69a7ac_comparison.png fix)
if not all_countries:
    all_countries = ["India", "USA", "UK", "Russia", "China"]

with st.sidebar:
    st.markdown("<h2 style='color:var(--red); text-align:center;'>BIASSENTINEL</h2>", unsafe_allow_html=True)
    if st.button("📊 DASHBOARD"): st.session_state.tab = "dashboard"; st.rerun()
    if st.button("⚔️ COMPARE"): st.session_state.tab = "compare"; st.rerun()
    st.markdown("---")
    target = st.selectbox("ACTIVE TARGET", all_countries)

# ── MASTHEAD ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 30px;'>
    <div>
        <h1 style='margin:0; font-size:2.8rem;'>BIAS<span style='color:var(--red);'>SENTINEL</span></h1>
        <p style='font-size:0.6rem; color:var(--muted); letter-spacing:5px; margin-top:5px;'>GLOBAL MEDIA INTELLIGENCE ENGINE &nbsp; | &nbsp; V2.0</p>
    </div>
    <div style='border: 1px solid var(--red); padding: 8px 25px;'>
        <div style='font-size: 0.5rem; color: var(--red); letter-spacing: 3px;'>TARGET:</div>
        <div style='font-size: 1.1rem; color: white; letter-spacing: 4px;'>{(target or "INDIA").upper()}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "dashboard":
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{target}%",))
        reports = pd.read_sql("SELECT report_reason FROM bias_reports", conn)
        conn.close()

        if df.empty:
            st.error(f"NO DATA IN DATABASE FOR {target.upper()}. PLEASE RUN FIX_DB.PY.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='stat-card'><div class='stat-label'>TOTAL ARTICLES</div><div class='stat-value'>{len(df):,}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='stat-card'><div class='stat-label'>AVG SENTIMENT</div><div class='stat-value'>{df['sentiment_score'].mean():.2f}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='stat-card'><div class='stat-label'>SOURCES</div><div class='stat-value'>{df['source_url'].nunique()}</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='stat-card'><div class='stat-label'>FLAGGED BIAS</div><div class='stat-value'>{len(reports)}</div></div>", unsafe_allow_html=True)
            
            # (Rest of your Table and Graph code goes here...)
            st.info("Data loaded. Displaying Media Landscape...")
    except Exception as e:
        st.error(f"DATABASE CONNECTION ERROR: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2: COMPARE (Fixes image_69a7ac_comparison.png)
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "compare":
    st.markdown("<div class='section-header'><span>CROSS-REGIONAL DISPARITY</span><div></div></div>", unsafe_allow_html=True)
    comp_a, comp_b = st.columns(2)
    
    # Ensuring these never return None
    target_a = comp_a.selectbox("Region Alpha", all_countries, index=0)
    target_b = comp_b.selectbox("Region Beta", all_countries, index=min(1, len(all_countries)-1))

    try:
        conn = get_db_connection()
        res_a = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{target_a}%",))['avg'].iloc[0]
        res_b = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{target_b}%",))['avg'].iloc[0]
        conn.close()

        m1, m2 = st.columns(2)
        # Line 144 Fix: target_a and target_b are now guaranteed to have strings
        with m1: st.markdown(f"<div class='stat-card'><div class='stat-label'>{target_a.upper()} AVG</div><div class='stat-value'>{res_a if res_a else 0:+.3f}</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='stat-card'><div class='stat-label'>{target_b.upper()} AVG</div><div class='stat-value'>{res_b if res_b else 0:+.3f}</div></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"COMPARISON ERROR: {e}")
