"""Gaia-X Data Transfer Agent (DTA) Phase 6 Post-Transfer Obligation Verifier & JWS Signer."""

from __future__ import annotations

from typing import Any, Dict, Optional
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from odgs.dataspace.models import (
    DtaVerificationResult,
    SemanticCertificate,
    Verdict,
)


def sign_s_cert_ed25519(
    s_cert: SemanticCertificate,
    private_key: Ed25519PrivateKey,
    authority_id: str,
    issuing_jwk_url: str,
    kid: str = "odgs-ed25519-key-1",
) -> SemanticCertificate:
    """Sign a Level 1 S-Cert with Ed25519 (RFC 7515 JWS / EdDSA) to produce a Level 2 Attested S-Cert."""
    claims = s_cert.to_canonical_dict(include_signature=False)
    jws_token = jwt.encode(
        payload=claims,
        key=private_key,
        algorithm="EdDSA",
        headers={"kid": kid, "typ": "odgs-scert+jwt"},
    )
    return SemanticCertificate(
        **claims,
        jws_signature=jws_token,
        authority_id=authority_id,
        issuing_jwk_url=issuing_jwk_url,
    )


def verify_dta_post_transfer_obligation(
    s_cert: SemanticCertificate,
    transfer_request_result: Dict[str, Any],
    expected_semantic_hash: str,
    public_key: Optional[Ed25519PublicKey] = None,
    require_level_2_signature: bool = True,
) -> DtaVerificationResult:
    """Verify a consumer's Phase 6 S-Cert against a Phase 5 Gaia-X DTA TransferRequestResult.

    Addresses Gaia-X Architecture Document 25.11 §4.8.4.2 (*Policy Enforcement*):
    "In the last phase, the data consumer provides proof of the implemented policy
    enforcement, which the data product provider verifies."
    """
    expected_corr_id = str(
        transfer_request_result.get("agreement_id")
        or transfer_request_result.get("transfer_id")
        or transfer_request_result.get("correlation_id")
        or ""
    )

    # 1. Verify correlation_id matches the Phase 5 DTA transfer agreement
    if expected_corr_id and s_cert.correlation_id != expected_corr_id:
        return DtaVerificationResult(
            verified=False,
            event_id=s_cert.event_id,
            correlation_id=s_cert.correlation_id,
            verdict=s_cert.verdict,
            semantic_hash_matched=(s_cert.semantic_hash == expected_semantic_hash),
            signature_verified=False,
            reason=(
                f"Correlation ID mismatch: S-Cert has '{s_cert.correlation_id}', "
                f"expected '{expected_corr_id}'."
            ),
        )

    # 2. Verify semantic_hash matches the agreed ODRL / Rulebook obligation
    sem_matched = s_cert.semantic_hash == expected_semantic_hash
    if not sem_matched:
        return DtaVerificationResult(
            verified=False,
            event_id=s_cert.event_id,
            correlation_id=s_cert.correlation_id,
            verdict=s_cert.verdict,
            semantic_hash_matched=False,
            signature_verified=False,
            reason=(
                f"Semantic hash mismatch: S-Cert evaluated '{s_cert.semantic_hash}', "
                f"expected '{expected_semantic_hash}'."
            ),
        )

    # 3. Verify runtime verdict is PASS
    if s_cert.verdict != Verdict.PASS:
        return DtaVerificationResult(
            verified=False,
            event_id=s_cert.event_id,
            correlation_id=s_cert.correlation_id,
            verdict=s_cert.verdict,
            semantic_hash_matched=True,
            signature_verified=False,
            reason=f"Post-transfer obligation not satisfied: S-Cert verdict is '{s_cert.verdict.value}'.",
        )

    # 4. Verify Level 2 cryptographic signature (EdDSA / Ed25519) if required
    sig_verified = False
    if require_level_2_signature:
        if not s_cert.jws_signature or public_key is None:
            return DtaVerificationResult(
                verified=False,
                event_id=s_cert.event_id,
                correlation_id=s_cert.correlation_id,
                verdict=s_cert.verdict,
                semantic_hash_matched=True,
                signature_verified=False,
                reason="Level 2 Attested JWS signature required by DTA policy but missing or no public key supplied.",
            )
        try:
            decoded = jwt.decode(
                s_cert.jws_signature,
                key=public_key,
                algorithms=["EdDSA"],
                options={"verify_aud": False},
            )
            if (
                decoded.get("event_id") != s_cert.event_id
                or decoded.get("payload_hash") != s_cert.payload_hash
                or decoded.get("semantic_hash") != s_cert.semantic_hash
            ):
                return DtaVerificationResult(
                    verified=False,
                    event_id=s_cert.event_id,
                    correlation_id=s_cert.correlation_id,
                    verdict=s_cert.verdict,
                    semantic_hash_matched=True,
                    signature_verified=False,
                    reason="JWS claims do not match S-Cert envelope fields (tampering detected).",
                )
            sig_verified = True
        except Exception as exc:
            return DtaVerificationResult(
                verified=False,
                event_id=s_cert.event_id,
                correlation_id=s_cert.correlation_id,
                verdict=s_cert.verdict,
                semantic_hash_matched=True,
                signature_verified=False,
                reason=f"Ed25519 JWS signature verification failed: {exc}",
            )

    return DtaVerificationResult(
        verified=True,
        event_id=s_cert.event_id,
        correlation_id=s_cert.correlation_id,
        verdict=s_cert.verdict,
        semantic_hash_matched=True,
        signature_verified=sig_verified,
        reason="Post-transfer consumer obligation verified via ODGS S-Cert.",
    )
