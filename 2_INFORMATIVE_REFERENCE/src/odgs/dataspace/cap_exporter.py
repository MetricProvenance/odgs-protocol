"""Exporters for Eclipse DCP v1.0 (ISO/IEC DIS 26451), Eclipse CAP v2.2.1 (W3C VC v2.0), W3C PROV-O, and NIST OSCAL v1.1.2."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

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


def _canonical_vc_claims(vc: Dict[str, Any]) -> Dict[str, Any]:
    """Return canonical VC claims excluding any detached `proof` envelope."""
    without_proof = {k: v for k, v in vc.items() if k != "proof"}
    return json.loads(json.dumps(without_proof, sort_keys=True, separators=(",", ":")))


def export_cap_declaration_vc(
    s_cert: SemanticCertificate,
    issuer_did: str,
    subject_did: str,
    scheme_uri: str = "https://w3id.org/eclipse-cap/v2.2.1/scheme/dataspace-governance",
    requirement_uri: Optional[str] = None,
    private_key: Optional[Ed25519PrivateKey] = None,
    verification_method: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap an ODGS S-Cert inside an Eclipse CAP v2.2.1 `cap:Declaration` W3C Verifiable Credential v2.0.

    Under the ODGS cross-party dataspace trust model, this credential represents a consumer-signed
    **first-party audit declaration** (`cap:Declaration` per ISO/IEC 17000) recording that the
    consumer evaluated payload-observable constraints against the referenced payload digest.
    When `private_key` is supplied, the credential itself is signed with the key from the
    consumer's DID document (`verification_method`).
    """
    req_uri = requirement_uri or f"urn:odgs:rule:{s_cert.rule_id}#sha256:{s_cert.semantic_hash}"
    vc: Dict[str, Any] = {
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
    if private_key is not None:
        eff_vm = verification_method or f"{issuer_did}#key-1"
        vc_jws = jwt.encode(
            payload=_canonical_vc_claims(vc),
            key=private_key,
            algorithm="EdDSA",
            headers={"kid": eff_vm, "typ": "vc+jwt"},
        )
        vc = {
            **vc,
            "proof": {
                "type": "JsonWebSignature2020",
                "created": s_cert.timestamp,
                "verificationMethod": eff_vm,
                "proofPurpose": "assertionMethod",
                "jws": vc_jws,
            },
        }
    return vc


def verify_cap_declaration_vc(
    vc: Dict[str, Any],
    public_key: Ed25519PublicKey,
    expected_issuer_did: Optional[str] = None,
) -> bool:
    """Cryptographically verify a DID-signed `cap:Declaration` Verifiable Credential."""
    if expected_issuer_did and vc.get("issuer") != expected_issuer_did:
        return False
    proof = vc.get("proof")
    if not isinstance(proof, dict) or not proof.get("jws"):
        return False
    try:
        decoded = jwt.decode(
            proof["jws"],
            key=public_key,
            algorithms=["EdDSA"],
            options={"verify_aud": False},
        )
        return decoded == _canonical_vc_claims(vc)
    except Exception:
        return False


def export_dcp_presentation_response(
    s_cert: SemanticCertificate,
    holder_did: str,
    subject_did: Optional[str] = None,
    scheme_uri: str = "https://w3id.org/eclipse-cap/v2.2.1/scheme/dataspace-governance",
    requirement_uri: Optional[str] = None,
    private_key: Optional[Ed25519PrivateKey] = None,
    verification_method: Optional[str] = None,
) -> Dict[str, Any]:
    """Export an ODGS S-Cert as an Eclipse DCP v1.0 (ISO/IEC DIS 26451) `PresentationResponseMessage`."""
    eff_subject_did = subject_did or f"{holder_did}#{s_cert.system_id}"
    vc = export_cap_declaration_vc(
        s_cert=s_cert,
        issuer_did=holder_did,
        subject_did=eff_subject_did,
        scheme_uri=scheme_uri,
        requirement_uri=requirement_uri,
        private_key=private_key,
        verification_method=verification_method,
    )
    vp: Dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://w3id.org/eclipse-cap/v2.2.1/",
            "https://w3id.org/odgs/dataspace/v1",
        ],
        "id": f"urn:uuid:{s_cert.event_id}:dcp-vp",
        "type": ["VerifiablePresentation"],
        "holder": holder_did,
        "verifiableCredential": [vc],
    }
    eff_vm = verification_method or s_cert.issuing_jwk_url or f"{holder_did}#key-1"
    if private_key is not None:
        vp_jws = jwt.encode(
            payload=_canonical_vc_claims(vp),
            key=private_key,
            algorithm="EdDSA",
            headers={"kid": eff_vm, "typ": "vp+jwt"},
        )
        vp = {
            **vp,
            "proof": {
                "type": "JsonWebSignature2020",
                "created": s_cert.timestamp,
                "verificationMethod": eff_vm,
                "proofPurpose": "authentication",
                "jws": vp_jws,
            },
        }
    elif s_cert.jws_signature:
        vp = {
            **vp,
            "proof": {
                "type": "JsonWebSignature2020",
                "created": s_cert.timestamp,
                "verificationMethod": eff_vm,
                "proofPurpose": "authentication",
                "jws": s_cert.jws_signature,
            },
        }
    return {
        "@context": [
            "https://w3id.org/dspace-dcp/v1.0/dcp.jsonld",
        ],
        "type": "PresentationResponseMessage",
        "presentation": [vp],
    }


def handle_dcp_presentation_query(
    query_message: Dict[str, Any],
    stored_credentials: Sequence[Dict[str, Any]],
    holder_did: str,
    private_key: Optional[Ed25519PrivateKey] = None,
    verification_method: Optional[str] = None,
) -> Dict[str, Any]:
    """Respond to an Eclipse DCP `PresentationQueryMessage` from a consumer credential store."""
    msg_type = query_message.get("type") or query_message.get("@type")
    if msg_type != "PresentationQueryMessage":
        raise ValueError(
            f"Expected Eclipse DCP 'PresentationQueryMessage', got '{msg_type}'."
        )

    scopes = [str(s) for s in query_message.get("scope", [])]
    requested_types: List[str] = []
    for scope in scopes:
        # Format: org.eclipse.dspace.dcp.vc.type:<vcType>:<permission>
        parts = scope.split("org.eclipse.dspace.dcp.vc.type:")
        if len(parts) == 2:
            vc_type_part = parts[1].rsplit(":", 1)[0]
            if vc_type_part:
                requested_types.append(vc_type_part)

    matched: List[Dict[str, Any]] = []
    for cred in stored_credentials:
        c_types = cred.get("type", [])
        if isinstance(c_types, str):
            c_types = [c_types]
        if not requested_types or any(rt in c_types for rt in requested_types):
            matched.append(dict(cred))

    vp: Dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://w3id.org/eclipse-cap/v2.2.1/",
            "https://w3id.org/odgs/dataspace/v1",
        ],
        "type": ["VerifiablePresentation"],
        "holder": holder_did,
        "verifiableCredential": matched,
    }
    if private_key is not None:
        eff_vm = verification_method or f"{holder_did}#key-1"
        vp_jws = jwt.encode(
            payload=_canonical_vc_claims(vp),
            key=private_key,
            algorithm="EdDSA",
            headers={"kid": eff_vm, "typ": "vp+jwt"},
        )
        vp = {
            **vp,
            "proof": {
                "type": "JsonWebSignature2020",
                "verificationMethod": eff_vm,
                "proofPurpose": "authentication",
                "jws": vp_jws,
            },
        }

    return {
        "@context": ["https://w3id.org/dspace-dcp/v1.0/dcp.jsonld"],
        "type": "PresentationResponseMessage",
        "presentation": [vp],
    }


def extract_dcp_presentation_claims(
    dcp_presentation_message: Dict[str, Any],
    expected_holder_did: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract and validate participant claims from an incoming Eclipse DCP `PresentationResponseMessage`.

    Used on the inbound control-to-data-plane boundary to bind DCP-verified participant
    credentials (such as membership, license, or conformity attributes) into the ODGS
    runtime evaluation payload.
    """
    msg_type = dcp_presentation_message.get("type") or dcp_presentation_message.get("@type")
    if msg_type != "PresentationResponseMessage":
        raise ValueError(
            f"Expected Eclipse DCP 'PresentationResponseMessage', got '{msg_type}'."
        )
    presentations = dcp_presentation_message.get("presentation", [])
    if not presentations or not isinstance(presentations, list):
        raise ValueError("Eclipse DCP PresentationResponseMessage contains no presentations.")

    holders: List[str] = []
    vc_ids: List[str] = []
    credential_types: List[str] = []
    subject_claims: List[Dict[str, Any]] = []

    for vp in presentations:
        if not isinstance(vp, dict):
            continue
        holder = vp.get("holder")
        if holder:
            holders.append(str(holder))
            if expected_holder_did and str(holder) != expected_holder_did:
                raise ValueError(
                    f"DCP holder DID mismatch: expected '{expected_holder_did}', got '{holder}'."
                )
        for vc in vp.get("verifiableCredential", []):
            if not isinstance(vc, dict):
                continue
            if "id" in vc:
                vc_ids.append(str(vc["id"]))
            vc_type = vc.get("type", [])
            if isinstance(vc_type, list):
                credential_types.extend(str(t) for t in vc_type)
            elif vc_type:
                credential_types.append(str(vc_type))
            cred_subj = vc.get("credentialSubject")
            if isinstance(cred_subj, dict):
                subject_claims.append(cred_subj)

    return {
        "dcp_verified": True,
        "holder_did": holders[0] if holders else None,
        "vc_ids": vc_ids,
        "credential_types": credential_types,
        "subject_claims": subject_claims,
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
