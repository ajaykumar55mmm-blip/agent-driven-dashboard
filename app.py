import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
import os
import io
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #0C0E14; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1E2230;
}
[data-testid="stSidebar"] .stMarkdown p { color: #6B7280; font-size: 12px; }

/* Main header */
.dash-header {
    padding: 2rem 0 1rem;
    border-bottom: 1px solid #1E2230;
    margin-bottom: 2rem;
}
.dash-title {
    font-size: 1.75rem; font-weight: 600; color: #F9FAFB;
    letter-spacing: -0.02em; margin: 0;
}
.dash-sub { color: #4B5563; font-size: 0.875rem; margin-top: 4px; }

/* Upload zone */
.upload-zone {
    border: 1.5px dashed #2D3748;
    border-radius: 12px;
    padding: 2.5rem;
    text-align: center;
    background: #111318;
    transition: border-color 0.2s;
}

/* Status pills */
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.03em;
    margin: 2px;
}
.pill-green  { background: #052E1C; color: #34D399; border: 1px solid #065F46; }
.pill-blue   { background: #0C1A3E; color: #60A5FA; border: 1px solid #1E40AF; }
.pill-amber  { background: #2D1B00; color: #FCD34D; border: 1px solid #78350F; }
.pill-purple { background: #1A0E3E; color: #A78BFA; border: 1px solid #4C1D95; }
.pill-red    { background: #2D0A0A; color: #F87171; border: 1px solid #7F1D1D; }

/* Chat bubbles */
.chat-user {
    background: #161B27;
    border: 1px solid #1E2230;
    border-left: 3px solid #3B82F6;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 8px 0;
    color: #D1D5DB;
    font-size: 13px;
}
.chat-ai {
    background: #0F1419;
    border: 1px solid #1E2230;
    border-left: 3px solid #10B981;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 8px 0;
    color: #9CA3AF;
    font-size: 13px;
}
.chat-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.chat-label.user { color: #3B82F6; }
.chat-label.ai   { color: #10B981; }

/* KPI cards */
.kpi-card {
    background: #111318;
    border: 1px solid #1E2230;
    border-radius: 10px;
    padding: 1.25rem;
    text-align: center;
}
.kpi-label { font-size: 11px; color: #6B7280; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
.kpi-value { font-size: 2rem; font-weight: 600; color: #F9FAFB; letter-spacing: -0.02em; }
.kpi-sub   { font-size: 11px; color: #4B5563; margin-top: 4px; }

/* Section headers */
.section-title {
    font-size: 13px; font-weight: 500; color: #6B7280;
    text-transform: uppercase; letter-spacing: 0.07em;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 6px;
    border-bottom: 1px solid #1E2230;
}

/* Metric tag */
.metric-tag {
    display: inline-block;
    background: #0C1A3E;
    color: #60A5FA;
    border: 1px solid #1E40AF;
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    margin: 2px;
}

/* Warning / info boxes */
.info-box {
    background: #0C1A3E;
    border: 1px solid #1E40AF;
    border-radius: 8px;
    padding: 12px 16px;
    color: #93C5FD;
    font-size: 13px;
    margin: 8px 0;
}
.warn-box {
    background: #2D1B00;
    border: 1px solid #78350F;
    border-radius: 8px;
    padding: 12px 16px;
    color: #FCD34D;
    font-size: 13px;
    margin: 8px 0;
}
.err-box {
    background: #2D0A0A;
    border: 1px solid #7F1D1D;
    border-radius: 8px;
    padding: 12px 16px;
    color: #F87171;
    font-size: 13px;
    margin: 8px 0;
}

/* Divider */
.soft-divider { border: none; border-top: 1px solid #1E2230; margin: 1.5rem 0; }

/* Stbutton override */
.stButton > button {
    background: #1D4ED8 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 0.5rem 1.25rem !important;
    width: 100% !important;
}
.stButton > button:hover { background: #1E40AF !important; }

/* Plotly chart background */
.js-plotly-plot { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "df": None,
    "filename": None,
    "messages": [],
    "charts": [],
    "kpis": [],
    "metric_library": {},
    "validated_metrics": [],
    "ai_plan": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Helpers ───────────────────────────────────────────────────────────────────
PLOTLY_DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#111318",
    plot_bgcolor="#111318",
    font=dict(family="DM Sans, sans-serif", color="#9CA3AF"),
    margin=dict(t=50, l=20, r=20, b=20),
    height=340,
)

def profile_dataframe(df: pd.DataFrame) -> str:
    lines = [f"Dataset: {len(df):,} rows × {len(df.columns)} columns\n\nColumns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = df[col].isna().sum()
        if pd.api.types.is_numeric_dtype(df[col]):
            lines.append(
                f"  {col} [numeric] min={df[col].min():.2f} max={df[col].max():.2f} "
                f"mean={df[col].mean():.2f} nulls={nulls}"
            )
        else:
            uniq = df[col].nunique()
            sample = ", ".join(str(v) for v in df[col].dropna().unique()[:5])
            lines.append(f"  {col} [text/date] {uniq} unique | sample: {sample} | nulls={nulls}")
    return "\n".join(lines)

def load_metric_library(path: str) -> dict:
    try:
        with open(path) as f:
            lib = json.load(f)
        approved = [m for m in lib.get("metrics", []) if m.get("status") == "approved"]
        return {m["name"]: m.get("dax", "") for m in approved}
    except Exception:
        return {}

def validate_against_library(metrics: list, library: dict) -> tuple[list, list]:
    valid, invalid = [], []
    if not library:
        return metrics, []
    for m in metrics:
        (valid if m in library else invalid).append(m)
    return valid, invalid

def call_ai(system_prompt: str, messages: list, ai_mode: str, api_key: str, ollama_model: str) -> str:
    if ai_mode == "Claude API":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        history = [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=history,
        )
        return resp.content[0].text.strip()
    else:
        from openai import OpenAI
        base = "http://localhost:11434/v1" if ai_mode == "Ollama (local)" else "https://api.openai.com/v1"
        key  = "ollama" if ai_mode == "Ollama (local)" else api_key
        client = OpenAI(base_url=base, api_key=key)
        history = [{"role": "system", "content": system_prompt}]
        history += [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = client.chat.completions.create(
            model=ollama_model if ai_mode == "Ollama (local)" else "gpt-4o",
            messages=history,
        )
        return resp.choices[0].message.content.strip()

def parse_json_from_response(text: str) -> dict | None:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None

def build_kpi(label: str, value, prefix="", suffix="", delta=None):
    if isinstance(value, float):
        fmt = f"{prefix}{value:,.4f}{suffix}" if abs(value) < 1 else f"{prefix}{value:,.2f}{suffix}"
    else:
        fmt = f"{prefix}{value:,}{suffix}"
    fig = go.Figure(go.Indicator(
        mode="number+delta" if delta else "number",
        value=float(value),
        delta={"reference": delta} if delta else None,
        title={"text": f"<span style='font-size:12px;color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>{label}</span>"},
        number={"font": {"size": 42, "color": "#F9FAFB", "family": "DM Sans"}},
    ))
    fig.update_layout(**PLOTLY_DARK, height=180)
    return fig

def auto_calculate_metrics(df: pd.DataFrame, metrics: list, library: dict) -> list:
    """Calculate KPI figures from the dataframe based on requested metrics."""
    kpis = []
    num_cols = df.select_dtypes("number").columns.tolist()

    # Map common metric names to dataframe operations
    for metric in metrics:
        m_lower = metric.lower().replace(" ", "_").replace("-", "_")

        # Loss ratio
        if "loss_ratio" in m_lower or "loss ratio" in metric.lower():
            if "claim_amount" in df.columns and "premium" in df.columns:
                val = df["claim_amount"].sum() / df["premium"].sum()
                kpis.append(("Loss Ratio", round(val, 4), "", ""))
            continue

        # Total / sum patterns
        if metric.lower().startswith("total "):
            target = metric.lower().replace("total ", "").replace(" ", "_")
            matches = [c for c in num_cols if target in c.lower()]
            if matches:
                kpis.append((metric, int(df[matches[0]].sum()), "", ""))
            continue

        # Average patterns
        if metric.lower().startswith("avg ") or metric.lower().startswith("average "):
            target = re.sub(r'^(avg|average)\s+', '', metric.lower()).replace(" ", "_")
            matches = [c for c in num_cols if target in c.lower()]
            if matches:
                kpis.append((metric, round(df[matches[0]].mean(), 2), "", ""))
            continue

        # Count patterns
        if metric.lower().startswith("count") or metric.lower() == "total claims":
            kpis.append((metric, len(df), "", " records"))
            continue

        # Generic: try to find a numeric column matching the metric name
        words = [w for w in metric.lower().split() if len(w) > 3]
        for word in words:
            matches = [c for c in num_cols if word in c.lower()]
            if matches:
                kpis.append((metric, round(df[matches[0]].sum(), 2), "", ""))
                break

    # If nothing matched, auto-generate KPIs from numeric columns
    if not kpis:
        for col in num_cols[:4]:
            kpis.append((col.replace("_", " ").title(), round(df[col].sum(), 2), "", ""))

    return kpis

def render_chart_from_plan(df: pd.DataFrame, chart_cfg: dict) -> go.Figure | None:
    ctype = chart_cfg.get("type", "bar").lower()
    x     = chart_cfg.get("x")
    y     = chart_cfg.get("y")
    color = chart_cfg.get("color")
    title = chart_cfg.get("title", "Chart")
    agg   = chart_cfg.get("aggregation", "sum")

    # Validate columns exist
    if x and x not in df.columns:
        return None
    if y and y not in df.columns:
        return None

    plot_df = df.copy()

    # Parse dates
    if x and x in df.columns:
        try:
            plot_df[x] = pd.to_datetime(plot_df[x], dayfirst=True)
        except Exception:
            pass

    # Aggregate
    if x and y:
        group_cols = [c for c in [x, color] if c and c in plot_df.columns]
        if group_cols:
            agg_func = {"sum": "sum", "mean": "mean", "count": "count",
                        "max": "max", "min": "min"}.get(agg, "sum")
            plot_df = plot_df.groupby(group_cols, as_index=False)[y].agg(agg_func)

    kwargs = dict(title=title, color=color if color and color in plot_df.columns else None)

    try:
        if ctype in ("bar", "column"):
            fig = px.bar(plot_df, x=x, y=y, **kwargs)
        elif ctype == "line":
            fig = px.line(plot_df, x=x, y=y, **kwargs)
        elif ctype == "area":
            fig = px.area(plot_df, x=x, y=y, **kwargs)
        elif ctype == "pie":
            fig = px.pie(plot_df, names=x, values=y, title=title)
        elif ctype == "scatter":
            fig = px.scatter(plot_df, x=x, y=y, **kwargs)
        elif ctype == "histogram":
            fig = px.histogram(plot_df, x=x, **kwargs)
        elif ctype == "box":
            fig = px.box(plot_df, x=x, y=y, **kwargs)
        else:
            fig = px.bar(plot_df, x=x, y=y, **kwargs)

        fig.update_layout(**PLOTLY_DARK)
        return fig
    except Exception as e:
        st.warning(f"Could not render '{title}': {e}")
        return None

def build_system_prompt(df: pd.DataFrame, metric_library: dict) -> str:
    profile = profile_dataframe(df)
    metric_section = (
        f"Approved metrics you MUST use:\n{json.dumps(metric_library, indent=2)}\n\n"
        if metric_library
        else "No metric library loaded — you may suggest appropriate metrics based on the data.\n\n"
    )

    return f"""You are an expert data analyst and dashboard-building AI.

The user has uploaded a dataset. Here is its full profile:

{profile}

{metric_section}RULES:
1. Only reference column names that exist in the dataset above.
2. If a metric library is provided, only use metrics from that approved list.
3. Always respond in this exact JSON format — no extra text, no markdown, no backticks:

{{
  "message": "Plain English explanation of what you are building and why.",
  "kpis": [
    {{"label": "Metric name", "column": "column_name", "aggregation": "sum|mean|count|max|min"}}
  ],
  "charts": [
    {{
      "type": "bar|line|area|pie|scatter|histogram|box",
      "title": "Chart title",
      "x": "x_axis_column",
      "y": "y_axis_column",
      "color": "grouping_column or null",
      "aggregation": "sum|mean|count|max|min",
      "description": "One sentence on what this shows."
    }}
  ]
}}

4. Return 2-5 KPIs and 2-4 charts. Choose the most insightful combinations.
5. For time-series columns, prefer line or area charts. For categorical, prefer bar. For distribution, prefer histogram.
6. Output ONLY valid JSON. Nothing else."""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    ai_mode = st.selectbox(
        "AI Engine",
        ["Ollama (local)", "Claude API", "OpenAI"],
        help="Ollama = runs on your machine, no data sent to cloud. Claude/OpenAI = cloud API."
    )

    api_key = ""
    ollama_model = "mistral"

    if ai_mode == "Ollama (local)":
        ollama_model = st.text_input("Ollama model", value="mistral",
            help="Must be pulled via: ollama pull mistral")
        st.markdown('<div class="info-box">🔒 All data stays on your machine. No cloud calls.</div>',
            unsafe_allow_html=True)
    elif ai_mode == "Claude API":
        api_key = st.text_input("Claude API Key", type="password",
            placeholder="sk-ant-...", help="Get from console.anthropic.com")
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")

    st.markdown("---")
    st.markdown("### 📋 Metric Library (optional)")
    metric_file = st.file_uploader("Upload metric_library.json",
        type=["json"],
        help="Your approved metrics JSON. Same format as your colleague's file.")

    if metric_file:
        try:
            lib_data = json.load(metric_file)
            approved = [m for m in lib_data.get("metrics", []) if m.get("status") == "approved"]
            st.session_state.metric_library = {m["name"]: m.get("dax", "") for m in approved}
            st.success(f"{len(st.session_state.metric_library)} approved metrics loaded")
            for name in list(st.session_state.metric_library.keys())[:6]:
                st.markdown(f'<span class="metric-tag">{name}</span>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not read metric library: {e}")

    st.markdown("---")
    st.markdown("### 📅 Date Filter")
    date_filter_enabled = st.checkbox("Filter by date range")
    date_col_filter = None
    date_from = date_to = None
    if date_filter_enabled and st.session_state.df is not None:
        df_cols = st.session_state.df.columns.tolist()
        date_col_filter = st.selectbox("Date column", df_cols)
        date_from = st.date_input("From")
        date_to   = st.date_input("To")

    st.markdown("---")
    if st.button("🗑️ Clear everything"):
        for k in ["df", "filename", "messages", "charts", "kpis", "ai_plan"]:
            st.session_state[k] = None if k == "df" else []
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <p class="dash-title">AI Dashboard Builder</p>
  <p class="dash-sub">Upload any data file · describe what you want · get an interactive report instantly</p>
</div>
""", unsafe_allow_html=True)

# ── File upload ───────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.markdown('<p class="section-title">Upload your data</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed"
    )
    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.session_state.df = df
            st.session_state.filename = uploaded.name
            st.session_state.messages = []
            st.session_state.charts   = []
            st.session_state.kpis     = []
            st.rerun()
        except Exception as e:
            st.error(f"Could not read file: {e}")
    st.stop()

# ── Data loaded ───────────────────────────────────────────────────────────────
df = st.session_state.df.copy()

# Apply date filter if set
if date_filter_enabled and date_col_filter and date_from and date_to:
    try:
        df[date_col_filter] = pd.to_datetime(df[date_col_filter], dayfirst=True)
        df = df[(df[date_col_filter].dt.date >= date_from) &
                (df[date_col_filter].dt.date <= date_to)]
        st.markdown(f'<div class="info-box">📅 Filtered to {date_from} → {date_to} — {len(df):,} rows</div>',
            unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Date filter error: {e}")

# ── Dataset summary strip ─────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
num_cols = df.select_dtypes("number").columns.tolist()
cat_cols = df.select_dtypes("object").columns.tolist()
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">File</div>'
                f'<div class="kpi-value" style="font-size:1rem">{st.session_state.filename}</div></div>',
                unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Rows</div>'
                f'<div class="kpi-value">{len(df):,}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Numeric cols</div>'
                f'<div class="kpi-value">{len(num_cols)}</div>'
                f'<div class="kpi-sub">{", ".join(num_cols[:3])}{"…" if len(num_cols)>3 else ""}</div></div>',
                unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">Category cols</div>'
                f'<div class="kpi-value">{len(cat_cols)}</div>'
                f'<div class="kpi-sub">{", ".join(cat_cols[:3])}{"…" if len(cat_cols)>3 else ""}</div></div>',
                unsafe_allow_html=True)

st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ── Render existing dashboard ─────────────────────────────────────────────────
if st.session_state.kpis:
    st.markdown('<p class="section-title">Key metrics</p>', unsafe_allow_html=True)
    kpi_cols = st.columns(len(st.session_state.kpis))
    for i, (label, value, prefix, suffix) in enumerate(st.session_state.kpis):
        with kpi_cols[i]:
            fig = build_kpi(label, value, prefix, suffix)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

if st.session_state.charts:
    st.markdown('<p class="section-title">Charts</p>', unsafe_allow_html=True)
    charts = st.session_state.charts
    for i in range(0, len(charts), 2):
        cols = st.columns(2)
        for j, cfg in enumerate(charts[i:i+2]):
            with cols[j]:
                fig = render_chart_from_plan(df, cfg)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(cfg.get("description", ""))

if st.session_state.kpis or st.session_state.charts:
    st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown('<p class="section-title">Conversation</p>', unsafe_allow_html=True)
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(
                f'<div class="chat-user"><div class="chat-label user">You</div>{m["content"]}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="chat-ai"><div class="chat-label ai">AI Agent</div>{m["content"]}</div>',
                unsafe_allow_html=True)

# ── Quick prompts ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">Ask the AI agent</p>', unsafe_allow_html=True)

quick_prompts = [
    "Build me a full dashboard overview",
    "Show top 5 categories by value",
    "Show trends over time",
    "Compare performance by region or category",
    "Show distribution of numeric columns",
]

cols = st.columns(len(quick_prompts))
for i, qp in enumerate(quick_prompts):
    with cols[i]:
        if st.button(qp, key=f"qp_{i}"):
            st.session_state["_pending"] = qp

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    "e.g. 'Show Loss Ratio and Total Claims by state' or 'Add a monthly trend chart'"
)
prompt = st.session_state.pop("_pending", None) or user_input

if prompt:
    # Check AI is configured
    if ai_mode != "Ollama (local)" and not api_key:
        st.markdown(
            '<div class="err-box">⚠️ Please enter your API key in the sidebar.</div>',
            unsafe_allow_html=True)
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Agent is analysing your data and building charts..."):
        try:
            system_prompt = build_system_prompt(df, st.session_state.metric_library)
            raw = call_ai(system_prompt, st.session_state.messages, ai_mode, api_key, ollama_model)
            plan = parse_json_from_response(raw)

            if not plan:
                st.markdown(
                    '<div class="warn-box">⚠️ AI returned an unexpected format. Try rephrasing your request.</div>',
                    unsafe_allow_html=True)
                st.stop()

            ai_message = plan.get("message", "Here is your dashboard.")

            # Validate metrics if library loaded
            requested_metrics = [k.get("label", "") for k in plan.get("kpis", [])]
            if st.session_state.metric_library and requested_metrics:
                valid, invalid = validate_against_library(
                    requested_metrics, st.session_state.metric_library)
                if invalid:
                    ai_message += f"\n\n⚠️ Skipped non-approved metrics: {', '.join(invalid)}"

            # Store results
            kpis = auto_calculate_metrics(df, requested_metrics, st.session_state.metric_library)
            new_charts = plan.get("charts", [])

            st.session_state.messages.append({"role": "assistant", "content": ai_message})

            # Full rebuild on dashboard/overview requests, else append
            is_rebuild = any(kw in prompt.lower() for kw in
                ["dashboard", "overview", "full", "start over", "rebuild", "clear"])
            if is_rebuild:
                st.session_state.kpis   = kpis
                st.session_state.charts = new_charts
            else:
                if kpis:   st.session_state.kpis   = kpis
                if new_charts: st.session_state.charts.extend(new_charts)

            st.session_state.ai_plan = plan
            st.rerun()

        except Exception as e:
            st.markdown(
                f'<div class="err-box">❌ Error: {e}<br>Check your API key and that Ollama is running if using local mode.</div>',
                unsafe_allow_html=True)

# ── Data preview ──────────────────────────────────────────────────────────────
with st.expander("🔍 Preview raw data"):
    st.dataframe(df.head(100), use_container_width=True)

if st.session_state.ai_plan:
    with st.expander("🤖 Last AI plan (JSON)"):
        st.json(st.session_state.ai_plan)
