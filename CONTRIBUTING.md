
# Contributing to the Open Data Governance Standard (ODGS)

Thank you for your interest in contributing to the **ODGS Protocol**. We are building a vendor-neutral standard for Sovereign Data Governance — decoupling business definitions from execution platforms.

## 🌟 How to Contribute

We welcome contributions in three main areas:
1.  **Core Protocol**: Improving the JSON schemas for Metrics, Rules, Ontology, and Sovereign Definitions.
2.  **Harvester Blueprints**: Adding new legislative source connectors (see `2_INFORMATIVE_REFERENCE/src/odgs/harvester/blueprints/`).
3.  **Platform Adapters**: Extending integrations for dbt, Power BI, Tableau, and new platforms.

## 🛠 Development Setup

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/MetricProvenance/odgs-protocol.git
    cd odgs-protocol
    ```

2.  **Install (Polyglot)**:
    We support both Python (Core Engine) and Node.js (Cross-Platform Interceptor).

    **Python:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[all]"    # Core + optional extras (demo, ai)
    # Or minimal: pip install -e .
    ```

    **Node.js:**
    ```bash
    npm install
    ```

3.  **Run the Stack**:
    *   **API Server**: `odgs api`
    *   **CLI**: `odgs --help`

## 🧪 Testing

Run the full test suite:

```bash
# Python tests (18 tests)
python -m pytest tests/ -v

# Node.js tests (2 parity tests)
npx vitest run

# Schema validation (122 items)
python 2_INFORMATIVE_REFERENCE/src/odgs/system/scripts/validate_schemas.py .
```

## 📜 License
This project is licensed under the Apache 2.0 License.

---
[< Back to README.md](/README.md)
