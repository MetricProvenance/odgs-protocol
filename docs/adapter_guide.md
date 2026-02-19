# ODGS Adapter Interface Guide

**Version:** 3.3.0  
**Source:** [`src/odgs/core/adapter.py`](file:///Users/kartik/Code/open-data-governance-protocol/odgs-protocol-main/src/odgs/core/adapter.py)

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
│  │  OdgsAdapter ABC │    │
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
        
        Args:
            context_id: The context identifier (e.g., "NHG_MARKET_VALUE")
            criteria: Query parameters (e.g., {"zipcode": "1011AA", "house_type": "apartment"})
        
        Returns:
            Dict with the resolved context values (e.g., {"market_value": 300000})
        """
        pass

    @abstractmethod
    def resolve_reference(self, urn: str) -> Any:
        """
        Resolve a URN to its underlying value or object.
        
        Args:
            urn: A valid ODGS URN (e.g., "urn:odgs:metric:101")
        
        Returns:
            The resolved value, definition object, or None if not found.
        """
        pass
```

---

## Implementing an Adapter

### Example: Snowflake Adapter

```python
import snowflake.connector
from odgs.core.adapter import OdgsAdapter

class SnowflakeAdapter(OdgsAdapter):
    """Resolves ODGS contexts against a Snowflake warehouse."""
    
    def __init__(self, account: str, user: str, password: str, database: str):
        self.conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            database=database
        )
    
    def fetch_context(self, context_id: str, criteria: dict) -> dict:
        """
        Maps ODGS context IDs to Snowflake views.
        The physical_data_map.json defines the column-level mappings.
        """
        cursor = self.conn.cursor()
        
        # Example: NHG_MARKET_VALUE → ANALYTICS.PROPERTY_VALUATIONS
        query = f"""
            SELECT market_value, valuation_date, source_authority
            FROM ANALYTICS.PROPERTY_VALUATIONS
            WHERE zipcode = %s AND house_type = %s
            ORDER BY valuation_date DESC
            LIMIT 1
        """
        cursor.execute(query, (criteria.get("zipcode"), criteria.get("house_type")))
        row = cursor.fetchone()
        
        if row:
            return {
                "market_value": row[0],
                "valuation_date": str(row[1]),
                "source": row[2]
            }
        return {}
    
    def resolve_reference(self, urn: str) -> any:
        """Resolve a metric URN to its current calculated value."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT current_value FROM GOVERNANCE.METRIC_REGISTRY WHERE urn = %s",
            (urn,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
```

### Example: PostgreSQL Adapter

```python
import psycopg2
from odgs.core.adapter import OdgsAdapter

class PostgresAdapter(OdgsAdapter):
    """Resolves ODGS contexts against PostgreSQL."""
    
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def fetch_context(self, context_id: str, criteria: dict) -> dict:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT data FROM odgs_contexts WHERE context_id = %s AND criteria @> %s::jsonb",
            (context_id, json.dumps(criteria))
        )
        row = cursor.fetchone()
        return row[0] if row else {}
    
    def resolve_reference(self, urn: str) -> any:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM odgs_references WHERE urn = %s", (urn,))
        row = cursor.fetchone()
        return row[0] if row else None
```

---

## Using the GenericAdapter (Testing)

For development and testing, ODGS ships a `GenericAdapter` that uses an in-memory dictionary:

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

The adapter is injected into the `OdgsInterceptor` during initialization. When the interceptor evaluates rules, it calls the adapter to hydrate data:

```python
from odgs.executive.interceptor import OdgsInterceptor

# Initialize with your platform adapter
interceptor = OdgsInterceptor(
    project_root="./lib/schemas",
    adapter=SnowflakeAdapter(...)
)

# The interceptor calls adapter.fetch_context() internally
# during Step 4: Context Hydration
result = interceptor.intercept(
    process_urn="urn:odgs:process:O2C_S03",
    data_context={"container_id": "MSKU1234567"},
    required_integrity_hash="7e240de74fb1ed..."
)
```

---

## Platform Support Matrix

| Platform | Adapter Class | Status |
|----------|--------------|--------|
| In-Memory (Testing) | `GenericAdapter` | ✅ Shipped |
| Snowflake | `SnowflakeAdapter` | 📋 Example above |
| PostgreSQL | `PostgresAdapter` | 📋 Example above |
| Databricks (SQL Warehouse) | `DatabricksAdapter` | 📋 Community |
| Azure Synapse | `SynapseAdapter` | 📋 Community |
| REST API | `ApiAdapter` | 📋 Community |

> **Contributing:** To add a new adapter, implement `OdgsAdapter` and submit a PR to the `adapters/` directory.

---

## Normative References

- **Physical Data Map:** [`lib/schemas/executive/physical_data_map.json`](/lib/schemas/executive/physical_data_map.json) defines column-level mappings
- **Context Bindings:** [`lib/schemas/executive/context_bindings.json`](/lib/schemas/executive/context_bindings.json) defines which metrics/rules apply to each process
- **Architecture:** [`docs/architecture.md`](/docs/architecture.md) Section 3 (The Sovereign Sidecar)

---
[< Back to README](/README.md) | [Documentation Map →](index.md) | 🎯 [Live Demo →](https://demo.metricprovenance.com)
