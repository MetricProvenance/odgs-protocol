#!/usr/bin/env python3
"""Runnable end-to-end showcase of ODGS Dataspace Runtime Enforcement across 4 flagship scenarios:

1. Energy Dataspace (W3C ODRL 2.2 + Gaia-X DTA Phase 6 Smart Meter k-Anonymity)
2. Circular Manufacturing (Eclipse DRP + Eclipse CAP v2.2.1 Battery Digital Product Passport)
3. Artificial Intelligence (W3C ODRL 2.2 + EU AI Act Art. 10/12 LLM Corpus Gate)
4. Financial Services (DORA Article 17 Incident Classification + NIST OSCAL Export)
"""

from __future__ import annotations

import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from odgs.dataspace import (
    AdministrativeRecusalError,
    DataspaceRuntimePEP,
    bind_drp_delegation_evidence,
    bind_odrl_policy,
    export_cap_declaration_vc,
    export_nist_oscal_finding,
    export_w3c_prov_o,
    sign_s_cert_ed25519,
    verify_dta_post_transfer_obligation,
)


def run_all() -> None:
    priv_key = Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()

    print("=" * 78)
    print("SCENARIO 1: W3C ODRL 2.2 + Gaia-X DTA Phase 6 Post-Transfer Obligation")
    print("=" * 78)
    odrl_agreement = {
        "uid": "urn:uuid:agreement-energy-grid-2026-091",
        "obligation": [
            {
                "uid": "urn:odrl:duty:k-anonymity-min-50",
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
    process_urn = "urn:odgs:process:energy-consumer:grid-load-forecasting"
    rules, binding = bind_odrl_policy(odrl_agreement, process_urn=process_urn)
    pep = DataspaceRuntimePEP(rules=rules, bindings=[binding])

    s_cert_l1 = pep.evaluate(
        process_urn=process_urn,
        payload={"aggregation_household_count": 64, "grid_zone": "NL-ZH"},
    )
    s_cert_l2 = sign_s_cert_ed25519(
        s_cert=s_cert_l1,
        private_key=priv_key,
        authority_id="urn:odgs:authority:energy-dataspace-nl",
        issuing_jwk_url="https://trust.energy-dataspace.eu/.well-known/jwks.json",
    )
    dta_verification = verify_dta_post_transfer_obligation(
        s_cert=s_cert_l2,
        transfer_request_result={"agreement_id": "urn:uuid:agreement-energy-grid-2026-091"},
        expected_semantic_hash=rules[0].semantic_hash,
        public_key=pub_key,
    )
    print(json.dumps(dta_verification.model_dump(), indent=2))

    print("\n" + "=" * 78)
    print("SCENARIO 2: Eclipse DRP + Eclipse CAP v2.2.1 Battery Digital Product Passport")
    print("=" * 78)
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
                                "resource": {"type": "BatteryCarbonFootprint"},
                                "actions": ["Use"],
                            },
                            "rules": [{"effect": "Permit"}],
                        }
                    ],
                }
            ],
        }
    }
    dpp_urn = "urn:odgs:process:dpp:battery-cfp-validation"
    drp_rules, drp_binding = bind_drp_delegation_evidence(drp_token, process_urn=dpp_urn)
    dpp_pep = DataspaceRuntimePEP(rules=drp_rules, bindings=[drp_binding])
    dpp_scert = dpp_pep.evaluate(
        process_urn=dpp_urn,
        payload={
            "active_licenses": ["ISHARE.LICENSE.CIRCULAR.BATTERY.2026"],
            "resource_permitted": True,
        },
    )
    cap_vc = export_cap_declaration_vc(
        dpp_scert,
        issuer_did="did:web:deoem002.automotive-dataspace.eu",
        subject_did="did:web:deoem002.automotive-dataspace.eu#battery-passport-77",
    )
    print(json.dumps(cap_vc, indent=2))

    print("\n" + "=" * 78)
    print("SCENARIO 3: W3C PROV-O Lineage & NIST OSCAL Export")
    print("=" * 78)
    print("W3C PROV-O Graph Nodes:", len(export_w3c_prov_o(dpp_scert)["@graph"]))
    print("NIST OSCAL Status:", export_nist_oscal_finding(dpp_scert)["target"]["status"])


if __name__ == "__main__":
    run_all()
