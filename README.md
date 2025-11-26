# 🏛️ The Open Governance Schema (OGS)
> **The Open Standard for Headless Metric Definitions**  
> Decouples Business Logic from BI Tools

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Standard](https://img.shields.io/badge/standard-OGS_v1.0-blue)]()
[![Maintained by](https://img.shields.io/badge/maintained%20by-QuirkySwirl-orange)](https://definitions.quirkyswirl.com)

[](https://opensource.org/licenses/MIT) [](https://json.org)
![Infographic](https://res.cloudinary.com/dcfadz2uh/image/upload/v1764178689/infographic-bdm_srl43z.png)

## 📉 The Problem: Definition Drift

In the modern data stack, business logic is fragmented. The definition of `Gross Margin` in dbt often conflicts with the DAX formula in Power BI, which differs from the calculation in Tableau.

**Result:** Executives don't trust the dashboard, and Data Engineers spend 40% of their time debugging "why the numbers don't match."

## 🚀 The Solution: Write Once, Sync Everywhere
![Headless Data Governance](https://res.cloudinary.com/dcfadz2uh/image/upload/v1764172903/headless-data-governance_tbli5k.png)

```mermaid
graph TD
    subgraph PROBLEM ["❌ The Problem: Definition Drift"]
        A[CFO: 'Gross Margin' in Excel] -->|Disconnect| B[dbt: SQL Logic]
        A -->|Disconnect| C[Power BI: DAX Logic]
        B -.-|Mismatch| C
    end

    subgraph SOLUTION ["✅ The Solution: Open Governance Schema"]
        D[("JSON Schema (OGS)
        Single Source of Truth")] 
        
        D -->|Auto-Sync| E[dbt / Snowflake]
        D -->|Auto-Sync| F[Power BI / Tableau]
        D -->|Auto-Sync| G[Data Catalog / Collibra]
    end

    style D fill:#f9f,stroke:#333,stroke-width:4px,color:black
    style PROBLEM fill:#ffcccc,stroke:#333,stroke-width:1px
    style SOLUTION fill:#ccffcc,stroke:#333,stroke-width:1px
```

The **Open Governance Schema (OGS)** is a vendor-neutral JSON protocol that acts as the "API" for your business definitions. By decoupling the **Definition** (The "What") from the **Tool** (The "How"), you achieve Headless Governance.

### How it works

```json
// example: standard_metrics.json
{
  "metric_id": "KPI_102",
  "name": "Gross_Margin",
  "domain": "Finance",
  "calculation_logic": {
    "abstract": "Revenue - COGS",
    "sql_standard": "SUM(gross_sales) - SUM(cost_of_goods)",
    "dax_pattern": "[Total Sales] - [Total Cost]"
  },
  "owner": "CFO_Office",
  "quality_threshold": "99.5%"
}
```

## 📂 The Protocol Structure

This repository contains the core schemas that define the "Alphabet" of Data Governance:

| File | Purpose |
| :--- | :--- |
| **`standard_metrics.json`** | The "Golden Record" for KPIs. Define logic, ownership, and sensitivity here. |
| **`standard_dq_dimensions.json`** | The 60 industry-standard dimensions of data quality (Accuracy, Timeliness, Completeness, etc.). |
| **`standard_data_rules.json`** | Technical validation rules (Regex patterns, null checks, referential integrity). |
| **`root_cause_factors.json`** | A standardized taxonomy for *why* data breaks (e.g., `Process_Gap` vs `Integration_Failure`). |
| **`business_process_maps.json`** | Maps how data entities flow through the business lifecycle. |

## ✅ Validation & CI/CD Integration

The repository includes a **validator script** that enforces the governance schema:

```bash
python3 validate_schema.py
```

**Output:**
```
🔍 Running Open Governance Schema Validator...
✅ Loaded 72 metrics.
✅ Loaded 50 data rules.
🎉 All Governance Checks Passed!
```

### CI/CD Integration

Add this to your GitHub Actions workflow to enforce governance standards:

```yaml
- name: Validate Governance Schema
  run: python3 validate_schema.py
```

This ensures that all metrics and rules have:
- Unique IDs
- Assigned owners
- Defined domains
- Clear calculation logic

---

## 🛠 Usage & Implementation

### Option A: Build your own Sync Engine

Fork this repository. Use these JSON files as the configuration layer in your CI/CD pipeline. Write Python/Node parsers to inject these definitions into your tools (dbt `schema.yml`, Power BI XMLA, etc.).

### Option B: The Reference Implementation

If you prefer a managed "Headless Governance" layer that natively supports OGS and handles the sync to Power BI/dbt automatically, first see the art of possible with **[Chartr Project](https://chartr.quirkyswirl.com/)** (Commercial Managed Services - coming soon).

-----

## Contributing

This is an open standard. We welcome Pull Requests to expand the `dq_dimensions` or refine the `root_cause_factors` taxonomy.

*Released under the MIT License.*