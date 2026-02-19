# Changelog

All notable changes to the Open Data Governance Standard (ODGS) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
