import os
import json

def create_mock_odgs_structure(base_dir):
    """
    Creates a minimal ODGS structure inside a sandbox for testing interceptor loads.
    """
    planes = ["sovereign", "judiciary", "executive", "legislative"]
    for p in planes:
        os.makedirs(os.path.join(base_dir, p), exist_ok=True)
        
    # judiciary / standard_data_rules.json
    with open(os.path.join(base_dir, "judiciary", "standard_data_rules.json"), "w") as f:
        json.dump({
            "rules": [
                {
                    "rule_id": "custom_bypass",
                    "urn": "urn:odgs:rule:custom_bypass",
                    "applicable_metrics": [],
                    "data_domain": "test",
                    "logic_expression": "True",
                    "enforcement_level": "LOG"
                }
            ]
        }, f)

    # executive / context_bindings.json
    with open(os.path.join(base_dir, "executive", "context_bindings.json"), "w") as f:
        json.dump({
            "contexts": [
                {
                    "context_id": "urn:odgs:custom:test",
                    "rules": ["urn:odgs:rule:custom_bypass"]
                }
            ]
        }, f)

    # executive / physical_data_map.json
    with open(os.path.join(base_dir, "executive", "physical_data_map.json"), "w") as f:
        json.dump({"test_indicator": "physical_map"}, f)
        
    # legislative / standard_metrics.json
    # legislative / ontology_graph.json
    with open(os.path.join(base_dir, "legislative", "ontology_graph.json"), "w") as f:
        json.dump({"test_indicator": "ontology"}, f)
        
    # legislative / standard_metrics.json
    with open(os.path.join(base_dir, "legislative", "standard_metrics.json"), "w") as f:
        json.dump({"test_indicator": "metrics"}, f)
        
    # schemas / validation / rule.schema.json
    schema_dir = os.path.join(base_dir, "schemas", "validation")
    os.makedirs(schema_dir, exist_ok=True)
    with open(os.path.join(schema_dir, "rule.schema.json"), "w") as f:
        json.dump({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string"},
                            "urn": {"type": "string"}
                        },
                        "required": ["rule_id"]
                    }
                }
            }
        }, f)
