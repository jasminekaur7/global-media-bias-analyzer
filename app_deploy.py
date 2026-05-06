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
.badge-negative { border: 1px solid var(--red); color: var(--red); font-size: 0.55rem; padding: 2px 8px; background: #a01a1a10; }
.badge-neutral { border: 1px solid var(--muted); color: var(--muted); font-size: 0.55rem; padding: 2px 8px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 0.6rem; color: var(--red); letter-spacing: 3px; padding: 15px 10px; border-bottom: 1px solid var(--border); }
td { padding: 15px 10px; border-bottom: 1px solid #121212; font-size: 0.7rem; }
.intercept-card { background: #0f0f0f; border-top: 1px solid var(--red); padding: 15px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace("www.", "").upper()
    except: return "UNKNOWN"

# ── NAVIGATION & STATE ──────────────────────────────────────────────────────
if "target" not in st.session_state: st.session_state.target = "India"
if "tab" not in st.session_state: st.session_state.tab = "dashboard"

with st.sidebar:
    st.markdown("<h2 style='color:var(--red); text-align:center;'>BIASSENTINEL</h2>", unsafe_allow_html=True)
    if st.button("📊 DASHBOARD"): st.session_state.tab = "dashboard"; st.rerun()
    if st.button("⚔️ COMPARE"): st.session_state.tab = "compare"; st.rerun()
    st.markdown("---")
    
    # 190+ Countries Logic: Pull directly from your news_signals table
    try:
        conn = get_db_connection()
        countries = sorted(pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist())
        conn.close()
    except: countries = ["India", "USA", "Russia"]
    
    st.session_state.target = st.selectbox("ACTIVE TARGET", countries if countries else ["India"])

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

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "dashboard":
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{st.session_state.target}%",))
    reports = pd.read_sql("SELECT report_reason FROM bias_reports", conn)
    conn.close()

    if df.empty:
        st.error("No signals for this region. Please run fix_db.py to restore global data.")
    else:
        # Stat Grid
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='stat-card'><div class='stat-label'>TOTAL ARTICLES</div><div class='stat-value'>{len(df):,}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='stat-card'><div class='stat-label'>AVG SENTIMENT</div><div class='stat-value'>{df['sentiment_score'].mean():.2f}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='stat-card'><div class='stat-label'>SOURCES</div><div class='stat-value'>{df['source_url'].nunique()}</div></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='stat-card'><div class='stat-label'>FLAGGED BIAS</div><div class='stat-value'>{len(reports)}</div></div>", unsafe_allow_html=True)

        # Media Landscape
        st.markdown("<div class='section-header'><span>MEDIA LANDSCAPE</span><div></div></div>", unsafe_allow_html=True)
        df_grouped = df.groupby("actor_name")["sentiment_score"].agg(["mean", "count"]).reset_index()
        df_grouped["REPORTS"] = df_grouped["actor_name"].apply(lambda x: reports['report_reason'].str.contains(x, case=False).sum() if not reports.empty else 0)
        df_grouped = df_grouped.sort_values("mean", ascending=True).head(10)

        rows = ""
        for _, row in df_grouped.iterrows():
            badge = "badge-negative" if row['mean'] < -2 else "badge-neutral"
            rows += f"<tr><td>{row['actor_name']}</td><td><span class='{badge}'>Analysis</span></td><td style='color:var(--red)'>{row['mean']:+.2f}</td><td>{row['REPORTS']}</td></tr>"
        st.markdown(f"<table><tr><th>CHANNEL</th><th>ANALYSIS</th><th>SCORE</th><th>REPORTS</th></tr>{rows}</table>", unsafe_allow_html=True)

        # THE GRAPHS
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("<div class='section-header'><span>SENTIMENT DISTRIBUTION</span><div></div></div>", unsafe_allow_html=True)
            fig1 = px.histogram(df, x="sentiment_score", color_discrete_sequence=['#a01a1a'])
            fig1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            st.markdown("<div class='section-header'><span>SOURCE BIAS RANKING</span><div></div></div>", unsafe_allow_html=True)
            fig2 = px.bar(df_grouped, x='mean', y='actor_name', orientation='h', color_discrete_sequence=['#444'])
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig2, use_container_width=True)

        # Signal Intercepts
        st.markdown("<div class='section-header'><span>SIGNAL INTERCEPTS</span><div></div></div>", unsafe_allow_html=True)
        grid = st.columns(3)
        sample = df.sample(min(len(df), 6))
        for i, (_, row) in enumerate(sample.iterrows()):
            with grid[i % 3]:
                st.markdown(f"<div class='intercept-card'><div class='intercept-source'>{extract_source(row['source_url'])}</div><div class='intercept-score' style='color:var(--red)'>{row['sentiment_score']:+.2f}</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2: COMPARE
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "compare":
    st.markdown("<div class='section-header'><span>CROSS-REGIONAL DISPARITY</span><div></div></div>", unsafe_allow_html=True)
    comp_a, comp_b = st.columns(2)
    with comp_a: c_a = st.selectbox("Region Alpha", countries, index=0)
    with comp_b: c_b = st.selectbox("Region Beta", countries, index=1)

    conn = get_db_connection()
    res_a = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_a}%",))['avg'].iloc[0]
    res_b = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_b}%",))['avg'].iloc[0]
    conn.close()

    m1, m2 = st.columns(2)
    with m1: st.markdown(f"<div class='stat-card'><div class='stat-label'>{c_a.upper()} AVG</div><div class='stat-value'>{res_a if res_a else 0:+.3f}</div></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='stat-card'><div class='stat-label'>{c_b.upper()} AVG</div><div class='stat-value'>{res_b if res_b else 0:+.3f}</div></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center; margin-top:20px; font-size:0.8rem; color:var(--red);'>DELTA DISPARITY: {abs((res_a or 0) - (res_b or 0)):.4f}</div>", unsafe_allow_html=True)
