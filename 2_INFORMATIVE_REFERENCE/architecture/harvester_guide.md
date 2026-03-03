# ODGS Harvester Guide: The HarvesterFactory

**Version:** 4.0.0  
**Source:** [`2_INFORMATIVE_REFERENCE/src/odgs/harvester/factory.py`](file:///Users/kartik/Code/open-data-governance-protocol/odgs-protocol-main/2_INFORMATIVE_REFERENCE/src/odgs/harvester/factory.py)

---

## The Definition-Execution Gap

The primary problem in enterprise data governance is the translation of human-readable text (Legal Contracts, SLAs, B2Bs, SOC2 Documents) into mechanical code (Python, YAML, JSON). 

The ODGS **HarvesterFactory** bridges this gap. It provides a standardized framework for parsing arbitrary textual agreements and outputting them as immutable, structured ODGS objects (JSON Schemas) ready for ingestion by the Universal Validation Engine.

---

## Bring Your Own Blueprints (BYOB)

In earlier versions of ODGS, the engine was hardcoded with Sovereign Harvesters (like the `NLAwbHarvester` for Dutch Law or `FiboHarvester` for Financial Ontologies).

With **v4.0.0**, the Harvester acts as a completely agnostic plugin architecture. You, your internal development team, or your consulting partners (e.g., Deloitte, Capgemini) can write Python blueprints to automatically harvest and serialize your proprietary contracts or internal wikis.

### 1. The `BaseHarvester` Interface

Every harvester must implement the `BaseHarvester` class.

```python
from odgs.harvester.base import BaseHarvester
from typing import Dict, Any

class BaseHarvester(BaseHarvester):
    name = "abstract"  # Set to your unique blueprint name

    def fetch(self, reference: str) -> Dict[str, Any]:
        """
        Parses a reference source (an API, a Notion page, a PDF) 
        and extracts the governance definition.
        """
        pass
```

### 2. Implementing a Custom Proprietary Harvester

Imagine your organization manages Master Service Agreements (MSAs) on a secure internal portal.

You can write a `ProprietaryMsaHarvester` to hook into that portal, extract the exact data delivery SLA bounds mathematically, and serialize it for ODGS.

```python
# Save this somewhere in your infrastructure: /opt/odgs/blueprints/msa_harvester.py
from odgs.harvester.base import BaseHarvester

class ProprietaryMsaHarvester(BaseHarvester):
    name = "msa"  # This is the CLI mapping name 

    def fetch(self, reference: str) -> dict:
        """
        reference: e.g., "DOC-2026-991"
        """
        # 1. Reach out to your internal contract management API
        # api_response = requests.get(f"https://internal.contracts.local/api/v1/docs/{reference}")
        
        # 2. Extract Data Quality Constraints from the JSON payload or text
        # (For this example, we mock the extraction)
        sla_threshold = "0.999" 
        
        # 3. Output the ODGS Schema valid structure
        return {
            "urn": f"urn:odgs:custom:msa:{reference}",
            "name": f"MSA Availability SLA for {reference}",
            "logic_expression": f"uptime_percentage >= {sla_threshold}",
            "threshold_type": "float",
            "threshold_value": sla_threshold,
            "action_on_fail": "HARD_STOP"
        }
```

### 3. Dynamic Execution via the CLI

Data engineers do not need to modify the ODGS Python package to run your blueprint. They simply expose the path to the blueprints folder using an environment variable, and the `HarvesterFactory` dynamically imports the schemas at runtime.

```bash
# 1. Expose your custom blueprints path
export ODGS_CUSTOM_BLUEPRINTS="/opt/odgs/blueprints"

# 2. Run the native ODGS CLI using your custom harvester name
odgs harvest msa DOC-2026-991
```

**Expected Output:**
```text
> [SUCCESS] Harvested urn:odgs:custom:msa:DOC-2026-991
> Saved Immutable Definition: ./schemas/custom/msa_docs/DOC-2026-991.json
```

Once the schema is saved, the ODGS Universal Validation Engine can instantly route payloads to evaluate compliance against it entirely offline.

---

## Official First-Party Harvesters

The Open-Source ODGS engine natively ships with the following blueprints for public Sovereign laws and Ontologies:

| Harvester | CLI Name | Description | Source |
| :--- | :--- | :--- | :--- |
| **FIBO Ontology** | `fibo` | Financial Industry Business Ontology (Indicators) | EDM Council / OMG |
| **EU AI Act** | `eu_ai_act` | High-Risk System Compliance Directives | EUR-Lex |
| **Dutch Law** | `nl_awb` | General Administrative Law Act (AwB) | wetten.overheid.nl |

```bash
# Example: Harvesting the official FIBO Interest Rate dimension
odgs harvest fibo InterestRate
```

---

[< Back to README](/README.md) | [Documentation Map →](index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)
