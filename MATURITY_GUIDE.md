# ODGS Governance Maturity: Why It Matters and How It Works

> **Author:** Metric Provenance · **Version:** 1.0 · **Standard:** ODGS v6  
> **Audience:** CDOs, Heads of Data, Governance Practitioners, Technology Leaders

---

## The Problem This Solves

Most governance programmes fail for the same reason: they measure *activity*, not *reality*.

Organisations install tools, write policies, create stewardship councils, and build dashboards — then declare victory. Six months later, nobody trusts the data, nobody reads the policies, and the stewardship council hasn't met since Q2. The dashboards, of course, still show green.

This is **organisational theatre**. And it's expensive.

ODGS Maturity Assessment exists because we needed a way to measure whether governance is *actually working* — not whether the governance team is *busy*.

---

## What ODGS Maturity Actually Measures

The maturity engine reads your **actual workspace configuration** — the files, the bindings, the rules, the connections — and scores what it finds. Not what you *plan* to do. Not what your slide deck says. What exists on disk, right now.

### The 8 Pillars

The scoring framework spans 8 pillars, 6 adapted from DAMA DMBOK knowledge areas and 2 native to ODGS:

| Pillar | Weight | What It Measures |
|--------|--------|-----------------|
| **Governance Foundations** | 20% | Are rules bound to business processes? Do you have context bindings — or just rules floating in space? |
| **Quality Enforcement** | 18% | Do your rules have executable logic? Are there owners — real people accountable — or just "TBD" placeholders? |
| **Operational Readiness** | 15% | Is the interceptor installed? Is enforcement set to `strict` (blocking) or `permissive` (logging, i.e. doing nothing useful)? |
| **Metadata Integrity** | 12% | Is your ontology populated with real terms? Do metrics have calculation logic — or are they aspirational names? |
| **Usage & Analytics** | 8% | Are rules linked to measurable DQ dimensions? Can you actually track improvement? |
| **Organisational Adoption** | 12% | Have you customised rules for your industry? Are contexts bound to enforcement — or decorative? |
| **Certification & Trust** | 8% | Are regulation packs installed? Are they cryptographically signed? Is the sovereign audit trail configured? |
| **Bridge Connectivity** | 7% | Are source systems connected? Is there diversity in connection types (not just one pipe)? |

### The 5 Maturity Levels

| Level | Range | Label | What It Means |
|-------|-------|-------|--------------|
| 1 | 0-19% | **Initial** | Governance exists in name only. |
| 2 | 20-39% | **Developing** | Some artifacts present. Basic structure, no customisation. |
| 3 | 40-59% | **Defined** | Rules bound to processes. Enforcement configured. Not yet measured. |
| 4 | 60-79% | **Measured** | Active monitoring. DQ dimensions linked. Owners assigned. |
| 5 | 80-100% | **Optimised** | Continuous improvement. All pillars at production grade. |

---

## How the Three-Branch Model Maps to Maturity

ODGS structures governance as three independent branches — borrowing from constitutional design:

### Legislative Branch (What the organisation defines as truth)
Ontology terms, metrics definitions, DQ dimensions. Scored by:
- `META-01`: Ontology Graph Populated
- `META-02`: Metrics Catalogue Depth  
- `QE-03`: DQ Dimensions Coverage

### Judiciary Branch (How truth is enforced)
Data quality rules, logic expressions, root cause factors. Scored by:
- `QE-01`: Data Rules With Logic
- `QE-02`: Rule Owner Assignment
- `OPS-03`: Root Cause Factors Loaded

### Executive Branch (Where truth meets reality)
Context bindings, physical data maps, business process maps. Scored by:
- `GOV-01`: Context Bindings Populated
- `GOV-02`: Business Process Maps Defined
- `META-03`: Physical Data Map Coverage
- `OPS-01`: Interceptor Present
- `OPS-02`: Enforcement Mode Set

The maturity engine scores across all three branches because governance fails when any branch is missing. Rules without context bindings are decorative. Context bindings without rules are empty. Both without an interceptor are fiction.

---

## Conformance Rules and Maturity Scoring

The v6 normative specification defines four conformance requirements. Each maps to maturity rules:

| Conformance Requirement | Maturity Rule(s) | Assessment |
|------------------------|------------------|------------|
| §3.1 Semantic Decoupling | OPS-01, OPS-02 | Interceptor present + enforcement mode |
| §3.2 Ontology Baseline | META-01 | Ontology graph populated with terms |
| §3.3 Administrative Recusal (Hard Stop) | OPS-02 | `strict` mode = full score; `permissive` = 50% |
| §3.4 Forensic Sovereignty (Art. 12) | CERT-01, CERT-02, CERT-03 | Pack signatures + sovereign audit trail |

---

## Why a Fresh Install Scores ~30-35%

This is **by design**. The package ships with standard rules, metrics, and definitions (Legislative + Judiciary branches), but the Executive branch — context bindings, source system maps, enforcement configuration — is necessarily empty. Nobody can pre-configure your business processes.

The ~30-35% score is the honest answer: **the protocol works, but it hasn't been configured for your organisation yet.**

---

## Enterprise Framework Alignment (GOV-04)

As of v6.0.3, the normative schemas include a `framework_tags` dictionary — an extensible structure for binding governance artefacts to recognised enterprise frameworks such as APQC Process Classification, DAMA DMBOK Knowledge Areas, BIAN Service Landscape, and CDMC Principles.

The maturity engine scores whether these tags are populated (GOV-04). A score of 0% on this rule indicates that the schema is present but no framework mappings have been configured.

Framework alignment is increasingly relevant for organisations reporting under **DORA Article 11** (ICT risk management frameworks) and **EU AI Act Article 10** (data governance requirements for high-risk AI). Mapping governance artefacts to an established framework provides auditors with a recognisable reference point and accelerates regulatory review.

Certified Regulatory Law Packs and enterprise framework mappings are maintained within the Metric Provenance Sovereign S-Cert Registry.

---

## Getting Started

```bash
pip install odgs-maturity

# Assess your workspace
odgs-maturity score --workspace /path/to/odgs-workspace

# JSON output for pipelines
odgs-maturity score --json

# Generate improvement charter
odgs-maturity charter --type lifecycle
```

---

*For the full technical specification, see the [odgs-maturity package on PyPI](https://pypi.org/project/odgs-maturity/). For implementation details, see the [odgs-maturity repository on GitHub](https://github.com/MetricProvenance/odgs-maturity).*
