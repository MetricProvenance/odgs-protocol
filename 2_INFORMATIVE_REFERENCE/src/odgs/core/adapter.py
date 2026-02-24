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
