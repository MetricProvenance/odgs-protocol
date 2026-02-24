import hashlib
import json
import os
from typing import Dict, Any

def get_deterministic_json_hash(data: Any) -> str:
    """
    Generates a SHA-256 hash of a JSON-serializable object.
    Ensures determinism by sorting keys.
    """
    # abuse json.dumps to canonicalize the structure
    # separators=(',', ':') removes whitespace to ensure compact representation
    try:
        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
    except TypeError as e:
        print(f"Hashing Error: {e}")
        return "ERROR_NON_SERIALIZABLE"

def generate_project_hash(project_root: str) -> Dict[str, str]:
    """
    Reads all 7 component schemas from their Sovereign Planes and generates a composite hash.
    Returns a dict with individual file hashes and the global root hash.
    """
    
    # The 7 Immutable Pillars of ODGS, mapped to their Plane
    schema_map = {
        "1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_metrics.json": "standard_metrics.json",
        "1_NORMATIVE_SPECIFICATION/schemas/legislative/standard_dq_dimensions.json": "standard_dq_dimensions.json",
        "1_NORMATIVE_SPECIFICATION/schemas/legislative/ontology_graph.json": "ontology_graph.json",
        "1_NORMATIVE_SPECIFICATION/schemas/judiciary/standard_data_rules.json": "standard_data_rules.json",
        "1_NORMATIVE_SPECIFICATION/schemas/judiciary/root_cause_factors.json": "root_cause_factors.json",
        "1_NORMATIVE_SPECIFICATION/schemas/executive/business_process_maps.json": "business_process_maps.json",
        "1_NORMATIVE_SPECIFICATION/schemas/executive/physical_data_map.json": "physical_data_map.json"
    }
    
    hashes = {}
    combo_string = ""
    
    # Process each file
    for rel_path, filename in sorted(schema_map.items()):
        full_path = os.path.join(project_root, rel_path)
        
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                try:
                    data = json.load(f)
                    file_hash = get_deterministic_json_hash(data)
                except json.JSONDecodeError:
                    file_hash = "INVALID_JSON"
        else:
            file_hash = "MISSING_FILE"
            
        hashes[filename] = file_hash
        combo_string += file_hash
        
    # Generate the Master Governance Hash
    # This is the single 256-bit proof of the entire governance state
    master_hash = hashlib.sha256(combo_string.encode('utf-8')).hexdigest()
    
    return {
        "master_hash": master_hash,
        "components": hashes
    }

if __name__ == "__main__":
    # Test run
    # Assuming run from project root or package
    result = generate_project_hash(os.getcwd())
    print(json.dumps(result, indent=2))
