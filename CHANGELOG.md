# Changelog

All notable changes to the Open Data Governance Standard (ODGS) reference specification and runtime engine are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v6.1.0] - 2026-10-19

### Added — ISO/IEC 38505 & ISO/IEC 25012 Normative Grounding + Dataspace Runtime Enforcement (`odgs.dataspace`)
- **Normative ISO/IEC 38505-1:2026 & ISO/IEC 25012:2008 Schema Alignment:**
  - Migrated all 60 data quality dimensions in `1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_dq_dimensions.json` and `dimension.schema.json` to `ISO/IEC 25012:2008` (`iso25012Characteristic`: `Inherent`, `System-Dependent`, `Inherent_and_System_Dependent`), `ISO 8000-8`, `ETSI EN 304 311`, and `ISO/IEC 38505-1:2026` (`iso38505GovernanceFacet`: `Evaluate`, `Direct`, `Monitor`).
  - Added contextual governance bindings (`1_NORMATIVE_SPECIFICATION/schemas/executive/context_bindings.json` and `03-ontology-schema.json`) separating corporate governance of data (`ISO/IEC 38505-1:2026`) from operational data management.
  - Updated `1_NORMATIVE_SPECIFICATION/ontology/ontology_graph.owl` to v6.1.0 with `ContextBinding` and `SemanticCertificate` OWL 2 classes and object properties.
- **Dataspace Runtime Policy Enforcement & Certification Package (`2_INFORMATIVE_REFERENCE/src/odgs/dataspace/`):**
  - `odrl_binder.py`: Compiles **W3C ODRL 2.2** agreements (`odrl:Duty`, `odrl:Permission`, `odrl:Prohibition`), **Gaia-X ODRL-VC** constraints, and **Eclipse DRP** `delegationEvidence` tokens into deterministic ODGS enforcement rules and process bindings.
  - `runtime_pep.py`: Phase 6 in-pipeline Policy Enforcement Point supporting `HARD_STOP` (`AdministrativeRecusalError`), `SOFT_STOP` (with cryptographically logged `override_token`), and `LOG_ONLY`, emitting RFC 8785 JCS + RFC 7515 JWS **Semantic Certificates (`S-Cert`)**.
  - `cap_exporter.py`: Deterministic exporters projecting `S-Cert` attestations into **Eclipse CAP v2.2.1** (`cap:Declaration` & `cred:Evidence` W3C VC 2.0), **W3C PROV-O** lineage graphs, and **NIST OSCAL v1.1.2** assessment findings.
  - `dta_verifier.py`: Zero-knowledge verification of **Gaia-X Data Transfer Agent (DTA)** Phase 6 post-transfer obligations and upstream provenance hashes.
  - Added `1_NORMATIVE_SPECIFICATION/ontology/odgs_dataspace.linkml.yaml`, `1_NORMATIVE_SPECIFICATION/schemas/04-s-cert-schema.json`, and `1_NORMATIVE_SPECIFICATION/schemas/odgs-dataspace.context.jsonld`.
- **CLI & Documentation:**
  - Added `odgs dataspace-demo` command (`--format s-cert|cap-vc|prov-o|oscal`) and `odgs-dataspace` entrypoint.
  - Added `1_NORMATIVE_SPECIFICATION/SPECIFICATION.md` and updated `1_NORMATIVE_SPECIFICATION/conformance_rules.md` with explicit disambiguation between ODGS Implementation Conformance Levels (`Level 1 Core` / `Level 2 Attested`), `ISO/IEC 17000` (Eclipse CAP), and `EAS 18425:2026`.

## [v6.0.0] - 2026-04-04

### Added — Core Runtime Enforcement Enhancements
- **`SOFT_STOP` Override-able Severity:** Enables controlled exception handling where a failed rule halts execution unless an authorised `override_token` is supplied and logged in the attestation.
- **Batch Evaluation (`intercept_batch`):** Evaluates multiple data payloads in a single invocation with `fail_fast` support.
- **Rule Dependency Chains (DAG):** Topological sort (`depends_on`) via Kahn's algorithm with cascading `DEPENDENCY_FAILED` status.
- **Webhook Event Dispatch:** Emits structured runtime events (`BLOCKED`, `SOFT_STOP_OVERRIDE`, `SOFT_STOP_BLOCKED`).
- **Conformance Self-Check (`odgs conformance`):** Verifies `L1` (Level 1 Core) and `L2` (Level 2 Attested) project structure and cross-reference integrity.
- **Rule Versioning & Temporal Bounds:** Tracks `version` (semver) and `effective_from` / `effective_to` validity windows in every emitted attestation.
