import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from urllib.parse import urlparse

# ============================================================
# 1. PAGE CONFIG & THEME
# ============================================================
st.set_page_config(page_title="BIASSENTINEL | COMMAND", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=JetBrains+Mono:wght@300;400;700&display=swap');

:root {
    --bg:      #0d0d0d;
    --panel:   #111111;
    --border:  #1e1e1e;
    --red:     #a01a1a;
    --cream:   #e0e0d1;
    --muted:   #444444;
    --dim:     #2a2a2a;
}

.main, [data-testid="stAppViewContainer"]  { background: var(--bg) !important; }
[data-testid="stSidebar"]                  { background: var(--panel) !important; border-right: 1px solid var(--border); }
html, body, p, div, span, li              { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4                            { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }

/* inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] { 
    background: var(--panel) !important; color: var(--cream) !important;
    border: 1px solid var(--dim) !important; border-radius: 0 !important;
}
label { color: var(--red) !important; text-transform: uppercase !important; font-size: 0.65rem !important; letter-spacing: 3px !important; font-weight: bold; }

/* buttons */
.stButton > button { 
    background: transparent; color: var(--cream); border: 1px solid var(--dim); border-radius: 0; 
    text-transform: uppercase; letter-spacing: 2px; width: 100%; transition: 0.18s; 
}
.stButton > button:hover { border-color: var(--red); background: #1a0808; }

.cyber-card { border-radius: 0px; padding: 20px; background: #1a1a1a; border: 1px solid #333; height: 100%; margin-bottom: 10px; }
.legend-box { border: 1px solid #444; border-left: 10px solid #a01a1a; padding: 15px; background-color: #1a1a1a; margin-bottom: 25px; }

/* Tab Styling */
.stTabs [data-baseweb="tab-list"] { background-color: var(--panel); border-bottom: 1px solid var(--dim); }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important; letter-spacing: 2px; }
.stTabs [aria-selected="true"] { color: var(--cream) !important; border-bottom-color: var(--red) !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. HELPERS & DB UTILITIES
# ============================================================
def get_db_connection():
    return psycopg2.connect("postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")

def extract_source(url):
    try: return urlparse(str(url)).netloc.replace("www.", "").upper()
    except: return "UNKNOWN"

def stat_card(col, label, value):
    col.markdown(f"""
    <div style='background:#111; border-top:2px solid #a01a1a; padding:14px 16px; margin-bottom:1rem;'>
      <div style='font-size:0.55rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>{label}</div>
      <div style='font-family:"Playfair Display",serif; font-size:1.6rem; color:#e0e0d1; margin-top:5px;'>{value}</div>
    </div>""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_countries():
    try:
        conn = get_db_connection()
        raw = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist()
        conn.close()
        return sorted(set([str(l).split(",")[-1].strip() for l in raw if l and len(str(l)) > 2]))
    except:
        return ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Brazil"]

# ============================================================
# 3. SESSION STATE
# ============================================================
if "target" not in st.session_state: st.session_state.target = "India"

country_list = load_countries()

# ============================================================
# 4. SIDEBAR (ROULETTE & AUDIT)
# ============================================================
with st.sidebar:
    st.markdown("<h3 style='text-align:center; color:#e0e0d1;'>BIAS<span style='color:#a01a1a;'>SENTINEL</span></h3>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>Regional Roulette</div>", unsafe_allow_html=True)
    slot = st.empty()
    slot.markdown(f"<div style='background:#0d0d0d; border:1px solid #1e1e1e; border-left:2px solid #a01a1a; padding:15px; text-align:center; color:#e0e0d1; font-size:1.2rem;'>{st.session_state.target.upper()}</div>", unsafe_allow_html=True)

    if st.button("SPIN TARGET"):
        for _ in range(8):
            slot.markdown(f"<div style='background:#0d0d0d; border:1px solid #1e1e1e; border-left:2px solid #a01a1a; padding:15px; text-align:center; color:#a01a1a; font-size:1.2rem;'>{random.choice(country_list).upper()}</div>", unsafe_allow_html=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown("---")
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>Bureau Audit</div>", unsafe_allow_html=True)
    if st.button("RUN BIAS AUDIT"):
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("CALL run_bias_audit();"); conn.commit(); conn.close()
            st.success("Audit complete.")
        except Exception as e: st.error(str(e))

# ============================================================
# 5. DATA FETCH (TARGET GEOGRAPHY)
# ============================================================
conn = get_db_connection()
filtered_df = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{st.session_state.target}%",))
conn.close()

# ============================================================
# 6. MASTHEAD
# ============================================================
st.markdown(f"""
<div style='border-bottom:1px solid #1e1e1e; padding-bottom:1rem; margin-bottom:1.5rem; display:flex; align-items:flex-end; justify-content:space-between;'>
  <div>
    <div style='font-family:"Playfair Display",serif; font-size:2.2rem; color:#e0e0d1; letter-spacing:8px; text-transform:uppercase;'>BIAS<span style='color:#a01a1a;'>SENTINEL</span></div>
    <div style='font-size:0.55rem; color:#333; letter-spacing:4px; text-transform:uppercase;'>Global Media Intelligence Engine &nbsp;·&nbsp; Neon Cloud &nbsp;·&nbsp; PL/SQL</div>
  </div>
  <div style='background:#a01a1a12; border:1px solid #a01a1a33; padding:6px 18px; font-size:0.65rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>TARGET: {st.session_state.target.upper()}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 7. MAIN NAVIGATION (TABS)
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["DASHBOARD", "COMPARE", "SOURCES", "REPORTING"])

# ----------------- TAB 1: DASHBOARD -----------------
with tab1:
    if filtered_df.empty:
        st.info("No active signals found for this region.")
    else:
        # Stats
        s1, s2, s3, s4 = st.columns(4)
        stat_card(s1, "Total Articles", str(len(filtered_df)))
        stat_card(s2, "Avg Sentiment", f"{filtered_df['sentiment_score'].mean():.3f}")
        stat_card(s3, "Sources", str(filtered_df["source_url"].nunique()))
        stat_card(s4, "Status", "SYNCED")

        # Original Landscape Table
        st.markdown("### Regional Media Landscape")
        sort_order = st.selectbox("Editorial Priority", ["Most Negative First", "Most Positive First"])
        
        df_grouped = filtered_df.groupby("source_url")["sentiment_score"].agg(["mean", "count"]).reset_index()
        df_grouped.columns = ["source_url", "avg_score", "Articles"]
        df_grouped = df_grouped.sort_values("avg_score", ascending=("Negative" in sort_order)).head(15)
        df_grouped["CHANNEL"] = df_grouped["source_url"].apply(extract_source)
        
        st.table(df_grouped[['CHANNEL', 'avg_score', 'Articles']].rename(columns={'avg_score': 'Score'}))

        # Visuals
        ch1, ch2 = st.columns(2)
        with ch1:
            fig1 = px.histogram(filtered_df, x="sentiment_score", title="Sentiment Polarity Distribution", color_discrete_sequence=["#a01a1a"])
            fig1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig1, use_container_width=True)
        with ch2:
            fig2 = px.bar(df_grouped.head(10), x="avg_score", y="CHANNEL", orientation='h', title="Top Channel Bias", color_discrete_sequence=["#444"])
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

# ----------------- TAB 2: COMPARE -----------------
with tab2:
    st.subheader("Cross-Regional Disparity Analysis")
    st.markdown('<div class="legend-box">INTERNAL ADVISORY: Comparing systemic sentiment averages between two sovereign nations.</div>', unsafe_allow_html=True)
    
    ca_col, cb_col = st.columns(2)
    with ca_col: c_a = st.selectbox("Region Alpha", country_list, index=0)
    with cb_col: c_b = st.selectbox("Region Beta",  country_list, index=min(1, len(country_list) - 1))

    conn = get_db_connection()
    avg_a = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_a}%",))['avg'].iloc[0]
    avg_b = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s", conn, params=(f"%{c_b}%",))['avg'].iloc[0]
    conn.close()

    m1, m2 = st.columns(2)
    stat_card(m1, c_a.upper(), f"{avg_a if avg_a else 0.0:+.3f}")
    stat_card(m2, c_b.upper(), f"{avg_b if avg_b else 0.0:+.3f}")

# ----------------- TAB 3: SOURCES -----------------
with tab3:
    st.subheader("Active Signal Feed")
    st.dataframe(filtered_df[['actor_name', 'location_name', 'sentiment_score', 'source_url']].head(30), use_container_width=True)

# ----------------- TAB 4: REPORTING -----------------
with tab4:
    st.subheader("🚩 SIGNAL INTERCEPTION & REPORTING")
    st.markdown('<div class="legend-box">AUDIT INTERFACE: Categorize and log biased reporting patterns. This data triggers backend PL/SQL audit cycles.</div>', unsafe_allow_html=True)
    
    col_rep1, col_rep2, col_rep3 = st.columns([2, 2, 1])
    with col_rep1:
        report_channel = st.selectbox("CHANNEL TO FLAG:", filtered_df['actor_name'].unique() if not filtered_df.empty else ["No signals detected"])
    with col_rep2:
        bias_category = st.selectbox("BASIS OF REPORTING:", [
            "Inaccurate Reporting (Fake News)", "Political Favoritism", 
            "Sensationalism", "Cultural / Regional Insensitivity"
        ])
    with col_rep3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("SUBMIT FLAG"):
            try:
                conn = get_db_connection(); cur = conn.cursor()
                full_reason = f"{bias_category} flagged for {report_channel}"
                cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (full_reason,))
                conn.commit(); conn.close()
                st.toast(f"LOGGED: {report_channel} flagged for {bias_category}", icon="✒️")
            except Exception as e: st.error(f"DATABASE ERROR: Ensure 'bias_reports' table exists. Error: {e}")

    st.markdown("---")
    st.subheader("📑 RECENT SIGNAL INTERCEPTS")
    if not filtered_df.empty:
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

st.markdown('<div style="position: fixed; bottom: 0; left: 0; width: 100%; background: #000; text-align: center; padding: 5px; color: #a01a1a; font-size:0.7rem; border-top:1px solid #a01a1a;">BIASSENTINEL DISPATCH | DATABASE: NEON CLOUD | PL/SQL ENABLED</div>', unsafe_allow_html=True)