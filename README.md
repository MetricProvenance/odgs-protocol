# 🏛️ The Open Governance Schema (OGS)
> The "HTML" for Business Logic.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Standard](https://img.shields.io/badge/standard-OGS_v1.0-blue)]()
[![Maintained by](https://img.shields.io/badge/maintained%20by-QuirkySwirl-orange)](https://definitions.quirkyswirl.com)
**The open standard for "Headless" Data Governance.**

[](https://opensource.org/licenses/MIT) [](https://json.org)

## 📉 The Problem: Definition Drift

In the modern data stack, business logic is fragmented. The definition of `Gross Margin` in dbt often conflicts with the DAX formula in Power BI, which differs from the calculation in Tableau.

**Result:** Executives don't trust the dashboard, and Data Engineers spend 40% of their time debugging "why the numbers don't match."

## 🚀 The Solution: Write Once, Sync Everywhere

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

## 🛠 Usage & Implementation

### Option A: Build your own Sync Engine

Fork this repository. Use these JSON files as the configuration layer in your CI/CD pipeline. Write Python/Node parsers to inject these definitions into your tools (dbt `schema.yml`, Power BI XMLA, etc.).

### Option B: The Reference Implementation

If you prefer a managed "Headless Governance" layer that natively supports OGS and handles the sync to Power BI/dbt automatically, see the **[Clavis Project](https://www.google.com/search?q=https://definitions.quirkyswirl.com)** (Commercial Managed Service).

-----

## Contributing

This is an open standard. We welcome Pull Requests to expand the `dq_dimensions` or refine the `root_cause_factors` taxonomy.

*Released under the MIT License.*