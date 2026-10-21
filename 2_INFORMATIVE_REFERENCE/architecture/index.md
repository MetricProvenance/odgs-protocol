# ODGS Architecture & Reference Documentation (v6.1.0)

> Informative reference documentation for the Open Data Governance Standard (ODGS).

---

## Quick Navigation

| Role / Focus | Start Here | Then Read |
|---|---|---|
| **Standards & Dataspace Architects** | [Normative Specification](../../1_NORMATIVE_SPECIFICATION/SPECIFICATION.md) | [Technical Annex](technical_annex.md) |
| **Governance & Compliance Leads** | [Technical Annex](technical_annex.md) | [Architecture Specification](architecture.md) |
| **Conformity Assessment & Auditors** | [Audit Ledger & S-Cert Guide](audit_ledger_guide.md) | [Conformance Rules](../../1_NORMATIVE_SPECIFICATION/conformance_rules.md) |
| **Semantic & Ontology Engineers** | [Ontology Guide](ontology_guide.md) | [LinkML Dataspace Profile](../../1_NORMATIVE_SPECIFICATION/ontology/odgs_dataspace.linkml.yaml) |
| **Data & Platform Engineers** | [Adapter Interface Guide](adapter_guide.md) | [Case Studies](case_studies.md) |

---

## Core Documents

| Document | Description |
|---|---|
| [Normative Specification (`SPECIFICATION.md`)](../../1_NORMATIVE_SPECIFICATION/SPECIFICATION.md) | Planes I–V boundary, `ISO/IEC 38505-1:2026` & `ISO/IEC 25012:2008` alignment, and Phase 6 Dataspace profile |
| [Conformance Rules (`conformance_rules.md`)](../../1_NORMATIVE_SPECIFICATION/conformance_rules.md) | ODGS Implementation Conformance Levels (`Level 1 Core` / `Level 2 Attested`) |
| [Architecture Specification (`architecture.md`)](architecture.md) | 5-Plane reference architecture and runtime sequence |
| [Technical Annex (`technical_annex.md`)](technical_annex.md) | Runtime policy enforcement, DAG dependencies, and `SOFT_STOP` override mechanics |
| [Ontology Guide (`ontology_guide.md`)](ontology_guide.md) | W3C OWL 2 (`ontology_graph.owl`) and LinkML (`odgs_dataspace.linkml.yaml`) semantic bridge |
| [Adapter Interface Guide (`adapter_guide.md`)](adapter_guide.md) | Implementing `OdgsAdapter` for databases, streams, and dataspace connectors |
| [Audit Ledger & S-Cert Guide (`audit_ledger_guide.md`)](audit_ledger_guide.md) | Tri-Partite Cryptographic Binding (`payload_hash`, `definition_hash`, `config_hash`) |
| [Architectural Case Studies (`case_studies.md`)](case_studies.md) | Contextual policy enforcement scenarios across regulated domains |

---

[< Back to README.md](../../README.md)
