"""Immutable domain models for ODGS Dataspace Runtime Enforcement & Semantic Certification."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Verdict(str, Enum):
    """Deterministic Plane IV runtime evaluation outcomes."""

    PASS = "PASS"
    HARD_STOP = "HARD_STOP"
    SOFT_STOP = "SOFT_STOP"
    LOG_ONLY = "LOG_ONLY"


class ConformanceLevel(str, Enum):
    """ODGS technical implementation conformance profiles."""

    LEVEL_1_CORE = "LEVEL_1_CORE"
    LEVEL_2_ATTESTED = "LEVEL_2_ATTESTED"


class AuthoritativeSource(BaseModel):
    """Plane I Legislative / Rulebook Ontology source definition."""

    model_config = ConfigDict(frozen=True)

    source_urn: str = Field(..., pattern=r"^urn:odgs:def:[a-zA-Z0-9_-]+:[a-zA-Z0-9_.-]+$")
    legislative_source: str = Field(..., min_length=1)
    verbatim_source_text: str = Field(..., min_length=1)
    semantic_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    @classmethod
    def from_verbatim(
        cls,
        source_urn: str,
        legislative_source: str,
        verbatim_source_text: str,
    ) -> "AuthoritativeSource":
        """Create an immutable AuthoritativeSource with a deterministic SHA-256 semantic_hash."""
        digest = hashlib.sha256(verbatim_source_text.strip().encode("utf-8")).hexdigest()
        return cls(
            source_urn=source_urn,
            legislative_source=legislative_source,
            verbatim_source_text=verbatim_source_text.strip(),
            semantic_hash=digest,
        )


class ExecutableRule(BaseModel):
    """Plane II/IV deterministic executable governance rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., min_length=1)
    pack_id: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    legislative_source: str = Field(..., min_length=1)
    semantic_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    verbatim_source_text: str = Field(..., min_length=1)
    expression: str = Field(..., min_length=1)
    fields_evaluated: Tuple[str, ...] = Field(..., min_length=1)
    verdict_on_fail: Verdict = Field(default=Verdict.HARD_STOP)
    verdict_on_pass: Verdict = Field(default=Verdict.PASS)
    plain_english_description: str = Field(..., min_length=1)
    non_conformance_message: str = Field(..., min_length=1)
    bound_processes: Tuple[str, ...] = Field(..., min_length=1)
    effective_from: str = Field(default="2026-01-01T00:00:00Z")
    effective_to: Optional[str] = Field(default=None)
    odrl_policy_uid: Optional[str] = Field(default=None)
    odrl_rule_type: Optional[str] = Field(default=None)


class ProcessBinding(BaseModel):
    """Plane III Governance Binding associating rules and contract agreements with a process URN."""

    model_config = ConfigDict(frozen=True)

    process_urn: str = Field(..., pattern=r"^urn:odgs:process:[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$")
    bound_rules: Tuple[str, ...] = Field(..., min_length=1)
    correlation_id: Optional[str] = Field(default=None)
    delegation_license_ref: Optional[str] = Field(default=None)
    effective_from: str = Field(default="2026-01-01T00:00:00Z")
    effective_to: Optional[str] = Field(default=None)


class SemanticCertificate(BaseModel):
    """Zero-knowledge Semantic Certificate (S-Cert) emitted at runtime (Annex A)."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(..., min_length=36, max_length=36)
    timestamp: str = Field(..., min_length=20)
    process_urn: str = Field(..., pattern=r"^urn:odgs:process:[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$")
    rule_id: str = Field(..., min_length=1)
    semantic_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    verdict: Verdict
    system_id: str = Field(..., min_length=1)
    payload_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    correlation_id: Optional[str] = Field(default=None)
    jws_signature: Optional[str] = Field(default=None)
    authority_id: Optional[str] = Field(default=None)
    issuing_jwk_url: Optional[str] = Field(default=None)

    def to_canonical_dict(self, include_signature: bool = True) -> Dict[str, Any]:
        """Return a dictionary matching the normative S-Cert JSON Schema (excluding None fields)."""
        data: Dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "process_urn": self.process_urn,
            "rule_id": self.rule_id,
            "semantic_hash": self.semantic_hash,
            "verdict": self.verdict.value,
            "system_id": self.system_id,
            "payload_hash": self.payload_hash,
        }
        if self.correlation_id is not None:
            data["correlation_id"] = self.correlation_id
        if include_signature:
            if self.jws_signature is not None:
                data["jws_signature"] = self.jws_signature
            if self.authority_id is not None:
                data["authority_id"] = self.authority_id
            if self.issuing_jwk_url is not None:
                data["issuing_jwk_url"] = self.issuing_jwk_url
        return data

    def canonical_json_bytes(self, include_signature: bool = False) -> bytes:
        """Return deterministic canonical JSON bytes for cryptographic signing/digesting."""
        payload = self.to_canonical_dict(include_signature=include_signature)
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def compute_evidence_digest(self) -> str:
        """Compute the SHA-256 digest of the canonical S-Cert (or JWS signature if Level 2)."""
        if self.jws_signature:
            return hashlib.sha256(self.jws_signature.encode("utf-8")).hexdigest()
        return hashlib.sha256(self.canonical_json_bytes(include_signature=False)).hexdigest()


class DtaVerificationResult(BaseModel):
    """Result of verifying a consumer S-Cert against a Gaia-X DTA TransferRequestResult."""

    model_config = ConfigDict(frozen=True)

    verified: bool
    event_id: str
    correlation_id: Optional[str]
    verdict: Verdict
    semantic_hash_matched: bool
    signature_verified: bool
    reason: str
