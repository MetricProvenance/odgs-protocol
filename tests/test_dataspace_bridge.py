"""Comprehensive unit and integration tests for odgs-dataspace-bridge."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from odgs.dataspace import (
    AdministrativeRecusalError,
    AuthoritativeSource,
    DataspaceRuntimePEP,
    ExecutableRule,
    ProcessBinding,
    SoftStopOverrideRequiredError,
    Verdict,
    bind_drp_delegation_evidence,
    bind_odrl_policy,
    compute_semantic_hash,
    export_cap_cred_evidence,
    export_cap_declaration_vc,
    export_nist_oscal_finding,
    export_w3c_prov_o,
    sign_s_cert_ed25519,
    verify_dta_post_transfer_obligation,
)
from odgs.dataspace.cli import main as cli_main

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "04-s-cert-schema.json"
SCERT_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_authoritative_source_from_verbatim() -> None:
    src = AuthoritativeSource.from_verbatim(
        source_urn="urn:odgs:def:eu_dora:art_17_1",
        legislative_source="Regulation (EU) 2022/2554 - Article 17(1)",
        verbatim_source_text="Financial entities shall define, establish and implement an ICT-related incident management process.",
    )
    assert len(src.semantic_hash) == 64
    assert src.semantic_hash == compute_semantic_hash(src.verbatim_source_text)


def test_odrl_duty_binding_and_phase6_enforcement_pass_and_hard_stop() -> None:
    odrl_agreement = {
        "@context": "http://www.w3.org/ns/odrl.jsonld",
        "@type": "Agreement",
        "uid": "urn:uuid:agreement-energy-grid-2026-091",
        "obligation": [
            {
                "uid": "urn:odrl:duty:k-anonymity-min-50",
                "action": "aggregate",
                "constraint": [
                    {
                        "leftOperand": "aggregation_household_count",
                        "operator": "gteq",
                        "rightOperand": {"@value": "50", "@type": "xsd:integer"},
                    }
                ],
            }
        ],
    }
    process_urn = "urn:odgs:process:energy-consumer:grid-load-forecasting"
    rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
    assert len(rules) == 1
    assert binding.correlation_id == "urn:uuid:agreement-energy-grid-2026-091"

    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding], system_id="energy-node-01")

    # 1. Conformant payload (n = 64 >= 50) -> PASS S-Cert
    s_cert_pass = pep.evaluate(
        process_urn=process_urn,
        payload={"aggregation_household_count": 64, "region": "NL-ZH"},
    )
    assert s_cert_pass.verdict == Verdict.PASS
    assert s_cert_pass.correlation_id == "urn:uuid:agreement-energy-grid-2026-091"
    jsonschema.validate(instance=s_cert_pass.to_canonical_dict(), schema=SCERT_SCHEMA)

    # 2. Non-conformant payload (n = 12 < 50) -> HARD_STOP (Administrative Recusal)
    with pytest.raises(AdministrativeRecusalError) as exc_info:
        pep.evaluate(
            process_urn=process_urn,
            payload={"aggregation_household_count": 12, "region": "NL-ZH"},
        )
    s_cert_fail = exc_info.value.s_cert
    assert s_cert_fail.verdict == Verdict.HARD_STOP
    assert s_cert_fail.payload_hash != s_cert_pass.payload_hash
    jsonschema.validate(instance=s_cert_fail.to_canonical_dict(), schema=SCERT_SCHEMA)


def test_odrl_prohibition_and_permission_binding() -> None:
    odrl_policy = {
        "uid": "urn:uuid:policy-ai-corpus-2026",
        "prohibition": [
            {
                "uid": "urn:odrl:prohib:no-pii",
                "constraint": [
                    {
                        "leftOperand": "contains_unmasked_pii",
                        "operator": "eq",
                        "rightOperand": True,
                    }
                ],
            }
        ],
        "permission": [
            {
                "uid": "urn:odrl:perm:eu-jurisdiction",
                "constraint": [
                    {
                        "leftOperand": "jurisdiction",
                        "operator": "eq",
                        "rightOperand": "EU",
                    }
                ],
            }
        ],
    }
    process_urn = "urn:odgs:process:ai-training:corpus-ingestion"
    rules, binding = bind_odrl_policy(odrl_policy, process_urn=process_urn)
    assert len(rules) == 2

    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
    s_cert = pep.evaluate(
        process_urn=process_urn,
        payload={"contains_unmasked_pii": False, "jurisdiction": "EU"},
    )
    assert s_cert.verdict == Verdict.PASS

    with pytest.raises(AdministrativeRecusalError):
        pep.evaluate(
            process_urn=process_urn,
            payload={"contains_unmasked_pii": True, "jurisdiction": "EU"},
        )


def test_eclipse_drp_delegation_evidence_binding_and_breach_halt() -> None:
    drp_token = {
        "delegationEvidence": {
            "policyIssuer": "EU.EORI.NLBATTERY001",
            "target": {"accessSubject": "EU.EORI.DEOEM002"},
            "policySets": [
                {
                    "target": {
                        "environment": {
                            "licenses": ["ISHARE.LICENSE.CIRCULAR.BATTERY.2026"]
                        }
                    },
                    "policies": [
                        {
                            "target": {
                                "resource": {
                                    "type": "BatteryCarbonFootprintDeclaration",
                                    "identifiers": ["*"],
                                    "attributes": ["*"],
                                },
                                "actions": ["Read", "Use"],
                            },
                            "rules": [{"effect": "Permit"}],
                        }
                    ],
                }
            ],
        }
    }
    process_urn = "urn:odgs:process:dpp:battery-cfp-validation"
    rules, binding = bind_drp_delegation_evidence(drp_token, process_urn=process_urn)
    assert binding.delegation_license_ref == "ISHARE.LICENSE.CIRCULAR.BATTERY.2026"

    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])

    # Valid license present -> PASS
    s_cert = pep.evaluate(
        process_urn=process_urn,
        payload={
            "active_licenses": ["ISHARE.LICENSE.CIRCULAR.BATTERY.2026"],
            "resource_permitted": True,
        },
    )
    assert s_cert.verdict == Verdict.PASS

    # Missing required DRP license -> HARD_STOP (DRP breach clause)
    with pytest.raises(AdministrativeRecusalError):
        pep.evaluate(
            process_urn=process_urn,
            payload={"active_licenses": [], "resource_permitted": True},
        )


def test_proportional_soft_stop_and_log_only() -> None:
    process_urn = "urn:odgs:process:finance:sla-latency-monitor"
    soft_rule = ExecutableRule(
        rule_id="SLA-LATENCY-SOFT-001",
        pack_id="ODGS-FINANCE-SLA",
        legislative_source="Internal Operational SLA Section 4.2",
        semantic_hash=compute_semantic_hash("pipeline_latency_ms <= 500"),
        verbatim_source_text="Pipeline latency should not exceed 500ms.",
        expression="pipeline_latency_ms <= 500",
        fields_evaluated=("pipeline_latency_ms",),
        verdict_on_fail=Verdict.SOFT_STOP,
        plain_english_description="Warn when latency exceeds 500ms",
        non_conformance_message="Latency exceeded 500ms threshold",
        bound_processes=(process_urn,),
    )
    binding = ProcessBinding(
        process_urn=process_urn, bound_rules=("SLA-LATENCY-SOFT-001",)
    )
    pep = DataspaceRuntimePEP(rules=[soft_rule], bindings=[binding])

    # Without override_token -> raises SoftStopOverrideRequiredError carrying S-Cert
    with pytest.raises(SoftStopOverrideRequiredError) as exc_info:
        pep.evaluate(process_urn=process_urn, payload={"pipeline_latency_ms": 720})
    assert exc_info.value.s_cert.verdict == Verdict.SOFT_STOP

    # With override_token -> returns SOFT_STOP S-Cert without raising
    s_cert_overridden = pep.evaluate(
        process_urn=process_urn,
        payload={"pipeline_latency_ms": 720},
        override_token="AUTH-OVERRIDE-2026-OPS",
    )
    assert s_cert_overridden.verdict == Verdict.SOFT_STOP


def test_gaia_x_dta_phase6_obligation_verification_with_ed25519_jws() -> None:
    priv_key = Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    odrl_agreement = {
        "uid": "urn:uuid:dta-transfer-2026-7781",
        "obligation": [
            {
                "uid": "urn:odrl:duty:anonymise-cohort",
                "constraint": [
                    {"leftOperand": "k_anonymity", "operator": "gteq", "rightOperand": 50}
                ],
            }
        ],
    }
    process_urn = "urn:odgs:process:ehds:federated-cohort-query"
    rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])

    s_cert_l1 = pep.evaluate(
        process_urn=process_urn,
        payload={"k_anonymity": 120, "hospital_node": "NL-LUMC"},
    )
    s_cert_l2 = sign_s_cert_ed25519(
        s_cert=s_cert_l1,
        private_key=priv_key,
        authority_id="urn:odgs:authority:ehds-nl-node",
        issuing_jwk_url="https://trust.ehds.example.eu/.well-known/jwks.json",
    )
    jsonschema.validate(instance=s_cert_l2.to_canonical_dict(), schema=SCERT_SCHEMA)

    dta_transfer_result = {
        "transfer_id": "urn:uuid:dta-transfer-2026-7781",
        "status": "TRANSFERRED",
    }

    # Valid Level 2 S-Cert -> verified == True
    res = verify_dta_post_transfer_obligation(
        s_cert=s_cert_l2,
        transfer_request_result=dta_transfer_result,
        expected_semantic_hash=rules[0].semantic_hash,
        public_key=pub_key,
        require_level_2_signature=True,
    )
    assert res.verified is True
    assert res.signature_verified is True

    # Mismatched correlation_id -> verified == False
    bad_corr = verify_dta_post_transfer_obligation(
        s_cert=s_cert_l2,
        transfer_request_result={"transfer_id": "urn:uuid:wrong-transfer-id"},
        expected_semantic_hash=rules[0].semantic_hash,
        public_key=pub_key,
    )
    assert bad_corr.verified is False


def test_exporters_eclipse_cap_w3c_prov_o_and_nist_oscal() -> None:
    odrl_agreement = {
        "uid": "urn:uuid:dpp-battery-2026-501",
        "obligation": [
            {
                "uid": "urn:odrl:duty:cfp-positive",
                "constraint": [
                    {
                        "leftOperand": "cfp_kg_co2e_per_kwh",
                        "operator": "gt",
                        "rightOperand": 0,
                    }
                ],
            }
        ],
    }
    process_urn = "urn:odgs:process:dpp:battery-passport-issuance"
    rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
    s_cert = pep.evaluate(
        process_urn=process_urn, payload={"cfp_kg_co2e_per_kwh": 61.4}
    )

    # 1. Eclipse CAP cred:Evidence & cap:Declaration VC
    ev = export_cap_cred_evidence(s_cert)
    assert ev["cred:id"] == f"urn:uuid:{s_cert.event_id}"
    assert ev["cred:digest"].startswith("sha256-")

    vc = export_cap_declaration_vc(
        s_cert,
        issuer_did="did:web:oem.battery-dataspace.eu",
        subject_did="did:web:oem.battery-dataspace.eu#pack-992",
    )
    assert "cap:Declaration" in vc["type"]
    assert vc["credentialSubject"]["cap:assessmentOutcome"] == "CONFORMANT"

    # 2. W3C PROV-O JSON-LD
    prov_doc = export_w3c_prov_o(s_cert)
    assert "@graph" in prov_doc
    assert len(prov_doc["@graph"]) == 4

    # 3. NIST OSCAL Finding
    oscal = export_nist_oscal_finding(s_cert)
    assert oscal["target"]["status"]["state"] == "satisfied"


def test_cli_demo_modes() -> None:
    for fmt in ("s-cert", "cap-vc", "prov-o", "oscal"):
        rc = cli_main(["demo", "--format", fmt])
        assert rc == 0


def test_iso_38505_and_25012_normative_schema_alignment() -> None:
    """Verify all 60 DQ dimensions and context bindings conform to ISO/IEC 25012 & ISO/IEC 38505-1."""
    dims_path = REPO_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative" / "standard_dq_dimensions.json"
    dim_schema_path = REPO_ROOT / "2_INFORMATIVE_REFERENCE" / "src" / "odgs" / "schemas" / "validation" / "dimension.schema.json"
    ctx_bindings_path = REPO_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "executive" / "context_bindings.json"
    ontology_graph_path = REPO_ROOT / "1_NORMATIVE_SPECIFICATION" / "schemas" / "legislative" / "ontology_graph.json"
    ontology_schema_path = REPO_ROOT / "2_INFORMATIVE_REFERENCE" / "src" / "odgs" / "schemas" / "validation" / "ontology.schema.json"
    owl_path = REPO_ROOT / "1_NORMATIVE_SPECIFICATION" / "ontology" / "ontology_graph.owl"

    dims = json.loads(dims_path.read_text(encoding="utf-8"))
    dim_schema = json.loads(dim_schema_path.read_text(encoding="utf-8"))
    assert len(dims) == 60
    jsonschema.validate(instance=dims, schema=dim_schema)

    for dim in dims:
        assert "damaId" not in dim
        assert bool(dim.get("iso25012Characteristic"))
        assert "ISO" in dim.get("isoReference", "") or "ETSI" in dim.get("isoReference", "")
        assert "38505" in dim.get("iso38505Role", "")

    ctx_bindings = json.loads(ctx_bindings_path.read_text(encoding="utf-8"))
    assert len(ctx_bindings.get("contexts", [])) >= 3

    ontology_graph = json.loads(ontology_graph_path.read_text(encoding="utf-8"))
    ontology_schema = json.loads(ontology_schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=ontology_graph, schema=ontology_schema)
    assert "38505" in ontology_graph["meta"].get("normative_alignment", "")

    owl_text = owl_path.read_text(encoding="utf-8")
    assert "https://w3id.org/odgs/ontology#ContextBinding" in owl_text or "ContextBinding" in owl_text
    assert "SemanticCertificate" in owl_text


