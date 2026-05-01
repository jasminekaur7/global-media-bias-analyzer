import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & THEME ---
st.set_page_config(page_title="SHADOW NETWORK | LIVE", layout="wide")

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

# --- 2. DATABASE UTILITIES (REPLACING CSV MODE) ---
def get_db_connection():
    # CHANGE 'your_password' TO YOUR ACTUAL PGADMIN PASSWORD
    return psycopg2.connect(
        host="localhost",
        database="shadow_network",
        user="postgres",
        password="jasmine" 
    )

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. SESSION STATE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

# --- 4. SIDEBAR: ROULETTE & DBMS CONTROLS ---
with st.sidebar:
    st.markdown("### 🎰 GLOBAL ROULETTE")
    
    # FETCHING COUNTRY LIST FROM DATABASE
    try:
        conn = get_db_connection()
        country_list_query = "SELECT DISTINCT location_name FROM news_signals"
        country_list = pd.read_sql(country_list_query, conn)['location_name'].tolist()
        conn.close()
    except:
        country_list = ["India", "USA", "Russia", "UK"]

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
    
    st.markdown("---")
    st.markdown("### 🛠️ DBMS ADMIN")
    if st.button("📜 RUN BIAS AUDIT (CURSOR)"):
        conn = get_db_connection()
        cur = conn.cursor()
        # This calls your PL/SQL Procedure that uses a CURSOR
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit Procedure Executed. Check pgAdmin 'Messages' for Cursor output.")
        conn.close()

# --- 5. MAIN INTERFACE ---
st.title("🛰️ SHADOW NETWORK: GLOBAL BIAS ENGINE")
st.markdown('<div class="legend-box">DEPLOYMENT MODE: Reading from LIVE PostgreSQL Instance (PL/SQL Enabled).</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("🎯 ENTER TARGET COUNTRY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ PRIORITY FILTER:", ["Most Negative First", "Most Positive First"])

# --- FETCH DATA FROM SQL ---
conn = get_db_connection()
# High-level SQL filtering (Requirement: Demonstrate SQL knowledge)
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{target}%'"
filtered_df = pd.read_sql(query, conn)
conn.close()

if not filtered_df.empty:
    ascending = True if "Negative" in sort_order else False
    
    # Aggregation
    df_grouped = filtered_df.groupby('source_url')['sentiment_score'].agg(['mean', 'count']).reset_index()
    df_grouped.columns = ['source_url', 'avg_score', 'vol']
    df_grouped = df_grouped.sort_values(by='avg_score', ascending=ascending).head(15)
    df_grouped['CHANNEL'] = df_grouped['source_url'].apply(extract_source)
    
    def get_label(s):
        if s < -4: return "🛑 SYSTEMIC NEGATIVE"
        if s > 4: return "✨ SYSTEMIC POSITIVE"
        return "⚖️ NEUTRAL ALIGNMENT"
    df_grouped['ANALYSIS'] = df_grouped['avg_score'].apply(get_label)

    # --- SECTION 1: THE TABLE ---
    st.subheader(f"📊 Media Bias Landscape: {target.upper()}")
    st.table(df_grouped[['CHANNEL', 'ANALYSIS', 'vol']].rename(columns={'vol': 'Articles'}))

    # --- SECTION 2: GRAPHS ---
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.histogram(filtered_df, x="sentiment_score", title="Sentiment Polarity Spread", color_discrete_sequence=['#58a6ff'])
        fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="Top Source Bias Comparison", color="avg_score", color_continuous_scale="RdBu")
        fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 3: PL/SQL TRIGGER TEST ---
    st.markdown("---")
    st.subheader("🚨 REPORT BIAS (TRIGGER TEST)")
    col_rep1, col_rep2 = st.columns([3,1])
    with col_rep1:
        report_channel = st.selectbox("Select Channel to Report:", df_grouped['CHANNEL'].tolist())
    with col_rep2:
        if st.button("🚩 SUBMIT REPORT"):
            conn = get_db_connection()
            cur = conn.cursor()
            # This INSERT fires the PL/SQL Trigger automatically!
            cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias found in {report_channel}",))
            conn.commit()
            conn.close()
            st.toast("Trigger Activated: Database is auditing channel status.", icon="🔥")

    # --- SECTION 4: CARDS ---
    st.markdown("---")
    st.subheader("📑 RECENT SIGNAL INTERCEPTS")
    cards_df = filtered_df.sample(min(len(filtered_df), 6))
    grid = st.columns(3)
    for i, (idx, row) in enumerate(cards_df.iterrows()):
        with grid[i % 3]:
            score = row['sentiment_score']
            color = "#f85149" if score < -5 else "#d29922" if score < 0 else "#58a6ff" if score < 5 else "#3fb950"
            st.markdown(f"""<div class="cyber-card" style="border-top: 5px solid {color};">
                <h4 style="margin:0;">📡 {extract_source(row['source_url'])}</h4>
                <p style="color: {color}; margin-top:10px;"><b>SCORE: {score:.2f}</b></p>
            </div>""", unsafe_allow_html=True)
            st.link_button("DECRYPT", str(row['source_url']), use_container_width=True)
else:
    st.info("Searching database for signal matches...")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(88, 166, 255, 0.1); text-align: center; padding: 5px; color: #58a6ff;">DATABASE SYNC: POSTGRESQL ACTIVE | PL/SQL ENABLED</div>', unsafe_allow_html=True)