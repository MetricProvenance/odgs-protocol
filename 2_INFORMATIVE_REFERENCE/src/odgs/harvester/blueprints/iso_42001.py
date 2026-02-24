"""
ISO 42001 Harvester Blueprint
=============================
Harvests clause definitions from ISO/IEC 42001:2023 (AI Management System).

This blueprint demonstrates the "Universal Harvester" design principle:
any new standard (ISO, NEN, GDPR, Basel IV) can be added by:
  1. Registering a new entry in `harvester_registry.json`  — NO Python changes
  2. Implementing a new Blueprint class if the source format is novel  — rare

Architecture Goal: "Self-Describing Data"
  A node can discover a new standard's URN prefix (e.g. urn:odgs:def:iso:42001:*)
  and call `odgs harvest iso 6.1` to fetch it — without redeploying the codebase.

Status: SPEC / MOCK — ISO 42001 does not have a public machine-readable endpoint.
        The self-describing test (GDPR Art. 22) is answered in `UNIVERSAL_SPEC` below.
"""

from __future__ import annotations
import json
import ssl
import hashlib
import urllib.request
from typing import Dict, Any
from ..core import BaseHarvester, HarvesterException


# ── Harvester Registry — the "Self-Describing" config ─────────────────────────
# This is the key to data-driven extensibility.
# A new standard is registered HERE, not in Python code.
# The Python interpreter reads this at runtime and routes harvest() calls.
#
# Format:
#   authority_key  ->  { source_type, endpoint, authority_id, authority_name, ... }
#
# To add GDPR Article 22 with ZERO code changes:
#   1. Add "eu_gdpr" entry to this dict (or to an external harvester_registry.json)
#   2. Its source_type must match an existing BaseHarvester subclass ("jsonld", "xml", "static")
#   3. Call: odgs harvest eu_gdpr art_22
#
HARVESTER_REGISTRY: Dict[str, Dict] = {
    "nl_gov": {
        "source_type":    "xml",
        "endpoint":       "https://repository.officiele-overheidspublicaties.nl/bwb/BWBR0005537/2024-01-01_0/xml/BWBR0005537_2024-01-01_0.xml",
        "authority_id":   "NL_GOV",
        "authority_name": "Government of the Netherlands",
        "document_ref":   "Algemene wet bestuursrecht (AwB)",
        "blueprint":      "AwBHarvester",
        "language":       "nl-NL",
    },
    "fibo": {
        "source_type":    "jsonld",
        "endpoint":       "https://spec.edmcouncil.org/fibo/ontology/master/latest/FND/Accounting/CurrencyAmount.jsonld",
        "authority_id":   "FIBO",
        "authority_name": "Financial Industry Business Ontology",
        "document_ref":   "FIBO Master",
        "blueprint":      "FIBOHarvester",
        "language":       "en-US",
    },
    "iso": {
        "source_type":    "static",  # ISO 42001 has no public machine-readable endpoint
        "endpoint":       None,       # Override with local file or licensed API
        "authority_id":   "ISO",
        "authority_name": "International Organization for Standardization",
        "document_ref":   "ISO/IEC 42001:2023 — AI Management Systems",
        "blueprint":      "ISO42001Harvester",
        "language":       "en-US",
    },
    # ── GDPR: can be added HERE with no Python code changes ─────────────────
    # "eu_gdpr": {
    #     "source_type":    "static",
    #     "endpoint":       None,      # Plug in EUR-Lex API key when available
    #     "authority_id":   "EU",
    #     "authority_name": "European Union",
    #     "document_ref":   "General Data Protection Regulation (GDPR)",
    #     "blueprint":      "StaticHarvester",  # Uses local JSON file
    #     "language":       "en-EU",
    # },
}


# ── ISO 42001 Clause Map — the "self-describing" local dataset ─────────────────
# When no live endpoint exists, the harvester falls back to this curated map.
# Any clause not listed here returns a 404-style HarvesterException.
# Adding GDPR Art. 22 = add it to a similar dict, zero Python required.
ISO_42001_CLAUSES: Dict[str, Dict[str, str]] = {
    "4.1": {
        "title":       "Understanding the organisation and its context",
        "verbatim":    "The organisation shall determine external and internal issues that are "
                       "relevant to its purpose and that affect its ability to achieve the "
                       "intended outcome(s) of its AI management system.",
        "applicability": "All organisations deploying or developing AI systems subject to EU AI Act.",
    },
    "4.2": {
        "title":       "Understanding the needs and expectations of interested parties",
        "verbatim":    "The organisation shall determine the interested parties that are relevant "
                       "to the AI management system and the relevant requirements of these "
                       "interested parties.",
        "applicability": "Relevant to stakeholder mapping for AI governance boards.",
    },
    "6.1": {
        "title":       "Actions to address risks and opportunities",
        "verbatim":    "When planning for the AI management system, the organisation shall consider "
                       "the issues referred to in 4.1 and the requirements referred to in 4.2 and "
                       "determine the risks and opportunities that need to be addressed.",
        "applicability": "Directly maps to ODGS risk rule evaluation in OdgsInterceptor.",
    },
    "8.4": {
        "title":       "AI system impact assessment",
        "verbatim":    "The organisation shall conduct an AI system impact assessment to identify "
                       "and evaluate the potential impacts of its AI systems on individuals, groups "
                       "of individuals, and society.",
        "applicability": "Required for EU AI Act Art. 9 high-risk AI systems.",
    },
    "9.1": {
        "title":       "Monitoring, measurement, analysis and evaluation",
        "verbatim":    "The organisation shall determine what needs to be monitored and measured, "
                       "including AI system performance and AI system risks.",
        "applicability": "Maps to ODGS audit log obligations and the sovereign_audit.log pattern.",
    },
    "10.2": {
        "title":       "Nonconformity and corrective action",
        "verbatim":    "When a nonconformity occurs, the organisation shall react to the "
                       "nonconformity and, as applicable, take action to control and correct it "
                       "and deal with the consequences.",
        "applicability": "Maps to ProcessBlockedException in OdgsInterceptor.",
    },
}


# ── The Harvester ──────────────────────────────────────────────────────────────
class ISO42001Harvester(BaseHarvester):
    """
    Harvester for ISO/IEC 42001:2023 (AI Management System Standard).

    Since ISO does not publish a free machine-readable endpoint, this harvester
    uses a curated local clause map (ISO_42001_CLAUSES) as its source.
    This is the 'static' source_type in the HARVESTER_REGISTRY.

    To connect to a licensed ISO API (e.g. via ANSI or BSI):
        1. Set ISO_42001_API_ENDPOINT in .env
        2. Override _fetch_live() with the vendor's auth pattern
        3. No other changes needed — the SovereignDefinition structure is identical

    Usage:
        from odgs.harvester.blueprints.iso_42001 import ISO42001Harvester
        h = ISO42001Harvester()
        definition = h.harvest("6.1")   # Clause 6.1
    """

    SOURCE_TYPE = "static"
    REGISTRY_KEY = "iso"

    def harvest(self, reference_id: str) -> Dict[str, Any]:
        """
        Harvest an ISO 42001 clause by its clause number (e.g. "6.1", "9.1").

        Returns a SovereignDefinition-compatible dict with:
          - urn:odgs:def:iso:42001_<clause>:v2023
          - content_hash (SHA-256 of verbatim_text)
          - authority_id = "ISO"
        """
        clause_key = reference_id.strip()
        if clause_key not in ISO_42001_CLAUSES:
            available = ", ".join(sorted(ISO_42001_CLAUSES.keys()))
            raise HarvesterException(
                f"ISO 42001 clause '{clause_key}' not in local map. "
                f"Available: {available}. "
                f"To add it, append to ISO_42001_CLAUSES in iso_42001.py."
            )

        clause = ISO_42001_CLAUSES[clause_key]
        verbatim = f"Clause {clause_key}: {clause['title']}\n\n{clause['verbatim']}"
        content_hash = hashlib.sha256(verbatim.encode("utf-8")).hexdigest()

        # Normalise clause ID for URN (6.1 -> 42001_6_1)
        clause_urn_id = f"42001_{clause_key.replace('.', '_')}"

        return {
            "urn": f"urn:odgs:def:iso:{clause_urn_id}:v2023",
            "metadata": {
                "authority_id":   "ISO",
                "authority_name": "International Organization for Standardization",
                "document_ref":   "ISO/IEC 42001:2023 — AI Management Systems",
                "source_uri":     f"https://www.iso.org/standard/81230.html#clause-{clause_key}",
                "content_hash":   content_hash,
                "hierarchy": {
                    "level":     "section",
                    "parent_ref": "ISO/IEC 42001:2023",
                    "local_id":   clause_key,
                },
            },
            "relations": [],
            "content": {
                "verbatim_text": verbatim,
                "language":      "en-US",
                "format":        "TEXT",
                "structured_data": [
                    {"key": "clause_number", "value": clause_key},
                    {"key": "clause_title",  "value": clause["title"]},
                ],
            },
            "interpretation": {
                "summary":       clause["title"],
                "applicability": clause["applicability"],
            },
        }


# ── Universal Harvester Spec ───────────────────────────────────────────────────
UNIVERSAL_SPEC = """
UNIVERSAL HARVESTER — Architecture Specification
================================================

Q: Can the system ingest a NEW standard (GDPR Art. 22) without changing Python code?
A: YES — for standards with a supported source_type. Here's the proof:

STEP 1 — Add to HARVESTER_REGISTRY (this file, or harvester_registry.json):
    "eu_gdpr": {
        "source_type":    "static",
        "authority_id":   "EU",
        "authority_name": "European Union",
        "document_ref":   "General Data Protection Regulation (GDPR)",
        "blueprint":      "StaticHarvester",
        "language":       "en-EU",
    }

STEP 2 — Add clause data to a JSON file (no Python):
    data/gdpr_clauses.json:
    {
      "art_22": {
        "title": "Automated individual decision-making, including profiling",
        "verbatim": "The data subject shall have the right not to be subject to a decision...",
        "applicability": "Any automated processing that produces legal or similarly significant effects."
      }
    }

STEP 3 — Harvest (no redeployment):
    odgs harvest eu_gdpr art_22
    # Returns: urn:odgs:def:eu:gdpr_art_22:v2016

SOURCE TYPE SUPPORT MATRIX:
    static   → local JSON clause map (ISO, NEN, GDPR)         ← implemented
    xml      → government XML repositories (AwB, EUR-Lex)     ← implemented (nl_awb.py)
    jsonld   → W3C/FIBO JSON-LD ontologies                    ← implemented (fibo.py)
    sparql   → SPARQL endpoints (DBpedia, Wikidata)           ← roadmap v3.3
    pdf      → machine-readable PDFs via pdfminer             ← roadmap v4.0

Adding a new source_type = one new Python class + HARVESTER_REGISTRY entry.
Adding a new standard within an existing type = ZERO Python changes.
"""


if __name__ == "__main__":
    # Quick smoke test
    h = ISO42001Harvester()
    result = h.harvest("6.1")
    print(json.dumps(result, indent=2))
    print("\n--- UNIVERSAL SPEC ---")
    print(UNIVERSAL_SPEC)
