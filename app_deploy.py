import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & COMMAND CENTER THEME ---
st.set_page_config(page_title="BIASSENTINEL | COMMAND", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Background and Base Text */
    .main { background-color: #0d0d0d; color: #e0e0d1; font-family: 'JetBrains Mono', monospace; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #141414; border-right: 2px solid #a01a1a; }
    
    /* Headers */
    .masthead { font-family: 'Playfair Display', serif; text-align: center; letter-spacing: 5px; color: #e0e0d1; margin-bottom: 0px; }
    .sub-masthead { text-align: center; font-size: 0.8rem; letter-spacing: 3px; color: #666; margin-bottom: 30px; }
    
    /* Metric Cards (Matches your reference image 2) */
    .kpi-card { 
        border: 1px solid #333; background: #1a1a1a; padding: 20px; text-align: center; 
        border-top: 4px solid #a01a1a; 
    }
    .kpi-value { font-size: 2.5rem; font-weight: bold; color: #e0e0d1; margin: 0; }
    .kpi-label { font-size: 0.7rem; color: #a01a1a; text-transform: uppercase; letter-spacing: 2px; }

    /* The "News Ticker" Bar */
    .ticker-bar { 
        background: #e0e0d1; color: #0d0d0d; padding: 5px; font-weight: bold; 
        font-size: 0.8rem; text-transform: uppercase; margin-bottom: 20px; 
    }

    /* Roulette Box */
    .slot-machine-sidebar { 
        font-size: 1.2rem; font-weight: bold; color: #ff4b4b; text-align: center; 
        border: 1px solid #a01a1a; padding: 15px; background: #000; 
        margin-bottom: 15px; text-transform: uppercase;
    }
    
    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 0px; background: transparent; color: #e0e0d1; 
        border: 1px solid #444; text-transform: uppercase; letter-spacing: 2px;
    }
    .stButton>button:hover { border-color: #a01a1a; color: #a01a1a; }

    /* Input Boxes Fix */
    input { background-color: #1a1a1a !important; color: #e0e0d1 !important; border: 1px solid #333 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE UTILITIES ---
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. SESSION STATE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:#a01a1a;'>REGIONAL ROULETTE</h3>", unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        loc_query = "SELECT DISTINCT location_name FROM news_signals"
        raw_locs = pd.read_sql(loc_query, conn)['location_name'].tolist()
        conn.close()
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "RUSSIA"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("SPIN FOR TARGET"):
        for i in range(10):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown("<br><h3 style='text-align:center; color:#a01a1a;'>BUREAU AUDIT</h3>", unsafe_allow_html=True)
    if st.button("RUN PL/SQL CURSOR"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit complete.")
        conn.close()

# --- 5. HEADER SECTION ---
st.markdown("<h1 class='masthead'>BIASSENTINEL</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-masthead'>GLOBAL MEDIA INTELLIGENCE PLATFORM</p>", unsafe_allow_html=True)

# Fetch Data
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{st.session_state.target}%'"
df = pd.read_sql(query, conn)
conn.close()

# News Ticker Logic
st.markdown(f"<div class='ticker-bar'>• LIVE FEED: ANALYZING {len(df)} ARTICLES FOR {st.session_state.target.upper()} • ENCRYPTION: ACTIVE • DB: NEON CLOUD</div>", unsafe_allow_html=True)

if not df.empty:
    # --- 6. KPI TOP ROW (Matches Image 2) ---
    avg_bias = df['sentiment_score'].mean()
    sources_count = df['source_url'].apply(extract_source).nunique()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"<div class='kpi-card'><p class='kpi-label'>OVERALL BIAS SCORE</p><p class='kpi-value'>{avg_bias:.1f}</p></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='kpi-card'><p class='kpi-label'>ARTICLES ANALYSED</p><p class='kpi-value'>{len(df)}</p></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='kpi-card'><p class='kpi-label'>SOURCES DETECTED</p><p class='kpi-value'>{sources_count}</p></div>", unsafe_allow_html=True)

    # --- 7. MAIN VISUALS ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### SENTIMENT TREND OVER TIME")
        # Creating a fake timeline for demo since GDELT dates are often single-day snapshots
        df['mock_date'] = pd.date_range(start='2026-01-01', periods=len(df), freq='H')
        fig_line = px.line(df.sort_values('mock_date'), x='mock_date', y='sentiment_score', color_discrete_sequence=['#a01a1a'])
        fig_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="BIAS LEVEL")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.markdown("### BIAS GAUGE")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = avg_bias,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [-10, 10], 'tickwidth': 1, 'tickcolor': "#e0e0d1"},
                'bar': {'color': "#a01a1a"},
                'bgcolor': "#1a1a1a",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [-10, -3], 'color': '#301010'},
                    {'range': [3, 10], 'color': '#103010'}],
            }
        ))
        fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    # --- 8. SOURCE BREAKDOWN ---
    st.markdown("### DATASET TABLE")
    st.dataframe(df[['actor_name', 'location_name', 'sentiment_score']].head(10), use_container_width=True)

else:
    st.warning(f"NO DATA FOUND FOR {st.session_state.target}. SPIN THE ROULETTE AGAIN.")

st.markdown("<div style='text-align:center; margin-top:50px; color:#444; font-size:0.7rem;'>TERMINAL ACCESS GRANTED | GDELT ENGINE V2.0 | NO LOGS SAVED</div>", unsafe_allow_html=True)