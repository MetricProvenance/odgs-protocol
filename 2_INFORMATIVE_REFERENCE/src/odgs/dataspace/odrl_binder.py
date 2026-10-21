"""W3C ODRL 2.2, Gaia-X ODRL-VC, and Eclipse DRP Policy Binder for ODGS."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from odgs.dataspace.models import ExecutableRule, ProcessBinding, Verdict

_ODRL_OPERATOR_MAP: Dict[str, str] = {
    "eq": "==",
    "odrl:eq": "==",
    "neq": "!=",
    "odrl:neq": "!=",
    "gt": ">",
    "odrl:gt": ">",
    "gteq": ">=",
    "odrl:gteq": ">=",
    "lt": "<",
    "odrl:lt": "<",
    "lteq": "<=",
    "odrl:lteq": "<=",
}


def compute_semantic_hash(source_text_or_dict: Any) -> str:
    """Compute a deterministic lowercase hexadecimal SHA-256 digest."""
    if isinstance(source_text_or_dict, str):
        canonical = source_text_or_dict.strip().encode("utf-8")
    else:
        canonical = json.dumps(
            source_text_or_dict, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _extract_value(raw_operand: Any) -> Any:
    """Extract literal value from an ODRL rightOperand (which may be a dict with @value)."""
    if isinstance(raw_operand, dict) and "@value" in raw_operand:
        val = raw_operand["@value"]
        xsd_type = raw_operand.get("@type", "")
        if "integer" in xsd_type or "int" in xsd_type:
            return int(val)
        if "decimal" in xsd_type or "float" in xsd_type or "double" in xsd_type:
            return float(val)
        if "boolean" in xsd_type:
            return str(val).lower() == "true"
        return val
    return raw_operand


def _normalize_field_name(operand: str) -> str:
    """Normalize an ODRL leftOperand or JSONPath into a safe Python identifier."""
    cleaned = operand.strip()
    if cleaned.startswith("$."):
        cleaned = cleaned[2:]
    if ":" in cleaned:
        cleaned = cleaned.split(":")[-1]
    return cleaned.replace(".", "_").replace("-", "_")


def _compile_constraints(
    constraints: List[Dict[str, Any]], invert_for_prohibition: bool = False
) -> Tuple[str, Tuple[str, ...]]:
    """Compile a list of ODRL / OVC constraints into a deterministic boolean expression."""
    expressions: List[str] = []
    fields: List[str] = []

    for c in constraints:
        left_raw = c.get("leftOperand") if "leftOperand" in c else c.get("ovc:leftOperand")
        op_raw = c.get("operator") if "operator" in c else c.get("odrl:operator", "eq")
        right_raw = c["rightOperand"] if "rightOperand" in c else c.get("odrl:rightOperand")

        if not left_raw:
            raise ValueError(f"ODRL constraint missing leftOperand: {c}")

        field_name = _normalize_field_name(str(left_raw))
        if field_name not in fields:
            fields.append(field_name)

        py_op = _ODRL_OPERATOR_MAP.get(str(op_raw), "==")
        right_val = _extract_value(right_raw)
        right_repr = repr(right_val)

        clause = f"{field_name} {py_op} {right_repr}"
        expressions.append(clause)

    combined = " and ".join(expressions) if expressions else "True"
    if invert_for_prohibition and expressions:
        combined = f"not ({combined})"
    return combined, tuple(fields)


def bind_odrl_policy(
    odrl_policy: Dict[str, Any],
    process_urn: str,
    pack_id: str = "ODGS-DATASPACE-ODRL",
    correlation_id: Optional[str] = None,
) -> Tuple[Tuple[ExecutableRule, ...], ProcessBinding]:
    """Bind a W3C ODRL 2.2 / Gaia-X ODRL-VC Policy into ODGS ExecutableRules and a ProcessBinding.

    Supports `obligation` / `duty` (post-transfer consumer obligations), `prohibition`,
    and constrained `permission` blocks.
    """
    policy_uid = str(odrl_policy.get("uid") or odrl_policy.get("@id") or "urn:odrl:policy:unnamed")
    eff_corr_id = correlation_id or policy_uid
    compiled_rules: List[ExecutableRule] = []

    # 1. Process obligations / duties
    obligations = odrl_policy.get("obligation", []) + odrl_policy.get("duty", [])
    for idx, duty in enumerate(obligations):
        duty_uid = str(duty.get("uid") or f"{policy_uid}#duty-{idx + 1}")
        constraints = duty.get("constraint", []) + duty.get("refinement", [])
        if isinstance(duty.get("action"), dict):
            constraints = constraints + duty["action"].get("refinement", [])

        expr, eval_fields = _compile_constraints(constraints, invert_for_prohibition=False)
        verbatim = json.dumps(duty, sort_keys=True, separators=(",", ":"))
        sem_hash = compute_semantic_hash(verbatim)
        rule_id = f"ODRL-DUTY-{idx + 1:03d}"

        compiled_rules.append(
            ExecutableRule(
                rule_id=rule_id,
                pack_id=pack_id,
                version="1.0.0",
                legislative_source=f"W3C ODRL 2.2 Agreement {policy_uid} ({duty_uid})",
                semantic_hash=sem_hash,
                verbatim_source_text=verbatim,
                expression=expr,
                fields_evaluated=eval_fields or ("_context_verified",),
                verdict_on_fail=Verdict.HARD_STOP,
                verdict_on_pass=Verdict.PASS,
                plain_english_description=f"Enforce post-transfer ODRL duty {duty_uid}",
                non_conformance_message=f"ODRL duty breach on {duty_uid}: required constraint ({expr}) evaluated to False.",
                bound_processes=(process_urn,),
                odrl_policy_uid=policy_uid,
                odrl_rule_type="Duty",
            )
        )

    # 2. Process prohibitions
    prohibitions = odrl_policy.get("prohibition", [])
    for idx, prohib in enumerate(prohibitions):
        prohib_uid = str(prohib.get("uid") or f"{policy_uid}#prohibition-{idx + 1}")
        constraints = prohib.get("constraint", []) + prohib.get("refinement", [])
        expr, eval_fields = _compile_constraints(constraints, invert_for_prohibition=True)
        verbatim = json.dumps(prohib, sort_keys=True, separators=(",", ":"))
        sem_hash = compute_semantic_hash(verbatim)
        rule_id = f"ODRL-PROHIB-{idx + 1:03d}"

        compiled_rules.append(
            ExecutableRule(
                rule_id=rule_id,
                pack_id=pack_id,
                version="1.0.0",
                legislative_source=f"W3C ODRL 2.2 Prohibition {policy_uid} ({prohib_uid})",
                semantic_hash=sem_hash,
                verbatim_source_text=verbatim,
                expression=expr,
                fields_evaluated=eval_fields or ("_context_verified",),
                verdict_on_fail=Verdict.HARD_STOP,
                verdict_on_pass=Verdict.PASS,
                plain_english_description=f"Enforce ODRL prohibition {prohib_uid}",
                non_conformance_message=f"ODRL prohibition violated on {prohib_uid}: prohibited condition triggered.",
                bound_processes=(process_urn,),
                odrl_policy_uid=policy_uid,
                odrl_rule_type="Prohibition",
            )
        )

    # 3. Process permissions with duties or constraints
    permissions = odrl_policy.get("permission", [])
    for idx, perm in enumerate(permissions):
        perm_duties = perm.get("duty", [])
        perm_constraints = perm.get("constraint", [])
        for d_idx, duty in enumerate(perm_duties):
            duty_uid = str(duty.get("uid") or f"{policy_uid}#perm-{idx + 1}-duty-{d_idx + 1}")
            constraints = duty.get("constraint", []) + duty.get("refinement", [])
            if isinstance(duty.get("action"), dict):
                constraints = constraints + duty["action"].get("refinement", [])
            expr, eval_fields = _compile_constraints(constraints, invert_for_prohibition=False)
            verbatim = json.dumps(duty, sort_keys=True, separators=(",", ":"))
            sem_hash = compute_semantic_hash(verbatim)
            rule_id = f"ODRL-PERM-DUTY-{idx + 1:02d}-{d_idx + 1:02d}"

            compiled_rules.append(
                ExecutableRule(
                    rule_id=rule_id,
                    pack_id=pack_id,
                    version="1.0.0",
                    legislative_source=f"W3C ODRL 2.2 Permission Duty {policy_uid} ({duty_uid})",
                    semantic_hash=sem_hash,
                    verbatim_source_text=verbatim,
                    expression=expr,
                    fields_evaluated=eval_fields or ("_context_verified",),
                    verdict_on_fail=Verdict.HARD_STOP,
                    verdict_on_pass=Verdict.PASS,
                    plain_english_description=f"Enforce ODRL permission duty {duty_uid}",
                    non_conformance_message=f"ODRL permission duty breach on {duty_uid}: ({expr}) evaluated to False.",
                    bound_processes=(process_urn,),
                    odrl_policy_uid=policy_uid,
                    odrl_rule_type="Duty",
                )
            )

        if perm_constraints and not perm_duties:
            perm_uid = str(perm.get("uid") or f"{policy_uid}#perm-{idx + 1}")
            expr, eval_fields = _compile_constraints(perm_constraints, invert_for_prohibition=False)
            verbatim = json.dumps(perm, sort_keys=True, separators=(",", ":"))
            sem_hash = compute_semantic_hash(verbatim)
            rule_id = f"ODRL-PERM-{idx + 1:03d}"

            compiled_rules.append(
                ExecutableRule(
                    rule_id=rule_id,
                    pack_id=pack_id,
                    version="1.0.0",
                    legislative_source=f"W3C ODRL 2.2 Permission Constraint {policy_uid} ({perm_uid})",
                    semantic_hash=sem_hash,
                    verbatim_source_text=verbatim,
                    expression=expr,
                    fields_evaluated=eval_fields or ("_context_verified",),
                    verdict_on_fail=Verdict.HARD_STOP,
                    verdict_on_pass=Verdict.PASS,
                    plain_english_description=f"Enforce ODRL permission constraint {perm_uid}",
                    non_conformance_message=f"ODRL permission constraint breach on {perm_uid}: ({expr}) evaluated to False.",
                    bound_processes=(process_urn,),
                    odrl_policy_uid=policy_uid,
                    odrl_rule_type="Permission",
                )
            )

    if not compiled_rules:
        raise ValueError("ODRL policy contained no actionable obligation, prohibition, or constrained permission.")

    binding = ProcessBinding(
        process_urn=process_urn,
        bound_rules=tuple(r.rule_id for r in compiled_rules),
        correlation_id=eff_corr_id,
    )
    return tuple(compiled_rules), binding


def bind_drp_delegation_evidence(
    delegation_evidence: Dict[str, Any],
    process_urn: str,
    pack_id: str = "ODGS-ECLIPSE-DRP",
    correlation_id: Optional[str] = None,
) -> Tuple[Tuple[ExecutableRule, ...], ProcessBinding]:
    """Bind an Eclipse Dataspace Rights Profile (DRP) delegationEvidence object to ODGS.

    Enforces DRP's mandatory breach clause: if `target.environment.licenses` or rule
    effect conditions are not satisfied at runtime, the `accessSubject` MUST NOT
    process the resource (`HARD_STOP`).
    """
    evidence_root = delegation_evidence.get("delegationEvidence", delegation_evidence)
    policy_issuer = evidence_root.get("policyIssuer", "UNKNOWN_ISSUER")
    access_subject = evidence_root.get("target", {}).get("accessSubject", "UNKNOWN_SUBJECT")
    policy_sets = evidence_root.get("policySets", [])

    compiled_rules: List[ExecutableRule] = []
    all_licenses: List[str] = []

    for ps_idx, ps in enumerate(policy_sets):
        licenses = ps.get("target", {}).get("environment", {}).get("licenses", [])
        for lic in licenses:
            if lic not in all_licenses:
                all_licenses.append(lic)

        policies = ps.get("policies", [])
        for p_idx, pol in enumerate(policies):
            res_type = pol.get("target", {}).get("resource", {}).get("type", "Resource")
            rules = pol.get("rules", [])
            effect = rules[0].get("effect", "Permit") if rules else "Permit"
            verbatim = json.dumps(pol, sort_keys=True, separators=(",", ":"))
            sem_hash = compute_semantic_hash(verbatim)
            rule_id = f"DRP-PS{ps_idx + 1}-POL{p_idx + 1}"

            if effect == "Permit" and licenses:
                lic_checks = [f"'{lic}' in active_licenses" for lic in licenses]
                expr = " and ".join(lic_checks) + " and resource_permitted == True"
                eval_fields = ("active_licenses", "resource_permitted")
            elif effect == "Deny":
                expr = "resource_permitted == False"
                eval_fields = ("resource_permitted",)
            else:
                expr = "resource_permitted == True"
                eval_fields = ("resource_permitted",)

            compiled_rules.append(
                ExecutableRule(
                    rule_id=rule_id,
                    pack_id=pack_id,
                    version="1.0.0",
                    legislative_source=f"Eclipse DRP delegationEvidence ({policy_issuer} -> {access_subject}, {res_type})",
                    semantic_hash=sem_hash,
                    verbatim_source_text=verbatim,
                    expression=expr,
                    fields_evaluated=eval_fields,
                    verdict_on_fail=Verdict.HARD_STOP,
                    verdict_on_pass=Verdict.PASS,
                    plain_english_description=(
                        f"Enforce Eclipse DRP delegation policy for {res_type} "
                        f"under licenses {licenses}"
                    ),
                    non_conformance_message=(
                        f"Eclipse DRP breach: accessSubject '{access_subject}' MUST NOT "
                        f"process resource '{res_type}' without required licenses {licenses}."
                    ),
                    bound_processes=(process_urn,),
                    odrl_policy_uid=f"urn:eclipse:drp:{policy_issuer}:{access_subject}",
                    odrl_rule_type=f"DRP-{effect}",
                )
            )

    if not compiled_rules:
        raise ValueError("delegationEvidence contained no policySets/policies to bind.")

    binding = ProcessBinding(
        process_urn=process_urn,
        bound_rules=tuple(r.rule_id for r in compiled_rules),
        correlation_id=correlation_id or f"urn:eclipse:drp:{policy_issuer}:{access_subject}",
        delegation_license_ref=",".join(all_licenses) if all_licenses else None,
    )
    return tuple(compiled_rules), binding
