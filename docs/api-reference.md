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

## 2. W3C ODRL 2.2 Policy Binder (`odgs.dataspace.odrl_binder`)

### `bind_odrl_policy`

Compiles a negotiated **W3C ODRL 2.2** policy (`Agreement`, `Offer`, or `Set`) and optional **Eclipse DRP** `delegationEvidence` into deterministic ODGS validation rules and a Plane IV contextual process binding.

```python
from odgs.dataspace.odrl_binder import bind_odrl_policy, OdrlBindingError

rules, binding = bind_odrl_policy(
    odrl_policy=odrl_agreement,
    process_urn="urn:odgs:process:consumer:pipeline",
    delegation_evidence=drp_delegation,
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

## 5. Conformity & Lineage Exporters (`odgs.dataspace.cap_exporter`)

Projects canonical `S-Cert` receipts into external conformity assessment, lineage, and audit standards:

```python
from odgs.dataspace.cap_exporter import (
    export_cap_declaration_vc,
    export_gaiax_compliance_evidence,
    export_w3c_prov_o,
    export_nist_oscal_finding,
)
```

| Function | Target Standard | Output Artifact |
| :--- | :--- | :--- |
| `export_cap_declaration_vc(s_cert, issuer_did, subject_did)` | **Eclipse CAP v2.2.1** & **W3C VC 2.0** | `VerifiableCredential` containing `cap:Declaration` and `cred:Evidence` |
| `export_gaiax_compliance_evidence(s_cert, dta_transfer_id)` | **Gaia-X Architecture 25.11** (`ovc:Constraint`) | Gaia-X Compliance Evidence Envelope |
| `export_w3c_prov_o(s_cert)` | **W3C PROV-O** | JSON-LD Provenance Graph (`prov:Activity`, `prov:Entity`, `prov:Agent`) |
| `export_nist_oscal_finding(s_cert)` | **NIST OSCAL v1.1.2** | OSCAL Assessment Results `finding` and `observation` structure |

---

## 6. Cryptographic Canonicalization (`odgs.core.crypto`)

```python
from odgs.core.crypto import hash_Object_JCS

digest = hash_Object_JCS({"b": 2, "a": 1})
# Returns deterministic RFC 8785 (JCS) SHA-256 hex digest identical across Python and Node.js
```
