import os
import inspect
import importlib.util
from typing import Dict, Type
from odgs.harvester.core import BaseHarvester

class HarvesterFactory:
    """Dynamically loads and registers harvester blueprints."""
    
    def __init__(self, blueprints_dir: str = None):
        if not blueprints_dir:
            # Default to the internal blueprints directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            blueprints_dir = os.path.join(current_dir, "blueprints")
            
        self.registry: Dict[str, Type[BaseHarvester]] = {}
        
        # 1. Load native blueprints explicitly to preserve package context
        self._load_native_blueprints()
        
        # 2. Load custom external blueprints if injected via ENV
        external_dir = os.environ.get("ODGS_CUSTOM_BLUEPRINTS")
        if external_dir and os.path.isdir(external_dir):
            self._load_from_directory(external_dir)

    def _load_native_blueprints(self):
        """Loads default blueprints distributed with the ODGS protocol."""
        try:
            from odgs.harvester.blueprints import nl_awb, fibo, iso_42001, gdpr, basel
            modules = [nl_awb, fibo, iso_42001, gdpr, basel]
            for module in modules:
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseHarvester) and obj is not BaseHarvester:
                        blueprint_name = getattr(obj, "BLUEPRINT_NAME", module.__name__.split('.')[-1])
                        self.registry[blueprint_name] = obj
        except Exception as e:
            print(f"Warning: Failed to load native blueprints: {e}")

    def _load_from_directory(self, directory: str):
        """Scans the given directory and registers any BaseHarvester subclasses."""
        if not os.path.exists(directory):
            return

        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                filepath = os.path.join(directory, filename)
                
                # Dynamically load the module
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                        
                        # Find subclasses of BaseHarvester
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, BaseHarvester) and obj is not BaseHarvester:
                                # Default to the python filename (e.g., 'nl_awb', 'fibo', 'msa_harvester')
                                # Can be overridden by the class attribute BLUEPRINT_NAME
                                registry_key = getattr(obj, "BLUEPRINT_NAME", module_name)
                                self.registry[registry_key] = obj
                    except Exception as e:
                        print(f"Warning: Failed to load blueprint module {filename}: {e}")

    def get_harvester(self, blueprint_name: str) -> Type[BaseHarvester]:
        """Retrieve a harvester class by its registered name."""
        return self.registry.get(blueprint_name)

    def list_blueprints(self) -> list:
        """Return a list of all registered blueprint names."""
        return list(self.registry.keys())
