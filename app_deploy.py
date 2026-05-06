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
st.set_page_config(
    page_title="BIASSENTINEL | COMMAND",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=JetBrains+Mono:wght@300;400;700&display=swap');

:root {
    --bg:    #0d0d0d;
    --panel: #111111;
    --border:#1e1e1e;
    --red:   #a01a1a;
    --cream: #e0e0d1;
    --muted: #444444;
    --dim:   #2a2a2a;
}

.main, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebar"]                 { background: var(--panel) !important; border-right: 1px solid var(--border); }
html, body, p, div, span, li             { color: var(--cream); font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, h4                           { font-family: 'Playfair Display', serif; color: var(--cream); letter-spacing: 2px; }

.stTextInput input                        { background: var(--panel) !important; color: var(--cream) !important;
                                            border: 1px solid var(--dim) !important; border-radius: 0 !important; }
.stSelectbox div[data-baseweb="select"]   { background: var(--panel) !important; color: var(--cream) !important;
                                            border: 1px solid var(--dim) !important; border-radius: 0 !important; }
.stSelectbox div[data-baseweb="select"] * { color: var(--cream) !important; font-family: 'JetBrains Mono', monospace !important; }

label { color: var(--red) !important; text-transform: uppercase !important;
        font-size: 0.65rem !important; letter-spacing: 3px !important; font-weight: bold; }

.stButton > button { background: transparent; color: var(--cream); border: 1px solid var(--dim);
                     border-radius: 0; text-transform: uppercase; letter-spacing: 2px;
                     width: 100%; transition: 0.18s; font-family: 'JetBrains Mono', monospace; }
.stButton > button:hover { border-color: var(--red); background: #1a0808; }

.stLinkButton a { border: 1px solid var(--dim) !important; border-radius: 0 !important;
                  font-family: 'JetBrains Mono', monospace !important; font-size: 0.65rem !important;
                  color: var(--muted) !important; text-transform: uppercase !important; letter-spacing: 1px !important; }
.stLinkButton a:hover { border-color: var(--red) !important; color: var(--cream) !important; }

.stTabs [data-baseweb="tab-list"]  { background-color: var(--panel); border-bottom: 1px solid var(--dim); gap: 0; }
.stTabs [data-baseweb="tab"]       { color: var(--muted) !important; font-family: 'JetBrains Mono', monospace !important;
                                     letter-spacing: 2px; font-size: 0.72rem !important; border-radius: 0 !important;
                                     padding: 12px 24px !important; }
.stTabs [aria-selected="true"]     { color: var(--cream) !important; border-bottom: 2px solid var(--red) !important;
                                     background: #1a0808 !important; }

.stDataFrame                       { background: var(--panel) !important; }
.stAlert                           { border-radius: 0 !important; border-left: 3px solid var(--red) !important; }

#MainMenu, footer                  { visibility: hidden; }
::-webkit-scrollbar                { width: 3px; }
::-webkit-scrollbar-thumb          { background: var(--dim); }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 2. HELPERS
# ============================================================
def get_db_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )

def extract_source(url):
    try:
        return urlparse(str(url)).netloc.replace("www.", "").upper()
    except Exception:
        return "UNKNOWN"

def stat_card(col, label, value):
    col.markdown(
        f"""
        <div style='background:#111; border-top:2px solid #a01a1a;
                    padding:14px 16px; margin-bottom:1rem;'>
          <div style='font-size:0.55rem; color:#444; letter-spacing:3px;
                      text-transform:uppercase;'>{label}</div>
          <div style='font-family:"Playfair Display",serif; font-size:1.6rem;
                      color:#e0e0d1; margin-top:5px;'>{value}</div>
        </div>""",
        unsafe_allow_html=True
    )

def section_label(text):
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:10px; margin:1.4rem 0 0.6rem;'>
          <span style='font-size:0.6rem; color:#a01a1a; letter-spacing:4px;
                       text-transform:uppercase; white-space:nowrap;'>{text}</span>
          <div style='flex:1; height:1px; background:#1e1e1e;'></div>
        </div>""",
        unsafe_allow_html=True
    )

PLOT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#444", size=10),
    margin=dict(t=20, b=20, l=10, r=10),
)


# ============================================================
# 3. CACHED DATA LOADERS
# ============================================================
@st.cache_data(ttl=300)
def load_countries():
    try:
        conn = get_db_connection()
        raw  = pd.read_sql(
            "SELECT DISTINCT location_name FROM news_signals", conn
        )["location_name"].tolist()
        conn.close()
        return sorted(set([
            str(l).split(",")[-1].strip()
            for l in raw if l and len(str(l)) > 2
        ]))
    except Exception:
        return ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Brazil"]

@st.cache_data(ttl=60)
def fetch_signals(geography):
    try:
        conn = get_db_connection()
        df   = pd.read_sql(
            "SELECT * FROM news_signals WHERE location_name ILIKE %s",
            conn, params=(f"%{geography}%",)
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def fetch_avg_sentiment(country):
    try:
        conn = get_db_connection()
        val  = pd.read_sql(
            "SELECT AVG(sentiment_score) as avg FROM news_signals WHERE location_name ILIKE %s",
            conn, params=(f"%{country}%",)
        )["avg"].iloc[0]
        conn.close()
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0


# ============================================================
# 4. SESSION STATE
# ============================================================
if "target" not in st.session_state:
    st.session_state.target = "India"

country_list = load_countries()


# ============================================================
# 5. SIDEBAR
# ============================================================
with st.sidebar:

    st.markdown("""
    <div style='text-align:center; padding:1rem 0 1.5rem;'>
      <div style='font-family:"Playfair Display",serif; font-size:1.5rem;
                  color:#e0e0d1; letter-spacing:6px;'>
        BIAS<span style='color:#a01a1a;'>SENTINEL</span>
      </div>
      <div style='font-size:0.55rem; color:#333; letter-spacing:4px;
                  text-transform:uppercase; margin-top:4px;'>
        Media Intelligence v2.0
      </div>
    </div>
    <div style='height:1px; background:#1e1e1e; margin-bottom:1.2rem;'></div>
    """, unsafe_allow_html=True)

    # ── Roulette ──
    st.markdown(
        "<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px;"
        " text-transform:uppercase; margin-bottom:8px;'>Regional Roulette</div>",
        unsafe_allow_html=True
    )

    slot = st.empty()

    def render_slot(text, spinning=False):
        color = "#a01a1a" if spinning else "#e0e0d1"
        slot.markdown(
            f"""
            <div style='background:#0d0d0d; border:1px solid #1e1e1e;
                        border-left:2px solid #a01a1a; padding:14px;
                        text-align:center; font-family:"Playfair Display",serif;
                        font-size:1.2rem; color:{color}; letter-spacing:4px;
                        text-transform:uppercase; margin-bottom:10px;'>
              {text.upper()}
            </div>""",
            unsafe_allow_html=True
        )

    render_slot(st.session_state.target)

    if st.button("SPIN TARGET"):
        for _ in range(9):
            render_slot(random.choice(country_list), spinning=True)
            time.sleep(0.08)
        st.session_state.target = random.choice(country_list)
        st.rerun()

    st.markdown(
        "<div style='height:1px; background:#1e1e1e; margin:1rem 0;'></div>",
        unsafe_allow_html=True
    )

    # ── Bureau Audit ──
    st.markdown(
        "<div style='font-size:0.6rem; color:#a01a1a; letter-spacing:3px;"
        " text-transform:uppercase; margin-bottom:8px;'>Bureau Audit</div>",
        unsafe_allow_html=True
    )

    if st.button("RUN BIAS AUDIT"):
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("CALL run_bias_audit();")
            conn.commit()
            conn.close()
            st.success("Audit complete.")
        except Exception as e:
            st.error(str(e))


# ============================================================
# 6. MASTHEAD
# ============================================================
target = st.session_state.target

st.markdown(
    f"""
    <div style='border-bottom:1px solid #1e1e1e; padding-bottom:1rem;
                margin-bottom:1.5rem; display:flex; align-items:flex-end;
                justify-content:space-between;'>
      <div>
        <div style='font-family:"Playfair Display",serif; font-size:2.2rem;
                    color:#e0e0d1; letter-spacing:8px; text-transform:uppercase;'>
          BIAS<span style='color:#a01a1a;'>SENTINEL</span>
        </div>
        <div style='font-size:0.55rem; color:#333; letter-spacing:4px; text-transform:uppercase;'>
          Global Media Intelligence Engine &nbsp;·&nbsp; Neon Cloud &nbsp;·&nbsp; PL/SQL
        </div>
      </div>
      <div style='background:#a01a1a12; border:1px solid #a01a1a33;
                  padding:6px 18px; font-size:0.65rem; color:#a01a1a;
                  letter-spacing:3px; text-transform:uppercase;'>
        TARGET: {target.upper()}
      </div>
    </div>""",
    unsafe_allow_html=True
)


# ============================================================
# 7. LOAD DATA FOR TARGET
# ============================================================
filtered_df = fetch_signals(target)


# ============================================================
# 8. TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["DASHBOARD", "COMPARE", "SOURCES", "REPORTING"])


# ──────────────────────────────────────────────
# TAB 1 · DASHBOARD
# ──────────────────────────────────────────────
with tab1:
    if filtered_df.empty:
        st.info("No active signals found for this region.")
    else:
        # Stat strip
        s1, s2, s3, s4 = st.columns(4)
        stat_card(s1, "Total Articles",    str(len(filtered_df)))
        stat_card(s2, "Avg Sentiment",     f"{filtered_df['sentiment_score'].mean():.3f}")
        stat_card(s3, "Sources Monitored", str(filtered_df["source_url"].nunique()))
        stat_card(s4, "Status",            "SYNCED")

        # Media landscape table
        section_label("Regional Media Landscape")
        sort_order = st.selectbox(
            "Editorial Priority",
            ["Most Negative First", "Most Positive First"]
        )

        df_grouped = (
            filtered_df
            .groupby("source_url")["sentiment_score"]
            .agg(["mean", "count"])
            .reset_index()
        )
        df_grouped.columns = ["source_url", "avg_score", "Articles"]
        df_grouped = df_grouped.sort_values(
            "avg_score", ascending=("Negative" in sort_order)
        ).head(15)
        df_grouped["CHANNEL"] = df_grouped["source_url"].apply(extract_source)

        # Styled HTML table
        rows_html = ""
        for _, row in df_grouped.iterrows():
            s  = row["avg_score"]
            sc = "#a01a1a" if s < -1 else ("#e0e0d1" if s > 1 else "#555")
            rows_html += (
                f"<tr>"
                f"<td style='padding:8px 12px; color:#e0e0d1; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{row['CHANNEL']}</td>"
                f"<td style='padding:8px 12px; color:{sc}; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{s:+.3f}</td>"
                f"<td style='padding:8px 12px; color:#444; border-bottom:1px solid #1a1a1a; font-size:0.72rem;'>{row['Articles']}</td>"
                f"</tr>"
            )

        st.markdown(
            f"""
            <table style='width:100%; background:#111; border-collapse:collapse; margin-bottom:1.2rem;'>
              <thead>
                <tr style='background:#0d0d0d;'>
                  <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #2a2a2a;'>Channel</th>
                  <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #2a2a2a;'>Avg Score</th>
                  <th style='padding:9px 12px; text-align:left; font-size:0.6rem; color:#a01a1a; letter-spacing:3px; border-bottom:1px solid #2a2a2a;'>Articles</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>""",
            unsafe_allow_html=True
        )

        # Charts
        section_label("Signal Analysis")
        ch1, ch2 = st.columns(2)

        with ch1:
            fig1 = px.histogram(
                filtered_df, x="sentiment_score",
                color_discrete_sequence=["#a01a1a"], nbins=30
            )
            fig1.update_layout(**PLOT)
            fig1.update_traces(marker_line_width=0)
            st.plotly_chart(fig1, use_container_width=True)

        with ch2:
            top10  = df_grouped.head(10)
            colors = ["#a01a1a" if s < 0 else "#444" for s in top10["avg_score"]]
            fig2 = go.Figure(go.Bar(
                x=top10["avg_score"], y=top10["CHANNEL"],
                orientation="h", marker_color=colors, marker_line_width=0
            ))
            fig2.update_layout(**PLOT)
            st.plotly_chart(fig2, use_container_width=True)


# ──────────────────────────────────────────────
# TAB 2 · COMPARE
# ──────────────────────────────────────────────
with tab2:
    section_label("Cross-Regional Disparity Analysis")
    st.markdown(
        "<div style='background:#111; border-left:3px solid #a01a1a; padding:12px 16px;"
        " font-size:0.7rem; color:#555; letter-spacing:2px; text-transform:uppercase;"
        " margin-bottom:1.2rem;'>"
        "INTERNAL ADVISORY: Comparing systemic sentiment averages between two sovereign nations."
        "</div>",
        unsafe_allow_html=True
    )

    ca_col, cb_col = st.columns(2)
    with ca_col:
        c_a = st.selectbox("Region Alpha", country_list, index=0)
    with cb_col:
        c_b = st.selectbox("Region Beta",  country_list, index=min(1, len(country_list) - 1))

    avg_a = fetch_avg_sentiment(c_a)
    avg_b = fetch_avg_sentiment(c_b)

    m1, m2 = st.columns(2)
    stat_card(m1, c_a.upper(), f"{avg_a:+.3f}")
    stat_card(m2, c_b.upper(), f"{avg_b:+.3f}")

    # Delta
    delta  = avg_a - avg_b
    dc     = "#a01a1a" if delta < 0 else "#e0e0d1"
    st.markdown(
        f"""
        <div style='background:#0d0d0d; border:1px solid #1e1e1e; padding:1rem 2rem;
                    text-align:center; margin-bottom:1.5rem;'>
          <span style='font-size:0.6rem; color:#444; letter-spacing:3px; text-transform:uppercase;'>Delta &nbsp;</span>
          <span style='font-family:"Playfair Display",serif; font-size:1.8rem; color:{dc};'>{delta:+.3f}</span>
          <span style='font-size:0.6rem; color:#333; letter-spacing:2px;'>&nbsp; ({c_a.upper()} vs {c_b.upper()})</span>
        </div>""",
        unsafe_allow_html=True
    )

    section_label("Visual Comparison")
    fig_comp = go.Figure(data=[
        go.Bar(name=c_a.upper(), x=[c_a.upper()], y=[avg_a],
               marker_color="#a01a1a", marker_line_width=0),
        go.Bar(name=c_b.upper(), x=[c_b.upper()], y=[avg_b],
               marker_color="#444",   marker_line_width=0),
    ])
    fig_comp.update_layout(
        **PLOT,
        barmode="group",
        legend=dict(font=dict(color="#555", size=9))
    )
    st.plotly_chart(fig_comp, use_container_width=True)


# ──────────────────────────────────────────────
# TAB 3 · SOURCES
# ──────────────────────────────────────────────
with tab3:
    section_label("Active Signal Feed")

    if filtered_df.empty:
        st.info("No signals found for this region.")
    else:
        cols_available = [
            c for c in ["actor_name", "location_name", "sentiment_score", "source_url"]
            if c in filtered_df.columns
        ]
        st.dataframe(
            filtered_df[cols_available].head(30),
            use_container_width=True
        )


# ──────────────────────────────────────────────
# TAB 4 · REPORTING
# ──────────────────────────────────────────────
with tab4:
    section_label("Signal Interception & Reporting")
    st.markdown(
        "<div style='background:#111; border-left:3px solid #a01a1a; padding:12px 16px;"
        " font-size:0.7rem; color:#555; letter-spacing:2px; text-transform:uppercase;"
        " margin-bottom:1.2rem;'>"
        "AUDIT INTERFACE: Categorize and log biased reporting patterns."
        " This data triggers backend PL/SQL audit cycles."
        "</div>",
        unsafe_allow_html=True
    )

    # Determine channel list safely
    if not filtered_df.empty and "actor_name" in filtered_df.columns:
        channel_options = filtered_df["actor_name"].dropna().unique().tolist()
    elif not filtered_df.empty:
        channel_options = df_grouped["CHANNEL"].tolist() if "df_grouped" in dir() else ["No signals detected"]
    else:
        channel_options = ["No signals detected"]

    col_rep1, col_rep2, col_rep3 = st.columns([2, 2, 1])
    with col_rep1:
        report_channel = st.selectbox("Channel to Flag", channel_options)
    with col_rep2:
        bias_category  = st.selectbox(
            "Basis of Reporting",
            [
                "Inaccurate Reporting (Fake News)",
                "Political Favoritism",
                "Sensationalism",
                "Cultural / Regional Insensitivity",
            ]
        )
    with col_rep3:
        st.markdown("<div style='margin-top:1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("SUBMIT FLAG"):
            try:
                conn         = get_db_connection()
                cur          = conn.cursor()
                full_reason  = f"{bias_category} flagged for {report_channel}"
                cur.execute(
                    "INSERT INTO bias_reports (report_reason) VALUES (%s)",
                    (full_reason,)
                )
                conn.commit()
                conn.close()
                st.toast(f"LOGGED: {report_channel} flagged for {bias_category}", icon="✒️")
            except Exception as e:
                st.error(f"DATABASE ERROR: {e}")

    # Signal intercept cards
    section_label("Recent Signal Intercepts")

    if not filtered_df.empty:
        cards_df = filtered_df.sample(min(len(filtered_df), 6))
        grid     = st.columns(3)
        for i, (_, row) in enumerate(cards_df.iterrows()):
            score  = row["sentiment_score"]
            accent = "#a01a1a" if score < 0 else "#2a2a2a"
            with grid[i % 3]:
                st.markdown(
                    f"""
                    <div style='background:#111; border-top:2px solid {accent};
                                padding:12px 14px; margin-bottom:8px;'>
                      <div style='font-size:0.58rem; color:#444; letter-spacing:2px; text-transform:uppercase;'>
                        {extract_source(row["source_url"])}
                      </div>
                      <div style='font-family:"Playfair Display",serif; font-size:1.3rem;
                                  color:{"#a01a1a" if score < 0 else "#e0e0d1"}; margin-top:6px;'>
                        {score:+.2f}
                      </div>
                    </div>""",
                    unsafe_allow_html=True
                )
                st.link_button("Read Article", str(row["source_url"]), use_container_width=True)
    else:
        st.info("No signals to display.")


# ============================================================
# 9. FIXED FOOTER
# ============================================================
st.markdown(
    """
    <div style='position:fixed; bottom:0; left:0; width:100%; background:#000;
                border-top:1px solid #1e1e1e; padding:5px 1.5rem;
                display:flex; justify-content:space-between; align-items:center; z-index:9999;'>
      <span style='font-size:0.55rem; color:#a01a1a; letter-spacing:3px; text-transform:uppercase;'>
        Biassentinel Dispatch
      </span>
      <span style='font-size:0.55rem; color:#2a2a2a; letter-spacing:2px; text-transform:uppercase;'>
        Database: Neon Cloud &nbsp;|&nbsp; PL/SQL Enabled
      </span>
    </div>""",
    unsafe_allow_html=True
)