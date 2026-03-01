import pytest
import os
import shutil
from odgs.harvester.factory import HarvesterFactory

@pytest.fixture
def registry_sandbox():
    sandbox_dir = "/tmp/odgs_registry_sandbox_clean"
    os.makedirs(sandbox_dir, exist_ok=True)
    
    # Write a valid dummy harvester
    with open(os.path.join(sandbox_dir, "harvester_valid.py"), "w") as f:
        f.write("""
from odgs.harvester.core import BaseHarvester

class HarvesterValid(BaseHarvester):
    BLUEPRINT_NAME = "valid_dummy"
    name = "valid_dummy"
    def harvest(self, reference):
        return {"status": "success", "reference": reference}
""")

    # Write a malicious/invalid harvester (doesn't inherit, or has syntax error)
    with open(os.path.join(sandbox_dir, "harvester_invalid.py"), "w") as f:
        f.write("""
class JustSomeClass:
    name = "invalid_dummy"
    # missing fetch method
    # doesn't inherit BaseHarvester
""")
    
    yield sandbox_dir
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)

def test_harvester_injection(registry_sandbox, monkeypatch):
    monkeypatch.setenv("ODGS_CUSTOM_BLUEPRINTS", registry_sandbox)
    
    factory = HarvesterFactory()
    # Factory should be able to load 'valid_dummy'
    harvester_class = factory.get_harvester("valid_dummy")
    assert harvester_class is not None
    
    instance = harvester_class()
    result = instance.harvest("test_ref")
    assert result["status"] == "success"

def test_malicious_injection(registry_sandbox, monkeypatch):
    monkeypatch.setenv("ODGS_CUSTOM_BLUEPRINTS", registry_sandbox)
    
    factory = HarvesterFactory()
    # Factory should NOT crash if it encounters an invalid harvester.
    # It should return None or raise a specific controlled exception, not crash the process.
    harvester_class = factory.get_harvester("invalid_dummy")
    assert harvester_class is None
