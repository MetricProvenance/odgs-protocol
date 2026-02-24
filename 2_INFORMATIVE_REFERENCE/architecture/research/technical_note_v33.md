# Technical Note: What's New in ODGS v3.3.0

**Companion to:** *"The Quality-Liability Fallacy: Why Your Data Governance Can't Protect You from the EU AI Act"*
**Authors:** Kartik Iyer, Metric Provenance B.V.
**Date:** February 2026
**DOI:** 10.5281/zenodo.18564270

---

## Abstract

This technical note supplements our original whitepaper (v3.0.0) with the architectural innovations introduced in ODGS v3.1.0 through v3.3.0. While the whitepaper's core thesis — that data quality frameworks alone cannot satisfy the EU AI Act's requirements for deterministic AI safety — remains valid and unchanged, the reference implementation has evolved significantly.

This document covers four major additions:

1. **The Sovereign Handshake** — content-addressed integrity verification
2. **The Tri-Partite Binding** — cryptographic audit trail
3. **The Sovereign Harvester** — self-describing data governance with 5 authoritative sources
4. **The W3C OWL/RDF Ontology** — formal semantic specification

---

## 1. The Sovereign Handshake

### Problem Statement

The original whitepaper identified a critical gap: even if governance definitions are externalized in JSON, there is no mechanism to detect **tampering**. A malicious actor could modify a definition file and the system would continue operating on corrupted rules.

### Solution: Content-Addressed Integrity

ODGS v3.1.0 introduced the **Sovereign Handshake** — a cryptographic verification step that occurs before any data processing:

```
1. At harvest time: SHA-256(definition_content) → stored as content_hash
2. At runtime: SHA-256(loaded_definition) → computed_hash
3. Handshake: computed_hash == stored_hash?
   ✅ → Proceed (definition integrity verified)
   ❌ → HARD STOP (TAMPERED_DEFINITION detected)
```

**Significance:** This converts the governance layer from "trust-based" to "verify-based." The system operates on a **zero-trust model** where even its own configuration files are treated as potentially compromised.

### Relationship to Whitepaper

The whitepaper's Section 4 ("The Compliance Severity Level") assumes definition integrity. The Sovereign Handshake makes this assumption explicit and enforceable.

---

## 2. The Tri-Partite Binding

### Problem Statement

EU AI Act Article 12 requires "automatic recording of events." But *what* should be recorded? A simple log of "Rule X was applied to Data Y" is insufficient for forensic reconstruction.

### Solution: Three-Hash Evidence

ODGS v3.2.0 introduced the **Tri-Partite Binding**, which cryptographically binds three independent elements in every audit log entry:

| Element | What It Proves | Privacy Stance |
|---|---|---|
| **Input Data Hash** | *What* was processed | Data never leaves the perimeter |
| **Definition Hash** | *Which* rule was applied | Sovereign Handshake verified |
| **Configuration Hash** | *In what context* | Business context is traceable |

**Forensic use case:** An auditor can reconstruct any decision by:
1. Identifying the audit log entry
2. Verifying the three hashes against their sources
3. Reproducing the exact decision path

This provides **reproducible governance** — the ability to deterministically replay any AI decision.

### Relationship to Whitepaper

The whitepaper's Logistics Giant case study (Section 5) describes a scenario where "1.7 million deliveries lacked a valid customs declaration." With Tri-Partite Binding, the *exact* rule version, data state, and configuration context for each of those 1.7 million decisions would be forensically traceable.

---

## 3. The Sovereign Harvester

### Problem Statement

The whitepaper argues that governance definitions must be "legally binding." But if organizations author their own definitions, who validates them against the actual law?

### Solution: Self-Describing Governance

ODGS v3.2.0 introduced the **Sovereign Harvester** — a framework for ingesting definitions directly from authoritative external sources:

| Source | Blueprint | Authority | Example Harvest |
|---|---|---|---|
| Dutch AwB | `nl_awb` | wetten.overheid.nl | `odgs harvest nl_awb 1:3` |
| FIBO Ontology | `fibo` | spec.edmcouncil.org | `odgs harvest fibo InterestRate` |
| ISO 42001 | `iso_42001` | iso.org | `odgs harvest iso_42001 4` |
| EU GDPR | `gdpr` | eur-lex.europa.eu | `odgs harvest gdpr 25` |
| Basel III/IV | `basel` | bis.org | `odgs harvest basel CET1` |

**Key design principle:** Adding a new source requires **zero Python code changes** — only a new entry in the harvester registry. This makes the governance framework extensible by data stewards, not just developers.

### What Gets Harvested

Each harvested definition becomes a **Sovereign Definition** — a content-addressed, SHA-256-hashed, immutable record:

```json
{
  "urn": "urn:odgs:def:eu:gdpr:art_25:v2016",
  "metadata": {
    "authority_id": "EU_GDPR",
    "source_uri": "https://eur-lex.europa.eu/...",
    "content_hash": "sha256:a3f2b..."
  },
  "content": {
    "verbatim_text": "The controller shall implement appropriate technical...",
    "language": "en"
  }
}
```

### Relationship to Whitepaper

The whitepaper's recommendation (Section 7) calls for "a complementary system-level safeguard." The Sovereign Harvester is that safeguard — it ensures that governance definitions are not just internally consistent, but traceable to their legal origins.

---

## 4. The W3C OWL/RDF Ontology

### Problem Statement

The ODGS knowledge graph (72 metrics, 101 rules, 57 dimensions, 50 processes, 30 factors) exists as JSON. While human-readable, it is not machine-reasonable in the Semantic Web sense.

### Solution: Formal Ontology

ODGS v3.3.0 introduced `specifications/ontology_graph.owl` — a W3C-standard OWL/RDF formal ontology that makes the entire governance graph:

1. **Queryable** via SPARQL
2. **Reasoner-compatible** (HermiT, Pellet, FaCT++)
3. **Interoperable** with external ontologies (FIBO, PROV-O, Dublin Core)
4. **Publishable** as Linked Data

### Practical Applications

| Use Case | Tool | Benefit |
|---|---|---|
| Consistency validation | Protégé + HermiT | Proves no contradictions exist in the governance graph |
| Impact analysis | SPARQL query | "If Rule X fails, which metrics and processes are affected?" |
| Knowledge graph import | Neo4j, AWS Neptune | Visual exploration of governance relationships |
| Regulatory publication | RDF endpoint | Third parties can reference ODGS definitions by URI |

### Relationship to Whitepaper

The whitepaper's Figure 1 (the 5-Plane Architecture) is now formally specified as an OWL ontology. Every relationship described in prose is now a machine-readable axiom.

---

## 5. Version History Since Whitepaper

| Version | Codename | Key Features |
|---|---|---|
| 3.0.0 | "The Constitution" | Original 5-Plane Architecture, CSL Formula, Hard Stop |
| 3.1.0 | "Sovereign Handshake" | Content-addressed integrity, SHA-256 verification |
| 3.2.0 | "Tri-Partite" | Cryptographic binding, Sovereign Harvester, new-function security fix |
| 3.3.0 | "Sovereign" | W3C OWL ontology, 5 harvester blueprints, GDPR/Basel III alignment, repo restructure |

---

## 6. Conclusion

The innovations in v3.1.0–v3.3.0 strengthen the whitepaper's argument rather than change it. The core thesis — that reactive data quality frameworks create a **Quality-Liability Fallacy** — is now backed by:

- **Cryptographic proof** (Sovereign Handshake) that definitions haven't been tampered with
- **Forensic evidence** (Tri-Partite Binding) of every AI decision
- **Legal traceability** (Sovereign Harvester) to authoritative sources
- **Formal specification** (OWL Ontology) that can be machine-validated

The ODGS Protocol is no longer just a conceptual framework — it is a **verified, standards-aligned, formally specified governance engine.**

---

### References

1. EU AI Act (2024/1689), Articles 10, 12, 99. *Official Journal of the European Union.*
2. ISO/IEC 42001:2023 — *Artificial Intelligence — Management System.*
3. FIBO — Financial Industry Business Ontology. *EDM Council / Object Management Group.*
4. GDPR (2016/679) — *General Data Protection Regulation.*
5. BCBS d424 (2017) — *Basel III: Finalising post-crisis reforms.*
6. Iyer, K. (2026). "The Quality-Liability Fallacy." *Metric Provenance Working Paper.*

---
[< Back to README](/README.md) | [Documentation Map →](../index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)
