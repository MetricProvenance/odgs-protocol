"""Phase 6 Runtime Policy Enforcement Point (PEP) for Dataspace Transactions."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import socket
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import jsonschema
from simpleeval import NameNotDefined, simple_eval

from odgs.dataspace.models import (
    ExecutableRule,
    ProcessBinding,
    SemanticCertificate,
    Verdict,
)

_SCHEMA_PATH = Path(__file__).resolve().parents[4] / "1_NORMATIVE_SPECIFICATION" / "schemas" / "04-s-cert-schema.json"


class AdministrativeRecusalError(RuntimeError):
    """Raised when a HARD_STOP governance rule is breached at runtime (Clause 7.1)."""

    def __init__(self, message: str, s_cert: SemanticCertificate) -> None:
        super().__init__(message)
        self.s_cert = s_cert


class SoftStopOverrideRequiredError(RuntimeError):
    """Raised when a SOFT_STOP rule is breached without an authorised override token (Clause 7.3)."""

    def __init__(self, message: str, s_cert: SemanticCertificate) -> None:
        super().__init__(message)
        self.s_cert = s_cert


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 digest of a runtime payload (Clause 8.2.1 Data Minimisation)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class DataspaceRuntimePEP:
    """Deterministic Plane IV Policy Enforcement Point (PEP) for Phase 6 dataspace execution."""

    def __init__(
        self,
        rules: Sequence[ExecutableRule],
        bindings: Sequence[ProcessBinding],
        system_id: Optional[str] = None,
        validate_s_cert_schema: bool = True,
    ) -> None:
        self._rules_by_id: Dict[str, ExecutableRule] = {r.rule_id: r for r in rules}
        self._bindings_by_urn: Dict[str, ProcessBinding] = {
            b.process_urn: b for b in bindings
        }
        self._system_id = (
            system_id
            or os.environ.get("ODGS_SYSTEM_ID")
            or socket.gethostname()
            or "odgs-dataspace-pep"
        )
        self._validate_schema = validate_s_cert_schema
        self._s_cert_schema: Optional[Dict[str, Any]] = None
        if validate_s_cert_schema and _SCHEMA_PATH.exists():
            self._s_cert_schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

    def evaluate(
        self,
        process_urn: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        override_token: Optional[str] = None,
    ) -> SemanticCertificate:
        """Evaluate a runtime payload at `process_urn`, enforce HARD_STOP/SOFT_STOP, and emit an S-Cert."""
        if process_urn not in self._bindings_by_urn:
            raise KeyError(f"No Plane III ProcessBinding registered for '{process_urn}'.")

        binding = self._bindings_by_urn[process_urn]
        eff_correlation_id = correlation_id or binding.correlation_id
        payload_hash = compute_payload_hash(payload)

        active_rules: List[ExecutableRule] = []
        for rid in binding.bound_rules:
            if rid not in self._rules_by_id:
                raise KeyError(f"Bound rule '{rid}' not found in registered rules.")
            active_rules.append(self._rules_by_id[rid])

        verdict = Verdict.PASS
        violated_rule: Optional[ExecutableRule] = None
        failure_reason: str = ""

        for rule in active_rules:
            try:
                passed = bool(
                    simple_eval(
                        rule.expression,
                        names=payload,
                        functions={"len": len, "min": min, "max": max, "abs": abs},
                    )
                )
            except NameNotDefined as exc:
                passed = False
                failure_reason = f"Missing required field in payload: {exc}"
            except Exception as exc:
                passed = False
                failure_reason = f"Deterministic evaluation error: {exc}"

            if not passed:
                violated_rule = rule
                if not failure_reason:
                    failure_reason = rule.non_conformance_message
                verdict = rule.verdict_on_fail
                break

        primary_rule = violated_rule or active_rules[0]
        s_cert = SemanticCertificate(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            process_urn=process_urn,
            rule_id=primary_rule.rule_id,
            semantic_hash=primary_rule.semantic_hash,
            verdict=verdict,
            system_id=self._system_id,
            payload_hash=payload_hash,
            correlation_id=eff_correlation_id,
        )

        if self._validate_schema and self._s_cert_schema is not None:
            jsonschema.validate(
                instance=s_cert.to_canonical_dict(), schema=self._s_cert_schema
            )

        if verdict == Verdict.HARD_STOP:
            raise AdministrativeRecusalError(
                f"HARD_STOP (Administrative Recusal) at {process_urn} "
                f"[rule={primary_rule.rule_id}]: {failure_reason}",
                s_cert=s_cert,
            )

        if verdict == Verdict.SOFT_STOP and not override_token:
            raise SoftStopOverrideRequiredError(
                f"SOFT_STOP at {process_urn} [rule={primary_rule.rule_id}]: "
                f"override_token required to proceed ({failure_reason})",
                s_cert=s_cert,
            )

        return s_cert
