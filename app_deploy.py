import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & BIASSENTINEL THEME ---
st.set_page_config(page_title="BIASSENTINEL | LIVE", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    .main { background-color: #0d0d0d; color: #e0e0d1; font-family: 'JetBrains Mono', monospace; }
    [data-testid="stAppViewContainer"] { background-color: #0d0d0d; }
    [data-testid="stSidebar"] { background-color: #141414; border-right: 2px solid #a01a1a; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', serif; color: #e0e0d1; text-transform: uppercase; letter-spacing: 3px; }
    
    /* Roulette Box */
    .slot-machine-sidebar { 
        font-size: 1.4rem; font-weight: bold; color: #ff4b4b; text-align: center; 
        border: 2px solid #a01a1a; padding: 15px; background: #000000; 
        margin-bottom: 15px; text-transform: uppercase; box-shadow: 0 0 10px rgba(160, 26, 26, 0.5);
    }
    
    /* Top Banner / Ticker Area */
    .legend-box { 
        border: 1px solid #444; border-left: 10px solid #a01a1a; padding: 15px; 
        background-color: #1a1a1a; color: #e0e0d1; margin-bottom: 25px; 
        font-size: 0.9rem; text-transform: uppercase;
    }
    
    /* Cards */
    .cyber-card { 
        border-radius: 0px; padding: 20px; background: #1a1a1a; 
        border: 1px solid #333; height: 100%; transition: 0.3s; 
    }
    .cyber-card:hover { border-color: #a01a1a; background: #222; }
    
    /* Comparison Metric Boxes */
    .compare-box {
        padding: 20px; border: 1px solid #444; background: #111; text-align: center; border-top: 4px solid #a01a1a;
    }

    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 0px; background: #e0e0d1; color: #0d0d0d; 
        font-weight: bold; border: 1px solid #e0e0d1; text-transform: uppercase;
    }
    .stButton>button:hover { background: #a01a1a; color: white; border-color: #a01a1a; }
    
    /* Fix for "weird boxes" in selectbox/inputs */
    input, .stSelectbox div { background-color: #1a1a1a !important; color: #e0e0d1 !important; border: 1px solid #444 !important; border-radius: 0px !important; }
    label { color: #a01a1a !important; text-transform: uppercase; font-size: 0.8rem !important; letter-spacing: 1px; font-weight: bold; }
    
    /* Tables */
    .stTable { background-color: #1a1a1a; color: #e0e0d1; border: 1px solid #333; }
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

# --- 4. SIDEBAR: ROULETTE & DBMS CONTROLS ---
with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:#a01a1a;'>REGIONAL ROULETTE</h3>", unsafe_allow_html=True)
    
    try:
        conn = get_db_connection()
        loc_query = "SELECT DISTINCT location_name FROM news_signals"
        raw_locs = pd.read_sql(loc_query, conn)['location_name'].tolist()
        conn.close()
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "RUSSIA", "UK"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("SPIN FOR TARGET"):
        for i in range(8):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()
    
    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color:#a01a1a;'>BUREAU AUDIT</h3>", unsafe_allow_html=True)
    if st.button("RUN BIAS AUDIT"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit complete.")
        conn.close()

# --- 5. MAIN INTERFACE ---
st.markdown("<h1 style='text-align:center; letter-spacing:10px;'>BIASSENTINEL</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; margin-bottom:30px;'>GLOBAL MEDIA INTELLIGENCE ENGINE | V2.0</p>", unsafe_allow_html=True)

st.markdown('<div class="legend-box">DEPLOYMENT ADVISORY: Analyzing regional bias patterns for ' + st.session_state.target.upper() + '. Records retrieved via Cloud SQL.</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    # Removed emojis from labels to fix "weird boxes" issue
    target = st.text_input("TARGET GEOGRAPHY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    # Removed emojis from labels
    sort_order = st.selectbox("EDITORIAL PRIORITY:", ["Most Negative First", "Most Positive First"])

# --- FETCH DATA FROM SQL ---
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{target}%'"
filtered_df = pd.read_sql(query, conn)
conn.close()

if not filtered_df.empty:
    ascending = True if "Negative" in sort_order else False
    df_grouped = filtered_df.groupby('source_url')['sentiment_score'].agg(['mean', 'count']).reset_index()
    df_grouped.columns = ['source_url', 'avg_score', 'vol']
    df_grouped = df_grouped.sort_values(by='avg_score', ascending=ascending).head(15)
    df_grouped['CHANNEL'] = df_grouped['source_url'].apply(extract_source)
    
    def get_label(s):
        if s < -4: return "🛑 SYSTEMIC NEGATIVE"
        if s > 4: return "✨ SYSTEMIC POSITIVE"
        return "⚖️ NEUTRAL ALIGNMENT"
    df_grouped['ANALYSIS'] = df_grouped['avg_score'].apply(get_label)

    st.subheader(f"MEDIA LANDSCAPE: {target.upper()}")
    st.table(df_grouped[['CHANNEL', 'ANALYSIS', 'vol']].rename(columns={'vol': 'Articles'}))

    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.histogram(filtered_df, x="sentiment_score", title="Sentiment Polarity Spread", color_discrete_sequence=['#a01a1a'])
        fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e0e0d1"))
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="Top Source Bias Comparison", color="avg_score", color_continuous_scale=["#a01a1a", "#e0e0d1"])
        fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e0e0d1"))
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 6: COMPARE 2 COUNTRIES ---
    st.markdown("---")
    st.subheader("⚔️ CROSS-REGIONAL COMPARE")
    comp_a, comp_b = st.columns(2)
    
    with comp_a:
        c_a = st.selectbox("COUNTRY ALPHA:", country_list, index=0)
    with comp_b:
        c_b = st.selectbox("COUNTRY BETA:", country_list, index=min(1, len(country_list)-1))

    conn = get_db_connection()
    res_a = pd.read_sql(f"SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE '%{c_a}%'", conn)['avg'].iloc[0]
    res_b = pd.read_sql(f"SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE '%{c_b}%'", conn)['avg'].iloc[0]
    conn.close()

    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"<div class='compare-box'><p style='color:#666; margin:0;'>{c_a}</p><h2 style='color:#a01a1a;'>{res_a if res_a else 0.0:.2f}</h2></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='compare-box'><p style='color:#666; margin:0;'>{c_b}</p><h2 style='color:#e0e0d1;'>{res_b if res_b else 0.0:.2f}</h2></div>", unsafe_allow_html=True)

    # --- SECTION 7: REPORT & CARDS ---
    st.markdown("---")
    st.subheader("🚩 REPORT BIAS")
    col_rep1, col_rep2 = st.columns([3,1])
    with col_rep1:
        report_channel = st.selectbox("CHANNEL TO REPORT:", df_grouped['CHANNEL'].tolist())
    with col_rep2:
        if st.button("SUBMIT REPORT"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias Flagged: {report_channel}",))
            conn.commit()
            conn.close()
            st.toast("Trigger Activated.", icon="✒️")

    st.markdown("---")
    st.subheader("📑 RECENT SIGNAL INTERCEPTS")
    cards_df = filtered_df.sample(min(len(filtered_df), 6))
    grid = st.columns(3)
    for i, (idx, row) in enumerate(cards_df.iterrows()):
        with grid[i % 3]:
            score = row['sentiment_score']
            color = "#a01a1a" if score < 0 else "#e0e0d1"
            st.markdown(f"""<div class="cyber-card" style="border-top: 5px solid {color};">
                <h4 style="margin:0; border:none; font-size:1rem;">📡 {extract_source(row['source_url'])}</h4>
                <p style="color: {color}; margin-top:10px;"><b>BIAS SCORE: {score:.2f}</b></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("READ ARTICLE", str(row['source_url']), use_container_width=True)
else:
    st.info("Scanning for signal matches...")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: #000; text-align: center; padding: 5px; color: #a01a1a; font-size:0.7rem; border-top:1px solid #a01a1a;">BIASSENTINEL DISPATCH | DATABASE: NEON CLOUD | PL/SQL ENABLED</div>', unsafe_allow_html=True)