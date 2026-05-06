import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from urllib.parse import urlparse

# ============================================================
# 1. SETUP & THEME
# ============================================================
st.set_page_config(page_title="BIASSENTINEL", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@300;400;700&display=swap');
:root { --bg: #0d0d0d; --panel: #111111; --red: #a01a1a; --cream: #e0e0d1; --dim: #2a2a2a; }
.main, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid var(--dim); }
html, body, p, div, span, li { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }
.stButton > button { background: transparent; color: var(--cream); border: 1px solid var(--dim); border-radius: 0; text-transform: uppercase; width: 100%; transition: 0.2s; }
.stButton > button:hover { border-color: var(--red); background: #1a0808; }
.legend-box { border-left: 8px solid var(--red); padding: 15px; background: #1a1a1a; margin-bottom: 20px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. CORE UTILITIES
# ============================================================
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace("www.", "").upper()
    except: return "UNKNOWN"

@st.cache_data(ttl=300)
def load_countries():
    try:
        conn = get_db_connection()
        raw = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist()
        conn.close()
        return sorted(set([str(l).split(",")[-1].strip() for l in raw if l and len(str(l)) > 2]))
    except: return ["India", "USA", "Russia", "UK", "China"]

# ============================================================
# 3. NAVIGATION & TARGET SELECTION
# ============================================================
if "target" not in st.session_state: st.session_state.target = "India"
if "view" not in st.session_state: st.session_state.view = "Dashboard"

country_list = load_countries()

with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#a01a1a;'>BIASSENTINEL</h2>", unsafe_allow_html=True)
    
    # Navigation Buttons (The 2 Main Columns)
    if st.button("📊 DASHBOARD"): st.session_state.view = "Dashboard"; st.rerun()
    if st.button("⚔️ COMPARE"): st.session_state.view = "Compare"; st.rerun()
    
    st.markdown("---")
    # Roulette
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:2px; text-transform:uppercase;'>Roulette</div>", unsafe_allow_html=True)
    if st.button("SPIN TARGET"):
        st.session_state.target = random.choice(country_list)
        st.rerun()
    st.write(f"Current: **{st.session_state.target.upper()}**")

# ============================================================
# 4. VIEW LOGIC
# ============================================================
target = st.session_state.target

if st.session_state.view == "Dashboard":
    # Fetch Data
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{target}%",))
    conn.close()

    st.title(f"DASHBOARD: {target.upper()}")
    
    if df.empty:
        st.warning("No signals found. Please re-run your ingestion script.")
    else:
        # Stats
        c1, c2, c3 = st.columns(3)
        c1.metric("Articles", len(df))
        c2.metric("Avg Bias", f"{df['sentiment_score'].mean():.2f}")
        c3.metric("Sources", df['source_url'].nunique())

        # Charts
        col_a, col_b = st.columns(2)
        with col_a:
            fig1 = px.histogram(df, x="sentiment_score", title="Sentiment Distribution", color_discrete_sequence=['#a01a1a'])
            fig1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig1, use_container_width=True)
        with col_b:
            df_g = df.groupby('actor_name')['sentiment_score'].mean().reset_index().head(10)
            fig2 = px.bar(df_g, x='sentiment_score', y='actor_name', orientation='h', title="Top Channel Bias")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        # 🚩 THE CORRECT REPORTING PORTAL (As per Synopsis)
        st.markdown("---")
        st.subheader("🚩 REPORT BIAS")
        st.markdown('<div class="legend-box">AUDIT INTERFACE: Convert anecdotal complaints into structured data.</div>', unsafe_allow_html=True)
        
        r_col1, r_col2, r_col3 = st.columns([2,2,1])
        with r_col1:
            report_channel = st.selectbox("CHANNEL TO FLAG:", df['actor_name'].unique())
        with r_col2:
            # Fixing the options based on your synopsis pillars
            basis = st.selectbox("BASIS OF REPORTING:", [
                "Inaccurate Reporting (Fake News)",
                "Political Favoritism",
                "Sensationalism",
                "Cultural / Regional Insensitivity"
            ])
        with r_col3:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("SUBMIT FLAG"):
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"{basis} for {report_channel}",))
                conn.commit(); conn.close()
                st.toast("Flag successfully stored in database.")

elif st.session_state.view == "Compare":
    st.title("⚔️ REGIONAL COMPARISON")
    comp_a, comp_b = st.columns(2)
    with comp_a: c_a = st.selectbox("Region Alpha", country_list, index=0)
    with comp_b: c_b = st.selectbox("Region Beta", country_list, index=min(1, len(country_list)-1))

    conn = get_db_connection()
    avg_a = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_a}%",))['avg'].iloc[0]
    avg_b = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_b}%",))['avg'].iloc[0]
    conn.close()

    m1, m2 = st.columns(2)
    m1.metric(c_a, f"{avg_a if avg_a else 0:.3f}")
    m2.metric(c_b, f"{avg_b if avg_b else 0:.3f}")
    
    st.info(f"Disparity Delta: {abs((avg_a or 0) - (avg_b or 0)):.3f}")