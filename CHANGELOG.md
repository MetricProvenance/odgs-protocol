# Changelog

All notable changes to the Open Data Governance Standard (ODGS) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v5.2.0] - 2026-03-23

### ✨ Added

- **Tiered Governance Architecture (Minimalist Execution):** The `odgs init` CLI command now accepts a `--tier` flag. Using `odgs init <name> --tier minimalist` will scaffold a streamlined 3-file setup (`standard_metrics.json`, `standard_data_rules.json`, `runtime_config.json`) for startups and fast-moving teams.
- **Graceful File Degradation:** The AI Safety Validator (`validate`) and Deterministic Hashing Engine (`hash`) now treat non-core legislative files as `OPTIONAL`, preventing false-positive failures in minimalist configurations.
- **Deployment Status Telemetry:** The CLI validation output and audit logs now surface the deployment's certification status, giving teams clear visibility into whether their active rule packs are cryptographically signed or running as standard local deployments.
- **Dynamic Version Mapping:** The CLI `version` and `init` commands now dynamically extract the installed package version natively via `importlib.metadata` to ensure standard sync.

### 🔧 Fixed

- **Validation Path Mismatch:** Corrected bug where `init` generated `legislative/` but `validate` searched the normative `1_NORMATIVE_SPECIFICATION/...` path. Dual-path resolution is now implemented.
- **Noisy Telemetry:** Suppressed `GitPython` optional dependency warnings by migrating `print` statements to standardized python `logging` (`logger.warning`), preserving cleaner CLI output.
- **Conflicting Terminal Reports:** Aligned structural checks text to `Schema Validation Passed!` to avoid confusion with `Registry Verification Failed` cryptographic hash failures.

---

## [v5.1.0] - 2026-03-19

### ✨ Added

- **Complete S-Cert audit fields:** The audit log now emits all required fields at the top level of
  every S-Cert entry:
  - `rule_id` — identifier of the applied rule(s)
  - `semantic_hash` — SHA-256 of the rule source text (`"UNATTESTED"` if not declared in rule)
  - `verdict` — `"APPROVED"` / `"BLOCKED"`
  - `system_id` — evaluating system instance (set via `ODGS_SYSTEM_ID` env var; falls back to hostname)
  - `payload_hash` — SHA-256 of the canonical input JSON body (zero-knowledge; raw payload never logged)

- **`LOG_ONLY` verdict type:** Rules can now be declared with `"severity": "LOG_ONLY"`. On failure,
  the event is recorded in `log_only_events` in the audit entry but processing is **not blocked**.
  Use for monitoring-mode rollouts before switching to `HARD_STOP`.

- **Rule lifecycle — temporal bounds:** Rules may declare `effective_from` and/or `effective_to`
  (ISO 8601 date strings). The enforcement engine silently skips rules outside their validity window.
  Pre-deploy rules ahead of regulatory go-live dates, or sunset expired rules automatically.

- **9 new unit tests** covering all v5.1.0 features in `tests/test_v5_1_0_features.py`.

### 🔧 Fixed

- **Python 3.14 forward compatibility:** Fixed last remaining `datetime.datetime.utcnow()` call
  in `git_log_adapter.py` (line 54). All timestamp generation now uses timezone-aware
  `datetime.datetime.now(datetime.timezone.utc)`.

### ⚠️ Migration Notes

All changes are **additive** — existing configurations continue to work without modification.

- New S-Cert fields are appended to the existing structure; no existing fields removed.
- `"severity": "LOG_ONLY"` is a new option; existing `HARD_STOP` and `WARNING` severities unchanged.
- Rules without `effective_from`/`effective_to` are evaluated as before (always active).
- `ODGS_SYSTEM_ID` env var is optional; falls back to `socket.gethostname()` if not set.

---

## [v5.0.1] - 2026-03-16


### 🔧 Fixed

- **Audit Log Compatibility:** Re-added `s_cert_status` field to the `OdgsInterceptor` audit entry.
  `s_cert_status` was removed during the v4→v5 migration when `certification_status` was introduced
  as the canonical field. However, downstream commercial consumers (audit log parsers, S-Cert registry
  integration tests, sovereign audit dashboards) still read `s_cert_status`. Both fields now coexist:
  - `certification_status`: `"CERTIFIED"` / `"LOCAL_ONLY"` — the v5 canonical form
  - `s_cert_status`: `"ISSUED_AND_VERIFIED"` / `"NOT_ISSUED"` — backward-compat alias

- **Audit Log Compatibility:** Re-added `cryptographic_attestation` (singular dict) alongside the
  existing `cryptographic_attestations` (list). The singular form exposes the first attestation for
  consumers that pre-date the v5 multi-attestation model.

- **Python 3.14 Forward Compatibility:** Replaced deprecated `datetime.datetime.utcnow()` with
  `datetime.datetime.now(datetime.timezone.utc)` throughout the interceptor.
  `utcnow()` is scheduled for removal in Python 3.14. 

  > ⚠️ **Timestamp format change:** Audit log `timestamp` field changes from `"2026-03-16T08:00:00Z"`
  > (naive UTC with trailing `Z`) to `"2026-03-16T08:00:00+00:00"` (timezone-aware ISO 8601).
  > Both formats represent the same moment. Update any audit log consumers that match the literal `Z` suffix.

---

## [v5.0.0] - 2026-03-14

### 🚀 Added
- **Polymorphic Ingestion Engine:** The Universal Interceptor now natively handles both legacy v4 table/column metrics and v5 W3C JSON-LD strict semantic ontologies simultaneously.
- **Administrative Recusal (`HARD_STOP`):** Regulatory failures evaluating W3C JSON-LD `EnforcementRule` schemas now raise a distinct `AdministrativeRecusal` exception to ensure strict "Black Box" liability indemnification.
- **Audit Lineage Enhancements:** Appended `provenance_metadata` (containing semantic hashes) and `attempted_payload_drift` to the cryptographic JSON audit log when v5 legislative rules trigger.

### 🛡️ Security & Enterprise
- **Telemetry Routing:** Injected "CLI Billboards" into initialization sequences to alert users proceeding without a Sovereign CA cryptographic signature.
- **Backwards Compatibility:** Databricks, Snowflake, and Collibra bridges remain fully supported out of the box emitting backwards-compatible v4 rules.
- **Sovereign FLINT Bridge:** Officially decoupled `odgs-flint-bridge` to translate Dutch Administrative Law (Regels als Code) into strict v5 syntax.

## [v4.0.1] - 2026-03-07

### 🚀 Added
- **Audit Transparency:** Added `certification_status` field to all execution audit log entries. Sovereign packs with valid cryptographic attestation report `CERTIFIED`; internal custom rules report `LOCAL_ONLY`.
- **Platform Bridges Ecosystem:** Announced bridge integrations for Collibra Business Glossary, Databricks Unity Catalog, and Snowflake Data Dictionary. Bridges transform passive data dictionaries into active ODGS runtime enforcement schemas.

### 📦 Packaging
- **Reduced sdist size:** Excluded architecture screenshots and research documents from PyPI source distribution (3.2 MB → ~200 KB).
- **npm cleanup:** Added `.DS_Store` to `.npmignore`.

## [v4.0.0] - 2026-03-02

### 🚀 Added
- **Universal Validation Engine:** Transformed the core enforcement engine to be completely headless and agnostic, functioning as a "Linux of Data Governance" rather than a rigid RegTech tool.
- **Universal URN Routing:** Introduced strict namespace separation (`urn:odgs:custom:*` vs `urn:odgs:sov:*`) allowing developers to execute free-form Internal Governance policies seamlessly on the exact same engine as high-risk compliance checks.
- **Dynamic Extensibility:** Added `HarvesterFactory` (Bring Your Own Blueprints) and `AdapterRegistry` (Bring Your Own Integrations). Developers can now inject proprietary parsing or custom data sinks without altering the protocol's core standard.
- **Ontology Repositioning:** Re-positioned `ontology_graph.owl` as a "Semantic Bridge for Agentic AI," providing autonomous agents with formal, mathematically verifiable boundaries for business rules.

### 🔧 Changed
- **Decoupled Policy from Mechanism:** The `OdgsInterceptor` no longer requires strictly formatted "Law Packs" to run, avoiding "System of Record" lock-in and allowing pure "System of Mechanism" utility.
- **Documentation Overhaul:** Updated Architectural specification (`technical_annex.md`), `comparison_matrix.md`, and `eli5_guide.md` to cleanly reflect the Universal Primitive positioning.

## [v3.3.0] - 2026-02-19

### 🛡️ Security
- **Sovereign Handshake:** Cryptographic integrity verification of legislative artifacts before rule evaluation (Python + Node.js).
- **Node.js Security:** Replaced `new Function()` (eval vulnerability) with sandboxed `expr-eval` parser.
- **Bare Exception Handling:** Replaced all bare `except:` blocks with specific exception types (6 Python + 3 JS).

### 🚀 Added
- **Tri-Partite Binding:** Audit log entries now cryptographically bind Input Hash + Definition Hash + Configuration Hash (EU AI Act Article 12).
- **Integration Test Suite:** 11 end-to-end tests covering schema loading, handshake, rule evaluation (PASS/BLOCK), and audit generation.
- **GitHub Actions CI/CD:** 3-job pipeline (Python tests, Node.js tests, schema validation).
- **`py.typed` Marker:** PEP 561 compliance for downstream type checkers.
- **Type Hints:** Added to all remaining public API functions.

### 🔧 Changed
- **Rule Enforcement:** `logic_expression` added to 43/50 rules (86% enforceable, up from 15%).
- **Severity Levels:** All 50 rules now classified as `HARD_STOP`, `WARNING`, or `INFO`.
- **Context Bindings:** Expanded from 2 to 14 contexts with `effective_from`/`effective_until` temporal versioning.
- **Time-Travel Resolution:** `_resolve_by_date()` fully implemented in `resolver.py`.
- **Schema Validation:** JSON Schema meta-validation passes for all 122 items (72 metrics + 50 rules).

### 🐛 Fixed
- **AwB Harvester:** Namespace-agnostic XML parsing; corrected `lidnummer` → `lidnr` element name.
- **URN Resolver:** Regex now correctly handles multi-segment sovereign URNs (e.g., `urn:odgs:def:nl_gov:awb:art_1_3:v2024`).
- **API Start:** Factory imports guarded with try/except; API starts without `google-genai`.
- **Sovereign Brake:** Replaced hardcoded date with dynamic `datetime.utcnow()`.
- **Duplicate Model:** Removed duplicate `InterceptRequest` class in `api.py`.

### 📦 Packaging
- **Lean Dependencies:** Private dependencies (`streamlit`, `google-genai`, `pandas`) moved to optional extras (`pip install odgs[demo]`, `pip install odgs[ai]`).
- **Build Exclusions:** `ui/`, `factory/`, `audit_logs/` excluded from PyPI wheel via hatchling config.
- **PyPI Metadata:** Added license, author, classifiers, keywords, and project URLs.
- **npm Metadata:** Added author, license, repository, homepage, keywords, and engine requirements.

## [v3.2.0] - 2026-02-17

### 🚀 Added
- **Sovereign Harvester:** New CLI command `odgs harvest` to fetch authoritative definitions from external sources.
    - Added `nl_awb` blueprint for Dutch Administrative Law (XML).
    - Added `fibo` blueprint for Financial Industry Business Ontology (JSON-LD).
- **Time-Travel Resolver:** Implemented `src/odgs/core/resolver.py` to resolve URNs based on a specific legal date (`as_of_date`).
- **Sovereign Definition Schema:** New properties for `hierarchy` (Article/Paragraph) and `content.verbatim_text`.
- **Content Hashing:** All harvested definitions are now automatically signed with a SHA-256 `content_hash` for immutability.

### ⚠️ Changed
- **BREAKING:** ID Refactor. Transformed all integer-based Foreign Keys in Rules and Factors to URN strings.
    - `improvesDqDimensionIds` -> `related_dimension_urns`
    - `dqDimensionsImpactedDamaIds` -> `related_dimension_urns`
- **Ontology Graph:** Updated `ontology_graph.json` to include `IS_DEFINED_BY` and `WAS_DERIVED_FROM` edge types.
- **Metrics Schema:** Deprecated legacy `definition` string in favor of `sovereign_urn`.

### 🛡️ Security
- **Immutability:** Enforced SHA-256 hashing on `verbatim_text` during the harvest process to prevent Definition Drift.

## [v3.1.0] - 2026-02-16

### 🛡️ Security
- **Identity Standardization:** All 72 metrics and 50 rules migrated from integer IDs to URN format (`urn:odgs:metric:*`, `urn:odgs:rule:*`).
- **DAX Fix:** Corrected mismatched brackets in Net Profit Margin formula.

### 🔧 Changed
- **Import Path Fix:** Resolved inconsistency between `lib/interceptor.js` and `lib/index.js` import paths.

## [v3.0.0] - 2026-02-14

### 🚀 Added
- Initial public release of the Sovereign Sidecar architecture.
- 5-Plane Constitutional Stack (Governance → Legislative → Judiciary → Executive → Physical).
- Python Interceptor with `simpleeval`-based rule evaluation.
- Node.js Interceptor with cross-platform parity.
- Git-backed audit logging (Zero-Trust Sovereignty).
- 72 business metrics across 7 industry domains.
- 50 data governance rules with pseudocode logic.
- Ontology graph with typed semantic edges.
- CLI interface (`odgs init`, `odgs run`, `odgs migrate`).
