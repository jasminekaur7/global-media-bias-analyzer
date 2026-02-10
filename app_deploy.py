import streamlit as st
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

# --- 2. DATA UTILITIES (CSV MODE) ---
@st.cache_data
def get_full_dataset():
    # This reads the CSV file you exported from pgAdmin
    try:
        df = pd.read_csv("data.csv")
        # Ensure sentiment_score is a number
        df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data.csv: {e}")
        return pd.DataFrame(columns=['location_name', 'sentiment_score', 'source_url'])

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace('www.', '').upper()
    except: return "UNKNOWN SOURCE"

# Load the fuel
all_data = get_full_dataset()

# --- 3. SESSION STATE ---
if 'target' not in st.session_state:
    st.session_state.target = "India"

# --- 4. SIDEBAR: ROULETTE ---
with st.sidebar:
    st.markdown("### 🎰 GLOBAL ROULETTE")
    country_list = sorted(all_data['location_name'].dropna().unique().tolist())
    
    if not country_list:
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

# --- 5. MAIN INTERFACE ---
st.title("🛰️ SHADOW NETWORK: GLOBAL BIAS ENGINE")
st.markdown('<div class="legend-box">DEPLOYMENT MODE: Reading from static satellite data stream.</div>', unsafe_allow_html=True)

col_search, col_sort = st.columns([3, 2])
with col_search:
    target = st.text_input("🎯 ENTER TARGET COUNTRY:", value=st.session_state.target)
    st.session_state.target = target
with col_sort:
    sort_order = st.selectbox("↕️ PRIORITY FILTER:", ["Most Negative First", "Most Positive First"])

# Filter the data based on search
mask = all_data['location_name'].str.contains(target, case=False, na=False)
filtered_df = all_data[mask].copy()

if not filtered_df.empty:
    # Sorting logic
    ascending = True if "Negative" in sort_order else False
    
    # Create the aggregation table
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
    st.markdown("---")
    st.subheader("📉 SIGNAL ANALYTICS")
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.histogram(filtered_df, x="sentiment_score", title="Sentiment Polarity Spread", color_discrete_sequence=['#58a6ff'])
        fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="Top Source Bias Comparison", color="avg_score", color_continuous_scale="RdBu")
        fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECTION 3: CARDS ---
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
    st.info("No signals detected in the static data file.")

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(88, 166, 255, 0.1); text-align: center; padding: 5px; color: #58a6ff;">DATABASE SYNC: STABLE</div>', unsafe_allow_html=True)