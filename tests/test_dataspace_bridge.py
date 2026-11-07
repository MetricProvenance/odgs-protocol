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
    bind_dsp_contract_agreement,
    bind_odrl_policy,
    compute_semantic_hash,
    export_cap_cred_evidence,
    export_cap_declaration_vc,
    export_dcp_presentation_response,
    export_nist_oscal_finding,
    export_w3c_prov_o,
    extract_dcp_presentation_claims,
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
    for fmt in ("s-cert", "cap-vc", "dcp-vp", "prov-o", "oscal"):
        rc = cli_main(["demo", "--format", fmt])
        assert rc == 0


def test_eclipse_dsp_contract_agreement_and_dcp_presentation_roundtrip() -> None:
    """Verify Eclipse DSP (ISO/IEC DIS 26450) ContractAgreementMessage + TransferStartMessage binding
    and Eclipse DCP (ISO/IEC DIS 26451) PresentationResponseMessage roundtrip."""
    dsp_contract_agreement_msg = {
        "@context": "https://w3id.org/dspace/2025/1/context.jsonld",
        "@type": "dspace:ContractAgreementMessage",
        "dspace:providerPid": "urn:uuid:dsp-provider-pid-101",
        "dspace:consumerPid": "urn:uuid:dsp-consumer-pid-202",
        "dspace:agreement": {
            "@id": "urn:uuid:dsp-agreement-energy-2026-901",
            "@type": "odrl:Agreement",
            "odrl:target": "urn:uuid:dataset-smart-grid-2026",
            "dspace:timestamp": "2026-11-05T12:00:00Z",
            "dspace:consumerId": "did:web:consumer.energy-dataspace.eu",
            "dspace:providerId": "did:web:provider.energy-dataspace.eu",
            "odrl:obligation": [
                {
                    "odrl:uid": "urn:odrl:duty:k-anonymity-min-50",
                    "odrl:action": "odrl:aggregate",
                    "odrl:constraint": [
                        {
                            "odrl:leftOperand": "aggregation_household_count",
                            "odrl:operator": "odrl:gteq",
                            "odrl:rightOperand": 50,
                        }
                    ],
                }
            ],
        },
    }
    dsp_transfer_start_msg = {
        "@context": "https://w3id.org/dspace/2025/1/context.jsonld",
        "@type": "dspace:TransferStartMessage",
        "dspace:providerPid": "urn:uuid:transfer-provider-501",
        "dspace:consumerPid": "urn:uuid:transfer-consumer-602",
        "dspace:agreementId": "urn:uuid:dsp-agreement-energy-2026-901",
    }

    process_urn = "urn:odgs:process:dsp-consumer:grid-load-ingestion"
    rules, binding = bind_dsp_contract_agreement(
        dsp_agreement_message=dsp_contract_agreement_msg,
        process_urn=process_urn,
        transfer_message=dsp_transfer_start_msg,
    )
    assert len(rules) == 1
    assert (
        binding.correlation_id
        == "urn:uuid:dsp-agreement-energy-2026-901#transfer:urn:uuid:transfer-consumer-602"
    )

    # Verify mismatched DSP transfer agreementId is rejected
    with pytest.raises(ValueError, match="agreementId mismatch"):
        bind_dsp_contract_agreement(
            dsp_agreement_message=dsp_contract_agreement_msg,
            process_urn=process_urn,
            transfer_message={"dspace:agreementId": "urn:uuid:wrong-agreement"},
        )

    # Evaluate payload at Data-Plane PEP and sign Level 2 S-Cert
    priv_key = Ed25519PrivateKey.generate()
    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
    s_cert_l1 = pep.evaluate(
        process_urn=process_urn,
        payload={"aggregation_household_count": 75, "region": "NL-ZH"},
    )
    s_cert_l2 = sign_s_cert_ed25519(
        s_cert=s_cert_l1,
        private_key=priv_key,
        authority_id="did:web:consumer.energy-dataspace.eu",
        issuing_jwk_url="https://consumer.energy-dataspace.eu/.well-known/jwks.json",
    )

    # Export as Eclipse DCP v1.0 PresentationResponseMessage and verify claims roundtrip
    dcp_msg = export_dcp_presentation_response(
        s_cert=s_cert_l2,
        holder_did="did:web:consumer.energy-dataspace.eu",
    )
    assert dcp_msg["type"] == "PresentationResponseMessage"
    assert dcp_msg["presentation"][0]["type"] == ["VerifiablePresentation"]
    assert "proof" in dcp_msg["presentation"][0]

    extracted = extract_dcp_presentation_claims(
        dcp_presentation_message=dcp_msg,
        expected_holder_did="did:web:consumer.energy-dataspace.eu",
    )
    assert extracted["dcp_verified"] is True
    assert extracted["holder_did"] == "did:web:consumer.energy-dataspace.eu"
    assert "cap:Declaration" in extracted["credential_types"]


def test_data_plane_signaling_prepare_and_agreement_retrieval_flow() -> None:
    """Verify consumer data-plane registration flow: DataFlowPrepareMessage ->
    GET /transfers/:dataFlowId/agreement -> payload evaluation -> S-Cert audit record."""
    from odgs.dataspace import (
        DataPlaneSignalingBridge,
        build_agreement_retrieval_path,
    )

    data_flow_id = "urn:uuid:dsp-transfer-flow-7701"
    agreement_id = "urn:uuid:dsp-agreement-grid-2026-44"

    assert (
        build_agreement_retrieval_path(data_flow_id)
        == f"/transfers/{data_flow_id}/agreement"
    )

    stored_agreements = {
        data_flow_id: {
            "@context": "https://w3id.org/dspace/2025/1/context.jsonld",
            "@id": agreement_id,
            "@type": "odrl:Agreement",
            "odrl:target": "urn:uuid:dataset-grid-load-2026",
            "dspace:consumerId": "did:web:consumer.energy-dataspace.eu",
            "dspace:providerId": "did:web:provider.energy-dataspace.eu",
            "odrl:obligation": [
                {
                    "odrl:uid": "urn:odrl:duty:k-anonymity-min-50",
                    "odrl:action": "odrl:aggregate",
                    "odrl:constraint": [
                        {
                            "odrl:leftOperand": "aggregation_household_count",
                            "odrl:operator": "odrl:gteq",
                            "odrl:rightOperand": 50,
                        }
                    ],
                }
            ],
        }
    }

    class MockControlPlaneClient:
        def __init__(self) -> None:
            self.requested_paths: list[str] = []
            self.notifications: list[tuple[str, dict]] = []

        def get_transfer_agreement(self, flow_id: str) -> dict:
            self.requested_paths.append(build_agreement_retrieval_path(flow_id))
            return stored_agreements[flow_id]

        def notify_transfer_event(self, flow_id: str, dsp_message: dict) -> None:
            self.notifications.append((flow_id, dsp_message))

    cp_client = MockControlPlaneClient()
    bridge = DataPlaneSignalingBridge(
        agreement_resolver=cp_client,
        control_plane_notifier=cp_client,
        system_id="consumer-dataplane-01",
    )

    prepare_msg = {
        "@context": "https://w3id.org/dspace/2025/1/dps/context.jsonld",
        "@type": "DataFlowPrepareMessage",
        "processId": data_flow_id,
        "agreementId": agreement_id,
        "participantId": "did:web:consumer.energy-dataspace.eu",
        "counterPartyId": "did:web:provider.energy-dataspace.eu",
        "providerPid": "urn:uuid:provider-transfer-pid-88",
    }

    prep_resp = bridge.prepare_flow(
        signaling_message=prepare_msg,
        process_urn="urn:odgs:process:consumer:dataplane-ingest",
    )
    assert prep_resp["@type"] == "DataFlowResponseMessage"
    assert prep_resp["state"] == "PREPARED"
    assert cp_client.requested_paths == [f"/transfers/{data_flow_id}/agreement"]

    # 1. Conformant payload -> PASS S-Cert (Consumer First-Party Audit Record)
    eval_pass = bridge.evaluate_flow(
        data_flow_id=data_flow_id,
        payload={"aggregation_household_count": 82, "region": "NL-ZH"},
    )
    assert eval_pass.verdict == Verdict.PASS
    assert eval_pass.trust_model == "CONSUMER_FIRST_PARTY_AUDIT_RECORD"
    assert eval_pass.dsp_control_message is None
    assert (
        eval_pass.s_cert.correlation_id
        == f"{agreement_id}#transfer:{data_flow_id}"
    )
    jsonschema.validate(instance=eval_pass.s_cert.to_canonical_dict(), schema=SCERT_SCHEMA)

    # 2. Violating payload -> HARD_STOP -> emits dspace:TransferTerminationMessage
    eval_fail = bridge.evaluate_flow(
        data_flow_id=data_flow_id,
        payload={"aggregation_household_count": 14, "region": "NL-ZH"},
    )
    assert eval_fail.verdict == Verdict.HARD_STOP
    assert eval_fail.dsp_control_message is not None
    assert eval_fail.dsp_control_message["@type"] == "dspace:TransferTerminationMessage"
    assert eval_fail.dsp_control_message["dspace:consumerPid"] == data_flow_id
    assert (
        eval_fail.dsp_control_message["dspace:providerPid"]
        == "urn:uuid:provider-transfer-pid-88"
    )
    assert len(cp_client.notifications) == 1
    assert cp_client.notifications[0][0] == data_flow_id
    assert (
        cp_client.notifications[0][1]["@type"]
        == "dspace:TransferTerminationMessage"
    )


def test_dsp_transfer_suspension_message_on_soft_stop() -> None:
    """Verify SOFT_STOP violation emits dspace:TransferSuspensionMessage when un-overridden."""
    from odgs.dataspace import build_dsp_transfer_suspension_message

    process_urn = "urn:odgs:process:consumer:latency-flow"
    soft_rule = ExecutableRule(
        rule_id="FLOW-SOFT-001",
        pack_id="ODGS-DSP-SOFT",
        legislative_source="DSP SLA Clause 3",
        semantic_hash=compute_semantic_hash("batch_size <= 1000"),
        verbatim_source_text="batch_size <= 1000",
        expression="batch_size <= 1000",
        fields_evaluated=("batch_size",),
        verdict_on_fail=Verdict.SOFT_STOP,
        plain_english_description="Suspend flow if batch_size exceeds 1000",
        non_conformance_message="Batch size exceeded 1000",
        bound_processes=(process_urn,),
    )
    binding = ProcessBinding(
        process_urn=process_urn,
        bound_rules=("FLOW-SOFT-001",),
        correlation_id="urn:uuid:agr-1#transfer:urn:uuid:flow-1",
    )
    pep = DataspaceRuntimePEP(rules=[soft_rule], bindings=[binding])

    with pytest.raises(SoftStopOverrideRequiredError) as exc_info:
        pep.evaluate(process_urn=process_urn, payload={"batch_size": 2500})

    susp_msg = build_dsp_transfer_suspension_message(
        consumer_pid="urn:uuid:flow-1",
        provider_pid="urn:uuid:prov-flow-1",
        s_cert=exc_info.value.s_cert,
        reason="SOFT_STOP triggered on batch_size constraint; awaiting override or remediation.",
    )
    assert susp_msg["@type"] == "dspace:TransferSuspensionMessage"
    assert susp_msg["dspace:consumerPid"] == "urn:uuid:flow-1"
    assert susp_msg["dspace:providerPid"] == "urn:uuid:prov-flow-1"
    assert susp_msg["dspace:code"] == "ODGS_SOFT_STOP"
    assert any(exc_info.value.s_cert.event_id in str(r) for r in susp_msg["dspace:reason"])


def test_dcp_did_signed_vc_and_presentation_query_exchange() -> None:
    """Verify runtime evidence issued as a DID-signed VC, held in consumer store,
    and presented via DCP PresentationQueryMessage -> PresentationResponseMessage."""
    from odgs.dataspace import (
        handle_dcp_presentation_query,
        verify_cap_declaration_vc,
    )

    consumer_did = "did:web:consumer.energy-dataspace.eu"
    key_id = f"{consumer_did}#key-ed25519-1"
    priv_key = Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    odrl_agreement = {
        "@id": "urn:uuid:dsp-agreement-992",
        "obligation": [
            {
                "uid": "urn:odrl:duty:min-records",
                "constraint": [
                    {"leftOperand": "record_count", "operator": "gteq", "rightOperand": 10}
                ],
            }
        ],
    }
    process_urn = "urn:odgs:process:consumer:batch-transform"
    rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])
    s_cert = sign_s_cert_ed25519(
        s_cert=pep.evaluate(process_urn=process_urn, payload={"record_count": 25}),
        private_key=priv_key,
        authority_id=consumer_did,
        issuing_jwk_url="https://consumer.energy-dataspace.eu/.well-known/jwks.json",
        kid=key_id,
    )

    signed_vc = export_cap_declaration_vc(
        s_cert=s_cert,
        issuer_did=consumer_did,
        subject_did=f"{consumer_did}#dataplane",
        private_key=priv_key,
        verification_method=key_id,
    )
    assert "proof" in signed_vc
    assert signed_vc["proof"]["verificationMethod"] == key_id
    assert verify_cap_declaration_vc(
        vc=signed_vc,
        public_key=pub_key,
        expected_issuer_did=consumer_did,
    ) is True

    # Provider sends DCP PresentationQueryMessage requesting cap:Declaration audit credentials
    dcp_query = {
        "@context": ["https://w3id.org/dspace-dcp/v1.0/dcp.jsonld"],
        "type": "PresentationQueryMessage",
        "scope": ["org.eclipse.dspace.dcp.vc.type:cap:Declaration:read"],
    }
    dcp_response = handle_dcp_presentation_query(
        query_message=dcp_query,
        stored_credentials=[signed_vc],
        holder_did=consumer_did,
        private_key=priv_key,
        verification_method=key_id,
    )
    assert dcp_response["type"] == "PresentationResponseMessage"
    returned_vc = dcp_response["presentation"][0]["verifiableCredential"][0]
    assert verify_cap_declaration_vc(
        vc=returned_vc,
        public_key=pub_key,
        expected_issuer_did=consumer_did,
    ) is True


def test_trust_model_constraint_observability_classification() -> None:
    """Verify ODRL behavioral usage constraints (purpose, retention, onward sharing)
    are explicitly flagged as unobservable via pre-processing payload inspection."""
    from odgs.dataspace import inspect_odrl_constraint_observability

    mixed_policy = {
        "@id": "urn:uuid:agreement-mixed-observability",
        "permission": [
            {
                "uid": "urn:odrl:perm:purpose-and-retention",
                "action": "use",
                "constraint": [
                    {
                        "leftOperand": "odrl:purpose",
                        "operator": "eq",
                        "rightOperand": "grid-capacity-planning",
                    },
                    {
                        "leftOperand": "odrl:elapsedTime",
                        "operator": "lteq",
                        "rightOperand": "P30D",
                    },
                ],
            }
        ],
        "prohibition": [
            {
                "uid": "urn:odrl:prohib:no-onward-sharing",
                "action": "odrl:distribute",
            }
        ],
        "obligation": [
            {
                "uid": "urn:odrl:duty:k-anonymity-50",
                "action": "aggregate",
                "constraint": [
                    {
                        "leftOperand": "aggregation_household_count",
                        "operator": "gteq",
                        "rightOperand": 50,
                    }
                ],
            }
        ],
    }

    report = inspect_odrl_constraint_observability(mixed_policy)
    assert report.trust_model == "CONSUMER_FIRST_PARTY_AUDIT_RECORD"
    assert "aggregation_household_count" in report.observable_payload_operands
    assert any("purpose" in item for item in report.unobservable_usage_constraints)
    assert any("elapsedTime" in item for item in report.unobservable_usage_constraints)
    assert any("distribute" in item for item in report.unobservable_usage_constraints)
    assert report.fully_observable_in_payload is False


def test_signaling_and_vc_security_edge_cases() -> None:
    """Verify security input validation, SOFT_STOP bridge suspension, and tampered VC rejection."""
    from odgs.dataspace import (
        DataPlaneSignalingBridge,
        build_agreement_retrieval_path,
        handle_dcp_presentation_query,
        verify_cap_declaration_vc,
    )

    # Path traversal / invalid IDs rejected
    for bad_id in ("", "   ", "../secret", "flow/../../etc"):
        with pytest.raises(ValueError):
            build_agreement_retrieval_path(bad_id)

    class SoftAgreementResolver:
        def get_transfer_agreement(self, flow_id: str) -> dict:
            return {
                "@id": "urn:uuid:agr-soft-1",
                "obligation": [
                    {
                        "uid": "urn:odrl:duty:check-count",
                        "constraint": [
                            {"leftOperand": "count_val", "operator": "gteq", "rightOperand": 5}
                        ],
                    }
                ],
            }

    events: list[tuple[str, dict]] = []

    class Notifier:
        def notify_transfer_event(self, flow_id: str, dsp_message: dict) -> None:
            events.append((flow_id, dsp_message))

    bridge = DataPlaneSignalingBridge(
        agreement_resolver=SoftAgreementResolver(),
        control_plane_notifier=Notifier(),
    )

    with pytest.raises(ValueError, match="Unsupported Data Plane Signaling"):
        bridge.prepare_flow({"@type": "UnknownMessage"}, "urn:odgs:process:a:b")

    with pytest.raises(ValueError, match="must include"):
        bridge.prepare_flow({"@type": "DataFlowStartMessage"}, "urn:odgs:process:a:b")

    with pytest.raises(KeyError):
        bridge.evaluate_flow("urn:uuid:unprepared", {"count_val": 1})

    start_resp = bridge.prepare_flow(
        {
            "@type": "DataFlowStartMessage",
            "dataFlowId": "urn:uuid:flow-start-1",
            "agreementId": "urn:uuid:agr-soft-1",
        },
        process_urn="urn:odgs:process:consumer:start-flow",
    )
    assert start_resp["state"] == "STARTED"

    # Tampered VC verification fails closed
    priv_key = Ed25519PrivateKey.generate()
    wrong_key = Ed25519PrivateKey.generate()
    eval_res = bridge.evaluate_flow("urn:uuid:flow-start-1", {"count_val": 10})
    vc = export_cap_declaration_vc(
        s_cert=eval_res.s_cert,
        issuer_did="did:web:consumer.example.eu",
        subject_did="did:web:consumer.example.eu#dp",
        private_key=priv_key,
    )
    assert verify_cap_declaration_vc(vc, wrong_key.public_key()) is False
    assert (
        verify_cap_declaration_vc(
            vc, priv_key.public_key(), expected_issuer_did="did:web:other.example.eu"
        )
        is False
    )
    tampered_vc = {**vc, "issuer": "did:web:attacker.example.eu"}
    assert verify_cap_declaration_vc(tampered_vc, priv_key.public_key()) is False

    with pytest.raises(ValueError, match="PresentationQueryMessage"):
        handle_dcp_presentation_query(
            {"type": "InvalidQuery"}, [vc], "did:web:consumer.example.eu"
        )


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


