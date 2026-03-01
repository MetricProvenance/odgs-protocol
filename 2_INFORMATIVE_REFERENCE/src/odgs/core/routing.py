import os
from typing import Optional, Dict

class NamespaceRouter:
    """
    Dynamically routes URN namespaces to their configured physical paths.
    Enables schema-agnostic routing for the Universal Engine.
    """
    def __init__(self, base_config_dir: str = None):
        self.base_dir = base_config_dir or os.environ.get("ODGS_CONFIG_PATH", "/etc/odgs/packs")
        
        # Default known namespaces mapping
        self.routes: Dict[str, str] = {
            "urn:odgs:sov:": os.path.join(self.base_dir, "sovereign"),
            "urn:odgs:contract:": os.path.join(self.base_dir, "contracts"),
            "urn:odgs:custom:": os.path.join(self.base_dir, "custom"),
            "urn:odgs:rule:": os.path.join(self.base_dir, "judiciary"),
            "urn:odgs:metric:": os.path.join(self.base_dir, "legislative"),
            "urn:odgs:dimension:": os.path.join(self.base_dir, "legislative"),
            "urn:odgs:process:": os.path.join(self.base_dir, "executive")
        }
        
    def register_route(self, prefix: str, path: str):
        """Allows dynamic injection of new URN namespaces."""
        self.routes[prefix] = path
        
    def get_path(self, urn: str) -> Optional[str]:
        """Returns the base directory for a given URN based on its prefix."""
        for prefix, path in self.routes.items():
            if urn.startswith(prefix):
                return path
        return None
