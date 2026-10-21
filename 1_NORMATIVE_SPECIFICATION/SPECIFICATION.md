# Open Data Governance Standard (ODGS) — Normative Architecture & Dataspace Profile (v6.1.0)

**Status:** Normative Protocol Specification (Open-Source Reference Profile)  
**Version:** 6.1.0  
**License:** Apache-2.0  

---

## 1. Scope & Boundary

The Open Data Governance Standard (ODGS) specifies a vendor-neutral, machine-executable protocol for **Runtime Semantic Policy Enforcement and Cryptographic Attestation** across intra-enterprise data pipelines and federated cross-organisational dataspaces.

Specifically, ODGS resolves the **Phase 6 Operationalisation Gap** between:
1. **Control-Plane Policy Negotiation** — W3C ODRL 2.2 agreements, Eclipse Dataspace Protocol (DSP) 2025-1 contract negotiation, and Eclipse Delegation & Revocation Protocol (DRP); and
2. **Data-Plane Runtime Execution** — deterministic evaluation of data quality, schema, and usage obligations at the moment a payload is ingested, transformed, or consumed, emitting a verifiable **Semantic Certificate (S-Cert)** (RFC 8785 JCS + RFC 7515 JWS).

### 1.1 Organisational Control Boundary
ODGS separates **Governance of Data** (`ISO/IEC 38505-1:2026` — Evaluate, Direct, Monitor) from **Operational Data Management**:
- **Governance Plane (Plane I) & Legislative Plane (Plane II):** Authoritative policy intent, metric definitions (`01-metrics-schema.json`), and `ISO/IEC 25012:2008` / `ISO 8000-8` quality characteristics (`standard_dq_dimensions.json`).
- **Judiciary Plane (Plane III):** Deterministic validation rules (`02-rules-schema.json`) and root-cause taxonomy (`root_cause_factors.json`).
- **Executive Plane (Plane IV):** Contextual process bindings (`context_bindings.json`, `03-ontology-schema.json`) and the Runtime Policy Enforcement Point (`OdgsInterceptor` / `DataspaceRuntimePEP`).
- **Physical & Forensic Audit Plane (Plane V):** Adapter execution and emission of cryptographic **Semantic Certificates (S-Cert)** (`04-s-cert-schema.json`).

---

## 2. Normative Standards Alignment

| Domain | Normative / Reference Standard | ODGS Mapping |
| :--- | :--- | :--- |
| **Governance of Data** | `ISO/IEC 38505-1:2026` & `ISO/IEC TR 38505-2:2018` | Evaluate–Direct–Monitor (EDM) separation and accountability metadata across Planes I–IV |
| **Data Quality Model** | `ISO/IEC 25012:2008`, `ISO 8000-8`, `ETSI EN 304 311` | All 60 dimensions in `standard_dq_dimensions.json` carry `iso25012Characteristic` (`Inherent`, `System-Dependent`, `Inherent_and_System_Dependent`) and `iso38505GovernanceFacet` |
| **Policy Expression** | `W3C ODRL 2.2` | `odgs.dataspace.odrl_binder` compiles `odrl:Agreement`, `odrl:Duty`, `odrl:Permission`, and `odrl:Prohibition` into Plane III/IV enforcement rules |
| **Conformity Assessment** | `Eclipse CAP v2.2.1` (`LinkML`) & `W3C VC 2.0` | `1_NORMATIVE_SPECIFICATION/ontology/odgs_dataspace.linkml.yaml` and `odgs.dataspace.cap_exporter` project S-Certs into `cap:Declaration` and `cred:Evidence` |
| **Data Provenance** | `Gaia-X Data Trust & Provenance (DTA)` & `W3C PROV-O` | `odgs.dataspace.dta_verifier` verifies upstream provenance hashes at Phase 6 ingestion and emits `prov:Activity` / `prov:Entity` graphs |
| **Compliance Assessment** | `NIST OSCAL` | `export_nist_oscal_finding()` maps S-Cert tri-partite hashes to OSCAL Assessment Results `finding` and `observation` records |
| **Cryptographic Attestation** | `IETF RFC 8785 (JCS)` & `RFC 7515 (JWS)` | Deterministic canonicalisation and Ed25519/ES256 signing of the Tri-Partite Binding (`payload_hash`, `definition_hash`, `config_hash`) |

---

## 3. Contextual Governance (Rejecting Universal Schema Fallacy)

In accordance with `ISO/IEC 38505-1:2026` and European data governance research, data semantics are **process- and context-dependent**: the same physical dataset is subject to distinct legal, contractual, and quality constraints depending on the business process stage (`process_urn`), jurisdiction, and active dataspace agreement (`agreement_uid`).

ODGS enforces contextual governance through `context_bindings.json` (`03-ontology-schema.json`):
- Rules are **never** hardcoded globally onto tables.
- Instead, each `ContextBinding` binds a `context_id` / `process_urn` to a specific set of `Rule` URNs, temporal validity windows (`effective_from`, `effective_to`), and dataspace agreement UIDs.

---

## 4. Enforcement Modes (`HARD_STOP`, `SOFT_STOP`, `LOG_ONLY`)

Every ODGS rule specifies a deterministic enforcement behavior:
1. **`HARD_STOP` (Administrative Recusal):** Immediately halts pipeline execution (`ProcessBlockedException` / `AdministrativeRecusalError`) when a constraint fails or when upstream provenance (`expected_upstream_hash`) does not match.
2. **`SOFT_STOP` (Controlled Exception):** Halts execution by default unless an authorised caller provides an explicit `override_token`, whose SHA-256 digest and rationale are recorded in the emitted `S-Cert`.
3. **`LOG_ONLY` (Observability Mode):** Evaluates the constraint and records the pass/fail result in the `S-Cert` without interrupting execution.

---

## 5. Semantic Certificate (`S-Cert`) Structure

Every runtime evaluation produces a canonical JSON attestation (`1_NORMATIVE_SPECIFICATION/schemas/04-s-cert-schema.json`) containing the **Tri-Partite Cryptographic Binding**:
- `payload_hash`: `SHA-256(RFC8785(Payload))` — proves the exact data evaluated without exposing raw records or PII.
- `definition_hash`: `SHA-256(RFC8785(Rules + Metrics + ODRL Agreement))` — proves the exact policy active at evaluation time.
- `config_hash`: `SHA-256(RFC8785(Context Binding + Engine Version))` — proves the execution context and runtime version.
