import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import random
import time
import os
from urllib.parse import urlparse

# ── CONFIG ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="BIASSENTINEL | V2.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;600;700&display=swap');

/* ── BASE ── */
html, body, [data-testid="stApp"] {
    background-color: #0a0a0a !important;
    color: #c8c8c8;
    font-family: 'Barlow', sans-serif;
}
[data-testid="stAppViewContainer"] { background-color: #0a0a0a !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #1e1e1e;
}
[data-testid="stSidebar"] * { font-family: 'Share Tech Mono', monospace !important; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem; max-width: 100%; }

/* ── HEADER ── */
.bs-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid #1e1e1e;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
}
.bs-logo { font-family: 'Share Tech Mono', monospace; letter-spacing: 0.18em; }
.bs-logo .bias { color: #e8e8e8; font-size: 2.4rem; font-weight: 700; }
.bs-logo .sentinel { color: #cc2200; font-size: 2.4rem; font-weight: 700; }
.bs-logo .sub { color: #555; font-size: 0.65rem; letter-spacing: 0.3em; margin-top: -4px; }
.bs-target-badge {
    border: 1px solid #cc2200;
    color: #cc2200;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.2em;
    padding: 0.5rem 1.2rem;
    background: transparent;
}

/* ── STAT CARDS ── */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; border-top: 2px solid #cc2200; margin-bottom: 2.5rem; }
.stat-card { border-right: 1px solid #1e1e1e; padding: 1.2rem 1.5rem; background: #0a0a0a; }
.stat-card:last-child { border-right: none; }
.stat-label { font-family: 'Share Tech Mono', monospace; font-size: 0.6rem; letter-spacing: 0.25em; color: #555; text-transform: uppercase; margin-bottom: 0.4rem; }
.stat-value { font-family: 'Share Tech Mono', monospace; font-size: 2rem; color: #e8e8e8; }

/* ── SECTION HEADERS ── */
.section-header {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.35em;
    color: #cc2200;
    text-transform: uppercase;
    border-bottom: 1px solid #1e1e1e;
    padding-bottom: 0.6rem;
    margin-bottom: 1.5rem;
    margin-top: 2rem;
}

/* ── MEDIA LANDSCAPE TABLE ── */
.ml-table { width: 100%; border-collapse: collapse; }
.ml-table th {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.25em;
    color: #555;
    text-align: left;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #1a1a1a;
}
.ml-table td { padding: 0.85rem 1rem; border-bottom: 1px solid #141414; font-size: 0.85rem; }
.ml-table tr:hover td { background: #111; }
.channel-name { font-family: 'Share Tech Mono', monospace; color: #c8c8c8; font-size: 0.82rem; letter-spacing: 0.05em; }
.badge-neg { border: 1px solid #cc2200; color: #cc2200; font-family: 'Share Tech Mono', monospace; font-size: 0.62rem; padding: 0.25rem 0.7rem; letter-spacing: 0.1em; }
.badge-neu { border: 1px solid #444; color: #888; font-family: 'Share Tech Mono', monospace; font-size: 0.62rem; padding: 0.25rem 0.7rem; letter-spacing: 0.1em; }
.badge-pos { border: 1px solid #2a6a2a; color: #4a9a4a; font-family: 'Share Tech Mono', monospace; font-size: 0.62rem; padding: 0.25rem 0.7rem; letter-spacing: 0.1em; }
.score-neg { color: #cc2200; font-family: 'Share Tech Mono', monospace; font-weight: 700; }
.score-pos { color: #4a9a4a; font-family: 'Share Tech Mono', monospace; font-weight: 700; }
.score-neu { color: #888; font-family: 'Share Tech Mono', monospace; font-weight: 700; }
.articles-col { color: #888; font-family: 'Share Tech Mono', monospace; font-size: 0.8rem; }

/* ── SIGNAL INTERCEPTS ── */
.intercept-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: #1a1a1a; margin-top: 1rem; }
.intercept-card { background: #0a0a0a; padding: 1.5rem; }
.intercept-source { font-family: 'Share Tech Mono', monospace; font-size: 0.62rem; letter-spacing: 0.2em; color: #555; text-transform: uppercase; margin-bottom: 0.6rem; }
.intercept-score-neg { font-family: 'Share Tech Mono', monospace; font-size: 2rem; color: #cc2200; }
.intercept-score-pos { font-family: 'Share Tech Mono', monospace; font-size: 2rem; color: #4a9a4a; }
.intercept-score-neu { font-family: 'Share Tech Mono', monospace; font-size: 2rem; color: #888; }

/* ── FOOTER ── */
.bs-footer {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    color: #333;
    border-top: 1px solid #1a1a1a;
    padding-top: 1rem;
    margin-top: 3rem;
    display: flex;
    justify-content: space-between;
}

/* ── SIDEBAR STYLE ── */
.sidebar-logo { color: #cc2200; font-size: 0.9rem; letter-spacing: 0.2em; font-weight: 700; margin-bottom: 1.5rem; }
.sidebar-label { font-size: 0.6rem; letter-spacing: 0.2em; color: #555; text-transform: uppercase; margin-bottom: 0.3rem; }
.sidebar-target { color: #e8e8e8; font-size: 1rem; letter-spacing: 0.05em; margin-bottom: 1.5rem; border-bottom: 1px solid #1e1e1e; padding-bottom: 1rem; }

/* Streamlit overrides */
.stTextInput > div > div > input {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    color: #c8c8c8 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
    border-radius: 0 !important;
}
.stButton > button {
    background: transparent !important;
    border: 1px solid #cc2200 !important;
    color: #cc2200 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em !important;
    border-radius: 0 !important;
    width: 100% !important;
    padding: 0.5rem !important;
}
.stButton > button:hover {
    background: #cc2200 !important;
    color: #fff !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 0 !important;
    color: #c8c8c8 !important;
}
.stPlotlyChart { border: 1px solid #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# ── DB CONNECTION ────────────────────────────────────────────────────────────
DATABASE_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"DB CONNECTION ERROR: {e}")
        return None

def run_query(query, params=None):
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        conn.rollback()
        if params:
            return pd.read_sql(query, conn, params=params)
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"QUERY ERROR: {e}")
        return pd.DataFrame()

def extract_source(url):
    try:
        netloc = urlparse(str(url)).netloc.replace("www.", "").upper()
        return netloc if netloc else str(url).upper()[:20]
    except:
        return "UNKNOWN"

def get_badge(score):
    if score <= -4:
        return '<span class="badge-neg">Systemic Negative</span>'
    elif score >= 4:
        return '<span class="badge-pos">Systemic Positive</span>'
    else:
        return '<span class="badge-neu">Neutral</span>'

def get_score_class(score):
    if score < 0: return "score-neg"
    if score > 0: return "score-pos"
    return "score-neu"

def get_intercept_class(score):
    if score < 0: return "intercept-score-neg"
    if score > 0: return "intercept-score-pos"
    return "intercept-score-neu"

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "target" not in st.session_state:
    st.session_state.target = "India"

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">BIASSENTINEL</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("📊 DASHBOARD"):
            st.session_state.view = "dashboard"
    with col2:
        if st.button("⚔ COMPARE"):
            st.session_state.view = "compare"

    st.markdown("---")
    st.markdown('<div class="sidebar-label">ROULETTE</div>', unsafe_allow_html=True)

    # Get country list
    countries_df = run_query("SELECT DISTINCT location_name FROM news_signals WHERE location_name IS NOT NULL LIMIT 100")
    if not countries_df.empty:
        country_list = countries_df["location_name"].dropna().tolist()
    else:
        country_list = ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Brazil"]

    roulette_placeholder = st.empty()
    roulette_placeholder.markdown(
        f'<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.85rem; color:#e8e8e8; padding: 0.5rem 0;">SPIN TARGET</div>'
        f'<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.75rem; color:#555;">Current: <span style="color:#c8c8c8">{st.session_state.target.upper()}</span></div>',
        unsafe_allow_html=True
    )

    if st.button("⟳ SPIN TARGET"):
        for _ in range(10):
            tmp = random.choice(country_list)
            roulette_placeholder.markdown(
                f'<div style="font-family:\'Share Tech Mono\',monospace; color:#cc2200; font-size:1rem; padding: 0.5rem 0;">{tmp.upper()}</div>',
                unsafe_allow_html=True
            )
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown("---")
    target_input = st.text_input("TARGET COUNTRY", value=st.session_state.target, label_visibility="collapsed")
    if target_input:
        st.session_state.target = target_input

target = st.session_state.target

# ── QUERIES ──────────────────────────────────────────────────────────────────
total_df = run_query(
    "SELECT COUNT(*) as cnt, AVG(sentiment_score) as avg_s, COUNT(DISTINCT actor_name) as srcs FROM news_signals WHERE location_name ILIKE %s",
    (f"%{target}%",)
)
total_articles = int(total_df["cnt"].iloc[0]) if not total_df.empty else 0
avg_sentiment  = float(total_df["avg_s"].iloc[0]) if not total_df.empty and total_df["avg_s"].iloc[0] is not None else 0.0
total_sources  = int(total_df["srcs"].iloc[0]) if not total_df.empty else 0

# Flagged bias = sources with score < -4
flagged_df = run_query(
    "SELECT COUNT(DISTINCT actor_name) as flagged FROM news_signals WHERE location_name ILIKE %s AND sentiment_score < -4",
    (f"%{target}%",)
)
flagged_bias = int(flagged_df["flagged"].iloc[0]) if not flagged_df.empty else 0

# Media landscape
landscape_df = run_query(
    """SELECT actor_name, AVG(sentiment_score) as avg_score, COUNT(*) as articles
       FROM news_signals WHERE location_name ILIKE %s
       GROUP BY actor_name ORDER BY avg_score ASC LIMIT 10""",
    (f"%{target}%",)
)

# Sentiment distribution (histogram buckets)
dist_df = run_query(
    "SELECT sentiment_score FROM news_signals WHERE location_name ILIKE %s AND sentiment_score IS NOT NULL LIMIT 2000",
    (f"%{target}%",)
)

# Signal intercepts (latest 6 unique sources)
intercepts_df = run_query(
    """SELECT DISTINCT ON (actor_name) actor_name, sentiment_score, source_url
       FROM news_signals WHERE location_name ILIKE %s AND actor_name IS NOT NULL
       ORDER BY actor_name, published_at DESC LIMIT 6""",
    (f"%{target}%",)
)

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bs-header">
  <div class="bs-logo">
    <div><span class="bias">BIAS</span><span class="sentinel">SENTINEL</span></div>
    <div class="sub">GLOBAL MEDIA INTELLIGENCE ENGINE &nbsp;|&nbsp; V2.0</div>
  </div>
  <div class="bs-target-badge">TARGET: {target.upper()}</div>
</div>
""", unsafe_allow_html=True)

# ── STATS ────────────────────────────────────────────────────────────────────
avg_fmt = f"{avg_sentiment:+.2f}" if avg_sentiment != 0 else "0.00"
st.markdown(f"""
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-label">Total Articles</div>
    <div class="stat-value">{total_articles:,}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Avg Sentiment</div>
    <div class="stat-value">{avg_fmt}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Sources</div>
    <div class="stat-value">{total_sources}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Flagged Bias</div>
    <div class="stat-value">{flagged_bias}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── MEDIA LANDSCAPE ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">MEDIA LANDSCAPE</div>', unsafe_allow_html=True)

if not landscape_df.empty:
    rows_html = ""
    for _, row in landscape_df.iterrows():
        src    = extract_source(str(row["actor_name"])) if row["actor_name"] else "UNKNOWN"
        score  = float(row["avg_score"]) if row["avg_score"] is not None else 0.0
        arts   = int(row["articles"])
        badge  = get_badge(score)
        scls   = get_score_class(score)
        sfmt   = f"{score:+.2f}" if score != 0 else "0.00"
        rows_html += f"""
        <tr>
          <td><span class="channel-name">{src}</span></td>
          <td>{badge}</td>
          <td><span class="{scls}">{sfmt}</span></td>
          <td><span class="articles-col">{arts}</span></td>
        </tr>"""
    st.markdown(f"""
    <table class="ml-table">
      <thead>
        <tr>
          <th>CHANNEL</th>
          <th>ANALYSIS</th>
          <th>SCORE</th>
          <th>ARTICLES</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#555; font-family:\'Share Tech Mono\',monospace; font-size:0.8rem;">NO SIGNALS DETECTED FOR THIS TARGET</p>', unsafe_allow_html=True)

# ── CHARTS ROW ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header" style="margin-top:2.5rem;">SIGNAL ANALYTICS</div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)

# Sentiment Distribution
with col_left:
    st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.7rem; letter-spacing:0.2em; color:#888; margin-bottom:0.8rem;">SENTIMENT DISTRIBUTION</div>', unsafe_allow_html=True)
    if not dist_df.empty:
        scores = dist_df["sentiment_score"].dropna().tolist()
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=scores,
            nbinsx=20,
            marker_color=["#cc2200" if s < 0 else "#333" for s in scores],
            marker_line_width=0,
        ))
        # Red for negative half, dark for positive
        fig.add_trace(go.Histogram(
            x=[s for s in scores if s < 0],
            nbinsx=20,
            marker_color="#cc2200",
            showlegend=False
        ))
        fig.add_trace(go.Histogram(
            x=[s for s in scores if s >= 0],
            nbinsx=20,
            marker_color="#2a2a2a",
            showlegend=False
        ))
        fig.data = fig.data[1:]  # remove first combined trace
        fig.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#0a0a0a",
            font=dict(family="Share Tech Mono", color="#555", size=10),
            margin=dict(l=30, r=10, t=10, b=30),
            xaxis=dict(
                title="POLARITY",
                title_font=dict(size=9, color="#555"),
                gridcolor="#141414",
                tickfont=dict(size=9),
                range=[-10, 10],
                zeroline=True,
                zerolinecolor="#333",
                zerolinewidth=1,
            ),
            yaxis=dict(gridcolor="#141414", tickfont=dict(size=9)),
            showlegend=False,
            height=250,
            barmode="overlay",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<p style="color:#555; font-size:0.8rem; font-family:\'Share Tech Mono\',monospace;">NO DATA</p>', unsafe_allow_html=True)

# Source Bias Ranking
with col_right:
    st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.7rem; letter-spacing:0.2em; color:#888; margin-bottom:0.8rem;">SOURCE BIAS RANKING</div>', unsafe_allow_html=True)
    if not landscape_df.empty:
        df_plot = landscape_df.head(7).copy()
        df_plot["source"] = df_plot["actor_name"].apply(lambda x: extract_source(str(x)))
        df_plot["avg_score"] = df_plot["avg_score"].astype(float)
        df_plot = df_plot.sort_values("avg_score")

        bar_colors = ["#cc2200" if s < 0 else "#2a6a2a" for s in df_plot["avg_score"]]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_plot["avg_score"],
            y=df_plot["source"],
            orientation="h",
            marker_color=bar_colors,
            marker_line_width=0,
            text=[f"{s:+.1f}" for s in df_plot["avg_score"]],
            textposition="outside",
            textfont=dict(family="Share Tech Mono", size=9, color="#888"),
        ))
        fig2.update_layout(
            paper_bgcolor="#0a0a0a",
            plot_bgcolor="#0a0a0a",
            font=dict(family="Share Tech Mono", color="#555", size=10),
            margin=dict(l=80, r=60, t=10, b=10),
            xaxis=dict(
                gridcolor="#141414",
                tickfont=dict(size=9),
                zeroline=True, zerolinecolor="#333", zerolinewidth=1,
            ),
            yaxis=dict(tickfont=dict(size=9), gridcolor="#0a0a0a"),
            showlegend=False,
            height=250,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown('<p style="color:#555; font-size:0.8rem; font-family:\'Share Tech Mono\',monospace;">NO DATA</p>', unsafe_allow_html=True)

# ── SIGNAL INTERCEPTS ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header" style="margin-top:2rem;">SIGNAL INTERCEPTS</div>', unsafe_allow_html=True)

if not intercepts_df.empty:
    cards_html = ""
    for _, row in intercepts_df.iterrows():
        src   = extract_source(str(row.get("actor_name", ""))) if row.get("actor_name") else "UNKNOWN"
        score = float(row["sentiment_score"]) if row["sentiment_score"] is not None else 0.0
        sfmt  = f"{score:+.2f}"
        icls  = get_intercept_class(score)
        cards_html += f"""
        <div class="intercept-card">
          <div class="intercept-source">{src}</div>
          <div class="{icls}">{sfmt}</div>
        </div>"""
    # Pad to 6 if fewer
    while cards_html.count('intercept-card') < 6:
        cards_html += '<div class="intercept-card"></div>'
    st.markdown(f'<div class="intercept-grid">{cards_html}</div>', unsafe_allow_html=True)
else:
    st.markdown('<p style="color:#555; font-family:\'Share Tech Mono\',monospace; font-size:0.8rem;">NO INTERCEPTS AVAILABLE</p>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="bs-footer">
  <span>BIASSENTINEL DISPATCH</span>
  <span>DATABASE: NEON CLOUD &nbsp;|&nbsp; PL/SQL ENABLED</span>
</div>
""", unsafe_allow_html=True)
