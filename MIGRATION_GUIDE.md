# ODGS v5.0.0 Migration Guide

**WARNING:** This release contains **BREAKING CHANGES** from v4.1.0 for users evaluating W3C JSON-LD rule structures.
Do not deploy v5.0.0 without reading this guide. ODGS is now a **Polymorphic Validation Engine**.

---

## 1. Polymorphic Rule Ingestion (The 5-Plane Architecture)

Version 5.0.0 fully realizes the 5-Plane Architecture by natively supporting two distinct execution models simultaneously without requiring separate engine processes.

### Legacy v4 Schema Compatibility 
If you are using the ODGS Enterprise Bridges (`odgs-databricks-bridge`, `odgs-snowflake-bridge`, `odgs-collibra-bridge`), absolutely **no changes** are required to your downstream ingestion. The v5 engine is 100% backwards compatible with the v4 schema (`https://metricprovenance.com/schemas/odgs/v4`). Standard `ProcessBlockedException` continues to be raised for standard `HARD_STOP` conditions.

### The Legislative W3C JSON-LD Tier
If you are integrating TNO FLINT, Sovereign Packs, or any rule claiming the `https://metricprovenance.com/schemas/odgs/v5` `@context` OR the `Legislative Compliance` domain:
* **The New Hard Stop:** The engine will now escalate `HARD_STOP` conditions and violently halt the pipeline by raising an `AdministrativeRecusal` exception instead of a standard `ProcessBlockedException`. You must update your try/catch blocks if you are absorbing these errors natively.
* **Audit Metadata:** Legislative halts now strictly enforce the inclusion of `provenance_metadata` and track `attempted_payload_drift` in the final JSON audit log seal.

---

# ODGS v4.0.0 Migration Guide

**WARNING:** This release contains **BREAKING CHANGES** from v3.3.0.
Do not deploy v4.0.0 without reading this guide. ODGS is now a **Universal Validation Engine**.

---


## 🛑 Strict Deprecation Notice (Legacy v3.3 Users)

Version 3.3 and earlier were designed as a strict "RegTech Tool" specifically for Sovereign Law enforcement. These versions hardcoded restrictive terminology ("EU AI Act", "Law Packs") and assumed all URNs required cryptographic identity verification from the Quirkyswirl authority. 

**v3.3 is officially deprecated.** We strongly encourage all Data Engineering and Compliance teams to migrate to v4.0.0 to unlock the completely free, agnostic, local evaluation capabilities (the "Linux of Data Governance").

---

## 1. URN Namespace Routing

The most significant change in v4.0.0 is the introduction of a dynamic `NamespaceRouter`. Your engine's behavior now fundamentally shifts depending on the prefix of the URN it evaluates.

### The Two Namespaces

1.  **`urn:odgs:custom:*` (The Free, Local Tier)**
    *   Use this for your internal data quality rules, B2B SLAs, and SOC2 checks.
    *   **Routing:** The engine attempts to load these directly from `./schemas/custom/` in your local active directory.
    *   **Enforcement:** It does **not** check for JWKS cryptographic signatures. It executes silently and locally for free.

2.  **`urn:odgs:sov:*` (The Premium, Sovereign Tier)**
    *   Use this for EU AI Act, GDPR, FIBO, and DORA compliance. 
    *   **Routing:** The engine enforces the *Sovereign Handshake* and strictly loads statutory packs from enterprise mounts at `/etc/odgs/law-packs/`.
    *   **Enforcement:** It mathematically verifies the cryptographic signature of the external JSON file before executing it. If it fails, the pipeline is hard-stopped with a `428 Precondition Required`.

### Migration Action
Review all instances of `interceptor.intercept("urn:...")`. If you were hacking v3.3 to evaluate internal data quality rules, change your URN prefix to `urn:odgs:custom:`. 

---

## 2. Strict JSON Schema Validation

In v4.0.0, we introduced a Universal Verification Check. To protect internal corporate pipelines from crashing due to malformed logic, the engine now enforces strict **JSON Schema Draft-7** validation before loading any configuration into memory.

### Migration Action
Every custom JSON file you place in `./schemas/custom/` (e.g., your custom rules, metrics, or contexts) **must** now include a `$schema` property pointing to the relevant validation schemas.

**Example: A Valid Custom Rule (v4.0.0)**
```json
{
  "$schema": "https://raw.githubusercontent.com/MetricProvenance/odgs-protocol/main/1_NORMATIVE_SPECIFICATION/schemas/validation/rule.schema.json",
  "urn": "urn:odgs:custom:data-quality:no-nulls",
  "name": "Strict non-null check for internal AML reporting",
  "logic_expression": "transaction_value > 0",
  "threshold_type": "boolean",
  "threshold_value": "True",
  "action_on_fail": "HARD_STOP"
}
```

If your JSON does not conform to the schema (e.g., passing an integer when `threshold_value` expects a string), the payload will fail the "Validation Gate" and throw a `SchemaValidationException` detailing exactly which line is formatted incorrectly.

---

## 3. Backwards Compatibility (`odgs migrate v4`)

If you are upgrading an existing v3.3 Sovereign Node project, you can use the built-in CLI migration utility to safely transition your existing integer/string maps into the new unified Namespace Architecture.

```bash
# Analyze your v3.3 environment and prepare the migration matrix
odgs migrate v4 --dry-run

# Commit the migration changes to your active directory
odgs migrate v4 --execute
```

## Rollback
If the migration fails or breaks downstream systems:
1.  Restore from your git commit backup.
2.  Pin your dependency to the legacy version: `pip install "odgs==3.3.0"`. Note that v3.3 will not receive any further non-critical security updates.
