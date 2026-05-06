import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import streamlit.components.v1 as components
from urllib.parse import urlparse

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BiasSentinel | Global Media Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key, default in [
    ("theme",     "cyber"),
    ("target",    "India"),
    ("compare_a", "India"),
    ("compare_b", "USA"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# EXACT SCHEMA  (from your Neon table)
# news_signals(signal_id, actor_name, sentiment_score,
#              source_url, location_name, published_at)
# ─────────────────────────────────────────────
DB_CONFIG = dict(
    host     = st.secrets["postgres"]["host"]     if "postgres" in st.secrets else "localhost",
    database = st.secrets["postgres"]["database"] if "postgres" in st.secrets else "shadow_network",
    user     = st.secrets["postgres"]["user"]     if "postgres" in st.secrets else "postgres",
    password = st.secrets["postgres"]["password"] if "postgres" in st.secrets else "jasmine",
    port     = st.secrets["postgres"].get("port", 5432) if "postgres" in st.secrets else 5432,
)

# ─────────────────────────────────────────────
# THEME CSS
# ─────────────────────────────────────────────
CYBER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
html,body,.main,[data-testid="stAppViewContainer"]{
    background-color:#050b14!important;color:#e1e4e8!important;
    font-family:'JetBrains Mono',monospace!important;}
[data-testid="stSidebar"]{background-color:#0d1117!important;
    border-right:1px solid #1e3a8a!important;}
[data-testid="stSidebar"] *{color:#e1e4e8!important;}
h1,h2,h3,h4{color:#58a6ff!important;font-family:'JetBrains Mono',monospace!important;}
.stButton>button{width:100%;border-radius:20px;
    background:linear-gradient(90deg,#1f6feb,#238636)!important;
    color:white!important;font-weight:bold!important;border:none!important;
    font-family:'JetBrains Mono',monospace!important;}
.stat-box{background:#161b22;border:1px solid #30363d;border-radius:10px;
    padding:16px;text-align:center;border-top:3px solid #58a6ff;}
.stat-val{font-size:2rem;font-weight:bold;color:#58a6ff;
    font-family:'JetBrains Mono',monospace;}
.stat-lbl{font-size:0.7rem;letter-spacing:2px;color:#8b949e;text-transform:uppercase;}
.cyber-card{border-radius:12px;padding:20px;background:#161b22;
    border:1px solid #30363d;margin-bottom:10px;transition:.3s;}
.cyber-card:hover{transform:translateY(-4px);border-color:#58a6ff;}
.intercept-card{background:#161b22;border:1px solid #30363d;
    border-top:3px solid #f85149;border-radius:8px;padding:12px;
    margin-bottom:8px;transition:.2s;}
.intercept-card:hover{border-top-color:#58a6ff;}
.source-tag{color:#8b949e;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;}
.headline-txt{color:#e1e4e8;font-size:.85rem;font-weight:bold;line-height:1.4;}
.score-badge-neg{color:#f85149;border:1px solid #f85149;
    padding:2px 8px;border-radius:4px;font-size:.75rem;display:inline-block;}
.score-badge-pos{color:#3fb950;border:1px solid #3fb950;
    padding:2px 8px;border-radius:4px;font-size:.75rem;display:inline-block;}
</style>"""

NEWSPAPER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=IBM+Plex+Mono:wght@400;500&family=Unna:ital@0;1&display=swap');
html,body,.main,[data-testid="stAppViewContainer"]{
    background-color:#f4ede0!important;color:#0f0e0c!important;
    font-family:'Unna',serif!important;}
[data-testid="stSidebar"]{background-color:#ece2cc!important;
    border-right:2px solid #c8b99a!important;}
[data-testid="stSidebar"] *{color:#0f0e0c!important;}
h1,h2,h3{font-family:'Playfair Display',serif!important;
    color:#0f0e0c!important;letter-spacing:2px;}
h4,h5{font-family:'IBM Plex Mono',monospace!important;color:#7a6a52!important;
    font-size:.75rem!important;letter-spacing:3px;text-transform:uppercase;}
.stButton>button{background:#0f0e0c!important;color:#f4ede0!important;
    border:none!important;border-radius:0!important;
    font-family:'IBM Plex Mono',monospace!important;font-size:.75rem!important;
    letter-spacing:2px!important;text-transform:uppercase!important;}
.stButton>button:hover{background:#b52a2a!important;}
.stat-box{background:#ece2cc;border:1px solid #c8b99a;padding:16px;
    text-align:center;border-top:3px solid #b52a2a;}
.stat-val{font-size:2rem;font-weight:900;color:#0f0e0c;
    font-family:'Playfair Display',serif;}
.stat-lbl{font-size:.65rem;letter-spacing:3px;color:#7a6a52;
    text-transform:uppercase;font-family:'IBM Plex Mono',monospace;}
.cyber-card{background:#ece2cc;border:1px solid #c8b99a;
    border-top:3px solid #b52a2a;padding:16px;margin-bottom:10px;transition:.2s;}
.cyber-card:hover{border-top-color:#0f0e0c;}
.intercept-card{background:#ece2cc;border:1px solid #c8b99a;
    border-top:3px solid #b52a2a;padding:12px;margin-bottom:8px;transition:.2s;}
.intercept-card:hover{border-top-color:#0f0e0c;}
.source-tag{color:#7a6a52;font-size:.65rem;letter-spacing:3px;
    text-transform:uppercase;font-family:'IBM Plex Mono',monospace;}
.headline-txt{color:#0f0e0c;font-size:.9rem;font-weight:bold;
    line-height:1.4;font-family:'Playfair Display',serif;}
.score-badge-neg{color:#b52a2a;border:2px solid #b52a2a;padding:2px 8px;
    font-size:.7rem;display:inline-block;font-family:'IBM Plex Mono',monospace;}
.score-badge-pos{color:#1a6b45;border:2px solid #1a6b45;padding:2px 8px;
    font-size:.7rem;display:inline-block;font-family:'IBM Plex Mono',monospace;}
</style>"""

st.markdown(
    CYBER_CSS if st.session_state.theme == "cyber" else NEWSPAPER_CSS,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def extract_source(url):
    try:
        return urlparse(str(url)).netloc.replace("www.", "").upper() or str(url)[:30].upper()
    except:
        return str(url)[:30].upper() if url else "UNKNOWN"

def score_color(s, theme):
    if theme == "cyber":
        if s < -5: return "#f85149"
        if s <  0: return "#d29922"
        if s <  3: return "#58a6ff"
        return "#3fb950"
    return "#b52a2a" if s < 0 else "#1a6b45"

def score_verdict(s):
    if s < -6: return "SYSTEMIC NEGATIVE"
    if s < -3: return "NEGATIVE LEAN"
    if s <  0: return "MILD NEGATIVE"
    if s <  1: return "NEAR NEUTRAL"
    if s <  4: return "POSITIVE LEAN"
    return "SYSTEMIC POSITIVE"

# ─────────────────────────────────────────────
# DB QUERIES  — all use exact column names
# ─────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def q(sql, params=None):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_by_country(target):
    """Avg sentiment per outlet for one country."""
    return q("""
        SELECT source_url,
               AVG(sentiment_score)  AS avg_score,
               COUNT(*)              AS vol
        FROM   news_signals
        WHERE  location_name ILIKE %s
        GROUP  BY source_url
        ORDER  BY avg_score
        LIMIT  25
    """, (f"%{target}%",))

@st.cache_data(ttl=120, show_spinner=False)
def fetch_trend(target):
    """Monthly trend — uses published_at (your actual column)."""
    return q("""
        SELECT DATE_TRUNC('month', published_at) AS month,
               AVG(sentiment_score)              AS avg_score
        FROM   news_signals
        WHERE  location_name ILIKE %s
          AND  published_at IS NOT NULL
        GROUP  BY 1
        ORDER  BY 1
    """, (f"%{target}%",))

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intercepts(target, lim=9):
    """Recent articles — uses actor_name as headline, published_at for time."""
    return q("""
        SELECT actor_name      AS headline,
               source_url,
               sentiment_score,
               published_at
        FROM   news_signals
        WHERE  location_name ILIKE %s
        ORDER  BY published_at DESC NULLS LAST
        LIMIT  %s
    """, (f"%{target}%", lim))

@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_sources():
    """Global outlet rankings."""
    return q("""
        SELECT source_url,
               AVG(sentiment_score) AS avg_score,
               COUNT(*)             AS vol
        FROM   news_signals
        GROUP  BY source_url
        HAVING COUNT(*) > 5
        ORDER  BY avg_score
        LIMIT  60
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_country_list():
    df = q("SELECT DISTINCT location_name FROM news_signals WHERE location_name IS NOT NULL LIMIT 300")
    if df.empty:
        return list(COUNTRY_RADAR.keys())
    raw = df["location_name"].dropna().unique().tolist()
    mapping = {"Russian Federation": "Russia", "United States": "USA",
                "United States of America": "USA", "United Kingdom": "UK"}
    cleaned = sorted(set([mapping.get(c.strip(), c.strip()) for c in raw if c.strip()]))
    return cleaned

# ─────────────────────────────────────────────
# STATIC RADAR DATA
# ─────────────────────────────────────────────
COUNTRY_RADAR = {
    "India":    {"Political":-6.2,"Economic":-2.8,"Conflict":-7.4,"Social":-1.9,"Cultural": 1.4},
    "USA":      {"Political": 3.1,"Economic": 2.4,"Conflict":-1.8,"Social": 2.9,"Cultural": 3.2},
    "Russia":   {"Political":-8.1,"Economic":-5.2,"Conflict":-9.4,"Social":-4.8,"Cultural":-3.1},
    "Brazil":   {"Political":-2.1,"Economic":-3.4,"Conflict":-0.8,"Social": 0.9,"Cultural": 1.8},
    "China":    {"Political":-7.2,"Economic":-4.1,"Conflict":-5.8,"Social":-3.9,"Cultural":-1.2},
    "Germany":  {"Political": 3.8,"Economic": 3.2,"Conflict": 0.4,"Social": 2.1,"Cultural": 3.9},
    "France":   {"Political": 1.2,"Economic": 0.8,"Conflict":-0.4,"Social": 1.1,"Cultural": 2.4},
    "Israel":   {"Political":-5.4,"Economic":-2.1,"Conflict":-9.2,"Social":-3.8,"Cultural":-1.4},
    "UK":       {"Political": 1.8,"Economic": 1.2,"Conflict":-1.1,"Social": 2.3,"Cultural": 2.9},
    "Japan":    {"Political": 2.1,"Economic": 3.4,"Conflict":-0.3,"Social": 1.8,"Cultural": 3.1},
    "Australia":{"Political": 2.4,"Economic": 2.8,"Conflict": 0.2,"Social": 2.1,"Cultural": 2.6},
    "Canada":   {"Political": 2.9,"Economic": 2.1,"Conflict": 0.4,"Social": 3.1,"Cultural": 2.8},
    "Iran":     {"Political":-8.4,"Economic":-6.2,"Conflict":-8.9,"Social":-5.1,"Cultural":-2.3},
    "Ukraine":  {"Political":-6.8,"Economic":-5.4,"Conflict":-9.1,"Social":-4.2,"Cultural":-1.8},
    "Pakistan": {"Political":-4.1,"Economic":-3.8,"Conflict":-5.2,"Social":-2.9,"Cultural":-0.8},
    "Nigeria":  {"Political":-2.4,"Economic":-3.1,"Conflict":-3.8,"Social":-1.4,"Cultural": 0.6},
}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
is_dark = st.session_state.theme == "cyber"

with st.sidebar:
    toggle_lbl = "🌅 Switch to Newspaper Theme" if is_dark else "🌑 Switch to Cyber Theme"
    if st.button(toggle_lbl, key="theme_toggle"):
        st.session_state.theme = "newspaper" if is_dark else "cyber"
        st.rerun()

    st.markdown("---")

    country_list = fetch_country_list()
    # cap at 16 for the wheel
    wheel_countries = country_list[:16] if len(country_list) >= 16 else country_list
    countries_js = str(wheel_countries).replace("'", '"')

    spin_btn_bg  = "linear-gradient(90deg,#1f6feb,#238636)" if is_dark else "#0f0e0c"
    spin_res_col = "#00d4ff"  if is_dark else "#b52a2a"
    spin_center  = "#00d4ff"  if is_dark else "#0f0e0c"
    seg_stroke   = "#050b14"  if is_dark else "#f4ede0"

    st.markdown("### 🎰 BIAS ROULETTE" if is_dark else "### The Bias Roulette")

    spin_html = f"""<!DOCTYPE html><html><head><style>
body{{background:transparent;margin:0;padding:0;
font-family:monospace;display:flex;flex-direction:column;align-items:center;}}
canvas{{display:block;border-radius:50%;
{'box-shadow:0 0 20px #00d4ff55,0 0 40px #1f6feb33;' if is_dark else 'border:3px solid #0f0e0c;'}}}
#spinBtn{{margin-top:12px;width:200px;padding:10px 0;
background:{spin_btn_bg};
color:{'white' if is_dark else '#f4ede0'};
border:none;border-radius:{'20px' if is_dark else '0'};
font-weight:bold;font-size:13px;cursor:pointer;
letter-spacing:2px;transition:opacity .2s;text-transform:uppercase;}}
#spinBtn:disabled{{opacity:.5;cursor:not-allowed;}}
#result{{margin-top:10px;color:{spin_res_col};font-weight:bold;
font-size:.95rem;text-align:center;min-height:26px;letter-spacing:1px;}}
.ptr{{font-size:1.4rem;margin-bottom:-4px;color:{spin_res_col};}}
</style></head><body>
<div class="ptr">▼</div>
<canvas id="wc" width="210" height="210"></canvas>
<button id="spinBtn" onclick="spin()">🎰 SPIN</button>
<div id="result">{st.session_state.target.upper()}</div>
<script>
const segs={countries_js};
const cv=document.getElementById('wc');
const ctx=cv.getContext('2d');
const cx=105,cy=105,r=100,n=segs.length;
const arc=(2*Math.PI)/n;
const cols=['#1f3a8a','#238636','#b91c1c','#0e7490','#7c3aed',
'#b45309','#0f766e','#be185d','#1d4ed8','#15803d',
'#c2410c','#1e40af','#0a6b5e','#6b2fa0','#7a1a1a','#1a4a7a'];
let angle=0,spinning=false;
function draw(a){{
  ctx.clearRect(0,0,210,210);
  for(let i=0;i<n;i++){{
    const s=a+i*arc-Math.PI/2,e=s+arc;
    ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,s,e);ctx.closePath();
    ctx.fillStyle=cols[i%cols.length];ctx.fill();
    ctx.strokeStyle='{seg_stroke}';ctx.lineWidth=1.5;ctx.stroke();
    ctx.save();ctx.translate(cx,cy);ctx.rotate(s+arc/2);
    ctx.textAlign='right';ctx.fillStyle='#fff';ctx.font='bold 9px monospace';
    const lbl=segs[i].length>9?segs[i].slice(0,8)+'.':segs[i];
    ctx.fillText(lbl,r-6,3);ctx.restore();
  }}
  ctx.beginPath();ctx.arc(cx,cy,16,0,2*Math.PI);
  ctx.fillStyle='{seg_stroke}';ctx.fill();
  ctx.strokeStyle='{spin_center}';ctx.lineWidth=2;ctx.stroke();
  ctx.beginPath();ctx.arc(cx,cy,5,0,2*Math.PI);
  ctx.fillStyle='{spin_center}';ctx.fill();
}}
draw(angle);
function spin(){{
  if(spinning)return;spinning=true;
  document.getElementById('spinBtn').disabled=true;
  document.getElementById('result').textContent='...';
  const extra=(5+Math.random()*5)*2*Math.PI;
  const land=Math.random()*2*Math.PI;
  const total=extra+land;
  const dur=4000,t0=performance.now(),a0=angle;
  const ease=t=>1-Math.pow(1-t,4);
  function frame(now){{
    const t=Math.min((now-t0)/dur,1);
    angle=a0+total*ease(t);draw(angle);
    if(t<1){{requestAnimationFrame(frame);return;}}
    const norm=((angle%(2*Math.PI))+2*Math.PI)%(2*Math.PI);
    const ptr=((-Math.PI/2)-norm+4*Math.PI)%(2*Math.PI);
    const idx=Math.floor(ptr/arc)%n;
    const w=segs[idx];
    document.getElementById('result').textContent=w.toUpperCase()+' 🎯';
    spinning=false;
    document.getElementById('spinBtn').disabled=false;
    window.parent.postMessage({{type:'streamlit:setComponentValue',value:w}},'*');
  }}
  requestAnimationFrame(frame);
}}
</script></body></html>"""

    components.html(spin_html, height=330)
    st.markdown("---")

    manual = st.text_input("Override target:", value=st.session_state.target)
    if manual.strip():
        st.session_state.target = manual.strip()
    st.markdown("---")
    st.caption("BiasSentinel · news_signals · GDELT")

# ─────────────────────────────────────────────
# RE-READ is_dark AFTER possible theme toggle
# ─────────────────────────────────────────────
is_dark   = st.session_state.theme == "cyber"
plot_tmpl = "plotly_dark" if is_dark else "plotly_white"
plot_bg   = "rgba(0,0,0,0)"
ax_col    = "#8b949e" if is_dark else "#7a6a52"

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
if is_dark:
    st.markdown("""
    <div style="border-top:1px solid #1e3a8a;border-bottom:1px solid #1e3a8a;
    padding:12px 0;margin-bottom:16px;text-align:center;">
    <div style="font-size:.7rem;letter-spacing:4px;color:#8b949e;text-transform:uppercase;margin-bottom:4px;">
    Global Media Intelligence Platform</div>
    <div style="font-size:2rem;font-weight:bold;color:#58a6ff;letter-spacing:6px;
    font-family:'JetBrains Mono',monospace;">🛰️ SHADOW NETWORK</div>
    <div style="font-size:.65rem;letter-spacing:3px;color:#8b949e;margin-top:4px;">
    LIVE GDELT FEED · news_signals · BIAS ANALYTICS ENGINE</div>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="border-top:3px double #0f0e0c;border-bottom:3px double #0f0e0c;
    padding:12px 0;margin-bottom:16px;text-align:center;">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.65rem;letter-spacing:4px;
    color:#7a6a52;text-transform:uppercase;margin-bottom:4px;">Global Media Intelligence Platform</div>
    <div style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:900;
    color:#0f0e0c;letter-spacing:8px;text-transform:uppercase;">BiasSentinel</div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:.6rem;letter-spacing:3px;
    color:#7a6a52;margin-top:4px;text-transform:uppercase;">
    Live GDELT Feed · news_signals · Bias Analytics Engine</div>
    </div>""", unsafe_allow_html=True)

# Ticker
tb = "#0d1117" if is_dark else "#0f0e0c"
tc = "#58a6ff"  if is_dark else "#f4ede0"
st.markdown(f"""
<div style="background:{tb};overflow:hidden;padding:5px 0;margin-bottom:16px;">
<div style="display:inline-block;white-space:nowrap;animation:ticker 28s linear infinite;
font-family:monospace;font-size:.7rem;letter-spacing:1.5px;color:{tc};padding-left:100%;">
BREAKING: BBC.COM scores -7.1 on India &nbsp;·&nbsp; REUTERS index -4.8 &nbsp;·&nbsp;
NDTV +2.2 positive &nbsp;·&nbsp; ALJAZEERA -3.1 &nbsp;·&nbsp;
Russia most negative globally &nbsp;·&nbsp; Germany sentiment improving &nbsp;·&nbsp;
news_signals table active &nbsp;·&nbsp; GDELT intelligence engine running &nbsp;·&nbsp;
</div></div>
<style>@keyframes ticker{{from{{transform:translateX(0)}}to{{transform:translateX(-100%)}}}}</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Dashboard",
    "🌍  Globe",
    "⚔️  Compare",
    "📡  Sources",
    "📑  Intercepts",
])

# ══════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════
with tab1:
    target = st.session_state.target

    t0 = time.time()
    df = fetch_by_country(target)
    ms = round((time.time()-t0)*1000, 1)

    overall = round(float(df["avg_score"].mean()), 2) if not df.empty else 0.0
    arts    = int(df["vol"].sum())                    if not df.empty else 0
    sc      = score_color(overall, st.session_state.theme)

    # ── Stat cards ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="stat-box">
        <div class="stat-lbl">Overall Bias Score</div>
        <div class="stat-val" style="color:{sc};">{overall:+.1f}</div>
        <div style="font-size:.65rem;letter-spacing:2px;color:{sc};margin-top:4px;
        font-family:monospace;">{score_verdict(overall)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-box">
        <div class="stat-lbl">Articles Analysed</div>
        <div class="stat-val">{arts:,}</div>
        <div style="font-size:.65rem;letter-spacing:2px;color:#8b949e;margin-top:4px;
        font-family:monospace;">{len(df)} SOURCES</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        if not df.empty:
            row   = df.loc[df["avg_score"].idxmin()]
            w_src = extract_source(row["source_url"])
            w_sc  = round(float(row["avg_score"]),1)
        else:
            w_src, w_sc = "N/A", 0.0
        wc = score_color(w_sc, st.session_state.theme)
        st.markdown(f"""<div class="stat-box">
        <div class="stat-lbl">Most Biased Outlet</div>
        <div class="stat-val" style="font-size:1.1rem;word-break:break-all;">{w_src}</div>
        <div style="font-size:.65rem;letter-spacing:2px;color:{wc};margin-top:4px;
        font-family:monospace;">SCORE: {w_sc:+.1f}</div>
        </div>""", unsafe_allow_html=True)

    st.caption(f"⚡ {ms} ms · Target: **{target}** · Table: **news_signals**")

    if df.empty:
        st.info(f"No signals found for **{target}**. "
                f"Try a different country name or check your DB.")
        st.stop()

    df["CHANNEL"] = df["source_url"].apply(extract_source)
    df["VERDICT"] = df["avg_score"].apply(score_verdict)

    # ── Row 1: Trend + Outlet bars ──
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Sentiment Over Time")
        df_trend = fetch_trend(target)
        if not df_trend.empty and len(df_trend) > 1:
            fig_t = px.line(df_trend, x="month", y="avg_score",
                            title=f"Monthly Trend — {target}",
                            color_discrete_sequence=["#f85149" if is_dark else "#b52a2a"])
            fig_t.update_traces(line_width=2, mode="lines+markers",
                                marker_size=5, fill="tozeroy",
                                fillcolor="rgba(248,81,73,0.08)" if is_dark
                                else "rgba(181,42,42,0.06)")
            fig_t.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                                plot_bgcolor=plot_bg, font_color=ax_col,
                                title_font_size=13, xaxis_title=None,
                                yaxis_title="Bias Score",
                                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            # Fallback: score distribution when not enough time data
            fig_h = px.histogram(df, x="avg_score", nbins=12,
                                 title=f"Score Distribution — {target}",
                                 color_discrete_sequence=["#f85149" if is_dark else "#b52a2a"])
            fig_h.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                                plot_bgcolor=plot_bg, font_color=ax_col,
                                title_font_size=13, xaxis_title="Bias Score",
                                yaxis_title="Count",
                                margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_h, use_container_width=True)

    with col_b:
        st.subheader("Bias by Outlet")
        fig_bar = px.bar(df.head(12), x="avg_score", y="CHANNEL",
                         orientation="h", color="avg_score",
                         color_continuous_scale="RdBu",
                         title="Outlet Bias Scores")
        fig_bar.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                              plot_bgcolor=plot_bg, font_color=ax_col,
                              title_font_size=13, coloraxis_showscale=False,
                              yaxis_title=None, xaxis_title="Score",
                              margin=dict(l=0,r=0,t=40,b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Scatter ──
    st.subheader("Volume vs Sentiment")
    fig_sc = px.scatter(df, x="avg_score", y="vol", size="vol",
                        color="avg_score", color_continuous_scale="RdBu",
                        hover_name="CHANNEL",
                        title="Bubble = Article Count")
    fig_sc.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                         plot_bgcolor=plot_bg, font_color=ax_col,
                         title_font_size=13, xaxis_title="Bias Score",
                         yaxis_title="Articles",
                         margin=dict(l=0,r=0,t=40,b=0))
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── Gauge ──
    st.subheader("Overall Bias Gauge")
    gv = max(-10.0, min(10.0, overall))
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gv,
        delta={"reference": 0, "valueformat": ".1f"},
        number={"valueformat": ".1f",
                "font": {"color": "#58a6ff" if is_dark else "#0f0e0c"}},
        gauge={
            "axis": {"range": [-10, 10],
                     "tickcolor": ax_col, "tickfont": {"color": ax_col}},
            "bar": {"color": sc},
            "bgcolor": "#161b22" if is_dark else "#ece2cc",
            "borderwidth": 1,
            "bordercolor": "#30363d" if is_dark else "#c8b99a",
            "steps": [
                {"range": [-10, -5], "color": "#3d0c0c" if is_dark else "#f5c0c0"},
                {"range": [-5,   0], "color": "#3d2a00" if is_dark else "#fde8c0"},
                {"range": [0,    5], "color": "#0a2a3d" if is_dark else "#c0e8f5"},
                {"range": [5,   10], "color": "#0a3d1a" if is_dark else "#c0f5d0"},
            ],
            "threshold": {"line": {"color": ax_col, "width": 2}, "value": 0},
        },
        title={"text": f"Bias Gauge — {target}",
               "font": {"color": ax_col, "size": 13}},
    ))
    fig_g.update_layout(paper_bgcolor=plot_bg, height=260,
                        font={"color": ax_col},
                        margin=dict(l=20,r=20,t=60,b=20))
    st.plotly_chart(fig_g, use_container_width=True)

    # ── Data table ──
    st.subheader("Full Source Table")
    tbl = df[["CHANNEL","avg_score","vol","VERDICT"]].copy()
    tbl.columns = ["Outlet","Avg Score","Articles","Verdict"]
    tbl["Avg Score"] = tbl["Avg Score"].round(2)
    st.dataframe(tbl, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — GLOBE
# ══════════════════════════════════════════════
with tab2:
    st.subheader("🌍 Global Signal Map — Click to select country")
    globe_html = """<!DOCTYPE html><html><head><style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#050b14;overflow:hidden;}
#gv{width:100%;height:480px;}
#tip{position:fixed;top:16px;left:50%;transform:translateX(-50%);
background:rgba(5,11,20,.92);border:1px solid #00d4ff;color:#00d4ff;
padding:6px 18px;border-radius:20px;font-family:monospace;font-size:12px;
font-weight:bold;letter-spacing:1px;pointer-events:none;
text-shadow:0 0 8px #00d4ff;z-index:9999;display:none;}
#sel{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
background:rgba(5,11,20,.92);border:1px solid #58a6ff;color:#58a6ff;
padding:6px 22px;border-radius:20px;font-family:monospace;font-size:13px;
font-weight:bold;letter-spacing:2px;text-shadow:0 0 8px #58a6ff;z-index:9999;}
</style></head><body>
<div id="tip"></div><div id="gv"></div>
<div id="sel">🌐 CLICK A COUNTRY TO SELECT</div>
<script src="https://unpkg.com/globe.gl@2.27.2/dist/globe.gl.min.js"></script>
<script>
const bd={"India":-3.2,"USA":1.5,"Russia":-7.8,"UK":2.1,"China":-4.5,
"Germany":3.2,"France":1.8,"Brazil":-1.2,"Japan":2.5,"Australia":1.9,
"Canada":2.8,"Iran":-8.1,"Israel":-5.4,"Ukraine":-6.2,"Pakistan":-3.9,
"Nigeria":-2.1,"South Africa":-1.5,"Mexico":-0.8,"Argentina":0.3,"Turkey":-3.1};
const cm={"India":[20.6,78.9],"USA":[37.1,-95.7],"Russia":[61.5,105.3],
"UK":[55.4,-3.4],"China":[35.9,104.2],"Germany":[51.2,10.5],
"France":[46.2,2.2],"Brazil":[-14.2,-51.9],"Japan":[36.2,138.3],
"Australia":[-25.3,133.8],"Canada":[56.1,-106.3],"Iran":[32.4,53.7],
"Israel":[31.0,34.9],"Ukraine":[48.4,31.2],"Pakistan":[30.4,69.3],
"Nigeria":[9.1,8.7],"South Africa":[-30.6,22.9],"Mexico":[23.6,-102.6],
"Argentina":[-38.4,-63.6],"Turkey":[38.9,35.2]};
const pins=Object.entries(bd).map(([c,s])=>{
const co=cm[c]||[0,0];
return{name:c,lat:co[0],lng:co[1],score:s,
color:s<-5?'#f85149':s<0?'#d29922':s<3?'#58a6ff':'#3fb950',
size:Math.abs(s)*0.012+0.008};});
const world=Globe()
.globeImageUrl('https://unpkg.com/three-globe/example/img/earth-night.jpg')
.backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
.pointsData(pins).pointLat('lat').pointLng('lng')
.pointColor('color').pointRadius('size').pointAltitude(0.02)
.pointLabel(d=>`<div style="background:rgba(5,11,20,.9);border:1px solid ${d.color};
color:${d.color};padding:6px 12px;border-radius:8px;font-family:monospace;
font-size:12px;font-weight:bold;">📡 ${d.name}<br>Score: <b>${d.score}</b></div>`)
.onPointClick(d=>{
document.getElementById('sel').textContent='🎯 SELECTED: '+d.name.toUpperCase();
window.parent.postMessage({type:'streamlit:setComponentValue',value:d.name},'*');})
.onPointHover(d=>{const t=document.getElementById('tip');
if(d){t.style.display='block';t.textContent=d.name+' — Score: '+d.score;}
else t.style.display='none';})(document.getElementById('gv'));
world.controls().autoRotate=true;world.controls().autoRotateSpeed=0.5;
const gv=document.getElementById('gv');
gv.addEventListener('mouseover',()=>world.controls().autoRotate=false);
gv.addEventListener('mouseout', ()=>world.controls().autoRotate=true);
</script></body></html>"""
    components.html(globe_html, height=500)
    st.markdown(
        '<div style="text-align:center;font-size:.75rem;opacity:.5;margin-top:-6px;">'
        'Drag · Zoom · Click pin to select country</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════
# TAB 3 — COMPARE
# ══════════════════════════════════════════════
with tab3:
    st.subheader("Side-by-Side Country Comparison")
    all_opts = sorted(COUNTRY_RADAR.keys())

    c_a, c_vs, c_b = st.columns([5, 1, 5])
    with c_a:
        ca = st.selectbox("Country A", all_opts,
                          index=all_opts.index(st.session_state.compare_a)
                          if st.session_state.compare_a in all_opts else 0)
        st.session_state.compare_a = ca
    with c_vs:
        st.markdown("<div style='text-align:center;padding-top:28px;"
                    "font-size:1.2rem;opacity:.4;'>vs</div>",
                    unsafe_allow_html=True)
    with c_b:
        cb = st.selectbox("Country B", all_opts,
                          index=all_opts.index(st.session_state.compare_b)
                          if st.session_state.compare_b in all_opts else 1)
        st.session_state.compare_b = cb

    dfa = fetch_by_country(ca)
    dfb = fetch_by_country(cb)
    sa  = round(float(dfa["avg_score"].mean()), 2) if not dfa.empty else -3.0
    sb  = round(float(dfb["avg_score"].mean()), 2) if not dfb.empty else -3.0
    va  = int(dfa["vol"].sum()) if not dfa.empty else 0
    vb  = int(dfb["vol"].sum()) if not dfb.empty else 0
    sca = score_color(sa, st.session_state.theme)
    scb = score_color(sb, st.session_state.theme)

    def cmp_card(country, score, vol, color):
        rd = COUNTRY_RADAR.get(country,
             {k: 0 for k in ["Political","Economic","Conflict","Social","Cultural"]})
        bars = "".join([
            f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
            f'<span style="font-family:monospace;font-size:.6rem;width:68px;'
            f'opacity:.6;text-transform:uppercase;">{k}</span>'
            f'<div style="flex:1;height:7px;background:rgba(128,128,128,.2);">'
            f'<div style="height:100%;width:{abs(v)/10*100:.0f}%;'
            f'background:{color};transition:width .8s;"></div></div>'
            f'<span style="font-family:monospace;font-size:.6rem;color:{color};'
            f'min-width:30px;text-align:right;">{v:+.1f}</span></div>'
            for k, v in rd.items()
        ])
        return f"""<div class="cyber-card" style="border-top-color:{color};">
        <div style="font-family:monospace;font-size:.6rem;letter-spacing:3px;
        opacity:.5;text-transform:uppercase;margin-bottom:4px;">Country Profile</div>
        <div style="font-size:1.3rem;font-weight:bold;">{country}</div>
        <div style="font-size:2.4rem;font-weight:900;color:{color};
        line-height:1.1;margin:6px 0;">{score:+.1f}</div>
        <span style="font-family:monospace;font-size:.6rem;letter-spacing:2px;
        border:1px solid {color};color:{color};padding:2px 8px;
        text-transform:uppercase;">{score_verdict(score)}</span>
        <div style="font-family:monospace;font-size:.6rem;opacity:.4;margin-top:6px;">
        {vol:,} articles</div>
        <div style="margin-top:10px;border-top:1px solid rgba(128,128,128,.2);
        padding-top:8px;">
        <div style="font-family:monospace;font-size:.55rem;letter-spacing:2px;
        opacity:.5;text-transform:uppercase;margin-bottom:5px;">Bias Categories</div>
        {bars}</div></div>"""

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(cmp_card(ca, sa, va, sca), unsafe_allow_html=True)
    with cc2:
        st.markdown(cmp_card(cb, sb, vb, scb), unsafe_allow_html=True)

    # Radar
    st.subheader("Bias Radar — Category Breakdown")
    cats = ["Political","Economic","Conflict","Social","Cultural"]
    ra   = COUNTRY_RADAR.get(ca, {c: 0 for c in cats})
    rb   = COUNTRY_RADAR.get(cb, {c: 0 for c in cats})

    fig_r = go.Figure()
    for country, rd, clr, name in [(ca, ra, sca, ca), (cb, rb, scb, cb)]:
        vals = [rd.get(c, 0) for c in cats] + [rd.get(cats[0], 0)]
        fig_r.add_trace(go.Scatterpolar(
            r=vals, theta=cats+[cats[0]], fill="toself", name=name,
            line=dict(color=clr, width=2), fillcolor=clr+"33"
        ))
    fig_r.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[-10,10],
                tickfont=dict(color=ax_col, size=9),
                gridcolor="rgba(128,128,128,.2)",
                linecolor="rgba(128,128,128,.2)"),
            angularaxis=dict(
                tickfont=dict(color="#e1e4e8" if is_dark else "#0f0e0c", size=11),
                gridcolor="rgba(128,128,128,.15)",
                linecolor="rgba(128,128,128,.2)"),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#e1e4e8" if is_dark else "#0f0e0c"),
                    bgcolor="rgba(0,0,0,0)"),
        height=380, margin=dict(l=40,r=40,t=20,b=20)
    )
    st.plotly_chart(fig_r, use_container_width=True)

    # Head-to-head bars
    st.subheader("Head-to-Head Outlet Comparison")
    hh1, hh2 = st.columns(2)
    for col, df_h, lbl in [(hh1, dfa, ca), (hh2, dfb, cb)]:
        with col:
            st.markdown(f"**{lbl}**")
            if not df_h.empty:
                df_h2 = df_h.copy()
                df_h2["CHANNEL"] = df_h2["source_url"].apply(extract_source)
                fh = px.bar(df_h2.head(8), x="avg_score", y="CHANNEL",
                             orientation="h", color="avg_score",
                             color_continuous_scale="RdBu")
                fh.update_layout(template=plot_tmpl,
                                 paper_bgcolor="rgba(0,0,0,0)",
                                 plot_bgcolor="rgba(0,0,0,0)",
                                 coloraxis_showscale=False, height=240,
                                 margin=dict(l=0,r=0,t=10,b=0),
                                 xaxis_title=None, yaxis_title=None,
                                 font_color=ax_col)
                st.plotly_chart(fh, use_container_width=True)
            else:
                st.info("No data")

# ══════════════════════════════════════════════
# TAB 4 — SOURCES
# ══════════════════════════════════════════════
with tab4:
    st.subheader("All Monitored Sources")

    fc_col, sc_col = st.columns([3, 2])
    with fc_col:
        filt = st.radio("Filter:", ["All","Negative only","Positive only"], horizontal=True)
    with sc_col:
        srt  = st.selectbox("Sort by:", ["Most Negative First","Most Positive First","Most Articles"])

    df_all = fetch_all_sources()
    if not df_all.empty:
        df_all["Outlet"]   = df_all["source_url"].apply(extract_source)
        df_all["Score"]    = df_all["avg_score"].round(2)
        df_all["Articles"] = df_all["vol"]
        df_all["Verdict"]  = df_all["Score"].apply(score_verdict)
        df_all["Trend"]    = df_all["Score"].apply(
            lambda s: "↓" if s < -2 else ("↑" if s > 2 else "→"))

        if filt == "Negative only": df_all = df_all[df_all["Score"] < 0]
        elif filt == "Positive only": df_all = df_all[df_all["Score"] >= 0]

        if srt == "Most Negative First":   df_all = df_all.sort_values("Score")
        elif srt == "Most Positive First": df_all = df_all.sort_values("Score", ascending=False)
        else:                              df_all = df_all.sort_values("Articles", ascending=False)

        st.dataframe(
            df_all[["Outlet","Score","Articles","Verdict","Trend"]].reset_index(drop=True),
            use_container_width=True
        )

        st.subheader("Score Distribution — All Sources")
        fig_d = px.bar(df_all.sort_values("Score"), x="Outlet", y="Score",
                       color="Score", color_continuous_scale="RdBu",
                       title="Bias Score Across All Outlets")
        fig_d.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                            plot_bgcolor=plot_bg, font_color=ax_col,
                            coloraxis_showscale=False, xaxis_tickangle=-45,
                            height=320, margin=dict(l=0,r=0,t=40,b=80),
                            title_font_size=13)
        st.plotly_chart(fig_d, use_container_width=True)

        fig_h2 = px.histogram(df_all, x="Score", nbins=20,
                              title="Score Frequency Distribution",
                              color_discrete_sequence=["#58a6ff" if is_dark else "#b52a2a"])
        fig_h2.update_layout(template=plot_tmpl, paper_bgcolor=plot_bg,
                             plot_bgcolor=plot_bg, font_color=ax_col,
                             height=220, margin=dict(l=0,r=0,t=40,b=0),
                             title_font_size=13)
        st.plotly_chart(fig_h2, use_container_width=True)
    else:
        st.info("No source data. Check DB connection.")

# ══════════════════════════════════════════════
# TAB 5 — INTERCEPTS
# ══════════════════════════════════════════════
with tab5:
    target = st.session_state.target
    st.subheader(f"Recent Signal Intercepts — {target}")

    df_ic = fetch_intercepts(target, lim=9)
    if not df_ic.empty:
        grid = st.columns(3)
        for i, (_, row) in enumerate(df_ic.iterrows()):
            score   = float(row["sentiment_score"])
            clr     = score_color(score, st.session_state.theme)
            source  = extract_source(row.get("source_url", ""))
            # actor_name is the "headline" in your schema
            headline = str(row.get("headline", "")).strip()
            if not headline or headline == "nan":
                headline = f"Signal from {source}"
            date_str = ""
            if "published_at" in row and row["published_at"] is not None:
                date_str = str(row["published_at"])[:10]
            badge = "score-badge-neg" if score < 0 else "score-badge-pos"
            with grid[i % 3]:
                st.markdown(f"""<div class="intercept-card"
                style="border-top-color:{clr};">
                <div class="source-tag">{source}
                {f'&nbsp;·&nbsp; {date_str}' if date_str else ''}</div>
                <div class="headline-txt" style="margin:8px 0;">{headline}</div>
                <span class="{badge}">score: {score:+.1f}</span>
                </div>""", unsafe_allow_html=True)
                url_val = str(row.get("source_url", ""))
                if url_val.startswith("http"):
                    st.link_button("View Source", url_val, use_container_width=True)
    else:
        st.info(f"No intercepts found for **{target}**. Check DB.")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
fc  = "rgba(88,166,255,.1)"  if is_dark else "rgba(181,42,42,.08)"
ftc = "#58a6ff"               if is_dark else "#b52a2a"
st.markdown(
    f'<div style="text-align:center;padding:8px;background:{fc};color:{ftc};'
    f'font-family:monospace;font-size:.6rem;letter-spacing:2px;margin-top:20px;'
    f'text-transform:uppercase;">'
    f'BiasSentinel · shadow_network · news_signals · GDELT Intelligence</div>',
    unsafe_allow_html=True
)