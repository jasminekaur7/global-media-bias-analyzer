import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from urllib.parse import urlparse

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BIASSENTINEL",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL THEME INJECTION
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=JetBrains+Mono:wght@300;400;700&display=swap');

/* ── Reset & Root ── */
:root {
    --bg:        #0d0d0d;
    --surface:   #141414;
    --surface2:  #1c1c1c;
    --border:    #2a2a2a;
    --red:       #a01a1a;
    --red-glow:  rgba(160,26,26,0.35);
    --cream:     #e0e0d1;
    --muted:     #555;
    --mono:      'JetBrains Mono', monospace;
    --serif:     'Playfair Display', serif;
}

/* backgrounds */
.main, [data-testid="stAppViewContainer"]           { background: var(--bg) !important; }
[data-testid="stSidebar"]                           { background: var(--surface) !important; border-right: 1px solid var(--red); }
section[data-testid="stSidebar"] > div              { padding-top: 2rem; }

/* global text */
html, body, .main, p, span, div, label, .stMarkdown { color: var(--cream); font-family: var(--mono); }

/* all headings */
h1, h2, h3, h4                                      { font-family: var(--serif); color: var(--cream); letter-spacing: 2px; }

/* inputs */
input, textarea,
.stTextInput input                                  { background: var(--surface2) !important; color: var(--cream) !important;
                                                      border: 1px solid var(--border) !important; border-radius: 0 !important;
                                                      font-family: var(--mono) !important; }
.stSelectbox div[data-baseweb="select"]             { background: var(--surface2) !important; border-radius: 0 !important;
                                                      border: 1px solid var(--border) !important; }
.stSelectbox div[data-baseweb="select"] *           { color: var(--cream) !important; font-family: var(--mono) !important; }

/* labels */
label, .stSelectbox label, .stTextInput label       { color: var(--red) !important; font-family: var(--mono) !important;
                                                      font-size: 0.7rem !important; letter-spacing: 2px !important;
                                                      text-transform: uppercase !important; }

/* buttons */
.stButton > button                                  { background: transparent; color: var(--cream); border: 1px solid var(--red);
                                                      border-radius: 0; font-family: var(--mono); font-size: 0.75rem;
                                                      letter-spacing: 2px; text-transform: uppercase; width: 100%;
                                                      transition: all 0.2s; }
.stButton > button:hover                            { background: var(--red); color: #fff; box-shadow: 0 0 14px var(--red-glow); }

/* link buttons */
.stLinkButton a                                     { border: 1px solid var(--border) !important; border-radius: 0 !important;
                                                      font-family: var(--mono) !important; font-size: 0.7rem !important;
                                                      letter-spacing: 1px !important; color: var(--muted) !important;
                                                      text-transform: uppercase !important; }
.stLinkButton a:hover                               { border-color: var(--red) !important; color: var(--cream) !important; }

/* tables */
.stTable, .stDataFrame                              { background: var(--surface2) !important; }
.stTable th                                         { background: #000 !important; color: var(--red) !important;
                                                      font-family: var(--mono) !important; font-size: 0.7rem !important;
                                                      letter-spacing: 2px !important; text-transform: uppercase !important; border-bottom: 1px solid var(--red) !important; }
.stTable td                                         { color: var(--cream) !important; font-family: var(--mono) !important;
                                                      font-size: 0.8rem !important; border-bottom: 1px solid var(--border) !important; }

/* info/toast */
.stAlert                                            { background: var(--surface2) !important; border: 1px solid var(--border) !important;
                                                      border-left: 4px solid var(--red) !important; color: var(--cream) !important; border-radius: 0 !important; }

/* scrollbar */
::-webkit-scrollbar                                 { width: 4px; }
::-webkit-scrollbar-track                           { background: var(--bg); }
::-webkit-scrollbar-thumb                           { background: var(--red); }

/* plotly toolbar */
.modebar                                            { background: transparent !important; }

/* hide streamlit branding */
#MainMenu, footer                                   { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )

def extract_source(url):
    try:
        return urlparse(str(url)).netloc.replace("www.", "").upper()
    except:
        return "UNKNOWN"

def sentiment_label(s):
    if s < -4:  return "🛑 SYSTEMIC NEGATIVE"
    if s > 4:   return "✨ SYSTEMIC POSITIVE"
    return "⚖️ NEUTRAL"

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#e0e0d1", size=11),
    margin=dict(t=40, b=20, l=10, r=10),
)


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "target" not in st.session_state:
    st.session_state.target = "India"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "dashboard"


# ─────────────────────────────────────────────
#  LOAD COUNTRIES (for roulette + compare)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_countries():
    try:
        conn = get_db_connection()
        raw = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist()
        conn.close()
        return sorted(set([str(l).split(",")[-1].strip() for l in raw if l and len(str(l)) > 2]))
    except:
        return ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Brazil"]

country_list = load_countries()


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:

    # ── Wordmark ──────────────────────────────
    st.markdown("""
    <div style='text-align:center; margin-bottom:2rem;'>
      <div style='font-family:"Playfair Display",serif; font-size:1.6rem;
                  color:#e0e0d1; letter-spacing:6px; text-transform:uppercase;'>
        BIAS<span style='color:#a01a1a;'>SENTINEL</span>
      </div>
      <div style='font-family:"JetBrains Mono",monospace; font-size:0.6rem;
                  color:#555; letter-spacing:4px; margin-top:4px;'>
        MEDIA INTELLIGENCE ENGINE v2.0
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Divider ───────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #2a2a2a; margin:0 0 1.5rem;'>", unsafe_allow_html=True)

    # ── Roulette ──────────────────────────────
    st.markdown("""
    <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:0.6rem;'>
        ◈ Regional Roulette
    </div>
    """, unsafe_allow_html=True)

    roulette_slot = st.empty()
    roulette_slot.markdown(f"""
    <div style='background:#000; border:1px solid #a01a1a; padding:14px 10px;
                text-align:center; font-family:"Playfair Display",serif;
                font-size:1.3rem; color:#e0e0d1; letter-spacing:3px;
                text-transform:uppercase; box-shadow:0 0 12px rgba(160,26,26,0.3);
                margin-bottom:0.8rem;'>
        {st.session_state.target.upper()}
    </div>
    """, unsafe_allow_html=True)

    if st.button("⟳  SPIN TARGET"):
        for _ in range(9):
            tmp = random.choice(country_list)
            roulette_slot.markdown(f"""
            <div style='background:#000; border:1px solid #a01a1a; padding:14px 10px;
                        text-align:center; font-family:"Playfair Display",serif;
                        font-size:1.3rem; color:#a01a1a; letter-spacing:3px;
                        text-transform:uppercase; box-shadow:0 0 12px rgba(160,26,26,0.3);
                        margin-bottom:0.8rem;'>
                {tmp.upper()}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.07)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    # ── Country Selector ──────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    chosen = st.selectbox(
        "SELECT TARGET MANUALLY",
        options=country_list,
        index=country_list.index(st.session_state.target) if st.session_state.target in country_list else 0,
    )
    if chosen != st.session_state.target:
        st.session_state.target = chosen
        st.rerun()

    # ── Divider ───────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #2a2a2a; margin:1.5rem 0;'>", unsafe_allow_html=True)

    # ── Navigation (Compare only) ─────────────
    st.markdown("""
    <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:0.6rem;'>
        ◈ Navigation
    </div>
    """, unsafe_allow_html=True)

    if st.button("DASHBOARD"):
        st.session_state.active_tab = "dashboard"
        st.rerun()
    st.markdown("<div style='margin-top:0.4rem;'></div>", unsafe_allow_html=True)
    if st.button("⚔  COMPARE REGIONS"):
        st.session_state.active_tab = "compare"
        st.rerun()

    # ── Audit ─────────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #2a2a2a; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:0.6rem;'>
        ◈ Bureau Audit
    </div>
    """, unsafe_allow_html=True)
    if st.button("RUN BIAS AUDIT"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("CALL run_bias_audit();")
            conn.commit()
            conn.close()
            st.success("Audit complete.")
        except Exception as e:
            st.error(f"Audit failed: {e}")


# ─────────────────────────────────────────────
#  MASTHEAD
# ─────────────────────────────────────────────
target = st.session_state.target

st.markdown(f"""
<div style='border-bottom:1px solid #2a2a2a; padding-bottom:1.2rem; margin-bottom:2rem;'>
  <div style='display:flex; align-items:baseline; gap:1rem;'>
    <span style='font-family:"Playfair Display",serif; font-size:0.85rem;
                 color:#a01a1a; letter-spacing:4px; text-transform:uppercase;'>
      ACTIVE TARGET ›
    </span>
    <span style='font-family:"Playfair Display",serif; font-size:2.2rem;
                 color:#e0e0d1; letter-spacing:6px; text-transform:uppercase;'>
      {target.upper()}
    </span>
  </div>
  <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
               color:#555; letter-spacing:3px; margin-top:4px;'>
    GLOBAL MEDIA INTELLIGENCE ENGINE &nbsp;|&nbsp; DATABASE: NEON CLOUD &nbsp;|&nbsp; PL/SQL ENABLED
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_signals(geography: str):
    try:
        conn = get_db_connection()
        df = pd.read_sql(
            "SELECT * FROM news_signals WHERE location_name ILIKE %s",
            conn, params=(f"%{geography}%",)
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

filtered_df = fetch_signals(target)


# ═══════════════════════════════════════════════════
#  TAB: DASHBOARD
# ═══════════════════════════════════════════════════
if st.session_state.active_tab == "dashboard":

    if filtered_df.empty:
        st.markdown("""
        <div style='background:#141414; border:1px solid #2a2a2a; border-left:4px solid #a01a1a;
                    padding:2rem; text-align:center; font-family:"JetBrains Mono",monospace;
                    color:#555; letter-spacing:2px; font-size:0.8rem; text-transform:uppercase;'>
            NO SIGNAL MATCHES DETECTED — SCANNING...
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Controls row ────────────────────────────────
    ctrl_l, ctrl_r = st.columns([3, 2])
    with ctrl_l:
        manual_target = st.text_input("TARGET GEOGRAPHY:", value=target)
        if manual_target != target:
            st.session_state.target = manual_target
            st.rerun()
    with ctrl_r:
        sort_order = st.selectbox(
            "EDITORIAL PRIORITY:",
            ["Most Negative First", "Most Positive First"]
        )

    ascending = "Negative" in sort_order

    # ── Aggregate ────────────────────────────────────
    df_grouped = (
        filtered_df
        .groupby("source_url")["sentiment_score"]
        .agg(["mean", "count"])
        .reset_index()
    )
    df_grouped.columns = ["source_url", "avg_score", "Articles"]
    df_grouped = df_grouped.sort_values("avg_score", ascending=ascending).head(15)
    df_grouped["CHANNEL"]  = df_grouped["source_url"].apply(extract_source)
    df_grouped["ANALYSIS"] = df_grouped["avg_score"].apply(sentiment_label)
    df_grouped["SCORE"]    = df_grouped["avg_score"].round(3)

    # ── Stat strip ───────────────────────────────────
    total_arts   = len(filtered_df)
    avg_global   = filtered_df["sentiment_score"].mean()
    most_neg     = df_grouped.iloc[0]["CHANNEL"] if ascending else df_grouped.iloc[-1]["CHANNEL"]
    unique_srcs  = filtered_df["source_url"].nunique()

    s1, s2, s3, s4 = st.columns(4)
    for col, label, value in [
        (s1, "TOTAL ARTICLES",    str(total_arts)),
        (s2, "AVG SENTIMENT",     f"{avg_global:.3f}"),
        (s3, "SOURCES MONITORED", str(unique_srcs)),
        (s4, "MOST NEGATIVE SRC", most_neg[:18]),
    ]:
        col.markdown(f"""
        <div style='background:#141414; border:1px solid #2a2a2a; border-top:3px solid #a01a1a;
                    padding:1.2rem; text-align:center; margin-bottom:1.5rem;'>
          <div style='font-family:"JetBrains Mono",monospace; font-size:0.6rem;
                      color:#555; letter-spacing:3px; text-transform:uppercase;'>{label}</div>
          <div style='font-family:"Playfair Display",serif; font-size:1.6rem;
                      color:#e0e0d1; margin-top:6px; letter-spacing:1px;'>{value}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Media landscape table ─────────────────────────
    st.markdown(f"""
    <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem; color:#a01a1a;
                letter-spacing:3px; text-transform:uppercase; margin-bottom:0.5rem;'>
        ◈ Media Landscape — {target.upper()}
    </div>
    """, unsafe_allow_html=True)

    display_table = df_grouped[["CHANNEL", "ANALYSIS", "SCORE", "Articles"]].copy()
    st.table(display_table)

    # ── Charts ────────────────────────────────────────
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("""<div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                        color:#a01a1a; letter-spacing:3px; text-transform:uppercase;
                        margin-bottom:0.4rem;'>◈ Sentiment Polarity Distribution</div>""",
                    unsafe_allow_html=True)
        fig_hist = px.histogram(
            filtered_df, x="sentiment_score",
            color_discrete_sequence=["#a01a1a"],
            nbins=30,
        )
        fig_hist.update_layout(**PLOTLY_LAYOUT)
        fig_hist.update_traces(marker_line_color="#0d0d0d", marker_line_width=0.5)
        st.plotly_chart(fig_hist, use_container_width=True)

    with ch2:
        st.markdown("""<div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                        color:#a01a1a; letter-spacing:3px; text-transform:uppercase;
                        margin-bottom:0.4rem;'>◈ Source Bias Ranking</div>""",
                    unsafe_allow_html=True)
        fig_bar = px.bar(
            df_grouped.head(10),
            x="avg_score", y="CHANNEL",
            orientation="h",
            color="avg_score",
            color_continuous_scale=["#a01a1a", "#3a3a3a", "#e0e0d1"],
        )
        fig_bar.update_layout(**PLOTLY_LAYOUT, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Report Bias ───────────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #2a2a2a; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                    color:#a01a1a; letter-spacing:3px; text-transform:uppercase;
                    margin-bottom:0.6rem;'>◈ Report Bias</div>""", unsafe_allow_html=True)

    rep_col, btn_col = st.columns([4, 1])
    with rep_col:
        report_channel = st.selectbox("CHANNEL TO FLAG:", df_grouped["CHANNEL"].tolist())
    with btn_col:
        st.markdown("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
        if st.button("SUBMIT FLAG"):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO bias_reports (report_reason) VALUES (%s)",
                    (f"Bias Flagged: {report_channel}",)
                )
                conn.commit()
                conn.close()
                st.toast("Signal logged.", icon="✒️")
            except Exception as e:
                st.error(f"Failed: {e}")

    # ── Signal Intercepts ─────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #2a2a2a; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("""<div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                    color:#a01a1a; letter-spacing:3px; text-transform:uppercase;
                    margin-bottom:1rem;'>◈ Recent Signal Intercepts</div>""", unsafe_allow_html=True)

    sample_df = filtered_df.sample(min(len(filtered_df), 6))
    cols = st.columns(3)
    for i, (_, row) in enumerate(sample_df.iterrows()):
        score  = row["sentiment_score"]
        accent = "#a01a1a" if score < 0 else "#e0e0d1"
        src    = extract_source(row["source_url"])
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:#141414; border:1px solid #2a2a2a;
                        border-top:3px solid {accent}; padding:1rem;
                        margin-bottom:0.6rem;'>
              <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                          color:#555; letter-spacing:2px; text-transform:uppercase;'>
                  📡 {src}
              </div>
              <div style='font-family:"Playfair Display",serif; font-size:1.4rem;
                          color:{accent}; margin-top:6px;'>
                  {score:+.2f}
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("↗ READ ARTICLE", str(row["source_url"]), use_container_width=True)


# ═══════════════════════════════════════════════════
#  TAB: COMPARE
# ═══════════════════════════════════════════════════
elif st.session_state.active_tab == "compare":

    st.markdown("""
    <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem; color:#a01a1a;
                letter-spacing:3px; text-transform:uppercase; margin-bottom:1.5rem;'>
        ◈ Cross-Regional Bias Comparison
    </div>
    """, unsafe_allow_html=True)

    ca_col, cb_col = st.columns(2)
    with ca_col:
        c_a = st.selectbox("REGION ALPHA:", country_list, index=0)
    with cb_col:
        c_b = st.selectbox("REGION BETA:", country_list, index=min(1, len(country_list) - 1))

    @st.cache_data(ttl=60)
    def fetch_avg(country):
        try:
            conn = get_db_connection()
            val = pd.read_sql(
                "SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s",
                conn, params=(f"%{country}%",)
            )["avg"].iloc[0]
            conn.close()
            return float(val) if val is not None else 0.0
        except:
            return 0.0

    avg_a = fetch_avg(c_a)
    avg_b = fetch_avg(c_b)

    # ── Score cards ───────────────────────────────────
    m1, m2 = st.columns(2)
    for col, country, avg, color in [
        (m1, c_a, avg_a, "#a01a1a"),
        (m2, c_b, avg_b, "#e0e0d1"),
    ]:
        col.markdown(f"""
        <div style='background:#141414; border:1px solid #2a2a2a; border-top:4px solid {color};
                    padding:2rem; text-align:center; margin-bottom:1.5rem;'>
          <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                      color:#555; letter-spacing:3px; text-transform:uppercase;'>{country.upper()}</div>
          <div style='font-family:"Playfair Display",serif; font-size:3rem;
                      color:{color}; margin-top:0.5rem;'>{avg:+.3f}</div>
          <div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                      color:#555; letter-spacing:2px; margin-top:0.5rem;'>AVG SENTIMENT SCORE</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Delta ─────────────────────────────────────────
    delta = avg_a - avg_b
    delta_color = "#a01a1a" if delta < 0 else "#e0e0d1"
    st.markdown(f"""
    <div style='background:#000; border:1px solid #2a2a2a; padding:1rem 2rem;
                text-align:center; margin-bottom:1.5rem;'>
      <span style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                   color:#555; letter-spacing:3px; text-transform:uppercase;'>DELTA &nbsp;</span>
      <span style='font-family:"Playfair Display",serif; font-size:1.8rem; color:{delta_color};'>
          {delta:+.3f}
      </span>
      <span style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                   color:#555; letter-spacing:2px;'>&nbsp; ({c_a.upper()} vs {c_b.upper()})</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Radar / bar comparison ────────────────────────
    st.markdown("""<div style='font-family:"JetBrains Mono",monospace; font-size:0.65rem;
                    color:#a01a1a; letter-spacing:3px; text-transform:uppercase;
                    margin-bottom:0.4rem;'>◈ Visual Comparison</div>""", unsafe_allow_html=True)

    fig_comp = go.Figure(data=[
        go.Bar(name=c_a.upper(), x=[c_a.upper()], y=[avg_a],
               marker_color="#a01a1a", marker_line_color="#0d0d0d", marker_line_width=1),
        go.Bar(name=c_b.upper(), x=[c_b.upper()], y=[avg_b],
               marker_color="#e0e0d1", marker_line_color="#0d0d0d", marker_line_width=1),
    ])
    fig_comp.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        showlegend=True,
        legend=dict(font=dict(color="#e0e0d1", size=10)),
    )
    st.plotly_chart(fig_comp, use_container_width=True)


# ─────────────────────────────────────────────
#  FIXED FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div style='position:fixed; bottom:0; left:0; width:100%;
            background:#000; border-top:1px solid #2a2a2a;
            padding:6px 1.5rem; display:flex; justify-content:space-between;
            align-items:center; z-index:9999;'>
  <span style='font-family:"JetBrains Mono",monospace; font-size:0.6rem;
               color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>
    BIASSENTINEL DISPATCH
  </span>
  <span style='font-family:"JetBrains Mono",monospace; font-size:0.6rem;
               color:#333; letter-spacing:2px; text-transform:uppercase;'>
    DATABASE: NEON CLOUD &nbsp;|&nbsp; PL/SQL ENABLED
  </span>
</div>
""", unsafe_allow_html=True)