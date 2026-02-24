import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from odgs.core.models import SovereignDefinition

from odgs.system.config import settings

# Wrapper for Structured Output
class SovereignBundle(BaseModel):
    items: List[SovereignDefinition]


# ---------------------------------------------------------------------------
# Context Loaders — feed ALL 5 planes to the AI
# ---------------------------------------------------------------------------

def _load_standard_metrics_context() -> str:
    """Load summary of Standard Metrics for AI context (Legislative Plane)."""
    path = settings.PROJECT_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative" / "standard_metrics.json"
    if not path.exists():
        return "No Standard Metrics found."
    try:
        data = json.loads(path.read_text())
        summary = [f"- {m['metric_id']}: {m['name']} ({m.get('domain','General')})" for m in data]
        return "\n".join(summary[:50])
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logging.warning(f"Error loading metrics context: {e}")
        return "Error loading metrics."


def _load_rules_context() -> str:
    """Load summary of Data Rules for AI context (Legislative Plane)."""
    path = settings.PROJECT_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative" / "standard_data_rules.json"
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text())
        summary = [
            f"- {r['rule_id']}: {r['name']} [severity={r.get('severity','medium')}]"
            for r in data[:30]
        ]
        return "\n".join(summary)
    except (json.JSONDecodeError, KeyError, OSError):
        return ""


def _load_dq_dimensions_context() -> str:
    """Load summary of DQ Dimensions for AI context (Judiciary Plane)."""
    path = settings.PROJECT_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "judiciary" / "standard_dq_dimensions.json"
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text())
        # Group by category for conciseness
        cats: Dict[str, int] = {}
        for d in data:
            cat = d.get("category", "Other")
            cats[cat] = cats.get(cat, 0) + 1
        summary = [f"- {cat}: {cnt} dimensions" for cat, cnt in sorted(cats.items())]
        return "\n".join(summary)
    except (json.JSONDecodeError, KeyError, OSError):
        return ""


def _load_business_processes_context() -> str:
    """Load summary of Business Processes for AI context (Executive Plane)."""
    path = settings.PROJECT_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "executive" / "business_process_maps.json"
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text())
        # Handle both list format and dict-with-lifecycles format
        if isinstance(data, list):
            lifecycles = data
        elif isinstance(data, dict):
            lifecycles = data.get("lifecycles", [])
        else:
            return ""
        summary = []
        for lc in lifecycles[:10]:
            if not isinstance(lc, dict):
                continue
            lc_id = lc.get("lifecycleId") or lc.get("lifecycle_id", "unknown")
            lc_name = lc.get("lifecycleName") or lc.get("name", "")
            stages = lc.get("stages", [])
            summary.append(f"- {lc_id}: {lc_name} ({len(stages)} stages)")
        return "\n".join(summary)
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return ""


def _build_metric_index() -> Dict[str, Dict[str, Any]]:
    """Build a lookup index of all metrics for fuzzy matching."""
    path = settings.PROJECT_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative" / "standard_metrics.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {
            m["metric_id"]: {
                "name": m.get("name", ""),
                "domain": m.get("domain", "General"),
                "keywords": set(m.get("name", "").lower().split())
                | set(m.get("domain", "").lower().split()),
            }
            for m in data
        }
    except (json.JSONDecodeError, KeyError, OSError):
        return {}


def _fuzzy_match_metric(text: str, metric_index: Dict[str, Dict]) -> Optional[str]:
    """Find the best-matching metric URN for a given text using token overlap."""
    if not metric_index:
        return None
    words = set(text.lower().split())
    best_id, best_score = None, 0
    for mid, info in metric_index.items():
        score = len(words & info["keywords"])
        if score > best_score:
            best_score = score
            best_id = mid
    return f"urn:odgs:metric:{best_id}" if best_id and best_score > 0 else None


# ---------------------------------------------------------------------------
# Post-Generation Enrichment
# ---------------------------------------------------------------------------

def _enrich_bundle(items: List[SovereignDefinition]) -> List[SovereignDefinition]:
    """
    Post-generation enrichment pass:
    1. Auto-generate content_hash (SHA-256 of verbatim_text)
    2. Fuzzy-match to closest metric URN if relations are empty
    3. Set harvested_at timestamp
    """
    metric_index = _build_metric_index()
    enriched = []

    for item in items:
        # 1. Content hash
        text = item.content.verbatim_text or ""
        if text and not item.metadata.content_hash:
            item.metadata.content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # 2. Timestamp
        item.metadata.harvested_at = datetime.now(timezone.utc)

        # 3. Fuzzy metric linking (fill missing relations)
        if not item.relations:
            match = _fuzzy_match_metric(
                f"{item.content.verbatim_text} {item.interpretation.summary if item.interpretation else ''}",
                metric_index,
            )
            if match:
                from odgs.core.models import SovereignRelation, RelationType
                item.relations.append(
                    SovereignRelation(type=RelationType.IS_DEFINED_BY, target_urn=match)
                )

        enriched.append(item)

    return enriched


def _load_file_contents(files: List[str]) -> str:
    """Load multiple files and concatenate their contents for context."""
    context_parts = []
    for fpath in files:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r") as f:
                    content = f.read()
                context_parts.append(f"--- FILE: {os.path.basename(fpath)} ---\n{content[:3000]}")
            except Exception:
                pass
    return "\n\n".join(context_parts) if context_parts else "No context files available."


# ---------------------------------------------------------------------------
# Core Generation Function
# ---------------------------------------------------------------------------

def generate_bundle(industry: str, api_key: str = None) -> List[SovereignDefinition]:
    """
    Generates a list of Sovereign Definitions for a specific industry.
    Uses Google Gemini with strict Pydantic schema enforcement.
    Includes post-generation enrichment (content_hash, metric linking).
    """
    print(f"🏭 ODGS FACTORY: Synthesizing Governance Bundle for '{industry}'...")

    # Resolve API Key (Argument > Env/Config)
    final_key = api_key or settings.GEMINI_API_KEY
    if not final_key:
        print("❌ Error: No API Key provided.")
        return []

    try:
        client = genai.Client(api_key=final_key)
    except Exception as e:
        print(f"❌ Error initializing Gemini Client: {e}")
        return []

    # Load context from ALL 5 planes
    metrics_context = _load_standard_metrics_context()
    rules_context = _load_rules_context()
    dq_context = _load_dq_dimensions_context()
    process_context = _load_business_processes_context()

    # System Prompt: The Chief Data Officer Persona (v2 — all-planes)
    system_prompt = f"""You are the Chief Data Officer for the '{industry}' sector.
Your task is to define the Critical Data Elements (CDEs), Key Performance Indicators (KPIs),
and regulatory compliance concepts that are essential for this industry.

You have access to the FULL ODGS Protocol context across all 5 governance planes:

═══ LEGISLATIVE PLANE — Standard Metrics ═══
{metrics_context}

═══ LEGISLATIVE PLANE — Data Quality Rules ═══
{rules_context}

═══ JUDICIARY PLANE — DQ Dimension Categories ═══
{dq_context}

═══ EXECUTIVE PLANE — Business Process Lifecycles ═══
{process_context}

═══════════════════════════════════════════════

INSTRUCTIONS — PRODUCE 15-20 DEFINITIONS:
1. Define 15-20 critical governance concepts for {industry}.
   Include a MIX of: CDEs, KPIs, regulatory requirements, risk indicators, and compliance controls.
2. Assign each a unique Sovereign URN: urn:odgs:def:ai_synthetic:<slug>:v1
   The <slug> must be lowercase, underscore-separated, descriptive (e.g. customer_churn_rate).
3. MAPPING: Identify the most relevant Standard Metric from the list above.
4. BINDING: Populate the `relations` array with at least one relation:
   - type: "isDefinedBy"
   - target_urn: "urn:odgs:metric:<METRIC_ID>" (e.g. urn:odgs:metric:M-001)
   If no direct match exists, map to the closest Quality or Compliance metric.
5. Write RICH verbatim_text (2-4 sentences) explaining the concept, its regulatory basis,
   and why it matters for data governance. Do NOT write one-liners.
6. Write a meaningful interpretation.summary and interpretation.applicability.

CONSTRAINTS:
- Authority must be "AI_SYNTHETIC".
- authority_name must be "ODGS AI Factory".
- document_ref must be "AI-Generated Governance Bundle".
- Produce at MINIMUM 15 definitions. 20 is preferred.
- EVERY definition must have a valid `relations` entry linking to a metric.
- Content language must be "en-US".
- Content format must be "TEXT".
"""

    print(f"🤖 Prompting {settings.GEMINI_MODEL_NAME} with all-planes context...")

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=f"Generate the Sovereign Data Governance bundle for {industry}. Produce at least 15 rich, detailed definitions.",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SovereignBundle
            )
        )
    except Exception as e:
         print(f"❌ Generation Error: {e}")
         return []

    if unused := response.parsed:
        bundle = unused
        print(f"✨ Raw Output: {len(bundle.items)} items generated.")

        # Post-Processing: Enrichment
        enriched_items = _enrich_bundle(bundle.items)

        # Validation
        valid_items = []
        for item in enriched_items:
            try:
                valid_items.append(item)
            except ValidationError as e:
                print(f"⚠️ Validation Failed for item: {e}")

        print(f"✅ Validated & Enriched: {len(valid_items)} Sovereign Definitions ready.")
        return valid_items

    print("⚠️ No output parsed.")
    return []


# ---------------------------------------------------------------------------
# API-facing functions (used by odgs.system.api)
# ---------------------------------------------------------------------------

def generate_with_gemini(industry: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Generate a governance bundle via Gemini. Returns a dict with
    'definitions' and 'metadata' keys, or None on failure.

    This is the API-facing wrapper around generate_bundle().
    """
    print(f"🤖 Agent Directives Received: {industry}")
    items = generate_bundle(industry, api_key)

    if not items:
        return None

    # Convert SovereignDefinition Pydantic models to dicts
    definitions = [item.model_dump(mode="json") for item in items]

    return {
        "definitions": definitions,
        "metadata": {
            "industry": industry,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": settings.GEMINI_MODEL_NAME,
            "protocol_version": "3.3.0",
            "total_definitions": len(definitions)
        }
    }


def write_bundle(data: Dict[str, Any], output_dir: str) -> None:
    """
    Write a generated governance bundle to the filesystem.
    Creates definitions.json, bundle_metadata.json, and ontology_graph.json.
    """
    os.makedirs(output_dir, exist_ok=True)

    definitions = data.get("definitions", [])
    metadata = data.get("metadata", {})

    # Write definitions
    defs_path = os.path.join(output_dir, "definitions.json")
    with open(defs_path, "w") as f:
        json.dump(definitions, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved {len(definitions)} definitions → {defs_path}")

    # Write metadata
    meta_path = os.path.join(output_dir, "bundle_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  💾 Saved metadata → {meta_path}")

    # Generate ontology graph from the definitions
    edges = []
    for defn in definitions:
        for rel in defn.get("relations", []):
            edges.append({
                "source": defn.get("urn", ""),
                "target": rel.get("target_urn", ""),
                "relation": rel.get("type", "isDefinedBy"),
                "provenance": "AI_SYNTHETIC"
            })

    if edges:
        graph_path = os.path.join(output_dir, "ontology_graph.json")
        with open(graph_path, "w") as f:
            json.dump({"edges": edges}, f, indent=2)
        print(f"  💾 Saved ontology graph ({len(edges)} edges) → {graph_path}")

    print(f"  📁 Bundle written to: {output_dir}")


def run_agent_chat(prompt: str, files: List[str], api_key: str) -> str:
    """
    Interactive chat with the ODGS Governance AI.
    Accepts a prompt and optional context files, returns the AI response.
    """
    if not api_key:
        return "❌ Error: No API key provided. Set GEMINI_API_KEY in your environment."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"❌ Failed to initialize Gemini: {e}"

    model_name = settings.GEMINI_MODEL_NAME

    # Build context from files
    file_context = _load_file_contents(files)

    system_persona = """You are the ODGS Sovereign Governance AI — an expert system
that operates within the Open Data Governance Standard (ODGS) protocol.
You understand EU AI Act compliance, GDPR data quality requirements,
ISO 42001, Basel III/IV, and FIBO ontology concepts.
You reference ODGS concepts: Sovereign Definitions, Tri-Partite Bindings,
Semantic Certificates, and the 5-Plane Architecture."""

    full_prompt = f"""{system_persona}

CONTEXT — GOVERNANCE ARTIFACTS LOADED:
{file_context}

USER QUERY:
{prompt}

Respond with clear, structured analysis. Reference specific ODGS concepts,
metrics, and regulatory frameworks."""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=4096,
            )
        )
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {e}"
