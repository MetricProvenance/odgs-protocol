from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

class OdgsAdapter(ABC):
    """
    Abstract Base Class for Sovereign Data Adapters.
    Responsible for:
    1. Fetching external data (Context Hydration)
    2. resolving references (e.g. Market Value)
    """

    @abstractmethod
    def fetch_context(self, context_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch context data for a given ID and criteria.
        Example: fetch_context("NHG_MARKET_VALUE", {"zipcode": "1011AA", "house_type": "apartment"})
        Returns: {"market_value": 300000}
        """
        pass

    @abstractmethod
    def resolve_reference(self, urn: str) -> Any:
        """
        Resolve a specific URN to a value or object.
        """
        pass

class GenericAdapter(OdgsAdapter):
    """
    A simple, dictionary-based adapter for testing and default behavior.
    Acts as a 'Mock' database.
    """
    def __init__(self, data_store: Dict[str, Any] = None):
        self.store = data_store or {}
        self.logger = logging.getLogger("odgs.adapter")

    def fetch_context(self, context_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Fetching context: {context_id} with criteria: {criteria}")
        # Simple implementation: Look for exact match in store or return empty
        # In a real impl, this would query SQL/API
        key = f"{context_id}:{criteria.get('id', 'default')}"
        return self.store.get(key, {})

    def resolve_reference(self, urn: str) -> Any:
        return self.store.get(urn)

class AdapterRegistry:
    """
    Registry for dynamic Physical Plane injections.
    Allows external applications to map URN prefixes (e.g., 'urn:odgs:physical:dbt')
    to specific OdgsAdapter instances or lazy-load them via importlib strings.
    """
    _adapters: Dict[str, OdgsAdapter] = {}

    @classmethod
    def register(cls, prefix: str, adapter: OdgsAdapter):
        """Register an instantiated adapter against a URN prefix."""
        cls._adapters[prefix] = adapter

    @classmethod
    def get_adapter(cls, urn: str) -> Optional[OdgsAdapter]:
        """Find the matching adapter for a given target URN."""
        # Find the most specific prefix match
        best_match = None
        best_match_len = -1
        
        for prefix, adapter in cls._adapters.items():
            if urn.startswith(prefix) and len(prefix) > best_match_len:
                best_match = adapter
                best_match_len = len(prefix)
                
        return best_match
    
    @classmethod
    def clear(cls):
        """Clear all registered adapters (primarily for testing)."""
        cls._adapters.clear()
