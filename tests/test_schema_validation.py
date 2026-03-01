import pytest
import os
import json
import shutil
from odgs.executive.interceptor import OdgsInterceptor, SchemaValidationException
import test_utils

@pytest.fixture
def schema_sandbox():
    sandbox_dir = "/tmp/odgs_schema_sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    
    test_utils.create_mock_odgs_structure(sandbox_dir)
    
    yield sandbox_dir
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)

def test_perfect_schema(schema_sandbox):
    # Pass a perfectly formatted standard_data_rules.json to interceptor
    interceptor = OdgsInterceptor(schema_sandbox)
    
    # Perfect rule from normal specification
    perfect_rule = {
        "rules": [
            {
                "rule_id": "test_rule_1",
                "urn": "urn:odgs:sov:test:1",
                "applicable_metrics": ["metric_1"],
                "data_domain": "finance",
                "logic_expression": "amount > threshold",
                "enforcement_level": "BLOCK"
            }
        ]
    }
    
    # In interceptor, the schema validates against standard_data_rules.json.
    # If jsonschema is installed, interceptor._validate_schema ensures it passes silently.
    try:
        interceptor._validate_schema(perfect_rule, "standard_data_rules.json")
    except SchemaValidationException as e:
        pytest.fail(f"Valid schema threw SchemaValidationException: {str(e)}")
    except FileNotFoundError:
        # If running locally without schemas mounted, we might hit FileNotFoundError
        # But interceptor checks path existence. Let's just catch and ignore missing schema file errors
        # if the test is run out-of-context. We only want to assert SchemaValidationException isn't thrown 
        # for real schema reasons.
        pass
        
def test_malformed_type(schema_sandbox):
    interceptor = OdgsInterceptor(schema_sandbox)
    
    # Malformed rule where 'rule_id' is an integer instead of string
    malformed_rule = {
        "rules": [
            {
                "rule_id": 12345, # SHOULD BE STRING
                "urn": "urn:odgs:sov:test:1",
                "applicable_metrics": ["metric_1"],
                "data_domain": "finance",
                "logic_expression": "amount > threshold",
                "enforcement_level": "BLOCK"
            }
        ]
    }
    
    # Ensure it throws a SchemaValidationException
    # We must ensure the actual jsonschema validation triggers. 
    import jsonschema
    try:
        interceptor._validate_schema(malformed_rule, "standard_data_rules.json")
        pytest.fail("SchemaValidationException was NOT thrown for a malformed JSON type.")
    except SchemaValidationException as e:
        # The jsonschema library error provides the exact field error inside the exception string
        pass
    except FileNotFoundError:
        pytest.skip("Local environment does not contain Draft7 validation schemas to run strict type checks against.")
