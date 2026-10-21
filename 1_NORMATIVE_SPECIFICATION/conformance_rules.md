# ODGS Conformance Rules (Normative — v6.1.0)

## 1. Scope & Terminology Disambiguation
This document defines the normative requirements for achieving **ODGS Implementation Conformance** regarding runtime semantic policy verification, contextual bindings, and cryptographic attestation.

> **Terminology Disambiguation:**
> **ODGS Implementation Conformance Levels (`Level 1 Core` and `Level 2 Attested`)** apply strictly to software implementations of the ODGS specification. They are distinct from:
> - **`ISO/IEC 17000` Conformity Assessment & Eclipse CAP (`cap:ConformityAssessmentScheme`):** Formal conformity assessment vocabularies into which ODGS projects runtime evidence (`cred:Evidence`).
> - **Dataspace Interoperability Profiles:** Capability profiles across federated dataspace ecosystems.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

---

## 2. Core Conformance Requirements

### 2.1 Semantic & Contextual Decoupling (`ISO/IEC 38505-1:2026`)
Any system claiming ODGS conformance SHALL strictly decouple its policy definitions (Planes I–III) from its contextual process bindings (Plane IV) and physical execution (Plane V). Hard-coding legal, contractual, or data quality definitions inside application execution logic constitutes non-conformance.

### 2.2 Ontology & Data Quality Baseline (`ISO/IEC 25012:2008`)
The system MUST validate governance artifacts against the normative JSON Schemas (`1_NORMATIVE_SPECIFICATION/schemas/`) and the W3C OWL 2 / LinkML ontologies (`ontology_graph.owl`, `odgs_dataspace.linkml.yaml`), where data quality dimensions are grounded in `ISO/IEC 25012:2008` and `ISO 8000-8`.

### 2.3 Deterministic Enforcement (`HARD_STOP`, `SOFT_STOP`, `LOG_ONLY`)
1. When a rule with severity `HARD_STOP` fails evaluation, the ODGS Policy Enforcement Point SHALL halt execution (`ProcessBlockedException` / `AdministrativeRecusalError`) and MUST NOT probabilistically impute or bypass the failed constraint.
2. When a rule with severity `SOFT_STOP` fails evaluation, the engine SHALL halt execution unless a valid `override_token` is supplied, and MUST record the SHA-256 digest of the override token in the resulting attestation.

### 2.4 Cryptographic Attestation (`S-Cert` — Zero-Knowledge Auditing)
Upon completing an evaluation (whether `APPROVED`, `SOFT_STOP_OVERRIDDEN`, or `BLOCKED_HARD_STOP`), a Level 2 conformant implementation MUST emit a canonical **Semantic Certificate (`S-Cert`)** binding `payload_hash`, `definition_hash`, and `config_hash` via RFC 8785 (JCS) without transmitting raw data payloads to external third-party servers.

---

## 3. ODGS Implementation Conformance Levels

| Level | Designation | Normative Requirements | Verification Command |
| :--- | :--- | :--- | :--- |
| **L1** | **Level 1 Core** | Planes II–IV JSON artifacts exist and validate against Draft-07 JSON Schemas (`01-metrics-schema.json`, `02-rules-schema.json`, `03-ontology-schema.json`). | `odgs conformance --level L1` |
| **L2** | **Level 2 Attested** | Satisfies L1 plus full cross-reference integrity across `context_bindings.json`, deterministic RFC 8785 JCS hashing, and `04-s-cert-schema.json` attestation emission. | `odgs conformance --level L2` |
