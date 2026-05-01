import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & CYBER THEME ---
st.set_page_config(page_title="SHADOW NETWORK | RESTORED", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .main { background-color: #050b14; color: #e1e4e8; font-family: 'JetBrains Mono', monospace; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #1e3a8a; }
    .slot-machine-sidebar { 
        font-size: 1.2rem; font-weight: bold; color: #00d4ff; text-align: center; 
        border: 1px solid #00d4ff; border-radius: 8px; padding: 10px; 
        background: #050b14; margin-bottom: 10px; text-shadow: 0 0 5px #00d4ff; 
    }
    .legend-box { border-left: 5px solid #58a6ff; padding: 20px; background-color: #161b22; border-radius: 4px; margin-bottom: 25px; color: #8b949e; }
    .cyber-card { border-radius: 12px; padding: 20px; background: #161b22; border: 1px solid #30363d; height: 100%; transition: 0.3s; }
    .cyber-card:hover { transform: translateY(-5px); border-color: #58a6ff; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(90deg, #1f6feb, #238636); color: white; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA UTILITIES ---
def standardize_name(name):
    if not name: return "Unknown"
    mapping = {"Russian Federation": "Russia", "United States of America": "USA", "United Kingdom": "UK"}
    return mapping.get(str(name).strip(), str(name).strip())

def get_data(query):
    try:
        conn = psycopg2.connect(host="localhost", database="sentinel_db", user="postgres", password="password")
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"📡 CONNECTION ERROR: {e}")
        return pd.DataFrame()

def extract_source(url):
    try: return urlparse(url).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. SESSION STATE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

# --- 4. SIDEBAR: ROULETTE ---
with st.sidebar:
    st.markdown("### 🎰 GLOBAL ROULETTE")
    try:
        raw_names = get_data("SELECT DISTINCT location_name FROM global_events")['location_name'].tolist()
        country_list = list(set([standardize_name(c) for c in raw_names if c]))
    except:
        country_list = ["India", "USA", "Russia", "UK", "China"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("🎰 SPIN WHEEL"):
        for i in range(12):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.balloons()
        st.rerun()

# --- 5. MAIN INTERFACE ---
st.title("🛰️ SHADOW NETWORK: GLOBAL BIAS ENGINE")
st.markdown('<div class="legend-box">Analyzing news sentiment to identify systemic bias. Red: Conflict focus | Green: Stability focus.</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("🎯 ENTER TARGET COUNTRY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ PRIORITY FILTER:", ["Most Negative First", "Most Positive First"])

order_sql = "ASC" if "Negative" in sort_order else "DESC"

try:
    # --- RESTORED SECTION 1: THE TABLE ---
    st.subheader(f"📊 Media Bias Landscape: {target.upper()}")
    bias_query = f"""
        SELECT source_url, AVG(CAST(sentiment_score AS NUMERIC)) as avg_score, COUNT(*) as vol
        FROM global_events WHERE location_name ILIKE '%{target}%'
        GROUP BY source_url ORDER BY avg_score {order_sql} LIMIT 10
    """
    df = get_data(bias_query)

    if not df.empty:
        df['CHANNEL'] = df['source_url'].apply(extract_source)
        def get_label(s):
            if s < -4: return "🛑 SYSTEMIC NEGATIVE"
            if s > 4: return "✨ SYSTEMIC POSITIVE"
            return "⚖️ NEUTRAL ALIGNMENT"
        
        df['ANALYSIS'] = df['avg_score'].apply(get_label)
        df['DATABASE VOLUME'] = df['vol'].astype(str) + " Articles"
        
        # Displaying the Restored Table
        st.table(df[['CHANNEL', 'ANALYSIS', 'DATABASE VOLUME']])

        # --- SECTION 2: GRAPHS ---
        st.markdown("---")
        st.subheader("📉 SIGNAL ANALYTICS")
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.histogram(df, x="avg_score", title="Sentiment Distribution", color_discrete_sequence=['#58a6ff'])
            fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.bar(df, x="avg_score", y="CHANNEL", orientation='h', title="Bias by Outlet", color="avg_score", color_continuous_scale="RdBu")
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)

        # --- SECTION 3: CARDS ---
        st.markdown("---")
        st.subheader("📑 RECENT SIGNAL INTERCEPTS")
        news_df = get_data(f"SELECT sentiment_score, source_url FROM global_events WHERE location_name ILIKE '%{target}%' LIMIT 6")
        grid = st.columns(3)
        for i, row in news_df.iterrows():
            with grid[i % 3]:
                score = float(row['sentiment_score'])
                color = "#f85149" if score < -5 else "#d29922" if score < 0 else "#58a6ff" if score < 5 else "#3fb950"
                st.markdown(f"""<div class="cyber-card" style="border-top: 5px solid {color};">
                    <h4 style="margin:0;">📡 {extract_source(row['source_url'])}</h4>
                    <p style="color: {color}; margin-top:10px;"><b>{score}</b></p>
                </div>""", unsafe_allow_html=True)
                st.link_button("DECRYPT", row['source_url'], use_container_width=True)
    else:
        st.info("No signals detected.")
except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(88, 166, 255, 0.1); text-align: center; padding: 5px; color: #58a6ff;">SCANNING COMPLETE</div>', unsafe_allow_html=True)