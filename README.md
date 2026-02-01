# Open Data Governance Schema (ODGS)
![Explainer ODGS](https://res.cloudinary.com/drsprx7wk/image/upload/v1765951443/ODGS-explainer_ugwrqz.png)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![AI Safety](https://img.shields.io/badge/AI%20Safety-EU%20AI%20Act%20Compliant-blueviolet)]()

> **"The Protocol for Algorithmic Accountability"**

---

## What is ODGS?

**ODGS** is an open-source, vendor-neutral JSON protocol that serves as the **single source of truth** for your business logic. It solves the "Metric Drift" problem—where "Revenue" means three different things in three different tools—by defining metrics **once** and compiling them to **Snowflake**, **Power BI**, **dbt**, and **AI Agents** automatically.

---

## ⚡ Recent Milestone: The V2 Protocol Forge
We have recently integrated **Gemini 3.0 Flash** to evolve ODGS from a static schema into an **Autonomous Governance Forge**.

- **Full Protocol Generation**: Generate interconnected 4-file bundles (Metrics, Rules, Ontology, Data Map) for any industry sector in seconds.
- **Deterministic Integrity**: Every generated artifact is sealed with a **Digital Fingerprint (SHA-256)** to enable drift detection and AI grounding.
- **Governance Console**: A professional explorer to visualize the "Self-Annealing" process and business impact metrics.

---

Think of it as the **"Universal Remote for Data"**. Instead of programming the same metric into multiple tools, you define it once in ODGS, and it syncs everywhere.

### Why It Matters

- **For Enterprises**: Achieve **EU AI Act compliance** through Metric Provenance
- **For Data Teams**: Write definitions once, eliminate copy-paste SQL across tools  
- **For AI Engineers**: Prevent "Semantic Hallucinations" by grounding LLMs in structured, verifiable context

![EU AI Act Compliance](https://res.cloudinary.com/drsprx7wk/image/upload/v1765402023/EU-AI-Act-ODGS_ce3wuo.png)
---

## Architecture

```mermaid
graph LR
    ODGS[("ODGS Protocol
    (JSON Truth)")] -->|Compiles to| dbt["dbt Semantic Layer"]
    ODGS -->|Compiles to| PBI["Power BI (TMSL)"]
    ODGS -->|Compiles to| Tableau["Tableau (TDS)"]
    ODGS -->|Feeds Context| AI["AI Agents (RAG)"]
    
    style ODGS fill:#4CAF50,color:white,stroke:#333,stroke-width:3px
```

**Headless Governance** means decoupling the *Definition* (your business rules) from the *Tool* (Tableau, Power BI, etc.). ODGS acts as the compilation layer that transforms abstract logic into tool-native code.

### Authentic vs. Artificial Intelligence

We believe AI is only as good as the rules you give it.

- **Artificial Intelligence** guesses the answer based on probability
- **Authentic Intelligence** knows the answer based on codified human expertise

ODGS captures the *Authentic Intelligence* of your domain experts—the nuances, the exceptions, the business rules—and codifies them into a standard that AI can respect.

> **"The Table Format War is over. The Semantic War has just begun. Don't build another silo. Build on the Standard."**

![ODGS Protocol Architecture](https://res.cloudinary.com/drsprx7wk/image/upload/v1764513291/headless-architecure_ilnqfx.png)
---

## Quick Start

```bash
# Install
pip install odgs

# Initialize a project
odgs init my-governance-layer
cd my-governance-layer

# Validate your schemas
odgs validate

# Build artifacts for all downstream tools
odgs build --target all
```

---

## Documentation

📘 **[Complete Guide](guide.md)**  
End-to-end journey from concept to implementation. Includes quickstart, schema reference, CLI commands, and adapter examples.

🎯 **[Strategic Vision](vision.md)**  
The business case for ODGS: Market opportunity, AI Safety compliance, academic partnerships, and the "Swiss Army Knife" thesis.

---

## The 7 Core Schemas

| Schema | Purpose |
|:---|:---|
| [standard_metrics.json](../protocol/lib/standard_metrics.json) | KPI definitions (logic, ownership, compliance tags) |
| [standard_data_rules.json](../protocol/lib/standard_data_rules.json) | Validation rules (regex, nulls, ranges) |
| [standard_dq_dimensions.json](../protocol/lib/standard_dq_dimensions.json) | Data quality categories (Accuracy, Timeliness) |
| [root_cause_factors.json](../protocol/lib/root_cause_factors.json) | Taxonomy for data failures (Process Gap, Integration Failure) |
| [business_process_maps.json](../protocol/lib/business_process_maps.json) | Process workflows (Order-to-Cash, Procure-to-Pay) |
| [physical_data_map.json](../protocol/lib/physical_data_map.json) | Mapping logic to database tables/columns |
| [ontology_graph.json](../protocol/lib/ontology_graph.json) | Knowledge graph (Customer *has* Orders) |

---

## Contributing

We welcome contributions! Whether you're:
- **Researchers**: Expanding the DQ Dimensions taxonomy  
- **Engineers**: Building adapters for new tools (Looker, Qlik)  
- **Domain Experts**: Refining the Root Cause taxonomy

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

**Copyright © 2025 [Metric Provenance](https://github.com/MetricProvenance)**