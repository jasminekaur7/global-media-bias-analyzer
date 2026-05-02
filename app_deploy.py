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
# 1. PAGE CONFIG & INTELLIGENCE THEME
# ============================================================
st.set_page_config(
    page_title="BiasSentinel | Intelligence Command",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Deep Intelligence Theme: Black, Beige, and Red
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    .main { background-color: #0d0d0d !important; color: #e0e0d1 !important; font-family: 'JetBrains Mono', monospace !important; }
    [data-testid="stAppViewContainer"] { background-color: #0d0d0d !important; }
    [data-testid="stSidebar"] { background-color: #141414 !important; border-right: 2px solid #a01a1a !important; }
    [data-testid="stSidebar"] * { color: #e0e0d1 !important; }

    .masthead { font-family: 'Playfair Display', serif; text-align: center; letter-spacing: 10px; color: #e0e0d1; margin-bottom: 0px; text-transform: uppercase; }
    .sub-masthead { text-align: center; font-size: 0.7rem; letter-spacing: 4px; color: #666; margin-bottom: 20px; text-transform: uppercase; }

    /* KPI Cards from Image 2 */
    .kpi-card { border: 1px solid #333; background: #1a1a1a; padding: 25px; text-align: center; border-top: 4px solid #a01a1a; margin-bottom: 20px; }
    .kpi-value { font-size: 2.8rem; font-weight: bold; color: #e0e0d1; margin: 0; line-height: 1; }
    .kpi-label { font-size: 0.75rem; color: #a01a1a; text-transform: uppercase; letter-spacing: 2px; margin-top: 10px; }

    /* Buttons & Tabs */
    .stButton>button { 
        width: 100%; border-radius: 0px; background: #e0e0d1 !important; color: #0d0d0d !important; 
        border: none; font-weight: bold; text-transform: uppercase; letter-spacing: 2px;
    }
    .stButton>button:hover { background: #a01a1a !important; color: white !important; }
    .stTabs [data-baseweb="tab"] { color: #666 !important; font-family: 'JetBrains Mono', monospace !important; letter-spacing: 2px; }
    .stTabs [aria-selected="true"] { color: #e0e0d1 !important; border-bottom-color: #a01a1a !important; }

    /* Input Fields Fix */
    input, .stSelectbox div { background-color: #1a1a1a !important; color: #e0e0d1 !important; border: 1px solid #444 !important; }
    label { color: #a01a1a !important; text-transform: uppercase; font-size: 0.8rem !important; font-weight: bold; }
    
    .ticker-bar { background: #e0e0d1; color: #0d0d0d; padding: 8px; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; border: 1px solid #a01a1a; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. DATABASE & SESSION UTILITIES (NEON CLOUD)
# ============================================================
if "target" not in st.session_state:
    st.session_state.target = "India"

def get_db_connection():
    # Using your Neon Cloud Deployment string
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# ============================================================
# 3. SIDEBAR (BUREAU CONTROLS)
# ============================================================
with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:#a01a1a; letter-spacing:2px;'>BUREAU AUDIT</h3>", unsafe_allow_html=True)
    if st.button("📜 RUN PL/SQL CURSOR"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CALL run_bias_audit();")
        st.sidebar.success("Audit Procedures Synced.")
        conn.close()
    
    st.markdown("---")
    st.caption("Intelligence Terminal v3.0")
    st.caption("Deployment: Neon Cloud PostgreSQL")

# ============================================================
# 4. HEADER & TICKER
# ============================================================
st.markdown("<h1 class='masthead'>BIASSENTINEL</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-masthead'>GLOBAL MEDIA INTELLIGENCE PLATFORM · CLOUD DEPLOYMENT ACTIVE</p>", unsafe_allow_html=True)

# Fetch Data for Ticker/KPIs
conn = get_db_connection()
query = f"SELECT * FROM news_signals WHERE location_name ILIKE '%{st.session_state.target}%'"
df = pd.read_sql(query, conn)
conn.close()

st.markdown(f"<div class='ticker-bar'>• MONITORING {st.session_state.target.upper()} • ANALYZING {len(df)} SIGNALS • DB STATUS: SYNCED • BIAS DETECTION: ON</div>", unsafe_allow_html=True)

# ============================================================
# 5. INTEGRATED TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "🎰 ROULETTE", "⚔️ COMPARE", "📡 SOURCES"])

# ----------------- TAB 1: DASHBOARD (YOUR ORIGINAL FRONT PAGE) -----------------
with tab1:
    if not df.empty:
        # KPI ROW
        avg_bias = df['sentiment_score'].mean()
        sources_count = df['source_url'].apply(extract_source).nunique()
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>OVERALL BIAS SCORE</p><p class='kpi-value'>{avg_bias:+.1f}</p></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>ARTICLES ANALYSED</p><p class='kpi-value'>{len(df):,}</p></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi-card'><p class='kpi-label'>SOURCES DETECTED</p><p class='kpi-value'>{sources_count}</p></div>", unsafe_allow_html=True)

        # YOUR ORIGINAL TARGET TABLE & PRIORITY
        st.markdown("---")
        st.subheader(f"📍 REGIONAL ANALYSIS: {st.session_state.target.upper()}")
        
        col_f1, col_f2 = st.columns([3, 2])
        with col_f1:
            target_search = st.text_input("🎯 SEARCH GEOGRAPHY:", value=st.session_state.target)
            st.session_state.target = target_search
        with col_f2:
            sort_order = st.selectbox("↕️ EDITORIAL PRIORITY:", ["Most Negative First", "Most Positive First"])

        # Table Logic
        ascending = True if "Negative" in sort_order else False
        table_df = df.groupby('source_url')['sentiment_score'].agg(['mean', 'count']).reset_index()
        table_df.columns = ['source_url', 'avg_score', 'Articles']
        table_df['CHANNEL'] = table_df['source_url'].apply(extract_source)
        table_df = table_df.sort_values(by='avg_score', ascending=ascending).head(15)
        
        st.table(table_df[['CHANNEL', 'avg_score', 'Articles']].rename(columns={'avg_score': 'Bias Score'}))

        # DASHBOARD GRAPHS
        g_left, g_right = st.columns([2, 1])
        with g_left:
            st.markdown("### SENTIMENT POLARITY SPREAD")
            fig_hist = px.histogram(df, x="sentiment_score", color_discrete_sequence=['#a01a1a'])
            fig_hist.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_hist, use_container_width=True)
        with g_right:
            st.markdown("### BIAS GAUGE")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = avg_bias,
                gauge = {'axis': {'range': [-10, 10], 'tickcolor': "#e0e0d1"}, 'bar': {'color': "#a01a1a"}, 'bgcolor': "#1a1a1a",
                         'steps': [{'range': [-10, -3], 'color': '#300a0a'}, {'range': [3, 10], 'color': '#0a300a'}]}
            ))
            fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

# ----------------- TAB 2: BIAS ROULETTE (INTEGRATED) -----------------
with tab2:
    st.subheader("🎰 GLOBAL SIGNAL ROULETTE")
    
    # Generate List from DB
    conn = get_db_connection()
    raw_locs = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)['location_name'].tolist()
    conn.close()
    country_list = sorted(list(set([str(l).split(',')[-1].strip() for l in raw_locs if l and len(str(l)) > 2])))
    
    countries_js = str(country_list).replace("'", '"')
    
    # Custom Roulette Component
    spin_html = f"""
    <div style="text-align:center; background:#0d0d0d; padding:20px; border:1px solid #333;">
        <canvas id="wc" width="250" height="250" style="border:2px solid #a01a1a; border-radius:50%;"></canvas>
        <script>
            const ctx = document.getElementById('wc').getContext('2d');
            const segs = {countries_js}.slice(0,12);
            const arc = (2 * Math.PI) / segs.length;
            for(let i=0; i<segs.length; i++) {{
                ctx.beginPath(); ctx.moveTo(125,125); ctx.arc(125,125, 120, i*arc, (i+1)*arc);
                ctx.fillStyle = i % 2 == 0 ? '#1a1a1a' : '#a01a1a'; ctx.fill();
                ctx.save(); ctx.translate(125,125); ctx.rotate(i*arc + arc/2);
                ctx.textAlign='right'; ctx.fillStyle='#e0e0d1'; ctx.font='bold 10px monospace';
                ctx.fillText(segs[i].substring(0,10), 115, 5); ctx.restore();
            }}
        </script>
    </div>
    """
    components.html(spin_html, height=300)
    
    if st.button("🎲 SPIN FOR RANDOM GEOGRAPHY"):
        st.session_state.target = random.choice(country_list)
        st.rerun()

# ----------------- TAB 3: COMPARE (SIDE-BY-SIDE) -----------------
with tab3:
    st.subheader("⚔️ CROSS-REGIONAL BIAS COMPARISON")
    comp_a, comp_b = st.columns(2)
    
    with comp_a:
        country_a = st.selectbox("Select Country Alpha:", country_list, index=0)
    with comp_b:
        country_b = st.selectbox("Select Country Beta:", country_list, index=min(1, len(country_list)-1))
        
    # Quick Compare Logic
    conn = get_db_connection()
    df_a = pd.read_sql(f"SELECT sentiment_score FROM news_signals WHERE location_name ILIKE '%{country_a}%'", conn)
    df_b = pd.read_sql(f"SELECT sentiment_score FROM news_signals WHERE location_name ILIKE '%{country_b}%'", conn)
    conn.close()
    
    c1, c2 = st.columns(2)
    c1.metric(f"{country_a} Bias", f"{df_a['sentiment_score'].mean():.2f}")
    c2.metric(f"{country_b} Bias", f"{df_b['sentiment_score'].mean():.2f}")

# ----------------- TAB 4: SOURCES -----------------
with tab4:
    st.subheader("📡 BROADCAST SOURCE ARCHIVE")
    if not df.empty:
        sources_df = df.groupby('source_url')['sentiment_score'].mean().reset_index()
        sources_df['SOURCE'] = sources_df['source_url'].apply(extract_source)
        st.dataframe(sources_df[['SOURCE', 'sentiment_score']].rename(columns={'sentiment_score': 'AVG BIAS'}), use_container_width=True)

# ============================================================
# 6. FOOTER
# ============================================================
st.markdown("<div style='text-align:center; margin-top:50px; color:#444; font-size:0.6rem; letter-spacing:2px;'>SECURE COMMAND ACCESS · GDELT INTELLIGENCE ENGINE · CLOUD STATUS: ONLINE</div>", unsafe_allow_html=True)