
import json
import pytest
import os
from odgs import OdgsInterceptor, ProcessBlockedException
from odgs.system.scripts.hashing import generate_project_hash

# Load fixtures
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "../fixtures/standard_scenarios.json")

def load_scenarios():
    with open(FIXTURE_PATH) as f:
        return json.load(f)

@pytest.mark.parametrize("scenario", load_scenarios())
def test_protocol_parity(scenario):
    """
    Execute standard scenarios to ensure Python behavior matches the Protocol Definition.
    """
    interceptor = OdgsInterceptor()
    
    # Generate the valid hash for the current codebase
    # This simulates a "Clean Handshake" environment
    project_hash = generate_project_hash(interceptor.project_root)["master_hash"]
    
    context = scenario["input"]
    rule_id = scenario["rule_id"]
    expected = scenario["expected_result"]
    
    # Mock process URN for testing
    process_urn = "urn:odgs:process:test"
    
    if expected == "PASS":
        # Should not raise exception
        try:
            interceptor.intercept(process_urn, context, required_integrity_hash=project_hash)
        except ProcessBlockedException:
            pytest.fail(f"Scenario {scenario['id']} blocked but expected PASS")
            
    elif expected == "BLOCK":
        # Should raise ProcessBlockedException
        with pytest.raises(ProcessBlockedException):
            interceptor.intercept(process_urn, context, required_integrity_hash=project_hash)
