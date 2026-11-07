"""Eclipse Data Plane Signaling & DSP Transfer Lifecycle Bridge for ODGS.

Implements consumer-side Data Plane Signaling registration/preparation (`DataFlowPrepareMessage` /
`DataFlowStartMessage`), control-plane DSP agreement retrieval (`GET /transfers/:dataFlowId/agreement`),
DSP violation signaling (`dspace:TransferSuspensionMessage` / `dspace:TransferTerminationMessage`),
and explicit ODRL constraint observability classification under ODGS's first-party consumer
audit record trust model.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Tuple
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict

from odgs.dataspace.models import (
    ExecutableRule,
    ProcessBinding,
    SemanticCertificate,
    Verdict,
)
from odgs.dataspace.odrl_binder import bind_dsp_contract_agreement
from odgs.dataspace.runtime_pep import (
    AdministrativeRecusalError,
    DataspaceRuntimePEP,
    SoftStopOverrideRequiredError,
)

TRUST_MODEL_CONSUMER_AUDIT_RECORD = "CONSUMER_FIRST_PARTY_AUDIT_RECORD"

_UNOBSERVABLE_USAGE_OPERANDS = frozenset(
    {
        "purpose",
        "elapsedtime",
        "datetime",
        "delayperiod",
        "count",
        "recipient",
        "event",
        " nextpolicy",
        "nextpolicy",
    }
)

_UNOBSERVABLE_BEHAVIORAL_ACTIONS = frozenset(
    {
        "distribute",
        "share",
        "transfer",
        "delete",
        "uninstall",
        "sell",
        "lend",
        "give",
    }
)


class AgreementResolver(Protocol):
    """Protocol for retrieving negotiated DSP agreements from the consumer control plane."""

    def get_transfer_agreement(self, flow_id: str) -> Dict[str, Any]:
        """Retrieve the negotiated `odrl:Agreement` via `GET /transfers/:dataFlowId/agreement`."""
        ...


class ControlPlaneNotifier(Protocol):
    """Protocol for notifying the consumer control plane to suspend or terminate a DSP transfer."""

    def notify_transfer_event(self, flow_id: str, dsp_message: Dict[str, Any]) -> None:
        """Deliver a `dspace:TransferSuspensionMessage` or `dspace:TransferTerminationMessage`."""
        ...


class ConstraintObservabilityReport(BaseModel):
    """Explicit classification of payload-observable vs. unobservable ODRL usage constraints."""

    model_config = ConfigDict(frozen=True)

    policy_uid: str
    trust_model: str = TRUST_MODEL_CONSUMER_AUDIT_RECORD
    observable_payload_operands: Tuple[str, ...]
    unobservable_usage_constraints: Tuple[str, ...]
    fully_observable_in_payload: bool


class PreparedDataFlow(BaseModel):
    """Immutable state for a prepared Data Plane Signaling flow."""

    model_config = ConfigDict(frozen=True)

    data_flow_id: str
    agreement_id: str
    provider_pid: Optional[str] = None
    process_urn: str
    rules: Tuple[ExecutableRule, ...]
    binding: ProcessBinding
    observability_report: ConstraintObservabilityReport


class FlowEvaluationResult(BaseModel):
    """Immutable outcome of evaluating a payload on a prepared consumer data-plane flow."""

    model_config = ConfigDict(frozen=True)

    data_flow_id: str
    agreement_id: str
    verdict: Verdict
    s_cert: SemanticCertificate
    trust_model: str = TRUST_MODEL_CONSUMER_AUDIT_RECORD
    dsp_control_message: Optional[Dict[str, Any]] = None
    observability_report: ConstraintObservabilityReport


def build_agreement_retrieval_path(data_flow_id: str) -> str:
    """Build the canonical consumer control-plane endpoint `GET /transfers/:dataFlowId/agreement`."""
    cleaned = data_flow_id.strip()
    if not cleaned or "/" in cleaned or ".." in cleaned:
        raise ValueError(f"Invalid dataFlowId for agreement retrieval: {data_flow_id!r}")
    encoded = quote(cleaned, safe=":-_.")
    return f"/transfers/{encoded}/agreement"


def _strip_prefix(term: str) -> str:
    cleaned = term.strip()
    if ":" in cleaned:
        cleaned = cleaned.split(":")[-1]
    return cleaned.lower()


def inspect_odrl_constraint_observability(
    odrl_policy: Dict[str, Any],
) -> ConstraintObservabilityReport:
    """Classify ODRL rules into payload-observable checks vs. unobservable downstream usage obligations.

    Pre-processing payload inspection can verify structural, value-range, or aggregation fields
    (e.g., `aggregation_household_count >= 50`), whereas behavioral constraints on downstream use
    (such as `purpose`, `retention` / `elapsedTime`, or `distribute` / onward sharing) cannot be
    observed from a payload prior to processing.
    """
    agreement = (
        odrl_policy.get("dspace:agreement")
        or odrl_policy.get("agreement")
        or odrl_policy
    )
    policy_uid = str(
        agreement.get("@id")
        or agreement.get("odrl:uid")
        or agreement.get("uid")
        or "urn:odrl:policy:unnamed"
    )

    observable: List[str] = []
    unobservable: List[str] = []

    rule_lists: List[Dict[str, Any]] = []
    for key in (
        "permission",
        "odrl:permission",
        "prohibition",
        "odrl:prohibition",
        "obligation",
        "odrl:obligation",
        "duty",
        "odrl:duty",
    ):
        items = agreement.get(key, [])
        if isinstance(items, list):
            rule_lists.extend(i for i in items if isinstance(i, dict))

    for rule in rule_lists:
        rule_uid = str(
            rule.get("uid") or rule.get("odrl:uid") or rule.get("@id") or "unnamed-rule"
        )
        raw_action = rule.get("action") or rule.get("odrl:action")
        action_name = ""
        if isinstance(raw_action, str):
            action_name = raw_action
        elif isinstance(raw_action, dict):
            action_name = str(
                raw_action.get("odrl:value") or raw_action.get("@id") or ""
            )

        if action_name and _strip_prefix(action_name) in _UNOBSERVABLE_BEHAVIORAL_ACTIONS:
            unobservable.append(f"{rule_uid}:action={action_name}")

        constraints: List[Dict[str, Any]] = []
        for c_key in ("constraint", "odrl:constraint", "refinement", "odrl:refinement"):
            c_items = rule.get(c_key, [])
            if isinstance(c_items, list):
                constraints.extend(c for c in c_items if isinstance(c, dict))

        for c in constraints:
            left_raw = str(
                c.get("leftOperand")
                or c.get("odrl:leftOperand")
                or c.get("ovc:leftOperand")
                or ""
            )
            if not left_raw:
                continue
            norm_left = _strip_prefix(left_raw)
            if norm_left in _UNOBSERVABLE_USAGE_OPERANDS:
                unobservable.append(f"{rule_uid}:operand={left_raw}")
            else:
                clean_field = left_raw.split(":")[-1].replace(".", "_").replace("-", "_")
                if clean_field not in observable:
                    observable.append(clean_field)

    return ConstraintObservabilityReport(
        policy_uid=policy_uid,
        trust_model=TRUST_MODEL_CONSUMER_AUDIT_RECORD,
        observable_payload_operands=tuple(observable),
        unobservable_usage_constraints=tuple(unobservable),
        fully_observable_in_payload=(len(unobservable) == 0 and len(observable) > 0),
    )


def build_dsp_transfer_termination_message(
    consumer_pid: str,
    provider_pid: Optional[str],
    s_cert: SemanticCertificate,
    reason: str,
    code: str = "ODGS_HARD_STOP",
) -> Dict[str, Any]:
    """Build an Eclipse DSP (`ISO/IEC DIS 26450`) `dspace:TransferTerminationMessage`."""
    msg: Dict[str, Any] = {
        "@context": "https://w3id.org/dspace/2025/1/context.jsonld",
        "@type": "dspace:TransferTerminationMessage",
        "dspace:consumerPid": consumer_pid,
        "dspace:code": code,
        "dspace:reason": [
            reason,
            f"odgs:sCertEventId={s_cert.event_id}",
            f"odgs:evidenceDigest=sha256-{s_cert.compute_evidence_digest()}",
        ],
    }
    if provider_pid:
        msg["dspace:providerPid"] = provider_pid
    return msg


def build_dsp_transfer_suspension_message(
    consumer_pid: str,
    provider_pid: Optional[str],
    s_cert: SemanticCertificate,
    reason: str,
    code: str = "ODGS_SOFT_STOP",
) -> Dict[str, Any]:
    """Build an Eclipse DSP (`ISO/IEC DIS 26450`) `dspace:TransferSuspensionMessage`."""
    msg: Dict[str, Any] = {
        "@context": "https://w3id.org/dspace/2025/1/context.jsonld",
        "@type": "dspace:TransferSuspensionMessage",
        "dspace:consumerPid": consumer_pid,
        "dspace:code": code,
        "dspace:reason": [
            reason,
            f"odgs:sCertEventId={s_cert.event_id}",
            f"odgs:evidenceDigest=sha256-{s_cert.compute_evidence_digest()}",
        ],
    }
    if provider_pid:
        msg["dspace:providerPid"] = provider_pid
    return msg


class DataPlaneSignalingBridge:
    """Consumer data-plane bridge integrating Eclipse Data Plane Signaling and DSP lifecycle events."""

    def __init__(
        self,
        agreement_resolver: AgreementResolver,
        control_plane_notifier: Optional[ControlPlaneNotifier] = None,
        system_id: Optional[str] = None,
    ) -> None:
        self._agreement_resolver = agreement_resolver
        self._control_plane_notifier = control_plane_notifier
        self._system_id = system_id
        self._flows: Dict[str, PreparedDataFlow] = {}

    def prepare_flow(
        self,
        signaling_message: Dict[str, Any],
        process_urn: str,
    ) -> Dict[str, Any]:
        """Handle `DataFlowPrepareMessage` or `DataFlowStartMessage` from the consumer control plane."""
        msg_type = str(
            signaling_message.get("@type") or signaling_message.get("type") or ""
        )
        if msg_type not in (
            "DataFlowPrepareMessage",
            "dps:DataFlowPrepareMessage",
            "DataFlowStartMessage",
            "dps:DataFlowStartMessage",
        ):
            raise ValueError(
                f"Unsupported Data Plane Signaling message type: {msg_type!r}"
            )

        data_flow_id = str(
            signaling_message.get("processId")
            or signaling_message.get("dps:processId")
            or signaling_message.get("dataFlowId")
            or signaling_message.get("dps:dataFlowId")
            or ""
        )
        agreement_id = str(
            signaling_message.get("agreementId")
            or signaling_message.get("dps:agreementId")
            or ""
        )
        if not data_flow_id or not agreement_id:
            raise ValueError(
                "Data Plane Signaling message must include `processId`/`dataFlowId` and `agreementId`."
            )

        provider_pid_raw = signaling_message.get("providerPid") or signaling_message.get(
            "dspace:providerPid"
        )
        provider_pid = str(provider_pid_raw) if provider_pid_raw else None

        agreement = self._agreement_resolver.get_transfer_agreement(data_flow_id)
        observability = inspect_odrl_constraint_observability(agreement)

        synthetic_transfer_msg: Dict[str, Any] = {
            "dspace:consumerPid": data_flow_id,
            "dspace:agreementId": agreement_id,
        }
        if provider_pid:
            synthetic_transfer_msg["dspace:providerPid"] = provider_pid

        rules, binding = bind_dsp_contract_agreement(
            dsp_agreement_message=agreement,
            process_urn=process_urn,
            transfer_message=synthetic_transfer_msg,
        )

        prepared = PreparedDataFlow(
            data_flow_id=data_flow_id,
            agreement_id=agreement_id,
            provider_pid=provider_pid,
            process_urn=process_urn,
            rules=rules,
            binding=binding,
            observability_report=observability,
        )
        self._flows = {**self._flows, data_flow_id: prepared}

        target_state = (
            "PREPARED" if "Prepare" in msg_type else "STARTED"
        )
        return {
            "@context": "https://w3id.org/dspace/2025/1/dps/context.jsonld",
            "@type": "DataFlowResponseMessage",
            "state": target_state,
        }

    def evaluate_flow(
        self,
        data_flow_id: str,
        payload: Dict[str, Any],
        override_token: Optional[str] = None,
    ) -> FlowEvaluationResult:
        """Evaluate a flow payload and emit DSP suspension/termination messages on violation."""
        if data_flow_id not in self._flows:
            raise KeyError(f"Data flow '{data_flow_id}' has not been prepared.")

        flow = self._flows[data_flow_id]
        pep = DataspaceRuntimePEP(
            rules=flow.rules,
            bindings=[flow.binding],
            system_id=self._system_id,
        )

        try:
            s_cert = pep.evaluate(
                process_urn=flow.process_urn,
                payload=payload,
                override_token=override_token,
            )
            return FlowEvaluationResult(
                data_flow_id=flow.data_flow_id,
                agreement_id=flow.agreement_id,
                verdict=s_cert.verdict,
                s_cert=s_cert,
                trust_model=TRUST_MODEL_CONSUMER_AUDIT_RECORD,
                dsp_control_message=None,
                observability_report=flow.observability_report,
            )
        except AdministrativeRecusalError as exc:
            term_msg = build_dsp_transfer_termination_message(
                consumer_pid=flow.data_flow_id,
                provider_pid=flow.provider_pid,
                s_cert=exc.s_cert,
                reason=str(exc),
            )
            if self._control_plane_notifier is not None:
                self._control_plane_notifier.notify_transfer_event(
                    flow.data_flow_id, term_msg
                )
            return FlowEvaluationResult(
                data_flow_id=flow.data_flow_id,
                agreement_id=flow.agreement_id,
                verdict=Verdict.HARD_STOP,
                s_cert=exc.s_cert,
                trust_model=TRUST_MODEL_CONSUMER_AUDIT_RECORD,
                dsp_control_message=term_msg,
                observability_report=flow.observability_report,
            )
        except SoftStopOverrideRequiredError as exc:
            susp_msg = build_dsp_transfer_suspension_message(
                consumer_pid=flow.data_flow_id,
                provider_pid=flow.provider_pid,
                s_cert=exc.s_cert,
                reason=str(exc),
            )
            if self._control_plane_notifier is not None:
                self._control_plane_notifier.notify_transfer_event(
                    flow.data_flow_id, susp_msg
                )
            return FlowEvaluationResult(
                data_flow_id=flow.data_flow_id,
                agreement_id=flow.agreement_id,
                verdict=Verdict.SOFT_STOP,
                s_cert=exc.s_cert,
                trust_model=TRUST_MODEL_CONSUMER_AUDIT_RECORD,
                dsp_control_message=susp_msg,
                observability_report=flow.observability_report,
            )
