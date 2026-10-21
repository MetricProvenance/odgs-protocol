"""ODGS Dataspace Runtime Enforcement & Semantic Certification Bridge.

Vendor-neutral reference integration connecting the Open Data Governance Standard (ODGS)
runtime enforcement model to:
- W3C ODRL 2.2 & Gaia-X ODRL-VC Profile
- Eclipse Dataspace Working Group (CAP v2.2.1, DRP, DSP, DCP)
- Gaia-X Data Transfer Agent (DTA) Phase 6 Obligation Verification
- IDSA Rulebook (2026-3) Decentralized Observability
- W3C PROV-O & NIST OSCAL v1.1.2
"""

from odgs.dataspace.models import (
    AuthoritativeSource,
    ConformanceLevel,
    DtaVerificationResult,
    ExecutableRule,
    ProcessBinding,
    SemanticCertificate,
    Verdict,
)
from odgs.dataspace.odrl_binder import (
    bind_drp_delegation_evidence,
    bind_odrl_policy,
    compute_semantic_hash,
)
from odgs.dataspace.runtime_pep import (
    AdministrativeRecusalError,
    DataspaceRuntimePEP,
    SoftStopOverrideRequiredError,
)
from odgs.dataspace.cap_exporter import (
    export_cap_cred_evidence,
    export_cap_declaration_vc,
    export_nist_oscal_finding,
    export_w3c_prov_o,
)
from odgs.dataspace.dta_verifier import (
    sign_s_cert_ed25519,
    verify_dta_post_transfer_obligation,
)

__version__ = "0.1.0"

__all__ = [
    "AuthoritativeSource",
    "ConformanceLevel",
    "DtaVerificationResult",
    "ExecutableRule",
    "ProcessBinding",
    "SemanticCertificate",
    "Verdict",
    "bind_drp_delegation_evidence",
    "bind_odrl_policy",
    "compute_semantic_hash",
    "AdministrativeRecusalError",
    "DataspaceRuntimePEP",
    "SoftStopOverrideRequiredError",
    "export_cap_cred_evidence",
    "export_cap_declaration_vc",
    "export_nist_oscal_finding",
    "export_w3c_prov_o",
    "sign_s_cert_ed25519",
    "verify_dta_post_transfer_obligation",
]
