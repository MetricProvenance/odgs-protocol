# ODGS Adapter Interface Guide

**Version:** 6.0.0  
**Source:** [`2_INFORMATIVE_REFERENCE/src/odgs/core/adapter.py`](../src/odgs/core/adapter.py)

---

## Overview

The **OdgsAdapter** is the Abstract Base Class (ABC) that connects the ODGS Constitutional Stack to external data sources. It lives at the boundary between the **Executive Plane** (governance context) and the **Physical Plane** (real-world data).

Every data platform integration (Snowflake, Databricks, PostgreSQL, Synapse, API endpoints) implements this interface.

```
┌──────────────────────────┐
│    ODGS Interceptor      │
│    (Executive Plane)     │
│                          │
│  1. Sovereign Handshake  │
│  2. Resolve Context      │
│  3. Enforce Rules        │
│          │               │
│          ▼               │
│  ┌──────────────────┐    │
│  │ AdapterRegistry  │    │
│  └──────────────────┘    │
│          │               │
└──────────┼───────────────┘
           │
    ┌──────┼──────────────────────┐
    │      │      │               │
    ▼      ▼      ▼               ▼
 Snowflake  Databricks  PostgreSQL  API
```

---

## The Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class OdgsAdapter(ABC):

    @abstractmethod
    def fetch_context(self, context_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch context data for a given ID and criteria.
        """
        pass

    @abstractmethod
    def resolve_reference(self, urn: str) -> Any:
        """
        Resolve a URN to its underlying value or object.
        """
        pass
```

---

## The AdapterRegistry (Bring Your Own Integrations)

ODGS is headless. Using the `AdapterRegistry`, you can inject custom Python hooks to serialize rule execution plans back and forth to your proprietary systems (e.g., Rust backends, Kafka streams, Databricks clusters) without waiting for us to build the integration.

### Dynamic Injection Tutorial

Instead of hardcoding adapters into the core engine, you can write your own Python modules and dynamically load them into the Sovereign Validation Engine at runtime via Python's native `importlib`.

**1. Create a Custom Adapter Class**
Create a new file anywhere in your VPC, for example: `/usr/local/lib/odgs/kafka_adapter.py`.

```python
from odgs.core.adapter import OdgsAdapter
import json

class KafkaAdapter(OdgsAdapter):
    name = "kafka"

    def fetch_context(self, context_id: str, criteria: dict) -> dict:
        # In a real scenario, you might read the latest offset for a particular entity
        return {"entity_status": "ACTIVE", "topic": "governance-pipeline"}
        
    def resolve_reference(self, urn: str) -> any:
        # Resolve a specific rule threshold dynamically via your streaming infra
        return "100"
```

**2. Injecting via the Registry**
The ODGS v6.0.0 engine exposes an `AdapterRegistry` that allows you to cleanly inject your Python class before initializing the Interceptor.

```python
from odgs.core.adapter import AdapterRegistry
from odgs.executive.interceptor import OdgsInterceptor
import importlib.util

# 1. Dynamically load your Python file (no need to touch the core ODGS pip install)
spec = importlib.util.spec_from_file_location("kafka_adapter", "/usr/local/lib/odgs/kafka_adapter.py")
kafka_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kafka_module)

# 2. Register your custom adapter
registry = AdapterRegistry()
registry.register("kafka", kafka_module.KafkaAdapter())

# 3. Initialize the Engine
interceptor = OdgsInterceptor(
    project_root="./schemas",
    adapter_registry=registry
)

# 4. Bind the active logic flow to your custom adapter
active_adapter = registry.get("kafka")
```

---

## Using the GenericAdapter (Testing)

For development and local testing, ODGS ships a `GenericAdapter` that uses an in-memory dictionary. You can use this to mock out Databricks or Snowflake before pushing your pipeline to production.

```python
from odgs.core.adapter import GenericAdapter

# Create a mock data store
adapter = GenericAdapter(data_store={
    "NHG_MARKET_VALUE:1011AA": {"market_value": 300000},
    "urn:odgs:metric:101": 0.15
})

# Use it
context = adapter.fetch_context("NHG_MARKET_VALUE", {"id": "1011AA"})
# → {"market_value": 300000}

value = adapter.resolve_reference("urn:odgs:metric:101")
# → 0.15
```

---

## Integration with the Interceptor

The active adapter is fetched from the registry inside the `OdgsInterceptor`. When the interceptor evaluates rules, it calls the adapter to hydrate data. If the pipeline encounters missing or corrupt context, it throws a `ProcessBlockedException` ("Hard Stop").

```python
# The interceptor uses the adapter to fetch live SQL/Kafka data during Step 4: Context Hydration.
result = interceptor.intercept(
    process_urn="urn:odgs:process:O2C_S03",
    data_context={"container_id": "MSKU1234567"}
)
```

---

## Platform Support Matrix

| Platform | Adapter Class | Status |
|----------|--------------|--------|
| In-Memory (Testing) | `GenericAdapter` | ✅ Shipped |
| Distributed Streaming (Kafka) | `Custom Implementation` | 📋 Covered in Tutorial |
| Snowflake | `SnowflakeAdapter` | 📋 Community |
| PostgreSQL | `PostgresAdapter` | 📋 Community |
| Databricks (SQL Warehouse) | `DatabricksAdapter` | 📋 Community |
| REST API | `ApiAdapter` | 📋 Community |

> **Contributing:** To add a new adapter, implement the `OdgsAdapter` ABC and use the `AdapterRegistry` to deterministically inject it into your internal Airflow or PySpark environments.

---
> **Require architectural clearance or SLA support for your organization?** [Consult the Sovereign S-Cert Registry](https://metricprovenance.com/brief).

[< Back to README](/README.md) | [Documentation Map →](index.md) | 🎯 [Watch the demo →](https://www.metricprovenance.com/watch)
