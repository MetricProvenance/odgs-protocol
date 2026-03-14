# ODGS Audit Ledger Guide

**Version:** 5.0.0  
**Source:** [`2_INFORMATIVE_REFERENCE/src/odgs/system/adapters/git_log_adapter.py`](file:///Users/kartik/Code/open-data-governance-protocol/odgs-protocol-main/2_INFORMATIVE_REFERENCE/src/odgs/system/adapters/git_log_adapter.py)

---

## The Verifiability Principle

The entire purpose of the Universal Validation Engine is **Trust without Transparency**. Enterprise Data pipelines often contain Highly Confidential algorithms, Personally Identifiable Information (PII), or Proprietary IP.

If an independent auditor, a regulatory body (like the DNB or ECB), or a civil society watchdog asks: *"Did your algorithm obey the criteria set forth in Article 10 of the EU AI Act on Tuesday at 4:00 PM?"* you cannot hand them your raw database.

**The Solution:** The engine outputs a mathematically agnostic JSON schema called the `cryptographic_attestation` (often referred to mechanically as the "Tri-Partite Hash" or previously as an S-Cert).

---

## 1. The Tri-Partite Hash

When ODGS validates a payload against a rule definition (e.g., `urn:odgs:sov:eu-ai-act:art10`), it records the event to a local Git repository (by default: `.odgs/audit/`) using a zero-knowledge structure. 

The core of this mathematically pure ledger entry is the combination of three independent SHA-256 hashes. If any piece of data changes later, the hashes will fail to reconcile when recomputed.

1.  **The Definition Hash (`definition_hash`):**
    *   This is the SHA-256 hash of the JSON Rule Configuration active at the exact time of execution.
    *   **Proves:** The exact legal constraints the engine applied without revealing the proprietary threshold (e.g., "Must equal X").
    
2.  **The Execution Hash (`config_hash`):** 
    *   This is the SHA-256 hash of the core Engine binaries (the Python Interceptor logic).
    *   **Proves:** The mathematical `simpleeval` framework actually evaluated the data, completely removing the possibility of human override or "Blind Clones".

3.  **The Origin Hash (`payload_hash`):**
    *   This is the SHA-256 hash of the physical database payload or API response evaluated during the process.
    *   **Proves:** The specific snapshot of the underlying payload without exposing PII (e.g., John Doe's mortgage amount).

---

## 2. Independent Verification (How an Auditor Proves Integrity)

To independently verify the mechanical integrity of an algorithmic decision, an auditor only needs three components:

1.  The `cryptographic_attestation.json` log from your repository.
2.  The public Sovereign JSON Rule (`urn:odgs:sov:eu-ai-act:art10.json`).
3.  The public source code of ODGS v5.0.0 at the specific Git Commit.

### The Math:

```bash
# 1. Auditor recalculates the Legal Definition Hash:
sha256sum(eu_ai_act_art10.json) 
# -> Must equal the `definition_hash` printed in the ledger.

# 2. Auditor inspects the mathematical engine version:
sha256sum(odgs/executive/interceptor.py)
# -> Must equal the `config_hash` printed in the ledger.

# 3. Secure Verification:
# If both hashes match precisely, the auditor is mathematically assured 
# that the algorithm was evaluated strictly against the defined law.
```

If your pipeline fails compliance and is **Hard-Stopped**, the ledger accurately logs the Exception along with the `payload_hash`, proving that you blocked the invalid data from proceeding into your infrastructure.

---

## 3. Commercial Notarization (The S-Cert Registry)

By default, the open-source `cryptographic_attestation` is logged completely offline as a JSON file to your local drive. This is sufficient for internal testing, but radically insufficient for regulatory audits.

For strict regulatory reporting scenarios (e.g., EU AI Act, DORA), enterprises require absolute cryptographic proof that the JSON log itself was not maliciously edited retroactively by a rogue DBA prior to an auditor's arrival.

**The Commercial Upgrade:**

If the engine is securely bound to the **Metric Provenance Enterprise Portal** with `ODGS_REQUIRE_SCERT=True`, it physically prevents the pipeline from executing unless the Tri-Partite Hash payload is successfully transmitted over mutual TLS to the **Air-Gapped S-Cert Registry**.

The SaaS/On-Premise registry cryptographically wraps the raw ODGS hashes in its own Sovereign Private Key, returning an immutable **"S-Cert" (Semantic Certificate)**. 

Organizations can take this S-Cert URN and publicly display it on physical products (e.g., an MRI machine UI screen) or embed it within regulatory filings, providing immediate, zero-knowledge mathematical proof that an independent 3rd-party Certificate Authority verified the internal execution log transaction.

👉 **Auditors require S-Certs, not text files. [Book a compliance consultation to deploy the Sovereign Node](https://platform.metricprovenance.com)**.

---

[< Back to README](/README.md) | [Documentation Map →](index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)

---
> **Require architectural clearance or SLA support for your organization?** [Consult the Metric Provenance Enterprise Portal](https://platform.metricprovenance.com).
