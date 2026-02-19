import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import date

# ODGS Core Imports
from odgs.system.config import settings
from odgs.factory.generator import generate_bundle, generate_with_gemini, write_bundle

# Set Page Config
st.set_page_config(
    page_title="ODGS Sovereign Interface — v3.3.0",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME CSS: EU Institutional + Premium Protocol ---
st.markdown("""
<style>
    /* ---------- GLOBAL TYPOGRAPHY ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, .stCode, pre {
        font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace !important;
    }

    /* ---------- SOVEREIGN CARDS ---------- */
    .sov-card {
        background: #FFFFFF;
        border: 1px solid #D5DBE4;
        padding: 22px 24px;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .sov-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-color: #0052CC44;
    }

    /* ---------- KPI STAT CARDS ---------- */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #D5DBE4;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .kpi-card.kpi-blue::before { background: #003399; }
    .kpi-card.kpi-green::before { background: #006644; }
    .kpi-card.kpi-purple::before { background: #5B2D8E; }
    .kpi-card.kpi-amber::before { background: #B7630A; }
    .kpi-card.kpi-eu::before { background: linear-gradient(90deg, #003399, #FFCC00); }
    .kpi-value {
        font-size: 2em;
        font-weight: 800;
        color: #172B4D;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .kpi-label {
        font-size: 0.78em;
        color: #6B778C;
        font-weight: 600;
        margin-top: 4px;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .kpi-sub {
        font-size: 0.72em;
        color: #97A0AF;
        margin-top: 2px;
    }

    /* ---------- STATUS CHIPS ---------- */
    .chip-sovereign {
        background: #E3FCEF; color: #006644;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #ABF5D1; display: inline-block;
    }
    .chip-draft {
        background: #FFF7E6; color: #974F0C;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #FFE0B2; display: inline-block;
    }
    .chip-critical {
        background: #FFEBE6; color: #BF2600;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #FFBDAD; display: inline-block;
    }
    .chip-high {
        background: #FFF3E0; color: #E65100;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #FFCC80; display: inline-block;
    }
    .chip-medium {
        background: #FFFDE7; color: #F57F17;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #FFF59D; display: inline-block;
    }
    .chip-low {
        background: #E8F5E9; color: #2E7D32;
        padding: 3px 10px; border-radius: 20px;
        font-size: 0.78em; font-weight: 700;
        border: 1px solid #A5D6A7; display: inline-block;
    }
    .chip-live {
        background: #E3FCEF; color: #006644;
        padding: 2px 8px; border-radius: 12px;
        font-size: 0.72em; font-weight: 700;
        border: 1px solid #ABF5D1; display: inline-block;
    }
    .chip-static {
        background: #EAE6FF; color: #403294;
        padding: 2px 8px; border-radius: 12px;
        font-size: 0.72em; font-weight: 700;
        border: 1px solid #C0B6F2; display: inline-block;
    }

    /* ---------- DARK SECURITY PANEL (SIDEBAR) ---------- */
    .security-panel {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B2838 100%);
        border: 1px solid #1E3A5F;
        border-radius: 10px;
        padding: 14px 16px;
        font-size: 0.80em;
        color: #B0BEC5;
    }
    .security-panel .sp-title {
        color: #4FC3F7; font-weight: 700;
        font-size: 1.05em; margin-bottom: 8px;
    }
    .security-panel .sp-row {
        display: flex; justify-content: space-between;
        padding: 3px 0; border-bottom: 1px solid #1E3A5F22;
    }
    .security-panel .sp-ok { color: #66BB6A; font-weight: 700; }
    .security-panel .sp-label { color: #90A4AE; }

    /* ---------- EU PROTOCOL HEADER ---------- */
    .eu-header {
        background: #FFFFFF;
        border: 1px solid #D5DBE4;
        border-radius: 10px;
        padding: 24px 28px;
        margin-bottom: 16px;
        border-left: 4px solid #003399;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .eu-header .eu-flag {
        display: inline-block;
        width: 28px; height: 20px;
        background: linear-gradient(180deg, #003399 0%, #003399 100%);
        border-radius: 3px;
        margin-right: 10px;
        vertical-align: middle;
        position: relative;
    }
    .eu-header .eu-flag::after {
        content: '★';
        color: #FFCC00;
        font-size: 10px;
        position: absolute;
        top: 2px; left: 9px;
    }
    .eu-title {
        font-size: 1.4em;
        font-weight: 800;
        color: #172B4D;
        letter-spacing: -0.01em;
    }
    .eu-subtitle {
        font-size: 0.85em;
        color: #6B778C;
        margin-top: 4px;
        font-weight: 500;
    }

    /* ---------- HARVESTER SOURCE CARDS ---------- */
    .source-card {
        background: #FFFFFF;
        border: 1px solid #D5DBE4;
        border-radius: 10px;
        padding: 20px 22px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
        height: 100%;
    }
    .source-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-color: #0052CC44;
        transform: translateY(-1px);
    }
    .source-icon {
        font-size: 1.8em;
        margin-bottom: 8px;
    }
    .source-title {
        font-size: 1.05em;
        font-weight: 700;
        color: #172B4D;
        margin-bottom: 4px;
    }
    .source-authority {
        font-size: 0.78em;
        color: #6B778C;
        font-weight: 500;
        margin-bottom: 10px;
    }
    .source-desc {
        font-size: 0.82em;
        color: #505F79;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    .source-meta {
        font-size: 0.75em;
        color: #97A0AF;
        border-top: 1px solid #EBECF0;
        padding-top: 10px;
        margin-top: auto;
    }
    .source-meta code {
        background: #F4F5F7;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.92em;
        color: #172B4D;
    }

    /* ---------- GUIDE CARDS ---------- */
    .guide-card {
        background: #FFFFFF;
        border: 1px solid #D5DBE4;
        border-radius: 10px;
        padding: 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        height: 100%;
    }
    .guide-card .guide-icon {
        font-size: 2em;
        margin-bottom: 10px;
    }
    .guide-card h4 {
        color: #172B4D;
        margin: 0 0 8px 0;
        font-weight: 700;
    }
    .guide-card p {
        color: #505F79;
        font-size: 0.88em;
        line-height: 1.6;
        margin: 0;
    }

    /* ---------- CLEAN TABLE LOOK ---------- */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ---------- TAB STYLING ---------- */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        font-size: 0.85em;
        font-weight: 600;
    }

    /* ---------- SIDEBAR BRANDING ---------- */
    section[data-testid="stSidebar"] {
        border-right: 2px solid #00339922;
    }

    /* ---------- ARCHITECTURE PLANE ---------- */
    .plane-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        transition: background 0.15s;
    }
    .plane-row:hover { background: #F4F5F7; }
    .plane-icon {
        font-size: 1.4em;
        width: 36px;
        text-align: center;
        margin-right: 14px;
    }
    .plane-name {
        font-weight: 700;
        color: #172B4D;
        font-size: 0.95em;
    }
    .plane-role {
        color: #6B778C;
        font-size: 0.82em;
        margin-top: 1px;
    }
    .plane-artifact {
        margin-left: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75em;
        color: #97A0AF;
        background: #F4F5F7;
        padding: 2px 8px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: Institutional Branding ---
with st.sidebar:
    st.markdown("""
<div style="padding:4px 0 12px 0;">
  <div style="font-size:2em; line-height:1;">🏛️</div>
  <div style="font-size:1.15em; font-weight:800; color:#003399; letter-spacing:0.02em; margin-top:6px;">
    ODGS Protocol
  </div>
  <div style="font-size:0.78em; color:#5E6C84; font-weight:600; margin-top:2px;">
    v3.3.0 &nbsp;·&nbsp; Sovereign Edition
  </div>
  <div style="font-size:0.68em; color:#97A0AF; margin-top:4px;">
    EU AI Act · ISO 42001 · NEN 381 525
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    st.markdown("**🕰️ Time Machine**")
    effective_date = st.date_input("Effective Date", value=date.today(), label_visibility="collapsed")
    st.caption(f"Resolving reality as of **{effective_date}**")

    st.divider()
    st.markdown("""
<div style="background:#E3FCEF; border:1px solid #ABF5D1; border-radius:8px; padding:10px 12px; font-size:0.82em; color:#006644;">
  <strong>● Connected</strong><br>Private Repository
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
<div class="security-panel">
  <div class="sp-title">🛡️ Protocol Integrity</div>
  <div class="sp-row"><span class="sp-label">Sovereign Handshake</span><span class="sp-ok">✅ Active</span></div>
  <div class="sp-row"><span class="sp-label">Secure Evaluator</span><span class="sp-ok">✅ expr-eval</span></div>
  <div class="sp-row"><span class="sp-label">Schema Validation</span><span class="sp-ok">✅ 122/122</span></div>
  <div class="sp-row"><span class="sp-label">Temporal Resolution</span><span class="sp-ok">✅ Active</span></div>
  <div class="sp-row"><span class="sp-label">Tri-Partite Binding</span><span class="sp-ok">✅ SHA-256</span></div>
  <div class="sp-row"><span class="sp-label">Harvester Sources</span><span class="sp-ok">✅ 5 Active</span></div>
  <div class="sp-row"><span class="sp-label">OWL Ontology</span><span class="sp-ok">✅ W3C</span></div>
</div>
""", unsafe_allow_html=True)

from odgs.ui.graph_query import graph_engine, URN_PREFIX_METRIC, URN_PREFIX_RULE
from odgs.ui.semantic_certificate import render_certificate_tab, render_chain_tab

# --- TOP-LEVEL GROUPS (4 pillars of the architecture) ---
grp1, grp2, grp3, grp4 = st.tabs([
    "📊 Governance",
    "⚖️ Enforcement",
    "🏢 Operations",
    "📖 Reference",
])

# ════════════════════════════════════════════════════════════════
# GROUP 1: GOVERNANCE — The "What" (Legislative + DQ layer)
# ════════════════════════════════════════════════════════════════
with grp1:
    tab1, tab2, tab9 = st.tabs([
        "📊 Compliance Matrix",
        "🔭 The Explorer",
        "🧬 DQ Observatory",
    ])

# --- TAB 1: COMPLIANCE MATRIX ---
with tab1:
    # EU Protocol Header
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Sovereign Compliance Matrix</span>
        <div class="eu-subtitle">Real-time governance status across all data assets · Aligned with EU AI Act Art. 10 & 12</div>
    </div>
</div>
""", unsafe_allow_html=True)
    
    df = graph_engine.get_compliance_matrix()
    phase_stats = graph_engine.get_phase_stats()
    
    if not df.empty:
        # Row 1: Core KPIs as custom cards
        total_metrics = len(df)
        sovereign_count = len(df[df["Status"] == "Sovereign"])
        draft_count = len(df[df["Status"] == "Draft (AI)"])
        naked_count = len(df[df["Status"] == "Naked"])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""
<div class="kpi-card kpi-blue">
    <div class="kpi-value">{total_metrics}</div>
    <div class="kpi-label">Business Metrics</div>
    <div class="kpi-sub">Legislative Plane</div>
</div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
<div class="kpi-card kpi-green">
    <div class="kpi-value">{sovereign_count}</div>
    <div class="kpi-label">Sovereign Backed</div>
    <div class="kpi-sub">Legally Bound</div>
</div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
<div class="kpi-card kpi-amber">
    <div class="kpi-value">{draft_count}</div>
    <div class="kpi-label">AI Drafts</div>
    <div class="kpi-sub">Pending Review</div>
</div>""", unsafe_allow_html=True)
        with col4:
            logic_pct = round(phase_stats['rules_with_logic'] / max(phase_stats['unique_rules'], 1) * 100)
            st.markdown(f"""
<div class="kpi-card kpi-purple">
    <div class="kpi-value">{logic_pct}%</div>
    <div class="kpi-label">Enforceable Rules</div>
    <div class="kpi-sub">{phase_stats['rules_with_logic']}/{phase_stats['unique_rules']} with logic</div>
</div>""", unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
<div class="kpi-card kpi-eu">
    <div class="kpi-value">5</div>
    <div class="kpi-label">Harvester Sources</div>
    <div class="kpi-sub">Authoritative Bodies</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        
        # Filter
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            domain_filter = st.multiselect("Filter by Domain", options=df["Domain"].unique(), default=df["Domain"].unique())
        with col_filter2:
            status_filter = st.multiselect("Filter by Status", options=df["Status"].unique(), default=df["Status"].unique())
        
        visible_df = df[df["Domain"].isin(domain_filter) & df["Status"].isin(status_filter)]

        # Show enriched table (hide internal columns)
        display_cols = ["ID", "Metric Name", "Domain", "Status", "Authority", "DQ Dims", "Rules"]
        st.dataframe(
            visible_df[display_cols],
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "DQ Dims": st.column_config.NumberColumn("DQ Dims", help="Linked Data Quality Dimensions"),
                "Rules": st.column_config.NumberColumn("Rules", help="Linked enforcement rules"),
            },
            use_container_width=True,
            hide_index=True
        )

        # --- Expandable Detail ---
        st.divider()
        st.markdown("#### 🔍 Metric Deep Dive")
        metric_options = {row["Metric Name"]: row["ID"] for _, row in visible_df.iterrows()}
        selected = st.selectbox("Select a metric to inspect:", ["— Select —"] + list(metric_options.keys()), key="matrix_detail_select")
        if selected != "— Select —":
            row = visible_df[visible_df["ID"] == metric_options[selected]].iloc[0]
            dc1, dc2 = st.columns(2)
            with dc1:
                with st.container(border=True):
                    st.markdown(f"**📐 Calculation Logic**")
                    st.caption("Abstract")
                    st.code(row.get("_calc_abstract", "—"), language="text")
                    st.caption("SQL Standard")
                    st.code(row.get("_calc_sql", "—"), language="sql")
                    st.caption("DAX Pattern")
                    st.code(row.get("_calc_dax", "—"), language="text")
            with dc2:
                with st.container(border=True):
                    st.markdown(f"**📖 Business Context**")
                    st.info(row.get("_definition", "No definition available."))
                    if row.get("_interpretation"):
                        st.markdown(f"**Interpretation:** {row['_interpretation']}")
                    if row.get("_example"):
                        st.markdown(f"**Example:** {row['_example']}")
                    if row.get("_industries"):
                        st.markdown(f"**Target Industries:** `{row['_industries']}`")
                    if row.get("_dq_names") and row["_dq_names"] != "—":
                        st.markdown(f"**Linked DQ Dimensions:** {row['_dq_names']}")
    else:
        st.warning("No metrics found in Legislative Plane.")

# --- TAB 2: THE EXPLORER ---
with tab2:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Sovereign Lens Explorer</span>
        <div class="eu-subtitle">Trace the semantic chain: Business Definition → Enforcement Logic → Sovereign Law</div>
    </div>
</div>
""", unsafe_allow_html=True)
    
    # Selector
    all_metrics = graph_engine.metrics
    options = {m["name"]: mid for mid, m in all_metrics.items()}
    
    selected_name = st.selectbox("Select a Metric to Audit:", options.keys())
    
    if selected_name:
        mid = options[selected_name]
        lineage = graph_engine.get_metric_lineage(mid)
        
        if lineage:
            metric = lineage["metric"]
            rules = lineage["rules"]
            definition = lineage["definition"]
            physical = lineage.get("physical")
            dq_dims = lineage.get("dq_dimensions", [])
            
            # --- 4 COLUMN LAYOUT ---
            c1, c2, c3, c4 = st.columns(4)
            
            # 1. Business Logic
            with c1:
                with st.container(border=True):
                    st.subheader("💼 Business")
                    st.markdown(f"**{metric.get('name')}**")
                    st.caption(f"ID: {metric.get('metric_id')}")
                    st.markdown(f"*{metric.get('definition') or metric.get('description', '')}*")
                    st.divider()
                    st.markdown(f"**Owner:** {metric.get('owner', 'Unassigned')}")
                    st.markdown(f"**Domain:** {metric.get('domain')}")
                    if dq_dims:
                        st.divider()
                        st.caption(f"🧬 {len(dq_dims)} DQ Dimensions:")
                        for dim in dq_dims[:5]:
                            st.markdown(f"- {dim.get('name', '')}")
            
            # 2. Data Logic (Rules)
            with c2:
                with st.container(border=True):
                    st.subheader("⚙️ Logic")
                    if rules:
                        for r in rules:
                            rule_name = r.get('name') or r.get('rule_name', 'Unknown Rule')
                            severity = r.get('severity', '')
                            sev_colors = {'CRITICAL': 'chip-critical', 'HARD_STOP': 'chip-critical', 'HIGH': 'chip-high', 'MEDIUM': 'chip-medium', 'LOW': 'chip-low'}
                            sev_chip = f' <span class="{sev_colors.get(severity, "chip-draft")}">{severity}</span>' if severity else ''
                            st.markdown(f"**🛡️ {rule_name}**{sev_chip}", unsafe_allow_html=True)
                            
                            rule_urn = r.get('urn', '')
                            if rule_urn:
                                st.caption(f"`{rule_urn}`")
                            
                            logic = r.get("calculation_logic") or r.get("check_logic", "N/A")
                            if isinstance(logic, dict):
                                logic = logic.get("sql_standard") or logic.get("abstract", "N/A")
                            st.code(logic, language="sql")
                            
                            logic_expr = r.get('logic_expression')
                            if logic_expr:
                                st.markdown("**Executable Expression:**")
                                st.code(logic_expr, language="python")
                            
                            st.caption(r.get("businessRule") or r.get("error_message") or r.get("definition", ""))
                            st.divider()
                    else:
                        st.warning("No linked Data Rules.")
            
            # 3. Sovereign Law
            with c3:
                with st.container(border=True):
                    st.subheader("⚖️ Law")
                    if definition:
                        auth = definition.get("metadata", {}).get("authority_id", "Unknown")
                        urn = definition.get("urn")
                        
                        badge_color = "green" if auth != "AI_SYNTHETIC" else "orange"
                        st.markdown(f":{badge_color}[**{auth}**]")
                        st.markdown(f"`{urn}`")
                        
                        st.divider()
                        st.markdown("**Verbatim Definition:**")
                        st.info(definition.get("content", {}).get("verbatim_text", "No text content."))
                        
                        if auth == "AI_SYNTHETIC":
                            st.caption("🤖 Generated by AI Factory")
                    else:
                        st.error("❌ No Sovereign Definition found.")
                        st.caption("This metric is 'Naked' (Unprotected). Use the AI Factory to generate a draft.")
            
            # 4. Physical Binding
            with c4:
                with st.container(border=True):
                    st.subheader("🔌 Physical")
                    if physical:
                        st.markdown(f"**Map ID:** `{physical.get('map_id', '')}`")
                        if physical.get("vector_embedding_hint"):
                            st.caption(f"🧠 {physical['vector_embedding_hint']}")
                        for binding in physical.get("bindings", []):
                            st.divider()
                            st.markdown(f"**Platform:** `{binding.get('platform', '')}`")
                            tbl = binding.get("table", "")
                            st.markdown(f"**Table:** `{binding.get('schema','')}.{tbl}`")
                            st.markdown(f"**Privacy:** `{binding.get('privacy_level', '—')}`")
                            st.markdown(f"**SLA:** `{binding.get('freshness_sla', '—')}`")
                            cols = binding.get("column_mapping", {})
                            if cols:
                                st.markdown("**Columns:**")
                                for concept, col in cols.items():
                                    st.markdown(f"- `{concept}` → `{col}`")
                    else:
                        st.warning("No Physical Binding.")
                        st.caption("No warehouse mapping configured for this metric.")

# ════════════════════════════════════════════════════════════════
# GROUP 3: OPERATIONS — The "Where" (Executive + Physical layer)
# ════════════════════════════════════════════════════════════════
with grp3:
    tab10, tab3, tab5 = st.tabs([
        "🏢 Executive Plane",
        "🌐 Harvester Sources",
        "🏭 AI Factory",
    ])

# --- TAB 3: HARVESTER SOURCES ---
with tab3:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Sovereign Harvester — Authoritative Sources</span>
        <div class="eu-subtitle">Definitions harvested from trusted regulatory bodies and international standards organisations</div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Source cards
    sources = [
        {
            "icon": "🇳🇱",
            "title": "Dutch Administrative Law (AwB)",
            "authority": "Overheid.nl — Kingdom of the Netherlands",
            "type": "live",
            "format": "XML (BWBR)",
            "concepts": "Administrative law articles (e.g., Art. 1:3 — Administrative Decision)",
            "url": "https://repository.officiele-overheidspublicaties.nl/",
            "cli": "odgs harvest nl_awb 1:3",
            "description": "Harvests verbatim articles from Dutch administrative law via the official government XML repository. Each article is content-hashed and stored as a Sovereign Definition.",
        },
        {
            "icon": "🏦",
            "title": "FIBO — Financial Industry Business Ontology",
            "authority": "EDM Council / Object Management Group",
            "type": "live",
            "format": "JSON-LD",
            "concepts": "8 modules: CurrencyAmount, AccountingEquity, Debt, LegalEntity, FinancialInstrument, RegulatoryAgency, Loan, DebtInstrument",
            "url": "https://spec.edmcouncil.org/fibo/",
            "cli": "odgs harvest fibo InterestRate",
            "description": "Fetches financial ontology concepts from the FIBO Linked Data endpoint. Supports dynamic module routing — each FIBO module is individually addressable.",
        },
        {
            "icon": "🤖",
            "title": "ISO/IEC 42001:2023 — AI Management System",
            "authority": "International Organization for Standardization",
            "type": "static",
            "format": "Static Registry",
            "concepts": "Clauses 4–10: Context, Leadership, Planning, Support, Operation, Performance, Improvement",
            "url": "https://www.iso.org/standard/81230.html",
            "cli": "odgs harvest iso_42001 4",
            "description": "Self-describing definitions for the 6 core clauses of the AI Management System standard. Provides the governance framework for responsible AI deployment.",
        },
        {
            "icon": "🇪🇺",
            "title": "EU General Data Protection Regulation",
            "authority": "European Parliament & Council — EUR-Lex",
            "type": "static",
            "format": "Static Registry",
            "concepts": "7 key articles: Art. 5 (Principles), Art. 6 (Lawfulness), Art. 17 (Right to Erasure), Art. 25 (Privacy by Design), Art. 30 (Records), Art. 35 (DPIA), Art. 83 (Fines)",
            "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
            "cli": "odgs harvest gdpr 25",
            "description": "Key GDPR articles mapped to data governance concepts. Each article includes verbatim text, chapter reference, and relevance to ODGS data quality dimensions.",
        },
        {
            "icon": "🏛️",
            "title": "Basel III/IV — Prudential Standards",
            "authority": "Bank for International Settlements (BIS)",
            "type": "static",
            "format": "Static Registry",
            "concepts": "7 standards: CET1, LCR, NSFR, Leverage Ratio, FRTB, IRRBB, Operational Risk",
            "url": "https://www.bis.org/bcbs/publ/d424.htm",
            "cli": "odgs harvest basel CET1",
            "description": "Prudential regulatory definitions from the Basel Framework. Each standard includes the regulatory reference, source URL, and relevance to financial metrics governance.",
        },
    ]

    for i in range(0, len(sources), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(sources):
                s = sources[i + j]
                type_chip = f'<span class="chip-live">● LIVE API</span>' if s["type"] == "live" else f'<span class="chip-static">◆ STATIC</span>'
                with col:
                    st.markdown(f"""
<div class="source-card">
    <div class="source-icon">{s['icon']}</div>
    <div class="source-title">{s['title']}</div>
    <div class="source-authority">{s['authority']} &nbsp; {type_chip}</div>
    <div class="source-desc">{s['description']}</div>
    <div class="source-meta">
        <strong>Format:</strong> {s['format']}<br>
        <strong>Concepts:</strong> {s['concepts']}<br>
        <strong>CLI:</strong> <code>{s['cli']}</code><br>
        <strong>Source:</strong> <a href="{s['url']}" target="_blank" style="color:#003399">{s['url'][:60]}{'…' if len(s['url']) > 60 else ''}</a>
    </div>
</div>
""", unsafe_allow_html=True)
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    st.divider()

    # ── Harvested Definitions from Disk ──
    st.subheader("📦 Harvested Sovereign Definitions")
    sov_base = settings.PROJECT_ROOT / "lib" / "schemas" / "sovereign"
    if sov_base.exists():
        import glob as _glob
        authority_dirs = sorted([d for d in sov_base.iterdir() if d.is_dir() and d.name != "ai_synthetic"])
        if authority_dirs:
            authority_labels = {
                "eu_gdpr": "🇪🇺 EU GDPR",
                "iso": "🤖 ISO 42001",
                "bis_bcbs": "🏛️ Basel III/IV",
                "nl_gov": "🇳🇱 Dutch AwB",
                "fibo": "🏦 FIBO",
            }
            total_defs = 0
            for auth_dir in authority_dirs:
                json_files = sorted(auth_dir.glob("*.json"))
                json_files = [f for f in json_files if f.name != "01-definitions-schema.json"]
                if not json_files:
                    continue
                total_defs += len(json_files)
                label = authority_labels.get(auth_dir.name, auth_dir.name)
                with st.expander(f"{label} — **{len(json_files)}** definitions", expanded=False):
                    for jf in json_files:
                        try:
                            defn = json.loads(jf.read_text())
                            urn = defn.get("urn", jf.stem)
                            interp = defn.get("interpretation") or {}
                            summary = interp.get("summary", "") if isinstance(interp, dict) else ""
                            content = defn.get("content") or {}
                            text = (content.get("verbatim_text", "") if isinstance(content, dict) else "")[:120]
                            authority = defn.get("authority", "")
                            auth_chip = f' <span class="chip-sovereign">{authority}</span>' if authority else ""
                            st.markdown(f"""**`{urn}`**{auth_chip}  \n{summary}""", unsafe_allow_html=True)
                            if text:
                                st.caption(f"{text}{'…' if len((content.get('verbatim_text','') if isinstance(content,dict) else '')) > 120 else ''}")
                            st.markdown("---")
                        except Exception:
                            st.caption(f"⚠️ Could not parse {jf.name}")
            st.info(f"📊 **{total_defs}** sovereign definitions across **{len(authority_dirs)}** authorities")
        else:
            st.warning("No harvested definitions found. Run `python3 scripts/run_all_harvesters.py` to populate.")
    else:
        st.warning("Sovereign directory not found.")

    st.divider()
    
    # Harvester Architecture Diagram
    st.subheader("Harvester Architecture")
    import streamlit.components.v1 as components
    _arch_html = """
<div style="
    background: linear-gradient(135deg, #0d1b3e 0%, #1a2a5e 50%, #0d1b3e 100%);
    border-radius: 16px;
    padding: 32px 24px;
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    position: relative;
    overflow: hidden;
">
    <!-- Subtle grid pattern overlay -->
    <div style="
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0);
        background-size: 24px 24px;
        pointer-events: none;
    "></div>

    <!-- Title -->
    <div style="text-align: center; margin-bottom: 28px; position: relative;">
        <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 3px; color: #7B8EC8; margin-bottom: 6px;">Data Pipeline</div>
        <div style="font-size: 20px; font-weight: 700; color: #FFFFFF;">Sovereign Harvester Architecture</div>
    </div>

    <!-- Pipeline Flow -->
    <div style="display: flex; align-items: center; justify-content: center; gap: 0; flex-wrap: nowrap; position: relative;">

        <!-- SOURCES Column -->
        <div style="flex: 0 0 200px;">
            <div style="text-align: center; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: #7B8EC8; margin-bottom: 12px;">Authoritative Sources</div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
                <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🇳🇱</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 600;">Dutch AwB</div>
                        <div style="font-size: 9px; color: #7B8EC8;">XML · wetten.overheid.nl</div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🏦</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 600;">FIBO</div>
                        <div style="font-size: 9px; color: #7B8EC8;">JSON-LD · edmcouncil.org</div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🤖</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 600;">ISO 42001</div>
                        <div style="font-size: 9px; color: #7B8EC8;">Static · iso.org</div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🇪🇺</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 600;">EU GDPR</div>
                        <div style="font-size: 9px; color: #7B8EC8;">Static · eur-lex.europa.eu</div>
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🏛️</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 600;">Basel III/IV</div>
                        <div style="font-size: 9px; color: #7B8EC8;">Static · bis.org</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Arrow 1 -->
        <div style="flex: 0 0 60px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div style="font-size: 9px; color: #7B8EC8; margin-bottom: 4px;">fetch</div>
            <div style="width: 40px; height: 2px; background: linear-gradient(90deg, #7B8EC8, #4C9AFF); position: relative;">
                <div style="position: absolute; right: -4px; top: -3px; width: 0; height: 0; border-top: 4px solid transparent; border-bottom: 4px solid transparent; border-left: 6px solid #4C9AFF;"></div>
            </div>
        </div>

        <!-- ENGINE -->
        <div style="flex: 0 0 160px; text-align: center;">
            <div style="
                background: linear-gradient(135deg, #003399 0%, #004FC4 100%);
                border: 2px solid #4C9AFF;
                border-radius: 16px;
                padding: 24px 16px;
                box-shadow: 0 0 30px rgba(0,51,153,0.4);
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">⚙️</div>
                <div style="font-size: 14px; font-weight: 700;">Harvester</div>
                <div style="font-size: 14px; font-weight: 700;">Engine</div>
                <div style="margin-top: 12px; display: flex; flex-direction: column; gap: 4px;">
                    <div style="font-size: 9px; background: rgba(255,255,255,0.15); border-radius: 4px; padding: 3px 6px;">Parse & Extract</div>
                    <div style="font-size: 9px; background: rgba(255,255,255,0.15); border-radius: 4px; padding: 3px 6px;">SHA-256 Seal</div>
                    <div style="font-size: 9px; background: rgba(255,255,255,0.15); border-radius: 4px; padding: 3px 6px;">URN Assignment</div>
                </div>
            </div>
        </div>

        <!-- Arrow 2 -->
        <div style="flex: 0 0 60px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <div style="font-size: 9px; color: #7B8EC8; margin-bottom: 4px;">seal</div>
            <div style="width: 40px; height: 2px; background: linear-gradient(90deg, #4C9AFF, #36B37E); position: relative;">
                <div style="position: absolute; right: -4px; top: -3px; width: 0; height: 0; border-top: 4px solid transparent; border-bottom: 4px solid transparent; border-left: 6px solid #36B37E;"></div>
            </div>
        </div>

        <!-- OUTPUT Column -->
        <div style="flex: 0 0 200px;">
            <div style="text-align: center; font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: #36B37E; margin-bottom: 12px;">Sovereign Plane</div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="
                    background: rgba(54, 179, 126, 0.1);
                    border: 1px solid rgba(54, 179, 126, 0.3);
                    border-radius: 12px;
                    padding: 16px;
                    text-align: center;
                ">
                    <div style="font-size: 24px; margin-bottom: 6px;">📜</div>
                    <div style="font-size: 12px; font-weight: 600; color: #36B37E;">Sovereign Definitions</div>
                    <div style="font-size: 10px; color: #7B8EC8; margin-top: 4px;">Content-hashed JSON artifacts</div>
                    <div style="font-size: 10px; color: #7B8EC8;">with cryptographic integrity</div>
                </div>
                <div style="
                    background: rgba(101, 84, 192, 0.1);
                    border: 1px solid rgba(101, 84, 192, 0.3);
                    border-radius: 12px;
                    padding: 16px;
                    text-align: center;
                ">
                    <div style="font-size: 24px; margin-bottom: 6px;">🕸️</div>
                    <div style="font-size: 12px; font-weight: 600; color: #8777D9;">Ontology Graph</div>
                    <div style="font-size: 10px; color: #7B8EC8; margin-top: 4px;">URN-linked semantic edges</div>
                    <div style="font-size: 10px; color: #7B8EC8;">between metrics & law</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer stats -->
    <div style="display: flex; justify-content: center; gap: 32px; margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); position: relative;">
        <div style="text-align: center;">
            <div style="font-size: 18px; font-weight: 700; color: #4C9AFF;">5</div>
            <div style="font-size: 9px; color: #7B8EC8; text-transform: uppercase; letter-spacing: 1px;">Sources</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 18px; font-weight: 700; color: #36B37E;">28</div>
            <div style="font-size: 9px; color: #7B8EC8; text-transform: uppercase; letter-spacing: 1px;">Definitions</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 18px; font-weight: 700; color: #FFAB00;">SHA-256</div>
            <div style="font-size: 9px; color: #7B8EC8; text-transform: uppercase; letter-spacing: 1px;">Integrity</div>
        </div>
    </div>
</div>
"""
    components.html(_arch_html, height=520, scrolling=False)

# ════════════════════════════════════════════════════════════════
# GROUP 4: REFERENCE — The "Why" (Education + Network)
# ════════════════════════════════════════════════════════════════
with grp4:
    tab8, tab4 = st.tabs([
        "📖 Protocol Guide",
        "🕸️ Network",
    ])

# --- TAB 4: NETWORK ---
with tab4:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Ontology Network</span>
        <div class="eu-subtitle">Visualising ontology_graph.json — the semantic backbone of ODGS governance</div>
    </div>
</div>
""", unsafe_allow_html=True)
    
    try:
        from streamlit_agraph import agraph, Node, Edge, Config
        
        raw_edges = graph_engine.edges
        
        nodes = []
        edges = []
        node_ids = set()
        
        if raw_edges:
            for edge in raw_edges:
                if "comment" in edge: continue
                
                src = edge["source_urn"]
                tgt = edge["target_urn"]
                rel = edge["relationship"]
                
                def get_color(urn):
                    if "metric" in urn: return "#003399"   # EU Blue
                    if "rule" in urn: return "#BF2600"     # Red
                    if "def" in urn: return "#5B2D8E"      # Purple
                    if "dimension" in urn: return "#B7630A" # Amber
                    return "#6B778C"

                if src not in node_ids:
                    nodes.append(Node(id=src, label=src.split(":")[-1], size=20, color=get_color(src)))
                    node_ids.add(src)
                if tgt not in node_ids:
                    nodes.append(Node(id=tgt, label=tgt.split(":")[-1], size=20, color=get_color(tgt)))
                    node_ids.add(tgt)
                    
                edges.append(Edge(source=src, target=tgt, label=rel))
                
            # Legend
            st.markdown("""
**Legend:** 
:blue[● Metrics] · :red[● Rules] · :violet[● Definitions] · :orange[● Dimensions]
""")
            
            config = Config(width=None, height=700, directed=True)
            return_value = agraph(nodes=nodes, edges=edges, config=config)
            
        else:
            st.error("Ontology Graph is empty.")

    except ImportError:
        # Fallback: Graphviz rendering
        st.info("Interactive graph requires `streamlit-agraph`. Showing static network view:")
        
        raw_edges = graph_engine.edges
        if raw_edges:
            # Build a graphviz DOT
            dot_nodes = set()
            dot_edges_list = []
            for edge in raw_edges:
                if "comment" in edge: continue
                src = edge["source_urn"]
                tgt = edge["target_urn"]
                rel = edge["relationship"]
                dot_nodes.add(src)
                dot_nodes.add(tgt)
                dot_edges_list.append((src, tgt, rel))
            
            def node_color(urn):
                if "metric" in urn: return "#003399"
                if "rule" in urn: return "#BF2600"
                if "def" in urn: return "#5B2D8E"
                if "dimension" in urn: return "#B7630A"
                return "#6B778C"
            
            dot_str = 'digraph G {\n  rankdir=LR; bgcolor="transparent";\n'
            dot_str += '  node [fontname="Inter" fontsize="9" style="filled,rounded" shape=box margin="0.12,0.06"];\n'
            dot_str += '  edge [fontsize="7" fontname="Inter" color="#97A0AF" fontcolor="#97A0AF"];\n\n'
            
            for n in dot_nodes:
                label = n.split(":")[-1]
                color = node_color(n)
                dot_str += f'  "{n}" [label="{label}" fillcolor="{color}" fontcolor="white"];\n'
            dot_str += '\n'
            for src, tgt, rel in dot_edges_list:
                dot_str += f'  "{src}" -> "{tgt}" [label="{rel}"];\n'
            dot_str += '}\n'
            
            st.graphviz_chart(dot_str, use_container_width=True)
        else:
            st.error("Ontology Graph is empty.")
    except Exception as e:
        st.error(f"Visualization Error: {e}")

# --- TAB 5: AI FACTORY ---
with tab5:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Sovereign Factory (AI)</span>
        <div class="eu-subtitle">Generate governance bundles for any industry using AI · Powered by Google Gemini · 15-20 definitions per bundle</div>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Preset Industries ──
    PRESET_INDUSTRIES = [
        "(Custom — type your own below)",
        "Banking & Financial Services",
        "Healthcare & Life Sciences",
        "Insurance & Risk Management",
        "Telecommunications",
        "Energy & Utilities",
        "Supply Chain & Logistics",
        "Government & Public Sector",
        "Retail & E-Commerce",
        "Manufacturing & Industry 4.0",
        "Automotive & Mobility",
    ]

    selected_preset = st.selectbox(
        "🏭 Select Industry Domain",
        PRESET_INDUSTRIES,
        help="Choose a preset or select the first option to type your own"
    )

    with st.form("ai_factory_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            if selected_preset == PRESET_INDUSTRIES[0]:
                industry = st.text_input("Custom Industry / Domain", placeholder="e.g. Quantum Computing Supply Chain")
            else:
                industry = st.text_input("Industry / Domain", value=selected_preset)
        with col2:
            key_input = st.text_input("Gemini API Key", type="password", help="Required. Get one at ai.google.dev")

        submitted = st.form_submit_button("🏭 Generate Governance Bundle", type="primary")

        if submitted and industry:
            if not key_input and not settings.GEMINI_API_KEY:
                st.error("❌ API Key required. Enter a Gemini API key or set GEMINI_API_KEY in your .env file.")
            else:
                with st.spinner(f"Synthesising '{industry}' Protocol (15-20 definitions)..."):
                    try:
                        api_key = key_input if key_input else None
                        result_data = generate_with_gemini(industry, api_key)

                        if result_data:
                            definitions = result_data["definitions"]
                            metadata = result_data["metadata"]

                            st.session_state["factory_result"] = result_data
                            st.session_state["factory_industry"] = industry

                            # ── Generation Stats Bar ──
                            st.success(f"✨ Generated {len(definitions)} Sovereign Definitions!")
                            stat_cols = st.columns(4)
                            stat_cols[0].metric("📊 Definitions", len(definitions))
                            stat_cols[1].metric("🤖 Model", metadata.get("model", "unknown"))
                            stat_cols[2].metric("📋 Protocol", metadata.get("protocol_version", "3.3.0"))
                            stat_cols[3].metric("🕐 Generated", metadata.get("generated_at", "")[:19])

                            # ── Bundle Preview Cards ──
                            st.markdown("### 📦 Bundle Preview")
                            for i, defn in enumerate(definitions):
                                urn = defn.get("urn", "unknown") if isinstance(defn, dict) else "unknown"
                                interp = defn.get("interpretation") or {} if isinstance(defn, dict) else {}
                                interp = interp if isinstance(interp, dict) else {}
                                summary = interp.get("summary", "No summary")
                                applicability = interp.get("applicability", "")
                                content = defn.get("content") or {} if isinstance(defn, dict) else {}
                                content = content if isinstance(content, dict) else {}
                                verbatim = (content.get("verbatim_text", "") or "")[:200]
                                meta = defn.get("metadata") or {} if isinstance(defn, dict) else {}
                                meta = meta if isinstance(meta, dict) else {}
                                content_hash = meta.get("content_hash", "") or ""
                                relations = defn.get("relations", []) if isinstance(defn, dict) else []
                                if relations and isinstance(relations, list) and isinstance(relations[0], dict):
                                    linked_metric = relations[0].get("target_urn", "—")
                                else:
                                    linked_metric = "—"

                                with st.expander(f"**{i+1}.** `{urn}`", expanded=(i < 3)):
                                    c1, c2 = st.columns([3, 1])
                                    with c1:
                                        st.markdown(f"**{summary}**")
                                        if applicability:
                                            st.caption(f"📌 {applicability}")
                                        if verbatim:
                                            full_text = content.get("verbatim_text", "") or ""
                                            st.markdown(f"> {verbatim}{'...' if len(full_text) > 200 else ''}")
                                    with c2:
                                        st.markdown(f"**Linked Metric**")
                                        st.code(linked_metric, language=None)
                                        if content_hash:
                                            st.markdown(f"**Integrity**")
                                            st.code(content_hash[:16] + "…", language=None)
                        else:
                            st.error("Generation failed. Check your API key and try again.")

                    except Exception as e:
                        st.error(f"Factory Error: {e}")
                        import traceback
                        st.code(traceback.format_exc(), language="python")

    # ── Approve & Commit Button (outside form) ──
    if "factory_result" in st.session_state:
        st.divider()
        result_data = st.session_state["factory_result"]
        industry_name = st.session_state.get("factory_industry", "unknown")
        n_defs = len(result_data.get("definitions", []))

        st.markdown(f"### ✅ Ready to Commit: **{n_defs}** definitions for *{industry_name}*")
        st.caption("This will write the bundle to `lib/schemas/sovereign/ai_synthetic/` and generate an ontology graph.")

        if st.button("🚀 Approve & Commit Bundle", type="primary"):
            try:
                slug = industry_name.lower().replace(" ", "_").replace("-", "_")
                output_dir = str(settings.PROJECT_ROOT / "lib" / "schemas" / "sovereign" / "ai_synthetic" / slug)
                write_bundle(result_data, output_dir)
                st.success(f"💾 Bundle committed to `{output_dir}`")
                st.balloons()

                # Clean up session state
                del st.session_state["factory_result"]
                del st.session_state["factory_industry"]
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Commit Error: {e}")

# ════════════════════════════════════════════════════════════════
# GROUP 2: ENFORCEMENT — The "How" (Judiciary + Interceptor layer)
# ════════════════════════════════════════════════════════════════
with grp2:
    tab11, tab6, tab7 = st.tabs([
        "⚡ Sovereign Brake",
        "🔐 Semantic Certificate",
        "🔗 Chain of Trust",
    ])

# --- TAB 6: SEMANTIC CERTIFICATE ---
with tab6:
    render_certificate_tab(graph_engine)

# --- TAB 7: CHAIN OF TRUST ---
with tab7:
    render_chain_tab(graph_engine)

# --- TAB 8: PROTOCOL GUIDE ---
with tab8:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Understanding the ODGS Protocol</span>
        <div class="eu-subtitle">How it works, why it matters, and what it means for your organisation</div>
    </div>
</div>
""", unsafe_allow_html=True)

    # The Problem
    st.subheader("The Problem: The Definition-Execution Gap")
    st.markdown("""
Most organisations cannot answer two simple questions with certainty:

1. **"What rules did your AI follow?"**
2. **"Can you prove it?"**

Today, governance logic is typically embedded in application code — hard-coded 
`if` statements that **drift** from the policy documents over time. Nobody notices 
until a regulator asks, or worse, until something goes wrong.

ODGS resolves this by **strictly separating what the rules say (Definition) from
what the systems do (Execution)**.
""")

    st.divider()

    # 5-Plane Architecture
    st.subheader("The 5-Plane Architecture")
    st.caption("A constitutional stack where mechanical execution is legally bound by semantic definitions")
    
    planes = [
        ("🏛️", "Governance", "The Mandate", "Captures human intent and policy scope", "Policy Documents"),
        ("📜", "Legislative", "The Definition", "72 metrics, 101 rules, 57 data quality dimensions — the semantic definition of truth", "standard_metrics.json"),
        ("⚖️", "Judiciary", "The Enforcer", "If Data ≠ Definition → Hard Stop. The logic engine that validates data.", "OdgsInterceptor"),
        ("🏢", "Executive", "The Context", "Maps definitions to business contexts (e.g., 'Fiscal Year 2026', 'EU Region')", "context_bindings.json"),
        ("🔌", "Physical", "The Reality", "Raw data streams, databases, APIs — connected via vendor-neutral adapters", "Adapter Layer"),
    ]
    
    for icon, name, role, desc, artifact in planes:
        st.markdown(f"""
<div class="plane-row">
    <div class="plane-icon">{icon}</div>
    <div>
        <div class="plane-name">Plane: {name} — {role}</div>
        <div class="plane-role">{desc}</div>
    </div>
    <div class="plane-artifact">{artifact}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # Three Key Innovations
    st.subheader("Three Key Innovations")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="guide-card">
    <div class="guide-icon">📜</div>
    <h4>Configuration as Law</h4>
    <p>Governance rules are externalised in immutable JSON files — not embedded in code. A policy change is a configuration update, not a software deployment.</p>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="guide-card">
    <div class="guide-icon">🛡️</div>
    <h4>Hard Stop / Administrative Recusal</h4>
    <p>When data doesn't match its definition, the system refuses to proceed. "Silence over Error" — preventing bad decisions rather than just logging them.</p>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="guide-card">
    <div class="guide-icon">🔐</div>
    <h4>Tri-Partite Binding</h4>
    <p>Every AI decision is cryptographically signed: what data was processed, which rule was applied, and in what context. An unbreakable evidence chain for Article 12.</p>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # Standards Alignment
    st.subheader("Standards Alignment")
    
    alignment_data = pd.DataFrame([
        {"Standard": "EU AI Act (2024/1689)", "Articles": "Art. 10, Art. 12", "ODGS Mechanism": "Data Quality Enforcement + Automatic Event Recording", "Status": "✅ Aligned"},
        {"Standard": "ISO/IEC 42001:2023", "Articles": "Clauses 4–10, Controls B.4–B.10", "ODGS Mechanism": "AI Management System via Legislative Plane", "Status": "✅ Aligned"},
        {"Standard": "NEN 381 525", "Articles": "Data, Cloud & Edge", "ODGS Mechanism": "Semantic Interoperability + Sovereign Sidecar", "Status": "✅ Aligned"},
        {"Standard": "GDPR (2016/679)", "Articles": "Art. 5, 25, 30, 35", "ODGS Mechanism": "Privacy-Native Architecture + Zero-Trust Logging", "Status": "✅ Aligned"},
        {"Standard": "Basel III/IV", "Articles": "CET1, LCR, NSFR, FRTB", "ODGS Mechanism": "Financial Metrics Governance Definitions", "Status": "✅ Aligned"},
    ])
    
    st.dataframe(alignment_data, use_container_width=True, hide_index=True)

    st.divider()

    # Who is this for?
    st.subheader("Who Is This For?")
    
    roles = [
        ("🏢", "CEO / Board", "Reduces regulatory risk. Provides evidence of \"due diligence\" for AI decisions."),
        ("📊", "Chief Data Officer", "Single source of truth for all data governance rules across the organisation."),
        ("⚖️", "Compliance Officer", "Pre-built alignment with EU AI Act, GDPR, ISO 42001, and Basel III."),
        ("💻", "Data Engineer", "Drop-in sidecar that works with Snowflake, PostgreSQL, dbt, Power BI."),
        ("🔍", "Regulator / Auditor", "Machine-readable governance validated with standard W3C tools."),
    ]
    
    role_cols = st.columns(len(roles))
    for idx, (icon, role, desc) in enumerate(roles):
        with role_cols[idx]:
            st.markdown(f"""
<div class="guide-card" style="text-align:center;">
    <div class="guide-icon">{icon}</div>
    <h4 style="font-size:0.95em;">{role}</h4>
    <p style="font-size:0.82em;">{desc}</p>
</div>
""", unsafe_allow_html=True)

# --- TAB 9: DQ OBSERVATORY ---
with tab9:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Data Quality Observatory</span>
        <div class="eu-subtitle">57 Data Quality Dimensions mapped across the DAMA framework · Linked to Metrics & Rules</div>
    </div>
</div>
""", unsafe_allow_html=True)

    dq_df = graph_engine.get_dq_dimensions_df()
    if not dq_df.empty:
        # KPI row
        dq_c1, dq_c2, dq_c3, dq_c4 = st.columns(4)
        with dq_c1:
            st.markdown(f"""
<div class="kpi-card kpi-blue">
    <div class="kpi-value">{len(dq_df)}</div>
    <div class="kpi-label">DQ Dimensions</div>
    <div class="kpi-sub">DAMA Framework</div>
</div>""", unsafe_allow_html=True)
        with dq_c2:
            cats = dq_df["Category"].nunique()
            st.markdown(f"""
<div class="kpi-card kpi-purple">
    <div class="kpi-value">{cats}</div>
    <div class="kpi-label">Categories</div>
    <div class="kpi-sub">Format, Datasets, Values…</div>
</div>""", unsafe_allow_html=True)
        with dq_c3:
            linked_m = dq_df["Linked Metrics"].sum()
            st.markdown(f"""
<div class="kpi-card kpi-green">
    <div class="kpi-value">{linked_m}</div>
    <div class="kpi-label">Metric Links</div>
    <div class="kpi-sub">Cross-references</div>
</div>""", unsafe_allow_html=True)
        with dq_c4:
            linked_r = dq_df["Linked Rules"].sum()
            st.markdown(f"""
<div class="kpi-card kpi-amber">
    <div class="kpi-value">{linked_r}</div>
    <div class="kpi-label">Rule Links</div>
    <div class="kpi-sub">Enforcement points</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Filter by category
        cat_filter = st.multiselect("Filter by Category", dq_df["Category"].unique(), default=dq_df["Category"].unique(), key="dq_cat_filter")
        filtered_dq = dq_df[dq_df["Category"].isin(cat_filter)]

        st.dataframe(
            filtered_dq[["ID", "Name", "Category", "Definition", "Unit", "Linked Metrics", "Linked Rules"]],
            use_container_width=True, hide_index=True
        )

        # Detail view
        st.divider()
        st.markdown("#### 🔬 Dimension Deep Dive")
        dim_options = {row["Name"]: row["ID"] for _, row in filtered_dq.iterrows()}
        sel_dim = st.selectbox("Select a dimension:", ["— Select —"] + list(dim_options.keys()), key="dq_detail_select")
        if sel_dim != "— Select —":
            detail = graph_engine.get_dq_dimension_detail(dim_options[sel_dim])
            if detail:
                dd1, dd2 = st.columns(2)
                with dd1:
                    with st.container(border=True):
                        st.markdown(f"**📊 Business Impact**")
                        impacts = detail.get("potentialBusinessImpacts", {})
                        if impacts.get("positive"):
                            st.markdown("**✅ Positive Impacts:**")
                            for p in impacts["positive"]:
                                st.markdown(f"- {p}")
                        if impacts.get("negative"):
                            st.markdown("**⚠️ Negative Impacts (if neglected):**")
                            for n in impacts["negative"]:
                                st.markdown(f"- {n}")
                with dd2:
                    with st.container(border=True):
                        st.markdown("**📋 Illustrative KPIs**")
                        for kpi in detail.get("illustrativeKpis", []):
                            st.markdown(f"- `{kpi}`")
                        st.divider()
                        st.markdown("**✅ Good Example:**")
                        for ex in (detail.get("exampleGood") or [])[:2]:
                            st.success(ex)
                        st.markdown("**❌ Poor Example:**")
                        for ex in (detail.get("examplePoor") or [])[:2]:
                            st.error(ex)
    else:
        st.warning("No DQ Dimensions found.")

# --- TAB 10: EXECUTIVE PLANE ---
with tab10:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Executive Plane — Operational Context</span>
        <div class="eu-subtitle">Business Process Maps · Context Bindings · Physical Data Layer</div>
    </div>
</div>
""", unsafe_allow_html=True)

    exec_sub = st.radio("View:", ["Business Processes", "Context Bindings", "Physical Data Map"], horizontal=True, key="exec_radio")

    if exec_sub == "Business Processes":
        processes = graph_engine.get_business_processes()
        if processes:
            st.markdown(f"**{len(processes)} Business Process Lifecycles loaded**")
            for proc in processes:
                with st.expander(f"🔄 {proc['lifecycleName']} ({proc['lifecycleId']})", expanded=False):
                    st.markdown(f"*{proc.get('description', '')}*")
                    pc1, pc2 = st.columns(2)
                    with pc1:
                        st.markdown("**Industries:**")
                        for ind in proc.get("typicalIndustries", []):
                            st.markdown(f"- {ind}")
                    with pc2:
                        st.markdown("**Stakeholders:**")
                        for s in proc.get("keyStakeholders", []):
                            st.markdown(f"- {s}")
                    st.divider()
                    st.markdown("**Process Stages:**")
                    for i, stage in enumerate(proc.get("stages", []), 1):
                        st.markdown(f"""
<div class="plane-row">
    <div class="plane-icon">{i}️⃣</div>
    <div>
        <div class="plane-name">{stage['stageName']}</div>
        <div class="plane-role">{stage.get('description', '')}</div>
    </div>
    <div class="plane-artifact">{stage['stageId']}</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No business process maps loaded.")

    elif exec_sub == "Context Bindings":
        contexts = graph_engine.get_all_contexts()
        if contexts:
            st.markdown(f"**{len(contexts)} Context Bindings** — each binding maps a process to its required metrics and rules")
            for ctx in contexts:
                with st.expander(f"🔗 {ctx['context_id']}", expanded=False):
                    st.markdown(f"*{ctx.get('description', '')}*")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown("**Required Metrics:**")
                        for m_urn in ctx.get("required_metrics", []):
                            st.code(m_urn, language="text")
                    with cc2:
                        st.markdown("**Enforcement Rules:**")
                        for r_urn in ctx.get("rules", []):
                            st.code(r_urn, language="text")
                    if ctx.get("effective_from"):
                        st.caption(f"Effective: {ctx['effective_from']} → {ctx.get('effective_until') or 'Ongoing'}")
        else:
            st.info("No context bindings loaded.")

    else:  # Physical Data Map
        maps = graph_engine.physical_maps
        if maps:
            st.markdown(f"**{len(maps)} Physical Bindings** — mapping abstract metrics to warehouse tables")
            for pm in maps:
                with st.expander(f"🔌 {pm['concept_name']} → {pm['map_id']}", expanded=False):
                    st.markdown(f"*{pm.get('description', '')}*")
                    st.caption(f"Concept URN: `{pm.get('concept_urn', '')}`")
                    if pm.get("vector_embedding_hint"):
                        st.info(f"🧠 **AI Hint:** {pm['vector_embedding_hint']}")
                    for binding in pm.get("bindings", []):
                        with st.container(border=True):
                            bc1, bc2 = st.columns(2)
                            with bc1:
                                st.markdown(f"**Platform:** `{binding.get('platform', '')}`")
                                tbl = binding.get("table", binding.get("catalog", ""))
                                st.markdown(f"**Table:** `{binding.get('schema','')}.{tbl}`")
                                st.markdown(f"**Granularity:** {binding.get('granularity', '—')}")
                            with bc2:
                                st.markdown(f"**Privacy:** `{binding.get('privacy_level', '—')}`")
                                st.markdown(f"**SLA:** `{binding.get('freshness_sla', '—')}`")
                                cols = binding.get("column_mapping", {})
                                if cols:
                                    st.markdown("**Columns:**")
                                    for concept, physical in cols.items():
                                        st.markdown(f"- `{concept}` → `{physical}`")
        else:
            st.info("No physical data maps loaded.")

# --- TAB 11: SOVEREIGN BRAKE SIMULATOR ---
with tab11:
    st.markdown("""
<div class="eu-header">
    <div>
        <span class="eu-title"><span class="eu-flag"></span> Sovereign Brake — Live Interceptor</span>
        <div class="eu-subtitle">Simulate the ODGS Hard Stop: Definition ≠ Data → Administrative Recusal</div>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
> **The Sovereign Brake** is the core enforcement mechanism of ODGS. When data does not match
> its statutory definition, the system **refuses to proceed** — preventing bad AI decisions
> rather than just logging them. This is the "Administrative Recusal" principle enshrined in
> the EU AI Act Article 10.
""")

    # Context selector
    contexts = graph_engine.get_all_contexts()
    if contexts:
        ctx_options = {f"{c['context_id']} — {c.get('description', '')[:60]}": c for c in contexts}
        selected_ctx_label = st.selectbox("Select Process Context:", list(ctx_options.keys()), key="brake_ctx")
        selected_ctx = ctx_options[selected_ctx_label]

        st.divider()

        # Show what this context requires
        sb1, sb2 = st.columns(2)
        with sb1:
            with st.container(border=True):
                st.markdown("**📋 Required Metrics**")
                for m_urn in selected_ctx.get("required_metrics", []):
                    m_id = m_urn.replace(URN_PREFIX_METRIC, "")
                    m_name = graph_engine.metrics.get(m_id, {}).get("name", m_id)
                    st.markdown(f"- 📊 **{m_name}** `{m_urn}`")
                if not selected_ctx.get("required_metrics"):
                    st.caption("No metrics required for this context.")
        with sb2:
            with st.container(border=True):
                st.markdown("**⚖️ Enforcement Rules**")
                for r_urn in selected_ctx.get("rules", []):
                    r_id = r_urn.replace(URN_PREFIX_RULE, "")
                    rule = graph_engine.rules.get(r_id, {})
                    sev = rule.get("severity", "—")
                    sev_colors = {'HARD_STOP': 'chip-critical', 'CRITICAL': 'chip-critical', 'HIGH': 'chip-high', 'MEDIUM': 'chip-medium'}
                    sev_chip = f' <span class="{sev_colors.get(sev, "chip-draft")}">{sev}</span>' if sev != "—" else ""
                    st.markdown(f"- 🛡️ **{rule.get('name', r_id)}**{sev_chip}", unsafe_allow_html=True)
                    if rule.get("logic_expression"):
                        st.code(rule["logic_expression"], language="python")
                if not selected_ctx.get("rules"):
                    st.caption("No rules bound to this context.")

        st.divider()

        # Simulation
        st.markdown("### ⚡ Run Simulation")
        st.caption("Provide sample data to test against the enforcement rules.")

        # Build input fields from rules
        rule_urns = selected_ctx.get("rules", [])
        sim_rules = []
        for r_urn in rule_urns:
            r_id = r_urn.replace(URN_PREFIX_RULE, "")
            rule = graph_engine.rules.get(r_id)
            if rule and rule.get("logic_expression"):
                sim_rules.append(rule)

        if sim_rules:
            with st.form("brake_sim_form"):
                st.markdown("**Data Context (simulated input):**")
                sim_data = {}

                # All rules evaluate against 'value' — provide a clean single input
                # rather than extracting false-positive variables from regex patterns
                st.caption("Enter a test value below. Each rule will check this value against its constraint.")
                
                sim_cols = st.columns([2, 1])
                with sim_cols[0]:
                    sim_data["value"] = st.text_input(
                        "📊 Test Value",
                        value="",
                        key="sim_value",
                        placeholder="e.g. NL, EUR, user@example.com, +31612345678",
                        help="This value will be tested against each enforcement rule"
                    )
                with sim_cols[1]:
                    st.markdown("")
                    st.markdown("")
                    st.info("💡 Try: **NL** (country), **EUR** (currency), **test@email.com** (email)")

                run_sim = st.form_submit_button("🚀 Execute Sovereign Brake", type="primary")

                if run_sim:
                    st.divider()
                    import re as _re
                    all_pass = True
                    for r in sim_rules:
                        expr = r.get("logic_expression", "")
                        rule_name = r.get("name", "Unknown")
                        severity = r.get("severity", "WARNING")
                        try:
                            from simpleeval import simple_eval
                            import datetime as _dt
                            safe_funcs = {
                                "regex_match": lambda p, v: bool(_re.match(p, str(v))),
                                "parse_date": lambda v: _dt.datetime.strptime(str(v)[:10], "%Y-%m-%d") if v else _dt.datetime.min,
                                "today": lambda: _dt.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                                "len": len,
                            }
                            result = simple_eval(expr, names=sim_data, functions=safe_funcs)
                            if result:
                                st.markdown(f"✅ **{rule_name}** — `PASS`")
                            else:
                                all_pass = False
                                if severity == "HARD_STOP":
                                    st.markdown(f"""
<div style="background:#FFEBE6; border:2px solid #BF2600; border-radius:8px; padding:12px; margin:6px 0;">
    <strong>🛑 HARD STOP — {rule_name}</strong><br>
    <code>{expr}</code> → <strong>FAILED</strong><br>
    <em>Administrative Recusal: Process blocked. The data does not match the statutory definition.</em>
</div>""", unsafe_allow_html=True)
                                else:
                                    st.warning(f"⚠️ **{rule_name}** — `FAILED` (Severity: {severity})")
                        except Exception as e:
                            st.error(f"❌ **{rule_name}** — Evaluation error: `{e}`")
                            all_pass = False

                    st.divider()
                    if all_pass:
                        st.markdown("""
<div style="background:#E3FCEF; border:2px solid #006644; border-radius:8px; padding:16px; text-align:center;">
    <div style="font-size:2em;">✅</div>
    <strong>SOVEREIGN HANDSHAKE COMPLETE</strong><br>
    All rules passed. Process may proceed under Tri-Partite Binding.
</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("""
<div style="background:#FFEBE6; border:2px solid #BF2600; border-radius:8px; padding:16px; text-align:center;">
    <div style="font-size:2em;">🛑</div>
    <strong>ADMINISTRATIVE RECUSAL</strong><br>
    One or more rules failed. The Sovereign Brake has been engaged. Process halted.
</div>""", unsafe_allow_html=True)
        else:
            st.info("No executable rules (with `logic_expression`) found for this context. Select a context with enforceable rules.")
    else:
        st.warning("No context bindings loaded. Cannot run simulation.")

