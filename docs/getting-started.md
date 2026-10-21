# Getting Started & Quickstart (`v6.1.0`)

This guide walks through installing the Open Data Governance Standard (ODGS) reference runtime, executing CLI verification, embedding the in-pipeline Policy Enforcement Point (`OdgsInterceptor` and `DataspaceRuntimePEP`), and running the cross-sector enterprise verification suites.

---

## 1. Installation

### From PyPI

```bash
pip install odgs
```

### Local Development / Reference Verification

Clone the repository and install with development and verification dependencies:

```bash
git clone https://github.com/MetricProvenance/odgs-protocol.git
cd odgs-protocol
pip install -e ".[dev]"
```

---

## 2. Command-Line Interface (`odgs`)

The `odgs` CLI provides commands for schema validation, conformance verification, and end-to-end dataspace demonstration:

```bash
# Run the 5 normative dataspace scenarios and output an Eclipse CAP v2.2.1 Declaration VC
odgs dataspace-demo --format cap-vc

# Output a canonical Semantic Certificate (S-Cert: RFC 8785 JCS + SHA-256 / JWS)
odgs dataspace-demo --format s-cert

# Output a W3C PROV-O Lineage Graph
odgs dataspace-demo --format prov-o

# Output a NIST OSCAL v1.1.2 Assessment Results Finding
odgs dataspace-demo --format oscal
```

---

## 3. Python Quickstart: In-Pipeline Enforcement (`OdgsInterceptor`)

The core Python interceptor evaluates data payloads at runtime against declarative metric definitions, `ISO/IEC 25012:2008` data quality rules, and `ISO/IEC 38505-1:2026` contextual process bindings (`context_bindings.json`):

```python
from odgs.executive.interceptor import OdgsInterceptor, ProcessBlockedException

interceptor = OdgsInterceptor()

payload = {
    "gross_revenue": 150000.0,
    "net_revenue": 125000.0,
    "tax_rate": 0.19,
    "Data_Completeness_Ratio": 0.998,
}

try:
    result = interceptor.intercept(
        process_urn="urn:odgs:process:financial_close",
        data_map=payload,
    )
    print("Execution status:", result["execution_status"])
    print("S-Cert hash:", result["cryptographic_attestation"]["payload_hash"])
except ProcessBlockedException as exc:
    print("Execution halted by HARD_STOP rule:", exc)
```

---

## 4. Dataspace Phase 6 Quickstart (`DataspaceRuntimePEP`)

When a dataset crosses an organizational boundary under a negotiated **W3C ODRL 2.2** agreement (e.g., via an Eclipse DSP/DCP connector or Gaia-X Data Transfer Agent), `odrl_binder` compiles the agreement's obligations into executable ODGS rules and evaluates the payload at the receiving pipeline boundary:

```python
from odgs.dataspace.odrl_binder import bind_odrl_policy
from odgs.dataspace.runtime_pep import DataspaceRuntimePEP, AdministrativeRecusalError
from odgs.dataspace.cap_exporter import export_cap_declaration_vc

odrl_agreement = {
    "@context": "http://www.w3.org/ns/odrl.jsonld",
    "@type": "Agreement",
    "uid": "urn:uuid:agreement-energy-grid-2026-091",
    "obligation": [{
        "uid": "urn:odrl:duty:k-anonymity-min-50",
        "action": "aggregate",
        "constraint": [{
            "leftOperand": "aggregation_household_count",
            "operator": "gteq",
            "rightOperand": 50
        }]
    }]
}

process_urn = "urn:odgs:process:energy-consumer:grid-load-forecasting"
rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])

# Evaluate runtime payload and emit Semantic Certificate (S-Cert)
s_cert = pep.evaluate(
    process_urn=process_urn,
    payload={"aggregation_household_count": 64, "region": "NL-ZH"},
)

# Project S-Cert into an Eclipse CAP v2.2.1 Declaration Verifiable Credential
cap_vc = export_cap_declaration_vc(
    s_cert,
    issuer_did="did:web:consumer.energy-dataspace.eu",
    subject_did="did:web:consumer.energy-dataspace.eu#pipeline-1",
)
```

---

## 5. Cross-Language Node.js Runtime (`interceptor.js`)

ODGS maintains deterministic cross-language parity between Python and Node.js. Both runtimes produce identical RFC 8785 (JCS) canonical SHA-256 digests and identical enforcement decisions:

```bash
# Run the Node.js cross-language parity test suite
npm test
```

---

## 6. Running the Enterprise & Dataspace Verification Suites

The repository includes two self-contained verification scripts that execute real-world scenarios across automotive (`Catena-X` PCF), energy smart grids, clinical AI (`EU AI Act Article 10`), and sovereign inter-agency sharing:

```bash
# 1. Run the 5 normative dataspace protocol scenarios
python3 examples/run_all_dataspace_scenarios.py

# 2. Run the 4 cross-sector enterprise verification scenarios
python3 examples/verify_real_life_enterprise_use_cases.py

# 3. Run the full 75-test pytest conformance suite
pytest -v
```
