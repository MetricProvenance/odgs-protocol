# ODGS Audit Ledger & Semantic Certificate (`S-Cert`) Guide

**Version:** 6.1.0  
**Source:** [`2_INFORMATIVE_REFERENCE/src/odgs/system/adapters/git_log_adapter.py`](../src/odgs/system/adapters/git_log_adapter.py) · [`2_INFORMATIVE_REFERENCE/src/odgs/dataspace/cap_exporter.py`](../src/odgs/dataspace/cap_exporter.py)

---

## The Verifiability Principle

The core design goal of the ODGS attestation layer is **Verifiable Compliance Without Raw Data Exposure**. Enterprise data pipelines and cross-organisational dataspaces frequently process confidential records, trade secrets, or Personally Identifiable Information (PII).

When an auditor, conformity assessment body, or dataspace participant asks whether a data payload satisfied an agreed policy or quality threshold at a specific point in time, raw records should not need to be disclosed. Instead, the ODGS Policy Enforcement Point outputs a deterministic **Semantic Certificate (`S-Cert`)** conforming to `1_NORMATIVE_SPECIFICATION/schemas/04-s-cert-schema.json`.

---

## 1. The Tri-Partite Cryptographic Binding

Every `S-Cert` binds three independent SHA-256 digests computed over RFC 8785 (JSON Canonicalization Scheme) representations:

1. **The Definition Hash (`definition_hash`):**
   - SHA-256 digest of the active JSON Rule, Metric, and (where applicable) W3C ODRL 2.2 Agreement definitions at the time of evaluation.
   - **Proves:** The exact normative constraints applied during evaluation.

2. **The Configuration Hash (`config_hash`):**
   - SHA-256 digest of the active contextual binding (`context_bindings.json` / `process_urn`) and engine version.
   - **Proves:** The business process context and runtime engine state.

3. **The Payload Hash (`payload_hash`):**
   - SHA-256 digest of the canonicalised physical data payload or batch summary evaluated during the process.
   - **Proves:** The exact snapshot of the evaluated data without exposing underlying PII or raw payload values.

---

## 2. Independent Verification

To independently verify the mechanical integrity of an evaluation, a verifier inspects:

1. The `S-Cert` JSON attestation (or its W3C Verifiable Credential / Eclipse CAP `cap:Declaration` projection).
2. The referenced JSON Rule and Context Binding definitions.
3. The JWS signature (`RFC 7515`) or SHA-256 digest chain.

```bash
# 1. Verify the Policy Definition Hash (RFC 8785 canonical JSON -> SHA-256)
# Must match `definition_hash` in the S-Cert.

# 2. Verify the Contextual Configuration Hash
# Must match `config_hash` in the S-Cert.

# 3. Verify the Dataspace Projections
odgs dataspace-demo --format cap-vc
odgs dataspace-demo --format prov-o
odgs dataspace-demo --format oscal
```

---

## 3. Standards Projections (Eclipse CAP v2.2.1, W3C PROV-O, NIST OSCAL)

Using `odgs.dataspace.cap_exporter`, any `S-Cert` can be deterministically projected into:
- **Eclipse Conformity Assessment Policy (`CAP v2.2.1`) & W3C VC 2.0:** `export_cap_declaration_vc()` wraps the `S-Cert` as `cred:Evidence` inside a `cap:Declaration`.
- **W3C PROV-O Lineage Graph:** `export_w3c_prov_o()` emits a JSON-LD provenance graph linking `prov:Activity`, `prov:Entity`, and `prov:Agent`.
- **NIST OSCAL Assessment Finding:** `export_nist_oscal_finding()` maps the tri-partite hashes to an OSCAL `finding` and `observation` structure.

---

[< Back to README.md](../../README.md) | [Documentation Map →](index.md)
