# IDSA Rulebook, W3C PROV-O & NIST OSCAL Exports

## 1. IDSA Rulebook (`2026-3`) Decentralized Observability (§121)

The **IDSA Rulebook (`2026-3`, §121)** specifies that observability in a dataspace is decentralized: each participant logs its own transaction events locally and correlates them across participants upon authorised request.

`odgs-dataspace-bridge` implements this pattern via:
- **Zero-knowledge data minimisation:** Every `S-Cert` records only `payload_hash` (SHA-256), never raw payload contents.
- **Cross-participant correlation:** The `correlation_id` field links the provider's transfer log and the consumer's Phase 6 `S-Cert` receipt without centralising data.

## 2. W3C PROV-O Lineage Export (`export_w3c_prov_o`)

Exports any `S-Cert` as a **W3C PROV-O** JSON-LD `@graph` mapping:
- Evaluated payload (`payload_hash`) → `prov:Entity`
- Runtime evaluation (`event_id`, `process_urn`) → `prov:Activity`
- Evaluating runtime (`system_id`) → `prov:SoftwareAgent`
- Governing constraint (`rule_id`, `semantic_hash`) → `prov:Plan`
- Verdict (`PASS` / `HARD_STOP`) → `prov:wasGeneratedBy` / `prov:wasInvalidatedBy`

## 3. NIST OSCAL v1.1.2 Assessment Finding Export (`export_nist_oscal_finding`)

Exports any `S-Cert` into a **NIST OSCAL** Assessment Results `finding` + `observation` object with `status.state = "satisfied"` (`PASS`) or `"not-satisfied"` (`HARD_STOP` / `SOFT_STOP`).
