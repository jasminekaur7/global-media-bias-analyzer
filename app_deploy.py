import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import random
import time
from urllib.parse import urlparse

# --- 1. UI CONFIG & THEME (NEWSPAPER THEME) ---
st.set_page_config(page_title="THE SHADOW NETWORK | PRESS DISPATCH", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+Pro:wght@400;600&display=swap');
    
    /* Background and Base Text */
    .main { background-color: #f4f1ea; color: #1a1a1a; font-family: 'Source Sans Pro', sans-serif; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #e8e4d9; border-right: 2px solid #2c2c2c; }
    
    /* Headers - The "Masthead" look */
    h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: #1a1a1a; border-bottom: 1px solid #d3d3d3; padding-bottom: 5px; }
    
    /* Roulette Box - Mimicking a Headline Box */
    .slot-machine-sidebar { 
        font-size: 1.4rem; font-weight: bold; color: #a01a1a; text-align: center; 
        border: 2px solid #1a1a1a; border-radius: 0px; padding: 15px; 
        background: #ffffff; margin-bottom: 15px; text-transform: uppercase;
        box-shadow: 3px 3px 0px #2c2c2c;
    }
    
    /* Legend/Notice Box */
    .legend-box { border: 1px solid #2c2c2c; border-left: 10px solid #a01a1a; padding: 20px; background-color: #ffffff; margin-bottom: 25px; color: #333333; font-style: italic; }
    
    /* Cards - Mimicking Newspaper Clippings */
    .cyber-card { border-radius: 0px; padding: 20px; background: #ffffff; border: 1px solid #d3d3d3; height: 100%; transition: 0.3s; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .cyber-card:hover { transform: translateY(-3px); border-color: #a01a1a; box-shadow: 4px 4px 0px #a01a1a; }
    
    /* Buttons - "Ink" style */
    .stButton>button { width: 100%; border-radius: 0px; background: #1a1a1a; color: #f4f1ea; font-weight: bold; border: 2px solid #1a1a1a; transition: 0.2s; }
    .stButton>button:hover { background: #a01a1a; color: white; border-color: #a01a1a; }
    
    /* Data Table Styling */
    .stTable { background-color: #ffffff; border: 1px solid #2c2c2c; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE UTILITIES ---
def get_db_connection():
    return psycopg2.connect(
      "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require" 
    )

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# --- 3. SESSION STATE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

# --- 4. SIDEBAR: ROULETTE & DBMS CONTROLS ---
with st.sidebar:
    st.markdown("### 📰 PRESS ROULETTE")
    
    try:
        conn = get_db_connection()
        loc_query = "SELECT DISTINCT location_name FROM news_signals"
        raw_locs = pd.read_sql(loc_query, conn)['location_name'].tolist()
        conn.close()
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "UK", "CANADA"]

    wheel_placeholder = st.empty()
    wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{st.session_state.target.upper()}</div>', unsafe_allow_html=True)

    if st.button("🎲 SPIN FOR REGION"):
        for i in range(12):
            temp = random.choice(country_list)
            wheel_placeholder.markdown(f'<div class="slot-machine-sidebar">{temp.upper()}</div>', unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🛡️ BUREAU CONTROLS")
    if st.button("⚖️ INITIATE BIAS AUDIT"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit complete. Records logged to Bureau archives.")
        conn.close()

# --- 5. MAIN INTERFACE ---
st.title("🗞️ THE SHADOW NETWORK: DAILY BIAS DISPATCH")
st.markdown('<div class="legend-box">INTERNAL MEMO: Analyzing live signal streams from Neon Cloud Database.</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("📍 TARGET GEOGRAPHY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ EDITORIAL PRIORITY:", ["Most Negative First", "Most Positive First"])

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
        if s < -4: return "CRITICAL NEGATIVE"
        if s > 4: return "PROMINENT POSITIVE"
        return "NEUTRAL BALANCE"
    df_grouped['ANALYSIS'] = df_grouped['avg_score'].apply(get_label)

    # --- SECTION 1: THE TABLE ---
    st.subheader(f"Front Page Analysis: {target.upper()}")
    st.table(df_grouped[['CHANNEL', 'ANALYSIS', 'vol']].rename(columns={'vol': 'Records'}))

    # --- SECTION 2: GRAPHS (LIGHT THEME) ---
    c1, c2 = st.columns(2)
    with c1:
        # Changed to plotly_white for newspaper theme
        fig1 = px.histogram(filtered_df, x="sentiment_score", title="Sentiment Distribution", color_discrete_sequence=['#a01a1a'])
        fig1.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        # Red-to-Black color scale for newspaper look
        fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="Top Source Disparity", color="avg_score", color_continuous_scale="Reds")
        fig2.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 3: PL/SQL TRIGGER TEST ---
    st.markdown("---")
    st.subheader("🚩 FLAG CONTENT FOR REVIEW")
    col_rep1, col_rep2 = st.columns([3,1])
    with col_rep1:
        report_channel = st.selectbox("Select Source to Report:", df_grouped['CHANNEL'].tolist())
    with col_rep2:
        if st.button("SUBMIT REPORT"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias Flagged: {report_channel}",))
            conn.commit()
            conn.close()
            st.toast(f"Report Filed: Audit Trigger initiated for {report_channel}.", icon="✒️")

    # --- SECTION 4: CARDS (THE "CLIPPINGS") ---
    st.markdown("---")
    st.subheader("📑 RECENT WIRE CLIPPINGS")
    cards_df = filtered_df.sample(min(len(filtered_df), 6))
    grid = st.columns(3)
    for i, (idx, row) in enumerate(cards_df.iterrows()):
        with grid[i % 3]:
            score = row['sentiment_score']
            color = "#a01a1a" if score < 0 else "#238636"
            st.markdown(f"""<div class="cyber-card" style="border-left: 5px solid {color};">
                <h4 style="margin:0; border:none; font-size:1.1rem;">🗞️ {extract_source(row['source_url'])}</h4>
                <p style="color: {color}; margin-top:10px; font-weight:bold;">IMPACT SCORE: {score:.2f}</p>
            </div>""", unsafe_allow_html=True)
            st.link_button("READ FULL ARTICLE", str(row['source_url']), use_container_width=True)
else:
    st.info(f"No headlines found for {target}. Scanning the archives...")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: #1a1a1a; text-align: center; padding: 5px; color: #f4f1ea; font-size: 0.8rem;">OFFICIAL DISPATCH | DATABASE: NEON CLOUD | REFRESH RATE: LIVE</div>', unsafe_allow_html=True)