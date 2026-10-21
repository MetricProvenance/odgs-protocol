# Open Data Governance Standard (ODGS) — Technical Documentation (`v6.1.0`)

Welcome to the normative and reference implementation documentation for **ODGS `v6.1.0`**, the vendor-neutral specification and runtime engine for **in-pipeline semantic policy enforcement** and **cryptographic attestation (`S-Cert`)** across enterprise data pipelines and federated dataspaces.

![Two Complementary Governance Tracks](assets/fig1_two_tracks.svg)

---

## Documentation Navigation

| Section | Focus | Standards & Specifications Covered |
| :--- | :--- | :--- |
| **[Getting Started & Quickstart](getting-started.md)** | Installation (`pip install odgs`), CLI commands, Python/Node.js quickstart, and enterprise verification suites | `OdgsInterceptor`, `DataspaceRuntimePEP`, CLI (`odgs`) |
| **[5-Plane Architecture & Planes](architecture-and-planes.md)** | The 3-Layer / 5-Plane Architecture, `ISO/IEC 38505-1` *Evaluate–Direct–Monitor* model, and Trustworthy Data Transaction (`TDT`) sequence | `ISO/IEC 38505-1:2026`, `ISO/IEC 25012:2008`, `EN 18235`, `EAS 18425:2026` |
| **[Conformance Levels (`L1` & `L2`)](conformance-levels.md)** | Normative requirements for `Level 1 Core` and `Level 2 Attested` implementations and mapping to `EAS 18425` (`CL0–CL5`) | `RFC 2119`, `RFC 8785 (JCS)`, `EAS 18425:2026`, `ISO/IEC 17000` |
| **[Eclipse EDWG (`ODRL 2.2`, `CAP v2.2.1`, `DRP`)](eclipse-edwg.md)** | Compiling negotiated `W3C ODRL 2.2` agreements into runtime PEPs and projecting `S-Cert` receipts into `cap:Declaration` VCs | `W3C ODRL 2.2`, `Eclipse CAP v2.2.1`, `Eclipse DRP`, `W3C VC 2.0` |
| **[Gaia-X Phase 6 & DTA Verification](gaia-x-dta.md)** | Post-transfer obligation enforcement, `ovc:Constraint` verification, and upstream Data Transfer Agent (`DTA`) provenance hash checks | `Gaia-X Architecture 25.11` (§4.8.4.2), `Gaia-X Trust Framework` |
| **[IDSA Rulebook, W3C PROV-O & NIST OSCAL](idsa-prov-oscal.md)** | Decentralized observability (`correlation_id`), W3C PROV-O lineage export, and NIST OSCAL v1.1.2 assessment findings | `IDSA Rulebook 2026-3` (§121), `W3C PROV-O`, `NIST OSCAL v1.1.2` |
| **[JSON Schemas, OWL 2 & LinkML](schemas-and-linkml.md)** | Normative Draft-07 JSON Schemas (`01`–`04`), W3C OWL 2 ontology, and LinkML dataspace metamodel | `JSON Schema Draft-07`, `W3C OWL 2`, `LinkML`, `JSON-LD 1.1` |
| **[Python & Node.js API Reference](api-reference.md)** | Reference for `OdgsInterceptor`, `bind_odrl_policy`, `DataspaceRuntimePEP`, `verify_dta_provenance`, and conformity exporters | Python `3.10+`, Node.js `18+` |

---

## Core Architectural Principle

Pre-transfer dataspace protocols (**Eclipse DSP/DCP**, **W3C ODRL 2.2**, **Eclipse DRP**, and the **Gaia-X Data Transfer Agent**) govern *negotiation and authorization before data moves*.

**ODGS (`v6.1.0`)** governs **what happens at the moment data is processed inside the receiving or originating pipeline**:

1. **Declarative Policy Binding:** Binds `ISO/IEC 25012:2008` data quality rules and compiled `W3C ODRL 2.2` obligations to physical execution contexts (`context_bindings.json`) per `ISO/IEC 38505-1:2026`.
2. **Deterministic Runtime Enforcement:** Evaluates payloads in-memory and enforces `HARD_STOP` (`ProcessBlockedException` / `AdministrativeRecusalError`), `SOFT_STOP` (cryptographic `override_token` required), or `LOG_ONLY`.
3. **Zero-Knowledge Semantic Certificate (`S-Cert`):** Emits an RFC 8785 (JCS) canonicalized cryptographic receipt binding `payload_hash`, `definition_hash`, and `config_hash`—proving conformance without exposing raw data payloads.
