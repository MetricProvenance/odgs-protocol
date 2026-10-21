"""Exporters for Eclipse CAP v2.2.1 (W3C VC v2.0), W3C PROV-O, and NIST OSCAL v1.1.2."""

from __future__ import annotations

from typing import Any, Dict, Optional

from odgs.dataspace.models import SemanticCertificate, Verdict


def export_cap_cred_evidence(s_cert: SemanticCertificate) -> Dict[str, Any]:
    """Export an ODGS S-Cert as a W3C VC v2.0 / Eclipse CAP v2.2.1 `cred:Evidence` block.

    Aligns directly with `gitlab.eclipse.org/eclipse/dataspace-cap/cap-ontology` (`linkml/cap.yaml`).
    """
    evidence: Dict[str, Any] = {
        "id": f"urn:uuid:{s_cert.event_id}",
        "type": ["Evidence", "odgs:SemanticCertificate"],
        "cred:id": f"urn:uuid:{s_cert.event_id}",
        "cred:digest": f"sha256-{s_cert.compute_evidence_digest()}",
        "odgs:processUrn": s_cert.process_urn,
        "odgs:ruleId": s_cert.rule_id,
        "odgs:semanticHash": s_cert.semantic_hash,
        "odgs:payloadHash": s_cert.payload_hash,
        "odgs:verdict": s_cert.verdict.value,
        "odgs:timestamp": s_cert.timestamp,
        "odgs:systemId": s_cert.system_id,
    }
    if s_cert.correlation_id:
        evidence["odgs:correlationId"] = s_cert.correlation_id
    if s_cert.jws_signature:
        evidence["odgs:jwsSignature"] = s_cert.jws_signature
        evidence["odgs:authorityId"] = s_cert.authority_id
        evidence["odgs:issuingJwkUrl"] = s_cert.issuing_jwk_url
    return evidence


def export_cap_declaration_vc(
    s_cert: SemanticCertificate,
    issuer_did: str,
    subject_did: str,
    scheme_uri: str = "https://w3id.org/eclipse-cap/v2.2.1/scheme/dataspace-governance",
    requirement_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap an ODGS S-Cert inside an Eclipse CAP v2.2.1 `cap:Declaration` W3C Verifiable Credential v2.0."""
    req_uri = requirement_uri or f"urn:odgs:rule:{s_cert.rule_id}#sha256:{s_cert.semantic_hash}"
    return {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://w3id.org/eclipse-cap/v2.2.1/",
            "https://w3id.org/odgs/dataspace/v1",
        ],
        "id": f"urn:uuid:{s_cert.event_id}:cap-declaration",
        "type": ["VerifiableCredential", "cap:Declaration"],
        "issuer": issuer_did,
        "validFrom": s_cert.timestamp,
        "credentialSubject": {
            "id": subject_did,
            "type": "cap:ConformityAssessment",
            "cap:conformsToScheme": scheme_uri,
            "cap:assessedRequirement": {
                "id": req_uri,
                "type": "cap:SpecifiedRequirement",
                "odgs:semanticHash": s_cert.semantic_hash,
            },
            "cap:assessmentOutcome": (
                "CONFORMANT" if s_cert.verdict == Verdict.PASS else "NON_CONFORMANT"
            ),
        },
        "evidence": [export_cap_cred_evidence(s_cert)],
    }


def export_w3c_prov_o(s_cert: SemanticCertificate) -> Dict[str, Any]:
    """Export an ODGS S-Cert as a W3C PROV-O JSON-LD provenance graph."""
    relation_key = (
        "prov:wasGeneratedBy"
        if s_cert.verdict == Verdict.PASS
        else "prov:wasInvalidatedBy"
    )
    return {
        "@context": {
            "prov": "http://www.w3.org/ns/prov#",
            "odgs": "https://w3id.org/odgs/dataspace/v1#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
        },
        "@graph": [
            {
                "@id": f"urn:sha256:{s_cert.payload_hash}",
                "@type": "prov:Entity",
                "odgs:payloadHash": s_cert.payload_hash,
            },
            {
                "@id": f"urn:uuid:{s_cert.event_id}",
                "@type": ["prov:Entity", "odgs:SemanticCertificate"],
                relation_key: {"@id": f"{s_cert.process_urn}#eval-{s_cert.event_id}"},
                "prov:generatedAtTime": s_cert.timestamp,
                "odgs:verdict": s_cert.verdict.value,
                "odgs:correlationId": s_cert.correlation_id,
            },
            {
                "@id": f"{s_cert.process_urn}#eval-{s_cert.event_id}",
                "@type": "prov:Activity",
                "prov:used": {"@id": f"urn:sha256:{s_cert.payload_hash}"},
                "prov:wasAssociatedWith": {"@id": f"urn:odgs:system:{s_cert.system_id}"},
                "prov:qualifiedAssociation": {
                    "@type": "prov:Association",
                    "prov:agent": {"@id": f"urn:odgs:system:{s_cert.system_id}"},
                    "prov:hadPlan": {
                        "@id": f"urn:odgs:rule:{s_cert.rule_id}",
                        "@type": ["prov:Plan", "prov:Entity"],
                        "odgs:semanticHash": s_cert.semantic_hash,
                    },
                },
            },
            {
                "@id": f"urn:odgs:system:{s_cert.system_id}",
                "@type": ["prov:SoftwareAgent", "prov:Agent"],
            },
        ],
    }


def export_nist_oscal_finding(s_cert: SemanticCertificate) -> Dict[str, Any]:
    """Export an ODGS S-Cert as a NIST OSCAL v1.1.2 Assessment Results `finding` object."""
    is_satisfied = s_cert.verdict == Verdict.PASS
    finding: Dict[str, Any] = {
        "uuid": s_cert.event_id,
        "title": f"ODGS Runtime Assessment — {s_cert.rule_id}",
        "description": (
            f"Deterministic Plane IV evaluation of rule '{s_cert.rule_id}' "
            f"at process '{s_cert.process_urn}'."
        ),
        "target": {
            "type": "objective-id",
            "target-id": s_cert.rule_id,
            "status": {
                "state": "satisfied" if is_satisfied else "not-satisfied",
                "reason": s_cert.verdict.value,
            },
            "props": [
                {"name": "semantic_hash", "value": s_cert.semantic_hash},
                {"name": "process_urn", "value": s_cert.process_urn},
            ],
        },
        "observation": {
            "uuid": s_cert.event_id,
            "collected": s_cert.timestamp,
            "methods": ["TEST-AUTOMATED"],
            "subject-references": [
                {
                    "subject-uuid": s_cert.event_id,
                    "type": "component",
                    "props": [
                        {"name": "payload_hash", "value": s_cert.payload_hash},
                        {"name": "system_id", "value": s_cert.system_id},
                    ],
                }
            ],
        },
    }
    if s_cert.correlation_id:
        finding["target"]["props"].append(
            {"name": "correlation_id", "value": s_cert.correlation_id}
        )
    if s_cert.verdict == Verdict.SOFT_STOP:
        finding["associated-risk"] = {
            "status": "open",
            "description": "SOFT_STOP non-conformance logged with override token.",
        }
    return finding
