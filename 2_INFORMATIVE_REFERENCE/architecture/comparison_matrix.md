# ODGS Competitive Comparison Matrix

**Version:** 5.0.0
**Purpose:** Formal differentiation of ODGS from existing data governance frameworks.

---

## The Definition-Execution Gap

No existing framework binds **data to its legal definition** at runtime with cryptographic proof. This is the structural gap ODGS fills.

> Traditional tools answer: *"Is this data clean?"*
> ODGS answers: *"Is this data being interpreted using the correct legal definition — and can I prove it?"*

---

## Feature Comparison

| Capability | ODGS v5.0 | Great Expectations | dbt Tests | Soda Core | Open Lineage | Monte Carlo | W3C PROV |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Universal URN Routing** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Semantic Binding** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Constitutional Stack** (5-Plane) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Tri-Partite Audit** (3-hash binding) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Partial |
| **Sovereign Handshake** (integrity verification) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Fail-Closed Pattern** (Hard Stop) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Time-Travel Resolution** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Partial |
| **EU AI Act Alignment** (Art. 10 + 12) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Data Shape Validation | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Data Lineage Tracking | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Anomaly Detection (Statistical) | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Schema Drift Detection | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Vendor-Neutral Protocol | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Git-Backed Audit Log | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-Platform Runtime (Python + JS) | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

---

## Structural Differentiation

### What They Do vs. What ODGS Does

| Framework | Function | ODGS Equivalent | The Gap |
|---|---|---|---|
| **Great Expectations** | Validates data *shape* ("Is this column non-null?") | Validates data *meaning* ("Is this value interpreted using Rule 2027?") | Shape ≠ Meaning |
| **dbt Tests** | Checks referential integrity ("Does FK exist?") | Checks *semantic* integrity ("Does the FK's definition match its context?") | Reference ≠ Semantics |
| **Open Lineage** | Tracks data *movement* ("Where did the data come from?") | Tracks data *interpretation* ("Which legal definition was applied?") | Movement ≠ Interpretation |
| **W3C PROV** | Records provenance ("Who touched what?") | Records *constitutional provenance* ("Under which law was this processed?") | Agent ≠ Authority |
| **Monte Carlo** | Detects data *anomalies* ("This looks different") | Detects *semantic drift* ("The AI is using the wrong definition") | Statistical ≠ Legal |
| **Soda Core** | Validates data *quality* ("Is this within range?") | Validates data *sovereignty* ("Is this processed under the correct jurisdiction?") | Quality ≠ Sovereignty |

---

## The Tri-Partite Binding (Unique to ODGS)

No existing framework provides a cryptographic bond between all three elements of an AI decision:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT LOG ENTRY                           │
│                                                             │
│  1. Input Hash      SHA-256(payload)     → WHAT was processed│
│  2. Definition Hash SHA-256(legislation) → WHICH rule applied│
│  3. Config Hash     SHA-256(context)     → UNDER what context│
│                                                             │
│  Binding: {input}:{definition}:{config}                     │
│  → Proves the exact state at the moment of decision         │
└─────────────────────────────────────────────────────────────┘
```

This binding satisfies **EU AI Act Article 12** (Automatic Recording) and **ISO/IEC 42001 Control B.9** (Operational Control).

---

## When to Use ODGS vs. Alternatives

| If You Need... | Use | Why Not ODGS? |
|---|---|---|
| Statistical anomaly detection | Monte Carlo, Great Expectations | ODGS is deterministic, not statistical |
| Data lineage visualization | Open Lineage, Marquez | ODGS tracks *interpretation*, not *movement* |
| CI/CD data testing | dbt Tests, Soda Core | Use ODGS alongside dbt for *meaning* + *shape* |
| **Legal compliance proof** | **ODGS** | No alternative provides constitutional provenance |
| **AI Act audit trail** | **ODGS** | No alternative provides Tri-Partite Binding |
| **Semantic drift prevention** | **ODGS** | No alternative binds data to legal definitions |

---

## Normative References

- **EU AI Act (2024/1689):** Articles 10, 12
- **ISO/IEC 42001:2023:** Control B.7 (Data Management), B.9 (Operational Control)
- **NEN 381 525:** Data, Data Management, Cloud and Edge
- **DAMA DMBOK v2:** Data Quality Dimensions Framework

---
> **Require architectural clearance or SLA support for your organization?** [Consult the Metric Provenance Enterprise Portal](https://platform.metricprovenance.com).

[< Back to README](/README.md) | [Documentation Map →](index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)
