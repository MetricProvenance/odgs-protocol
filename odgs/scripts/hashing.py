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
    Reads all 7 component schemas and generates a composite hash.
    Returns a dict with individual file hashes and the global root hash.
    """
    
    # The 7 Immutable Pillars of ODGS
    # Note: filenames must match exactly what `odgs init` creates
    schema_files = [
        "standard_metrics.json",
        "standard_data_rules.json",
        "standard_dq_dimensions.json",
        "root_cause_factors.json",
        "business_process_maps.json",
        "physical_data_map.json",
        "ontology_graph.json"
    ]
    
    hashes = {}
    combo_string = ""
    
    # Process each file
    for filename in sorted(schema_files):
        path = os.path.join(project_root, filename)
        
        if os.path.exists(path):
            with open(path, 'r') as f:
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
