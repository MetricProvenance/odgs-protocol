#!/usr/bin/env python3
"""
Harvest all sovereign definitions from all 5 source blueprints.
Writes directly to ../1_NORMATIVE_SPECIFICATION/schemas/sovereign/ without needing the full 'odgs' package.

Usage:
    python3 scripts/run_all_harvesters.py
"""
import sys
import os
import json
import hashlib
from datetime import datetime

# Add the src directory to Python path (scripts are inside src/scripts now, so src is ..)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "1_NORMATIVE_SPECIFICATION", "schemas", "sovereign")

def save_definition(definition: dict, authority_subdir: str) -> str:
    """Save a sovereign definition to disk with content_hash."""
    # Ensure content_hash
    text = definition.get("content", {}).get("verbatim_text", "")
    if text:
        definition.setdefault("metadata", {})["content_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    definition.setdefault("metadata", {})["harvested_at"] = datetime.utcnow().isoformat() + "Z"

    save_dir = os.path.join(OUTPUT_BASE, authority_subdir)
    os.makedirs(save_dir, exist_ok=True)

    # Build filename from URN
    urn = definition.get("urn", "unknown")
    parts = urn.split(":")
    if len(parts) >= 5:
        filename = "_".join(parts[3:]) + ".json"
    else:
        filename = urn.replace(":", "_") + ".json"

    path = os.path.join(save_dir, filename)
    with open(path, "w") as f:
        json.dump(definition, f, indent=2, ensure_ascii=False)
    return path


def harvest_gdpr():
    """Harvest all GDPR articles (static)."""
    print("\n═══ GDPR Harvester ═══")
    from odgs.harvester.blueprints.gdpr import GDPRHarvester
    h = GDPRHarvester(output_dir=OUTPUT_BASE)
    articles = ["5", "6", "17", "25", "30", "35", "83"]
    count = 0
    for art in articles:
        try:
            defn = h.harvest(art)
            path = save_definition(defn, "eu_gdpr")
            print(f"  ✅ Art. {art}: {defn['metadata'].get('document_ref', '')} → {os.path.basename(path)}")
            count += 1
        except Exception as e:
            print(f"  ❌ Art. {art}: {e}")
    return count


def harvest_iso_42001():
    """Harvest all ISO 42001 clauses (static)."""
    print("\n═══ ISO 42001 Harvester ═══")
    from odgs.harvester.blueprints.iso_42001 import ISO42001Harvester
    h = ISO42001Harvester(output_dir=OUTPUT_BASE)
    clauses = ["4.1", "4.2", "6.1", "8.4", "9.1", "10.2"]
    count = 0
    for clause in clauses:
        try:
            defn = h.harvest(clause)
            path = save_definition(defn, "iso")
            print(f"  ✅ Clause {clause}: {defn.get('interpretation', {}).get('summary', '')} → {os.path.basename(path)}")
            count += 1
        except Exception as e:
            print(f"  ❌ Clause {clause}: {e}")
    return count


def harvest_basel():
    """Harvest all Basel III/IV concepts (static)."""
    print("\n═══ Basel III/IV Harvester ═══")
    from odgs.harvester.blueprints.basel import BaselHarvester
    h = BaselHarvester(output_dir=OUTPUT_BASE)
    concepts = ["CET1", "LCR", "NSFR", "LeverageRatio", "FRTB", "IRRBB", "OpRisk"]
    count = 0
    for concept in concepts:
        try:
            defn = h.harvest(concept)
            path = save_definition(defn, "bis_bcbs")
            print(f"  ✅ {concept}: {defn.get('interpretation', {}).get('summary', '')} → {os.path.basename(path)}")
            count += 1
        except Exception as e:
            print(f"  ❌ {concept}: {e}")
    return count


def harvest_nl_awb():
    """Harvest Dutch AwB articles (live XML from wetten.overheid.nl)."""
    print("\n═══ NL AwB Harvester (LIVE) ═══")
    from odgs.harvester.blueprints.nl_awb import AwBHarvester
    h = AwBHarvester(output_dir=OUTPUT_BASE)
    articles = ["1:3", "3:4", "4:8"]
    count = 0
    for art in articles:
        try:
            defn = h.harvest(art)
            path = save_definition(defn, "nl_gov")
            print(f"  ✅ Art. {art} → {os.path.basename(path)}")
            count += 1
        except Exception as e:
            print(f"  ❌ Art. {art}: {e}")
    return count


def harvest_fibo():
    """Harvest FIBO concepts (live JSON-LD from edmcouncil.org)."""
    print("\n═══ FIBO Harvester (LIVE) ═══")
    from odgs.harvester.blueprints.fibo import FIBOHarvester
    h = FIBOHarvester(output_dir=OUTPUT_BASE)
    concepts = [
        "InterestRate", "AccountingEquity", "CurrencyAmount", "LegalEntity",
        "FinancialInstrument", "RegulatoryAgency", "Loan", "DebtInstrument"
    ]
    count = 0
    for concept in concepts:
        try:
            defn = h.harvest(concept)
            path = save_definition(defn, "fibo")
            print(f"  ✅ {concept} → {os.path.basename(path)}")
            count += 1
        except Exception as e:
            print(f"  ❌ {concept}: {e}")
    return count


if __name__ == "__main__":
    print("🌐 ODGS Sovereign Harvester — Full Run")
    print(f"   Output: {os.path.abspath(OUTPUT_BASE)}")
    print("=" * 60)

    total = 0

    # Static harvesters first (guaranteed to work)
    total += harvest_gdpr()
    total += harvest_iso_42001()
    total += harvest_basel()

    # Live harvesters (network-dependent)
    total += harvest_nl_awb()
    total += harvest_fibo()

    print("\n" + "=" * 60)
    print(f"🏁 COMPLETE: {total} sovereign definitions harvested.")

    # List all files
    print(f"\n📁 Contents of {os.path.abspath(OUTPUT_BASE)}:")
    for root, dirs, files in os.walk(OUTPUT_BASE):
        for f in sorted(files):
            if f.endswith(".json") and f != "01-definitions-schema.json":
                rel = os.path.relpath(os.path.join(root, f), OUTPUT_BASE)
                print(f"  {rel}")
