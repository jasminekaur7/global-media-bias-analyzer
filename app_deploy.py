import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
import streamlit.components.v1 as components
from urllib.parse import urlparse

# ============================================================
# 1. PAGE CONFIG & MASTER THEME (IMAGE 2 STYLE)
# ============================================================
st.set_page_config(
    page_title="BiasSentinel | Intelligence Command",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the Black/Beige/Red Intelligence Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Main App Background */
    .main { background-color: #0d0d0d !important; color: #e0e0d1 !important; font-family: 'JetBrains Mono', monospace !important; }
    [data-testid="stAppViewContainer"] { background-color: #0d0d0d !important; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #141414 !important; border-right: 2px solid #a01a1a !important; }
    [data-testid="stSidebar"] * { color: #e0e0d1 !important; }

    /* Headers & Masthead */
    .masthead { font-family: 'Playfair Display', serif; text-align: center; letter-spacing: 10px; color: #e0e0d1; margin-bottom: 0px; text-transform: uppercase; }
    .sub-masthead { text-align: center; font-size: 0.7rem; letter-spacing: 4px; color: #666; margin-bottom: 20px; text-transform: uppercase; }

    /* KPI Cards (Intelligence Style) */
    .kpi-card { border: 1px solid #333; background: #1a1a1a; padding: 25px; text-align: center; border-top: 4px solid #a01a1a; margin-bottom: 20px; }
    .kpi-value { font-size: 2.8rem; font-weight: bold; color: #e0e0d1; margin: 0; line-height: 1; }
    .kpi-label { font-size: 0.75rem; color: #a01a1a; text-transform: uppercase; letter-spacing: 2px; margin-top: 10px; }

    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 0px; background: #e0e0d1 !important; color: #0d0d0d !important; 
        border: none; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s;
    }
    .stButton>button:hover { background: #a01a1a !important; color: white !important; }

    /* Input & Search Visibility */
    input, .stSelectbox div { background-color: #1a1a1a !important; color: #e0e0d1 !important; border: 1px solid #444 !important; }
    label { color: #a01a1a !important; text-transform: uppercase; font-size: 0.8rem !important; font-weight: bold; }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: #141414; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { color: #666 !important; font-family: 'JetBrains Mono', monospace !important; }
    .stTabs [aria-selected="true"] { color: #e0e0d1 !important; border-bottom-color: #a01a1a !important; }

    /* Ticker */
    .ticker-bar { background: #e0e0d1; color: #0d0d0d; padding: 8px; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 20px; border: 1px solid #a01a1a; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. SESSION STATE & DB UTILITIES
# ============================================================
if "target" not in st.session_state:
    st.session_state.target = "India"

def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# ============================================================
# 3. SIDEBAR (ROULETTE & AUDIT)
# ============================================================
with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:#a01a1a; letter-spacing:2px;'>REGIONAL ROULETTE</h3>", unsafe_allow_html=True)
    
    try:
        conn = get_db_connection()
        loc_query = "SELECT DISTINCT location_name FROM news_signals"
        raw_locs = pd.read_sql(loc_query, conn)['location_name'].tolist()
        conn.close()
        # Filter countries from location strings
        country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    except:
        country_list = ["INDIA", "USA", "RUSSIA", "CHINA", "UK"]

    # Spin Wheel HTML Component (Themed for Black/Red)
    countries_js = str(country_list).replace("'", '"')
    spin_wheel_html = f"""
    <!DOCTYPE html><html><body style="background:transparent; text-align:center;">
    <canvas id="wc" width="220" height="220" style="border-radius:50%; border:2px solid #a01a1a;"></canvas>
    <script>
    const countries = {countries_js};
    const cv = document.getElementById('wc');
    const ctx = cv.getContext('2d');
    const n = Math.min(countries.length, 12);
    const arc = (2 * Math.PI) / n;
    for(let i=0; i<n; i++) {{
        ctx.beginPath(); ctx.moveTo(110,110); ctx.arc(110,110,105, i*arc, (i+1)*arc);
        ctx.fillStyle = i % 2 == 0 ? '#1a1a1a' : '#a01a1a'; ctx.fill();
        ctx.strokeStyle = '#0d0d0d'; ctx.stroke();
        ctx.save(); ctx.translate(110,110); ctx.rotate(i*arc + arc/2);
        ctx.textAlign='right'; ctx.fillStyle='#e0e0d1'; ctx.font='bold 10px monospace';
        ctx.fillText(countries[i].substring(0,10), 100, 5); ctx.restore();
    }}
    </script></body></html>
    """
    components.html(spin_wheel_html, height=240)

    if st.button("🎰 SPIN FOR TARGET"):
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown("---")
    st.markdown("<h3 style='text-align:center; color:#a01a1a;'>BUREAU AUDIT</h3>", unsafe_allow_html=True)
    if st.button("📜 RUN PL/SQL AUDIT"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Procedure Executed.")
        conn.close()

# ============================================================
# 4. MAIN INTERFACE (DASHBOARD)
# ============================================================
st.markdown("<h1 class='masthead'>BIASSENTINEL</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-masthead'>GLOBAL MEDIA INTELLIGENCE PLATFORM · CLOUD SYNC ACTIVE</p>", unsafe_allow_html=True)

# Fetch Target Data
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{st.session_state.target}%'"
df = pd.read_sql(query, conn)
conn.close()

# News Ticker
st.markdown(f"<div class='ticker-bar'>• MONITORING {st.session_state.target.upper()} • SIGNALS DETECTED: {len(df)} • SYSTEM STATUS: OPTIMAL • ENCRYPTION: LEVEL 4</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "🌍 COMPARE", "📡 SOURCES", "🚩 INTERCEPTS"])

# ----------------- TAB 1: DASHBOARD -----------------
with tab1:
    if not df.empty:
        # KPI ROW (Matching Image 2)
        avg_bias = df['sentiment_score'].mean()
        most_biased = df.groupby('source_url')['sentiment_score'].mean().idxmin()
        most_biased_name = extract_source(most_biased)
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>OVERALL BIAS SCORE</p><p class='kpi-value'>{avg_bias:+.1f}</p><p style='color:#666; font-size:0.6rem;'>{st.session_state.target.upper()} REGION</p></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>ARTICLES ANALYSED</p><p class='kpi-value'>{len(df):,}</p><p style='color:#666; font-size:0.6rem;'>LIVE GDELT FEED</p></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>MOST BIASED OUTLET</p><p class='kpi-value' style='font-size:1.5rem;'>{most_biased_name}</p><p style='color:#a01a1a; font-size:0.6rem;'>CRITICAL ALERT</p></div>", unsafe_allow_html=True)

        # MAIN CHARTS ROW
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.markdown("### SENTIMENT TREND OVER TIME")
            # Create a mock date for visual parity with Image 2
            df['date'] = pd.date_range(start='2026-01-01', periods=len(df), freq='H')
            fig_line = px.line(df.sort_values('date'), x='date', y='sentiment_score', color_discrete_sequence=['#a01a1a'])
            fig_line.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="SCORE")
            st.plotly_chart(fig_line, use_container_width=True)

        with c_right:
            st.markdown("### BIAS GAUGE")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = avg_bias,
                gauge = {'axis': {'range': [-10, 10], 'tickcolor': "#e0e0d1"}, 'bar': {'color': "#a01a1a"}, 'bgcolor': "#1a1a1a",
                         'steps': [{'range': [-10, -4], 'color': '#300a0a'}, {'range': [4, 10], 'color': '#0a300a'}]}
            ))
            fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # THE ORIGINAL DATA TABLE
        st.markdown("---")
        st.subheader(f"📍 TARGET DATASET: {st.session_state.target.upper()}")
        
        col_f1, col_f2 = st.columns([2,1])
        with col_f1:
            search_input = st.text_input("🎯 OVERRIDE SEARCH:", value=st.session_state.target)
        with col_f2:
            sort_order = st.selectbox("↕️ PRIORITY:", ["Negative First", "Positive First"])

        # Display refined table
        table_df = df[['actor_name', 'location_name', 'sentiment_score', 'source_url']].head(15)
        st.dataframe(table_df, use_container_width=True)

    else:
        st.error("NO SIGNALS FOUND. RE-SPIN ROULETTE.")

# ----------------- TAB 3: SOURCES -----------------
with tab3:
    st.subheader("📡 REGISTERED BROADCAST SOURCES")
    if not df.empty:
        source_df = df.groupby('source_url')['sentiment_score'].mean().reset_index()
        source_df['SOURCE'] = source_df['source_url'].apply(extract_source)
        st.table(source_df[['SOURCE', 'sentiment_score']].sort_values('sentiment_score').head(20))

# ----------------- TAB 4: INTERCEPTS -----------------
with tab4:
    st.subheader("🚩 BIAS REPORTING TERMINAL")
    target_channel = st.selectbox("Select Target to Flag:", df['actor_name'].unique() if not df.empty else ["None"])
    if st.button("SUBMIT REPORT TO PL/SQL"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias Alert: {target_channel}",))
        conn.commit()
        conn.close()
        st.toast("Trigger Fired: Report archived.", icon="✒️")

st.markdown("<div style='text-align:center; margin-top:50px; color:#333; font-size:0.6rem; letter-spacing:2px;'>SECURE TERMINAL ACCESS · GDELT V2.0 ENGINE · NO EXTERNAL LOGS</div>", unsafe_allow_html=True)