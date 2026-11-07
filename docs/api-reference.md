# Python & Node.js API Reference (`v6.1.0`)

This page provides a reference for the primary modules in the ODGS `v6.1.0` Informative Reference Implementation (`2_INFORMATIVE_REFERENCE/src/odgs/`).

---

## 1. Core Executive Interceptor (`odgs.executive.interceptor`)

### `OdgsInterceptor`

The in-pipeline Policy Enforcement Point (`PEP`) for enterprise data pipelines.

```python
from odgs.executive.interceptor import (
    OdgsInterceptor,
    ProcessBlockedException,
    MissingOverrideException,
    SchemaValidationError,
    SecurityException,
)
```

#### Key Methods

- `OdgsInterceptor(project_root_path: Optional[str] = None)`
  Initializes the interceptor and loads Planes II–IV definitions (`metrics`, `rules`, `context_bindings`, `physical_data_map`).
- `intercept(process_urn: str, data_map: Dict[str, Any], override_token: Optional[str] = None, required_edition: Optional[str] = None) -> Dict[str, Any]`
  Evaluates all rules bound to `process_urn` against `data_map`, enforces `HARD_STOP` / `SOFT_STOP` / `LOG_ONLY` semantics, and emits a signed/hashed `cryptographic_attestation` (`S-Cert`).

---

## 2. Eclipse DSP & W3C ODRL 2.2 Policy Binder (`odgs.dataspace.odrl_binder`)

### `bind_dsp_contract_agreement` & `bind_odrl_policy`

Compiles an **Eclipse Dataspace Protocol (`DSP v2025-1` / `ISO/IEC DIS 26450`)** `dspace:ContractAgreementMessage` (and optional `dspace:TransferStartMessage` / `dspace:TransferCompletionMessage`), a **W3C ODRL 2.2** policy (`Agreement`, `Offer`, or `Set`), or **Eclipse DRP** `delegationEvidence` into deterministic ODGS validation rules and a Plane IV contextual process binding.

```python
from odgs.dataspace.odrl_binder import (
    bind_dsp_contract_agreement,
    bind_odrl_policy,
    bind_drp_delegation_evidence,
)

# 1. Bind directly from an Eclipse DSP ContractAgreementMessage + TransferStartMessage
rules, binding = bind_dsp_contract_agreement(
    dsp_agreement_message=dsp_contract_agreement_msg,
    process_urn="urn:odgs:process:consumer:pipeline",
    transfer_message=dsp_transfer_start_msg,
)

# 2. Or bind from a standalone W3C ODRL 2.2 policy
rules, binding = bind_odrl_policy(
    odrl_policy=odrl_agreement,
    process_urn="urn:odgs:process:consumer:pipeline",
)
```

#### Supported ODRL Operators

| ODRL 2.2 Operator | Compiled Python / AST Operator |
| :--- | :--- |
| `eq` | `==` |
| `neq` | `!=` |
| `gt` | `>` |
| `gteq` | `>=` |
| `lt` | `<` |
| `lteq` | `<=` |
| `isPartOf` / `isA` | Membership / set inclusion check |

---

## 3. Phase 6 Dataspace Runtime PEP (`odgs.dataspace.runtime_pep`)

### `DataspaceRuntimePEP`

Evaluates post-transfer dataspace payloads at the consumer or provider pipeline boundary and emits canonical `S-Cert` receipts (`04-s-cert-schema.json`).

```python
from odgs.dataspace.runtime_pep import DataspaceRuntimePEP, AdministrativeRecusalError

pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
s_cert = pep.evaluate(
    process_urn="urn:odgs:process:consumer:pipeline",
    payload={"aggregation_household_count": 64},
    correlation_id="urn:uuid:corr-99102",
    override_token=None,
)
```

---

## 4. Gaia-X DTA Provenance Verifier (`odgs.dataspace.dta_verifier`)

### `verify_dta_provenance` & `compute_jcs_sha256`

Verifies that the payload arriving at the Phase 6 runtime boundary matches the upstream **Gaia-X Data Transfer Agent (DTA)** transfer provenance digest (`RFC 8785 JCS` + `SHA-256`).

```python
from odgs.dataspace.dta_verifier import (
    verify_dta_provenance,
    compute_jcs_sha256,
    DtaProvenanceMismatchError,
)

expected_hash = compute_jcs_sha256(payload)
verify_dta_provenance(payload=payload, expected_provenance_hash=expected_hash)
```

---

## 5. Eclipse Data Plane Signaling, DCP, CAP v2.2.1, Lineage & Audit (`odgs.dataspace.signaling` & `cap_exporter`)

Integrates consumer-side **Data Plane Signaling**, **DSP suspension/termination messages**, **Eclipse DCP (`ISO/IEC DIS 26451`)** DID-signed credentials, **Eclipse CAP v2.2.1**, **W3C PROV-O**, and **NIST OSCAL v1.1.2**:

```python
from odgs.dataspace import (
    DataPlaneSignalingBridge,
    build_agreement_retrieval_path,
    build_dsp_transfer_suspension_message,
    build_dsp_transfer_termination_message,
    inspect_odrl_constraint_observability,
    export_dcp_presentation_response,
    extract_dcp_presentation_claims,
    handle_dcp_presentation_query,
    export_cap_declaration_vc,
    verify_cap_declaration_vc,
    export_cap_cred_evidence,
    export_w3c_prov_o,
    export_nist_oscal_finding,
)
```

| Function / Class | Target Standard | Output / Behavior |
| :--- | :--- | :--- |
| `DataPlaneSignalingBridge` | **Data Plane Signaling** & **Eclipse DSP** | Handles `DataFlowPrepareMessage` / `DataFlowStartMessage`, fetches `GET /transfers/:dataFlowId/agreement`, evaluates payloads, and emits DSP suspension/termination messages on violation |
| `inspect_odrl_constraint_observability(odrl_policy)` | **W3C ODRL 2.2** & **Eclipse DSP** | Classifies payload-observable checks vs. unobservable behavioral usage constraints (`purpose`, `elapsedTime`, `distribute`) under `CONSUMER_FIRST_PARTY_AUDIT_RECORD` |
| `handle_dcp_presentation_query(query_message, stored_credentials, holder_did)` | **Eclipse DCP v1.0 (`ISO/IEC DIS 26451`)** | Serves DID-signed `VerifiablePresentation` (`PresentationResponseMessage`) from consumer credentials in response to `PresentationQueryMessage` |
| `export_cap_declaration_vc(s_cert, issuer_did, subject_did, private_key=...)` | **Eclipse CAP v2.2.1** & **W3C VC 2.0** | Consumer-signed first-party `cap:Declaration` VC with `JsonWebSignature2020` DID proof and `cred:Evidence` |
| `verify_cap_declaration_vc(vc, public_key, expected_issuer_did)` | **Eclipse DCP / CAP v2.2.1** | Verifies consumer DID Ed25519/EdDSA proof and canonical claims on a `cap:Declaration` VC |
| `export_w3c_prov_o(s_cert)` | **W3C PROV-O** | JSON-LD Provenance Graph (`prov:Activity`, `prov:Entity`, `prov:Agent`) |
| `export_nist_oscal_finding(s_cert)` | **NIST OSCAL v1.1.2** | OSCAL Assessment Results `finding` and `observation` structure |

---

## 6. Cryptographic Canonicalization (`odgs.core.crypto`)

```python
from odgs.core.crypto import hash_Object_JCS

digest = hash_Object_JCS({"b": 2, "a": 1})
# Returns deterministic RFC 8785 (JCS) SHA-256 hex digest identical across Python and Node.js
```
