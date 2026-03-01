import pytest
import os
import shutil
from odgs.executive.interceptor import OdgsInterceptor, MissingRuleException
import test_utils

@pytest.fixture
def router_sandbox():
    sandbox_dir = "/tmp/odgs_router_sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    
    # We create the mock structure for custom bypass but leave sovereign empty to test the trap
    test_utils.create_mock_odgs_structure(sandbox_dir)
    
    # Create the custom schema explicitly to test bypass
    custom_dir = os.path.join(sandbox_dir, "custom")
    os.makedirs(custom_dir, exist_ok=True)
    
    import json
    with open(os.path.join(custom_dir, "test.json"), "w") as f:
        json.dump({"test": "bypass_schema"}, f)
        
    yield sandbox_dir
    
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)

def test_sovereign_trap(router_sandbox):
    # Pass the valid local context, which doesn't contain the specific sovereign rules requested
    interceptor = OdgsInterceptor(router_sandbox)
    
    with pytest.raises(MissingRuleException) as exc_info:
        interceptor.intercept("urn:odgs:sov:eu-ai-act:art10", {})
        
    assert exc_info.value.status_code == 428
    assert "Missing Required Configuration for Namespace" in str(exc_info.value)

def test_custom_bypass(router_sandbox):
    interceptor = OdgsInterceptor(router_sandbox)
    
    # Custom bypass should not throw MissingRuleException
    # It might fail later in evaluation if the mock isn't full, but the trap itself is bypassed
    
    try:
        # Load custom rules. Let's see if it tries to load custom bypass.
        # urn:odgs:custom:test will attempt to load custom/test.json
        # Since it exists in the sandbox, it will be loaded without throwing MissingRuleException
        interceptor.intercept("urn:odgs:custom:test", {"mock": "data"})
    except MissingRuleException:
        pytest.fail("MissingRuleException was incorrectly thrown for a custom URN")
    except Exception:
        # Other exceptions (like execution errors inside) are acceptable as long as it bypassed the 428 trap
        pass
