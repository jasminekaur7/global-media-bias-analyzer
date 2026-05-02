import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & HIGH-CONTRAST INTELLIGENCE THEME ---
st.set_page_config(page_title="SHADOW NETWORK | BIAS SENTINEL", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=IBM+Plex+Mono:wght@400;500&family=Unna:ital@0;1&display=swap');
    
    :root {
        --ink: #0f0e0c; --paper: #f4ede0; --aged: #ece2cc; --crease: #c8b99a;
        --red: #b52a2a; --green: #1a6b45; --muted: #7a6a52;
        --hf: 'Playfair Display', serif; --mono: 'IBM Plex Mono', monospace; --body: 'Unna', serif;
    }

    /* Force high contrast: Dark text on Paper background */
    .main { background-color: var(--paper); color: var(--ink); font-family: var(--body); }
    [data-testid="stSidebar"] { background-color: var(--aged); border-right: 2px solid var(--ink); }
    
    /* Ensure all Streamlit text elements are visible */
    .stMarkdown, p, span, label, .stSelectbox, .stTextInput { color: var(--ink) !important; }
    
    /* Masthead & Ticker[cite: 1] */
    .masthead { text-align: center; padding: 15px; border-bottom: 3px double var(--ink); background: var(--paper); }
    .mast-title { font-family: var(--hf); font-size: 38px; font-weight: 900; letter-spacing: 6px; text-transform: uppercase; color: var(--ink); margin: 0; }
    .ticker-wrap { background: var(--ink); color: var(--paper); overflow: hidden; padding: 6px 0; }
    .ticker-track { display: inline-block; white-space: nowrap; animation: tick 30s linear infinite; font-family: var(--mono); font-size: 10px; }
    @keyframes tick { from { transform: translateX(100%); } to { transform: translateX(-100%); } }

    /* Legend Box - Original Layout Style */
    .legend-box { border: 1px solid var(--ink); border-left: 10px solid var(--red); padding: 15px; background-color: #ffffff; color: var(--ink); font-style: italic; margin-bottom: 20px; }

    /* Cards - Restore Clipping Style */
    .cyber-card { border-radius: 0px; padding: 15px; background: #ffffff; border: 1px solid var(--crease); height: 100%; transition: 0.3s; box-shadow: 2px 2px 0px var(--crease); }
    .cyber-card:hover { border-color: var(--red); transform: translateY(-3px); }
    
    /* Slot Machine Sidebar */
    .slot-machine-sidebar { 
        font-family: var(--mono); font-size: 1.1rem; font-weight: bold; color: var(--red); 
        text-align: center; border: 2px solid var(--ink); padding: 12px; 
        background: #ffffff; margin-bottom: 10px; text-transform: uppercase;
    }

    .stButton>button { border-radius: 0px; background: var(--ink); color: var(--paper); font-family: var(--mono); font-size: 10px; width: 100%; }
    .stButton>button:hover { background: var(--red); color: white; border-color: var(--red); }
    
    /* Styling for the original data table */
    .stTable { background-color: #ffffff !important; border: 1px solid var(--ink); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE UTILITIES ---
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. MASTHEAD & TICKER ---
st.markdown("""
    <div class="masthead">
        <div style="font-family:var(--mono); font-size:9px; letter-spacing:3px; color:var(--muted); text-transform:uppercase;">Global Media Intelligence Platform</div>
        <div class="mast-title">BiasSentinel</div>
    </div>
    <div class="ticker-wrap">
        <div class="ticker-track">
            SATELLITE SYNC: ACTIVE &nbsp;·&nbsp; DATABASE: NEON CLOUD POSTGRESQL &nbsp;·&nbsp; 
            PL/SQL TRIGGER STATUS: STANDBY &nbsp;·&nbsp; REUTERS BIAS INDEX: -4.8 &nbsp;·&nbsp; 
            BBC.COM MONITORING: CRITICAL &nbsp;·&nbsp; TOTAL SIGNALS: 12,840
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR: ORIGINAL ROULETTE LOGIC ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

with st.sidebar:
    st.markdown("<h3 style='font-family:var(--hf); font-size:1.2rem; border-bottom:1px solid var(--ink)'>REGIONAL ROULETTE</h3>", unsafe_allow_html=True)
    try:
        conn = get_db_connection()
        raw_locs = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)['location_name'].tolist()
        conn.close()
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "RUSSIA", "UK"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("🎰 SPIN FOR TARGET"):
        for i in range(12):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()
    
    st.markdown("---")
    st.markdown("<h3 style='font-family:var(--hf); font-size:1.2rem;'>BUREAU AUDIT</h3>", unsafe_allow_html=True)
    if st.button("📜 RUN BIAS AUDIT (CURSOR)"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit Procedure Executed.")
        conn.close()

# --- 5. MAIN CONTENT: ORIGINAL LAYOUT ---
st.markdown(f'<div class="legend-box">DEPLOYMENT ADVISORY: Analyzing regional bias patterns for {st.session_state.target.upper()}. Records retrieved via Cloud SQL.</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("🎯 ENTER TARGET GEOGRAPHY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ EDITORIAL PRIORITY:", ["Most Negative First", "Most Positive First"])

# Fetch Data from SQL
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{st.session_state.target}%'"
filtered_df = pd.read_sql(query, conn)
conn.close()

if not filtered_df.empty:
    ascending = True if "Negative" in sort_order else False
    
    # Original Aggregation Table Logic
    df_grouped = filtered_df.groupby('source_url')['sentiment_score'].agg(['mean', 'count']).reset_index()
    df_grouped.columns = ['source_url', 'avg_score', 'vol']
    df_grouped = df_grouped.sort_values(by='avg_score', ascending=ascending).head(15)
    df_grouped['CHANNEL'] = df_grouped['source_url'].apply(extract_source)
    
    def get_label(s):
        if s < -4: return "🛑 SYSTEMIC NEGATIVE"
        if s > 4: return "✨ SYSTEMIC POSITIVE"
        return "⚖️ NEUTRAL ALIGNMENT"
    df_grouped['ANALYSIS'] = df_grouped['avg_score'].apply(get_label)

    # --- RESTORED PRIORITY: THE DATA TABLE ---
    st.markdown(f"<h2 style='font-family:var(--hf)'>MEDIA LANDSCAPE: {st.session_state.target.upper()}</h2>", unsafe_allow_html=True)
    st.table(df_grouped[['CHANNEL', 'ANALYSIS', 'vol']].rename(columns={'vol': 'Articles'}))

    # --- SECTION 2: THE GRAPHS (Original Priority) ---
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.histogram(filtered_df, x="sentiment_score", title="SENTIMENT POLARITY SPREAD", color_discrete_sequence=['#b52a2a'])
        fig1.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#0f0e0c")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="TOP SOURCE COMPARISON", color_discrete_sequence=['#1a1a1a'])
        fig2.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#0f0e0c")
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 3: PL/SQL TRIGGER TEST ---
    st.markdown("---")
    st.markdown("<h3 style='font-family:var(--hf)'>REPORT CHANNEL BIAS (TRIGGER TEST)</h3>", unsafe_allow_html=True)
    col_rep1, col_rep2 = st.columns([3,1])
    with col_rep1:
        report_channel = st.selectbox("Select Source for Review:", df_grouped['CHANNEL'].tolist())
    with col_rep2:
        if st.button("🚩 SUBMIT FLAG"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias Flagged: {report_channel}",))
            conn.commit()
            conn.close()
            st.toast(f"Trigger Executed: Audit Log Updated.", icon="✒️")

    # --- SECTION 4: CARDS (RECENT SIGNALS) ---
    st.markdown("---")
    st.markdown("<h3 style='font-family:var(--hf)'>RECENT SIGNAL INTERCEPTS</h3>", unsafe_allow_html=True)
    cards_df = filtered_df.sample(min(len(filtered_df), 6))
    grid = st.columns(3)
    for i, (idx, row) in enumerate(cards_df.iterrows()):
        with grid[i % 3]:
            score = row['sentiment_score']
            color = "#b52a2a" if score < 0 else "#1a6b45"
            st.markdown(f"""<div class="cyber-card" style="border-top: 5px solid {color};">
                <div style="font-family:var(--mono); font-size:10px; color:var(--muted);">{extract_source(row['source_url'])}</div>
                <h4 style="margin:8px 0; font-family:var(--hf); font-size:1.1rem;">IMPACT ANALYSIS</h4>
                <p style="color: {color}; font-family:var(--mono); font-weight:bold;">SCORE: {score:.2f}</p>
            </div>""", unsafe_allow_html=True)
            st.link_button("DECRYPT SOURCE", str(row['source_url']), use_container_width=True)
else:
    st.info("Searching regional signal archives...")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: var(--ink); text-align: center; padding: 5px; color: var(--paper); font-family:var(--mono); font-size: 0.7rem;">OFFICIAL BIASSENTINEL DISPATCH | DATABASE: NEON CLOUD | PL/SQL ENABLED</div>', unsafe_allow_html=True)