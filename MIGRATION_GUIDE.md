# ODGS v3.3 Migration Guide

**WARNING:** This release contains **BREAKING CHANGES** from v3.0.
Do not pull or deploy v3.3.0 without reading this guide.

## Overview
ODGS v3.3 introduces the **Sovereign Knowledge Graph**, **Sovereign Handshake** (integrity verification), and **Tri-Partite Binding** (3-hash audit trail). To achieve global uniqueness and time-travel capabilities, we have strictly enforced **URNs (Uniform Resource Names)** for all identifiers.

**The Change:**
*   **Old (v3.0):** Integer IDs (e.g., `damaId: 57`, `param_id: 101`)
*   **New (v3.3):** URN Strings (e.g., `urn:odgs:dimension:timeliness`, `urn:odgs:metric:net-profit`)

This affects `standard_data_rules.json`, `root_cause_factors.json`, and `standard_metrics.json`.

---

## 🛡️ Stay Informed (Enterprise Nodes)

**Why did my pipeline break?**
You are likely pulling `latest` from PyPI/npm in a firewalled environment.
v3.3 introduces Sovereign Schemas, Handshake verification, and Tri-Partite Binding to comply with EU AI Act Articles 10 & 12.

**How do I prevent future breaks?**
Click the **Watch** button (top right of this repository) → select **Releases Only**.

This ensures your Engineering Leads receive an immediate GitHub notification before any schema-breaking change is merged. We do not track you — this is GitHub's native notification system.

---

## Step 1: Backup Your Data
Before running any scripts, ensure your current `lib/schemas` directory is backed up.

```bash
cp -r lib/schemas lib/schemas_backup_v3_0
```

## Step 2: Run the Migration Script
We have provided a "Data Rescue" script that automatically:
1.  Reads your existing Dimensions to build a URN Map.
2.  Rewrites `standard_data_rules.json` to replace `improvesDqDimensionIds` (integers) with `related_dimension_urns`.
3.  Rewrites `root_cause_factors.json` to replace `dqDimensionsImpactedDamaIds` (integers) with `related_dimension_urns`.

**Execute:**
```bash
python scripts/migrate_v3_0_to_v3_2.py
```

**Expected Output:**
```text
Loading Dimensions...
Building URN Map...
Migrating Rules...
Updated lib/schemas/judiciary/standard_data_rules.json
Migrating Factors...
Updated lib/schemas/judiciary/root_cause_factors.json
```

## Step 3: Verify Data Integrity
Open `lib/schemas/judiciary/standard_data_rules.json` and check a Rule entry.

**v3.0 (Old):**
```json
"improvesDqDimensionIds": [ 15, 57 ]
```

**v3.3 (New):**
```json
"related_dimension_urns": [
    "urn:odgs:dimension:accuracy",
    "urn:odgs:dimension:timeliness"
]
```

## Step 4: Update Your Metrics
The migration script determines URNs for *Rules* and *Factors*, but you must manually link your *Metrics* to the new **Sovereign Definitions** you harvest.

1.  Run `odgs harvest` to get your definitions.
2.  Edit `standard_metrics.json`.
3.  Populate the `sovereign_urn` field for each metric.

## Rollback
If the migration fails or breaks downstream systems:

1.  Delete the corrupted `lib/schemas`.
2.  Restore from backup: `cp -r lib/schemas_backup_v3_0 lib/schemas`.
3.  Pin your dependency to v3.0: `pip install "odgs<3.1"`.
