import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import time
from urllib.parse import urlparse

st.set_page_config(page_title="BIASSENTINEL", layout="wide", initial_sidebar_state="expanded")

# ── THEME ───────────────────────────────────────────────────────────────────
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

/* base */
.main, [data-testid="stAppViewContainer"]  { background: var(--bg) !important; }
[data-testid="stSidebar"]                  { background: var(--panel) !important; border-right: 1px solid var(--border); }
html, body, p, div, span, li              { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4                            { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }

/* inputs */
.stTextInput input                         { background: var(--panel) !important; color: var(--cream) !important;
                                             border: 1px solid var(--dim) !important; border-radius: 0 !important;
                                             font-family: 'JetBrains Mono', monospace !important; }
.stSelectbox div[data-baseweb="select"]    { background: var(--panel) !important; border: 1px solid var(--dim) !important;
                                             border-radius: 0 !important; }
.stSelectbox div[data-baseweb="select"] *  { color: var(--cream) !important; font-family: 'JetBrains Mono', monospace !important; }
label, .stSelectbox label, .stTextInput label {
    color: var(--red) !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important; letter-spacing: 3px !important; text-transform: uppercase !important; }

/* buttons */
.stButton > button                         { background: transparent; color: var(--cream); border: 1px solid var(--dim);
                                             border-radius: 0; font-family: 'JetBrains Mono', monospace;
                                             font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase;
                                             width: 100%; transition: all 0.18s; }
.stButton > button:hover                   { border-color: var(--red); color: var(--cream); background: #1a0808; }

/* link buttons */
.stLinkButton a                            { border: 1px solid var(--dim) !important; border-radius: 0 !important;
                                             font-family: 'JetBrains Mono', monospace !important;
                                             font-size: 0.65rem !important; letter-spacing: 1px !important;
                                             color: var(--muted) !important; text-transform: uppercase !important; }
.stLinkButton a:hover                      { border-color: var(--dim) !important; color: var(--cream) !important; }

/* tables */
.stTable th                                { background: var(--bg) !important; color: var(--red) !important;
                                             font-family: 'JetBrains Mono', monospace !important;
                                             font-size: 0.6rem !important; letter-spacing: 3px !important;
                                             text-transform: uppercase !important; border-bottom: 1px solid var(--dim) !important; }
.stTable td                                { color: var(--cream) !important; background: var(--panel) !important;
                                             font-family: 'JetBrains Mono', monospace !important;
                                             font-size: 0.75rem !important; border-bottom: 1px solid var(--border) !important; }

/* alerts */
.stAlert                                   { background: var(--panel) !important; border: 1px solid var(--dim) !important;
                                             border-left: 2px solid var(--red) !important;
                                             color: var(--cream) !important; border-radius: 0 !important; }

/* hide branding */
#MainMenu, footer                          { visibility: hidden; }
::-webkit-scrollbar                        { width: 3px; }
::-webkit-scrollbar-thumb                  { background: var(--dim); }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────────────────────────
def get_db_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )

def extract_source(url):
    try:    return urlparse(str(url)).netloc.replace("www.", "").upper()
    except: return "UNKNOWN"

def sentiment_label(s):
    if s < -4: return "SYSTEMIC NEGATIVE"
    if s > 4:  return "SYSTEMIC POSITIVE"
    return "NEUTRAL"

def label_color(label):
    return "color:#a01a1a;" if "NEGATIVE" in label else ("color:#e0e0d1;" if "POSITIVE" in label else "color:#555;")

PLOT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#444", size=10),
    margin=dict(t=20, b=20, l=10, r=10),
)

def section(label):
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:10px; margin:1.4rem 0 0.6rem;'>
      <span style='font-size:0.6rem; color:#a01a1a; letter-spacing:4px; text-transform:uppercase; white-space:nowrap;'>{label}</span>
      <div style='flex:1; height:1px; background:#1e1e1e;'></div>
    </div>""", unsafe_allow_html=True)

def stat_card(col, label, value):
    col.markdown(f"""
    <div style='background:#111; border-top:2px solid #a01a1a; padding:14px 16px; margin-bottom:1rem;'>
      <div style='font-size:0.55rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>{label}</div>
      <div style='font-family:"Playfair Display",serif; font-size:1.6rem; color:#e0e0d1; margin-top:5px;'>{value}</div>
    </div>""", unsafe_allow_html=True)


# ── SESSION STATE ────────────────────────────────────────────────────────────
if "target" not in st.session_state:  st.session_state.target = "India"
if "tab"    not in st.session_state:  st.session_state.tab    = "dashboard"


# ── COUNTRIES ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_countries():
    try:
        conn = get_db_connection()
        raw  = pd.read_sql("SELECT DISTINCT location_name FROM news_signals", conn)["location_name"].tolist()
        conn.close()
        return sorted(set([str(l).split(",")[-1].strip() for l in raw if l and len(str(l)) > 2]))
    except:
        return ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Brazil"]

country_list = load_countries()


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # wordmark
    st.markdown("""
    <div style='text-align:center; padding:1rem 0 1.5rem;'>
      <div style='font-family:"Playfair Display",serif; font-size:1.4rem; color:#e0e0d1;
                  letter-spacing:6px; text-transform:uppercase;'>
        BIAS<span style='color:#a01a1a;'>SENTINEL</span>
      </div>
      <div style='font-size:0.55rem; color:#333; letter-spacing:4px; text-transform:uppercase; margin-top:4px;'>
        Media Intelligence v2.0
      </div>
    </div>
    <div style='height:1px; background:#1e1e1e; margin-bottom:1.5rem;'></div>
    """, unsafe_allow_html=True)

    # roulette
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:8px;'>Regional Roulette</div>", unsafe_allow_html=True)
    slot = st.empty()
    def render_slot(text, spinning=False):
        color = "#a01a1a" if spinning else "#e0e0d1"
        slot.markdown(f"""
        <div style='background:#0d0d0d; border:1px solid #1e1e1e; border-left:2px solid #a01a1a;
                    padding:14px; text-align:center; font-family:"Playfair Display",serif;
                    font-size:1.2rem; color:{color}; letter-spacing:4px;
                    text-transform:uppercase; margin-bottom:10px;'>
          {text.upper()}
        </div>""", unsafe_allow_html=True)
    render_slot(st.session_state.target)

    if st.button("SPIN TARGET"):
        for _ in range(9):
            render_slot(random.choice(country_list), spinning=True)
            time.sleep(0.07)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    chosen = st.selectbox("Select manually", country_list,
                          index=country_list.index(st.session_state.target)
                          if st.session_state.target in country_list else 0)
    if chosen != st.session_state.target:
        st.session_state.target = chosen
        st.rerun()

    # nav
    st.markdown("<div style='height:1px; background:#1e1e1e; margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:8px;'>Navigation</div>", unsafe_allow_html=True)
    if st.button("Dashboard"):
        st.session_state.tab = "dashboard"; st.rerun()
    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    if st.button("Compare Regions"):
        st.session_state.tab = "compare"; st.rerun()

    # audit
    st.markdown("<div style='height:1px; background:#1e1e1e; margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase; margin-bottom:8px;'>Bureau Audit</div>", unsafe_allow_html=True)
    if st.button("Run Bias Audit"):
        try:
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("CALL run_bias_audit();"); conn.commit(); conn.close()
            st.success("Audit complete.")
        except Exception as e:
            st.error(str(e))


# ── MASTHEAD ─────────────────────────────────────────────────────────────────
target = st.session_state.target
st.markdown(f"""
<div style='border-bottom:1px solid #1e1e1e; padding-bottom:1rem; margin-bottom:1.5rem;
            display:flex; align-items:flex-end; justify-content:space-between;'>
  <div>
    <div style='font-family:"Playfair Display",serif; font-size:2rem;
                color:#e0e0d1; letter-spacing:8px; text-transform:uppercase;'>
      BIAS<span style='color:#a01a1a;'>SENTINEL</span>
    </div>
    <div style='font-size:0.55rem; color:#333; letter-spacing:4px; text-transform:uppercase; margin-top:4px;'>
      Global Media Intelligence Engine &nbsp;·&nbsp; Neon Cloud &nbsp;·&nbsp; PL/SQL
    </div>
  </div>
  <div style='background:#a01a1a12; border:1px solid #a01a1a33; padding:6px 18px;
              font-size:0.65rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>
    Target: {target.upper()}
  </div>
</div>
""", unsafe_allow_html=True)


# ── DATA FETCH ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_signals(geo):
    try:
        conn = get_db_connection()
        df   = pd.read_sql("SELECT * FROM news_signals WHERE location_name ILIKE %s",
                           conn, params=(f"%{geo}%",))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}"); return pd.DataFrame()

filtered_df = fetch_signals(target)


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD TAB
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "dashboard":

    if filtered_df.empty:
        st.markdown("""
        <div style='background:#111; border-left:2px solid #a01a1a; padding:2rem;
                    text-align:center; font-size:0.7rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>
          No signal matches — scanning...
        </div>""", unsafe_allow_html=True)
        st.stop()

    # controls
    ctrl_l, ctrl_r = st.columns([3, 2])
    with ctrl_l:
        manual = st.text_input("Target Geography", value=target)
        if manual != target:
            st.session_state.target = manual; st.rerun()
    with ctrl_r:
        sort_order = st.selectbox("Editorial Priority", ["Most Negative First", "Most Positive First"])

    ascending = "Negative" in sort_order

    # aggregate
    df_grouped = (
        filtered_df.groupby("source_url")["sentiment_score"]
        .agg(["mean", "count"]).reset_index()
    )
    df_grouped.columns = ["source_url", "avg_score", "Articles"]
    df_grouped = df_grouped.sort_values("avg_score", ascending=ascending).head(15)
    df_grouped["CHANNEL"]  = df_grouped["source_url"].apply(extract_source)
    df_grouped["ANALYSIS"] = df_grouped["avg_score"].apply(sentiment_label)
    df_grouped["SCORE"]    = df_grouped["avg_score"].round(3)

    # ── stat strip ───────────────────────────────────────────────────────────
    section("Overview")
    s1, s2, s3, s4 = st.columns(4)
    stat_card(s1, "Total Articles",    str(len(filtered_df)))
    stat_card(s2, "Avg Sentiment",     f"{filtered_df['sentiment_score'].mean():.3f}")
    stat_card(s3, "Sources Monitored", str(filtered_df["source_url"].nunique()))
    stat_card(s4, "Most Negative",     df_grouped.iloc[0]["CHANNEL"][:14] if ascending else df_grouped.iloc[-1]["CHANNEL"][:14])

    # ── table ────────────────────────────────────────────────────────────────
    section(f"Media Landscape — {target.upper()}")
    display = df_grouped[["CHANNEL", "ANALYSIS", "SCORE", "Articles"]].copy()

    # colour-code scores inline using styled html table
    rows_html = ""
    for _, row in display.iterrows():
        s     = row["SCORE"]
        sc    = "#a01a1a" if s < -1 else ("#e0e0d1" if s > 1 else "#555")
        badge = "background:#a01a1a18; color:#a01a1a; border:1px solid #a01a1a33;" if "NEGATIVE" in row["ANALYSIS"] else \
                ("background:#e0e0d118; color:#999; border:1px solid #2a2a2a;" if "POSITIVE" in row["ANALYSIS"] else "background:#1a1a1a; color:#555; border:1px solid #222;")
        rows_html += f"""
        <tr>
          <td style='padding:9px 12px; color:#e0e0d1; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{row["CHANNEL"]}</td>
          <td style='padding:9px 12px; border-bottom:1px solid #1a1a1a;'>
            <span style='{badge} font-size:0.55rem; letter-spacing:1px; padding:3px 9px; display:inline-block;'>{row["ANALYSIS"]}</span>
          </td>
          <td style='padding:9px 12px; color:{sc}; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{s:+.3f}</td>
          <td style='padding:9px 12px; color:#444; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{row["Articles"]}</td>
        </tr>"""

    st.markdown(f"""
    <table style='width:100%; background:#111; border-collapse:collapse;'>
      <thead>
        <tr style='background:#0d0d0d;'>
          <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #a01a1a33;'>Channel</th>
          <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #a01a1a33;'>Analysis</th>
          <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #a01a1a33;'>Score</th>
          <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #a01a1a33;'>Articles</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── charts ───────────────────────────────────────────────────────────────
    section("Signal Analysis")
    ch1, ch2 = st.columns(2)

    with ch1:
        fig1 = px.histogram(filtered_df, x="sentiment_score",
                            color_discrete_sequence=["#a01a1a"], nbins=30)
        fig1.update_layout(**PLOT, title=None)
        fig1.update_traces(marker_line_width=0)
        st.plotly_chart(fig1, use_container_width=True)

    with ch2:
        top10 = df_grouped.head(10)
        colors = ["#a01a1a" if s < 0 else "#444" for s in top10["avg_score"]]
        fig2 = go.Figure(go.Bar(
            x=top10["avg_score"], y=top10["CHANNEL"],
            orientation="h", marker_color=colors, marker_line_width=0,
        ))
        fig2.update_layout(**PLOT, title=None, xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    # ── report bias ──────────────────────────────────────────────────────────
    section("Report Bias")
    rep_c, btn_c = st.columns([4, 1])
    with rep_c:
        report_ch = st.selectbox("Channel to Flag", df_grouped["CHANNEL"].tolist())
    with btn_c:
        st.markdown("<div style='margin-top:1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("Submit Flag"):
            try:
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO bias_reports (report_reason) VALUES (%s)", (f"Bias Flagged: {report_ch}",))
                conn.commit(); conn.close()
                st.toast("Signal logged.", icon="✒️")
            except Exception as e:
                st.error(str(e))

    # ── intercept cards ──────────────────────────────────────────────────────
    section("Recent Signal Intercepts")
    sample = filtered_df.sample(min(len(filtered_df), 6))
    cols   = st.columns(3)
    for i, (_, row) in enumerate(sample.iterrows()):
        score  = row["sentiment_score"]
        accent = "#a01a1a" if score < 0 else "#2a2a2a"
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:#111; border-top:2px solid {accent};
                        padding:12px 14px; margin-bottom:8px;'>
              <div style='font-size:0.58rem; color:#444; letter-spacing:2px; text-transform:uppercase;'>
                {extract_source(row["source_url"])}
              </div>
              <div style='font-family:"Playfair Display",serif; font-size:1.3rem;
                          color:{"#a01a1a" if score < 0 else "#e0e0d1"}; margin-top:6px;'>
                {score:+.2f}
              </div>
            </div>""", unsafe_allow_html=True)
            st.link_button("Read Article", str(row["source_url"]), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPARE TAB
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "compare":

    section("Cross-Regional Bias Comparison")

    ca_col, cb_col = st.columns(2)
    with ca_col: c_a = st.selectbox("Region Alpha", country_list, index=0)
    with cb_col: c_b = st.selectbox("Region Beta",  country_list, index=min(1, len(country_list) - 1))

    @st.cache_data(ttl=60)
    def fetch_avg(country):
        try:
            conn = get_db_connection()
            val  = pd.read_sql("SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s",
                               conn, params=(f"%{country}%",))["avg"].iloc[0]
            conn.close()
            return float(val) if val is not None else 0.0
        except: return 0.0

    avg_a, avg_b = fetch_avg(c_a), fetch_avg(c_b)

    m1, m2 = st.columns(2)
    for col, country, avg, color in [(m1, c_a, avg_a, "#a01a1a"), (m2, c_b, avg_b, "#e0e0d1")]:
        col.markdown(f"""
        <div style='background:#111; border-top:2px solid {color};
                    padding:2rem; text-align:center; margin-bottom:1rem;'>
          <div style='font-size:0.6rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>{country.upper()}</div>
          <div style='font-family:"Playfair Display",serif; font-size:2.8rem; color:{color}; margin-top:8px;'>{avg:+.3f}</div>
          <div style='font-size:0.55rem; color:#333; letter-spacing:2px; margin-top:6px; text-transform:uppercase;'>Avg Sentiment Score</div>
        </div>""", unsafe_allow_html=True)

    delta = avg_a - avg_b
    dc    = "#a01a1a" if delta < 0 else "#e0e0d1"
    st.markdown(f"""
    <div style='background:#0d0d0d; border:1px solid #1e1e1e; padding:1rem 2rem;
                text-align:center; margin-bottom:1.5rem;'>
      <span style='font-size:0.6rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>Delta &nbsp;</span>
      <span style='font-family:"Playfair Display",serif; font-size:1.8rem; color:{dc};'>{delta:+.3f}</span>
      <span style='font-size:0.6rem; color:#333; letter-spacing:2px;'>&nbsp; ({c_a.upper()} vs {c_b.upper()})</span>
    </div>""", unsafe_allow_html=True)

    section("Visual Comparison")
    fig = go.Figure(data=[
        go.Bar(name=c_a.upper(), x=[c_a.upper()], y=[avg_a],
               marker_color="#a01a1a", marker_line_width=0),
        go.Bar(name=c_b.upper(), x=[c_b.upper()], y=[avg_b],
               marker_color="#444",   marker_line_width=0),
    ])
    fig.update_layout(**PLOT, barmode="group",
                      legend=dict(font=dict(color="#555", size=9)),
                      xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e"))
    st.plotly_chart(fig, use_container_width=True)


# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='position:fixed; bottom:0; left:0; width:100%; background:#0d0d0d;
            border-top:1px solid #1e1e1e; padding:6px 1.5rem;
            display:flex; justify-content:space-between; align-items:center; z-index:9999;'>
  <span style='font-size:0.55rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>Biassentinel Dispatch</span>
  <span style='font-size:0.55rem; color:#2a2a2a; letter-spacing:2px; text-transform:uppercase;'>Neon Cloud &nbsp;|&nbsp; PL/SQL Enabled</span>
</div>
""", unsafe_allow_html=True)