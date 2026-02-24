"""
Semantic Certificate — ODGS v3.3
==============================
"SSL for Semantics": renders a SovereignDefinition as a TLS-style certificate
pane, and visualizes the Chain of Trust as a directed graphviz flow.

Designed to be called from dashboard.py as a new tab:

    from odgs.ui.semantic_certificate import render_certificate_tab, render_chain_tab
    with tab_cert:
        render_certificate_tab(graph_engine)
    with tab_chain:
        render_chain_tab(graph_engine)
"""

from __future__ import annotations
import hashlib
import streamlit as st
from typing import Optional


# ── CSS injected once ─────────────────────────────────────────────────────────
CERT_CSS = """
<style>
/* Dark certificate panel — enterprise TLS aesthetic */
.cert-panel {
    background: linear-gradient(160deg, #0F0F1A 0%, #1A1A2E 100%);
    border: 1px solid #2D2D5E;
    border-radius: 12px;
    padding: 24px 28px;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.83em;
    box-shadow: 0 4px 24px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
}
.cert-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #2D2D5E;
}
.cert-lock-green  { font-size: 2em; filter: drop-shadow(0 0 8px #43E97B88); }
.cert-lock-red    { font-size: 2em; filter: drop-shadow(0 0 8px #FF6B6B88); }
.cert-lock-synth  { font-size: 2em; filter: drop-shadow(0 0 8px #FFB34788); }
.cert-row         { display: flex; margin: 5px 0; line-height: 1.6; }
.cert-label       { color: #7C85F3; min-width: 162px; flex-shrink: 0; font-weight: 700; letter-spacing: 0.04em; }
.cert-value       { color: #C8D0E0; word-break: break-all; }
.cert-fingerprint { color: #43E97B; font-size: 0.82em; letter-spacing: 0.05em; font-weight: 600; }
.cert-urn         { color: #B794F4; }
.cert-section     {
    color: #5C6BC0;
    font-size: 0.72em;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 800;
    margin: 14px 0 7px 0;
    display: block;
}
.cert-divider { border: none; border-top: 1px solid #2D2D5E; margin: 14px 0; }

/* Protocol decision shields */
.shield-blocked {
    background: linear-gradient(135deg, #1A0808 0%, #2D0F0F 100%);
    border: 2px solid #C0392B;
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    box-shadow: 0 0 28px rgba(192, 57, 43, 0.35);
}
.shield-approved {
    background: linear-gradient(135deg, #081A0E 0%, #0F2D1A 100%);
    border: 2px solid #43E97B;
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
    box-shadow: 0 0 28px rgba(67, 233, 123, 0.25);
}
</style>
"""


# ── Data structure ─────────────────────────────────────────────────────────────
def build_semantic_certificate(sovereign_def: dict, enforcing_rules: list[dict]) -> dict:
    """
    Produce a 'Semantic Certificate' dict from a SovereignDefinition and its rules.
    Mirrors the field layout of a browser TLS certificate detail pane.
    """
    meta = sovereign_def.get("metadata", {})
    content = sovereign_def.get("content", {})
    urn = sovereign_def.get("urn", "")

    version_pin = urn.split(":")[-1] if urn.startswith("urn:") else "unknown"

    harvested_at = meta.get("harvested_at") or ""
    if version_pin.startswith("v") and version_pin[1:].isdigit():
        valid_from = f"{version_pin[1:]}-01-01"
    else:
        valid_from = harvested_at[:10] if harvested_at else "unknown"

    ch = meta.get("content_hash")
    verbatim = content.get("verbatim_text", "")
    if not ch and verbatim:
        ch = hashlib.sha256(verbatim.encode()).hexdigest()
    fingerprint_value = ch or "UNSIGNED — no content_hash present"

    authority = meta.get("authority_id", "UNKNOWN")
    if authority == "AI_SYNTHETIC":
        status = "SYNTHETIC"
    elif ch:
        status = "VALID"
    else:
        status = "UNSIGNED"

    source_uri = meta.get("source_uri") or ""
    if "overheid" in source_uri or "bwb" in source_uri.lower():
        harvest_method = "AwBHarvester (XML/BWBR)"
    elif "edmcouncil" in source_uri or "fibo" in source_uri.lower():
        harvest_method = "FIBOHarvester (JSON-LD)"
    elif "iso.org" in source_uri:
        harvest_method = "ISO42001Harvester (Static)"
    elif "eur-lex" in source_uri or "gdpr" in source_uri.lower() or authority == "EU_GDPR":
        harvest_method = "GDPRHarvester (EUR-Lex)"
    elif "bis.org" in source_uri or "basel" in source_uri.lower() or authority == "BIS_BASEL":
        harvest_method = "BaselHarvester (BIS)"
    elif authority == "AI_SYNTHETIC":
        harvest_method = "AI Factory (Synthetic)"
    else:
        harvest_method = "Manual / Unknown"

    return {
        "subject": {
            "urn":         urn,
            "common_name": f"{meta.get('document_ref', 'Unknown')} — {urn.split(':')[-2] if ':' in urn else urn}",
            "authority":   authority,
            "document":    meta.get("document_ref", "Unknown"),
            "language":    content.get("language", "en"),
        },
        "issuer": {
            "authority_id":   authority,
            "authority_name": meta.get("authority_name", "Unknown"),
            "source_uri":     source_uri or "— not recorded —",
            "harvest_method": harvest_method,
        },
        "validity": {
            "harvested_at":   harvested_at or "unknown",
            "valid_from":     valid_from,
            "version_pin":    version_pin,
        },
        "fingerprint": {
            "algorithm":       "SHA-256",
            "value":           fingerprint_value,
            "verbatim_length": len(verbatim),
        },
        "constraints": [
            {
                "rule_urn": r.get("urn", f"urn:odgs:rule:{r.get('rule_id','')}"),
                "name":     r.get("name", "Unknown Rule"),
                "domain":   r.get("domain", "—"),
            }
            for r in enforcing_rules
        ],
        "chain_of_trust": [
            f"① Source Authority — {meta.get('authority_name', 'Unknown')}",
            f"② {harvest_method} — fetches + seals verbatim_text",
            f"③ SovereignDefinition — URN bound, SHA-256 fingerprinted",
            "④ OdgsInterceptor — evaluates constraints against live data",
            "⑤ GitAuditLogger — immutable, tamper-evident audit record",
        ],
        "status": status,
    }


# ── Rendering helpers ──────────────────────────────────────────────────────────
def _row(label: str, value: str) -> str:
    return (
        f'<div class="cert-row">'
        f'<span class="cert-label">{label}</span>'
        f'<span class="cert-value">{value}</span>'
        f'</div>'
    )


def render_certificate_pane(cert: dict) -> None:
    """Render the TLS-style dark certificate panel in Streamlit."""
    st.markdown(CERT_CSS, unsafe_allow_html=True)

    status = cert["status"]
    if status == "VALID":
        lock = "🔒"
        lock_class = "cert-lock-green"
        status_color = "#43E97B"
        status_label = "VALID"
    elif status == "SYNTHETIC":
        lock = "🤖"
        lock_class = "cert-lock-synth"
        status_color = "#FFB347"
        status_label = "SYNTHETIC (AI)"
    else:
        lock = "🔓"
        lock_class = "cert-lock-red"
        status_color = "#FF6B6B"
        status_label = "UNSIGNED"

    subj = cert["subject"]
    issuer = cert["issuer"]
    validity = cert["validity"]
    fp = cert["fingerprint"]

    src = issuer["source_uri"]
    src_display = (f'<a href="{src}" target="_blank" style="color:#7C85F3">{src[:70]}…</a>'
                   if len(src) > 70 else src)

    html = f"""
<div class="cert-panel">
  <div class="cert-header">
    <span class="{lock_class}">{lock}</span>
    <div>
      <span style="color:#E0E6F8; font-size:1.1em; font-weight:700; letter-spacing:0.02em;">
        Semantic Certificate
      </span><br>
      <span style="color:{status_color}; font-size:0.88em; font-weight:600;">● {status_label}</span>
    </div>
  </div>

  <span class="cert-section">Subject</span>
  {_row("Common Name", subj["common_name"])}
  {_row("URN", f'<span class="cert-urn">{subj["urn"]}</span>')}
  {_row("Authority", subj["authority"])}
  {_row("Document", subj["document"])}
  {_row("Language", subj["language"])}

  <div class="cert-divider"></div>
  <span class="cert-section">Issuer</span>
  {_row("Authority ID", issuer["authority_id"])}
  {_row("Authority Name", issuer["authority_name"])}
  {_row("Harvest Method", issuer["harvest_method"])}
  {_row("Source URI", src_display)}

  <div class="cert-divider"></div>
  <span class="cert-section">Validity</span>
  {_row("Valid From", validity["valid_from"])}
  {_row("Harvested At", validity["harvested_at"])}
  {_row("Version Pin", validity["version_pin"])}

  <div class="cert-divider"></div>
  <span class="cert-section">Fingerprint</span>
  {_row("Algorithm", fp["algorithm"])}
  <div class="cert-row">
    <span class="cert-label">Value</span>
    <span class="cert-fingerprint">{fp["value"]}</span>
  </div>
  {_row("Verbatim Length", f'{fp["verbatim_length"]:,} chars')}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

    if cert["constraints"]:
        st.markdown("")
        st.markdown("**🛡️ Active Constraints**")
        for c in cert["constraints"]:
            st.markdown(f"- `{c['rule_urn']}` — **{c['name']}** _{c['domain']}_")
    else:
        st.caption("_No constraints linked via ontology graph._")


def render_protocol_decision(approved: bool, violations: list[str] | None = None) -> None:
    """Render the 'Blocked by Protocol' shield or the green Approved state."""
    st.markdown(CERT_CSS, unsafe_allow_html=True)
    if approved:
        st.markdown("""
<div class="shield-approved">
  <div style="font-size:2.8em;">🔒</div>
  <div style="color:#43E97B; font-weight:800; font-size:1.3em; margin-top:10px; letter-spacing:0.05em;">
    PROTOCOL APPROVED
  </div>
  <div style="color:#A0B8A8; margin-top:8px; font-size:0.9em;">
    All constraints satisfied. Audit record written.
  </div>
</div>""", unsafe_allow_html=True)
    else:
        violations_html = "".join(
            f'<div style="color:#FF8A80; margin-top:6px; font-size:0.88em; text-align:left;">⛔ {v}</div>'
            for v in (violations or ["Unknown violation"])
        )
        st.markdown(f"""
<div class="shield-blocked">
  <div style="font-size:2.8em;">🔴</div>
  <div style="color:#FF6B6B; font-weight:800; font-size:1.3em; margin-top:10px; letter-spacing:0.05em;">
    BLOCKED BY PROTOCOL
  </div>
  <div style="color:#B8A0A0; margin-top:8px; font-size:0.9em;">
    Governance enforcement triggered. Operation halted.
  </div>
  <div style="margin-top:14px; background:rgba(192,57,43,0.15); padding:12px 16px; border-radius:8px; border-left:3px solid #C0392B;">
    {violations_html}
  </div>
</div>""", unsafe_allow_html=True)


# ── Chain of Trust — DOT string, no graphviz package required ─────────────────
def _build_chain_dot(cert: dict) -> str:
    """
    Build a Graphviz DOT string for the Semantic Chain of Trust diagram.
    Uses st.graphviz_chart() which renders via browser-side d3-graphviz —
    no Python 'graphviz' package or system binary needed.
    """
    authority_name = cert["issuer"]["authority_name"].replace('"', "'")
    doc_ref = cert["subject"]["document"][:32].replace('"', "'")
    urn_tail = cert["subject"]["urn"].split(":")[-2] if ":" in cert["subject"]["urn"] else cert["subject"]["urn"]
    harvest_method = cert["issuer"]["harvest_method"].replace('"', "'")
    fp_short = cert["fingerprint"]["value"][:16] + "..."
    status = cert["status"]

    def_fill = "#1A7A4A" if status == "VALID" else ("#B7630A" if status == "SYNTHETIC" else "#8B1A1A")

    constraint_block = ""
    if cert["constraints"]:
        names = "\\n".join(c["name"][:24] for c in cert["constraints"][:3])
        constraint_block = f"""
    rules [
        label="Constraints\\n{names}"
        shape=diamond style=filled
        fillcolor="#7B2D2D" fontcolor="#FFAAAA" fontsize="10"
    ]
    definition -> rules [
        label="enforces" color="#C0392B" fontcolor="#C0392B"
        fontsize="9" style=dashed penwidth="1.5"
    ]
    rules -> interceptor [
        label="governs" color="#C0392B" fontcolor="#C0392B"
        fontsize="9" style=dashed penwidth="1.5"
    ]"""

    return f"""digraph SemanticSSL {{
    rankdir=LR;
    bgcolor="transparent";
    pad="0.5";
    nodesep="0.55";
    ranksep="0.9";
    node [fontname="Helvetica" fontsize="11" margin="0.18,0.12"];
    edge [fontsize="9" fontname="Helvetica" color="#4A4A6A" fontcolor="#9090B0" penwidth="1.6"];

    source [
        label="Source Authority\\n{authority_name}\\n{doc_ref}"
        shape=cylinder style=filled
        fillcolor="#4A3580" fontcolor="#E0D0FF" fontsize="10"
    ]
    harvester [
        label="Harvester\\n{harvest_method}"
        shape=component style=filled
        fillcolor="#0D5C8A" fontcolor="#C0E8FF" fontsize="10"
    ]
    definition [
        label="SovereignDefinition\\n{urn_tail}\\nSHA-256: {fp_short}"
        shape=box style="filled,rounded"
        fillcolor="{def_fill}" fontcolor="#D0FFE8" fontsize="10"
    ]
    interceptor [
        label="OdgsInterceptor\\nRule Engine"
        shape=hexagon style=filled
        fillcolor="#7A5A00" fontcolor="#FFE5A0" fontsize="10"
    ]
    audit [
        label="Audit Log\\nGit-backed\\nTamper-evident"
        shape=cylinder style=filled
        fillcolor="#0A5A3A" fontcolor="#A0FFCC" fontsize="10"
    ]

    source -> harvester      [label="fetch + verify TLS"]
    harvester -> definition  [label="seal SHA-256"]
    definition -> interceptor [label="URN lookup"]
    interceptor -> audit     [label="write_entry()"]
    {constraint_block}
}}"""


def render_chain_of_trust(cert: dict) -> None:
    """Render the Semantic Chain as a left-to-right graphviz flow diagram."""
    dot = _build_chain_dot(cert)
    st.graphviz_chart(dot, use_container_width=True)


# ── Tab renderers called from dashboard.py ────────────────────────────────────
def render_certificate_tab(graph_engine) -> None:
    """Drop-in tab for the Semantic Certificate viewer."""
    st.header("🔐 Semantic Certificate")
    st.caption(
        "Every sovereign definition carries a cryptographic fingerprint bound to its "
        "issuing authority — the data equivalent of a TLS certificate."
    )

    if not graph_engine.definitions:
        st.error("No Sovereign Definitions loaded. Run `odgs harvest nl_awb 1:3` first.")
        return

    def_options = {
        f"{d.get('urn', 'unknown')} [{d.get('metadata', {}).get('authority_id', '?')}]": urn
        for urn, d in graph_engine.definitions.items()
    }
    selected_label = st.selectbox("Select a Sovereign Definition:", def_options.keys())
    selected_urn = def_options[selected_label]
    sovereign_def = graph_engine.definitions[selected_urn]

    enforcing_rules = []
    for edge in graph_engine.edges:
        if (edge.get("source_urn") == selected_urn
                and edge.get("relationship") == "VALIDATED_BY"):
            rule_urn = edge.get("target_urn", "")
            if rule_urn in graph_engine.rules:
                enforcing_rules.append(graph_engine.rules[rule_urn])

    cert = build_semantic_certificate(sovereign_def, enforcing_rules)

    col_cert, col_json = st.columns([3, 2])
    with col_cert:
        render_certificate_pane(cert)
    with col_json:
        st.caption("Raw Certificate JSON")
        st.json(cert)

    st.divider()

    st.subheader("Protocol Enforcement Simulator")
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        if st.button("✅ Simulate: Compliant Payload", use_container_width=True):
            render_protocol_decision(approved=True)
    with sim_col2:
        if st.button("🚫 Simulate: Rule Violation", use_container_width=True):
            render_protocol_decision(
                approved=False,
                violations=[
                    "Rule 2001 Failed: country_code 'Holland' is not ISO 3166-1 alpha-2",
                    "Rule 2002 Failed: currency 'Euro' is not ISO 4217 (expected 'EUR')",
                ]
            )


def render_chain_tab(graph_engine) -> None:
    """Drop-in tab for the Chain of Trust graph view."""
    st.header("🔗 Chain of Trust")
    st.caption(
        "The Semantic Chain: from Sovereign Law → JSON Definition → Rule Engine → Audit Log. "
        "This is what makes ODGS 'SSL for Semantics.'"
    )

    if not graph_engine.definitions:
        st.error("No definitions loaded.")
        return

    def_options = {
        f"{urn.split(':')[-2]} [{d.get('metadata', {}).get('authority_id', '?')}]": urn
        for urn, d in graph_engine.definitions.items()
    }
    selected_label = st.selectbox("Trace chain for:", def_options.keys(), key="chain_select")
    selected_urn = def_options[selected_label]
    sovereign_def = graph_engine.definitions[selected_urn]

    enforcing_rules = [
        graph_engine.rules[edge.get("target_urn", "")]
        for edge in graph_engine.edges
        if (edge.get("source_urn") == selected_urn
            and edge.get("relationship") == "VALIDATED_BY"
            and edge.get("target_urn") in graph_engine.rules)
    ]
    cert = build_semantic_certificate(sovereign_def, enforcing_rules)
    render_chain_of_trust(cert)

    st.divider()
    st.subheader("🌐 Harvest New Standard")
    with st.form("harvest_form"):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            harvest_urn = st.text_input(
                "Standard URN",
                placeholder="e.g. urn:odgs:def:iso:42001:v2023  or  urn:odgs:def:eu:gdpr_art_25:v2016",
                help="Supported blueprints: nl_awb (Dutch AwB), fibo (FIBO), iso_42001, gdpr (EU GDPR), basel (Basel III)"
            )
        with col_b:
            ref_id = st.text_input("Reference ID", placeholder="e.g. 6.1  or  art_22")

        submitted = st.form_submit_button("Harvest →", type="primary")
        if submitted and harvest_urn:
            authority = harvest_urn.split(":")[3] if harvest_urn.count(":") >= 3 else "unknown"
            st.info(
                f"**Authority detected:** `{authority}`\n\n"
                f"Blueprints registered: `nl_awb` → AwBHarvester, `fibo` → FIBOHarvester, "
                f"`iso_42001` → ISO42001Harvester, `gdpr` → GDPRHarvester, `basel` → BaselHarvester."
            )
            st.warning(
                "Live harvest via the `odgs harvest` CLI. "
                "Use: `odgs harvest <blueprint> <reference_id>` to fetch and seal definitions."
            )
