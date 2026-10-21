# Open Data Governance Standard (ODGS) — Project Governance & Neutrality Charter

**Status:** Open Specification & Reference Implementation  
**Version:** 6.1.0  
**License:** Apache-2.0  

---

## 1. Mission & Scope
The Open Data Governance Standard (ODGS) is an open, vendor-neutral specification and reference implementation bridging **Corporate Governance of Data (`ISO/IEC 38505-1:2026`)**, **Data Quality (`ISO/IEC 25012:2008`, `ISO 8000-8`)**, and **Dataspace Runtime Policy Enforcement (`W3C ODRL 2.2`, `Eclipse CAP v2.2.1`, `Eclipse DRP`, `Gaia-X DTA`)**.

ODGS addresses the **Phase 6 Operationalisation Gap**: ensuring that contractual, statutory, and data-quality constraints negotiated at the control plane are deterministically enforced inside the data-processing pipeline, producing verifiable, zero-knowledge cryptographic evidence (**Semantic Certificates / `S-Cert`**).

---

## 2. Standards & Working Group Alignment
This repository is structured to support open standardization and interoperability across:
- **CEN/CENELEC JTC 25 & NEN:** Data Management, Dataspaces, Cloud and Edge (Working Group 2 — Data Governance & Quality).
- **ISO/IEC JTC 1/SC 40 & SC 7:** Governance of IT and Data (`ISO/IEC 38505-1:2026`, `ISO/IEC TR 38505-2:2018`) and Data Quality (`ISO/IEC 25012:2008`).
- **Eclipse Dataspace Working Group (EDWG):** Complementing `Eclipse CAP v2.2.1` (`LinkML`), `Eclipse DRP`, and `Eclipse DSP/DCP`.
- **Gaia-X & IDSA:** Supporting Phase 6 post-transfer obligation enforcement (`Gaia-X Architecture Document 25.11` §4.8.4.2) and decentralized observability (`IDSA Rulebook 2026-3` §121).

---

## 3. Governance Principles
1. **Vendor Neutrality:** The normative schemas (`1_NORMATIVE_SPECIFICATION/`) and reference runtime (`2_INFORMATIVE_REFERENCE/`) do not depend on any proprietary cloud service, vendor platform, or closed registry.
2. **Open Licensing:** All source code, JSON Schemas, OWL 2 ontologies, and LinkML definitions in this repository are released under the **Apache License, Version 2.0**.
3. **Zero-Knowledge Verifiability:** Runtime attestations (`S-Cert`) bind SHA-256 digests (`payload_hash`, `definition_hash`, `config_hash`) over RFC 8785 canonical JSON without transmitting raw data outside the operating organisation's control boundary.
4. **Consensus-Driven Evolution:** Normative changes to schemas or ontologies require pull requests with passing Python (`pytest`), Node.js (`vitest`), and LinkML/JSON Schema conformance checks.

---

[< Back to README.md](README.md)
