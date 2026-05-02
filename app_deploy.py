import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & ADVANCED THEMING ---
st.set_page_config(page_title="SHADOW NETWORK | BIAS SENTINEL", layout="wide")

# Injecting the specific CSS variables and classes from the BiasSentinel theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=IBM+Plex+Mono:wght@400;500&family=Unna:ital@0;1&display=swap');
    
    :root {
        --ink: #0f0e0c; --paper: #f4ede0; --aged: #ece2cc; --crease: #c8b99a;
        --red: #b52a2a; --green: #1a6b45; --muted: #7a6a52;
        --hf: 'Playfair Display', serif; --mono: 'IBM Plex Mono', monospace; --body: 'Unna', serif;
    }

    .main { background-color: var(--paper); color: var(--ink); font-family: var(--body); }
    [data-testid="stSidebar"] { background-color: var(--aged); border-right: 2px solid var(--ink); }
    
    /* Masthead Styling */
    .masthead { text-align: center; padding: 20px; border-bottom: 3px double var(--ink); margin-bottom: 0px; }
    .mast-eyebrow { font-family: var(--mono); font-size: 10px; letter-spacing: 4px; color: var(--muted); text-transform: uppercase; }
    .mast-title { font-family: var(--hf); font-size: 42px; font-weight: 900; letter-spacing: 8px; text-transform: uppercase; color: var(--ink); }
    
    /* Ticker Animation */
    .ticker-wrap { background: var(--ink); color: var(--paper); overflow: hidden; padding: 8px 0; margin-bottom: 20px; }
    .ticker-track { display: inline-block; white-space: nowrap; animation: tick 30s linear infinite; font-family: var(--mono); font-size: 10px; letter-spacing: 1.5px; }
    @keyframes tick { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

    /* Cards & Panels[cite: 1] */
    .stat-card { background: var(--aged); border: 1px solid var(--crease); padding: 20px; border-top: 4px solid var(--red); box-shadow: 2px 2px 0px var(--crease); }
    .intercept-card { background: var(--paper); border: 1px solid var(--crease); padding: 15px; border-top: 3px solid var(--crease); transition: 0.3s; }
    .intercept-card:hover { border-top-color: var(--red); transform: translateY(-3px); }
    
    /* Roulette Box */
    .slot-machine-sidebar { 
        font-family: var(--mono); font-size: 1.2rem; font-weight: bold; color: var(--red); 
        text-align: center; border: 2px solid var(--ink); padding: 15px; 
        background: var(--paper); margin-bottom: 15px; text-transform: uppercase;
    }

    .stButton>button { border-radius: 0px; background: var(--ink); color: var(--paper); font-family: var(--mono); text-transform: uppercase; letter-spacing: 2px; }
    .stButton>button:hover { background: var(--red); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE UTILITIES ---
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. MASTHEAD & TICKER[cite: 1] ---
st.markdown("""
    <div class="masthead">
        <div class="mast-eyebrow">Global Media Intelligence Platform</div>
        <div class="mast-title">BiasSentinel</div>
    </div>
    <div class="ticker-wrap">
        <div class="ticker-track">
            BREAKING: BBC.COM SCORES -7.1 ON INDIA COVERAGE &nbsp;·&nbsp; REUTERS BIAS INDEX AT -4.8 &nbsp;·&nbsp; 
            NDTV REGISTERS +2.2 POSITIVE LEAN &nbsp;·&nbsp; ALJAZEERA AT -3.1 &nbsp;·&nbsp; 
            NEON CLOUD SYNC ACTIVE &nbsp;·&nbsp; GDELT DATABASE: 12,840 ARTICLES ANALYSED
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR: ROULETTE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

with st.sidebar:
    st.markdown("<h3 style='font-family:var(--hf)'>BIAS ROULETTE</h3>", unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        raw_locs = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)['location_name'].tolist()
        conn.close()
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "UK"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("SPIN THE WHEEL"):
        for i in range(12):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()

# --- 5. DATA FETCHING ---
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{st.session_state.target}%'"
df = pd.read_sql(query, conn)
conn.close()

# --- 6. DASHBOARD LAYOUT ---
col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("📍 TARGET GEOGRAPHY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ EDITORIAL PRIORITY:", ["Most Negative First", "Most Positive First"])

if not df.empty:
    # Stats row using the new 'stat-card' class[cite: 1]
    c1, c2, c3 = st.columns(3)
    avg_s = df['sentiment_score'].mean()
    with c1:
        st.markdown(f'<div class="stat-card"><small>OVERALL BIAS</small><h2>{avg_s:.2f}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><small>SIGNAL COUNT</small><h2>{len(df)}</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><small>DATABASE STATUS</small><h2 style="font-size:20px">SYNCED</h2></div>', unsafe_allow_html=True)

    # Graphs using matching Plotly colors
    st.markdown("---")
    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.histogram(df, x="sentiment_score", title="SENTIMENT DISTRIBUTION", color_discrete_sequence=['#b52a2a'])
        fig1.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        df_grouped = df.groupby('source_url')['sentiment_score'].mean().reset_index().head(10)
        fig2 = px.bar(df_grouped, x="sentiment_score", y="source_url", orientation='h', title="TOP SOURCE DISPARITY", color_discrete_sequence=['#0f0e0c'])
        fig2.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # Signal Intercepts using 'intercept-card' class[cite: 1]
    st.markdown("<h3 style='font-family:var(--hf)'>RECENT SIGNAL INTERCEPTS</h3>", unsafe_allow_html=True)
    grid = st.columns(3)
    sample_df = df.sample(min(len(df), 6))
    for i, (idx, row) in enumerate(sample_df.iterrows()):
        with grid[i % 3]:
            st.markdown(f"""<div class="intercept-card">
                <div style="font-family:var(--mono); font-size:9px; color:var(--muted);">{extract_source(row['source_url'])}</div>
                <div style="font-family:var(--hf); font-weight:700; margin:8px 0;">{st.session_state.target.upper()} ANALYSIS</div>
                <div style="color:var(--red); font-family:var(--mono); font-size:11px;">SCORE: {row['sentiment_score']:.2f}</div>
            </div>""", unsafe_allow_html=True)
            st.link_button("DECRYPT SOURCE", str(row['source_url']), use_container_width=True)
else:
    st.info("Awaiting satellite sync for target geography...")