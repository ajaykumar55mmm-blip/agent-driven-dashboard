import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json, re, os, io
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="InsightFlow", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ── Built-in themes ────────────────────────────────────────────────────────────
THEMES = {
    "Midnight Navy": {
        "bg":"#0A0F1E","surface":"#111827","surface2":"#1F2937","border":"#374151",
        "text":"#F9FAFB","text2":"#9CA3AF","accent":"#3B82F6","accent2":"#10B981",
        "accent3":"#F59E0B","danger":"#EF4444",
        "chart_colors":["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#EC4899","#06B6D4","#84CC16"],
        "plotly_template":"plotly_dark","paper_bg":"#111827","plot_bg":"#1F2937"
    },
    "Executive Slate": {
        "bg":"#F1F5F9","surface":"#FFFFFF","surface2":"#F8FAFC","border":"#E2E8F0",
        "text":"#0F172A","text2":"#64748B","accent":"#1E40AF","accent2":"#059669",
        "accent3":"#D97706","danger":"#DC2626",
        "chart_colors":["#1E40AF","#059669","#D97706","#DC2626","#7C3AED","#DB2777","#0891B2","#65A30D"],
        "plotly_template":"plotly_white","paper_bg":"#FFFFFF","plot_bg":"#F8FAFC"
    },
    "Charcoal Pro": {
        "bg":"#1C1C1E","surface":"#2C2C2E","surface2":"#3A3A3C","border":"#48484A",
        "text":"#FFFFFF","text2":"#AEAEB2","accent":"#0A84FF","accent2":"#30D158",
        "accent3":"#FFD60A","danger":"#FF453A",
        "chart_colors":["#0A84FF","#30D158","#FFD60A","#FF453A","#BF5AF2","#FF375F","#5AC8FA","#ACE400"],
        "plotly_template":"plotly_dark","paper_bg":"#2C2C2E","plot_bg":"#3A3A3C"
    },
    "Teal Corporate": {
        "bg":"#F0FDFA","surface":"#FFFFFF","surface2":"#F0FDFA","border":"#99F6E4",
        "text":"#134E4A","text2":"#0F766E","accent":"#0D9488","accent2":"#0369A1",
        "accent3":"#CA8A04","danger":"#DC2626",
        "chart_colors":["#0D9488","#0369A1","#CA8A04","#DC2626","#7C3AED","#DB2777","#0891B2","#65A30D"],
        "plotly_template":"plotly_white","paper_bg":"#FFFFFF","plot_bg":"#F0FDFA"
    },
    "Crimson Finance": {
        "bg":"#0F0A1E","surface":"#1A1030","surface2":"#241845","border":"#3D2E6B",
        "text":"#FAFAFA","text2":"#A78BFA","accent":"#E11D48","accent2":"#7C3AED",
        "accent3":"#F59E0B","danger":"#EF4444",
        "chart_colors":["#E11D48","#7C3AED","#F59E0B","#10B981","#3B82F6","#EC4899","#06B6D4","#84CC16"],
        "plotly_template":"plotly_dark","paper_bg":"#1A1030","plot_bg":"#241845"
    },
    "Custom": {
        "bg":"#0A0F1E","surface":"#111827","surface2":"#1F2937","border":"#374151",
        "text":"#F9FAFB","text2":"#9CA3AF","accent":"#3B82F6","accent2":"#10B981",
        "accent3":"#F59E0B","danger":"#EF4444",
        "chart_colors":["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#EC4899","#06B6D4","#84CC16"],
        "plotly_template":"plotly_dark","paper_bg":"#111827","plot_bg":"#1F2937"
    },
}

ALL_CHART_TYPES = [
    "bar","line","area","pie","donut","scatter","bubble",
    "histogram","box","violin","heatmap","treemap","sunburst",
    "funnel","waterfall","gauge","radar","strip","density"
]

# ── Session state ──────────────────────────────────────────────────────────────
DEFAULTS = {
    "datasets":{}, "pages":[], "active_page":0,
    "theme":"Midnight Navy", "custom_theme":{},
    "messages":[], "metric_library":{},
    "global_filters":{},   # cross-page synced filters
    "dashboard_built":False,
}
for k,v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

# Merge custom theme into base
T = dict(THEMES[st.session_state.theme])
if st.session_state.theme == "Custom" and st.session_state.custom_theme:
    T.update(st.session_state.custom_theme)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{{font-family:'Plus Jakarta Sans',sans-serif;background:{T['bg']} !important;color:{T['text']};}}
.stApp{{background:{T['bg']} !important;}}
[data-testid="stSidebar"]{{background:{T['surface']} !important;border-right:1px solid {T['border']};}}
.kpi-card{{background:{T['surface']};border:1px solid {T['border']};border-radius:12px;padding:1.2rem;position:relative;overflow:hidden;transition:transform 0.2s;margin-bottom:8px;}}
.kpi-card:hover{{transform:translateY(-2px);}}
.kpi-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{T['accent']},{T['accent2']});}}
.kpi-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{T['text2']};margin-bottom:8px;}}
.kpi-value{{font-size:1.8rem;font-weight:700;color:{T['text']};letter-spacing:-0.03em;line-height:1;}}
.chart-title{{font-size:13px;font-weight:600;color:{T['text']};margin-bottom:0.5rem;padding-bottom:0.5rem;border-bottom:1px solid {T['border']};}}
.page-tab{{padding:6px 18px;border-radius:20px;border:1px solid {T['border']};background:{T['surface']};color:{T['text2']};cursor:pointer;font-size:12px;font-weight:500;display:inline-block;margin:2px;}}
.page-tab.active{{background:{T['accent']};border-color:{T['accent']};color:white;font-weight:600;}}
.section-label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{T['text2']};margin:1rem 0 0.5rem;padding-bottom:4px;border-bottom:1px solid {T['border']};}}
.chat-user{{background:{T['surface2']};border:1px solid {T['border']};border-left:3px solid {T['accent']};border-radius:8px;padding:10px 14px;margin:6px 0;color:{T['text']};font-size:13px;}}
.chat-ai{{background:{T['surface']};border:1px solid {T['border']};border-left:3px solid {T['accent2']};border-radius:8px;padding:10px 14px;margin:6px 0;color:{T['text2']};font-size:13px;}}
.info-box{{background:{T['surface2']};border:1px solid {T['accent']};border-radius:8px;padding:10px 14px;color:{T['text2']};font-size:12px;margin:6px 0;}}
.warn-box{{background:{T['surface2']};border:1px solid {T['accent3']};border-radius:8px;padding:10px 14px;color:{T['accent3']};font-size:12px;margin:6px 0;}}
.err-box{{background:{T['surface2']};border:1px solid {T['danger']};border-radius:8px;padding:10px 14px;color:{T['danger']};font-size:12px;margin:6px 0;}}
.global-filter-bar{{background:{T['surface']};border:1px solid {T['accent']};border-radius:10px;padding:12px 16px;margin-bottom:1rem;}}
.global-filter-title{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{T['accent']};margin-bottom:8px;}}
.stButton>button{{background:{T['accent']} !important;color:white !important;border:none !important;border-radius:8px !important;font-family:'Plus Jakarta Sans',sans-serif !important;font-weight:600 !important;font-size:12px !important;padding:0.45rem 1rem !important;width:100% !important;}}
.stButton>button:hover{{opacity:0.85 !important;}}
hr.soft{{border:none;border-top:1px solid {T['border']};margin:1rem 0;}}
</style>
""", unsafe_allow_html=True)

# ── Chart rendering ────────────────────────────────────────────────────────────
def plotly_theme(height=380, bg=None, plot_bg=None, custom_colors=None):
    colors = custom_colors or T["chart_colors"]
    return dict(
        template=T["plotly_template"],
        paper_bgcolor=bg or T["paper_bg"],
        plot_bgcolor=plot_bg or T["plot_bg"],
        font=dict(family="Plus Jakarta Sans, sans-serif", color=T["text2"], size=11),
        margin=dict(t=40, l=10, r=10, b=30),
        height=height,
        colorway=colors,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=T["text2"])),
    )

def apply_filters_to_df(df, global_filters, page_filters):
    df = df.copy()
    all_filters = {**global_filters, **page_filters}
    for col, val in all_filters.items():
        if col not in df.columns or not val: continue
        if isinstance(val, list) and val:
            df = df[df[col].isin(val)]
        elif isinstance(val, tuple) and len(val)==2:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df = df[(df[col]>=val[0]) & (df[col]<=val[1])]
            except: pass
    return df

def render_chart(cfg, df, global_filters={}, page_filters={}, override_colors=None):
    ctype   = cfg.get("type","bar").lower()
    x       = cfg.get("x")
    y       = cfg.get("y")
    color   = cfg.get("color")
    title   = cfg.get("title","")
    agg     = cfg.get("aggregation","sum")
    height  = cfg.get("height", 350)
    cscheme = cfg.get("color_scheme","")
    custom_color = cfg.get("custom_color")  # single override color
    bg_color     = cfg.get("bg_color")
    plot_bg_col  = cfg.get("plot_bg_color")

    # Validate columns
    if x and x not in df.columns: x = None
    if y and y not in df.columns: y = None
    if color and color not in df.columns: color = None

    plot_df = apply_filters_to_df(df, global_filters, page_filters)

    # Parse dates
    if x and x in plot_df.columns:
        try: plot_df[x] = pd.to_datetime(plot_df[x], dayfirst=True)
        except: pass

    # Aggregate
    if x and y and x in plot_df.columns and y in plot_df.columns:
        group_cols = [c for c in [x, color] if c and c in plot_df.columns]
        if group_cols:
            try:
                agg_func = {"sum":"sum","mean":"mean","count":"count","max":"max","min":"min"}.get(agg,"sum")
                plot_df = plot_df.groupby(group_cols, as_index=False)[y].agg(agg_func)
            except: pass

    # Color setup
    colors = override_colors or T["chart_colors"]
    if custom_color: colors = [custom_color] * 20
    scale_map = {"blues":"Blues","greens":"Greens","reds":"Reds","purples":"Purples","oranges":"Oranges","teal":"Teal","viridis":"Viridis","plasma":"Plasma","turbo":"Turbo"}
    cscale = scale_map.get(cscheme, "Blues")

    theme = plotly_theme(height, bg=bg_color, plot_bg=plot_bg_col, custom_colors=colors)
    kw = dict(color=color if color else None)

    try:
        if ctype == "bar":
            fig = px.bar(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "line":
            fig = px.line(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "area":
            fig = px.area(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "pie":
            fig = px.pie(plot_df, names=x, values=y, title=title, color_discrete_sequence=colors)
        elif ctype == "donut":
            fig = px.pie(plot_df, names=x, values=y, title=title, hole=0.5, color_discrete_sequence=colors)
        elif ctype == "scatter":
            fig = px.scatter(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "bubble":
            size_col = [c for c in plot_df.select_dtypes("number").columns if c not in [x,y,color]]
            sz = size_col[0] if size_col else None
            fig = px.scatter(plot_df, x=x, y=y, size=sz, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "histogram":
            fig = px.histogram(plot_df, x=x, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "box":
            fig = px.box(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "violin":
            fig = px.violin(plot_df, x=x, y=y, title=title, box=True, **kw, color_discrete_sequence=colors)
        elif ctype == "strip":
            fig = px.strip(plot_df, x=x, y=y, title=title, **kw, color_discrete_sequence=colors)
        elif ctype == "heatmap":
            if x and y and color and color in plot_df.columns:
                pivot = plot_df.pivot_table(index=x, columns=color, values=y, aggfunc=agg)
                fig = px.imshow(pivot, title=title, color_continuous_scale=cscale)
            else:
                corr = plot_df.select_dtypes("number").corr()
                fig = px.imshow(corr, title=title or "Correlation Heatmap", color_continuous_scale=cscale)
        elif ctype == "treemap":
            path = [c for c in [color, x] if c and c in plot_df.columns]
            if path and y:
                fig = px.treemap(plot_df, path=path, values=y, title=title, color_discrete_sequence=colors)
            else:
                fig = px.bar(plot_df, x=x, y=y, title=title, color_discrete_sequence=colors)
        elif ctype == "sunburst":
            path = [c for c in [color, x] if c and c in plot_df.columns]
            if path and y:
                fig = px.sunburst(plot_df, path=path, values=y, title=title, color_discrete_sequence=colors)
            else:
                fig = px.pie(plot_df, names=x, values=y, title=title, color_discrete_sequence=colors)
        elif ctype == "funnel":
            fig = px.funnel(plot_df, x=y, y=x, title=title, color_discrete_sequence=colors)
        elif ctype == "waterfall":
            fig = go.Figure(go.Waterfall(
                x=plot_df[x].tolist() if x else [],
                y=plot_df[y].tolist() if y else [],
                name=title,
                connector={"line":{"color":colors[0]}},
                increasing={"marker":{"color":colors[1] if len(colors)>1 else "#10B981"}},
                decreasing={"marker":{"color":colors[3] if len(colors)>3 else "#EF4444"}},
            ))
            fig.update_layout(title=title)
        elif ctype == "gauge":
            val = float(plot_df[y].mean()) if y and y in plot_df.columns else 0
            max_val = float(plot_df[y].max()) if y and y in plot_df.columns else 100
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=val,
                title={"text": title},
                gauge={"axis":{"range":[0,max_val]},"bar":{"color":colors[0]},
                       "steps":[{"range":[0,max_val*0.5],"color":T["surface2"]},
                                 {"range":[max_val*0.5,max_val*0.8],"color":T["border"]}],
                       "threshold":{"line":{"color":colors[3] if len(colors)>3 else "red","width":4},"thickness":0.75,"value":max_val*0.9}}
            ))
        elif ctype == "radar":
            num_cols = plot_df.select_dtypes("number").columns.tolist()[:6]
            if num_cols:
                vals = [plot_df[c].mean() for c in num_cols]
                fig = go.Figure(go.Scatterpolar(r=vals, theta=num_cols, fill='toself', line_color=colors[0]))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
                fig.update_layout(title=title)
            else:
                fig = px.bar(plot_df, x=x, y=y, title=title, color_discrete_sequence=colors)
        elif ctype == "density":
            fig = px.density_contour(plot_df, x=x, y=y, title=title, color_discrete_sequence=colors)
        else:
            fig = px.bar(plot_df, x=x, y=y, title=title, color_discrete_sequence=colors)

        fig.update_layout(**theme)
        return fig
    except Exception as e:
        st.error(f"Chart error ({title}): {e}")
        return None

def calc_kpi(kpi_cfg, df):
    col  = kpi_cfg.get("column","")
    agg  = kpi_cfg.get("aggregation","sum")
    label= kpi_cfg.get("label", col)
    pre  = kpi_cfg.get("prefix","")
    suf  = kpi_cfg.get("suffix","")
    if col not in df.columns:
        matches = [c for c in df.select_dtypes("number").columns if any(w in c.lower() for w in col.lower().split() if len(w)>2)]
        if matches: col = matches[0]
        else: return (label,0,pre,suf)
    try:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return (label, df[col].nunique(), "", " unique")
        val = {"sum":df[col].sum(),"mean":df[col].mean(),"count":len(df),"max":df[col].max(),"min":df[col].min()}.get(agg, df[col].sum())
        return (label, round(float(val),2), pre, suf)
    except:
        return (label,0,pre,suf)

def fmt_val(v, pre="", suf=""):
    if abs(v)>=1_000_000: return f"{pre}{v/1_000_000:.1f}M{suf}"
    elif abs(v)>=1_000:   return f"{pre}{v/1_000:.1f}K{suf}"
    elif isinstance(v,float) and abs(v)<100: return f"{pre}{v:.3f}{suf}"
    else: return f"{pre}{v:,.0f}{suf}"

def profile_df(df):
    lines = [f"Dataset: {len(df):,} rows x {len(df.columns)} columns\n\nColumns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = df[col].isna().sum()
        if pd.api.types.is_numeric_dtype(df[col]):
            lines.append(f"  {col} [numeric] min={df[col].min():.2f} max={df[col].max():.2f} mean={df[col].mean():.2f} nulls={nulls}")
        else:
            uniq = df[col].nunique()
            sample = ", ".join(str(v) for v in df[col].dropna().unique()[:5])
            lines.append(f"  {col} [text/date] {uniq} unique | sample: {sample} | nulls={nulls}")
    return "\n".join(lines)

def call_ai(system_prompt, messages, ai_mode, api_key, ollama_model):
    history = [{"role":m["role"],"content":m["content"]} for m in messages]
    if ai_mode == "Claude API":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=4000, system=system_prompt, messages=history)
        return resp.content[0].text.strip()
    else:
        from openai import OpenAI
        base = "http://localhost:11434/v1" if ai_mode=="Ollama (local)" else "https://api.openai.com/v1"
        key  = "ollama" if ai_mode=="Ollama (local)" else api_key
        client = OpenAI(base_url=base, api_key=key)
        msgs = [{"role":"system","content":system_prompt}] + history
        resp = client.chat.completions.create(model=ollama_model if ai_mode=="Ollama (local)" else "gpt-4o", messages=msgs, timeout=120)
        return resp.choices[0].message.content.strip()

def parse_json(text):
    text = re.sub(r'^```(?:json)?\s*','',text.strip())
    text = re.sub(r'\s*```$','',text.strip())
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    try: return json.loads(text)
    except: return None

def build_system_prompt():
    profiles = []
    for name, df in st.session_state.datasets.items():
        profiles.append(f"=== {name} ===\n{profile_df(df)}")
    metric_section = ""
    if st.session_state.metric_library:
        metric_section = f"\nApproved metrics (USE ONLY THESE):\n{json.dumps(st.session_state.metric_library,indent=2)}\n"
    return f"""You are an expert data analyst and professional dashboard designer AI.
Available datasets:
{"".join(profiles)}
{metric_section}

Build professional Power BI-style dashboards. Respond ONLY in this exact JSON:
{{
  "message": "Brief description.",
  "pages": [
    {{
      "name": "Page name",
      "heading": "Dashboard heading",
      "heading_color": "#hex",
      "kpis": [
        {{"label":"KPI","column":"col","aggregation":"sum|mean|count|max|min","dataset":"name","prefix":"$","suffix":""}}
      ],
      "charts": [
        {{
          "type": "bar|line|area|pie|donut|scatter|bubble|histogram|box|violin|heatmap|treemap|sunburst|funnel|waterfall|gauge|radar|strip|density",
          "title":"Chart title","x":"col","y":"col","color":"col or null",
          "aggregation":"sum","dataset":"name","description":"What this shows.",
          "width":"full|half|third","height":350,"color_scheme":"blues|greens|reds|purples|viridis|plasma"
        }}
      ],
      "slicers": [
        {{"column":"col","dataset":"name","type":"multiselect|date_range|slider","global":true}}
      ]
    }}
  ]
}}
RULES: Only use columns that exist. Create 1-4 pages. Mix chart types — never all same. Make it BEAUTIFUL and PROFESSIONAL. Output ONLY valid JSON."""

def get_df_for(cfg):
    ds = cfg.get("dataset","")
    if ds in st.session_state.datasets: return st.session_state.datasets[ds]
    if st.session_state.datasets: return list(st.session_state.datasets.values())[0]
    return None

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<p style="font-size:1.1rem;font-weight:700;color:{T["text"]}">⚡ InsightFlow</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:11px;color:{T["text2"]};margin-top:-8px">AI Dashboard Builder</p>', unsafe_allow_html=True)
    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ── Theme ──────────────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Theme</p>', unsafe_allow_html=True)
    new_theme = st.selectbox("Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme), label_visibility="collapsed")
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    # ── Full dashboard custom colors ───────────────────────────────────────────
    with st.expander("🎨 Customise dashboard colors"):
        st.markdown(f'<p style="font-size:11px;color:{T["text2"]}">Override any color across the entire dashboard</p>', unsafe_allow_html=True)
        ct = st.session_state.custom_theme if st.session_state.theme == "Custom" else {}

        c1,c2 = st.columns(2)
        new_bg      = c1.color_picker("Background",    ct.get("bg",      T["bg"]),      key="cp_bg")
        new_surface = c2.color_picker("Card surface",  ct.get("surface", T["surface"]), key="cp_surface")
        new_text    = c1.color_picker("Text",          ct.get("text",    T["text"]),    key="cp_text")
        new_text2   = c2.color_picker("Subtitle text", ct.get("text2",   T["text2"]),   key="cp_text2")
        new_accent  = c1.color_picker("Accent (btns)", ct.get("accent",  T["accent"]),  key="cp_accent")
        new_accent2 = c2.color_picker("Accent 2 (KPI bar)", ct.get("accent2", T["accent2"]), key="cp_accent2")
        new_border  = c1.color_picker("Borders",       ct.get("border",  T["border"]),  key="cp_border")
        new_paper   = c2.color_picker("Chart bg",      ct.get("paper_bg",T["paper_bg"]),key="cp_paper")

        st.markdown("**Chart color palette** (click each to change)")
        base_colors = ct.get("chart_colors", T["chart_colors"])
        new_chart_colors = []
        pc_cols = st.columns(4)
        for ci in range(8):
            with pc_cols[ci % 4]:
                nc = st.color_picker(f"Color {ci+1}", base_colors[ci] if ci < len(base_colors) else "#888888", key=f"cp_chart_{ci}")
                new_chart_colors.append(nc)

        if st.button("Apply custom theme"):
            st.session_state.theme = "Custom"
            st.session_state.custom_theme = {
                "bg": new_bg, "surface": new_surface, "surface2": new_surface,
                "text": new_text, "text2": new_text2, "accent": new_accent,
                "accent2": new_accent2, "border": new_border,
                "paper_bg": new_paper, "plot_bg": new_paper,
                "chart_colors": new_chart_colors,
                "plotly_template": "plotly_dark" if new_bg < "#888888" else "plotly_white",
            }
            st.rerun()

        if st.button("Reset to theme defaults"):
            st.session_state.custom_theme = {}
            st.session_state.theme = "Midnight Navy"
            st.rerun()

    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ── AI engine ──────────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">AI Engine</p>', unsafe_allow_html=True)
    ai_mode = st.selectbox("AI Engine", ["Ollama (local)","Claude API","OpenAI"], label_visibility="collapsed")
    api_key = ""; ollama_model = "mistral"
    if ai_mode == "Ollama (local)":
        ollama_model = st.text_input("Model", value="mistral", label_visibility="collapsed")
        st.markdown(f'<div class="info-box">🔒 All data stays on your machine.</div>', unsafe_allow_html=True)
    elif ai_mode == "Claude API":
        api_key = st.text_input("Claude API Key", type="password", placeholder="sk-ant-...", label_visibility="collapsed")
    else:
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", label_visibility="collapsed")

    st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ── File uploads ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Data Files</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload CSV or Excel files", type=["csv","xlsx","xls"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        for f in uploaded:
            if f.name not in st.session_state.datasets:
                try:
                    df = pd.read_csv(f, low_memory=False) if f.name.endswith(".csv") else pd.read_excel(f)
                    st.session_state.datasets[f.name] = df
                    st.success(f"✓ {f.name} ({len(df):,} rows)")
                except Exception as e:
                    st.error(f"Error: {f.name} — {e}")

    if st.session_state.datasets:
        for name, df in st.session_state.datasets.items():
            st.markdown(f'<div class="info-box">📊 <b>{name}</b><br>{len(df):,} rows · {len(df.columns)} cols</div>', unsafe_allow_html=True)
        if st.button("🗑 Remove all datasets"):
            st.session_state.datasets={}; st.session_state.pages=[]; st.session_state.dashboard_built=False; st.rerun()

    # ── Metric library ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-label">Metric Library</p>', unsafe_allow_html=True)
    mf = st.file_uploader("metric_library.json", type=["json"], label_visibility="collapsed")
    if mf:
        try:
            lib = json.load(mf)
            approved = [m for m in lib.get("metrics",[]) if m.get("status")=="approved"]
            st.session_state.metric_library = {m["name"]: m.get("dax","") for m in approved}
            st.success(f"{len(st.session_state.metric_library)} approved metrics")
        except Exception as e: st.error(str(e))

    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    if st.button("🗑 Clear dashboard & chat"):
        st.session_state.pages=[]; st.session_state.messages=[]; st.session_state.dashboard_built=False; st.session_state.global_filters={}; st.rerun()

# ── MAIN ───────────────────────────────────────────────────────────────────────
if not st.session_state.datasets:
    st.markdown(f"""<div style="text-align:center;padding:5rem 2rem;">
      <p style="font-size:3.5rem;margin-bottom:0.5rem">📊</p>
      <p style="font-size:1.8rem;font-weight:700;color:{T['text']};margin-bottom:0.5rem">InsightFlow</p>
      <p style="color:{T['text2']};font-size:0.95rem">Upload your CSV or Excel files in the sidebar to get started.<br>You can upload multiple files at once.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

pages = st.session_state.pages
active_idx = st.session_state.active_page

# ── Heading ────────────────────────────────────────────────────────────────────
heading = pages[active_idx].get("heading","Dashboard") if pages and active_idx < len(pages) else "InsightFlow Dashboard"
h_color = pages[active_idx].get("heading_color", T["text"]) if pages and active_idx < len(pages) else T["text"]

hc1, hc2, hc3 = st.columns([4,1,1])
with hc1:
    new_heading = st.text_input("Title", value=heading, label_visibility="collapsed", placeholder="Dashboard title...")
    if new_heading != heading and pages and active_idx < len(pages):
        pages[active_idx]["heading"] = new_heading; st.session_state.pages = pages
with hc2:
    new_h_color = st.color_picker("Title color", value=h_color, label_visibility="collapsed")
    if new_h_color != h_color and pages and active_idx < len(pages):
        pages[active_idx]["heading_color"] = new_h_color; st.session_state.pages = pages
with hc3:
    st.markdown(f'<div style="text-align:right;color:{T["text2"]};font-size:11px;padding-top:10px">{len(st.session_state.datasets)} file(s) loaded</div>', unsafe_allow_html=True)

st.markdown(f'<h1 style="font-size:1.9rem;font-weight:700;color:{new_h_color};letter-spacing:-0.03em;margin:0.2rem 0 1rem">{new_heading}</h1>', unsafe_allow_html=True)

# ── Page navigation tabs ───────────────────────────────────────────────────────
if pages:
    tab_html = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:1rem;">'
    for i, pg in enumerate(pages):
        active_cls = f"background:{T['accent']};border-color:{T['accent']};color:white;font-weight:600;" if i==active_idx else f"background:{T['surface']};border-color:{T['border']};color:{T['text2']};"
        tab_html += f'<span style="padding:6px 18px;border-radius:20px;border:1px solid;cursor:pointer;font-size:12px;font-family:Plus Jakarta Sans,sans-serif;{active_cls}">{pg.get("name","Page "+str(i+1))}</span>'
    tab_html += '</div>'
    st.markdown(tab_html, unsafe_allow_html=True)

    page_names = [pg.get("name",f"Page {i+1}") for i,pg in enumerate(pages)]
    sel = st.selectbox("Page", page_names, index=active_idx, label_visibility="collapsed")
    new_idx = page_names.index(sel)
    if new_idx != active_idx:
        st.session_state.active_page = new_idx; st.rerun()

# ── GLOBAL FILTERS (synced across all pages) ───────────────────────────────────
all_cols_by_ds = {}
for ds_name, df in st.session_state.datasets.items():
    for col in df.columns:
        if col not in all_cols_by_ds:
            all_cols_by_ds[col] = ds_name

# Collect global slicer columns from all pages
global_slicer_cols = []
for pg in pages:
    for sl in pg.get("slicers", []):
        if sl.get("global", False) and sl.get("column") not in global_slicer_cols:
            global_slicer_cols.append(sl.get("column"))

if global_slicer_cols:
    st.markdown(f'<div class="global-filter-title">🌐 Global Filters — applied across all pages & visuals</div>', unsafe_allow_html=True)
    gf_cols = st.columns(min(len(global_slicer_cols), 4))
    for gi, gcol in enumerate(global_slicer_cols):
        ds_name = all_cols_by_ds.get(gcol, "")
        df_g = st.session_state.datasets.get(ds_name, list(st.session_state.datasets.values())[0])
        if gcol not in df_g.columns: continue
        with gf_cols[gi % 4]:
            if pd.api.types.is_numeric_dtype(df_g[gcol]):
                mn, mx = float(df_g[gcol].min()), float(df_g[gcol].max())
                gvals = st.slider(f"🌐 {gcol}", mn, mx, (mn, mx), key=f"gf_slider_{gcol}")
                st.session_state.global_filters[gcol] = gvals
            else:
                opts = sorted(df_g[gcol].dropna().unique().tolist())
                gsel = st.multiselect(f"🌐 {gcol}", opts, default=[], key=f"gf_ms_{gcol}")
                if gsel: st.session_state.global_filters[gcol] = gsel
                elif gcol in st.session_state.global_filters: del st.session_state.global_filters[gcol]
    st.markdown('<hr class="soft">', unsafe_allow_html=True)

# ── Add global filter manually ─────────────────────────────────────────────────
with st.expander("➕ Add global filter (synced across all pages)"):
    ac1, ac2 = st.columns([3,1])
    add_gcol = ac1.selectbox("Choose column", list(all_cols_by_ds.keys()), key="add_gcol")
    if ac2.button("Add as global filter", key="add_gf_btn"):
        ds_for_col = all_cols_by_ds.get(add_gcol,"")
        for pi, pg in enumerate(pages):
            if "slicers" not in pages[pi]: pages[pi]["slicers"] = []
            # Avoid duplicates
            existing = [s.get("column") for s in pages[pi]["slicers"]]
            if add_gcol not in existing:
                pages[pi]["slicers"].append({"column":add_gcol,"dataset":ds_for_col,"type":"multiselect","global":True})
        st.session_state.pages = pages
        st.rerun()

# ── Render active page ─────────────────────────────────────────────────────────
if pages and active_idx < len(pages):
    page = pages[active_idx]
    page_filters = {}

    # ── Page-level slicers (non-global) ───────────────────────────────────────
    local_slicers = [s for s in page.get("slicers",[]) if not s.get("global",False)]
    if local_slicers:
        st.markdown(f'<p class="section-label">Page Filters</p>', unsafe_allow_html=True)
        sl_cols = st.columns(min(len(local_slicers),4))
        for si, sl in enumerate(local_slicers):
            col   = sl.get("column","")
            stype = sl.get("type","multiselect")
            ds_n  = sl.get("dataset","")
            df_sl = st.session_state.datasets.get(ds_n, list(st.session_state.datasets.values())[0])
            if col not in df_sl.columns: continue
            with sl_cols[si % 4]:
                if stype == "multiselect":
                    opts = sorted(df_sl[col].dropna().unique().tolist())
                    sel_vals = st.multiselect(col, opts, default=[], key=f"sl_{active_idx}_{si}")
                    if sel_vals: page_filters[col] = sel_vals
                elif stype == "date_range":
                    try:
                        df_sl[col] = pd.to_datetime(df_sl[col], dayfirst=True)
                        df = st.date_input(f"{col} from", df_sl[col].min().date(), key=f"sld1_{active_idx}_{si}")
                        dt = st.date_input(f"{col} to",   df_sl[col].max().date(), key=f"sld2_{active_idx}_{si}")
                        page_filters[col] = (df, dt)
                    except: pass
                elif stype == "slider":
                    try:
                        mn, mx = float(df_sl[col].min()), float(df_sl[col].max())
                        sv = st.slider(col, mn, mx, (mn,mx), key=f"slsl_{active_idx}_{si}")
                        page_filters[col] = sv
                    except: pass
        st.markdown('<hr class="soft">', unsafe_allow_html=True)

    # ── Add page-level slicer ─────────────────────────────────────────────────
    with st.expander("➕ Add page filter (this page only)"):
        pc1, pc2, pc3 = st.columns([2,2,1])
        pf_col  = pc1.selectbox("Column", list(all_cols_by_ds.keys()), key="pf_col")
        pf_type = pc2.selectbox("Type", ["multiselect","slider","date_range"], key="pf_type")
        if pc3.button("Add", key="add_pf"):
            if "slicers" not in pages[active_idx]: pages[active_idx]["slicers"] = []
            pages[active_idx]["slicers"].append({"column":pf_col,"dataset":all_cols_by_ds.get(pf_col,""),"type":pf_type,"global":False})
            st.session_state.pages = pages; st.rerun()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpis = page.get("kpis",[])
    if kpis:
        st.markdown(f'<p class="section-label">Key Metrics</p>', unsafe_allow_html=True)
        kpi_cols = st.columns(min(len(kpis),5))
        for ki, kc in enumerate(kpis):
            df_k = st.session_state.datasets.get(kc.get("dataset",""), list(st.session_state.datasets.values())[0])
            df_k_f = apply_filters_to_df(df_k, st.session_state.global_filters, page_filters)
            label, value, prefix, suffix = calc_kpi(kc, df_k_f)
            with kpi_cols[ki % 5]:
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{fmt_val(value,prefix,suffix)}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    charts = page.get("charts",[])
    if charts:
        st.markdown(f'<p class="section-label">Visualisations</p>', unsafe_allow_html=True)
        i = 0
        while i < len(charts):
            cfg   = charts[i]
            width = cfg.get("width","half")

            def render_with_controls(cfg, idx, col_container):
                df_c = get_df_for(cfg)
                if df_c is None: return
                with col_container:
                    st.markdown(f'<div class="chart-title">{cfg.get("title","")}</div>', unsafe_allow_html=True)
                    fig = render_chart(cfg, df_c, st.session_state.global_filters, page_filters)
                    if fig: st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":True,"scrollZoom":True})

                    with st.expander("⚙️ Customise this chart"):
                        # Chart type — ALL types
                        cur_type = cfg.get("type","bar")
                        cur_type_idx = ALL_CHART_TYPES.index(cur_type) if cur_type in ALL_CHART_TYPES else 0
                        ec1, ec2 = st.columns(2)
                        new_type = ec1.selectbox("Chart type", ALL_CHART_TYPES, index=cur_type_idx, key=f"ctype_{active_idx}_{idx}")
                        new_h    = ec2.slider("Height (px)", 150, 800, cfg.get("height",350), 50, key=f"ch_{active_idx}_{idx}")

                        ec3, ec4 = st.columns(2)
                        new_cs   = ec3.selectbox("Color scheme", ["none","blues","greens","reds","purples","oranges","teal","viridis","plasma","turbo"], key=f"ccs_{active_idx}_{idx}")

                        # Custom single color for chart
                        use_custom = ec4.checkbox("Custom color", key=f"use_cc_{active_idx}_{idx}")
                        if use_custom:
                            custom_c = st.color_picker("Chart color", cfg.get("custom_color","#3B82F6"), key=f"cc_{active_idx}_{idx}")
                        else:
                            custom_c = None

                        # Custom bg colors for this chart
                        use_bg = st.checkbox("Custom chart background", key=f"use_bg_{active_idx}_{idx}")
                        if use_bg:
                            bg1, bg2 = st.columns(2)
                            chart_bg   = bg1.color_picker("Paper bg", cfg.get("bg_color", T["paper_bg"]), key=f"cbg_{active_idx}_{idx}")
                            chart_plot = bg2.color_picker("Plot bg",  cfg.get("plot_bg_color", T["plot_bg"]), key=f"cpbg_{active_idx}_{idx}")
                        else:
                            chart_bg = chart_plot = None

                        if st.button("✅ Apply changes", key=f"apply_{active_idx}_{idx}"):
                            pages[active_idx]["charts"][idx]["type"]   = new_type
                            pages[active_idx]["charts"][idx]["height"] = new_h
                            if new_cs != "none": pages[active_idx]["charts"][idx]["color_scheme"] = new_cs
                            if custom_c: pages[active_idx]["charts"][idx]["custom_color"] = custom_c
                            if chart_bg: pages[active_idx]["charts"][idx]["bg_color"] = chart_bg
                            if chart_plot: pages[active_idx]["charts"][idx]["plot_bg_color"] = chart_plot
                            st.session_state.pages = pages; st.rerun()

                        if st.button("🗑 Remove chart", key=f"rm_{active_idx}_{idx}"):
                            pages[active_idx]["charts"].pop(idx)
                            st.session_state.pages = pages; st.rerun()

            if width == "full":
                render_with_controls(cfg, i, st)
                i += 1
            elif width == "third":
                group = []
                while i < len(charts) and charts[i].get("width")=="third" and len(group)<3:
                    group.append(i); i+=1
                cols = st.columns(len(group))
                for j,idx2 in enumerate(group):
                    render_with_controls(charts[idx2], idx2, cols[j])
            else:  # half
                group = []
                while i < len(charts) and charts[i].get("width","half")=="half" and len(group)<2:
                    group.append(i); i+=1
                cols = st.columns(len(group))
                for j,idx2 in enumerate(group):
                    render_with_controls(charts[idx2], idx2, cols[j])

# ── Chat ───────────────────────────────────────────────────────────────────────
st.markdown('<hr class="soft">', unsafe_allow_html=True)
st.markdown(f'<p class="section-label">AI Agent</p>', unsafe_allow_html=True)

qps = ["Build me a full professional dashboard","Add a new page","Show trends over time","Add distribution charts","Build executive summary page"]
qp_cols = st.columns(len(qps))
for i,qp in enumerate(qps):
    with qp_cols[i]:
        if st.button(qp, key=f"qp_{i}"): st.session_state["_pending"] = qp

if st.session_state.messages:
    for m in st.session_state.messages[-4:]:
        cls = "chat-user" if m["role"]=="user" else "chat-ai"
        lbl = "You" if m["role"]=="user" else "AI"
        st.markdown(f'<div class="{cls}"><strong>{lbl}:</strong> {m["content"]}</div>', unsafe_allow_html=True)

user_input = st.chat_input("e.g. 'Build a full dashboard' or 'Add a claims analysis page' or 'Change the pie chart to a donut'")
prompt = st.session_state.pop("_pending", None) or user_input

if prompt:
    if ai_mode != "Ollama (local)" and not api_key:
        st.markdown('<div class="err-box">⚠️ Please enter your API key in the sidebar.</div>', unsafe_allow_html=True)
        st.stop()
    if not st.session_state.datasets:
        st.markdown('<div class="warn-box">⚠️ Upload a data file first.</div>', unsafe_allow_html=True)
        st.stop()

    st.session_state.messages.append({"role":"user","content":prompt})
    with st.spinner("AI agent is building your dashboard..."):
        try:
            raw    = call_ai(build_system_prompt(), st.session_state.messages, ai_mode, api_key, ollama_model)
            result = parse_json(raw)
            if not result:
                st.markdown('<div class="warn-box">⚠️ Could not parse response. Try rephrasing.</div>', unsafe_allow_html=True)
                st.stop()
            ai_msg   = result.get("message","Dashboard built.")
            new_pages= result.get("pages",[])
            st.session_state.messages.append({"role":"assistant","content":ai_msg})
            is_full = any(kw in prompt.lower() for kw in ["full","build","overview","dashboard","start","rebuild"])
            if is_full or not st.session_state.pages:
                st.session_state.pages = new_pages; st.session_state.active_page = 0
            else:
                st.session_state.pages.extend(new_pages)
            st.session_state.dashboard_built = True
            st.rerun()
        except Exception as e:
            st.markdown(f'<div class="err-box">❌ Error: {e}</div>', unsafe_allow_html=True)

with st.expander("🔍 Preview raw data"):
    for name, df in st.session_state.datasets.items():
        st.markdown(f"**{name}** — {len(df):,} rows")
        st.dataframe(df.head(100), use_container_width=True)

# ── EXPORT SECTION ─────────────────────────────────────────────────────────────
st.markdown('<hr class="soft">', unsafe_allow_html=True)
st.markdown(f'<p class="section-label">Export Dashboard</p>', unsafe_allow_html=True)

if not pages or not st.session_state.datasets:
    st.markdown(f'<div class="warn-box">⚠️ Build a dashboard first before exporting.</div>', unsafe_allow_html=True)
else:
    page = pages[active_idx] if active_idx < len(pages) else {}
    charts = page.get("charts", [])

    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

    # ── 1. Download as HTML (interactive) ─────────────────────────────────────
    with exp_col1:
        st.markdown(f'<p style="font-size:12px;font-weight:600;color:{T["text"]};margin-bottom:6px">📄 Interactive HTML</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;color:{T["text2"]};margin-bottom:8px">Full interactive dashboard. Open in any browser. Charts stay clickable.</p>', unsafe_allow_html=True)

        if st.button("Generate HTML", key="export_html"):
            with st.spinner("Building HTML..."):
                try:
                    html_parts = []
                    kpi_html = ""
                    chart_html = ""

                    # KPIs
                    kpis = page.get("kpis", [])
                    kpi_cards = []
                    for kc in kpis:
                        df_k = st.session_state.datasets.get(kc.get("dataset",""), list(st.session_state.datasets.values())[0])
                        label, value, prefix, suffix = calc_kpi(kc, df_k)
                        kpi_cards.append(f"""
                        <div style="background:{T['surface']};border:1px solid {T['border']};border-radius:12px;padding:1.2rem;flex:1;min-width:150px;">
                            <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{T['text2']};margin-bottom:8px">{label}</div>
                            <div style="font-size:1.8rem;font-weight:700;color:{T['text']}">{fmt_val(value,prefix,suffix)}</div>
                        </div>""")
                    kpi_html = f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:1.5rem">{"".join(kpi_cards)}</div>'

                    # Charts
                    chart_divs = []
                    for ci, cfg in enumerate(charts):
                        df_c = get_df_for(cfg)
                        if df_c is None: continue
                        fig = render_chart(cfg, df_c, st.session_state.global_filters, {})
                        if fig:
                            w = cfg.get("width","half")
                            width_pct = "100%" if w=="full" else ("48%" if w=="half" else "31%")
                            chart_html_inner = fig.to_html(full_html=False, include_plotlyjs='cdn' if ci==0 else False)
                            chart_divs.append(f'<div style="width:{width_pct};background:{T["surface"]};border:1px solid {T["border"]};border-radius:12px;padding:1rem;box-sizing:border-box">{chart_html_inner}</div>')

                    chart_html = f'<div style="display:flex;flex-wrap:wrap;gap:16px">{"".join(chart_divs)}</div>'

                    heading_text = page.get("heading","Dashboard")
                    heading_col  = page.get("heading_color", T["text"])

                    final_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{heading_text}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:{T['bg']}; padding:24px; color:{T['text']}; }}
  .header {{ margin-bottom:24px; border-bottom:2px solid {T['border']}; padding-bottom:16px; }}
  .header h1 {{ font-size:1.8rem; font-weight:700; color:{heading_col}; letter-spacing:-0.02em; }}
  .header p {{ font-size:13px; color:{T['text2']}; margin-top:4px; }}
  .footer {{ text-align:center; font-size:12px; color:{T['text2']}; margin-top:24px; padding-top:16px; border-top:1px solid {T['border']}; }}
</style>
</head>
<body>
  <div class="header">
    <h1>{heading_text}</h1>
    <p>Generated by InsightFlow · {datetime.now().strftime("%d %B %Y %H:%M")} · Page: {page.get("name","Dashboard")}</p>
  </div>
  {kpi_html}
  {chart_html}
  <div class="footer">InsightFlow AI Dashboard Builder · All charts are interactive — hover, zoom, click to explore</div>
</body>
</html>"""

                    st.download_button(
                        label="⬇️ Download HTML",
                        data=final_html.encode("utf-8"),
                        file_name=f"{page.get('name','dashboard').replace(' ','_').lower()}_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html",
                        key="dl_html"
                    )
                    st.success("Ready!")
                except Exception as e:
                    st.error(f"HTML export error: {e}")

    # ── 2. Download data as Excel ──────────────────────────────────────────────
    with exp_col2:
        st.markdown(f'<p style="font-size:12px;font-weight:600;color:{T["text"]};margin-bottom:6px">📊 Excel (.xlsx)</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;color:{T["text2"]};margin-bottom:8px">All datasets as separate sheets. Filtered data included. Ready to open in Power BI or Excel.</p>', unsafe_allow_html=True)

        if st.button("Generate Excel", key="export_excel"):
            with st.spinner("Building Excel..."):
                try:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        workbook = writer.book

                        # Formats
                        header_fmt = workbook.add_format({
                            "bold": True, "bg_color": "#1E40AF", "font_color": "#FFFFFF",
                            "border": 1, "align": "center"
                        })
                        num_fmt = workbook.add_format({"num_format": "#,##0.00"})

                        for ds_name, df in st.session_state.datasets.items():
                            # Apply global filters
                            df_export = apply_filters_to_df(df, st.session_state.global_filters, {})
                            sheet_name = ds_name[:31].replace("/","_").replace("\\","_")
                            df_export.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
                            worksheet = writer.sheets[sheet_name]

                            # Write headers with formatting
                            for ci, col in enumerate(df_export.columns):
                                worksheet.write(0, ci, col, header_fmt)
                                worksheet.set_column(ci, ci, max(len(str(col))+4, 14))

                        # KPI summary sheet
                        kpi_rows = []
                        for kc in page.get("kpis",[]):
                            df_k = st.session_state.datasets.get(kc.get("dataset",""), list(st.session_state.datasets.values())[0])
                            label, value, prefix, suffix = calc_kpi(kc, df_k)
                            kpi_rows.append({"Metric": label, "Value": value, "Prefix": prefix, "Suffix": suffix})
                        if kpi_rows:
                            pd.DataFrame(kpi_rows).to_excel(writer, sheet_name="KPI Summary", index=False)

                    output.seek(0)
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=output.getvalue(),
                        file_name=f"insightflow_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_excel"
                    )
                    st.success("Ready!")
                except Exception as e:
                    st.error(f"Excel export error: {e}")

    # ── 3. Download charts as PNG images ───────────────────────────────────────
    with exp_col3:
        st.markdown(f'<p style="font-size:12px;font-weight:600;color:{T["text"]};margin-bottom:6px">🖼️ Charts as PNG</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;color:{T["text2"]};margin-bottom:8px">All charts exported as high-res PNG images in a zip file. Use in Word, PowerPoint, emails.</p>', unsafe_allow_html=True)

        if st.button("Generate PNGs", key="export_png"):
            with st.spinner("Rendering charts..."):
                try:
                    import zipfile
                    zip_buffer = io.BytesIO()
                    chart_count = 0
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for ci, cfg in enumerate(charts):
                            df_c = get_df_for(cfg)
                            if df_c is None: continue
                            fig = render_chart(cfg, df_c, st.session_state.global_filters, {})
                            if fig:
                                try:
                                    img_bytes = fig.to_image(format="png", width=1200, height=cfg.get("height",400)*2, scale=2)
                                    safe_title = re.sub(r'[^\w\s-]','', cfg.get("title","chart")).strip().replace(" ","_")
                                    zf.writestr(f"chart_{ci+1}_{safe_title}.png", img_bytes)
                                    chart_count += 1
                                except Exception as ce:
                                    pass  # Skip charts that fail to render as image

                    zip_buffer.seek(0)
                    if chart_count > 0:
                        st.download_button(
                            label=f"⬇️ Download {chart_count} PNGs",
                            data=zip_buffer.getvalue(),
                            file_name=f"insightflow_charts_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                            mime="application/zip",
                            key="dl_png"
                        )
                        st.success(f"{chart_count} charts ready!")
                    else:
                        st.warning("No charts could be exported. Make sure kaleido is installed: pip install kaleido")
                except Exception as e:
                    st.error(f"PNG export error: {e}")

    # ── 4. Download as CSV ─────────────────────────────────────────────────────
    with exp_col4:
        st.markdown(f'<p style="font-size:12px;font-weight:600;color:{T["text"]};margin-bottom:6px">📋 CSV Data</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="font-size:11px;color:{T["text2"]};margin-bottom:8px">Download each dataset as CSV. Filtered by your active slicers. Import directly into Power BI.</p>', unsafe_allow_html=True)

        if len(st.session_state.datasets) == 1:
            ds_name, df = list(st.session_state.datasets.items())[0]
            df_export = apply_filters_to_df(df, st.session_state.global_filters, {})
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"⬇️ Download CSV ({len(df_export):,} rows)",
                data=csv_data,
                file_name=f"{ds_name.replace('.csv','').replace('.xlsx','')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="dl_csv_single"
            )
        else:
            # Multiple datasets — zip them all
            if st.button("Generate CSVs", key="export_csv"):
                with st.spinner("Preparing CSVs..."):
                    try:
                        import zipfile
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            for ds_name, df in st.session_state.datasets.items():
                                df_export = apply_filters_to_df(df, st.session_state.global_filters, {})
                                csv_str = df_export.to_csv(index=False)
                                safe_name = ds_name.replace(".xlsx","").replace(".xls","") + ".csv"
                                zf.writestr(safe_name, csv_str)
                        zip_buffer.seek(0)
                        st.download_button(
                            label=f"⬇️ Download All CSVs",
                            data=zip_buffer.getvalue(),
                            file_name=f"insightflow_data_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                            mime="application/zip",
                            key="dl_csv_multi"
                        )
                        st.success("Ready!")
                    except Exception as e:
                        st.error(f"CSV export error: {e}")

    # ── Export note ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="info-box" style="margin-top:12px">
        <strong>💡 Using with Power BI:</strong> Download the Excel export → open Power BI Desktop → 
        Get Data → Excel → select the file. Your filtered, cleaned data loads instantly as a Power BI dataset. 
        Then build your Power BI visuals on top of it.
    </div>
    """, unsafe_allow_html=True)

